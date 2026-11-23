"""Browser-driven sync of the Revenue Cloud catalog into the local cache.

One sync job walks every catalog object in order. For each object it first
checks metadata (describe) and record visibility (COUNT), records the result
in catalog_object_coverage, then pages records with SOQL into catalog_records.

Modes:
- incremental (default): objects with a watermark from the last successful
  run read only rows whose SystemModstamp is newer (5-minute overlap).
- full: every object is re-read and cache rows that Salesforce no longer
  returns are removed (deleted or no longer visible records).
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from simple_salesforce import Salesforce
from simple_salesforce.exceptions import (
    SalesforceError,
    SalesforceMalformedRequest,
    SalesforceRefusedRequest,
    SalesforceResourceNotFound,
)
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.catalog.objects import ALL_OBJECTS, CatalogObject
from src.catalog.salesforce_gateway import (
    connect,
    parse_sf_datetime,
    salesforce_error_text,
    sobject,
    soql_datetime,
)
from src.models import CatalogObjectCoverage, CatalogRecord
from src.sync import SyncJob, TickResult

logger = logging.getLogger(__name__)

SYNC_TYPE = "catalog"
TICK_BUDGET_SECONDS = 12
WATERMARK_OVERLAP = timedelta(minutes=5)
SYSTEM_FIELDS = ("Id", "LastModifiedDate", "SystemModstamp")


def _previous_run(db: Session) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Watermarks and per-object field lists from the last successful run."""
    job = (
        db.query(SyncJob)
        .filter(SyncJob.sync_type == SYNC_TYPE, SyncJob.status == "success")
        .order_by(SyncJob.finished_at.desc())
        .first()
    )
    if job is None:
        return {}, {}
    cursor = job.cursor or {}
    marks = cursor.get("watermarks") or {}
    field_sets = cursor.get("field_sets") or {}
    return (
        {k: v for k, v in marks.items() if isinstance(v, str)},
        {k: list(v) for k, v in field_sets.items() if isinstance(v, list)},
    )


def _init_cursor(db: Session, cursor: dict[str, Any]) -> dict[str, Any]:
    force_full = bool(cursor.get("force_full"))
    prev_marks, prev_fields = ({}, {}) if force_full else _previous_run(db)
    started = datetime.now(UTC) - WATERMARK_OVERLAP
    return {
        "initialized": True,
        "mode": "full" if force_full else "incremental",
        "token": str(uuid.uuid4()),
        "run_started": started.isoformat(),
        "prev_watermarks": prev_marks,
        "prev_field_sets": prev_fields,
        "watermarks": {},
        "field_sets": {},
        "idx": 0,
        "next_url": None,
        "filtered": False,
        "fields": [],
    }


def _save_coverage(
    db: Session,
    obj: CatalogObject,
    status: str,
    *,
    sf_count: int | None = None,
    missing: list[str] | None = None,
    detail: str | None = None,
) -> None:
    cached = 0
    if obj.mapped and status in ("blocked", "not_available"):
        # Never keep showing data the connector can no longer read.
        db.execute(
            delete(CatalogRecord).where(CatalogRecord.object_api_name == obj.api_name)
        )
    if obj.mapped:
        cached = (
            db.scalar(
                select(func.count())
                .select_from(CatalogRecord)
                .where(CatalogRecord.object_api_name == obj.api_name)
            )
            or 0
        )
    values = {
        "object_api_name": obj.api_name,
        "label": obj.label,
        "section": obj.section,
        "mapped": obj.mapped,
        "status": status,
        "salesforce_count": sf_count,
        "cached_count": cached,
        "missing_fields": missing or [],
        "detail": detail,
        "checked_at": func.now(),
    }
    stmt = insert(CatalogObjectCoverage).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["object_api_name"],
        set_={k: v for k, v in values.items() if k != "object_api_name"},
    )
    db.execute(stmt)


def _upsert_records(
    db: Session, obj: CatalogObject, records: list[dict[str, Any]], token: str
) -> int:
    rows = []
    for rec in records:
        data = {k: v for k, v in dict(rec).items() if k != "attributes"}
        rows.append(
            {
                "sf_id": data["Id"],
                "object_api_name": obj.api_name,
                "name": data.get(obj.name_field) if obj.name_field else None,
                "code": data.get(obj.code_field) if obj.code_field else None,
                "fields": data,
                "sf_last_modified": parse_sf_datetime(data.get("LastModifiedDate")),
                "sf_system_modstamp": parse_sf_datetime(data.get("SystemModstamp")),
                "sync_token": token,
            }
        )
    if not rows:
        return 0
    stmt = insert(CatalogRecord).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["sf_id"],
        set_={
            "object_api_name": stmt.excluded.object_api_name,
            "name": stmt.excluded.name,
            "code": stmt.excluded.code,
            "fields": stmt.excluded.fields,
            "sf_last_modified": stmt.excluded.sf_last_modified,
            "sf_system_modstamp": stmt.excluded.sf_system_modstamp,
            "sync_token": stmt.excluded.sync_token,
            "synced_at": func.now(),
        },
    )
    db.execute(stmt)
    return len(rows)


