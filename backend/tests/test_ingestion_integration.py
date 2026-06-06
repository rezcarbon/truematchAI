"""Integration tests for file and email ingestion workers.

Tests the complete pipeline:
1. File detection -> text extraction -> ingest queue item creation -> Celery task enqueue
2. Email attachment detection -> text extraction -> ingest queue item creation -> Celery task enqueue
"""
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base
from app.models.ingest_queue import (
    IngestQueueItem,
    IngestSource,
    IngestStatus,
    IngestType,
)


@pytest.fixture
async def test_db():
    """Create an in-memory SQLite database for testing."""
    # Use SQLite in-memory for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSessionLocal = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

    await engine.dispose()


class TestFileIngestionWorker:
    """Test file ingestion worker."""

    @pytest.mark.asyncio
    async def test_cv_file_processing(self, test_db: AsyncSession):
        """Test CV file is detected, extracted, and enqueued."""
        from app.workers.file_ingestion import DocumentFileEventHandler

        handler = DocumentFileEventHandler("cv")

        # Mock the extract_text function
        with patch("app.workers.file_ingestion.DocumentFileEventHandler._extract_text") as mock_extract:
            mock_extract.return_value = "John Doe\nSoftware Engineer\nPython, JavaScript"

            # Create a test PDF file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(b"%PDF-1.4\n%test content")
                test_file = Path(f.name)

            try:
                # Mock AsyncSessionLocal to use test_db
                with patch("app.workers.file_ingestion.AsyncSessionLocal") as mock_session:
                    mock_session.return_value.__aenter__ = AsyncMock(return_value=test_db)
                    mock_session.return_value.__aexit__ = AsyncMock(return_value=None)

                    # Mock Celery task
                    with patch("app.workers.file_ingestion.DocumentFileEventHandler._enqueue_processing_task") as mock_enqueue:
                        await handler._process_and_queue(test_file)

                        # Verify extract_text was called
                        mock_extract.assert_called_once()

                        # Verify task was enqueued
                        mock_enqueue.assert_called_once()

            finally:
                test_file.unlink()

    @pytest.mark.asyncio
    async def test_jd_file_processing(self, test_db: AsyncSession):
        """Test JD file is detected and processed."""
        from app.workers.file_ingestion import DocumentFileEventHandler

        handler = DocumentFileEventHandler("jd")

        with patch("app.workers.file_ingestion.DocumentFileEventHandler._extract_text") as mock_extract:
            mock_extract.return_value = "Senior Engineer\nLocation: SF\nRequirements: 5+ years Python"

            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
                f.write(b"PK\x03\x04\x14\x00\x06\x00")  # DOCX magic bytes
                test_file = Path(f.name)

            try:
                with patch("app.workers.file_ingestion.AsyncSessionLocal") as mock_session:
                    mock_session.return_value.__aenter__ = AsyncMock(return_value=test_db)
                    mock_session.return_value.__aexit__ = AsyncMock(return_value=None)

                    with patch("app.workers.file_ingestion.DocumentFileEventHandler._enqueue_processing_task"):
                        await handler._process_and_queue(test_file)

                        # Verify ingest type is JD
                        assert handler.folder_type == "jd"

            finally:
                test_file.unlink()

    @pytest.mark.asyncio
    async def test_duplicate_file_detection(self):
        """Test duplicate files are skipped by hash."""
        from app.workers.file_ingestion import DocumentFileEventHandler

        handler = DocumentFileEventHandler("cv")

        # Create two identical files
        content = b"Test CV content"
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f1:
            f1.write(content)
            file1 = Path(f1.name)

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f2:
            f2.write(content)
            file2 = Path(f2.name)

        try:
            # Process first file
            hash1 = await handler._get_file_hash(file1)
            handler.processed_hashes.add(hash1)

            # Check hash of second file
            hash2 = await handler._get_file_hash(file2)

            assert hash1 == hash2
            assert hash2 in handler.processed_hashes

        finally:
            file1.unlink()
            file2.unlink()


class TestEmailIngestionWorker:
    """Test email ingestion worker."""

    @pytest.mark.asyncio
    async def test_email_attachment_extraction(self):
        """Test email attachments are extracted correctly."""
        from app.workers.email_ingestion import EmailIngestor

        ingestor = EmailIngestor()

        # Create a mock email with attachment
        from email.mime.application import MIMEApplication
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart()
        msg["From"] = "candidate@example.com"
        msg["Subject"] = "CV Submission"

        # Add a PDF attachment
        attachment = MIMEApplication(b"%PDF-1.4\nTest content")
        attachment.add_header("Content-Disposition", "attachment", filename="resume.pdf")
        msg.attach(attachment)

        email_bytes = msg.as_bytes()

        # Extract attachments
        attachments = await ingestor.extract_attachments(
            email_bytes,
            "candidate@example.com",
            "CV Submission",
            "msg-id-123",
        )

        assert len(attachments) == 1
        assert attachments[0].filename == "resume.pdf"
        assert attachments[0].is_supported()

    @pytest.mark.asyncio
    async def test_email_address_extraction(self):
        """Test email address parsing from 'Name <email>' format."""
        from app.workers.email_ingestion import EmailIngestor

        ingestor = EmailIngestor()

        # Test various formats
        assert ingestor._extract_email_address("John Doe <john@example.com>") == "john@example.com"
        assert ingestor._extract_email_address("jane@example.com") == "jane@example.com"
        assert (
            ingestor._extract_email_address("Jane Smith <jane.smith@example.com>")
            == "jane.smith@example.com"
        )

    @pytest.mark.asyncio
    async def test_ingest_type_detection(self):
        """Test ingest type is correctly detected from filename."""
        from app.workers.email_ingestion import EmailIngestor

        ingestor = EmailIngestor()

        # Test CV detection
        assert ingestor._detect_ingest_type("John_Resume.pdf") == IngestType.cv
        assert ingestor._detect_ingest_type("CV_2024.docx") == IngestType.cv
        assert ingestor._detect_ingest_type("Curriculum_Vitae.txt") == IngestType.cv

        # Test JD detection
        assert ingestor._detect_ingest_type("Senior_Engineer_JD.pdf") == IngestType.jd_draft
        assert ingestor._detect_ingest_type("job_description.docx") == IngestType.jd_draft
        assert ingestor._detect_ingest_type("role_posting.txt") == IngestType.jd_draft

        # Test default (CV)
        assert ingestor._detect_ingest_type("document.pdf") == IngestType.cv


