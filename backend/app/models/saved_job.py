"""Saved jobs model for candidate job curation and tracking."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Integer, Float, Boolean, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, TEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import utcnow
from app.database import Base
from app.models._types import EncryptedJSON, EncryptedText


class SavedJobStatus(str, enum.Enum):
    """Status of a saved job."""
    saved = "saved"
    viewed = "viewed"
    applied = "applied"
    archived = "archived"
    rejected = "rejected"


class SavedJob(Base):
    """
    Saved jobs for candidate job curation.

    Allows candidates to:
    - Save jobs they're interested in
    - Organize saves into custom lists
    - Track application history
    - Receive updates on saved jobs
    - Store personalized notes and relevance scores
    """
    __tablename__ = "saved_jobs"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    position_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("positions.id", ondelete="CASCADE"),
        nullable=False,
    )
    list_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("saved_jobs_lists.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Save metadata
    list_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Default")
    notes: Mapped[str | None] = mapped_column(TEXT, nullable=True)

    # Job snapshot (denormalized for fast access without joins)
    job_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    job_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Relevance and matching scores (encrypted - PII)
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    relevance_metadata: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)

    # Status tracking
    status: Mapped[SavedJobStatus] = mapped_column(String(50), nullable=False, default=SavedJobStatus.saved)
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Notification preferences
    notify_on_update: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "position_id", name="uq_saved_jobs_user_position"),
        Index("ix_saved_jobs_user_id", "user_id"),
        Index("ix_saved_jobs_position_id", "position_id"),
        Index("ix_saved_jobs_status", "status"),
        Index("ix_saved_jobs_list_name", "list_name"),
        Index("ix_saved_jobs_list_id", "list_id"),
        Index("ix_saved_jobs_created_at", "created_at"),
        Index("ix_saved_jobs_archived_at", "archived_at"),
        Index("ix_saved_jobs_user_status", "user_id", "status"),
        Index("ix_saved_jobs_user_created", "user_id", "created_at"),
        Index("ix_saved_jobs_user_list_status", "user_id", "list_name", "status"),
    )


class SavedJobsList(Base):
    """
    Custom lists for organizing saved jobs.

    Allows candidates to organize jobs into custom folders/lists:
    - Default list for general saves
    - Custom lists like "Dream Jobs", "Startups", "Remote Only", etc.
    - Shared lists for collaboration
    """
    __tablename__ = "saved_jobs_lists"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # List metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)

    # List configuration
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_shared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    job_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_saved_jobs_list_user_name"),
        Index("ix_saved_jobs_lists_user_id", "user_id"),
        Index("ix_saved_jobs_lists_is_default", "is_default"),
        Index("ix_saved_jobs_lists_created_at", "created_at"),
    )
