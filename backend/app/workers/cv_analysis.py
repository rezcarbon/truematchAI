"""Celery tasks for CV analysis pipeline."""
from __future__ import annotations

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.core.governance import get_governance_config
from app.engines import governance_engine
from app.models.cv_analysis import CVAnalysisRequest, CVAnalysisStatus
from app.models.governance_review import GovernanceReview, ReviewType, ReviewStatus
from app.models.resume import Resume
from app.engines.cv_analysis_engine import analyze_candidate_cv
from app.engines.client import ClaudeClient
from app.workers.celery_app import celery_app
from app.workers.realtime_progress import get_progress_tracker

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


async def _run_analysis_async(
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
    # Create a FRESH async engine & session factory for this thread
    # This ensures no event loop contamination from parent process
    async_engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True)
    AsyncSessionFactory = async_sessionmaker(bind=async_engine, expire_on_commit=False)

    try:
        async with AsyncSessionFactory() as async_db:
            # Initialize Claude client
            claude_client = ClaudeClient(api_key=settings.anthropic_api_key)

            # Run the analysis engine
            result = await analyze_candidate_cv(async_db, claude_client, analysis_req)

            return result
    finally:
        # Clean up the engine
        await async_engine.dispose()


@celery_app.task(name="app.workers.cv_analysis.process_cv_analysis_task", bind=True, max_retries=3)
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
            # Not found - likely replication lag. Retry after brief delay.
            retry_count = self.request.retries
            if retry_count < self.max_retries:
                logger.warning(
                    "CV analysis request not found in database (retry %d/%d), likely replication lag",
                    retry_count + 1,
                    self.max_retries,
                    extra={"request_id": request_id},
                )
                # Exponential backoff: 1s, 2s, 4s for retries
                raise self.retry(countdown=2 ** retry_count, exc=Exception(f"Request {request_id} not found in DB"))
            else:
                # Max retries exhausted
                logger.error(
                    "CV analysis request not found after %d retries - giving up",
                    self.max_retries,
                    extra={"request_id": request_id},
                )
                return {"status": "failed", "request_id": request_id, "error": "Request not found in database after retries"}

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

            # Run async analysis in a separate thread to avoid event loop conflicts
            # ThreadPoolExecutor completely isolates the async context from Celery's sync context
            def _run_analysis_in_thread():
                """Run async analysis in a separate thread with its own event loop."""
                try:
                    # Create fresh event loop in this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        # Run the async analysis with fresh async engine
                        return loop.run_until_complete(_run_analysis_async(analysis_req, request_id))
                    finally:
                        loop.close()
                except Exception as e:
                    logger.error(f"Error in analysis thread: {e}", exc_info=True)
                    raise

            # Emit progress event: analysis starting
            tracker = get_progress_tracker()
            asyncio.run_coroutine_threadsafe(
                tracker.emit_event(__import__('app.workers.realtime_progress', fromlist=['ProgressEvent']).ProgressEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=__import__('app.workers.realtime_progress', fromlist=['ProgressEventType']).ProgressEventType.ASSESSMENT_PROCESSING,
                    assessment_id=request_id,
                    progress_percent=25,
                    status="Running CV analysis engine",
                )),
                __import__('asyncio').get_event_loop()
            ) if False else None  # Placeholder for async emit

            # Execute in thread pool to isolate async context completely
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_run_analysis_in_thread)
                result = future.result(timeout=600)  # 10 minute timeout

            logger.info(
                "Analysis engine completed",
                extra={"request_id": request_id},
            )

            # Apply governance gates to the analysis result
            logger.info(
                "Applying governance checks",
                extra={"request_id": request_id},
            )

            try:
                governance_cfg = get_governance_config()
            except Exception:
                governance_cfg = None
                logger.warning("Governance config unavailable; governance gates will be skipped.")

            # Build assessment view for governance checks
            assessment_view = {
                "missing_capabilities": result.missing_capabilities or [],
                "weakness_areas": result.weakness_areas or [],
                "strength_summary": result.strength_summary or "",
            }

            # Execute governance gates
            governance_passed = True
            if governance_cfg and governance_cfg.is_operational():
                # Gate 1: Coherence
                coherence_result = governance_engine.check_coherence(assessment_view, governance_cfg)
                result.governance_coherence = coherence_result
                if not coherence_result.get("passed", True):
                    governance_passed = False
                    logger.warning(
                        "Governance gate failed: coherence",
                        extra={
                            "request_id": request_id,
                            "observations": coherence_result.get("observations", ""),
                        },
                    )

                # Gate 2: Consistency
                consistency_result = governance_engine.check_consistency(assessment_view, governance_cfg)
                result.governance_consistency = consistency_result
                if not consistency_result.get("passed", True):
                    governance_passed = False
                    logger.warning(
                        "Governance gate failed: consistency",
                        extra={
                            "request_id": request_id,
                            "observations": consistency_result.get("observations", ""),
                        },
                    )

                # Gate 3: Fidelity
                resume = sync_db.get(Resume, analysis_req.resume_id)
                if resume:
                    fidelity_result = governance_engine.check_fidelity(
                        resume.parsed_data or {},
                        assessment_view,
                        governance_cfg
                    )
                    result.governance_fidelity = fidelity_result
                    if not fidelity_result.get("passed", True):
                        governance_passed = False
                        logger.warning(
                            "Governance gate failed: fidelity",
                            extra={
                                "request_id": request_id,
                                "observations": fidelity_result.get("observations", ""),
                            },
                        )

            # Gate 4: Bias check (always runs)
            bias_result = governance_engine.check_bias(
                sync_db.get(Resume, analysis_req.resume_id).parsed_data or {} if sync_db.get(Resume, analysis_req.resume_id) else {},
                assessment_view
            )
            result.governance_bias_flags = bias_result
            if bias_result.get("flags"):
                logger.warning(
                    "Governance gate flagged bias concerns",
                    extra={
                        "request_id": request_id,
                        "flags": bias_result.get("flags", []),
                    },
                )

            result.governance_passed = governance_passed

            # If governance failed, create a review record for human review
            if not governance_passed:
                failed_gates = []
                gate_details = {}

                if result.governance_coherence and not result.governance_coherence.get("passed", True):
                    failed_gates.append("coherence")
                    gate_details["coherence"] = result.governance_coherence

                if result.governance_consistency and not result.governance_consistency.get("passed", True):
                    failed_gates.append("consistency")
                    gate_details["consistency"] = result.governance_consistency

                if result.governance_fidelity and not result.governance_fidelity.get("passed", True):
                    failed_gates.append("fidelity")
                    gate_details["fidelity"] = result.governance_fidelity

                if result.governance_bias_flags and result.governance_bias_flags.get("flags"):
                    failed_gates.append("bias_check")
                    gate_details["bias_check"] = result.governance_bias_flags

                if failed_gates:
                    review = GovernanceReview(
                        id=uuid.uuid4(),
                        review_type=ReviewType.cv_analysis,
                        resource_id=result.id,
                        user_id=analysis_req.user_id,
                        failed_gates=failed_gates,
                        gate_details=gate_details,
                        failure_reason=f"CV analysis failed governance gates: {', '.join(failed_gates)}",
                        status=ReviewStatus.pending,
                    )
                    sync_db.add(review)
                    logger.warning(
                        "Governance review created for failed CV analysis",
                        extra={
                            "review_id": str(review.id),
                            "result_id": str(result.id),
                            "failed_gates": failed_gates,
                        },
                    )

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

            # Log detailed error information for debugging
            logger.error(
                "CV analysis failed for %s",
                request_id,
                extra={
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "request_retries": self.request.retries,
                },
                exc_info=True,
            )

            # Retry with exponential backoff (2s, 4s, 8s, then fail)
            retry_countdown = 2 ** self.request.retries
            logger.info(
                "Retrying CV analysis in %s seconds",
                retry_countdown,
                extra={"request_id": request_id, "attempt": self.request.retries + 1},
            )
            raise self.retry(exc=exc, countdown=retry_countdown)