class TestIngestQueueProcessing:
    """Test ingest queue item processing."""

    @pytest.mark.asyncio
    async def test_ingest_item_creation(self, test_db: AsyncSession):
        """Test ingest queue item is created correctly."""
        # Create an ingest item
        item = IngestQueueItem(
            source=IngestSource.folder,
            ingest_type=IngestType.cv,
            status=IngestStatus.pending,
            extracted_text="John Doe\nSoftware Engineer",
            source_ref="/inbox/cv/resume.pdf",
            retry_count=0,
        )

        test_db.add(item)
        await test_db.commit()

        # Verify item was created
        assert item.id is not None
        assert item.source == IngestSource.folder
        assert item.ingest_type == IngestType.cv
        assert item.status == IngestStatus.pending

    @pytest.mark.asyncio
    async def test_email_ingest_item_with_sender_meta(self, test_db: AsyncSession):
        """Test ingest item from email includes sender metadata."""
        item = IngestQueueItem(
            source=IngestSource.email,
            ingest_type=IngestType.cv,
            status=IngestStatus.pending,
            extracted_text="Jane Doe\nData Scientist",
            source_ref="msg-id-456",
            sender_meta={
                "name": "Jane Doe <jane@example.com>",
                "email": "jane@example.com",
                "filename": "resume.pdf",
                "subject": "CV Submission",
            },
            retry_count=0,
        )

        test_db.add(item)
        await test_db.commit()

        assert item.source == IngestSource.email
        assert item.sender_meta["email"] == "jane@example.com"
        assert item.sender_meta["filename"] == "resume.pdf"

    @pytest.mark.asyncio
    async def test_ingest_item_retry_tracking(self, test_db: AsyncSession):
        """Test retry count is tracked correctly."""
        item = IngestQueueItem(
            source=IngestSource.folder,
            ingest_type=IngestType.cv,
            status=IngestStatus.pending,
            extracted_text="Test CV",
            source_ref="/test/cv.pdf",
            retry_count=0,
        )

        test_db.add(item)
        await test_db.commit()

        # Simulate retry
        item.retry_count += 1
        item.status = IngestStatus.processing
        await test_db.commit()

        assert item.retry_count == 1

        # Simulate another retry
        item.retry_count += 1
        await test_db.commit()

        assert item.retry_count == 2


class TestFileSystemMonitor:
    """Test file system monitor integration."""

    def test_monitor_initialization(self):
        """Test monitor initializes with correct paths."""
        from app.workers.file_ingestion import FileSystemMonitor

        monitor = FileSystemMonitor()

        assert "cv" in monitor.watch_paths
        assert "jd" in monitor.watch_paths
        assert not monitor.is_running

    def test_monitor_lifecycle(self):
        """Test monitor start/stop lifecycle."""
        from app.workers.file_ingestion import FileSystemMonitor

        monitor = FileSystemMonitor()

        # Start monitor
        monitor.start()
        assert monitor.is_running
        assert len(monitor.event_handlers) == 2

        # Stop monitor
        monitor.stop()
        assert not monitor.is_running

    def test_monitor_context_manager(self):
        """Test monitor can be used as context manager."""
        from app.workers.file_ingestion import FileSystemMonitor

        with FileSystemMonitor() as monitor:
            assert monitor.is_running

        assert not monitor.is_running


class TestEmailIngestorLifecycle:
    """Test email ingestor lifecycle."""

    @pytest.mark.asyncio
    async def test_polling_loop_iteration(self):
        """Test email polling loop can iterate."""
        from app.workers.email_ingestion import EmailIngestor

        ingestor = EmailIngestor(
            imap_host="imap.example.com",
            imap_port=993,
            email_address="test@example.com",
            email_password="password",
            poll_interval=1.0,
        )

        # Mock the fetch_new_emails method
        with patch.object(ingestor, "fetch_new_emails", new_callable=AsyncMock) as mock_fetch:
            # Create a task for short polling
            ingestor.is_running = True

            async def stop_after_one_iteration():
                await asyncio.sleep(0.5)
                ingestor.is_running = False

            # Start polling and stop after one iteration
            polling_task = asyncio.create_task(ingestor._polling_loop())
            stop_task = asyncio.create_task(stop_after_one_iteration())

            try:
                await asyncio.wait_for(
                    asyncio.gather(polling_task, stop_task),
                    timeout=5,
                )
            except asyncio.CancelledError:
                pass

            # Verify fetch was called at least once
            assert mock_fetch.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
