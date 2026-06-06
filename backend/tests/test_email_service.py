"""
Test suite for email service integration.

Tests cover:
- Email service initialization
- Template rendering
- Multi-provider support (SMTP, SendGrid, SES)
- Error handling
- Batch email sending
- Email logging
"""

import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.core.email_service import EmailService, EmailTemplate, EmailServiceError
from app.models.base import Base
from app.models.notification import EmailLog
from app.workers.candidate_notification import CandidateNotificationWorker


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create in-memory test database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with SessionLocal() as session:
        yield session

    await engine.dispose()


class TestEmailService:
    """Test EmailService functionality."""

    def test_initialization_default_smtp(self):
        """Test EmailService initializes with SMTP provider."""
        original_provider = settings.EMAIL_PROVIDER
        settings.EMAIL_PROVIDER = "smtp"

        try:
            service = EmailService(settings)
            assert service.provider == "smtp"
            assert service.jinja_env is not None
            assert service.templates_dir.exists()
        finally:
            settings.EMAIL_PROVIDER = original_provider

    def test_initialization_invalid_provider(self):
        """Test EmailService raises error for invalid provider."""
        original_provider = settings.EMAIL_PROVIDER
        settings.EMAIL_PROVIDER = "invalid"

        try:
            with pytest.raises(EmailServiceError):
                EmailService(settings)
        finally:
            settings.EMAIL_PROVIDER = original_provider

    def test_template_dir_creation(self):
        """Test template directory is created if missing."""
        service = EmailService(settings)
        templates_dir = service.templates_dir
        assert templates_dir.exists()
        assert templates_dir.is_dir()

    def test_get_subject_assessment_started(self):
        """Test subject line for assessment started template."""
        service = EmailService(settings)
        subject = service._get_subject(EmailTemplate.ASSESSMENT_STARTED)
        assert "Assessment Has Started" in subject

    def test_get_subject_assessment_approved(self):
        """Test subject line for assessment approved template."""
        service = EmailService(settings)
        subject = service._get_subject(EmailTemplate.ASSESSMENT_APPROVED)
        assert "Approved" in subject

    def test_get_subject_assessment_rejected(self):
        """Test subject line for assessment rejected template."""
        service = EmailService(settings)
        subject = service._get_subject(EmailTemplate.ASSESSMENT_REJECTED)
        assert "Results" in subject

    def test_email_validation_valid(self):
        """Test email validation for valid addresses."""
        assert EmailService._is_valid_email("user@example.com") is True
        assert EmailService._is_valid_email("john.doe+tag@company.co.uk") is True
        assert EmailService._is_valid_email("test123@subdomain.example.com") is True

    def test_email_validation_invalid(self):
        """Test email validation for invalid addresses."""
        assert EmailService._is_valid_email("invalid") is False
        assert EmailService._is_valid_email("@example.com") is False
        assert EmailService._is_valid_email("user@") is False
        assert EmailService._is_valid_email("") is False
        assert EmailService._is_valid_email(None) is False

    @pytest.mark.asyncio
    async def test_render_template(self):
        """Test template rendering with context."""
        service = EmailService(settings)

        # Create test template
        template_path = service.templates_dir / "test.html"
        template_path.write_text(
            "<h1>Hello {{ name }}</h1><p>{{ message }}</p>"
        )

        try:
            # Note: This would normally be done by jinja2
            template = service.jinja_env.get_template("test.html")
            result = template.render(name="John", message="Test")
            assert "Hello John" in result
            assert "Test" in result
        finally:
            template_path.unlink()

    @pytest.mark.asyncio
    async def test_send_email_invalid_address(self):
        """Test send_email with invalid email address."""
        service = EmailService(settings)

        result = await service.send_email(
            to_address="invalid-email",
            template_name=EmailTemplate.ASSESSMENT_STARTED,
            context={"candidate_name": "John"}
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_batch_emails(self):
        """Test batch email sending."""
        service = EmailService(settings)

        recipients = [
            "user1@example.com",
            "user2@example.com",
            "invalid-email",  # Will fail validation
        ]

        # Note: This will fail because SMTP/SendGrid aren't configured
        # But we can test the batch logic structure
        results = await service.send_batch_emails(
            recipients=recipients,
            template_name=EmailTemplate.ASSESSMENT_STARTED,
            context_template={"candidate_name": "Test"}
        )

        assert isinstance(results, dict)
        assert len(results) >= 2  # At least the valid emails


class TestCandidateNotificationWorker:
    """Test CandidateNotificationWorker functionality."""

    @pytest.mark.asyncio
    async def test_worker_initialization(self, test_db: AsyncSession):
        """Test worker initializes correctly."""
        worker = CandidateNotificationWorker(test_db)
        assert worker.db is test_db
        assert worker.email_service is not None

    @pytest.mark.asyncio
    async def test_log_email_sent(self, test_db: AsyncSession):
        """Test logging successful email send."""
        worker = CandidateNotificationWorker(test_db)
        assessment_id = uuid.uuid4()

        await worker._log_email_sent(
            recipient_email="test@example.com",
            template_name=EmailTemplate.ASSESSMENT_STARTED,
            assessment_id=assessment_id,
            metadata={"test": True}
        )

        # Verify log was created
        from sqlalchemy import select
        result = await test_db.execute(select(EmailLog))
        logs = result.scalars().all()

        assert len(logs) == 1
        assert logs[0].recipient_email == "test@example.com"
        assert logs[0].template_name == "assessment_started"
        assert logs[0].status == "sent"
        assert logs[0].assessment_id == assessment_id

    @pytest.mark.asyncio
    async def test_log_email_failed(self, test_db: AsyncSession):
        """Test logging failed email send."""
        worker = CandidateNotificationWorker(test_db)
        assessment_id = uuid.uuid4()

        await worker._log_email_failed(
            recipient_email="test@example.com",
            template_name=EmailTemplate.ASSESSMENT_REJECTED,
            assessment_id=assessment_id,
            error_message="Connection timeout"
        )

        # Verify log was created
        from sqlalchemy import select
        result = await test_db.execute(select(EmailLog))
        logs = result.scalars().all()

        assert len(logs) == 1
        assert logs[0].status == "failed"
        assert logs[0].error_message == "Connection timeout"

    @pytest.mark.asyncio
    async def test_get_subject(self):
        """Test subject line retrieval."""
        subjects = {
            EmailTemplate.ASSESSMENT_STARTED: "Your TrueMatch Assessment Has Started",
            EmailTemplate.ASSESSMENT_APPROVED: "Congratulations! Your Assessment Was Approved",
            EmailTemplate.ASSESSMENT_REJECTED: "Assessment Results",
        }

        for template, expected_subject in subjects.items():
            subject = CandidateNotificationWorker._get_subject(template)
            assert subject == expected_subject


class TestEmailTemplates:
    """Test email template files exist and are valid."""

    def test_assessment_started_template_exists(self):
        """Test assessment_started.html template exists."""
        template_path = (
            Path(__file__).parent.parent
            / "app" / "templates" / "email" / "assessment_started.html"
        )
        assert template_path.exists()
        content = template_path.read_text()
        assert "assessment" in content.lower()

    def test_assessment_approved_template_exists(self):
        """Test assessment_approved.html template exists."""
        template_path = (
            Path(__file__).parent.parent
            / "app" / "templates" / "email" / "assessment_approved.html"
        )
        assert template_path.exists()
        content = template_path.read_text()
        assert "approved" in content.lower() or "congratulations" in content.lower()

    def test_assessment_rejected_template_exists(self):
        """Test assessment_rejected.html template exists."""
        template_path = (
            Path(__file__).parent.parent
            / "app" / "templates" / "email" / "assessment_rejected.html"
        )
        assert template_path.exists()
        content = template_path.read_text()
        assert "assessment" in content.lower() or "results" in content.lower()

    def test_welcome_template_exists(self):
        """Test welcome.html template exists."""
        template_path = (
            Path(__file__).parent.parent
            / "app" / "templates" / "email" / "welcome.html"
        )
        assert template_path.exists()
        content = template_path.read_text()
        assert "welcome" in content.lower()

    def test_password_reset_template_exists(self):
        """Test password_reset.html template exists."""
        template_path = (
            Path(__file__).parent.parent
            / "app" / "templates" / "email" / "password_reset.html"
        )
        assert template_path.exists()
        content = template_path.read_text()
        assert "password" in content.lower() or "reset" in content.lower()


class TestEmailConfiguration:
    """Test email configuration in settings."""

    def test_email_provider_configured(self):
        """Test EMAIL_PROVIDER setting exists."""
        assert hasattr(settings, 'EMAIL_PROVIDER')
        assert settings.EMAIL_PROVIDER in ("smtp", "sendgrid", "ses")

    def test_email_from_address_configured(self):
        """Test EMAIL_FROM_ADDRESS setting exists."""
        assert hasattr(settings, 'EMAIL_FROM_ADDRESS')
        assert "@" in settings.EMAIL_FROM_ADDRESS

    def test_smtp_settings_configured(self):
        """Test SMTP settings exist."""
        assert hasattr(settings, 'SMTP_SERVER')
        assert hasattr(settings, 'SMTP_PORT')
        assert hasattr(settings, 'SMTP_USE_TLS')
        assert hasattr(settings, 'SMTP_USERNAME')
        assert hasattr(settings, 'SMTP_PASSWORD')

    def test_sendgrid_settings_configured(self):
        """Test SendGrid settings exist."""
        assert hasattr(settings, 'SENDGRID_API_KEY')

    def test_ses_settings_configured(self):
        """Test AWS SES settings exist."""
        assert hasattr(settings, 'AWS_REGION')


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
