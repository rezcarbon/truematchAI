"""
AI-Native File Ingestion System - Phase A: Autonomy Layer

Monitors file system and email for new CV/JD submissions.
Automatically queues assessments for processing.
"""
import asyncio
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from app.config import settings
from app.models.assessment import Assessment
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class AssessmentFileEventHandler(FileSystemEventHandler):
    """
    Watches for new files in assessment inbox directory.

    Supported formats:
    - CV: PDF, DOCX, TXT, MD
    - JD: PDF, DOCX, TXT, CSV, JSON
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf", ".docx", ".txt", ".md",  # CV formats
        ".csv", ".json"  # JD formats
    }

    def __init__(self):
        self.processed_hashes = set()
        self.lock = asyncio.Lock()

    async def _get_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file content."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def _is_file_ready(self, file_path: str, wait_time: float = 2.0) -> bool:
        """
        Check if file is ready for processing.
        Waits to ensure file write is complete.
        """
        try:
            # Get initial size
            initial_size = Path(file_path).stat().st_size
            await asyncio.sleep(wait_time)

            # Check if size changed
            current_size = Path(file_path).stat().st_size
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

        # Check if already processed
        try:
            file_hash = asyncio.run(self._get_file_hash(str(file_path)))
            if file_hash in self.processed_hashes:
                logger.info(f"Skipping duplicate file: {file_path.name} (hash: {file_hash})")
                return

            # Wait for file write to complete
            is_ready = asyncio.run(self._is_file_ready(str(file_path)))
            if not is_ready:
                logger.warning(f"File not ready after wait: {file_path.name}")
                return

            # Queue for processing
            asyncio.run(self._queue_for_processing(str(file_path), file_hash))
            self.processed_hashes.add(file_hash)

        except Exception as e:
            logger.error(f"Error processing file {file_path.name}: {e}")

    async def _queue_for_processing(self, file_path: str, file_hash: str):
        """Queue file for assessment processing."""
        logger.info(f"Queuing file for assessment: {file_path} (hash: {file_hash})")

        # This would integrate with Phase A job queue
        # For now, just log it
        # TODO: Integration point with asyncio job queue


class FileSystemMonitor:
    """
    Autonomous file system monitor for assessment inbox.

    Watches configured directory for new CVs and JDs.
    Automatically processes and queues assessments.
    """

    def __init__(self, inbox_path: Optional[str] = None):
        self.inbox_path = Path(inbox_path or settings.assessment_inbox_path)
        self.observer = Observer()
        self.event_handler = AssessmentFileEventHandler()
        self.is_running = False

        # Create inbox if doesn't exist
        self.inbox_path.mkdir(parents=True, exist_ok=True)

    def start(self):
        """Start monitoring file system."""
        if self.is_running:
            logger.warning("File system monitor already running")
            return

        self.observer.schedule(self.event_handler, str(self.inbox_path), recursive=True)
        self.observer.start()
        self.is_running = True

        logger.info(f"File system monitor started: watching {self.inbox_path}")

    def stop(self):
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
