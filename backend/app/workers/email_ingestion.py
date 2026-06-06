"""
AI-Native Email Ingestion System - Phase A: Autonomy Layer

Monitors email inbox (IMAP) for new CV/JD submissions.
Extracts attachments and queues for assessment processing.
Sends automated responses to senders.
"""
import asyncio
import hashlib
import logging
import tempfile
from datetime import datetime, timedelta
from email import message_from_bytes
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional

import aioimap
import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


class EmailAttachment:
    """Represents extracted email attachment."""

    def __init__(self, filename: str, content: bytes, email_from: str, email_subject: str):
        self.filename = filename
        self.content = content
        self.email_from = email_from
        self.email_subject = email_subject
        self.content_hash = hashlib.sha256(content).hexdigest()
        self.received_at = datetime.utcnow()

    def is_supported(self) -> bool:
        """Check if attachment is supported format."""
        supported = {".pdf", ".docx", ".txt", ".csv", ".json", ".md"}
        ext = Path(self.filename).suffix.lower()
        return ext in supported


class EmailIngestor:
    """
    Autonomous email ingestion for assessment submissions.

    Monitors email inbox (IMAP) for CVs and JDs.
    Extracts attachments and queues for processing.
    Sends automated confirmations.
    """

    def __init__(
        self,
        imap_host: str = settings.email_imap_host,
        imap_port: int = settings.email_imap_port,
        email_address: str = settings.email_address,
        email_password: str = settings.email_password,
        smtp_host: str = settings.email_smtp_host,
        smtp_port: int = settings.email_smtp_port,
        poll_interval: int = 300,  # 5 minutes
    ):
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.email_address = email_address
        self.email_password = email_password
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.poll_interval = poll_interval
        self.is_running = False
        self.processed_message_ids = set()

    async def _connect_imap(self) -> aioimap.IMAP4:
        """Connect to IMAP server."""
        imap = await aioimap.IMAP4_SSL(self.imap_host, self.imap_port)
        await imap.login(self.email_address, self.email_password)
        return imap

    async def _connect_smtp(self) -> aiosmtplib.SMTP:
        """Connect to SMTP server."""
        smtp = aiosmtplib.SMTP(hostname=self.smtp_host, port=self.smtp_port)
        await smtp.connect()
        await smtp.login(self.email_address, self.email_password)
        return smtp

    async def extract_attachments(self, email_bytes: bytes, email_from: str, email_subject: str) -> List[EmailAttachment]:
        """
        Extract attachments from email message.

        Returns:
            List of EmailAttachment objects
        """
        attachments = []
        try:
            msg = message_from_bytes(email_bytes)

            for part in msg.walk():
                # Check if this part is an attachment
                if part.get_content_disposition() == "attachment":
                    filename = part.get_filename()
                    if not filename:
                        continue

                    content = part.get_payload(decode=True)
                    attachment = EmailAttachment(filename, content, email_from, email_subject)

                    if attachment.is_supported():
                        attachments.append(attachment)
                        logger.info(f"Extracted attachment: {filename} (hash: {attachment.content_hash})")
                    else:
                        logger.debug(f"Skipping unsupported attachment: {filename}")

        except Exception as e:
            logger.error(f"Error extracting attachments: {e}")

        return attachments

    async def send_confirmation_email(
        self,
        recipient: str,
        num_attachments: int,
        subject: str = "Assessment Processing Started",
    ):
        """Send confirmation email to sender."""
        try:
            body = f"""
Hello,

We have received your email with {num_attachments} attachment(s).

Your submission is now being processed by our AI assessment system.
You will receive an update within 60 seconds with the assessment results.

Subject: {subject}

Best regards,
TrueMatch Assessment System
"""

            msg = MIMEText(body)
            msg["Subject"] = f"Re: {subject}"
            msg["From"] = self.email_address
            msg["To"] = recipient

            async with await self._connect_smtp() as smtp:
                await smtp.send_message(msg)

            logger.info(f"Sent confirmation email to {recipient}")

        except Exception as e:
            logger.error(f"Error sending confirmation email: {e}")

    async def send_result_email(
        self,
        recipient: str,
        assessment_id: str,
        score: float,
        decision: str,
        subject: str = "Assessment Complete",
    ):
        """Send assessment results email to sender."""
        try:
            body = f"""
Hello,

Your assessment has been completed.

Assessment ID: {assessment_id}
Score: {score:.2f}
Decision: {decision}

You can view the full assessment details at:
https://truematch.example.com/assessments/{assessment_id}

Best regards,
TrueMatch Assessment System
"""

            msg = MIMEText(body)
            msg["Subject"] = f"Re: {subject} - Results Ready"
            msg["From"] = self.email_address
            msg["To"] = recipient

            async with await self._connect_smtp() as smtp:
                await smtp.send_message(msg)

            logger.info(f"Sent result email to {recipient}")

        except Exception as e:
            logger.error(f"Error sending result email: {e}")

    async def fetch_new_emails(self):
        """
        Fetch new unread emails from inbox.

        Searches for emails since last check.
        Extracts attachments and queues for processing.
        """
        try:
            imap = await self._connect_imap()

            # Select INBOX
            await imap.select("INBOX")

            # Search for recent unseen emails (since last 5 minutes)
            search_criteria = f'(UNSEEN SINCE "{self._format_date_for_imap(datetime.utcnow() - timedelta(minutes=5))}")'
            status, message_ids = await imap.search(search_criteria)

            if status != "OK":
                logger.warning(f"IMAP search failed: {status}")
                await imap.logout()
                return

            message_ids_list = message_ids[0].split()
            logger.info(f"Found {len(message_ids_list)} new emails")

            for message_id in message_ids_list:
                # Skip if already processed
                if message_id.decode() in self.processed_message_ids:
                    continue

                try:
                    # Fetch email
                    status, email_data = await imap.fetch(message_id, "(RFC822)")
                    if status != "OK":
                        continue

                    email_bytes = email_data[0][1]
                    msg = message_from_bytes(email_bytes)

                    email_from = msg.get("From", "unknown")
                    email_subject = msg.get("Subject", "No Subject")

                    logger.info(f"Processing email from {email_from}: {email_subject}")

                    # Extract attachments
                    attachments = await self.extract_attachments(email_bytes, email_from, email_subject)

                    if attachments:
                        # Send confirmation
                        await self.send_confirmation_email(email_from, len(attachments), email_subject)

                        # Queue for processing
                        await self._queue_attachments(attachments)

                        # Mark as processed
                        self.processed_message_ids.add(message_id.decode())

                        # Mark email as read
                        await imap.store(message_id, "+FLAGS", "\\Seen")

                except Exception as e:
                    logger.error(f"Error processing message {message_id}: {e}")

            await imap.logout()

        except Exception as e:
            logger.error(f"Error in fetch_new_emails: {e}")

    async def _queue_attachments(self, attachments: List[EmailAttachment]):
        """Queue attachments for assessment processing."""
        for attachment in attachments:
            logger.info(f"Queuing attachment for assessment: {attachment.filename}")
            # TODO: Integration point with Phase A job queue
            # Would save to temp file and queue assessment job

    @staticmethod
    def _format_date_for_imap(dt: datetime) -> str:
        """Format datetime for IMAP search."""
        return dt.strftime("%d-%b-%Y")

    async def start_polling(self):
        """Start polling for new emails."""
        self.is_running = True
        logger.info(f"Email ingestion started (polling every {self.poll_interval} seconds)")

        while self.is_running:
            try:
                await self.fetch_new_emails()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error in email polling loop: {e}")
                await asyncio.sleep(self.poll_interval)

    def stop_polling(self):
        """Stop polling for new emails."""
        self.is_running = False
        logger.info("Email ingestion stopped")


# Global email ingestor instance
_email_ingestor: Optional[EmailIngestor] = None


def get_email_ingestor() -> EmailIngestor:
    """Get or create email ingestor."""
    global _email_ingestor
    if _email_ingestor is None:
        _email_ingestor = EmailIngestor()
    return _email_ingestor


async def start_email_ingestion():
    """Start email ingestion on application startup."""
    if not settings.email_ingestion_enabled:
        logger.info("Email ingestion disabled in configuration")
        return

    ingestor = get_email_ingestor()
    # Start in background task
    asyncio.create_task(ingestor.start_polling())
    logger.info("Email ingestion started on application startup")


def stop_email_ingestion():
    """Stop email ingestion on application shutdown."""
    ingestor = get_email_ingestor()
    ingestor.stop_polling()
    logger.info("Email ingestion stopped on application shutdown")
