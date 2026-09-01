"""Pydantic schemas for candidate matches."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SkillMatchData(BaseModel):
    """Skill match breakdown."""

    technical: list[str] = Field(default_factory=list, description="Matched tech skills")
    required: list[str] = Field(default_factory=list, description="Required skills")
    gaps: list[str] = Field(default_factory=list, description="Missing skills")
    match_score: int = Field(0, ge=0, le=100)


class ExperienceMatchData(BaseModel):
    """Experience match breakdown."""

    years_required: int
    years_candidate: int
    relevance: str = Field(..., description="high/medium/low")
    growth_trajectory: str
    match_score: int = Field(0, ge=0, le=100)


class TeamFitData(BaseModel):
    """Team fit assessment."""

    communication_style: str
    collaboration_signals: list[str] = Field(default_factory=list)
    leadership_fit: str
    team_match_score: int = Field(0, ge=0, le=100)


class CompensationFitData(BaseModel):
    """Compensation fit analysis."""

    job_salary_range: str
    candidate_expectation: Optional[str] = None
    alignment: str = Field(..., description="aligned/stretch/misaligned")
    stretch_factor: float = Field(1.0, description="Salary multiplier")


class MatchValidationData(BaseModel):
    """Match validation gates."""

    passed: bool
    issues: list[str] = Field(default_factory=list)
    risk_indicators: list[str] = Field(default_factory=list)


class ConcernsData(BaseModel):
    """Match concerns."""

    growth_gaps: list[str] = Field(default_factory=list)
    risk_signals: list[str] = Field(default_factory=list)
    needs_discussion: list[str] = Field(default_factory=list)


class OpportunitiesData(BaseModel):
    """Match opportunities."""

    growth_potential: list[str] = Field(default_factory=list)
    unique_strengths: list[str] = Field(default_factory=list)
    value_adds: list[str] = Field(default_factory=list)


class CandidateMatchResponse(BaseModel):
    """Full candidate match response."""

    id: UUID
    analysis_result_id: UUID
    position_id: UUID
    candidate_id: UUID
    status: str
    skill_match: SkillMatchData
    experience_match: ExperienceMatchData
    team_fit: TeamFitData
    compensation_fit: CompensationFitData
    overall_score: int
    fit_level: str
    rank_in_batch: Optional[int] = None
    percentile: Optional[int] = None
    concerns: ConcernsData
    opportunities: OpportunitiesData
    match_confidence: int
    match_completed_at: Optional[datetime] = None
    recruiter_reviewed: bool = False
    recruiter_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MatchInitiateRequest(BaseModel):
    """Request to initiate matching."""

    analysis_result_id: UUID = Field(..., description="Analysis result to match")


__all__ = [
    "SkillMatchData",
    "ExperienceMatchData",
    "TeamFitData",
    "CompensationFitData",
    "MatchValidationData",
    "ConcernsData",
    "OpportunitiesData",
    "CandidateMatchResponse",
    "MatchInitiateRequest",
]
