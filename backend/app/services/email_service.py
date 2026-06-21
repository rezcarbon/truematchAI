"""Email service for sending notifications via email."""
import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""

    # Email templates
    TEMPLATES = {
        "interview_scheduled": {
            "subject": "Interview Scheduled for {candidate_name}",
            "body": """
Dear {recruiter_name},

A new interview has been scheduled:

Candidate: {candidate_name}
Position: {position_title}
Date & Time: {scheduled_at}
Location/Link: {location}

Please confirm your attendance by clicking the link below:
{action_url}

Best regards,
TrueMatch Team
            """,
        },
        "scorecard_request": {
            "subject": "Scorecard Needed for {candidate_name}",
            "body": """
Dear {recruiter_name},

Please complete the scorecard for:

Candidate: {candidate_name}
Position: {position_title}
Interview Date: {interview_date}

Complete the scorecard here:
{action_url}

Best regards,
TrueMatch Team
            """,
        },
        "candidate_advanced": {
            "subject": "{candidate_name} Advanced to {new_stage}",
            "body": """
Dear {recruiter_name},

{candidate_name} has advanced in the pipeline:

Position: {position_title}
New Stage: {new_stage}
Date: {stage_date}

View candidate profile:
{action_url}

Best regards,
TrueMatch Team
            """,
        },
        "pipeline_update": {
            "subject": "Pipeline Update: {position_title}",
            "body": """
Dear {recruiter_name},

There's an update to your pipeline:

Position: {position_title}
Update: {update_message}
Date: {update_date}

View full pipeline:
{action_url}

Best regards,
TrueMatch Team
            """,
        },
        "system_alert": {
            "subject": "System Alert from TrueMatch",
            "body": """
Dear {user_name},

{message}

Details: {action_url}

Best regards,
TrueMatch Team
            """,
        },
    }

    @staticmethod
    async def send_notification_email(
        recipient_email: str,
        notification_type: str,
        title: str,
        message: str,
        action_url: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> bool:
        """
        Send a notification email to a user.

        Args:
            recipient_email: Recipient email address
            notification_type: Type of notification (used to select template)
            title: Email title
            message: Email message body
            action_url: Optional action URL
            context: Optional context variables for template rendering

        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Check if email service is configured
            if not EmailService._is_configured():
                logger.warning(
                    "Email service not configured - skipping email send",
                    extra={"recipient": recipient_email, "type": notification_type},
                )
                return False

            # Build email content
            email_content = EmailService._build_email_content(
                notification_type,
                title,
                message,
                action_url,
                context or {},
            )

            # Send email
            result = await EmailService._send_email(
                recipient_email,
                email_content["subject"],
                email_content["body"],
            )

            if result:
                logger.info(
                    f"Notification email sent: {notification_type}",
                    extra={
                        "recipient": recipient_email,
                        "type": notification_type,
                    },
                )
            else:
                logger.error(
                    f"Failed to send notification email: {notification_type}",
                    extra={"recipient": recipient_email},
                )

            return result

        except Exception as e:
            logger.error(
                f"Error sending notification email: {str(e)}",
                extra={"recipient": recipient_email, "type": notification_type},
            )
            return False

    @staticmethod
    def _is_configured() -> bool:
        """Check if email service is configured."""
        return bool(
            settings.smtp_server
            and settings.smtp_port
            and settings.smtp_username
            and settings.smtp_password
        )

    @staticmethod
    def _build_email_content(
        notification_type: str,
        title: str,
        message: str,
        action_url: Optional[str],
        context: dict,
    ) -> dict:
        """Build email subject and body from template."""
        template = EmailService.TEMPLATES.get(
            notification_type,
            {
                "subject": title,
                "body": message,
            },
        )

        subject = template.get("subject", title)
        body = template.get("body", message)

        # Add context variables
        context_with_defaults = {
            "action_url": action_url or "",
            "message": message,
            **context,
        }

        # Format with context (safe - won't fail if key missing)
        try:
            subject = subject.format(**context_with_defaults)
            body = body.format(**context_with_defaults)
        except KeyError:
            # If template variables missing, use defaults
            pass

        return {
            "subject": subject,
            "body": body,
        }

    @staticmethod
    async def _send_email(
        recipient: str,
        subject: str,
        body: str,
    ) -> bool:
        """
        Send email using configured SMTP service.

        Supports: Standard SMTP (TLS/STARTTLS), SendGrid API, AWS SES

        Args:
            recipient: Email recipient
            subject: Email subject
            body: Email body (plain text or HTML)

        Returns:
            True if successful, False otherwise
        """
        try:
            if not EmailService._is_configured():
                logger.warning(
                    "Email service not configured - skipping send",
                    extra={"recipient": recipient},
                )
                return False

            # Use standard SMTP (most common)
            if settings.smtp_server:
                return await EmailService._send_via_smtp(
                    recipient, subject, body
                )

            # Alternative: SendGrid API
            elif settings.sendgrid_api_key:
                return await EmailService._send_via_sendgrid(
                    recipient, subject, body
                )

            # Alternative: AWS SES
            elif settings.aws_ses_region:
                return await EmailService._send_via_aws_ses(
                    recipient, subject, body
                )

            else:
                logger.error("No email service configured")
                return False

        except Exception as e:
            logger.error(
                f"Failed to send email: {str(e)}",
                extra={"recipient": recipient, "subject": subject},
            )
            return False

    @staticmethod
    async def _send_via_smtp(
        recipient: str,
        subject: str,
        body: str,
    ) -> bool:
        """Send email using SMTP (TLS/STARTTLS)."""
        try:
            # Run SMTP in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                EmailService._send_smtp_sync,
                recipient,
                subject,
                body,
            )
        except Exception as e:
            logger.error(f"SMTP send failed: {str(e)}", extra={"recipient": recipient})
            return False

    @staticmethod
    def _send_smtp_sync(recipient: str, subject: str, body: str) -> bool:
        """Synchronous SMTP implementation."""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
            msg["To"] = recipient
            msg["Subject"] = subject

            # Attach body as both plain text and HTML
            msg.attach(MIMEText(body, "plain", "utf-8"))

            # Connect to SMTP server
            if settings.smtp_use_tls:
                # STARTTLS (port 587)
                smtp = smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=10)
                smtp.starttls()
            else:
                # Direct TLS (port 465) or plain (port 25)
                smtp = smtplib.SMTP_SSL(
                    settings.smtp_server, settings.smtp_port, timeout=10
                )

            # Authenticate
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password)

            # Send
            smtp.send_message(msg)
            smtp.quit()

            logger.info(
                "Email sent successfully",
                extra={
                    "recipient": recipient,
                    "subject": subject,
                    "from": settings.smtp_from_email,
                },
            )
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error(
                "SMTP authentication failed - check credentials",
                extra={"recipient": recipient},
            )
            return False

        except smtplib.SMTPException as e:
            logger.error(
                f"SMTP error: {str(e)}",
                extra={"recipient": recipient},
            )
            return False

        except Exception as e:
            logger.error(
                f"Unexpected SMTP error: {str(e)}",
                extra={"recipient": recipient},
            )
            return False

    @staticmethod
    async def _send_via_sendgrid(
        recipient: str,
        subject: str,
        body: str,
    ) -> bool:
        """Send email using SendGrid API."""
        try:
            # Run SendGrid in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                EmailService._send_sendgrid_sync,
                recipient,
                subject,
                body,
            )
        except Exception as e:
            logger.error(f"SendGrid send failed: {str(e)}", extra={"recipient": recipient})
            return False

    @staticmethod
    def _send_sendgrid_sync(recipient: str, subject: str, body: str) -> bool:
        """Synchronous SendGrid implementation."""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content

            # Create email
            mail = Mail(
                from_email=Email(settings.smtp_from_email, settings.smtp_from_name),
                to_emails=To(recipient),
                subject=subject,
                plain_text_content=Content("text/plain", body),
            )

            # Send via SendGrid
            sg = SendGridAPIClient(settings.sendgrid_api_key)
            response = sg.send(mail)

            if response.status_code in [200, 201, 202]:
                logger.info(
                    "Email sent via SendGrid successfully",
                    extra={
                        "recipient": recipient,
                        "subject": subject,
                        "status_code": response.status_code,
                    },
                )
                return True
            else:
                logger.error(
                    f"SendGrid returned status {response.status_code}",
                    extra={"recipient": recipient},
                )
                return False

        except ImportError:
            logger.error(
                "SendGrid library not installed. Run: pip install sendgrid",
                extra={"recipient": recipient},
            )
            return False

        except Exception as e:
            logger.error(
                f"SendGrid error: {str(e)}",
                extra={"recipient": recipient},
            )
            return False

    @staticmethod
    async def _send_via_aws_ses(
        recipient: str,
        subject: str,
        body: str,
    ) -> bool:
        """Send email using AWS SES."""
        try:
            # Run AWS SES in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                EmailService._send_aws_ses_sync,
                recipient,
                subject,
                body,
            )
        except Exception as e:
            logger.error(f"AWS SES send failed: {str(e)}", extra={"recipient": recipient})
            return False

    @staticmethod
    def _send_aws_ses_sync(recipient: str, subject: str, body: str) -> bool:
        """Synchronous AWS SES implementation."""
        try:
            import boto3
            from botocore.exceptions import ClientError

            # Create SES client
            ses_client = boto3.client(
                "ses",
                region_name=settings.aws_ses_region,
            )

            # Send email
            response = ses_client.send_email(
                Source=f"{settings.smtp_from_name} <{settings.smtp_from_email}>",
                Destination={"ToAddresses": [recipient]},
                Message={
                    "Subject": {
                        "Data": subject,
                        "Charset": "UTF-8",
                    },
                    "Body": {
                        "Text": {
                            "Data": body,
                            "Charset": "UTF-8",
                        }
                    },
                },
            )

            message_id = response.get("MessageId")
            logger.info(
                "Email sent via AWS SES successfully",
                extra={
                    "recipient": recipient,
                    "subject": subject,
                    "message_id": message_id,
                },
            )
            return True

        except ImportError:
            logger.error(
                "boto3 library not installed. Run: pip install boto3",
                extra={"recipient": recipient},
            )
            return False

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")

            if error_code == "MessageRejected":
                logger.error(
                    f"SES rejected message - sender not verified. Verify {settings.smtp_from_email} in SES console",
                    extra={"recipient": recipient},
                )
            elif error_code == "ConfigurationSetDoesNotExist":
                logger.error(
                    "SES configuration set mismatch",
                    extra={"recipient": recipient},
                )
            elif error_code == "Throttling":
                logger.warning(
                    f"SES throttled - in sandbox mode? Add {recipient} to verified addresses",
                    extra={"recipient": recipient},
                )
            else:
                logger.error(
                    f"SES error {error_code}: {str(e)}",
                    extra={"recipient": recipient},
                )

            return False

        except Exception as e:
            logger.error(
                f"AWS SES unexpected error: {str(e)}",
                extra={"recipient": recipient},
            )
            return False


class EmailTemplate:
    """Email template builder for custom emails."""

    @staticmethod
    def interview_scheduled(
        recruiter_name: str,
        candidate_name: str,
        position_title: str,
        scheduled_at: str,
        location: str,
        action_url: str,
    ) -> tuple:
        """Build interview scheduled email."""
        context = {
            "recruiter_name": recruiter_name,
            "candidate_name": candidate_name,
            "position_title": position_title,
            "scheduled_at": scheduled_at,
            "location": location,
            "action_url": action_url,
        }
        return EmailService._build_email_content(
            "interview_scheduled",
            f"Interview Scheduled for {candidate_name}",
            "",
            action_url,
            context,
        )

    @staticmethod
    def scorecard_request(
        recruiter_name: str,
        candidate_name: str,
        position_title: str,
        interview_date: str,
        action_url: str,
    ) -> tuple:
        """Build scorecard request email."""
        context = {
            "recruiter_name": recruiter_name,
            "candidate_name": candidate_name,
            "position_title": position_title,
            "interview_date": interview_date,
            "action_url": action_url,
        }
        return EmailService._build_email_content(
            "scorecard_request",
            f"Scorecard Needed for {candidate_name}",
            "",
            action_url,
            context,
        )

    @staticmethod
    def candidate_advanced(
        recruiter_name: str,
        candidate_name: str,
        position_title: str,
        new_stage: str,
        stage_date: str,
        action_url: str,
    ) -> tuple:
        """Build candidate advanced email."""
        context = {
            "recruiter_name": recruiter_name,
            "candidate_name": candidate_name,
            "position_title": position_title,
            "new_stage": new_stage,
            "stage_date": stage_date,
            "action_url": action_url,
        }
        return EmailService._build_email_content(
            "candidate_advanced",
            f"{candidate_name} Advanced to {new_stage}",
            "",
            action_url,
            context,
        )
