"""Tick-driven catalog sync routes, admin-only."""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.auth import require_role
from src.catalog.sync_catalog import SYNC_TYPE, catalog_tick
from src.dependencies import get_db
from src.sync import SyncJob, SyncJobView, _view, make_sync_router

router = APIRouter(
    prefix="/api/sync/catalog",
    tags=["catalog-sync"],
    dependencies=[Depends(require_role("admin"))],
)


@router.post("/start-full", response_model=SyncJobView, status_code=202)
def start_full(db: Annotated[Session, Depends(get_db)]) -> SyncJobView:
    """Start a full refresh: re-read everything and drop records deleted in Salesforce."""
    db.execute(
        text(
            "INSERT INTO sync_jobs (id, sync_type, cursor) "
            "VALUES (:id, :sync_type, CAST(:cursor AS jsonb)) ON CONFLICT DO NOTHING"
        ),
        {"id": uuid4(), "sync_type": SYNC_TYPE, "cursor": '{"force_full": true}'},
    )
    db.commit()
    job = (
        db.query(SyncJob)
        .filter(
            SyncJob.sync_type == SYNC_TYPE, SyncJob.status.in_(["pending", "running"])
        )
        .one_or_none()
    )
    if job is None:
        raise HTTPException(409, "Sync state changed concurrently; retry.")
    cursor = job.cursor or {}
    is_full = bool(cursor.get("force_full")) or cursor.get("mode") == "full"
    if not is_full:
        if job.status == "pending" and not cursor.get("initialized"):
            # Not started yet: turn it into a full refresh.
            job.cursor = {"force_full": True}
            db.commit()
            db.refresh(job)
        else:
            raise HTTPException(
                409,
                "A Sync changes run is still in progress. Choose Sync changes to let it "
                "finish, then run Full refresh.",
            )
    return _view(job)


router.include_router(make_sync_router(SYNC_TYPE, catalog_tick))
