"""Pydantic schemas for analysis results."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ResponseAnalysisData(BaseModel):
    """Analysis of a single response."""

    text: str = Field(..., description="Candidate response text")
    parsed_intent: str = Field(..., description="Interpreted intent")
    correctness_level: str = Field(..., description="Technical correctness")
    comprehension_score: int = Field(0, ge=0, le=100, description="Understanding score")
    evidence: str = Field(..., description="Supporting evidence")


class ScoringResultData(BaseModel):
    """Score for a single question."""

    question_id: str
    score: int = Field(0, ge=0, le=100)
    rubric_alignment: str = Field(..., description="How well aligns with rubric")
    confidence: int = Field(0, ge=0, le=100)


class PatternAnalysisData(BaseModel):
    """Pattern analysis findings."""

    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    growth_signals: list[str] = Field(default_factory=list)


class OverallMetricsData(BaseModel):
    """Overall assessment metrics."""

    total_score: int = Field(0, ge=0, le=100)
    normalized_score: int = Field(0, ge=0, le=100)
    response_quality: str = Field(..., description="excellent/good/fair/poor")
    completeness: int = Field(0, ge=0, le=100)


class FairnessCheckData(BaseModel):
    """Fairness check results."""

    passed: bool
    bias_indicators: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    fairness_score: int = Field(0, ge=0, le=100)


class RecommendationData(BaseModel):
    """Analysis recommendation."""

    decision: str = Field(..., description="advance/explore/review")
    confidence: int = Field(0, ge=0, le=100)
    rationale: str = Field(...)


class AnalysisResultResponse(BaseModel):
    """Full analysis result response."""

    id: UUID
    assessment_id: UUID
    assessment_design_id: UUID
    candidate_id: UUID
    position_id: UUID
    status: str
    responses_analyzed: dict
    scoring_results: dict
    pattern_analysis: PatternAnalysisData
    overall_metrics: OverallMetricsData
    analysis_fairness_check: FairnessCheckData
    recommendation: RecommendationData
    overall_confidence: int
    analysis_note: Optional[str] = None
    analysis_completed_at: Optional[datetime] = None
    recruiter_reviewed: bool = False
    recruiter_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalysisInitiateRequest(BaseModel):
    """Request to initiate analysis."""

    assessment_id: UUID = Field(..., description="Assessment ID to analyze")


__all__ = [
    "ResponseAnalysisData",
    "ScoringResultData",
    "PatternAnalysisData",
    "OverallMetricsData",
    "FairnessCheckData",
    "RecommendationData",
    "AnalysisResultResponse",
    "AnalysisInitiateRequest",
]
