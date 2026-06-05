"""Training Simulation System - Models for virtual brain/digital assistant."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum
from sqlalchemy import ForeignKey, Index, String, Text, Float, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk


class FeedbackType(str, Enum):
    """Types of feedback on matches."""
    hire = "hire"
    reject = "reject"
    maybe = "maybe"
    interested = "interested"
    not_interested = "not_interested"
    applied = "applied"


class TrainingFeedback(Base, TimestampMixin):
    """
    Captures recruiter/candidate feedback on matches.

    This is the core training data that helps the virtual brain learn.
    Every time a recruiter hires/rejects a candidate or a candidate
    applies/skips a job, this creates a training signal.
    """
    __tablename__ = "training_feedback"

    id: Mapped[uuid.UUID] = uuid_pk()

    # Core relationships
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    match_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True
    )

    # Job/Candidate context
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("positions.id", ondelete="CASCADE"),
        nullable=True
    )
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True
    )

    # Feedback data
    feedback_type: Mapped[FeedbackType] = mapped_column(
        SAEnum(FeedbackType, name="feedback_type"),
        nullable=False
    )
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5 stars
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Action metrics
    time_to_action_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Outcome tracking
    outcome: Mapped[str | None] = mapped_column(String(50), nullable=True)  # hired, rejected, pending
    outcome_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hire_success: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # Still employed after 6mo?

    # Metadata
    source: Mapped[str] = mapped_column(String(50), default="web")  # web, mobile, api
    is_training: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        Index("ix_training_feedback_user_id", "user_id"),
        Index("ix_training_feedback_job_id", "job_id"),
        Index("ix_training_feedback_candidate_id", "candidate_id"),
        Index("ix_training_feedback_type", "feedback_type"),
        Index("ix_training_feedback_outcome", "outcome"),
    )


class CapabilityMapping(Base, TimestampMixin):
    """
    Maps CV keywords/phrases to specific capabilities.

    The virtual brain learns: "When candidate says X, they likely have Y capability"
    This mapping improves over time as recruiters provide feedback.
    """
    __tablename__ = "capability_mapping"

    id: Mapped[uuid.UUID] = uuid_pk()

    # The mapping
    cv_keyword: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    capability: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Confidence in this mapping (0-1)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)

    # Learning metrics
    frequency: Mapped[int] = mapped_column(Integer, default=1)  # How often seen
    positive_feedback: Mapped[int] = mapped_column(Integer, default=0)  # Confirmed correct
    negative_feedback: Mapped[int] = mapped_column(Integer, default=0)  # Confirmed incorrect

    # Context
    job_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Training metadata
    is_user_added: Mapped[bool] = mapped_column(Boolean, default=False)
    learned_from_feedback: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        Index("ix_capability_mapping_keyword", "cv_keyword"),
        Index("ix_capability_mapping_capability", "capability"),
        Index("ix_capability_mapping_confidence", "confidence_score"),
    )


class CredentialMapping(Base, TimestampMixin):
    """
    Maps credentials to job requirements.

    The virtual brain learns: "This degree matches that requirement"
    Handles equivalencies like "BS CS" = "Bachelor's in Computer Science"
    """
    __tablename__ = "credential_mapping"

    id: Mapped[uuid.UUID] = uuid_pk()

    # The mapping
    credential: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    requirement: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Match quality
    match_score: Mapped[float] = mapped_column(Float, default=0.5)  # 0-1
    is_exact_match: Mapped[bool] = mapped_column(Boolean, default=False)
    is_acceptable_alternative: Mapped[bool] = mapped_column(Boolean, default=False)

    # Alternative matches
    alternative_matches: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Learning metrics
    positive_feedback: Mapped[int] = mapped_column(Integer, default=0)
    negative_feedback: Mapped[int] = mapped_column(Integer, default=0)

    # Context
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)

    __table_args__ = (
        Index("ix_credential_mapping_credential", "credential"),
        Index("ix_credential_mapping_requirement", "requirement"),
        Index("ix_credential_mapping_score", "match_score"),
    )


class SuccessPattern(Base, TimestampMixin):
    """
    Learned patterns for successful hires.

    The virtual brain learns: "For this type of job, these are the success factors"
    Used to predict hiring success and recommend candidates.
    """
    __tablename__ = "success_pattern"

    id: Mapped[uuid.UUID] = uuid_pk()

    # Pattern context
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("positions.id", ondelete="CASCADE"),
        nullable=True
    )
    job_category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Learned characteristics of successful hires
    successful_candidate_profile: Mapped[dict] = mapped_column(JSONB, default={})

    # Key factors
    key_capabilities: Mapped[list] = mapped_column(JSONB, default=[])
    key_credentials: Mapped[list] = mapped_column(JSONB, default=[])

    # Success metrics
    success_rate: Mapped[float] = mapped_column(Float, default=0.0)  # % still employed 6mo+
    average_tenure_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    average_performance_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)  # # of hires analyzed

    # Context
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    salary_range: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Pattern metadata
    confidence_level: Mapped[float] = mapped_column(Float, default=0.5)  # 0-1
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        Index("ix_success_pattern_job_id", "job_id"),
        Index("ix_success_pattern_category", "job_category"),
        Index("ix_success_pattern_rate", "success_rate"),
    )


class TrainingProgress(Base, TimestampMixin):
    """
    Tracks the improvement of the virtual brain over time.

    Shows how the AI is learning and becoming more accurate.
    """
    __tablename__ = "training_progress"

    id: Mapped[uuid.UUID] = uuid_pk()

    # What metric are we tracking?
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Metric value and improvement
    current_value: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_value: Mapped[float] = mapped_column(Float, nullable=False)
    improvement_percent: Mapped[float] = mapped_column(Float, default=0.0)

    # Data used for this metric
    sample_count: Mapped[int] = mapped_column(Integer, default=0)

    # Period
    period: Mapped[str] = mapped_column(String(50), default="daily")  # daily, weekly, monthly

    # Additional context
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_training_progress_metric", "metric_name"),
        Index("ix_training_progress_period", "period"),
        Index("ix_training_progress_value", "current_value"),
    )


class TrainingInsight(Base, TimestampMixin):
    """
    Generated insights from what the virtual brain has learned.

    Examples:
    - "Python is the most requested skill"
    - "Full-stack engineers have highest success rate"
    - "80% of hires happy after 6 months"
    """
    __tablename__ = "training_insight"

    id: Mapped[uuid.UUID] = uuid_pk()

    # What is this insight about?
    insight_type: Mapped[str] = mapped_column(String(100), nullable=False)  # skill_demand, success_factor, trend, etc
    insight_category: Mapped[str | None] = mapped_column(String(100), nullable=True)  # software, engineering, marketing, etc

    # The insight
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Data backing this insight
    metric_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    # Supporting data
    supporting_data: Mapped[dict] = mapped_column(JSONB, default={})

    # Context
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Visibility
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    is_trending: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index("ix_training_insight_type", "insight_type"),
        Index("ix_training_insight_category", "insight_category"),
        Index("ix_training_insight_public", "is_public"),
    )


class VirtualBrainState(Base, TimestampMixin):
    """
    Stores the state of the virtual brain model.

    Allows versioning and rollback of the learned model.
    """
    __tablename__ = "virtual_brain_state"

    id: Mapped[uuid.UUID] = uuid_pk()

    # Model version
    version: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    # Model stats
    total_feedback_samples: Mapped[int] = mapped_column(Integer, default=0)
    total_patterns_learned: Mapped[int] = mapped_column(Integer, default=0)
    match_accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    hire_success_prediction_accuracy: Mapped[float] = mapped_column(Float, default=0.0)

    # Model data
    model_data: Mapped[dict] = mapped_column(JSONB, default={})

    # Model performance
    performance_metrics: Mapped[dict] = mapped_column(JSONB, default={})

    # Training info
    training_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    training_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_virtual_brain_state_version", "version"),
        Index("ix_virtual_brain_state_active", "is_active"),
    )
