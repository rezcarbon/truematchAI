"""Celery task for nightly learning cycle.

Scheduled to run daily at 11 PM UTC.
Max runtime: 6 hours (11 PM - 5 AM).

Orchestrates:
1. Daily metrics calculation
2. Feedback aggregation
3. Pattern identification
4. Model recalibration

All steps are best-effort; failures are logged but don't block.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.learning_pipeline import LearningPipeline
from app.workers.celery_app import celery_app

logger = logging.getLogger("truematch.learning_orchestrator")


@celery_app.task(
    bind=True,
    name="app.workers.learning_orchestrator.run_nightly_learning_cycle",
    time_limit=21600,  # 6-hour hard limit
    soft_time_limit=21300,  # 5h 55m soft limit for graceful cleanup
    track_started=True,
)
def run_nightly_learning_cycle(
    self,
    target_date_str: Optional[str] = None,
) -> dict:
    """
    Run the nightly learning cycle.

    Executes asynchronously with proper database session management.

    Args:
        self: Celery task context
        target_date_str: ISO date string (YYYY-MM-DD), defaults to yesterday

    Returns:
        Summary dict with results from each step

    Raises:
        Exception: Any unhandled exceptions during learning
                   (logged but may trigger Celery retry)
    """
    import asyncio

    try:
        logger.info(f"Nightly learning cycle started (task_id={self.request.id})")

        # Parse target date
        if target_date_str:
            target_date = date.fromisoformat(target_date_str)
        else:
            target_date = date.today() - timedelta(days=1)

        # Run async learning pipeline
        result = asyncio.run(_run_learning_async(target_date))

        logger.info(
            f"Nightly learning cycle completed (task_id={self.request.id}): "
            f"steps={result.get('steps_completed', [])} "
            f"f1={result.get('metrics', {}).get('f1_score', 'N/A')}"
        )

        return result

    except Exception as exc:
        logger.error(
            f"Nightly learning cycle failed (task_id={self.request.id}): {exc}",
            exc_info=True,
        )
        # Re-raise so Celery can log and potentially retry
        raise


async def _run_learning_async(target_date: date) -> dict:
    """Execute learning pipeline asynchronously with database session."""
    async for db in get_session():
        try:
            pipeline = LearningPipeline(db)
            result = await pipeline.run_nightly_learning(target_date)
            return result
        except Exception:
            await db.rollback()
            raise
        finally:
            await db.close()


# Beat schedule entry added to celery_app.conf.beat_schedule in celery_app.py


__all__ = ["run_nightly_learning_cycle"]
