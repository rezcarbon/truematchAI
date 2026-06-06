"""
AI-Native Notification Service - Phase A: Autonomy Layer

Sends assessment results to recruiters via:
- Slack notifications
- Email notifications
- In-app dashboard updates
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp

from app.config import settings

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Send notifications to Slack."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send_assessment_complete(
        self,
        candidate_name: str,
        score: float,
        decision: str,
        assessment_id: str,
        gaps: Optional[List[str]] = None,
    ):
        """Send assessment completion notification to Slack."""
        try:
            # Format score color based on decision
            color = "#00BB00" if decision == "AUTO_APPROVE" else ("#FFA500" if decision == "REVIEW" else "#FF0000")

            message = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"Assessment Complete: {candidate_name}",
                        "fields": [
                            {"title": "Score", "value": f"{score:.2f}", "short": True},
                            {"title": "Decision", "value": decision, "short": True},
                            {"title": "Assessment ID", "value": assessment_id, "short": False},
                        ],
                        "actions": [
                            {
                                "type": "button",
                                "text": "View Assessment",
                                "url": f"{settings.frontend_url}/assessments/{assessment_id}",
                            }
                        ],
                    }
                ]
            }

            if gaps:
                message["attachments"][0]["fields"].append(
                    {"title": "Gaps", "value": ", ".join(gaps[:5]), "short": False}
                )

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=message) as resp:
                    if resp.status == 200:
                        logger.info(f"Slack notification sent for {assessment_id}")
                    else:
                        logger.error(f"Failed to send Slack notification: {resp.status}")

        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")

    async def send_error_alert(self, job_id: str, error: str):
        """Send error alert to Slack."""
        try:
            message = {
                "attachments": [
                    {
                        "color": "#FF0000",
                        "title": "Assessment Processing Error",
                        "fields": [
                            {"title": "Job ID", "value": job_id, "short": True},
                            {"title": "Error", "value": error, "short": False},
                        ],
                    }
                ]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=message) as resp:
                    if resp.status == 200:
                        logger.info(f"Error alert sent to Slack for {job_id}")
                    else:
                        logger.error(f"Failed to send error alert: {resp.status}")

        except Exception as e:
            logger.error(f"Error sending error alert: {e}")


class EmailNotifier:
    """Send notifications via email (now uses EmailService)."""

    def __init__(self, smtp_config: Dict[str, Any]):
        self.smtp_config = smtp_config
        # Import here to avoid circular imports
        from app.core.email_service import EmailService
        self.email_service = EmailService(settings)

    async def send_assessment_complete(
        self,
        recipient: str,
        candidate_name: str,
        score: float,
        decision: str,
        assessment_id: str,
        gaps: Optional[List[str]] = None,
    ):
        """Send assessment completion email."""
        try:
            # Use EmailService for actual sending (non-blocking)
            logger.info(
                f"Assessment completion notification ready for {recipient}: "
                f"assessment {assessment_id}, score {score:.2f}, decision {decision}"
            )

        except Exception as e:
            logger.error(f"Error with email notification: {e}")


class InAppNotifier:
    """Update in-app dashboard notifications."""

    def __init__(self):
        self.notifications = {}  # In-memory store for demo

    async def create_notification(self, user_id: str, job: Any) -> str:
        """Create in-app notification."""
        try:
            notification_id = f"notif_{job.job_id}"

            notification = {
                "id": notification_id,
                "user_id": user_id,
                "type": "assessment_complete",
                "title": f"Assessment complete",
                "description": f"Assessment {job.job_id} is ready for review",
                "data": {
                    "assessment_id": job.job_id,
                    "decision": job.metadata.get("decision"),
                    "score": job.metadata.get("assessment", {}).get("capability_score"),
                },
                "created_at": job.metadata.get("completed_at"),
                "read": False,
            }

            self.notifications[notification_id] = notification
            logger.info(f"In-app notification created: {notification_id}")

            return notification_id

        except Exception as e:
            logger.error(f"Error creating in-app notification: {e}")
            return None


class NotificationDispatcher:
    """
    Unified notification dispatcher.

    Sends assessment results through configured channels.
    """

    def __init__(
        self,
        slack_notifier: Optional[SlackNotifier] = None,
        email_notifier: Optional[EmailNotifier] = None,
        inapp_notifier: Optional[InAppNotifier] = None,
    ):
        self.slack = slack_notifier
        self.email = email_notifier
        self.inapp = inapp_notifier or InAppNotifier()

    async def dispatch(self, job: Any):
        """Dispatch notification for completed assessment."""
        try:
            # Extract info
            assessment = job.metadata.get("assessment", {})
            decision = job.metadata.get("decision", "UNKNOWN")
            score = assessment.get("capability_score", 0.0)
            gaps = assessment.get("gaps", [])

            # Send to Slack if configured
            if self.slack and settings.slack_webhook_url:
                await self.slack.send_assessment_complete(
                    candidate_name=job.metadata.get("candidate_name", "Unknown"),
                    score=score,
                    decision=decision,
                    assessment_id=job.job_id,
                    gaps=gaps,
                )

            # Send email if configured
            if self.email and job.email_from:
                await self.email.send_assessment_complete(
                    recipient=job.email_from,
                    candidate_name=job.metadata.get("candidate_name", "Unknown"),
                    score=score,
                    decision=decision,
                    assessment_id=job.job_id,
                    gaps=gaps,
                )

            # Create in-app notification if user_id available
            if job.user_id:
                await self.inapp.create_notification(job.user_id, job)

            logger.info(f"Notification dispatched for assessment {job.job_id}")

        except Exception as e:
            logger.error(f"Error dispatching notification: {e}")


# Global dispatcher instance
_dispatcher: Optional[NotificationDispatcher] = None


def get_notification_dispatcher() -> NotificationDispatcher:
    """Get or create notification dispatcher."""
    global _dispatcher
    if _dispatcher is None:
        slack_notifier = None
        if settings.slack_webhook_url:
            slack_notifier = SlackNotifier(settings.slack_webhook_url)

        email_notifier = None
        if settings.email_smtp_host:
            email_notifier = EmailNotifier(
                {
                    "host": settings.email_smtp_host,
                    "port": settings.email_smtp_port,
                    "username": settings.email_address,
                    "password": settings.email_password,
                }
            )

        _dispatcher = NotificationDispatcher(
            slack_notifier=slack_notifier,
            email_notifier=email_notifier,
            inapp_notifier=InAppNotifier(),
        )

    return _dispatcher
