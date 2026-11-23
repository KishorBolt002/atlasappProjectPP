"""Mocked write-path tests for the Product2.Description update flow.

No Salesforce calls: every test uses FakeGateway. Database work runs inside an
outer transaction that is rolled back, so nothing persists.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from simple_salesforce.exceptions import SalesforceMalformedRequest
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.catalog import description_service
from src.catalog.salesforce_gateway import (
    FieldMetadata,
    LiveProduct,
    WriteConflictError,
)
from src.database import engine
from src.models import CatalogRecord, DescriptionChange
from src.schemas import DescriptionUpdateRequest

PID = "01tTEST0000000001A"
LAST_MOD = datetime(2026, 11, 7, 9, 53, 6, tzinfo=UTC)
USER = "admin@example.com"


class FakeGateway:
    def __init__(self, description: str | None = "Old text") -> None:
        self.live: LiveProduct | None = LiveProduct(
            sf_id=PID,
            name="Test Product",
            description=description,
            last_modified=LAST_MOD,
            system_modstamp=LAST_MOD,
            last_modified_by="Someone",
        )
        self.field: FieldMetadata | None = FieldMetadata(
            object_api_name="Product2",
            field_api_name="Description",
            label="Product Description",
            type="textarea",
            length=4000,
            updateable=True,
        )
        self.writes: list[tuple[str, str | None, datetime]] = []
        self.write_error: Exception | None = None
        self.store_override: str | None = None
        self.use_override = False

    def read_product(self, sf_id: str) -> LiveProduct | None:
        if self.live is None or sf_id != self.live.sf_id:
            return None
        return self.live

    def description_field(self) -> FieldMetadata | None:
        return self.field

    def write_description(
        self, sf_id: str, description: str | None, unmodified_since: datetime
    ) -> None:
        self.writes.append((sf_id, description, unmodified_since))
        if self.write_error is not None:
            raise self.write_error
        assert self.live is not None
        stored = self.store_override if self.use_override else description
        self.live = replace(
            self.live,
            description=stored,
            last_modified=LAST_MOD + timedelta(minutes=1),
            system_modstamp=LAST_MOD + timedelta(minutes=1),
        )


@pytest.fixture
def db():
    conn = engine.connect()
    outer = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint")
    session.add(
        CatalogRecord(
            sf_id=PID,
            object_api_name="Product2",
            name="Test Product",
            code="TP1",
            fields={
                "Id": PID,
                "Name": "Test Product",
                "Description": "Old text",
                "LastModifiedDate": "2026-11-07T09:53:06.000+0000",
            },
            sf_last_modified=LAST_MOD,
            sf_system_modstamp=LAST_MOD,
        )
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        outer.rollback()
        conn.close()


def req(
    text: str = "New text", expected: datetime = LAST_MOD, confirm: bool = True
) -> DescriptionUpdateRequest:
    return DescriptionUpdateRequest(
        proposed_description=text, expected_last_modified=expected, confirm=confirm
    )


def audits(db: Session) -> list[DescriptionChange]:
    return list(
        db.scalars(
            select(DescriptionChange).where(DescriptionChange.product_sf_id == PID)
        )
    )


def cached(db: Session) -> CatalogRecord:
    rec = db.scalar(select(CatalogRecord).where(CatalogRecord.sf_id == PID))
    assert rec is not None
    return rec


def test_success_writes_once_verifies_and_updates_cache(db):
    gw = FakeGateway()
    result = description_service.apply_update(db, gw, PID, req("New text"), USER)
    assert gw.writes == [(PID, "New text", LAST_MOD)]
    assert result.verified is True
    assert result.description == "New text"
    assert result.previous_description == "Old text"
    assert result.last_modified == LAST_MOD + timedelta(minutes=1)
    rec = cached(db)
    assert rec.fields["Description"] == "New text"
    assert rec.sf_last_modified == LAST_MOD + timedelta(minutes=1)
    [a] = audits(db)
    assert (
        a.outcome == "applied"
        and a.requested_by == USER
        and a.previous_description == "Old text"
    )


def test_confirm_false_rejected_without_write(db):
    gw = FakeGateway()
    with pytest.raises(HTTPException) as e:
        description_service.apply_update(db, gw, PID, req(confirm=False), USER)
    assert e.value.status_code == 422
    assert gw.writes == [] and audits(db) == []


def test_stale_expected_timestamp_conflicts_without_write(db):
    gw = FakeGateway()
    with pytest.raises(HTTPException) as e:
        description_service.apply_update(
            db, gw, PID, req(expected=LAST_MOD - timedelta(days=1)), USER
        )
    assert e.value.status_code == 409
    assert gw.writes == []
    [a] = audits(db)
    assert a.outcome == "conflict"


def test_salesforce_412_maps_to_conflict(db):
    gw = FakeGateway()
    gw.write_error = WriteConflictError("PRECONDITION_FAILED")
    with pytest.raises(HTTPException) as e:
        description_service.apply_update(db, gw, PID, req(), USER)
    assert e.value.status_code == 409
    assert len(gw.writes) == 1
    assert [a.outcome for a in audits(db)] == ["conflict"]
    assert cached(db).fields["Description"] == "Old text"


def test_salesforce_error_surfaces_code_and_audits(db):
    gw = FakeGateway()
    # simple-salesforce annotates content as bytes, but its exception_handler
    # passes the parsed JSON error list, which is what Salesforce returns.
    sf_errors = [
        {
            "errorCode": "FIELD_CUSTOM_VALIDATION_EXCEPTION",
            "message": "Blocked by rule",
            "fields": ["Description"],
        }
    ]
    gw.write_error = SalesforceMalformedRequest(
        "url",
        400,
        "Product2",
        sf_errors,  # ty: ignore[invalid-argument-type]
    )
    with pytest.raises(HTTPException) as e:
        description_service.apply_update(db, gw, PID, req(), USER)
    assert e.value.status_code == 502
    assert "FIELD_CUSTOM_VALIDATION_EXCEPTION" in str(e.value.detail)
    assert "Blocked by rule" in str(e.value.detail)
    [a] = audits(db)
    assert a.outcome == "failed" and "FIELD_CUSTOM_VALIDATION_EXCEPTION" in (
        a.error_detail or ""
    )


def test_unchanged_text_rejected_without_write(db):
    gw = FakeGateway()
    with pytest.raises(HTTPException) as e:
        description_service.apply_update(db, gw, PID, req("Old text"), USER)
    assert e.value.status_code == 422
    assert gw.writes == []


def test_too_long_rejected_without_write(db):
    gw = FakeGateway()
    assert gw.field is not None
    gw.field = replace(gw.field, length=10)
    with pytest.raises(HTTPException) as e:
        description_service.apply_update(db, gw, PID, req("x" * 11), USER)
    assert e.value.status_code == 422
    assert gw.writes == []


def test_field_not_updateable_forbidden(db):
    gw = FakeGateway()
    assert gw.field is not None
    gw.field = replace(gw.field, updateable=False)
    with pytest.raises(HTTPException) as e:
        description_service.apply_update(db, gw, PID, req(), USER)
    assert e.value.status_code == 403
    assert gw.writes == []


def test_reloaded_mismatch_is_unverified(db):
    gw = FakeGateway()
    gw.use_override = True
    gw.store_override = "Something else"
    with pytest.raises(HTTPException) as e:
        description_service.apply_update(db, gw, PID, req(), USER)
    assert e.value.status_code == 502
    [a] = audits(db)
    assert a.outcome == "unverified"


def test_product_not_cached_404(db):
    gw = FakeGateway()
    with pytest.raises(HTTPException) as e:
        description_service.apply_update(db, gw, "01tTEST0000000002A", req(), USER)
    assert e.value.status_code == 404
    assert gw.writes == []


def test_product_missing_in_salesforce_404(db):
    gw = FakeGateway()
    gw.live = None
    with pytest.raises(HTTPException) as e:
        description_service.apply_update(db, gw, PID, req(), USER)
    assert e.value.status_code == 404
    assert gw.writes == []


def test_crlf_normalized_before_write(db):
    gw = FakeGateway()
    description_service.apply_update(db, gw, PID, req("Line one\r\nLine two"), USER)
    assert gw.writes[0][1] == "Line one\nLine two"


def test_crlf_equal_to_current_is_unchanged(db):
    gw = FakeGateway(description="A\nB")
    with pytest.raises(HTTPException) as e:
        description_service.apply_update(db, gw, PID, req("A\r\nB"), USER)
    assert e.value.status_code == 422
    assert gw.writes == []


def test_blank_clears_to_none(db):
    gw = FakeGateway()
    result = description_service.apply_update(db, gw, PID, req("   "), USER)
    assert gw.writes[0][1] is None
    assert result.description is None


def test_preview_reports_problems_and_never_writes(db):
    gw = FakeGateway()
    p = description_service.preview(db, gw, PID, "Old text")
    assert p.changed is False and p.can_apply is False and p.problems
    p2 = description_service.preview(db, gw, PID, "")
    assert p2.clears_description is True and p2.can_apply is True
    p3 = description_service.preview(db, gw, PID, "Fresh")
    assert p3.changed and p3.can_apply and p3.last_modified == LAST_MOD
    assert gw.writes == []


def test_live_description_refreshes_stale_cache(db):
    gw = FakeGateway(description="Changed in Salesforce")
    live = description_service.live_description(db, gw, PID)
    assert live.cache_was_stale is True
    assert live.cached_description == "Old text"
    assert live.current_description == "Changed in Salesforce"
    assert live.field.updateable and live.field.max_length == 4000
    assert cached(db).fields["Description"] == "Changed in Salesforce"
    assert gw.writes == []
