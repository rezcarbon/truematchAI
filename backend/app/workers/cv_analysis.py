"""Celery tasks for CV analysis pipeline."""
from __future__ import annotations

import asyncio
import logging
import uuid

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.cv_analysis import CVAnalysisRequest, CVAnalysisStatus
from app.engines.cv_analysis_engine import analyze_candidate_cv
from app.engines.client import ClaudeClient
from app.workers.celery_app import celery_app

logger = logging.getLogger("truematch.cv_analysis_tasks")

# Synchronous engine for fetching/updating the request status
_sync_engine = None
_SyncSessionLocal: sessionmaker[Session] | None = None

# Async engine for the actual analysis
_async_engine = None
_AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


def _sync_database_url() -> str:
    """Derive a synchronous SQLAlchemy URL from the configured async URL."""
    url = settings.database_url
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg")
    return url


def _sync_session_factory() -> sessionmaker[Session]:
    """Get or create the synchronous session factory."""
    global _sync_engine, _SyncSessionLocal
    if _SyncSessionLocal is None:
        _sync_engine = create_engine(_sync_database_url(), pool_pre_ping=True, future=True)
        _SyncSessionLocal = sessionmaker(bind=_sync_engine, expire_on_commit=False)
    return _SyncSessionLocal


def _async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory."""
    global _async_engine, _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _async_engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True)
        _AsyncSessionLocal = async_sessionmaker(bind=_async_engine, expire_on_commit=False)
    return _AsyncSessionLocal


def _audit(db: Session, request_id: uuid.UUID, event_type: str, data: dict) -> None:
    """Log CV analysis event (audit trail not available yet for CV analysis).

    TODO: Create dedicated CVAnalysisAudit table when needed.
    For now, we log via the standard logger instead.
    """
    logger.info(
        f"CV Analysis Event: {event_type}",
        extra={"request_id": str(request_id), "event_data": data},
    )


async def _run_analysis(
    analysis_req: CVAnalysisRequest,
    request_id: str,
) -> dict:
    """Run the CV analysis in an async context.

    Args:
        analysis_req: The CVAnalysisRequest to process
        request_id: String UUID of the request

    Returns:
        Dict with analysis results
    """
    # Create a new async session for this analysis
    async_session_factory = _async_session_factory()
    async with async_session_factory() as async_db:
        # Initialize Claude client
        claude_client = ClaudeClient(api_key=settings.anthropic_api_key)

        # Run the analysis engine
        result = await analyze_candidate_cv(async_db, claude_client, analysis_req)

        return result


@celery_app.task(name="app.workers.cv_analysis.process_cv_analysis_task", bind=True, max_retries=2)
def process_cv_analysis_task(self, request_id: str) -> dict:
    """Process a CV analysis request end-to-end.

    This task:
    1. Fetches the CVAnalysisRequest from the database (sync)
    2. Runs the CV analysis engine (async)
    3. Persists results to CVAnalysisResult (sync)
    4. Updates the request status to completed/failed

    Args:
        request_id: UUID string of the CVAnalysisRequest

    Returns:
        Dict with status and result details
    """
    req_id = uuid.UUID(request_id)

    # Use sync session for initial fetch and status updates
    with _sync_session_factory()() as sync_db:
        # Fetch the request
        analysis_req = sync_db.get(CVAnalysisRequest, req_id)
        if analysis_req is None:
            logger.error("CV analysis request %s not found", request_id)
            return {"status": "not_found", "request_id": request_id}

        try:
            # Update status to analyzing
            analysis_req.status = CVAnalysisStatus.analyzing
            sync_db.commit()
            _audit(sync_db, req_id, "analysis.started", {})
            sync_db.commit()

            logger.info(
                "Starting CV analysis processing",
                extra={
                    "request_id": request_id,
                    "user_id": str(analysis_req.user_id),
                    "target_role": analysis_req.target_role,
                },
            )

            # Run async analysis
            result = asyncio.run(_run_analysis(analysis_req, request_id))

            # Persist the result in the sync database
            sync_db.add(result)
            sync_db.flush()

            # Update request status
            analysis_req.status = CVAnalysisStatus.completed
            _audit(
                sync_db,
                req_id,
                "analysis.completed",
                {
                    "result_id": str(result.id),
                    "gaps_count": len(result.missing_capabilities or []),
                    "job_matches": len(result.top_matching_position_ids or []),
                },
            )
            sync_db.commit()

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
            sync_db.rollback()
            analysis_req = sync_db.get(CVAnalysisRequest, req_id)
            if analysis_req is not None:
                analysis_req.status = CVAnalysisStatus.failed
                _audit(sync_db, req_id, "analysis.failed", {"error": str(exc)})
                sync_db.commit()

            logger.exception("CV analysis failed for %s", request_id)

            # Retry with exponential backoff
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
