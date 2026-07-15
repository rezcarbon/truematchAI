"""Assessment Design Queue - Phase 2 Celery Tasks.

Tasks for asynchronous assessment design operations:
- design_assessment() - Main design task
- batch_design_assessments() - Bulk design operations
"""
from __future__ import annotations

import logging
import traceback
from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.assessment_design import AssessmentDesign
from app.models.resume import Resume
from app.models.position import Position
from app.agents.assessment_designer_agent import AssessmentDesignerAgent
from app.workers.celery_app import celery_app

logger = logging.getLogger("truematch.assessment_design_queue")

# Synchronous database for Celery worker
_sync_engine = None
_SyncSessionLocal: sessionmaker[Session] | None = None


def _sync_database_url() -> str:
    """Convert async URL to sync for Celery."""
    url = settings.database_url
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg")
    return url


def _session_factory() -> sessionmaker[Session]:
    """Get synchronous session factory."""
    global _sync_engine, _SyncSessionLocal
    if _SyncSessionLocal is None:
        _sync_engine = create_engine(
            _sync_database_url(),
            pool_pre_ping=True,
            future=True,
        )
        _SyncSessionLocal = sessionmaker(bind=_sync_engine, expire_on_commit=False)
    return _SyncSessionLocal


@celery_app.task(
    name="assessment_design_queue.design_assessment",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    time_limit=600,  # 10 minutes max
)
def design_assessment(
    self,
    design_id: str,
    resume_id: str,
    position_id: str,
) -> dict:
    """
    Design assessment for a candidate (Celery task).

    Runs agent in background and updates AssessmentDesign record.

    Args:
        design_id: AssessmentDesign ID
        resume_id: Resume ID
        position_id: Position ID

    Returns:
        dict with design_id and status
    """
    db_session_factory = _session_factory()
    db = db_session_factory()

    try:
        design_uuid = UUID(design_id)
        resume_uuid = UUID(resume_id)
        position_uuid = UUID(position_id)

        logger.info(f"Starting assessment design task for {design_id}")

        # Load design record
        design = db.query(AssessmentDesign).filter_by(id=design_uuid).first()
        if not design:
            logger.error(f"Design {design_id} not found")
            return {"design_id": design_id, "error": "Design not found"}

        # Load resume
        resume = db.query(Resume).filter_by(id=resume_uuid).first()
        if not resume:
            logger.error(f"Resume {resume_id} not found")
            return {"design_id": design_id, "error": "Resume not found"}

        # Load position
        position = db.query(Position).filter_by(id=position_uuid).first()
        if not position:
            logger.error(f"Position {position_id} not found")
            return {"design_id": design_id, "error": "Position not found"}

        # Run agent
        agent = AssessmentDesignerAgent(db)
        result = agent.design_assessment(resume, position, str(design_uuid))

        # Update design record (already has agent_design and fairness_check set)
        logger.info(f"Design {design_id} completed successfully")

        return {
            "design_id": design_id,
            "status": "designed",
            "fairness_score": result["design_fairness_check"].get("fairness_score", 0),
        }

    except Exception as e:
        logger.error(f"Error in design task: {e}\n{traceback.format_exc()}")
        raise self.retry(exc=e)

    finally:
        db.close()


@celery_app.task(
    name="assessment_design_queue.batch_design_assessments",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def batch_design_assessments(
    self,
    design_ids: list[str],
) -> dict:
    """
    Design multiple assessments in batch.

    Args:
        design_ids: List of AssessmentDesign IDs

    Returns:
        dict with success count and status
    """
    db_session_factory = _session_factory()
    db = db_session_factory()

    try:
        logger.info(f"Starting batch design task for {len(design_ids)} designs")

        successful = 0
        failed = 0
        errors = []

        for design_id in design_ids:
            try:
                design_uuid = UUID(design_id)

                # Load design
                design = db.query(AssessmentDesign).filter_by(id=design_uuid).first()
                if not design:
                    failed += 1
                    errors.append(f"Design {design_id} not found")
                    continue

                # Load dependencies
                resume = db.query(Resume).filter_by(id=design.resume_id).first()
                position = db.query(Position).filter_by(id=design.position_id).first()

                if not resume or not position:
                    failed += 1
                    errors.append(f"Missing resume or position for {design_id}")
                    continue

                # Run agent
                agent = AssessmentDesignerAgent(db)
                result = agent.design_assessment(resume, position, design_id)

                successful += 1

            except Exception as e:
                logger.error(f"Error designing {design_id}: {e}")
                failed += 1
                errors.append(str(e))

        logger.info(
            f"Batch design complete: {successful} succeeded, {failed} failed"
        )

        return {
            "total": len(design_ids),
            "successful": successful,
            "failed": failed,
            "errors": errors[:10],  # Limit to first 10 errors
        }

    except Exception as e:
        logger.error(f"Error in batch design task: {e}")
        raise self.retry(exc=e)

    finally:
        db.close()


__all__ = [
    "design_assessment",
    "batch_design_assessments",
]
