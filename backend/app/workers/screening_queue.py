"""Screening Queue - Phase 1 Celery Tasks for Batch Candidate Screening.

Pipeline: batch_created → process_screening_batch → screening_completed → learning_triggered

The worker uses synchronous SQLAlchemy for Celery compatibility.
Async screening logic is wrapped in sync context.
"""
from __future__ import annotations

import asyncio
import json
import logging
import traceback
import uuid
from typing import Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.screening import (
    ScreeningBatch,
    ScreeningResult,
    ScreeningBatchStatus,
    RecruiterDecision,
)
from app.models.resume import Resume
from app.models.position import Position
from app.models.assessment import Assessment
from app.models.audit import AuditTrail
from app.models.decision import Decision
from app.agents.screening_agent import ScreeningAgent
from app.workers.celery_app import celery_app

logger = logging.getLogger("truematch.screening_queue")

# Synchronous engine for worker (same pattern as assessment_queue.py)
_sync_engine = None
_SyncSessionLocal: sessionmaker[Session] | None = None


def _sync_database_url() -> str:
    """Convert async URL to sync URL for Celery worker."""
    url = settings.database_url
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg")
    return url


def _session_factory() -> sessionmaker[Session]:
    """Lazy initialization of sync session factory."""
    global _sync_engine, _SyncSessionLocal
    if _SyncSessionLocal is None:
        _sync_engine = create_engine(
            _sync_database_url(),
            pool_pre_ping=True,
            future=True,
            echo=False,  # Set to True for debug
        )
        _SyncSessionLocal = sessionmaker(bind=_sync_engine, expire_on_commit=False)
    return _SyncSessionLocal


def _audit(
    db: Session,
    screening_batch_id: uuid.UUID,
    event_type: str,
    data: dict,
) -> AuditTrail:
    """Log screening event to audit trail."""
    entry = AuditTrail(
        assessment_id=None,  # Screening is not tied to single assessment
        event_type=event_type,
        event_data=data,
        actor_type="automation",  # Screening agent is automated
        metadata={"screening_batch_id": str(screening_batch_id)},
    )
    db.add(entry)
    db.flush()
    return entry


@celery_app.task(
    name="screening_queue.process_screening_batch",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    time_limit=3600,  # 1 hour max per batch
)
def process_screening_batch(
    self,
    batch_id: str,
    resume_ids: list[str],
    batch_config: Optional[dict] = None,
) -> dict:
    """
    Process a screening batch - main Celery task.

    Screens multiple resumes concurrently against a position.
    Updates batch progress and creates ScreeningResult records.

    Args:
        batch_id: UUID of ScreeningBatch
        resume_ids: List of resume UUIDs to screen
        batch_config: Optional screening configuration

    Returns:
        dict with batch_id, screened_count, status, errors

    Retries on failure (up to 3 times) before escalating.
    """
    db_session_factory = _session_factory()
    db = db_session_factory()

    try:
        batch_uuid = uuid.UUID(batch_id)
        resume_uuids = [uuid.UUID(rid) for rid in resume_ids]

        logger.info(
            f"Starting screening batch {batch_id}: {len(resume_uuids)} resumes"
        )

        # Load batch
        batch = db.query(ScreeningBatch).filter_by(id=batch_uuid).first()
        if not batch:
            logger.error(f"Batch {batch_id} not found")
            return {"batch_id": batch_id, "error": "Batch not found"}

        # Update batch status
        batch.status = ScreeningBatchStatus.screening
        db.commit()

        # Load position (needed for all screenings)
        position = db.query(Position).filter_by(id=batch.position_id).first()
        if not position:
            logger.error(f"Position {batch.position_id} not found")
            _audit(db, batch_uuid, "screening.error", {"error": "Position not found"})
            batch.status = ScreeningBatchStatus.completed
            db.commit()
            return {"batch_id": batch_id, "error": "Position not found"}

        # Process resumes concurrently with asyncio
        # Run in thread pool to avoid blocking Celery worker
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            results = loop.run_until_complete(
                _screen_batch_async(db, batch_uuid, resume_uuids, position, batch_config)
            )
        finally:
            loop.close()

        screened_count = results["screened"]
        failed_count = results["failed"]
        errors = results["errors"]

        logger.info(
            f"Batch {batch_id} screening complete: "
            f"{screened_count} screened, {failed_count} failed"
        )

        # Update batch final status
        batch.screened_count = screened_count
        batch.pending_review_count = screened_count  # All await review
        batch.status = ScreeningBatchStatus.pending_review
        db.commit()

        # Log completion
        _audit(
            db,
            batch_uuid,
            "screening.batch_completed",
            {
                "total": len(resume_uuids),
                "screened": screened_count,
                "failed": failed_count,
                "errors": errors,
            },
        )
        db.commit()

        return {
            "batch_id": batch_id,
            "screened": screened_count,
            "failed": failed_count,
            "status": "completed",
            "errors": errors,
        }

    except Exception as e:
        logger.error(f"Error processing screening batch: {e}\n{traceback.format_exc()}")
        try:
            batch = db.query(ScreeningBatch).filter_by(id=uuid.UUID(batch_id)).first()
            if batch:
                _audit(
                    db,
                    uuid.UUID(batch_id),
                    "screening.batch_error",
                    {"error": str(e), "traceback": traceback.format_exc()},
                )
                db.commit()
        except Exception as audit_error:
            logger.error(f"Error logging audit trail: {audit_error}")

        # Retry up to 3 times
        raise self.retry(exc=e)

    finally:
        db.close()


