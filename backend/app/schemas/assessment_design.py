"""Pydantic schemas for assessment design API."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# ASSESSMENT DESIGN REQUEST/RESPONSE
# ============================================================================


class AssessmentQuestion(BaseModel):
    """Single assessment question."""
    question: str = Field(..., description="The question text")
    question_type: str = Field(..., description="coding | design | behavioral | scenario")
    expected_duration_minutes: int = Field(..., ge=5, le=120)
    rubric: dict = Field(..., description="Scoring rubric for this question")
    accessibility_notes: Optional[str] = Field(None)


class InterviewGuidance(BaseModel):
    """Recruiter guidance for conducting assessment."""
    estimated_duration_minutes: int
    time_breakdown: dict  # {"coding": 30, "behavioral": 20, ...}
    probe_areas: list[str]  # What to dig deeper on
    red_flags: list[str]  # What to watch for
    growth_signals: list[str]  # What indicates growth
    accessibility_considerations: list[str]


class EvaluationRubric(BaseModel):
    """How to score the assessment."""
    competencies: list[str]
    scoring_levels: dict  # {"novice": 1, "intermediate": 2, "expert": 3}
    passing_threshold: int  # Minimum score to pass (0-100)


class FairnessCheckResult(BaseModel):
    """Fairness validation result."""
    passed: bool
    bias_indicators: list[str]
    fairness_score: int = Field(..., ge=0, le=100)
    recommendations: list[str]
    gates_evaluated: list[dict]


class AssessmentDesignCreateRequest(BaseModel):
    """Request to create assessment design."""
    screening_result_id: UUID = Field(..., description="From Phase 1 screening")
    position_id: UUID = Field(..., description="Position to assess for")


class AssessmentDesignResponse(BaseModel):
    """Assessment design for recruiter review."""
    id: UUID
    position_id: UUID
    candidate_id: UUID
    screening_result_id: Optional[UUID]

    # Agent design
    agent_designed_at: datetime
    questions: list[AssessmentQuestion]
    scenarios: list[dict]  # Real-world scenarios
    interview_guidance: InterviewGuidance
    evaluation_rubric: EvaluationRubric
    design_rationale: str  # Why designed this way

    # Fairness
    fairness_check: FairnessCheckResult

    # Recruiter review
    review_status: str  # pending_review | approved | changes_requested | rejected
    recruiter_feedback: Optional[str]
    recruiter_confidence: Optional[int]

    # Timestamps
    created_at: datetime
    updated_at: datetime


class AssessmentDesignPendingResponse(BaseModel):
    """Paginated pending designs for recruiter review."""
    designs: list[dict]  # Quick summary cards
    pagination: dict  # {total, page, limit, pages}


class AssessmentDesignApproveRequest(BaseModel):
    """Recruiter approval of assessment design."""
    recruiter_notes: Optional[str] = Field(None, description="Optional notes on approval")
    recruiter_confidence: Optional[int] = Field(None, ge=0, le=100, description="Confidence in design")


class AssessmentDesignRequestChangesRequest(BaseModel):
    """Request changes to assessment design."""
    feedback: str = Field(..., description="Specific feedback for revision")
    specific_issues: list[str] = Field(..., description="Issues to address")


class FairnessReportResponse(BaseModel):
    """Fairness analysis report."""
    fairness_score: int = Field(..., ge=0, le=100)
    bias_indicators: list[str]
    recommendations: list[str]
    gates_evaluated: list[dict]
    assessment_suitability: str  # "good" | "fair" | "needs_review"


__all__ = [
    "AssessmentQuestion",
    "InterviewGuidance",
    "EvaluationRubric",
    "FairnessCheckResult",
    "AssessmentDesignCreateRequest",
    "AssessmentDesignResponse",
    "AssessmentDesignPendingResponse",
    "AssessmentDesignApproveRequest",
    "AssessmentDesignRequestChangesRequest",
    "FairnessReportResponse",
]
