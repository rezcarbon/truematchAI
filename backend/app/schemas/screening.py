"""Pydantic schemas for screening API."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.screening import RecruiterDecision, ScreeningRecommendation


# ============================================================================
# BATCH MANAGEMENT
# ============================================================================


class ScreeningBatchConfig(BaseModel):
    """Configuration for screening batch."""
    min_experience_years: Optional[int] = Field(None, description="Minimum years of experience")
    required_skills: Optional[list[str]] = Field(
        None, description="Required skills (all must be present)"
    )
    preferred_skills: Optional[list[str]] = Field(
        None, description="Preferred skills (nice to have)"
    )
    red_flag_keywords: Optional[list[str]] = Field(
        None, description="Keywords that raise concerns"
    )
    custom_criteria: Optional[dict] = Field(None, description="Custom filtering criteria")


class ScreeningBatchCreateRequest(BaseModel):
    """Request to initiate screening batch."""
    position_id: UUID = Field(..., description="Position to screen candidates for")
    resume_ids: list[UUID] = Field(..., description="Resume IDs to screen (1000+)")
    batch_config: Optional[ScreeningBatchConfig] = Field(
        None, description="Optional batch configuration"
    )


class ScreeningBatchResponse(BaseModel):
    """Response for screening batch."""
    id: UUID
    position_id: UUID
    status: str  # "queued" | "screening" | "pending_review" | "completed"
    total_candidates: int
    screened_count: int
    pending_review_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ScreeningBatchStatusResponse(BaseModel):
    """Batch status for polling."""
    batch_id: UUID
    position_id: UUID
    status: str
    total_candidates: int
    screened_count: int
    pending_review_count: int
    progress_percentage: float
    estimated_completion_seconds: Optional[float] = None


# ============================================================================
# SCREENING RESULTS
# ============================================================================


class ScreeningResultSummaryCard(BaseModel):
    """Quick summary card for review queue."""
    screening_result_id: UUID
    candidate_name: str
    candidate_email: str
    resume_id: UUID
    agent_recommendation: ScreeningRecommendation
    confidence_score: int  # 0-100
    screening_summary_preview: str  # First 150 chars
    has_bias_alerts: bool


class ScreeningResultDetailResponse(BaseModel):
    """Full screening result for detailed review."""
    screening_result_id: UUID
    candidate_id: UUID
    candidate_name: str
    candidate_email: str
    resume_id: UUID

    # Agent analysis
    agent_recommendation: ScreeningRecommendation
    confidence_score: int  # 0-100
    screening_summary: str  # Full 5-min recruiter brief

    # Detailed analysis
    skills_matched: list[str]
    skills_missing: list[str]
    experience_fit: dict  # {"years": int, "relevance": "high" | "medium" | "low"}
    career_trajectory: dict
    red_flags: list[dict]  # [{"type": str, "description": str}]

    # Conscience checks
    bias_flags: dict  # {"demographic_indicators": [...], "fairness_notes": str, ...}

    # Recruiter decision (null if not yet decided)
    recruiter_decision: Optional[RecruiterDecision] = None
    recruiter_notes: Optional[str] = None
    was_overridden: bool = False

    # Timestamps
    created_at: datetime


class ScreeningBatchPendingResponse(BaseModel):
    """Paginated list of screening results pending recruiter review."""
    results: list[ScreeningResultSummaryCard]
    pagination: dict  # {"total": int, "page": int, "limit": int, "pages": int}


# ============================================================================
# RECRUITER DECISIONS
# ============================================================================


class ScreeningDecisionRequest(BaseModel):
    """Recruiter decision on a screening result."""
    recruiter_decision: RecruiterDecision = Field(
        ..., description="Interview, Hold, or Further Review"
    )
    recruiter_notes: Optional[str] = Field(
        None, description="Optional notes explaining the decision"
    )
    recruiter_confidence: Optional[int] = Field(
        None, ge=0, le=100, description="Recruiter's confidence (0-100, optional for learning)"
    )


class ScreeningDecisionResponse(BaseModel):
    """Response after recording recruiter decision."""
    status: str  # "recorded"
    decision_id: UUID
    screening_result_id: UUID


class ScreeningBulkDecisionRequest(BaseModel):
    """Bulk recruiter decisions."""
    decisions: list[dict] = Field(
        ...,
        description="List of {screening_result_id, recruiter_decision, recruiter_notes (optional)}",
    )


class ScreeningBulkDecisionResponse(BaseModel):
    """Response after bulk decisions."""
    status: str  # "recorded"
    count: int  # Number of decisions processed
    decision_ids: list[UUID]


# ============================================================================
# ANALYTICS
# ============================================================================


class ScreeningBatchMetricsResponse(BaseModel):
    """Analytics for screening batch."""
    batch_id: UUID
    position_id: UUID
    total_screened: int
    recommendations: dict  # {"advance": int, "hold": int, "review": int}
    recruiter_decisions: dict  # {"interview": int, "hold": int, "further_review": int, "pending": int}
    override_rate: float  # Percentage of overridden recommendations
    avg_confidence_score: float
    bias_alerts_count: int
    time_to_complete_minutes: Optional[float] = None
    avg_recruiter_review_time_seconds: Optional[float] = None


__all__ = [
    "ScreeningBatchCreateRequest",
    "ScreeningBatchResponse",
    "ScreeningBatchStatusResponse",
    "ScreeningResultDetailResponse",
    "ScreeningBatchPendingResponse",
    "ScreeningDecisionRequest",
    "ScreeningDecisionResponse",
    "ScreeningBulkDecisionRequest",
    "ScreeningBulkDecisionResponse",
    "ScreeningBatchMetricsResponse",
]
