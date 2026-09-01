"""Request and response schemas for JD simulation."""
from __future__ import annotations

from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional

from app.models.jd_simulation import JDSimulationStatus, SimulationType


class JDSimulationStartRequest(BaseModel):
    """Request to start a JD simulation."""
    position_id: Optional[UUID] = Field(None, description="UUID of existing position to analyze")
    jd_text: Optional[str] = Field(None, description="Pasted JD text if creating new")
    simulation_type: SimulationType = Field(..., description="Type of simulation to run")
    target_candidate_profile: Optional[dict] = Field(None, description="Optional candidate profile to test against")

    class Config:
        json_schema_extra = {
            "examples": [{
                "position_id": None,
                "jd_text": "Senior Backend Engineer...",
                "simulation_type": "requirement_fit"
            }]
        }


class JDSimulationStartResponse(BaseModel):
    """Response after starting JD simulation."""
    simulation_id: UUID = Field(..., description="UUID of the simulation request")
    status: JDSimulationStatus = Field(..., description="Initial status (always 'pending')")


# Defaults below keep a completed simulation renderable when the LLM omits a
# field in a sub-item (partial structured output shouldn't 500 the result).
class CapabilityGapItem(BaseModel):
    """A single capability gap finding."""
    capability: str = ""
    current_description: Optional[str] = None
    recommended_description: str = ""
    market_example: Optional[str] = None


class CreepWarning(BaseModel):
    """A requirement creep warning."""
    severity: str = Field(default="medium", description="high/medium/low")
    issue: str = ""
    context: Optional[str] = None
    suggestion: Optional[str] = None


class ArchetypeFit(BaseModel):
    """Candidate archetype fit analysis."""
    archetype: str = Field(default="mid", description="junior/mid/senior/lead")
    fit_score: int = Field(default=0, ge=0, le=100)
    matched_capabilities: list[str] = []
    missing_capabilities: list[str] = []
    talent_pool_estimate: Optional[str] = None


class WordingSuggestion(BaseModel):
    """Suggested wording for a capability."""
    capability_area: str = ""
    current_phrasing: Optional[str] = None
    suggested_alternatives: list[str] = []
    reasoning: str = ""


class JDSimulationResult(BaseModel):
    """Complete JD simulation results."""
    simulation_id: UUID
    status: JDSimulationStatus

    # Capability gaps
    critical_capabilities: list[CapabilityGapItem] = []
    missing_clarity: list[str] = []
    capability_recommendations: list[CapabilityGapItem] = []

    # Requirement creep
    # Optional so a pending/processing simulation can be returned before the
    # engine has computed scores (the result row doesn't exist yet).
    requirement_difficulty_score: Optional[int] = Field(default=None, ge=0, le=100)
    experience_years_assessment: Optional[str] = None
    tech_stack_balance: Optional[str] = None
    creep_warnings: list[CreepWarning] = []

    # Candidate fit
    fit_by_archetype: list[ArchetypeFit] = []
    best_archetype_fit: Optional[str] = None
    talent_pool_estimate: Optional[str] = None

    # Quality assessment
    quality_score: Optional[int] = Field(default=None, ge=0, le=100)
    market_positioning: Optional[str] = None
    missing_sections: list[str] = []
    quality_issues: list[str] = []

    # Wording suggestions
    suggested_job_title_variations: list[str] = []
    improved_role_description: Optional[str] = None
    capability_verbiage_suggestions: list[WordingSuggestion] = []
    benefits_suggestions: list[str] = []
    culture_fit_language: Optional[str] = None


class JDSimulationListItem(BaseModel):
    """JD simulation item in list response."""
    simulation_id: UUID
    position_id: Optional[UUID] = None
    simulation_type: SimulationType
    status: JDSimulationStatus
    created_at: str
    quality_score: Optional[int] = None
    capability_gaps_count: int
    creep_warnings_count: int


class PaginatedJDSimulationList(BaseModel):
    """Paginated list of JD simulations."""
    items: list[JDSimulationListItem]
    total: int
    page: int
    page_size: int
    pages: int


class DetailedJDAnalysisRequest(BaseModel):
    """Request for detailed JD analysis."""
    jd_text: str = Field(..., min_length=10, description="Job description text to analyze")
    position_title: Optional[str] = Field(None, description="Job title for context")
    target_seniority: Optional[str] = Field(None, description="Target seniority level (junior/mid/senior/lead)")

    class Config:
        json_schema_extra = {
            "example": {
                "jd_text": "Senior Backend Engineer with 5+ years...",
                "position_title": "Senior Backend Engineer",
                "target_seniority": "senior"
            }
        }


class DetailedJDAnalysisResponse(BaseModel):
    """Response with detailed JD analysis results."""
    score: int = Field(..., ge=0, le=100, description="Overall quality score")
    dimensions: dict = Field(..., description="Detailed scoring by dimension")
    issues: list[str] = Field(default_factory=list, description="Identified issues")
    suggestions: list[dict] = Field(default_factory=list, description="Improvement suggestions with priority")


class SuggestionAcceptanceRequest(BaseModel):
    """Request to accept and apply a JD suggestion."""
    suggestion_id: str = Field(..., description="ID of the suggestion to accept")
    modified_text: str = Field(..., min_length=10, description="Modified JD text after applying suggestion")

    class Config:
        json_schema_extra = {
            "example": {
                "suggestion_id": "sugg-001",
                "modified_text": "Improved job description text..."
            }
        }


class SuggestionAcceptanceResponse(BaseModel):
    """Response after accepting a suggestion."""
    updated_jd: str = Field(..., description="Updated JD text")
    suggestion_id: str = Field(..., description="ID of the applied suggestion")
    timestamp: str = Field(..., description="ISO 8601 timestamp")


class SimulationHistoryItem(BaseModel):
    """Item in simulation history list."""
    simulation_id: UUID
    position_id: Optional[UUID] = None
    position_title: Optional[str] = None
    jd_text_preview: str = Field(..., description="First 200 chars of JD")
    simulation_type: SimulationType
    status: JDSimulationStatus
    quality_score: Optional[int] = None
    created_at: str
    completed_at: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "simulation_id": "550e8400-e29b-41d4-a716-446655440000",
                "position_title": "Senior Engineer",
                "jd_text_preview": "We are hiring for a Senior Engineer...",
                "simulation_type": "requirement_fit",
                "status": "completed",
                "quality_score": 82,
                "created_at": "2026-06-03T10:30:00Z",
                "completed_at": "2026-06-03T10:45:00Z"
            }
        }


class PaginatedSimulationHistory(BaseModel):
    """Paginated simulation history."""
    items: list[SimulationHistoryItem]
    total: int
    limit: int
    offset: int
