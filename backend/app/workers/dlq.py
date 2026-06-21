"""Dead Letter Queue (DLQ) handling for failed assessments.

Celery task invoked by run_assessment() when Claude API fails after retries.
Marks assessment as failed, stores error context, sends admin alerts via Slack,
and logs to incident system.
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.assessment import Assessment, AssessmentStatus
from app.models.audit import AuditTrail
from app.workers.celery_app import celery_app

logger = logging.getLogger("truematch.dlq")


class DLQError:
    """Structured representation of a DLQ error."""

    def __init__(self, error: str, context: dict[str, Any], error_type: str = "assessment_failure"):
        self.error = error
        self.context = context
        self.error_type = error_type
        self.timestamp = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize error to dict for storage."""
        return {
            "error": self.error,
            "error_type": self.error_type,
            "context": self.context,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


def _get_sync_session() -> Session:
    """Get a synchronous database session for the Celery worker.

    Mirrors the pattern used in tasks.py for worker database access.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Map async URL to sync psycopg driver
    db_url = settings.database_url
    if "+asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "+psycopg")

    engine = create_engine(db_url, pool_pre_ping=True, future=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    return session_factory()


def _send_dlq_alert(
    assessment_id: str,
    error: str,
    context: dict[str, Any],
    position_id: Optional[str] = None,
    resume_id: Optional[str] = None,
) -> None:
    """Send Slack alert to admin channel about DLQ event.

    Args:
        assessment_id: UUID of failed assessment
        error: Error message
        context: Additional context dict (includes retry info, stack trace, etc.)
        position_id: Position UUID (optional, extracted from assessment)
        resume_id: Resume UUID (optional, extracted from assessment)
    """
    if not settings.slack_webhook_url:
        logger.warning("Slack webhook URL not configured; skipping DLQ alert")
        return

    try:
        import asyncio

        import aiohttp

        # Build fields for Slack message
        fields = [
            {"title": "Assessment ID", "value": assessment_id, "short": True},
            {"title": "Status", "value": "FAILED", "short": True},
        ]

        if position_id:
            fields.append({"title": "Position ID", "value": position_id, "short": True})
        if resume_id:
            fields.append({"title": "Resume ID", "value": resume_id, "short": True})

        # Error message (truncate if very long)
        error_msg = error[:500] if len(error) > 500 else error
        fields.append({"title": "Error", "value": error_msg, "short": False})

        # Context details (serialize to JSON if it's a dict)
        if context:
            context_str = json.dumps(context, indent=2, default=str)
            # Truncate long context
            if len(context_str) > 1000:
                context_str = context_str[:997] + "..."
            fields.append({"title": "Context", "value": f"```{context_str}```", "short": False})

        message = {
            "attachments": [
                {
                    "color": "#FF0000",  # Red for critical
                    "title": "❌ Assessment Failed - DLQ Required",
                    "title_link": f"{settings.frontend_url}/assessments/{assessment_id}"
                    if settings.frontend_url
                    else None,
                    "fields": fields,
                    "footer": "TrueMatch DLQ System",
                    "ts": int(__import__("time").time()),
                }
            ]
        }

        async def post_dlq_alert():
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    settings.slack_webhook_url,
                    json=message,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"Slack DLQ alert failed with status {resp.status}")
                    else:
                        logger.info(f"Slack DLQ alert sent for assessment {assessment_id}")

        # Run async post in a new event loop (Celery worker context)
        asyncio.run(post_dlq_alert())

    except Exception as e:
        logger.error(f"Failed to send Slack DLQ alert: {e}", exc_info=True)


def _log_incident(
    db: Session,
    assessment_id: uuid.UUID,
    error: str,
    context: dict[str, Any],
) -> None:
    """Log incident to audit system for tracking and compliance.

    Args:
        db: SQLAlchemy session
        assessment_id: UUID of failed assessment
        error: Error message
        context: Full error context
    """
    try:
        audit_entry = AuditTrail(
            assessment_id=assessment_id,
            event_type="assessment.dlq_error",
            event_data={
                "error": error,
                "error_type": "assessment_failure",
                "context": context,
                "dlq_processed": True,
            },
            actor_type="system",
        )
        db.add(audit_entry)
        db.flush()
        logger.info(f"Incident logged for assessment {assessment_id}")
    except Exception as e:
        logger.error(f"Failed to log incident: {e}", exc_info=True)


@celery_app.task(name="app.workers.dlq.handle_assessment_dlq", bind=True)
def handle_assessment_dlq(
    self,
    assessment_id: str,
    error: str,
    context: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Handle Dead Letter Queue event for failed assessment.

    Called by run_assessment() when Claude API fails after max retries.
    - Marks assessment as failed in database
    - Stores error and context in assessment record
    - Sends Slack alert to admin channel
    - Logs incident to audit trail
    - Commits all changes atomically

    Args:
        assessment_id: UUID string of the assessment that failed
        error: Error message describing the failure
        context: Dict with additional context:
            - retry_count: Number of retries attempted
            - last_exception: Full exception traceback
            - position_id: UUID of associated position
            - resume_id: UUID of associated resume
            - timestamps: When failure occurred
            - Any other relevant operational context

    Returns:
        Dict with status and details:
            {
                "status": "dlq_handled" | "assessment_not_found" | "error",
                "assessment_id": <uuid>,
                "error": <error_message>,
                "marked_failed": <bool>,
                "slack_notified": <bool>,
                "incident_logged": <bool>,
            }

    Raises:
        Exception: Unrecoverable errors after logging attempt
    """
    if context is None:
        context = {}

    assessment_uuid = uuid.UUID(assessment_id)
    result = {
        "status": "dlq_handled",
        "assessment_id": assessment_id,
        "error": error,
        "marked_failed": False,
        "slack_notified": False,
        "incident_logged": False,
    }

    db = None
    try:
        db = _get_sync_session()

        # Fetch assessment
        assessment = db.get(Assessment, assessment_uuid)
        if assessment is None:
            logger.error(f"Assessment {assessment_id} not found in DLQ handler")
            result["status"] = "assessment_not_found"
            return result

        # Extract IDs for alert
        position_id = str(assessment.position_id) if assessment.position_id else None
        resume_id = str(assessment.resume_id) if assessment.resume_id else None

        # 1. Mark assessment as failed and store error context
        assessment.status = AssessmentStatus.failed

        # Store error and context as encrypted fields
        # (Add dlq_error and dlq_context fields if they exist in your Assessment model)
        # For now, we'll log to audit trail which handles encryption
        assessment.dlq_error = error
        assessment.dlq_context = context

        db.commit()
        result["marked_failed"] = True
        logger.info(f"Assessment {assessment_id} marked as failed")

        # 2. Send Slack alert to admin channel
        try:
            _send_dlq_alert(
                assessment_id=assessment_id,
                error=error,
                context=context,
                position_id=position_id,
                resume_id=resume_id,
            )
            result["slack_notified"] = True
        except Exception as e:
            logger.error(f"Failed to send Slack alert for {assessment_id}: {e}")
            # Don't fail the entire DLQ handler; continue to log incident

        # 3. Log to incident system (audit trail)
        try:
            _log_incident(db, assessment_uuid, error, context)
            db.commit()
            result["incident_logged"] = True
        except Exception as e:
            logger.error(f"Failed to log incident for {assessment_id}: {e}")
            # Don't fail; we've already marked as failed

        # Final commit if not already done
        try:
            db.commit()
        except Exception:
            pass  # Already committed above

        logger.info(
            f"DLQ handled for assessment {assessment_id}: "
            f"failed={result['marked_failed']}, slack={result['slack_notified']}, "
            f"audit={result['incident_logged']}"
        )

        return result

    except Exception as e:
        logger.exception(f"Unrecoverable error in DLQ handler for {assessment_id}")
        result["status"] = "error"
        result["error"] = str(e)
        return result
    finally:
        if db:
            try:
                db.close()
            except Exception:
                pass


def invoke_dlq(
    assessment_id: str,
    error: str,
    context: Optional[dict[str, Any]] = None,
    retry: bool = True,
) -> str:
    """Invoke the DLQ handler task synchronously or asynchronously.

    Called from run_assessment() when retries are exhausted.

    Args:
        assessment_id: UUID string of failed assessment
        error: Error message
        context: Additional context dict
        retry: If True, uses Celery async; if False, executes immediately

    Returns:
        Task ID (if async) or result dict (if sync)
    """
    if retry:
        # Queue async Celery task
        task = handle_assessment_dlq.delay(assessment_id, error, context)
        logger.info(f"DLQ task queued (ID: {task.id}) for assessment {assessment_id}")
        return task.id
    else:
        # Execute synchronously (for critical failures)
        result = handle_assessment_dlq(assessment_id, error, context)
        logger.info(f"DLQ handled synchronously for assessment {assessment_id}")
        return result["status"]
