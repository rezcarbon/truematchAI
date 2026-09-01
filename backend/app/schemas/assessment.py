"""Assessment-related schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.assessment import AssessmentStatus


class AssessmentCreate(BaseModel):
    resume_id: uuid.UUID
    position_id: uuid.UUID


class SelfAssessmentCreate(BaseModel):
    """Candidate self-serve assessment: a resume + a pasted job description.

    The server creates an internal, company-less position from the JD and runs
    the standard pipeline against it.
    """

    resume_id: uuid.UUID
    jd_text: str = Field(min_length=20, max_length=20000)
    position_title: str | None = Field(default=None, max_length=255)


class AssessmentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resume_id: uuid.UUID
    position_id: uuid.UUID
    user_id: uuid.UUID
    status: AssessmentStatus
    traditional_score: int | None
    capability_score: int | None
    score_delta: int | None
    counter_rec_triggered: bool
    created_at: datetime
    updated_at: datetime


class AssessmentDetail(AssessmentSummary):
    traditional_detail: dict | None = None
    semantic_score: int | None = None
    semantic_detail: dict | None = None
    capability_components: dict | None = None
    capability_narrative: str | None = None
    capability_evidence: dict | None = None
    trajectory_data: dict | None = None
    trajectory_narrative: str | None = None
    counter_rec_reasoning: str | None = None
    counter_rec_evidence: dict | None = None
    jd_quality_score: int | None = None
    jd_issues: dict | None = None
    verified_evidence: dict | None = None
    substitutions: dict | None = None
    governance_audit_id: uuid.UUID | None = None
    # Detected source language of the original CV / JD when non-English (an English
    # pivot was scored). None or "en" means the input was English. Lets the UI show
    # a "translated from …" badge so reviewers know the text was machine-translated.
    source_language: str | None = None
    jd_source_language: str | None = None


class NarrativeResponse(BaseModel):
    assessment_id: uuid.UUID
    capability_narrative: str | None
    capability_components: dict | None
    capability_evidence: dict | None


class TrajectoryResponse(BaseModel):
    assessment_id: uuid.UUID
    trajectory_data: dict | None
    trajectory_narrative: str | None


class GovernanceResponse(BaseModel):
    """Governance results exposed to clients.

    IP-SAFETY: returns only pass/fail booleans and qualitative flags.
    No threshold values are ever included.
    """

    assessment_id: uuid.UUID
    coherence: dict | None
    consistency: dict | None
    fidelity: dict | None
    bias_flags: dict | None
    audit_id: uuid.UUID | None


class TraditionalResponse(BaseModel):
    assessment_id: uuid.UUID
    traditional_score: int | None
    traditional_detail: dict | None


class ComparisonResponse(BaseModel):
    """Side-by-side of the three signals: keyword baseline -> semantic -> capability."""

    assessment_id: uuid.UUID
    traditional_score: int | None
    semantic_score: int | None = None
    capability_score: int | None
    score_delta: int | None
    counter_rec_triggered: bool
    # hidden_gem | surfaced_strong_match | keyword_aligned
    match_type: str | None = None
    counter_rec_reasoning: str | None
    summary: str | None = None


class PaginatedAssessments(BaseModel):
    items: list[AssessmentSummary]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