def _start_object(
    db: Session, sf: Salesforce, obj: CatalogObject, state: dict[str, Any]
) -> dict[str, Any] | None:
    """Check metadata/visibility; return the first query page or None to skip."""
    try:
        describe = sobject(sf, obj.api_name).describe()
    except SalesforceResourceNotFound:
        _save_coverage(
            db,
            obj,
            "not_available",
            detail=f"{obj.api_name} is not present in this org or not visible to the connector user.",
        )
        return None
    except SalesforceRefusedRequest as exc:
        _save_coverage(db, obj, "blocked", detail=salesforce_error_text(exc))
        return None

    if not describe.get("queryable", False):
        _save_coverage(
            db,
            obj,
            "blocked",
            detail=f"{obj.api_name} exists but is not queryable for the connector user (object permission 'Read' missing).",
        )
        return None

    try:
        sf_count = int(sf.query(f"SELECT COUNT() FROM {obj.api_name}")["totalSize"])
    except (SalesforceMalformedRequest, SalesforceRefusedRequest) as exc:
        _save_coverage(db, obj, "blocked", detail=salesforce_error_text(exc))
        return None

    if not obj.mapped:
        _save_coverage(
            db,
            obj,
            "not_mapped",
            sf_count=sf_count,
            detail="Readable in Salesforce; not shown in this app yet.",
        )
        return None

    available = {f["name"] for f in describe["fields"]}
    wanted = [f for f in obj.fields if f not in SYSTEM_FIELDS]
    missing = [f for f in wanted if f not in available]
    select_fields = [f for f in SYSTEM_FIELDS if f in available] + [
        f for f in wanted if f in available
    ]
    state["fields"] = missing
    state["sf_count"] = sf_count

    where = ""
    state["select_fields"] = select_fields
    mark = state["prev_watermarks"].get(obj.api_name)
    prev_fields = state.get("prev_field_sets", {}).get(obj.api_name)
    state["filtered"] = False
    # Incremental only when the same fields were read last time; a newly
    # visible or newly mapped field needs a full read to backfill old rows.
    if mark and prev_fields == select_fields and "SystemModstamp" in available:
        where = f" WHERE SystemModstamp > {soql_datetime(datetime.fromisoformat(mark))}"
        state["filtered"] = True

    soql = f"SELECT {', '.join(select_fields)} FROM {obj.api_name}{where} ORDER BY Id"
    try:
        return sf.query(soql)
    except (SalesforceMalformedRequest, SalesforceRefusedRequest) as exc:
        _save_coverage(
            db,
            obj,
            "blocked",
            sf_count=sf_count,
            missing=missing,
            detail=salesforce_error_text(exc),
        )
        return None


def _finish_object(db: Session, obj: CatalogObject, state: dict[str, Any]) -> None:
    if not state["filtered"] or state.get("sf_count") == 0:
        # Unfiltered read: anything not touched by this run is gone in Salesforce.
        db.execute(
            delete(CatalogRecord).where(
                CatalogRecord.object_api_name == obj.api_name,
                (CatalogRecord.sync_token != state["token"])
                | CatalogRecord.sync_token.is_(None),
            )
        )
    db.flush()
    sf_count = state.get("sf_count")
    cached = (
        db.scalar(
            select(func.count())
            .select_from(CatalogRecord)
            .where(CatalogRecord.object_api_name == obj.api_name)
        )
        or 0
    )
    detail = None
    if sf_count is not None and cached != sf_count:
        detail = (
            f"Cache holds {cached} records but Salesforce reports {sf_count}. "
            "Run a full refresh to remove records deleted in Salesforce."
        )
    missing = state.get("fields") or []
    if missing:
        hidden = f"Fields not returned by the Salesforce describe for the connector user: {', '.join(missing)}."
        detail = f"{detail} {hidden}" if detail else hidden
    status = "empty" if sf_count == 0 else "synced"
    _save_coverage(db, obj, status, sf_count=sf_count, missing=missing, detail=detail)
    state["watermarks"][obj.api_name] = state["run_started"]
    state.setdefault("field_sets", {})[obj.api_name] = state.get("select_fields", [])


def catalog_tick(db: Session, cursor: dict[str, Any]) -> TickResult:
    state = dict(cursor) if cursor.get("initialized") else _init_cursor(db, cursor)
    sf = connect()
    started = time.monotonic()
    added = 0

    while state["idx"] < len(ALL_OBJECTS):
        if time.monotonic() - started > TICK_BUDGET_SECONDS:
            break
        obj = ALL_OBJECTS[state["idx"]]
        try:
            if state.get("next_url"):
                page = sf.query_more(str(state["next_url"]), identifier_is_url=True)
            else:
                page = _start_object(db, sf, obj, state)
        except SalesforceError as exc:
            text = salesforce_error_text(exc)
            if "REQUEST_LIMIT_EXCEEDED" in text:
                return TickResult(
                    new_cursor=state,
                    records_added=added,
                    failure_reason=f"Salesforce API limit reached; retry later. {text}",
                )
            raise

        if page is None:
            db.commit()
            state["idx"] += 1
            state["next_url"] = None
            continue

        added += _upsert_records(db, obj, page.get("records") or [], state["token"])
        if page.get("done", True):
            _finish_object(db, obj, state)
            state["idx"] += 1
            state["next_url"] = None
        else:
            state["next_url"] = page.get("nextRecordsUrl")
        db.commit()

    # Only objects read to completion this run get a watermark; a skipped or
    # blocked object is fully re-read the next time it becomes readable.
    done = state["idx"] >= len(ALL_OBJECTS)
    elapsed = time.monotonic() - started
    logger.info(
        "catalog sync tick: %s records in %.1fs (object %s/%s)",
        added,
        elapsed,
        state["idx"],
        len(ALL_OBJECTS),
    )
    return TickResult(new_cursor=state, records_added=added, done=done)
