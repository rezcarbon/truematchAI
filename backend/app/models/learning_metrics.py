"""Learning metrics and performance tracking models.

Captures daily model performance, accuracy metrics, and learning progression.
"""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin


class AssessmentMetrics(Base, TimestampMixin):
    """Daily aggregated assessment performance metrics.

    Tracks precision, recall, F1, and confidence calibration daily.
    Used to detect model drift and guide automated learning cycles.

    Stores:
    - Confusion matrix (TP, TN, FP, FN)
    - Standard ML metrics (accuracy, precision, recall, F1)
    - Confidence calibration error
    - Role-specific breakdowns
    - Thresholds tested on this day
    """

    __tablename__ = "assessment_metrics"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Date and model version
    metric_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True, comment="v1, v2, v3..."
    )

    # Aggregate counts
    total_assessments: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Total assessments on this day"
    )
    assessments_with_outcome: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Assessments with recorded outcomes"
    )

    # Confusion matrix
    true_positives: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Predicted hire, actually hired"
    )
    true_negatives: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Predicted reject, actually rejected"
    )
    false_positives: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Predicted hire, actually rejected"
    )
    false_negatives: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Predicted reject, actually hired"
    )

    # Standard metrics (0.0-1.0)
    accuracy: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="(TP+TN) / total"
    )
    precision: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="TP / (TP+FP)"
    )
    recall: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="TP / (TP+FN)"
    )
    f1_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="2*precision*recall / (precision+recall)"
    )
    false_positive_rate: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="FP / (FP+TN)"
    )
    false_negative_rate: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="FN / (FN+TP)"
    )

    # Confidence calibration
    avg_confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Average prediction confidence on this day"
    )
    expected_calibration_error: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="|avg_confidence - accuracy|"
    )

    # Role-specific breakdown
    metrics_by_role: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="{role_title: {accuracy, precision, recall, f1, sample_size}}",
    )

    # Thresholds tested this day
    thresholds_tested: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="{threshold_value: results_at_threshold}",
    )

    __table_args__ = (
        Index("ix_assessment_metrics_date", "metric_date"),
        Index("ix_assessment_metrics_model_version", "model_version"),
        Index("ix_assessment_metrics_accuracy", "accuracy"),
    )


class CognitiveState(Base, TimestampMixin):
    """Learned weights, thresholds, and decision patterns.

    Represents the current "intelligence" of the assessment system:
    - Learned capability weights per role
    - Calibrated hire/reject thresholds
    - Discovered biases and corrections
    - Heuristics from past decisions
    """

    __tablename__ = "cognitive_state"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # System-level cognitive state (agent_type="system")
    agent_type: Mapped[str] = mapped_column(
        String(64), nullable=False, default="system", index=True
    )

    # Decision weights per capability component
    decision_weights: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="{component_name: weight_0_to_1}",
    )

    # Calibrated gates/thresholds
    gate_thresholds: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={"capability_hire": 60},
        comment="{gate_name: score_threshold}",
    )

    # Per-source confidence calibration
    verification_confidence: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="{source_name: calibrated_confidence_0_to_1}",
    )

    # Discovered biases and their corrections
    known_biases: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="{bias_type: {discovered, correction_factor}}",
    )
    bias_corrections: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="{attribute: adjustment_factor}",
    )

    # Learned heuristics and decision rules
    heuristics: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="{heuristic_name: {condition, action}}",
    )
    decision_rules: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="{rule_name: {if_condition, then_action}}",
    )

    # Performance insights
    performance_insights: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="{insight_type: {works_well, doesnt_work}}",
    )

    # Known edge cases and how to handle them
    edge_cases: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="{edge_case: {description, handling}}",
    )

    # Overall confidence in current state
    reasoning_confidence: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.5, comment="0.0-1.0 confidence in current state"
    )

    __table_args__ = (
        Index("ix_cognitive_state_agent_type", "agent_type"),
        Index("ix_cognitive_state_reasoning_confidence", "reasoning_confidence"),
    )


class CognitiveEvolutionLog(Base, TimestampMixin):
    """Audit trail of cognitive state changes.

    Records when and why the system's learned state changed,
    enabling rollback and impact analysis.
    """

    __tablename__ = "cognitive_evolution_log"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # What changed
    agent_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, comment="system, role-specific, etc."
    )
    event_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, comment="threshold_adjusted, bias_corrected, pattern_learned"
    )

    # State snapshots (before and after)
    before_state: Mapped[dict] = mapped_column(
        JSON, nullable=False, default={}, comment="Relevant fields before change"
    )
    after_state: Mapped[dict] = mapped_column(
        JSON, nullable=False, default={}, comment="Relevant fields after change"
    )

    # Rationale and impact
    change_reason: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="Why this change was made"
    )
    expected_improvement: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Expected % improvement in accuracy"
    )
    actual_improvement: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Actual % improvement measured later"
    )

    # What triggered this
    triggered_by_assessment_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, comment="Assessment that triggered this change"
    )
    triggered_by_date: Mapped[date | None] = mapped_column(
        Date, nullable=True, comment="Learning cycle date that triggered this"
    )

    __table_args__ = (
        Index("ix_cognitive_evolution_log_agent_type", "agent_type"),
        Index("ix_cognitive_evolution_log_event_type", "event_type"),
        Index("ix_cognitive_evolution_log_created_at", "created_at"),
    )


__all__ = [
    "AssessmentMetrics",
    "CognitiveState",
    "CognitiveEvolutionLog",
]
