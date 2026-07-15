"""Pydantic schemas for hiring outcomes."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PerformanceDetailsData(BaseModel):
    """Performance evaluation details."""

    on_time: bool
    quality: int = Field(0, ge=0, le=100)
    feedback: str


class AccuracyTrackingData(BaseModel):
    """Prediction accuracy tracking."""

    prediction_correct: bool
    variance: int = Field(..., description="Score difference from prediction")
    factors: list[str] = Field(default_factory=list, description="Contributing factors")


class LearningFeedbackData(BaseModel):
    """Learning feedback for evolution agent."""

    assessment_predictiveness: str
    interview_signals_accuracy: str
    skill_match_accuracy: int = Field(0, ge=0, le=100)
    unexpected_outcomes: list[str] = Field(default_factory=list)


class BiasSignalsData(BaseModel):
    """Bias detection in hiring outcome."""

    suspected_bias: list[str] = Field(default_factory=list)
    protected_attributes: list[str] = Field(default_factory=list)
    fairness_concerns: list[str] = Field(default_factory=list)


class HiringOutcomeResponse(BaseModel):
    """Full hiring outcome response."""

    id: UUID
    candidate_match_id: UUID
    position_id: UUID
    candidate_id: UUID
    hiring_decision: str
    decision_made_at: Optional[datetime] = None
    decision_rationale: Optional[str] = None
    hired: bool
    hire_date: Optional[datetime] = None
    tenure_days: Optional[int] = None
    performance_rating: Optional[str] = None
    performance_evaluated_at: Optional[datetime] = None
    performance_details: Optional[PerformanceDetailsData] = None
    retained: Optional[bool] = None
    last_active_at: Optional[datetime] = None
    screening_recommendation: Optional[str] = None
    assessment_recommendation: Optional[str] = None
    match_score_at_time: Optional[int] = None
    actual_performance_vs_prediction: AccuracyTrackingData
    learning_feedback: LearningFeedbackData
    bias_signals: BiasSignalsData
    improvement_notes: Optional[str] = None
    recruiter_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HiringOutcomeRecordRequest(BaseModel):
    """Request to record hiring outcome."""

    candidate_match_id: UUID
    hiring_decision: str = Field(..., description="hired/not_hired/offer_declined/withdrawn")
    decision_rationale: Optional[str] = None
    hire_date: Optional[datetime] = None


class PerformanceRecordRequest(BaseModel):
    """Request to record performance."""

    hiring_outcome_id: UUID
    performance_rating: str = Field(..., description="exceeding/meeting/developing/underperforming")
    performance_details: PerformanceDetailsData
    learning_feedback: LearningFeedbackData


__all__ = [
    "PerformanceDetailsData",
    "AccuracyTrackingData",
    "LearningFeedbackData",
    "BiasSignalsData",
    "HiringOutcomeResponse",
    "HiringOutcomeRecordRequest",
    "PerformanceRecordRequest",
]
