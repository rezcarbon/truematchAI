"""Ingest queue — every autonomous ingestion event is tracked here.

Each row represents one inbound document (CV, cover letter, JD draft) regardless
of its source (email, drop-folder, API webhook). The agent updates the row as
it progresses through extraction → matching → pipeline dispatch → completion.
This is the audit record for all autonomous activity.
"""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import uuid_pk
from app.models._types import EncryptedJSON, EncryptedText


class IngestSource(str, enum.Enum):
    email = "email"
    folder = "folder"
    api = "api"
    webhook = "webhook"


class IngestType(str, enum.Enum):
    cv = "cv"
    jd_draft = "jd_draft"


class IngestStatus(str, enum.Enum):
    pending = "pending"           # picked up, not yet processed
    extracting = "extracting"     # extracting text from the raw document
    matching = "matching"         # matching CV to open positions
    processing = "processing"     # assessment pipeline enqueued
    completed = "completed"       # pipeline done; assessment/position created
    failed = "failed"             # unrecoverable error
    rejected = "rejected"         # human rejected via control API
    awaiting_review = "awaiting_review"  # needs human approval before proceeding


class IngestQueueItem(Base):
    __tablename__ = "ingest_queue"

    id: Mapped[uuid.UUID] = uuid_pk()

    source: Mapped[IngestSource] = mapped_column(
        String(20), nullable=False
    )
    ingest_type: Mapped[IngestType] = mapped_column(
        String(20), nullable=False
    )
    status: Mapped[IngestStatus] = mapped_column(
        String(30), nullable=False, default=IngestStatus.pending
    )

    # The raw origin reference (email message-id, file path, webhook event id).
    # Not PII itself but encrypted as defensive practice.
    source_ref: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)

    # Extracted document text (resume body, JD body) — PII → encrypted.
    extracted_text: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)

    # Cover letter text (if present alongside a CV) — PII → encrypted.
    cover_letter_text: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)

    # Sender / submitter metadata (name, email address) — PII → encrypted.
    sender_meta: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)

    # Links to the artifacts created by processing.
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
    )
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("assessments.id", ondelete="SET NULL"),
        nullable=True,
    )
    position_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("positions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # JD agent output: AI-improved draft and quality recommendations.
    jd_improved_draft: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    jd_agent_output: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)

    # Retry / error tracking.
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Human control.
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_ingest_queue_status", "status"),
        Index("ix_ingest_queue_source", "source"),
        Index("ix_ingest_queue_type", "ingest_type"),
        Index("ix_ingest_queue_created", "created_at"),
    )
