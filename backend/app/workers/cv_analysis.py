"""Celery tasks for CV analysis pipeline."""
from __future__ import annotations

import logging
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.cv_analysis import CVAnalysisRequest, CVAnalysisStatus
from app.models.audit import AuditTrail
from app.engines.cv_analysis_engine import analyze_candidate_cv
from app.engines.client import ClaudeClient
from app.workers.celery_app import celery_app

logger = logging.getLogger("truematch.cv_analysis_tasks")

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
    """Create an audit trail entry."""
    entry = AuditTrail(
        cv_analysis_request_id=request_id,
        event_type=event_type,
        event_data=data,
        actor_type="system",
    )
    db.add(entry)
    db.flush()
    return entry


@celery_app.task(name="app.workers.cv_analysis.process_cv_analysis_task", bind=True, max_retries=2)
def process_cv_analysis_task(self, request_id: str) -> dict:
    """Process a CV analysis request end-to-end.

    This task:
    1. Fetches the CVAnalysisRequest from the database
    2. Runs the CV analysis engine
    3. Persists results to CVAnalysisResult
    4. Updates the request status to completed/failed

    Args:
        request_id: UUID string of the CVAnalysisRequest

    Returns:
        Dict with status and result details
    """
    req_id = uuid.UUID(request_id)

    with _session_factory()() as db:
        # Fetch the request
        analysis_req = db.get(CVAnalysisRequest, req_id)
        if analysis_req is None:
            logger.error("CV analysis request %s not found", request_id)
            return {"status": "not_found", "request_id": request_id}

        try:
            # Update status to analyzing
            analysis_req.status = CVAnalysisStatus.analyzing
            db.commit()
            _audit(db, req_id, "analysis.started", {})
            db.commit()

            logger.info(
                "Starting CV analysis processing",
                extra={
                    "request_id": request_id,
                    "user_id": str(analysis_req.user_id),
                    "target_role": analysis_req.target_role,
                },
            )

            # Initialize Claude client
            claude_client = ClaudeClient(api_key=settings.anthropic_api_key)

            # Run the analysis engine (using sync wrapper)
            # Note: The engine itself is async, so we need to run it in an event loop
            import asyncio
            result = asyncio.run(
                analyze_candidate_cv(db, claude_client, analysis_req)
            )

            # Persist the result
            db.add(result)
            db.flush()

            # Update request status
            analysis_req.status = CVAnalysisStatus.completed
            _audit(
                db,
                req_id,
                "analysis.completed",
                {
                    "result_id": str(result.id),
                    "gaps_count": len(result.missing_capabilities or []),
                    "job_matches": len(result.top_matching_position_ids or []),
                },
            )
            db.commit()

            logger.info(
                "CV analysis completed",
                extra={
                    "request_id": request_id,
                    "result_id": str(result.id),
                    "gaps": len(result.missing_capabilities or []),
                    "matches": len(result.top_matching_position_ids or []),
                },
            )

            return {
                "status": "completed",
                "request_id": request_id,
                "result_id": str(result.id),
                "gaps_count": len(result.missing_capabilities or []),
            }

        except Exception as exc:
            db.rollback()
            analysis_req = db.get(CVAnalysisRequest, req_id)
            if analysis_req is not None:
                analysis_req.status = CVAnalysisStatus.failed
                _audit(db, req_id, "analysis.failed", {"error": str(exc)})
                db.commit()

            logger.exception("CV analysis failed for %s", request_id)

            # Retry with exponential backoff
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
