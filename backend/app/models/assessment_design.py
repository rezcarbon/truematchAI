"""Assessment Design models — Agent-designed assessments awaiting recruiter approval."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk
from app.models._types import EncryptedJSON, EncryptedText


class AssessmentDesignReviewStatus(str, enum.Enum):
    """Recruiter review status for assessment design."""
    pending_review = "pending_review"  # Awaiting recruiter review
    approved = "approved"  # Recruiter approved, assessment created
    changes_requested = "changes_requested"  # Recruiter requested changes
    rejected = "rejected"  # Recruiter rejected, manual redesign needed


class AssessmentDesign(Base, TimestampMixin):
    """Assessment design created by agent, awaiting recruiter approval."""
    __tablename__ = "assessment_designs"

    id: Mapped[uuid.UUID] = uuid_pk()

    # Core references
    position_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("positions.id", ondelete="CASCADE"),
        nullable=False,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    screening_result_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("screening_results.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Agent design (encrypted for sensitivity)
    agent_designed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    agent_design: Mapped[dict] = mapped_column(EncryptedJSON, nullable=False)
    # Contains:
    # {
    #   "questions": [
    #     {
    #       "question": "What would you do in this scenario?",
    #       "type": "coding" | "design" | "behavioral" | "scenario",
    #       "expected_duration_minutes": 20,
    #       "rubric": {...},
    #       "accessibility_notes": "Allow IDE of choice"
    #     }
    #   ],
    #   "scenarios": [...],
    #   "interview_guidance": {
    #     "estimated_duration_minutes": 90,
    #     "time_breakdown": {...},
    #     "probe_areas": ["error handling", "design thinking"],
    #     "red_flags": ["no error checking"],
    #     "growth_signals": ["asks clarifying questions"],
    #     "accessibility_considerations": [...]
    #   },
    #   "evaluation_rubric": {
    #     "competencies": [...],
    #     "scoring": {...}
    #   },
    #   "rationale": "Why this assessment was designed this way"
    # }

    # Fairness validation (encrypted for sensitivity)
    design_fairness_check: Mapped[dict] = mapped_column(EncryptedJSON, nullable=False, default={})
    # Contains:
    # {
    #   "passed": bool,
    #   "bias_indicators": [...],
    #   "fairness_score": 0-100,
    #   "recommendations": [...],
    #   "gates_evaluated": [
    #     {"gate": "bias_detection", "passed": bool, "issues": []}
    #   ]
    # }

    # Recruiter review
    review_status: Mapped[AssessmentDesignReviewStatus] = mapped_column(
        SAEnum(AssessmentDesignReviewStatus, name="assessment_design_review_status"),
        default=AssessmentDesignReviewStatus.pending_review,
        nullable=False,
    )

    recruiter_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    recruiter_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    recruiter_feedback: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    # When changes_requested: Specific feedback from recruiter
    # When approved: Optional notes
    # When rejected: Reason for rejection

    recruiter_confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 0-100: How confident recruiter is in assessment design
    # Used for learning: Design iterations approved by confident recruiter

    # Associated assessment (created after approval)
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("assessments.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Phase 3+: Relationships
    analysis_results = relationship("AnalysisResult", back_populates="assessment_design")

    __table_args__ = (
        Index("ix_assessment_designs_position_id", position_id),
        Index("ix_assessment_designs_candidate_id", candidate_id),
        Index("ix_assessment_designs_review_status", review_status),
        Index("ix_assessment_designs_recruiter_id", recruiter_id),
        Index("ix_assessment_designs_created_at", "created_at"),
        Index("ix_assessment_designs_position_status", position_id, review_status),
    )


__all__ = [
    "AssessmentDesign",
    "AssessmentDesignReviewStatus",
]
