"""Local filesystem storage service (replaces AWS S3 for Render Disk).

Files are stored at RENDER_DISK_PATH (default: /var/data) on Render's persistent disk.
This service provides an async interface for uploading, reading, and deleting files.
"""

from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

logger = logging.getLogger("truematch.storage")


class FileStorageError(Exception):
    """Base exception for storage operations."""

    pass


class FileNotFoundError(FileStorageError):
    """Raised when a file doesn't exist."""

    pass


class FileStorage:
    """Local filesystem storage using Render Disk.

    Provides async file operations for CVs, JDs, assessments, and reports.
    Files are persisted to RENDER_DISK_PATH across service restarts.
    """

    def __init__(self, base_path: str | Path = "/var/data"):
        """Initialize storage with base path.

        Args:
            base_path: Root directory for all files (default: /var/data on Render)
        """
        self.base_path = Path(base_path)
        self.logger = logging.getLogger("truematch.storage")

    async def _ensure_directory(self, directory: Path) -> None:
        """Create directory if it doesn't exist."""
        try:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Directory ensured: {directory}")
        except OSError as e:
            raise FileStorageError(f"Failed to create directory {directory}: {e}")

    async def save_file(
        self,
        category: str,
        user_id: str,
        file: UploadFile,
        filename: Optional[str] = None,
    ) -> str:
        """Save uploaded file to disk.

        Args:
            category: File category (e.g., 'resumes', 'assessments', 'reports')
            user_id: User ID (used for path organization)
            file: FastAPI UploadFile object
            filename: Optional override filename (UUID + original used if None)

        Returns:
            Relative file path from base (e.g., 'resumes/user123/uuid-file.pdf')

        Raises:
            FileStorageError: If save fails
        """
        try:
            # Create directory structure: /var/data/{category}/{user_id}/
            file_dir = self.base_path / category / str(user_id)
            await self._ensure_directory(file_dir)

            # Generate filename with UUID prefix to ensure uniqueness
            if not filename:
                original_name = file.filename or "file"
                filename = f"{uuid.uuid4()}-{original_name}"

            file_path = file_dir / filename

            # Write file asynchronously using aiofiles
            try:
                import aiofiles
                async with aiofiles.open(file_path, "wb") as f:
                    content = await file.read()
                    await f.write(content)
            except ImportError:
                # Fallback to sync if aiofiles not available
                content = await file.read()
                file_path.write_bytes(content)

            # Return relative path for database storage
            relative_path = str(file_path.relative_to(self.base_path))
            self.logger.info(f"File saved: {relative_path} ({file.size} bytes)")

            return relative_path

        except Exception as e:
            raise FileStorageError(f"Failed to save file {file.filename}: {e}")

    async def get_file(self, relative_path: str) -> bytes:
        """Read file from disk.

        Args:
            relative_path: File path relative to base (e.g., 'resumes/user123/uuid-file.pdf')

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If file doesn't exist
            FileStorageError: If read fails
        """
        try:
            file_path = self.base_path / relative_path

            # Security: Ensure path is within base_path (prevent directory traversal)
            file_path = file_path.resolve()
            base_resolved = self.base_path.resolve()
            if not str(file_path).startswith(str(base_resolved)):
                raise FileStorageError(f"Access denied: {relative_path}")

            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {relative_path}")

            # Read file asynchronously
            try:
                import aiofiles
                async with aiofiles.open(file_path, "rb") as f:
                    content = await f.read()
                    return content
            except ImportError:
                # Fallback to sync
                return file_path.read_bytes()

        except FileNotFoundError:
            raise
        except Exception as e:
            raise FileStorageError(f"Failed to read file {relative_path}: {e}")

    async def delete_file(self, relative_path: str) -> bool:
        """Delete file from disk.

        Args:
            relative_path: File path relative to base

        Returns:
            True if deleted, False if didn't exist

        Raises:
            FileStorageError: If delete fails
        """
        try:
            file_path = self.base_path / relative_path

            # Security check
            file_path = file_path.resolve()
            base_resolved = self.base_path.resolve()
            if not str(file_path).startswith(str(base_resolved)):
                raise FileStorageError(f"Access denied: {relative_path}")

            if file_path.exists():
                file_path.unlink()
                self.logger.info(f"File deleted: {relative_path}")
                return True

            return False

        except Exception as e:
            raise FileStorageError(f"Failed to delete file {relative_path}: {e}")

    async def exists(self, relative_path: str) -> bool:
        """Check if file exists.

        Args:
            relative_path: File path relative to base

        Returns:
            True if file exists, False otherwise
        """
        try:
            file_path = self.base_path / relative_path
            file_path = file_path.resolve()
            base_resolved = self.base_path.resolve()

            if not str(file_path).startswith(str(base_resolved)):
                return False

            return file_path.exists()

        except Exception:
            return False

    async def get_directory_size(self, category: str) -> int:
        """Get total size of files in category (bytes).

        Useful for monitoring disk usage.

        Args:
            category: File category (e.g., 'resumes')

        Returns:
            Total size in bytes
        """
        try:
            category_dir = self.base_path / category
            if not category_dir.exists():
                return 0

            total = sum(
                f.stat().st_size
                for f in category_dir.rglob("*")
                if f.is_file()
            )
            return total

        except Exception as e:
            self.logger.error(f"Failed to get directory size: {e}")
            return 0

    async def check_disk_health(self) -> dict:
        """Check disk availability and usage.

        Returns:
            Dict with 'available' (bool) and 'usage' (dict) info
        """
        try:
            if not self.base_path.exists():
                # Try to create it
                await self._ensure_directory(self.base_path)

            # Check write permission
            test_file = self.base_path / ".health_check"
            test_file.write_text("ok")
            test_file.unlink()

            # Get disk usage stats
            stat = shutil.disk_usage(self.base_path)

            return {
                "available": True,
                "path": str(self.base_path),
                "total_bytes": stat.total,
                "used_bytes": stat.used,
                "free_bytes": stat.free,
                "percent_used": (stat.used / stat.total * 100) if stat.total > 0 else 0,
            }

        except Exception as e:
            self.logger.error(f"Disk health check failed: {e}")
            return {
                "available": False,
                "error": str(e),
            }


# Singleton instance (initialized in main.py)
_storage_instance: Optional[FileStorage] = None


def get_storage(base_path: str = "/var/data") -> FileStorage:
    """Get or create storage instance.

    Args:
        base_path: Root directory for file storage

    Returns:
        FileStorage instance
    """
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = FileStorage(base_path)
    return _storage_instance
