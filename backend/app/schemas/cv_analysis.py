"""Request and response schemas for CV analysis."""
from __future__ import annotations

from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional

from app.models.cv_analysis import CVAnalysisStatus, SeniorityLevel


class CVAnalysisStartRequest(BaseModel):
    """Request to start a CV analysis."""
    resume_id: UUID = Field(..., description="UUID of the resume to analyze")
    target_role: str = Field(..., min_length=1, max_length=255, description="Target role (e.g., 'Senior Backend Engineer')")
    target_seniority: SeniorityLevel = Field(..., description="Target seniority level")
    career_focus_areas: Optional[list[str]] = Field(None, description="Capabilities they want to build")


class CVAnalysisStartResponse(BaseModel):
    """Response after starting CV analysis."""
    analysis_id: UUID = Field(..., description="UUID of the analysis request")
    status: CVAnalysisStatus = Field(..., description="Initial status (always 'pending')")


class CVAnalysisGapItem(BaseModel):
    """A single skill gap or weakness."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    capability: str
    importance: str = Field(..., description="high/medium/low")
    description: Optional[str] = None
    how_to_improve: Optional[str] = None


class CVAnalysisRecommendation(BaseModel):
    """A single CV improvement recommendation."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    category: str = Field(..., description="skills/achievements/keywords/structure")
    suggestion: str
    priority: str = Field(..., description="high/medium/low")
    example: Optional[str] = None


class JobFitMatch(BaseModel):
    """A job position match result."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    position_id: UUID
    job_title: str
    company: Optional[str] = None
    match_score: int = Field(..., ge=0, le=100)
    semantic_score: int = Field(..., ge=0, le=100)
    why_fit: str
    why_not_fit: Optional[str] = None
    key_aligned_capabilities: list[str] = []
    missing_capabilities: list[str] = []


class CVAnalysisResult(BaseModel):
    """Complete CV analysis results."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    analysis_id: UUID
    status: CVAnalysisStatus

    # Skill gaps
    missing_capabilities: list[CVAnalysisGapItem] = []
    weakness_areas: list[CVAnalysisGapItem] = []
    strength_summary: Optional[str] = None

    # Job fit analysis
    top_matching_positions: list[JobFitMatch] = []
    total_matching_jobs: int = 0

    # CV improvements
    improvement_suggestions: list[CVAnalysisRecommendation] = []
    reworded_cv_sections: Optional[dict] = None

    # Career insights
    trajectory_analysis: Optional[str] = None
    market_positioning: Optional[str] = None
    growth_opportunities: list[str] = []


class CVAnalysisListItem(BaseModel):
    """CV analysis item in list response."""
    analysis_id: UUID
    target_role: str
    target_seniority: SeniorityLevel
    status: CVAnalysisStatus
    created_at: str
    skill_gaps_count: int
    matching_jobs_count: int


class PaginatedCVAnalysisList(BaseModel):
    """Paginated list of CV analyses."""
    items: list[CVAnalysisListItem]
    total: int
    page: int
    page_size: int
    pages: int
