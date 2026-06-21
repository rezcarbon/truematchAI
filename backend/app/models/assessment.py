"""Assessment model — the core artifact of an evaluation run."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk
from app.models._types import EncryptedJSON, EncryptedText


class AssessmentStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    # A governed run whose output failed one or more governance gates. The
    # assessment is withheld from automated surfacing and routed to human review
    # rather than presented as a confident result.
    flagged_for_review = "flagged_for_review"


class DecisionType(str, enum.Enum):
    """EU AI Act compliance decision types (Article 14).

    approval: Autonomous approval (confidence >= 0.90 + governance passed)
    advisory: Recommendation requiring human review (confidence 0.40-0.90)
    escalate: Escalation to human (confidence < 0.40 OR governance failed)
    """
    approval = "approval"
    advisory = "advisory"
    escalate = "escalate"


class Assessment(Base, TimestampMixin):
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = uuid_pk()
    resume_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
    )
    position_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("positions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[AssessmentStatus] = mapped_column(
        SAEnum(AssessmentStatus, name="assessment_status"),
        default=AssessmentStatus.pending,
        nullable=False,
    )

    # Traditional ATS simulation. traditional_detail is candidate-derived
    # (matched/missing keywords against this resume) → encrypted at rest.
    traditional_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    traditional_detail: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)

    # Semantic / concept-level match (Pillar 1) — the independent middle signal
    # between keyword baseline and capability reasoning. Deterministic + versioned.
    semantic_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    semantic_detail: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)

    # Capability assessment. Components/evidence quote the resume → encrypted.
    capability_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capability_components: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    capability_narrative: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    capability_evidence: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)

    # Trajectory (candidate career data) → encrypted.
    trajectory_data: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    trajectory_narrative: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)

    # Counter-recommendation
    counter_rec_triggered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    counter_rec_reasoning: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    # Evidence quotes the resume → encrypted at rest.
    counter_rec_evidence: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)

    # JD interrogation
    jd_quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    jd_issues: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # External-evidence enrichment (Pillar 5) + credential substitution (Pillar 6).
    # Both can reference candidate-identifying material → encrypted at rest.
    verified_evidence: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    substitutions: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)

    # Governance results (structured outputs; thresholds applied server-side
    # only). Observations may reference candidate attributes → encrypted at rest.
    # IS NULL / IS NOT NULL checks (used by compliance counts) still work on the
    # underlying TEXT column.
    governance_coherence: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    governance_consistency: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    governance_fidelity: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    governance_bias_flags: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    governance_audit_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )

    # Difference between capability and traditional scoring
    score_delta: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # SHA-256 over (resume text + JD text + prompt-registry version). Identical
    # inputs can reuse a prior completed result instead of re-running the LLM
    # pipeline — effective determinism + zero cost for repeats.
    input_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Dead Letter Queue (DLQ) error tracking — populated when assessment fails
    # after max retries and is sent to DLQ handler.
    dlq_error: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    dlq_context: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)

    # EU AI Act compliance fields (Article 14)
    decision_type: Mapped[DecisionType | None] = mapped_column(
        SAEnum(DecisionType, name="decision_type"),
        nullable=True,
    )
    human_review_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    article_14_compliant: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_assessments_user_id", "user_id"),
        Index("ix_assessments_position_id", "position_id"),
        Index("ix_assessments_resume_id", "resume_id"),
        Index("ix_assessments_status", "status"),
        Index("ix_assessments_decision_type", "decision_type"),
        Index("ix_assessments_input_hash", "input_hash"),
    )
