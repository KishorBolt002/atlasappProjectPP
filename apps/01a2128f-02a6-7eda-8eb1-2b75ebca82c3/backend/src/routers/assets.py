"""Asset endpoints: cache-backed reads plus the tick-driven Salesforce sync."""

import logging
import math
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from src.clients.connectors.salesforce_client import get_salesforce_client
from src.dependencies import get_db
from src.models import CachedAsset
from src.schemas import AssetOut, AssetSummary
from src.sync import SyncJob, TickResult, make_sync_router

logger = logging.getLogger(__name__)

SYNC_TYPE = "assets"
ASSET_LIMIT = 10
ASSET_SOQL = (
    "SELECT Id, Name, Account.Name, ProductCode, ProductFamily, "
    "TotalLifecycleAmount, CurrentMrr, LifecycleStartDate, LifecycleEndDate, "
    "RenewalTerm, RenewalTermUnit, Owner.Name, CreatedDate "
    "FROM Asset ORDER BY CreatedDate DESC, Id DESC LIMIT 10"
)


class AssetValidationError(ValueError):
    """A Salesforce record cannot be represented under the API contract."""


def _renewal_term(sf_id: str, value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AssetValidationError(
            f"Asset {sf_id} has a non-numeric RenewalTerm {value!r}; "
            "expected a whole number or empty."
        )
    if isinstance(value, float) and (
        not math.isfinite(value) or not value.is_integer()
    ):
        raise AssetValidationError(
            f"Asset {sf_id} has RenewalTerm {value!r}, which is not a whole number; "
            "the sync was stopped so the value is not rounded. Previous data is unchanged."
        )
    return int(value)


def _money(sf_id: str, field: str, value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AssetValidationError(
            f"Asset {sf_id} has a non-numeric {field} {value!r}."
        )
    if isinstance(value, float) and not math.isfinite(value):
        raise AssetValidationError(f"Asset {sf_id} has an invalid {field} {value!r}.")
    return Decimal(str(value))


def _datetime(sf_id: str, field: str, value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%dT%H:%M:%S.%f%z")
    except ValueError as exc:
        raise AssetValidationError(
            f"Asset {sf_id} has an invalid {field} {value!r}."
        ) from exc


def _date(sf_id: str, field: str, value: Any) -> date | None:
    """Lifecycle dates are Salesforce datetimes in this org; keep the UTC calendar date.

    Plain YYYY-MM-DD values (date-typed orgs) are accepted too.
    """
    if value is None:
        return None
    raw = str(value)
    if len(raw) == 10:
        try:
            return date.fromisoformat(raw)
        except ValueError as exc:
            raise AssetValidationError(
                f"Asset {sf_id} has an invalid {field} {value!r}."
            ) from exc
    parsed = _datetime(sf_id, field, value)
    return parsed.astimezone(UTC).date() if parsed is not None else None


def _related_name(record: dict[str, Any], relation: str) -> str | None:
    related = record.get(relation)
    if isinstance(related, dict):
        name = related.get("Name")
        return str(name) if name is not None else None
    return None


def _to_row(record: dict[str, Any]) -> dict[str, Any]:
    sf_id = record.get("Id")
    if not sf_id:
        raise AssetValidationError("Salesforce returned an Asset without an Id.")
    sf_id = str(sf_id)
    name = record.get("Name")
    if name is None:
        raise AssetValidationError(f"Asset {sf_id} has no Name.")
    return {
        "sf_id": sf_id,
        "name": str(name),
        "account_name": _related_name(record, "Account"),
        "product_code": record.get("ProductCode"),
        "product_family": record.get("ProductFamily"),
        "current_mrr": _money(sf_id, "CurrentMrr", record.get("CurrentMrr")),
        "total_lifecycle_amount": _money(
            sf_id, "TotalLifecycleAmount", record.get("TotalLifecycleAmount")
        ),
        "lifecycle_start_date": _date(
            sf_id, "LifecycleStartDate", record.get("LifecycleStartDate")
        ),
        "lifecycle_end_date": _date(
            sf_id, "LifecycleEndDate", record.get("LifecycleEndDate")
        ),
        "renewal_term": _renewal_term(sf_id, record.get("RenewalTerm")),
        "renewal_term_unit": record.get("RenewalTermUnit"),
        "owner_name": _related_name(record, "Owner"),
        "sf_created_date": _datetime(sf_id, "CreatedDate", record.get("CreatedDate")),
    }


def _assets_tick(db: Session, cursor: dict[str, Any]) -> TickResult:
    """Replace the cache with the latest 10 Assets in one transaction.

    Salesforce is only read (SOQL query). Every record is validated before the
    cache is touched; the runner commits the cache replacement together with
    the job's success status, so the displayed set, the summary, and the last
    successful sync time always change together.
    """
    sf = get_salesforce_client()
    result = sf.query(ASSET_SOQL)
    records = result.get("records", [])
    try:
        rows = [_to_row(record) for record in records]
    except AssetValidationError as exc:
        logger.warning("assets sync rejected Salesforce data: %s", exc)
        return TickResult(new_cursor=cursor, failure_reason=str(exc))

    new_ids = [row["sf_id"] for row in rows]
    if new_ids:
        db.query(CachedAsset).filter(CachedAsset.sf_id.notin_(new_ids)).delete(
            synchronize_session=False
        )
    else:
        db.query(CachedAsset).delete(synchronize_session=False)

    for row in rows:
        db.execute(
            text("""
                INSERT INTO cached_assets (
                    sf_id, name, account_name, product_code, product_family,
                    current_mrr, total_lifecycle_amount, lifecycle_start_date,
                    lifecycle_end_date, renewal_term, renewal_term_unit,
                    owner_name, sf_created_date, synced_at
                ) VALUES (
                    :sf_id, :name, :account_name, :product_code, :product_family,
                    :current_mrr, :total_lifecycle_amount, :lifecycle_start_date,
                    :lifecycle_end_date, :renewal_term, :renewal_term_unit,
                    :owner_name, :sf_created_date, now()
                )
                ON CONFLICT (sf_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    account_name = EXCLUDED.account_name,
                    product_code = EXCLUDED.product_code,
                    product_family = EXCLUDED.product_family,
                    current_mrr = EXCLUDED.current_mrr,
                    total_lifecycle_amount = EXCLUDED.total_lifecycle_amount,
                    lifecycle_start_date = EXCLUDED.lifecycle_start_date,
                    lifecycle_end_date = EXCLUDED.lifecycle_end_date,
                    renewal_term = EXCLUDED.renewal_term,
                    renewal_term_unit = EXCLUDED.renewal_term_unit,
                    owner_name = EXCLUDED.owner_name,
                    sf_created_date = EXCLUDED.sf_created_date,
                    synced_at = EXCLUDED.synced_at
            """),
            row,
        )
    # No commit here: the runner's job-status UPDATE commits in the same transaction.
    logger.info("assets sync fetched %d records", len(rows))
    return TickResult(new_cursor={}, records_added=len(rows), done=True)


sync_router = make_sync_router(SYNC_TYPE, _assets_tick)

router = APIRouter(prefix="/api/assets", tags=["assets"])


def _out(asset: CachedAsset) -> AssetOut:
    return AssetOut(
        id=asset.sf_id,
        name=asset.name,
        account=asset.account_name,
        product_code=asset.product_code,
        family=asset.product_family,
        mrr=float(asset.current_mrr) if asset.current_mrr is not None else None,
        lifecycle_value=(
            float(asset.total_lifecycle_amount)
            if asset.total_lifecycle_amount is not None
            else None
        ),
        lifecycle_start=asset.lifecycle_start_date,
        lifecycle_end=asset.lifecycle_end_date,
        renewal_term=asset.renewal_term,
        renewal_unit=asset.renewal_term_unit,
        owner=asset.owner_name,
        created_date=asset.sf_created_date,
    )


@router.get("/", response_model=list[AssetOut])
def list_assets(db: Annotated[Session, Depends(get_db)]) -> list[AssetOut]:
    assets = (
        db.query(CachedAsset)
        .order_by(
            CachedAsset.sf_created_date.desc().nulls_last(), CachedAsset.sf_id.desc()
        )
        .limit(ASSET_LIMIT)
        .all()
    )
    return [_out(asset) for asset in assets]


@router.get("/summary", response_model=AssetSummary)
def asset_summary(db: Annotated[Session, Depends(get_db)]) -> AssetSummary:
    count, total_lifecycle, total_mrr = db.query(
        func.count(CachedAsset.id),
        func.sum(CachedAsset.total_lifecycle_amount),
        func.sum(CachedAsset.current_mrr),
    ).one()
    synced_at = (
        db.query(func.max(SyncJob.finished_at))
        .filter(SyncJob.sync_type == SYNC_TYPE, SyncJob.status == "success")
        .scalar()
    )
    return AssetSummary(
        asset_count=int(count),
        # Null amounts contribute 0; an empty cache sums to 0.
        total_lifecycle_value=float(total_lifecycle or 0),
        total_mrr=float(total_mrr or 0),
        synced_at=synced_at,
    )


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: str, db: Annotated[Session, Depends(get_db)]) -> AssetOut:
    asset = db.query(CachedAsset).filter(CachedAsset.sf_id == asset_id).one_or_none()
    if asset is None:
        raise HTTPException(
            status_code=404, detail="Asset not found in the local cache"
        )
    return _out(asset)
