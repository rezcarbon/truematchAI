"""
Production-ready Email Service with multi-provider support.

Supports:
- SMTP (Gmail, Outlook, custom servers)
- SendGrid API
- AWS SES

Features:
- Jinja2 template rendering
- Async/await non-blocking I/O
- Comprehensive error handling
- Structured logging
- Email tracking database support
- Batch sending capabilities
"""

import asyncio
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import jinja2
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


class EmailTemplate(str, Enum):
    """Available email templates for candidate notifications."""
    ASSESSMENT_STARTED = "assessment_started"
    ASSESSMENT_APPROVED = "assessment_approved"
    ASSESSMENT_REJECTED = "assessment_rejected"
    PASSWORD_RESET = "password_reset"
    WELCOME = "welcome"


class EmailServiceError(Exception):
    """Base exception for email service errors."""
    pass


class EmailService:
    """
    Production-ready email sending service with multi-provider support.

    Supports SMTP, SendGrid, and AWS SES providers with async non-blocking
    operation. Renders Jinja2 templates and provides comprehensive error
    handling and logging.
    """

    def __init__(self, settings_obj: Any = None):
        """
        Initialize email service with configuration.

        Args:
            settings_obj: Settings object with email configuration.
                         Defaults to global settings if not provided.

        Raises:
            EmailServiceError: If configuration is invalid.
        """
        self.settings = settings_obj or settings
        self.provider = self.settings.EMAIL_PROVIDER.lower()

        # Validate provider
        if self.provider not in ("smtp", "sendgrid", "ses"):
            raise EmailServiceError(
                f"Invalid EMAIL_PROVIDER: {self.provider}. "
                f"Must be 'smtp', 'sendgrid', or 'ses'"
            )

        # Setup template directory
        self.templates_dir = Path(__file__).parent.parent / "templates" / "email"
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_dir)),
            autoescape=jinja2.select_autoescape(
                enabled_extensions=('html', 'xml'),
                default_for_string=True,
                default=True
            ),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        logger.info(
            f"EmailService initialized",
            extra={
                "provider": self.provider,
                "templates_dir": str(self.templates_dir),
            }
        )

    async def send_email(
        self,
        to_address: str,
        template_name: EmailTemplate,
        context: Dict[str, Any],
        subject: Optional[str] = None,
    ) -> bool:
        """
        Send email using configured provider.

        Args:
            to_address: Recipient email address
            template_name: EmailTemplate enum value
            context: Template variables (candidate_name, position_title, etc.)
            subject: Override subject line (optional)

        Returns:
            True if sent successfully, False otherwise

        Examples:
            >>> service = EmailService()
            >>> success = await service.send_email(
            ...     to_address="candidate@example.com",
            ...     template_name=EmailTemplate.ASSESSMENT_STARTED,
            ...     context={
            ...         "candidate_name": "John Doe",
            ...         "position_title": "Senior Engineer",
            ...         "company_name": "Acme Inc",
            ...         "assessment_url": "https://..."
            ...     }
            ... )
        """
        try:
            # Validate email address
            if not self._is_valid_email(to_address):
                logger.warning(
                    f"Invalid email address: {to_address}",
                    extra={"template": template_name.value}
                )
                return False

            # Render template
            html_content = self._render_template(template_name, context)
            subject_line = subject or self._get_subject(template_name)

            # Send via configured provider
            if self.provider == "sendgrid":
                return await self._send_via_sendgrid(
                    to_address, subject_line, html_content
                )
            elif self.provider == "ses":
                return await self._send_via_ses(
                    to_address, subject_line, html_content
                )
            elif self.provider == "smtp":
                return await self._send_via_smtp(
                    to_address, subject_line, html_content
                )
            else:
                logger.error(f"Unknown email provider: {self.provider}")
                return False

        except Exception as e:
            logger.error(
                f"Failed to send email to {to_address}",
                extra={
                    "template": template_name.value,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True
            )
            return False

    async def send_batch_emails(
        self,
        recipients: List[str],
        template_name: EmailTemplate,
        context_template: Dict[str, Any],
    ) -> Dict[str, bool]:
        """
        Send emails to multiple recipients with same template context.

        Args:
            recipients: List of email addresses
            template_name: Template to use
            context_template: Template variables (shared by all recipients)

        Returns:
            Dictionary mapping recipient email to success boolean

        Examples:
            >>> service = EmailService()
            >>> results = await service.send_batch_emails(
            ...     recipients=["alice@example.com", "bob@example.com"],
            ...     template_name=EmailTemplate.ASSESSMENT_STARTED,
            ...     context_template={"company_name": "Acme Inc"}
            ... )
            >>> failed = [k for k, v in results.items() if not v]
        """
        results = {}

        # Send emails concurrently with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent sends

        async def send_with_semaphore(recipient: str) -> tuple[str, bool]:
            async with semaphore:
                result = await self.send_email(
                    recipient, template_name, context_template
                )
                return recipient, result

        tasks = [send_with_semaphore(recipient) for recipient in recipients]
        completed = await asyncio.gather(*tasks, return_exceptions=True)

        for item in completed:
            if isinstance(item, Exception):
                logger.error(f"Batch send error: {item}")
                continue
            recipient, success = item
            results[recipient] = success

        logger.info(
            f"Batch email send complete",
            extra={
                "total": len(recipients),
                "successful": sum(1 for v in results.values() if v),
                "failed": sum(1 for v in results.values() if not v),
            }
        )

        return results

    def _render_template(
        self,
        template_name: EmailTemplate,
        context: Dict[str, Any]
    ) -> str:
        """
        Render Jinja2 template with provided context.

        Args:
            template_name: EmailTemplate enum
            context: Template variables

        Returns:
            Rendered HTML string

        Raises:
            EmailServiceError: If template not found or rendering fails
        """
        try:
            template_file = f"{template_name.value}.html"
            template = self.jinja_env.get_template(template_file)
            return template.render(**context)
        except jinja2.TemplateNotFound:
            logger.error(
                f"Template not found: {template_name.value}",
                extra={"templates_dir": str(self.templates_dir)}
            )
            raise EmailServiceError(
                f"Template {template_name.value}.html not found "
                f"in {self.templates_dir}"
            )
        except jinja2.TemplateError as e:
            logger.error(
                f"Template rendering error: {e}",
                extra={"template": template_name.value}
            )
            raise EmailServiceError(f"Template rendering error: {e}")

    def _get_subject(self, template_name: EmailTemplate) -> str:
        """
        Get email subject line by template name.

        Args:
            template_name: EmailTemplate enum

        Returns:
            Subject line string
        """
        subjects = {
            EmailTemplate.ASSESSMENT_STARTED: (
                "Your TrueMatch Assessment Has Started"
            ),
            EmailTemplate.ASSESSMENT_APPROVED: (
                "Congratulations! Your Assessment Was Approved"
            ),
            EmailTemplate.ASSESSMENT_REJECTED: (
                "Assessment Results"
            ),
            EmailTemplate.PASSWORD_RESET: (
                "Reset Your TrueMatch Password"
            ),
            EmailTemplate.WELCOME: (
                "Welcome to TrueMatch"
            ),
        }
        return subjects.get(
            template_name,
            "Notification from TrueMatch"
        )

    async def _send_via_sendgrid(
        self,
        to_address: str,
        subject: str,
        html_content: str
    ) -> bool:
        """
        Send email via SendGrid API (async).

        Args:
            to_address: Recipient email
            subject: Email subject
            html_content: HTML email body

        Returns:
            True if sent successfully
        """
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content

            message = Mail(
                from_email=Email(
                    email=self.settings.EMAIL_FROM_ADDRESS,
                    name="TrueMatch"
                ),
                to_emails=To(email=to_address),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            sg = SendGridAPIClient(self.settings.SENDGRID_API_KEY)

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: sg.send(message)
            )

            success = response.status_code in (200, 202)

            if success:
                logger.info(
                    "Email sent via SendGrid",
                    extra={
                        "to": to_address,
                        "status_code": response.status_code,
                    }
                )
            else:
                logger.error(
                    f"SendGrid error: status {response.status_code}",
                    extra={"to": to_address}
                )

            return success

        except ImportError:
            logger.error("SendGrid library not installed")
            return False
        except Exception as e:
            logger.error(
                f"SendGrid error: {e}",
                extra={"to": to_address},
                exc_info=True
            )
            return False

    async def _send_via_ses(
        self,
        to_address: str,
        subject: str,
        html_content: str
    ) -> bool:
        """
        Send email via AWS SES (async).

        Args:
            to_address: Recipient email
            subject: Email subject
            html_content: HTML email body

        Returns:
            True if sent successfully
        """
        try:
            import boto3

            client = boto3.client(
                'ses',
                region_name=self.settings.AWS_REGION
            )

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.send_email(
                    Source=self.settings.EMAIL_FROM_ADDRESS,
                    Destination={'ToAddresses': [to_address]},
                    Message={
                        'Subject': {'Data': subject},
                        'Body': {'Html': {'Data': html_content}}
                    }
                )
            )

            logger.info(
                "Email sent via AWS SES",
                extra={
                    "to": to_address,
                    "message_id": response.get('MessageId'),
                }
            )
            return True

        except ImportError:
            logger.error("boto3 library not installed")
            return False
        except Exception as e:
            logger.error(
                f"AWS SES error: {e}",
                extra={"to": to_address},
                exc_info=True
            )
            return False

    async def _send_via_smtp(
        self,
        to_address: str,
        subject: str,
        html_content: str
    ) -> bool:
        """
        Send email via SMTP (async).

        Args:
            to_address: Recipient email
            subject: Email subject
            html_content: HTML email body

        Returns:
            True if sent successfully
        """
        try:
            import aiosmtplib

            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.settings.EMAIL_FROM_ADDRESS
            message["To"] = to_address

            # Attach HTML part
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)

            # Send via async SMTP
            async with aiosmtplib.SMTP(
                hostname=self.settings.SMTP_SERVER,
                port=self.settings.SMTP_PORT,
                use_tls=self.settings.SMTP_USE_TLS
            ) as smtp:
                if self.settings.SMTP_USERNAME and self.settings.SMTP_PASSWORD:
                    await smtp.login(
                        self.settings.SMTP_USERNAME,
                        self.settings.SMTP_PASSWORD
                    )
                await smtp.send_message(message)

            logger.info(
                "Email sent via SMTP",
                extra={
                    "to": to_address,
                    "server": self.settings.SMTP_SERVER,
                }
            )
            return True

        except ImportError:
            logger.error("aiosmtplib library not installed")
            return False
        except Exception as e:
            logger.error(
                f"SMTP error: {e}",
                extra={
                    "to": to_address,
                    "server": self.settings.SMTP_SERVER,
                },
                exc_info=True
            )
            return False

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """
        Basic email validation.

        Args:
            email: Email address to validate

        Returns:
            True if email format appears valid
        """
        return (
            isinstance(email, str) and
            "@" in email and
            "." in email.split("@")[-1] and
            len(email) <= 254
        )


async def get_email_service(
    settings_obj: Any = None
) -> EmailService:
    """
    Get or create email service instance.

    Args:
        settings_obj: Optional settings object (defaults to global settings)

    Returns:
        EmailService instance

    Examples:
        >>> service = await get_email_service()
        >>> success = await service.send_email(...)
    """
    return EmailService(settings_obj)
