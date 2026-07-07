"""Application model for ATS pipeline tracking."""
from __future__ import annotations

import uuid
from datetime import datetime
from app.core.clock import utcnow
from enum import Enum

from sqlalchemy import DateTime, String, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models._types import EncryptedText


class PipelineStage(str, Enum):
    """Pipeline stage enumeration."""
    applied = "applied"
    phone_screen = "phone_screen"
    technical = "technical"
    onsite = "onsite"
    offer = "offer"
    hired = "hired"
    rejected = "rejected"


class Application(Base):
    """Application record tracking candidate progress through hiring pipeline."""
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    position_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("positions.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Pipeline tracking
    stage: Mapped[PipelineStage] = mapped_column(String(50), nullable=False, default=PipelineStage.applied)
    stage_entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    # Application metadata
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)  # linkedin, referral, indeed, etc
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # custom tags
    # External ATS provenance, e.g. "greenhouse:application:9876" — idempotent import.
    external_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Candidate cover note or message submitted with application (encrypted at rest)
    cover_note: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)

    # Timestamps
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    # Relationships (lazy import to avoid circular dependency)
    interviews: Mapped[list] = relationship("Interview", back_populates="application", cascade="all, delete-orphan", foreign_keys="Interview.application_id")

    __table_args__ = (
        Index("ix_applications_user_id", "user_id"),
        Index("ix_applications_position_id", "position_id"),
        Index("ix_applications_resume_id", "resume_id"),
        Index("ix_applications_stage", "stage"),
        Index("ix_applications_source", "source"),
        Index("ix_applications_external_ref", "external_ref"),
        Index("ix_applications_applied_at", "applied_at"),
    )