async def _screen_batch_async(
    db: Session,
    batch_id: uuid.UUID,
    resume_ids: list[uuid.UUID],
    position: Position,
    batch_config: Optional[dict] = None,
) -> dict:
    """
    Async screening worker - screens multiple resumes concurrently.

    Args:
        db: Sync database session
        batch_id: Batch UUID
        resume_ids: Resume UUIDs to screen
        position: Position to screen against
        batch_config: Screening configuration

    Returns:
        dict with screened count, failed count, errors
    """
    # Create async-compatible screening agent
    agent = ScreeningAgent(db)

    screened_count = 0
    failed_count = 0
    errors = []

    # Process resumes with semaphore (max 10 concurrent)
    semaphore = asyncio.Semaphore(10)

    async def screen_one(resume_id: uuid.UUID) -> bool:
        """Screen a single resume, return success status."""
        async with semaphore:
            try:
                # Load resume from sync DB
                resume = db.query(Resume).filter_by(id=resume_id).first()
                if not resume:
                    logger.warning(f"Resume {resume_id} not found")
                    return False

                # Run screening agent
                agent_result = await agent.screen_resume(
                    resume, position, batch_config
                )

                # Create ScreeningResult record in sync DB
                screening_result = ScreeningResult(
                    screening_batch_id=batch_id,
                    position_id=position.id,
                    resume_id=resume_id,
                    user_id=resume.user_id,
                    assessment_id=None,
                    agent_recommendation=agent_result["agent_recommendation"],
                    confidence_score=agent_result["confidence_score"],
                    screening_summary=agent_result["screening_summary"],
                    screening_details=agent_result["screening_details"],
                    bias_flags=agent_result["bias_flags"],
                )

                db.add(screening_result)
                db.flush()

                logger.info(
                    f"Screened {resume_id}: {agent_result['agent_recommendation'].value} "
                    f"({agent_result['confidence_score']}%)"
                )

                return True

            except Exception as e:
                logger.error(f"Error screening {resume_id}: {e}\n{traceback.format_exc()}")
                errors.append({"resume_id": str(resume_id), "error": str(e)})
                return False

    # Run all screenings concurrently
    tasks = [screen_one(rid) for rid in resume_ids]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    # Count successes
    screened_count = sum(1 for r in results if r)
    failed_count = len(results) - screened_count

    # Commit all screening results at once
    try:
        db.commit()
    except Exception as e:
        logger.error(f"Error committing screening results: {e}")
        db.rollback()
        failed_count += screened_count
        screened_count = 0
        errors.append({"error": f"Commit failed: {str(e)}"})

    return {
        "screened": screened_count,
        "failed": failed_count,
        "errors": errors,
    }


