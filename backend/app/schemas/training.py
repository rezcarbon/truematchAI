"""Pydantic schemas for Training Simulation System API endpoints."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.training import FeedbackType


class TrainingFeedbackCreate(BaseModel):
    """Request schema for submitting training feedback."""

    user_id: UUID = Field(..., description="Recruiter or candidate ID")
    match_id: Optional[UUID] = Field(None, description="Match ID if feedback is on a specific match")
    job_id: Optional[UUID] = Field(None, description="Job ID being applied/rejected for")
    candidate_id: Optional[UUID] = Field(None, description="Candidate ID")
    feedback_type: FeedbackType = Field(
        ...,
        description="Type: hire, reject, maybe, interested, not_interested, applied"
    )
    rating: Optional[int] = Field(None, ge=1, le=5, description="1-5 star rating")
    comments: Optional[str] = Field(None, description="Comments explaining the decision")
    time_to_action_seconds: Optional[int] = Field(
        None, description="Time in seconds before making decision"
    )
    source: Optional[str] = Field("web", description="Source: web, mobile, api")


class TrainingFeedbackResponse(TrainingFeedbackCreate):
    """Response schema for training feedback."""

    id: UUID
    outcome: Optional[str] = Field(None, description="hired, rejected, pending")
    hire_success: Optional[bool] = Field(
        None, description="Still employed after 6 months?"
    )
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CapabilityMappingResponse(BaseModel):
    """Response schema for capability mappings."""

    id: UUID
    cv_keyword: str = Field(..., description="CV keyword/phrase")
    capability: str = Field(..., description="Corresponding capability")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in this mapping (0-1)"
    )
    frequency: int = Field(..., description="How many times seen")
    positive_feedback: int = Field(..., description="Confirmations of correctness")
    negative_feedback: int = Field(..., description="Rejections/corrections")
    job_category: Optional[str]
    industry: Optional[str]
    is_user_added: bool = Field(
        ..., description="Was this added manually by admin?"
    )
    learned_from_feedback: bool = Field(
        ..., description="Was this learned from user feedback?"
    )
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CredentialMappingResponse(BaseModel):
    """Response schema for credential mappings."""

    id: UUID
    credential: str = Field(..., description="Candidate credential")
    requirement: str = Field(..., description="Job requirement")
    match_score: float = Field(
        ..., ge=0.0, le=1.0, description="Match quality (0-1)"
    )
    is_exact_match: bool
    is_acceptable_alternative: bool
    alternative_matches: Optional[List[str]] = Field(
        None, description="Other credentials that also match"
    )
    positive_feedback: int
    negative_feedback: int
    industry: Optional[str]
    region: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SuccessPatternResponse(BaseModel):
    """Response schema for success patterns."""

    id: UUID
    job_id: Optional[UUID] = Field(None, description="Job this pattern applies to")
    job_category: Optional[str] = Field(None, description="Job category")
    successful_candidate_profile: Dict[str, Any] = Field(
        ..., description="Characteristics of successful hires"
    )
    key_capabilities: List[str] = Field(
        ..., description="Most important capabilities"
    )
    key_credentials: List[str] = Field(
        ..., description="Required credentials"
    )
    success_rate: float = Field(
        ..., ge=0.0, le=1.0, description="% of hires retained 6+ months"
    )
    average_tenure_months: Optional[int] = Field(
        None, description="Average time employed"
    )
    average_performance_rating: Optional[float]
    sample_size: int = Field(..., description="Number of hires analyzed")
    industry: Optional[str]
    region: Optional[str]
    salary_range: Optional[str]
    confidence_level: float = Field(
        ..., ge=0.0, le=1.0, description="How confident is this pattern?"
    )
    is_valid: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrainingProgressResponse(BaseModel):
    """Response schema for training progress metrics."""

    id: UUID
    metric_name: str = Field(
        ...,
        description="match_accuracy, hire_success_rate, user_satisfaction, etc"
    )
    current_value: float = Field(..., description="Current metric value")
    baseline_value: float = Field(..., description="Starting value for comparison")
    improvement_percent: float = Field(
        ..., description="% improvement from baseline"
    )
    sample_count: int = Field(
        ..., description="Number of data points used for this metric"
    )
    period: str = Field(..., description="daily, weekly, monthly")
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrainingInsightResponse(BaseModel):
    """Response schema for insights."""

    id: UUID
    insight_type: str = Field(
        ...,
        description="skill_demand, success_factor, trend, market_analysis"
    )
    insight_category: Optional[str] = Field(
        None, description="Domain: software, engineering, marketing, etc"
    )
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Full insight description")
    metric_value: Optional[float] = Field(
        None, description="Supporting metric value"
    )
    sample_size: int = Field(..., description="Data points backing this insight")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in this insight"
    )
    supporting_data: Dict[str, Any] = Field(
        ..., description="Additional data backing the insight"
    )
    industry: Optional[str]
    region: Optional[str]
    is_public: bool = Field(..., description="Can be shown to users?")
    is_trending: bool = Field(..., description="Is this a trending insight?")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VirtualBrainStateResponse(BaseModel):
    """Response schema for virtual brain state."""

    id: UUID
    version: int = Field(..., description="Model version number")
    is_active: bool = Field(..., description="Is this the current active model?")
    total_feedback_samples: int = Field(
        ..., description="Total training samples received"
    )
    total_patterns_learned: int = Field(
        ..., description="Number of patterns discovered"
    )
    match_accuracy: float = Field(
        ..., ge=0.0, le=1.0, description="Accuracy of match predictions"
    )
    hire_success_prediction_accuracy: float = Field(
        ..., ge=0.0, le=1.0, description="Accuracy of hire success predictions"
    )
    model_data: Dict[str, Any] = Field(..., description="Serialized model data")
    performance_metrics: Dict[str, Any] = Field(
        ..., description="Performance metrics over time"
    )
    training_started_at: Optional[datetime]
    training_completed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrainingStatsResponse(BaseModel):
    """Comprehensive training statistics response."""

    total_feedback: int = Field(..., description="Total feedback submissions")
    feedback_by_type: Dict[str, int] = Field(
        ..., description="Breakdown by feedback type"
    )
    capability_mappings_learned: int = Field(
        ..., description="Unique capability mappings learned"
    )
    credential_mappings_learned: int = Field(
        ..., description="Unique credential mappings learned"
    )
    success_patterns_discovered: int = Field(
        ..., description="Success patterns for different job types"
    )
    current_model: Dict[str, Any] = Field(
        ...,
        description={
            "version": "Model version",
            "match_accuracy": "% accurate matches",
            "hire_success_accuracy": "% accurate hire success predictions",
            "total_patterns": "Patterns learned",
        },
    )
