"""
AI-Native File Ingestion System - Phase A: Autonomy Layer

Monitors file system for new CV/JD submissions.
Automatically extracts text and queues assessments for processing.
"""
import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Optional
from uuid import UUID

import aiofiles
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.ingest_queue import (
    IngestQueueItem,
    IngestSource,
    IngestStatus,
    IngestType,
)

logger = logging.getLogger(__name__)


class DocumentFileEventHandler(FileSystemEventHandler):
    """
    Watches for new files in CV/JD inbox directories.

    Supported formats:
    - CV: PDF, DOCX, DOC, TXT
    - JD: PDF, DOCX, DOC, TXT
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}

    def __init__(self, folder_type: str):
        """Initialize handler.

        Args:
            folder_type: Either "cv" or "jd" to determine ingest type
        """
        self.folder_type = folder_type
        self.processed_hashes: set[str] = set()

    async def _get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content."""
        sha256_hash = hashlib.sha256()
        async with aiofiles.open(file_path, "rb") as f:
            async for byte_block in f:
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def _is_file_ready(self, file_path: Path, wait_time: float = 2.0) -> bool:
        """
        Check if file is ready for processing.
        Waits to ensure file write is complete.
        """
        try:
            initial_size = file_path.stat().st_size
            await asyncio.sleep(wait_time)
            current_size = file_path.stat().st_size
            return initial_size == current_size and current_size > 0
        except OSError:
            return False

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Check if supported extension
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            logger.debug(f"Skipping unsupported file: {file_path.name}")
            return

        # Queue async processing
        try:
            asyncio.create_task(self._process_file_async(file_path))
        except Exception as e:
            logger.error(f"Error queuing file {file_path.name}: {e}")

    async def _process_file_async(self, file_path: Path) -> None:
        """Process file asynchronously."""
        try:
            # Wait for file write to complete
            is_ready = await self._is_file_ready(file_path)
            if not is_ready:
                logger.warning(f"File not ready after wait: {file_path.name}")
                return

            # Calculate hash for duplicate detection
            file_hash = await self._get_file_hash(file_path)
            if file_hash in self.processed_hashes:
                logger.info(f"Skipping duplicate file: {file_path.name} (hash: {file_hash})")
                return

            self.processed_hashes.add(file_hash)

            # Process the file
            await self._process_and_queue(file_path)

        except Exception as e:
            logger.error(f"Error processing file {file_path.name}: {e}")

    async def _process_and_queue(self, file_path: Path) -> None:
        """Extract text from file, create ingest queue item, and enqueue task."""
        async with AsyncSessionLocal() as db:
            try:
                # Read file
                async with aiofiles.open(file_path, "rb") as f:
                    file_content = await f.read()

                if not file_content:
                    logger.warning(f"Empty file: {file_path}")
                    return

                # Determine ingest type
                ingest_type = (
                    IngestType.cv
                    if self.folder_type == "cv"
                    else IngestType.jd_draft
                )

                # Extract text using the intake engine
                extracted_text = await self._extract_text(file_content, file_path)
                if not extracted_text:
                    logger.warning(f"No text extracted from {file_path}")
                    return

                # Create ingest queue item
                ingest_item = IngestQueueItem(
                    source=IngestSource.folder,
                    ingest_type=ingest_type,
                    status=IngestStatus.pending,
                    extracted_text=extracted_text,
                    source_ref=str(file_path.absolute()),
                    retry_count=0,
                )

                db.add(ingest_item)
                await db.commit()

                logger.info(
                    "File ingested successfully",
                    extra={
                        "item_id": str(ingest_item.id),
                        "file": file_path.name,
                        "ingest_type": ingest_type,
                        "file_size": len(file_content),
                    },
                )

                # Enqueue processing task in Celery
                await self._enqueue_processing_task(ingest_item.id, ingest_type)

                # Archive file
                await self._archive_file(file_path)

            except Exception as e:
                logger.error(f"Error in _process_and_queue for {file_path}: {e}")

    async def _extract_text(self, file_content: bytes, file_path: Path) -> str | None:
        """Extract text from document using intake engine."""
        try:
            from app.engines.extract import extract_text, ExtractionError

            file_ext = file_path.suffix.lower()
            if file_ext in {".pdf", ".docx", ".doc"}:
                try:
                    extracted = extract_text(file_content, file_ext[1:])  # Remove leading dot
                    return extracted
                except ExtractionError as e:
                    logger.error(f"Extraction error for {file_path.name}: {e}")
                    return None
            elif file_ext == ".txt":
                try:
                    return file_content.decode("utf-8", errors="replace")
                except Exception as e:
                    logger.error(f"Text decode error for {file_path.name}: {e}")
                    return None

            return None
        except ImportError:
            logger.warning("extract_text not available; storing raw content")
            try:
                return file_content.decode("utf-8", errors="replace")
            except Exception:
                return None

    async def _enqueue_processing_task(
        self,
        item_id: UUID,
        ingest_type: IngestType,
    ) -> None:
        """Enqueue the item for assessment processing via Celery."""
        try:
            # Import here to avoid circular imports
            from app.workers.agents.ingest_cv import poll_cv_ingest
            from app.workers.agents.ingest_jd import poll_jd_ingest

            if ingest_type == IngestType.cv:
                # For CV processing, use the async task
                poll_cv_ingest.delay(str(item_id))
            else:
                # For JD draft, use the JD task
                poll_jd_ingest.delay(str(item_id))

            logger.info(
                "Enqueued processing task",
                extra={
                    "item_id": str(item_id),
                    "ingest_type": ingest_type.value,
                },
            )
        except Exception as e:
            logger.error(f"Error enqueueing task for {item_id}: {e}")

    async def _archive_file(self, file_path: Path) -> None:
        """Move processed file to archive folder."""
        try:
            archive_dir = Path(settings.assessment_inbox_path) / "archive"
            archive_dir.mkdir(parents=True, exist_ok=True)

            archive_path = archive_dir / file_path.name
            # Add timestamp to avoid collisions
            counter = 0
            while archive_path.exists():
                stem = file_path.stem
                suffix = file_path.suffix
                counter += 1
                archive_path = archive_dir / f"{stem}_{counter}{suffix}"

            # Use synchronous rename (watchdog runs in sync context)
            file_path.rename(archive_path)

            logger.info(f"Archived file: {archive_path}")
        except Exception as e:
            logger.warning(f"Failed to archive file {file_path.name}: {e}")


