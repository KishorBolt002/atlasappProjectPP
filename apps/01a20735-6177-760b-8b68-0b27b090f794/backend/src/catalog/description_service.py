"""Confirmed, concurrency-checked write-back of Product2.Description.

Order of checks for an update (nothing is written unless all pass):
1. explicit confirmation flag
2. the exact product ID exists in the synced catalog cache as a Product2
3. field metadata from a live describe: Description is updateable, length fits
4. live read: the record still exists and LastModifiedDate equals what the
   user reviewed (otherwise 409 with no write)
5. the proposed text differs from the current Salesforce value
6. PATCH with If-Unmodified-Since so Salesforce itself rejects a race (412)
7. re-read and verify the stored value; refresh the cache row
Every attempt past step 3 is recorded in description_changes.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException
from simple_salesforce.exceptions import SalesforceError
from sqlalchemy.orm import Session

from src.catalog.read_service import get_cached_product
from src.catalog.salesforce_gateway import (
    FieldMetadata,
    LiveProduct,
    ProductGateway,
    WriteConflictError,
    salesforce_error_text,
)
from src.models import CatalogRecord, DescriptionChange
from src.schemas import (
    DescriptionPreview,
    DescriptionUpdateRequest,
    DescriptionUpdateResult,
    FieldMetadataOut,
    LiveDescription,
)


def normalize(text: str | None) -> str | None:
    """Salesforce stores textarea newlines as \\n; blank text clears the field."""
    if text is None:
        return None
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text if text.strip() else None


def _same(a: str | None, b: str | None) -> bool:
    return (normalize(a) or "") == (normalize(b) or "")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).replace(microsecond=0)


def _sf_failure(action: str, exc: SalesforceError) -> HTTPException:
    return HTTPException(
        status_code=502,
        detail=f"Salesforce rejected the {action}: {salesforce_error_text(exc)}",
    )


def _require_cached(db: Session, sf_id: str) -> CatalogRecord:
    rec = get_cached_product(db, sf_id)
    if rec is None:
        raise HTTPException(
            status_code=404,
            detail=f"No product with Salesforce ID {sf_id} in the synced catalog. Run a catalog sync or check the ID.",
        )
    return rec


def _field(gateway: ProductGateway) -> FieldMetadata:
    try:
        meta = gateway.description_field()
    except SalesforceError as exc:
        raise _sf_failure("metadata request", exc) from exc
    if meta is None:
        raise HTTPException(
            status_code=503,
            detail="Product2.Description is not visible to the Salesforce connector user (field-level security).",
        )
    return meta


def _live(gateway: ProductGateway, sf_id: str) -> LiveProduct:
    try:
        live = gateway.read_product(sf_id)
    except SalesforceError as exc:
        raise _sf_failure("read", exc) from exc
    if live is None or live.sf_id != sf_id:
        raise HTTPException(
            status_code=404,
            detail=f"Salesforce returned no Product2 record with ID {sf_id}; it may have been deleted or hidden from the connector user.",
        )
    return live


def _refresh_cache(rec: CatalogRecord, live: LiveProduct) -> bool:
    fields = dict(rec.fields or {})
    stale = not _same(fields.get("Description"), live.description) or (
        rec.sf_last_modified is None
        or _utc(rec.sf_last_modified) != _utc(live.last_modified)
    )
    fields["Description"] = live.description
    fields["LastModifiedDate"] = live.last_modified.strftime(
        "%Y-%m-%dT%H:%M:%S.000+0000"
    )
    if live.name is not None:
        fields["Name"] = live.name
        rec.name = live.name
    rec.fields = fields
    rec.sf_last_modified = live.last_modified
    if live.system_modstamp is not None:
        rec.sf_system_modstamp = live.system_modstamp
    return stale


def _field_out(meta: FieldMetadata) -> FieldMetadataOut:
    return FieldMetadataOut(
        object_api_name=meta.object_api_name,
        field_api_name=meta.field_api_name,
        label=meta.label,
        type=meta.type,
        max_length=meta.length,
        updateable=meta.updateable,
    )


def live_description(
    db: Session, gateway: ProductGateway, sf_id: str
) -> LiveDescription:
    rec = _require_cached(db, sf_id)
    meta = _field(gateway)
    live = _live(gateway, sf_id)
    cached_description = (rec.fields or {}).get("Description")
    stale = _refresh_cache(rec, live)
    db.commit()
    return LiveDescription(
        product_sf_id=sf_id,
        product_name=live.name,
        current_description=live.description,
        last_modified=live.last_modified,
        last_modified_by=live.last_modified_by,
        field=_field_out(meta),
        cached_description=cached_description,
        cache_was_stale=stale,
    )


def _problems(
    meta: FieldMetadata, current: str | None, proposed: str | None
) -> list[str]:
    problems = []
    if not meta.updateable:
        problems.append(
            "Salesforce reports Product2.Description is not editable for the connector user."
        )
    length = len(proposed or "")
    if length > meta.length:
        problems.append(
            f"The proposed text is {length} characters; Salesforce allows at most {meta.length}."
        )
    if _same(current, proposed):
        problems.append(
            "The proposed text is the same as the current Salesforce description."
        )
    return problems


def preview(
    db: Session, gateway: ProductGateway, sf_id: str, proposed_raw: str
) -> DescriptionPreview:
    rec = _require_cached(db, sf_id)
    meta = _field(gateway)
    live = _live(gateway, sf_id)
    _refresh_cache(rec, live)
    db.commit()
    proposed = normalize(proposed_raw)
    problems = _problems(meta, live.description, proposed)
    return DescriptionPreview(
        product_sf_id=sf_id,
        product_name=live.name,
        current_description=live.description,
        proposed_description=proposed or "",
        changed=not _same(live.description, proposed),
        clears_description=proposed is None and bool(normalize(live.description)),
        proposed_length=len(proposed or ""),
        max_length=meta.length,
        writable=meta.updateable,
        last_modified=live.last_modified,
        problems=problems,
        can_apply=not problems,
    )


def _audit(
    db: Session,
    *,
    rec: CatalogRecord,
    previous: str | None,
    proposed: str | None,
    expected: datetime,
    outcome: str,
    user_email: str,
    error: str | None = None,
    after: datetime | None = None,
) -> DescriptionChange:
    change = DescriptionChange(
        product_sf_id=rec.sf_id,
        product_name=rec.name,
        previous_description=previous,
        proposed_description=proposed or "",
        expected_last_modified=expected,
        outcome=outcome,
        error_detail=error,
        salesforce_last_modified_after=after,
        requested_by=user_email,
    )
    db.add(change)
    db.commit()
    return change


def apply_update(
    db: Session,
    gateway: ProductGateway,
    sf_id: str,
    request: DescriptionUpdateRequest,
    user_email: str,
) -> DescriptionUpdateResult:
    if request.confirm is not True:
        raise HTTPException(
            status_code=422,
            detail="Set confirm to true after reviewing the current and proposed description.",
        )
    rec = _require_cached(db, sf_id)
    meta = _field(gateway)
    proposed = normalize(request.proposed_description)
    expected = _utc(request.expected_last_modified)

    if not meta.updateable:
        raise HTTPException(
            status_code=403,
            detail="Salesforce reports Product2.Description is not editable for the connector user.",
        )
    if len(proposed or "") > meta.length:
        raise HTTPException(
            status_code=422,
            detail=f"The proposed text is {len(proposed or '')} characters; Salesforce allows at most {meta.length}.",
        )

    live = _live(gateway, sf_id)
    if _utc(live.last_modified) != expected:
        _refresh_cache(rec, live)
        _audit(
            db,
            rec=rec,
            previous=live.description,
            proposed=proposed,
            expected=expected,
            outcome="conflict",
            user_email=user_email,
            error=f"Record changed in Salesforce at {live.last_modified.isoformat()} (by {live.last_modified_by or 'unknown'}) after it was reviewed.",
            after=live.last_modified,
        )
        raise HTTPException(
            status_code=409,
            detail=(
                "This product changed in Salesforce after you loaded it "
                f"(last modified {live.last_modified.isoformat()} by {live.last_modified_by or 'unknown'}). "
                "Nothing was saved. Reload the current description and review your change again."
            ),
        )
    if _same(live.description, proposed):
        raise HTTPException(
            status_code=422,
            detail="The proposed text is the same as the current Salesforce description; nothing to save.",
        )

    previous = live.description
    try:
        gateway.write_description(sf_id, proposed, live.last_modified)
    except WriteConflictError as exc:
        _audit(
            db,
            rec=rec,
            previous=previous,
            proposed=proposed,
            expected=expected,
            outcome="conflict",
            user_email=user_email,
            error=str(exc),
        )
        raise HTTPException(
            status_code=409,
            detail="Salesforce reports the product changed while saving (HTTP 412). Nothing was saved. Reload and try again.",
        ) from exc
    except SalesforceError as exc:
        message = salesforce_error_text(exc)
        _audit(
            db,
            rec=rec,
            previous=previous,
            proposed=proposed,
            expected=expected,
            outcome="failed",
            user_email=user_email,
            error=message,
        )
        raise HTTPException(
            status_code=502, detail=f"Salesforce rejected the update: {message}"
        ) from exc

    try:
        saved = gateway.read_product(sf_id)
    except SalesforceError as exc:
        _audit(
            db,
            rec=rec,
            previous=previous,
            proposed=proposed,
            expected=expected,
            outcome="unverified",
            user_email=user_email,
            error=f"Write accepted, but reloading failed: {salesforce_error_text(exc)}",
        )
        raise HTTPException(
            status_code=502,
            detail="Salesforce accepted the update but the saved value could not be reloaded to verify it. Reload the product to check.",
        ) from exc
    if saved is None or not _same(saved.description, proposed):
        _audit(
            db,
            rec=rec,
            previous=previous,
            proposed=proposed,
            expected=expected,
            outcome="unverified",
            user_email=user_email,
            error="Reloaded value differs from the proposed text.",
            after=saved.last_modified if saved else None,
        )
        raise HTTPException(
            status_code=502,
            detail="Salesforce accepted the update but the reloaded description differs from what was sent. Reload the product to review.",
        )

    _refresh_cache(rec, saved)
    change = _audit(
        db,
        rec=rec,
        previous=previous,
        proposed=proposed,
        expected=expected,
        outcome="applied",
        user_email=user_email,
        after=saved.last_modified,
    )
    return DescriptionUpdateResult(
        change_id=change.id,
        product_sf_id=sf_id,
        product_name=saved.name,
        previous_description=previous,
        description=saved.description,
        last_modified=saved.last_modified,
        verified=True,
    )
