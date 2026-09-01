"""
Training Data Models - For autonomous AI-native training system.

Tracks uploads, chat interactions, and auto-learning results.
"""
from datetime import datetime
from app.core.clock import utcnow
from typing import Optional
from uuid import UUID

from sqlalchemy import JSON, String, Text, DateTime, Integer, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, uuid_pk


class TrainingDataUpload(Base):
    """Track training data uploads (CSV/JSON batches)."""

    __tablename__ = "training_data_uploads"

    id: Mapped[UUID] = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[str] = mapped_column(String(10), nullable=False)  # csv, json
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, processing, completed, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Processing stats
    items_processed: Mapped[int] = mapped_column(Integer, default=0)
    items_failed: Mapped[int] = mapped_column(Integer, default=0)
    insights_extracted: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    processing_stats: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    items: Mapped[list["TrainingDataItem"]] = relationship(
        "TrainingDataItem", back_populates="upload", cascade="all, delete-orphan"
    )


class TrainingDataItem(Base):
    """Individual training record from upload (candidate feedback)."""

    __tablename__ = "training_data_items"

    id: Mapped[UUID] = uuid_pk()
    upload_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("training_data_uploads.id"), nullable=False)

    # Candidate profile
    candidate_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    candidate_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    candidate_profile: Mapped[dict] = mapped_column(JSON, default=dict)  # Full candidate data
    experience_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Years of experience
    skills: Mapped[list] = mapped_column(JSON, default=list)  # Array of skill strings
    education: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Education level/field

    # Decision and feedback
    decision: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # hire, reject, applied, interested, not_interested
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 stars

    # Auto-extracted training signals
    extracted_capabilities: Mapped[list] = mapped_column(JSON, default=list)  # Auto-extracted
    extracted_credentials: Mapped[list] = mapped_column(JSON, default=list)  # Auto-extracted
    capability_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # Metadata
    source_row: Mapped[int] = mapped_column(Integer, nullable=False)  # Row number in upload
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    applied_to_training: Mapped[bool] = mapped_column(Boolean, default=False)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    upload: Mapped["TrainingDataUpload"] = relationship("TrainingDataUpload", back_populates="items")


class TrainingChatMessage(Base):
    """Training conversation history for chat-based learning."""

    __tablename__ = "training_chat_messages"

    id: Mapped[UUID] = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)  # Group conversations

    # Message content
    user_message: Mapped[str] = mapped_column(Text, nullable=False)
    ai_response: Mapped[str] = mapped_column(Text, nullable=False)

    # Auto-extracted training signal
    extracted_training_signal: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    feedback_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # capability_suggestion, mapping_correction, credential_equivalency, pattern_discovery, etc

    # Impact tracking
    applied_to_training: Mapped[bool] = mapped_column(Boolean, default=False)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class TrainingInsightBatch(Base):
    """Results from auto-learning (aggregated improvements)."""

    __tablename__ = "training_insight_batches"

    id: Mapped[UUID] = uuid_pk()

    # Source tracking
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # upload, chat, auto
    source_id: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), nullable=True)  # upload_id or session_id

    # Learning results
    insights: Mapped[list] = mapped_column(JSON, default=list)  # Discovered patterns
    new_capabilities: Mapped[list] = mapped_column(JSON, default=list)  # New capability discoveries
    updated_mappings: Mapped[list] = mapped_column(JSON, default=list)  # Updated keyword→capability
    updated_credentials: Mapped[list] = mapped_column(JSON, default=list)  # New credential equivalencies
    new_success_patterns: Mapped[list] = mapped_column(JSON, default=list)  # New patterns

    # Impact metrics
    improvement_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    # { match_accuracy_delta, hire_success_delta, capability_coverage_delta, etc }

    # Virtual brain state
    virtual_brain_state_version: Mapped[int] = mapped_column(Integer, nullable=False)
    match_accuracy_before: Mapped[float] = mapped_column(Float, nullable=False)
    match_accuracy_after: Mapped[float] = mapped_column(Float, nullable=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class TrainingLearningSession(Base):
    """Track active training sessions (chat conversations)."""

    __tablename__ = "training_learning_sessions"

    id: Mapped[UUID] = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Session metadata
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    # Learning progress
    insights_extracted: Mapped[int] = mapped_column(Integer, default=0)
    mappings_updated: Mapped[int] = mapped_column(Integer, default=0)
    patterns_discovered: Mapped[int] = mapped_column(Integer, default=0)

    # Session status
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, archived
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
