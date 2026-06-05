"""Request and response schemas for JD simulation."""
from __future__ import annotations

from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional

from app.models.jd_simulation import JDSimulationStatus, SimulationType
from app.models.cv_analysis import SeniorityLevel


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


class CapabilityGapItem(BaseModel):
    """A single capability gap finding."""
    capability: str
    current_description: Optional[str] = None
    recommended_description: str
    market_example: Optional[str] = None


class CreepWarning(BaseModel):
    """A requirement creep warning."""
    severity: str = Field(..., description="high/medium/low")
    issue: str
    context: Optional[str] = None
    suggestion: Optional[str] = None


class ArchetypeFit(BaseModel):
    """Candidate archetype fit analysis."""
    archetype: str = Field(..., description="junior/mid/senior/lead")
    fit_score: int = Field(..., ge=0, le=100)
    matched_capabilities: list[str] = []
    missing_capabilities: list[str] = []
    talent_pool_estimate: Optional[str] = None


class WordingSuggestion(BaseModel):
    """Suggested wording for a capability."""
    capability_area: str
    current_phrasing: Optional[str] = None
    suggested_alternatives: list[str] = []
    reasoning: str


class JDSimulationResult(BaseModel):
    """Complete JD simulation results."""
    simulation_id: UUID
    status: JDSimulationStatus

    # Capability gaps
    critical_capabilities: list[CapabilityGapItem] = []
    missing_clarity: list[str] = []
    capability_recommendations: list[CapabilityGapItem] = []

    # Requirement creep
    requirement_difficulty_score: int = Field(..., ge=0, le=100)
    experience_years_assessment: Optional[str] = None
    tech_stack_balance: Optional[str] = None
    creep_warnings: list[CreepWarning] = []

    # Candidate fit
    fit_by_archetype: list[ArchetypeFit] = []
    best_archetype_fit: Optional[str] = None
    talent_pool_estimate: Optional[str] = None

    # Quality assessment
    quality_score: int = Field(..., ge=0, le=100)
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
