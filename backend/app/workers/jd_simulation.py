"""Celery tasks for JD simulation pipeline."""
from __future__ import annotations

import asyncio
import logging
import uuid

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.jd_simulation import JDSimulationRequest, JDSimulationStatus
from app.models.audit import AuditTrail
from app.engines.jd_simulation_engine import simulate_job_description
from app.engines.client import ClaudeClient
from app.workers.celery_app import celery_app

logger = logging.getLogger("truematch.jd_simulation_tasks")

# Synchronous engine for the worker (same pattern as app/workers/tasks.py)
_sync_engine = None
_SyncSessionLocal: sessionmaker[Session] | None = None


def _sync_database_url() -> str:
    """Derive a synchronous SQLAlchemy URL from the configured async URL."""
    url = settings.database_url
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg")
    return url


def _session_factory() -> sessionmaker[Session]:
    global _sync_engine, _SyncSessionLocal
    if _SyncSessionLocal is None:
        _sync_engine = create_engine(_sync_database_url(), pool_pre_ping=True, future=True)
        _SyncSessionLocal = sessionmaker(bind=_sync_engine, expire_on_commit=False)
    return _SyncSessionLocal


def _audit(db: Session, request_id: uuid.UUID, event_type: str, data: dict) -> AuditTrail:
    """Create an audit trail entry.

    AuditTrail has no JD-simulation FK column, so the request id is recorded
    inside `event_data` rather than as an (invalid) keyword argument.
    """
    entry = AuditTrail(
        event_type=event_type,
        event_data={**(data or {}), "jd_simulation_request_id": str(request_id)},
        actor_type="system",
    )
    db.add(entry)
    db.flush()
    return entry


async def _run_simulation_async(request_id: str) -> dict:
    """Run the (async) JD simulation engine with a fresh async session.

    The engine uses `await self.db.*`, so it needs a real AsyncSession — the
    worker's sync session can't drive it. A fresh async engine per run avoids
    event-loop contamination from the parent process (same pattern as the CV
    analysis worker).
    """
    async_engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True)
    factory = async_sessionmaker(bind=async_engine, expire_on_commit=False)
    try:
        async with factory() as adb:
            req = await adb.get(JDSimulationRequest, uuid.UUID(request_id))
            claude_client = ClaudeClient(api_key=settings.anthropic_api_key)
            result = await simulate_job_description(adb, claude_client, req)
            adb.add(result)
            await adb.flush()
            summary = {
                "result_id": str(result.id),
                "quality_score": result.quality_score,
                "difficulty_score": result.requirement_difficulty_score,
            }
            req.status = JDSimulationStatus.completed
            await adb.commit()
            return summary
    finally:
        await async_engine.dispose()


@celery_app.task(name="app.workers.jd_simulation.process_jd_simulation_task", bind=True, max_retries=2)
def process_jd_simulation_task(self, request_id: str) -> dict:
    """Process a JD simulation request end-to-end.

    This task:
    1. Fetches the JDSimulationRequest from the database
    2. Runs the JD simulation engine
    3. Persists results to JDSimulationResult
    4. Updates the request status to completed/failed

    Args:
        request_id: UUID string of the JDSimulationRequest

    Returns:
        Dict with status and result details
    """
    req_id = uuid.UUID(request_id)

    with _session_factory()() as db:
        # Fetch the request
        simulation_req = db.get(JDSimulationRequest, req_id)
        if simulation_req is None:
            logger.error("JD simulation request %s not found", request_id)
            return {"status": "not_found", "request_id": request_id}

        try:
            # Update status to analyzing
            simulation_req.status = JDSimulationStatus.analyzing
            db.commit()
            _audit(db, req_id, "simulation.started", {})
            db.commit()

            logger.info(
                "Starting JD simulation processing",
                extra={
                    "request_id": request_id,
                    "user_id": str(simulation_req.user_id),
                    "simulation_type": simulation_req.simulation_type.value,
                },
            )

            # Run the async engine with a fresh async session (it persists the
            # result + marks the request completed within that session).
            summary = asyncio.run(_run_simulation_async(request_id))

            # Record the completion audit on the sync session.
            _audit(db, req_id, "simulation.completed", summary)
            db.commit()

            logger.info(
                "JD simulation completed",
                extra={"request_id": request_id, **summary},
            )

            return {
                "status": "completed",
                "request_id": request_id,
                "result_id": summary["result_id"],
                "quality_score": summary["quality_score"],
            }

        except Exception as exc:
            db.rollback()
            simulation_req = db.get(JDSimulationRequest, req_id)
            if simulation_req is not None:
                simulation_req.status = JDSimulationStatus.failed
                _audit(db, req_id, "simulation.failed", {"error": str(exc)})
                db.commit()

            logger.exception("JD simulation failed for %s", request_id)

            # Retry with exponential backoff
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
