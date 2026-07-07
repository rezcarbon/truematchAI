"""Resume version model for tracking resume history and evolution."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Integer, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import utcnow
from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk
from app.models._types import EncryptedJSON, EncryptedText


class ChangeType(str, enum.Enum):
    """Type of change made to resume."""
    upload = "upload"
    edit = "edit"
    ai_enhancement = "ai_enhancement"
    import_sync = "import"


class ResumeVersion(Base, TimestampMixin):
    """
    Resume version history tracking.

    Stores all versions of a user's resume with full history, enabling:
    - Version comparison and rollback
    - Change tracking and audit trail
    - Quality scoring and improvement tracking
    - Multi-resume support per user
    """
    __tablename__ = "resume_versions"

    id: Mapped[uuid.UUID] = uuid_pk()
    resume_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Version tracking
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # File and parsing information
    file_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Language and content
    source_language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    detected_language: Mapped[str | None] = mapped_column(String(8), nullable=True)

    # PII at rest — encrypted using AES-256-GCM
    parsed_data: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    raw_narrative: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    supplementary: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    # Content diff tracking changes from previous version (encrypted)
    content_diff: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)

    # Metadata and quality scoring
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    completeness_percentage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sections_detected: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Change tracking
    change_summary: Mapped[str | None] = mapped_column(String(512), nullable=True)
    change_type: Mapped[ChangeType] = mapped_column(String(50), nullable=False, default=ChangeType.upload)
    change_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Audit trail
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_resume_versions_resume_version", "resume_id", "version_number"),
        Index("ix_resume_versions_resume_id", "resume_id"),
        Index("ix_resume_versions_user_id", "user_id"),
        Index("ix_resume_versions_is_current", "is_current"),
        Index("ix_resume_versions_change_type", "change_type"),
        Index("ix_resume_versions_created_at", "created_at"),
        Index("ix_resume_versions_archived_at", "archived_at"),
        Index("ix_resume_versions_user_current", "user_id", "is_current"),
        Index("ix_resume_versions_resume_created", "resume_id", "created_at"),
    )