@celery_app.task(
    name="screening_queue.record_recruiter_decision",
    bind=True,
    max_retries=3,
)
def record_recruiter_decision(
    self,
    screening_result_id: str,
    recruiter_decision: str,
    recruiter_id: str,
    recruiter_notes: Optional[str] = None,
    recruiter_confidence: Optional[int] = None,
) -> dict:
    """
    Record recruiter decision on screening result.

    Runs after recruiter makes a decision (interview/hold/further_review).
    Creates Decision record, captures override, triggers learning.

    Args:
        screening_result_id: ScreeningResult UUID
        recruiter_decision: "interview" | "hold" | "further_review"
        recruiter_id: Recruiter UUID
        recruiter_notes: Optional decision notes
        recruiter_confidence: Optional confidence (0-100)

    Returns:
        dict with decision_id, status
    """
    db_session_factory = _session_factory()
    db = db_session_factory()

    try:
        sr_uuid = uuid.UUID(screening_result_id)
        recruiter_uuid = uuid.UUID(recruiter_id)

        logger.info(
            f"Recording recruiter decision for {screening_result_id}: {recruiter_decision}"
        )

        # Load screening result
        screening_result = (
            db.query(ScreeningResult).filter_by(id=sr_uuid).first()
        )
        if not screening_result:
            logger.error(f"ScreeningResult {screening_result_id} not found")
            return {"error": "ScreeningResult not found"}

        # Determine if override
        was_overridden = (
            recruiter_decision != screening_result.agent_recommendation.value
        )

        # Update screening result
        screening_result.recruiter_decision = RecruiterDecision(recruiter_decision)
        screening_result.recruiter_id = recruiter_uuid
        screening_result.recruiter_notes = recruiter_notes
        screening_result.recruiter_confidence = recruiter_confidence
        screening_result.was_overridden = was_overridden

        # Create Decision record
        decision = Decision(
            assessment_id=screening_result.assessment_id,
            position_id=screening_result.position_id,
            recruiter_id=recruiter_uuid,
            decision=recruiter_decision,  # "interview" → DecisionOutcome
            ai_recommendation_followed=not was_overridden,
            override_reasoning=recruiter_notes,
            screening_override_reason=recruiter_notes if was_overridden else None,
            is_screening_decision=True,
        )

        db.add(decision)
        db.commit()

        # Audit trail
        _audit(
            db,
            screening_result.screening_batch_id,
            "screening.recruiter_decision",
            {
                "screening_result_id": str(sr_uuid),
                "decision": recruiter_decision,
                "was_overridden": was_overridden,
                "recruiter_id": str(recruiter_uuid),
            },
        )
        db.commit()

        logger.info(
            f"Recruiter decision recorded: {recruiter_decision} "
            f"(override={was_overridden})"
        )

        return {
            "decision_id": str(decision.id),
            "status": "recorded",
            "was_overridden": was_overridden,
        }

    except Exception as e:
        logger.error(f"Error recording recruiter decision: {e}\n{traceback.format_exc()}")
        raise self.retry(exc=e)

    finally:
        db.close()


@celery_app.task(
    name="screening_queue.trigger_learning_loop",
    bind=True,
    max_retries=2,
)
def trigger_learning_loop(self, batch_id: str) -> dict:
    """
    Trigger learning loop after batch screening completes.

    Analyzes recruiter decisions, detects patterns, updates agent weights.
    Called after batch transitions to pending_review status.

    Args:
        batch_id: ScreeningBatch UUID

    Returns:
        dict with learning status
    """
    db_session_factory = _session_factory()
    db = db_session_factory()

    try:
        batch_uuid = uuid.UUID(batch_id)

        logger.info(f"Triggering learning loop for batch {batch_id}")

        # Load batch
        batch = db.query(ScreeningBatch).filter_by(id=batch_uuid).first()
        if not batch:
            logger.error(f"Batch {batch_id} not found")
            return {"error": "Batch not found"}

        # Load all screening results for batch
        results = (
            db.query(ScreeningResult)
            .filter_by(screening_batch_id=batch_uuid)
            .all()
        )

        # Analyze override patterns
        decided_results = [r for r in results if r.recruiter_decision]
        overridden = [r for r in decided_results if r.was_overridden]

        override_rate = (
            len(overridden) / len(decided_results) if decided_results else 0.0
        )

        logger.info(
            f"Batch {batch_id} learning: "
            f"{len(decided_results)} decisions, "
            f"{len(overridden)} overrides ({override_rate:.1%})"
        )

        # TODO: Implement full learning loop
        # - Analyze which recommendation types were overridden
        # - Update agent weights based on hiring outcomes
        # - Detect bias patterns in recruiter decisions
        # - Store learning signals for next iteration

        # Log learning event
        _audit(
            db,
            batch_uuid,
            "screening.learning_triggered",
            {
                "total_results": len(results),
                "decided": len(decided_results),
                "overridden": len(overridden),
                "override_rate": override_rate,
            },
        )
        db.commit()

        return {
            "batch_id": batch_id,
            "status": "learning_triggered",
            "override_rate": override_rate,
        }

    except Exception as e:
        logger.error(f"Error triggering learning loop: {e}\n{traceback.format_exc()}")
        raise self.retry(exc=e)

    finally:
        db.close()


__all__ = [
    "process_screening_batch",
    "record_recruiter_decision",
    "trigger_learning_loop",
]