class FileSystemMonitor:
    """
    Autonomous file system monitor for CV/JD ingest folders.

    Watches configured directories for new documents.
    Automatically extracts text and queues assessments.
    """

    def __init__(self) -> None:
        self.observer = Observer()
        self.is_running = False
        self.event_handlers: dict[str, DocumentFileEventHandler] = {}
        self.watch_paths = {
            "cv": Path(settings.ingest_cv_folder),
            "jd": Path(settings.ingest_jd_folder),
        }

    def start(self) -> None:
        """Start monitoring file system."""
        if self.is_running:
            logger.warning("File system monitor already running")
            return

        # Create watch folders if they don't exist
        for folder_type, path in self.watch_paths.items():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Watching {folder_type} folder: {path}")

            # Create event handler for this folder
            event_handler = DocumentFileEventHandler(folder_type)
            self.event_handlers[folder_type] = event_handler
            self.observer.schedule(event_handler, str(path), recursive=False)

        self.observer.start()
        self.is_running = True

        logger.info("File system monitor started")

    def stop(self) -> None:
        """Stop monitoring file system."""
        if not self.is_running:
            return

        self.observer.stop()
        self.observer.join()
        self.is_running = False

        logger.info("File system monitor stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# Global monitor instance
_file_monitor: Optional[FileSystemMonitor] = None


def get_file_monitor() -> FileSystemMonitor:
    """Get or create file system monitor."""
    global _file_monitor
    if _file_monitor is None:
        _file_monitor = FileSystemMonitor()
    return _file_monitor


def start_file_monitoring():
    """Start file system monitoring on application startup."""
    monitor = get_file_monitor()
    monitor.start()
    logger.info("File system monitoring started on application startup")


def stop_file_monitoring():
    """Stop file system monitoring on application shutdown."""
    monitor = get_file_monitor()
    monitor.stop()
    logger.info("File system monitoring stopped on application shutdown")
