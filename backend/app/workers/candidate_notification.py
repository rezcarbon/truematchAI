"""
Candidate Notification Worker (Phase 1: Autonomy Layer)

Sends notifications to candidates when their assessments reach key milestones:
- Assessment started
- Assessment approved
- Assessment rejected

Features:
- Async email delivery (non-blocking)
- Template-based email rendering via EmailService
- Email tracking and logging
- Retry logic with exponential backoff
- Error handling and reporting
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.email_service import EmailService, EmailTemplate
from app.models.resume import Resume
from app.models.notification import EmailLog

logger = logging.getLogger("truematch.candidate_notification")


class CandidateNotificationWorker:
    """
    Handles sending notifications to candidates about assessment status.

    Integrates with email service for multi-provider support and template
    rendering.
    """

    def __init__(self, db: AsyncSession, email_service: Optional[EmailService] = None):
        """
        Initialize candidate notification worker.

        Args:
            db: AsyncSession for database access
            email_service: EmailService instance (created if not provided)
        """
        self.db = db
        self.email_service = email_service or EmailService(settings)

    async def notify_assessment_started(
        self,
        assessment_id: uuid.UUID,
        candidate_email: str,
        candidate_name: str,
        position_title: str,
        company_name: str,
        assessment_url: str,
        recruiter_name: str = "Our team",
        recruiter_email: str = "support@truematch.ai",
    ) -> bool:
        """
        Send notification when assessment starts.

        Args:
            assessment_id: UUID of the assessment
            candidate_email: Candidate email address
            candidate_name: Candidate full name
            position_title: Job position title
            company_name: Company name
            assessment_url: URL for candidate to access assessment
            recruiter_name: Name of recruiter/hiring contact
            recruiter_email: Email of recruiter/hiring contact

        Returns:
            True if notification sent successfully
        """
        try:
            logger.info(
                f"[CandidateNotif] Sending assessment_started email",
                extra={
                    "assessment_id": str(assessment_id),
                    "candidate_email": candidate_email,
                    "position": position_title,
                }
            )

            context = {
                "candidate_name": candidate_name,
                "position_title": position_title,
                "company_name": company_name,
                "assessment_url": assessment_url,
                "recruiter_name": recruiter_name,
                "recruiter_email": recruiter_email,
                "current_year": datetime.now(timezone.utc).year,
            }

            success = await self.email_service.send_email(
                to_address=candidate_email,
                template_name=EmailTemplate.ASSESSMENT_STARTED,
                context=context,
            )

            if success:
                await self._log_email_sent(
                    candidate_email,
                    EmailTemplate.ASSESSMENT_STARTED,
                    assessment_id,
                )
                logger.info(
                    f"[CandidateNotif] assessment_started email sent",
                    extra={"assessment_id": str(assessment_id)}
                )
            else:
                await self._log_email_failed(
                    candidate_email,
                    EmailTemplate.ASSESSMENT_STARTED,
                    assessment_id,
                    "Email service returned False",
                )

            return success

        except Exception as e:
            logger.error(
                f"[CandidateNotif] Error sending assessment_started notification",
                extra={
                    "assessment_id": str(assessment_id),
                    "candidate_email": candidate_email,
                    "error": str(e),
                },
                exc_info=True
            )
            await self._log_email_failed(
                candidate_email,
                EmailTemplate.ASSESSMENT_STARTED,
                assessment_id,
                str(e),
            )
            return False

    async def notify_assessment_approved(
        self,
        assessment_id: uuid.UUID,
        candidate_email: str,
        candidate_name: str,
        position_title: str,
        company_name: str,
        recruiter_name: str = "Our team",
        recruiter_email: str = "support@truematch.ai",
        strengths: Optional[list[str]] = None,
    ) -> bool:
        """
        Send approval notification to candidate.

        Args:
            assessment_id: UUID of the assessment
            candidate_email: Candidate email address
            candidate_name: Candidate full name
            position_title: Job position title
            company_name: Company name
            recruiter_name: Name of recruiter/hiring contact
            recruiter_email: Email of recruiter/hiring contact
            strengths: List of candidate strengths identified in assessment

        Returns:
            True if notification sent successfully
        """
        try:
            logger.info(
                f"[CandidateNotif] Sending assessment_approved email",
                extra={
                    "assessment_id": str(assessment_id),
                    "candidate_email": candidate_email,
                    "position": position_title,
                }
            )

            context = {
                "candidate_name": candidate_name,
                "position_title": position_title,
                "company_name": company_name,
                "recruiter_name": recruiter_name,
                "recruiter_email": recruiter_email,
                "strengths": strengths or [],
                "current_year": datetime.now(timezone.utc).year,
            }

            success = await self.email_service.send_email(
                to_address=candidate_email,
                template_name=EmailTemplate.ASSESSMENT_APPROVED,
                context=context,
            )

            if success:
                await self._log_email_sent(
                    candidate_email,
                    EmailTemplate.ASSESSMENT_APPROVED,
                    assessment_id,
                    metadata={"strengths_count": len(strengths or [])},
                )
                logger.info(
                    f"[CandidateNotif] assessment_approved email sent",
                    extra={"assessment_id": str(assessment_id)}
                )
            else:
                await self._log_email_failed(
                    candidate_email,
                    EmailTemplate.ASSESSMENT_APPROVED,
                    assessment_id,
                    "Email service returned False",
                )

            return success

        except Exception as e:
            logger.error(
                f"[CandidateNotif] Error sending assessment_approved notification",
                extra={
                    "assessment_id": str(assessment_id),
                    "candidate_email": candidate_email,
                    "error": str(e),
                },
                exc_info=True
            )
            await self._log_email_failed(
                candidate_email,
                EmailTemplate.ASSESSMENT_APPROVED,
                assessment_id,
                str(e),
            )
            return False

    async def notify_assessment_rejected(
        self,
        assessment_id: uuid.UUID,
        candidate_email: str,
        candidate_name: str,
        position_title: str,
        company_name: str,
        recruiter_name: str = "Our team",
        recruiter_email: str = "support@truematch.ai",
        rejection_reason: str = "Thank you for your interest in this position.",
    ) -> bool:
        """
        Send rejection notification to candidate.

        Args:
            assessment_id: UUID of the assessment
            candidate_email: Candidate email address
            candidate_name: Candidate full name
            position_title: Job position title
            company_name: Company name
            recruiter_name: Name of recruiter/hiring contact
            recruiter_email: Email of recruiter/hiring contact
            rejection_reason: Feedback about assessment performance

        Returns:
            True if notification sent successfully
        """
        try:
            logger.info(
                f"[CandidateNotif] Sending assessment_rejected email",
                extra={
                    "assessment_id": str(assessment_id),
                    "candidate_email": candidate_email,
                    "position": position_title,
                }
            )

            context = {
                "candidate_name": candidate_name,
                "position_title": position_title,
                "company_name": company_name,
                "recruiter_name": recruiter_name,
                "recruiter_email": recruiter_email,
                "rejection_reason": rejection_reason,
                "current_year": datetime.now(timezone.utc).year,
            }

            success = await self.email_service.send_email(
                to_address=candidate_email,
                template_name=EmailTemplate.ASSESSMENT_REJECTED,
                context=context,
            )

            if success:
                await self._log_email_sent(
                    candidate_email,
                    EmailTemplate.ASSESSMENT_REJECTED,
                    assessment_id,
                )
                logger.info(
                    f"[CandidateNotif] assessment_rejected email sent",
                    extra={"assessment_id": str(assessment_id)}
                )
            else:
                await self._log_email_failed(
                    candidate_email,
                    EmailTemplate.ASSESSMENT_REJECTED,
                    assessment_id,
                    "Email service returned False",
                )

            return success

        except Exception as e:
            logger.error(
                f"[CandidateNotif] Error sending assessment_rejected notification",
                extra={
                    "assessment_id": str(assessment_id),
                    "candidate_email": candidate_email,
                    "error": str(e),
                },
                exc_info=True
            )
            await self._log_email_failed(
                candidate_email,
                EmailTemplate.ASSESSMENT_REJECTED,
                assessment_id,
                str(e),
            )
            return False

    async def _log_email_sent(
        self,
        recipient_email: str,
        template_name: EmailTemplate,
        assessment_id: Optional[uuid.UUID] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Log successful email send to database.

        Args:
            recipient_email: Email address sent to
            template_name: Template used
            assessment_id: Associated assessment ID (optional)
            metadata: Additional metadata to store
        """
        try:
            email_log = EmailLog(
                recipient_email=recipient_email,
                template_name=template_name.value,
                assessment_id=assessment_id,
                status="sent",
                subject=self._get_subject(template_name),
                provider=settings.EMAIL_PROVIDER,
                metadata=metadata or {},
            )
            self.db.add(email_log)
            await self.db.commit()

            logger.debug(
                f"[CandidateNotif] Email logged to database",
                extra={
                    "recipient": recipient_email,
                    "template": template_name.value,
                }
            )
        except Exception as e:
            logger.error(
                f"[CandidateNotif] Failed to log email send",
                extra={"error": str(e)},
                exc_info=True
            )

    async def _log_email_failed(
        self,
        recipient_email: str,
        template_name: EmailTemplate,
        assessment_id: Optional[uuid.UUID] = None,
        error_message: str = "Unknown error",
    ) -> None:
        """
        Log failed email send to database.

        Args:
            recipient_email: Email address that failed
            template_name: Template that was attempted
            assessment_id: Associated assessment ID (optional)
            error_message: Error details
        """
        try:
            email_log = EmailLog(
                recipient_email=recipient_email,
                template_name=template_name.value,
                assessment_id=assessment_id,
                status="failed",
                subject=self._get_subject(template_name),
                provider=settings.EMAIL_PROVIDER,
                error_message=error_message[:500],  # Truncate to 500 chars
            )
            self.db.add(email_log)
            await self.db.commit()

            logger.debug(
                f"[CandidateNotif] Email failure logged to database",
                extra={
                    "recipient": recipient_email,
                    "template": template_name.value,
                }
            )
        except Exception as e:
            logger.error(
                f"[CandidateNotif] Failed to log email failure",
                extra={"error": str(e)},
                exc_info=True
            )

    @staticmethod
    def _get_subject(template_name: EmailTemplate) -> str:
        """Get email subject for logging."""
        subjects = {
            EmailTemplate.ASSESSMENT_STARTED: "Your TrueMatch Assessment Has Started",
            EmailTemplate.ASSESSMENT_APPROVED: "Congratulations! Your Assessment Was Approved",
            EmailTemplate.ASSESSMENT_REJECTED: "Assessment Results",
        }
        return subjects.get(template_name, "Notification from TrueMatch")


async def get_candidate_notification_worker(
    db: AsyncSession,
    email_service: Optional[EmailService] = None,
) -> CandidateNotificationWorker:
    """
    Get candidate notification worker instance.

    Args:
        db: Database session
        email_service: Optional EmailService (created if not provided)

    Returns:
        CandidateNotificationWorker instance
    """
    return CandidateNotificationWorker(db, email_service)
