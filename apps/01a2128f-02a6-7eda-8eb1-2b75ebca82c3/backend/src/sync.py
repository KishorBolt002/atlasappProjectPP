"""UI-driven chunked sync runner.

The browser drives the sync by repeatedly calling /{id}/tick. Each tick
atomically claims the row with a 90s lease (auto-healing any stale lease),
runs one bounded chunk via tick_fn, and writes the result with an
attempt_id guard so a zombie tick can't clobber a successor.

The UI must drive its "Syncing..." indicator from local React state, NOT
from the database `status` field. See the building-data-syncs skill.
"""

import json
import logging
import time
from collections.abc import Callable
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import DateTime, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, Session, mapped_column

from src.database import Base
from src.dependencies import get_db

LEASE_SECONDS = 90
CONTENDED_BACKOFF_SECONDS = 1
Status = Literal["pending", "running", "success", "failed"]
logger = logging.getLogger(__name__)


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    sync_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[Status] = mapped_column(
        String(32), nullable=False, server_default=text("'pending'")
    )
    cursor: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    attempt: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    attempt_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    records_synced: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        # At most one active job per sync_type. Terminal rows (success/failed)
        # accumulate freely; only pending/running participate in uniqueness.
        Index(
            "uq_sync_jobs_active",
            "sync_type",
            unique=True,
            postgresql_where=text("status IN ('pending', 'running')"),
        ),
        {
            "info": {
                "ontology_ignore": "Internal sync progress, cursor, and execution lease"
            }
        },
    )


class TickResult(BaseModel):
    """One bounded chunk of work. Must be idempotent — retried chunks
    re-write the same destination rows safely via ON CONFLICT DO UPDATE.
    """

    # None means "leave the saved cursor as-is" — needed for legitimate
    # no-progress ticks (rate-limit backoff, async-source polling) where
    # we'd otherwise clobber a job id / watermark / provider token.
    new_cursor: dict[str, Any] | None = None
    records_added: int = 0
    done: bool = False
    failure_reason: str | None = None


class SyncJobView(BaseModel):
    id: UUID
    status: Status
    records_synced: int
    finished: bool
    failure_reason: str | None = None
    finished_at: datetime | None = None


def _view(job: SyncJob) -> SyncJobView:
    return SyncJobView(
        id=job.id,
        status=job.status,
        records_synced=job.records_synced,
        finished=job.status in ("success", "failed"),
        failure_reason=job.failure_reason,
        finished_at=job.finished_at,
    )


def make_sync_router(
    sync_type: str,
    tick_fn: Callable[[Session, dict[str, Any]], TickResult],
) -> APIRouter:
    """Build /start and /{id}/tick routes for one sync type.

    tick_fn(db, cursor) runs ~5-15s of bounded work per call (hard cap 30s,
    lease window 90s). Must be idempotent.
    """
    if not sync_type or not sync_type.replace("_", "").isalnum():
        raise ValueError(f"sync_type must be alphanumeric/underscore: {sync_type!r}")

    router = APIRouter()

    @router.post("/start", response_model=SyncJobView, status_code=202)
    def start(db: Annotated[Session, Depends(get_db)]) -> SyncJobView:
        # Partial unique index keeps at most one (pending|running) row per sync_type;
        # ON CONFLICT DO NOTHING means a concurrent caller's row wins and we just fetch it.
        db.execute(
            text(
                "INSERT INTO sync_jobs (id, sync_type) VALUES (:id, :sync_type) "
                "ON CONFLICT DO NOTHING"
            ),
            {"id": uuid4(), "sync_type": sync_type},
        )
        db.commit()
        job = (
            db.query(SyncJob)
            .filter(
                SyncJob.sync_type == sync_type,
                SyncJob.status.in_(["pending", "running"]),
            )
            .one_or_none()
        )
        if job is None:
            # Race: a concurrent caller's job terminated between our INSERT and SELECT.
            raise HTTPException(409, "Sync state changed concurrently; retry.")
        return _view(job)

    @router.post("/{job_id}/tick", response_model=SyncJobView)
    def tick(job_id: UUID, db: Annotated[Session, Depends(get_db)]) -> SyncJobView:
        # Atomic claim — also reclaims rows whose lease has expired (auto-heal).
        attempt_id = uuid4()
        claimed = db.execute(
            text("""
                UPDATE sync_jobs
                SET status = 'running',
                    attempt = attempt + 1,
                    attempt_id = :attempt_id,
                    lease_expires_at = now() + make_interval(secs => :lease_secs),
                    started_at = COALESCE(started_at, now()),
                    updated_at = now()
                WHERE id = :job_id
                  AND sync_type = :sync_type
                  AND (
                    status = 'pending'
                    OR (status = 'running' AND (lease_expires_at IS NULL OR lease_expires_at < now()))
                  )
                RETURNING attempt_id, cursor
            """),
            {
                "job_id": str(job_id),
                "sync_type": sync_type,
                "attempt_id": str(attempt_id),
                "lease_secs": LEASE_SECONDS,
            },
        ).first()
        db.commit()

        if claimed is None:
            # Not found, wrong type, terminal, or another tick holds the lease.
            job = db.query(SyncJob).filter(SyncJob.id == job_id).one_or_none()
            if job is None or job.sync_type != sync_type:
                raise HTTPException(404, "Sync job not found")
            # Lease held by a concurrent tick (e.g. user opened a second tab).
            # Back off briefly so the browser tick loop doesn't hammer at
            # network round-trip speed waiting for the lease to clear.
            if job.status == "running":
                time.sleep(CONTENDED_BACKOFF_SECONDS)
            return _view(job)

        cursor = claimed.cursor or {}
        try:
            result = tick_fn(db, cursor)
        except Exception as exc:
            logger.exception(
                "sync tick raised for sync_type=%s job_id=%s", sync_type, job_id
            )
            db.rollback()
            result = TickResult(
                new_cursor=cursor,
                failure_reason=f"{type(exc).__name__}: {exc}"[:1000],
            )

        new_status: Status = (
            "failed"
            if result.failure_reason
            else "success"
            if result.done
            else "running"
        )
        finished = new_status in ("success", "failed")

        # Single UPDATE handles failure / done / continue. The attempt_id guard
        # makes a zombie tick (whose lease expired) a silent no-op. lease_expires_at
        # is cleared every time so the next /tick from the browser can re-claim
        # immediately — the lease only exists to fence concurrent ticks.
        db.execute(
            text("""
                UPDATE sync_jobs
                SET status = :status,
                    records_synced = records_synced + :added,
                    cursor = (:cursor)::jsonb,
                    failure_reason = :reason,
                    finished_at = CASE WHEN :finished THEN now() ELSE finished_at END,
                    lease_expires_at = NULL,
                    updated_at = now()
                WHERE id = :job_id AND attempt_id = :attempt_id
            """),
            {
                "job_id": str(job_id),
                "attempt_id": str(attempt_id),
                "status": new_status,
                "added": result.records_added,
                "cursor": json.dumps(
                    result.new_cursor if result.new_cursor is not None else cursor
                ),
                "reason": result.failure_reason,
                "finished": finished,
            },
        )
        db.commit()

        job = db.query(SyncJob).filter(SyncJob.id == job_id).one()
        return _view(job)

    return router
