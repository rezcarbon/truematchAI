"""Request/response schemas for Transition Intelligence."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.models.transition_analysis import TransitionStatus


class TransitionStartRequest(BaseModel):
    resume_id: UUID
    current_role: Optional[str] = Field(None, max_length=255)
    target: Optional[str] = Field(None, max_length=2000)


class TransitionStartResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    analysis_id: UUID
    status: TransitionStatus


class CourseRecommendation(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    capability: str
    title: str
    provider: str
    url: Optional[str] = None
    format: Optional[str] = None
    duration_weeks: Optional[int] = None
    level: Optional[str] = None
    relevance: str = ""


class UpskillingItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    capability: str
    why: str = ""
    how: str = ""
    recommended_training: list[CourseRecommendation] = []


class TransitionTimeline(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    months_min: int
    months_max: int
    confidence: str  # low | medium | high
    basis: str = ""


class TransitionOption(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    role: str
    direction: str  # lateral | upward | adjacent
    feasibility: str  # READY | STRETCH | ASPIRATIONAL
    rationale: str
    transferable_strengths: list[str] = []
    upskilling_gap: list[UpskillingItem] = []
    timeline: Optional[TransitionTimeline] = None
    evidence_strength: str  # HIGH | MEDIUM | WEAK


class TransitionResult(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    analysis_id: UUID
    status: TransitionStatus
    current_role: Optional[str] = None
    source_language: Optional[str] = None
    # The capability verdict the prediction is anchored on (the constant anchor).
    capability_score: Optional[int] = None
    readiness_summary: Optional[str] = None
    transition_options: list[TransitionOption] = []
    honesty_notes: Optional[str] = None
    dropped_ungrounded: int = 0
    error: Optional[str] = None


class TransitionListItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    analysis_id: UUID
    current_role: Optional[str] = None
    status: TransitionStatus
    created_at: str
    capability_score: Optional[int] = None


# --- Phase 3: longitudinal tracking ----------------------------------------


class TrackRequest(BaseModel):
    enabled: bool = True


class TrajectoryPoint(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    analysis_id: str
    date: Optional[str] = None
    capability_score: Optional[int] = None
    options: int = 0
    ready: int = 0
    stretch: int = 0
    aspirational: int = 0
    top_role: Optional[str] = None


class OutcomeRecordRequest(BaseModel):
    analysis_id: UUID
    predicted_role: str = Field(max_length=255)
    status: str  # predicted | pursuing | achieved | not_pursued
    actual_role: Optional[str] = Field(None, max_length=255)
    note: Optional[str] = Field(None, max_length=2000)


class OutcomeDTO(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: UUID
    analysis_id: UUID
    predicted_role: str
    status: str
    actual_role: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[str] = None


class TransitionMetrics(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    analyses_total: int = 0
    analyses_completed: int = 0
    tracked: int = 0
    candidates: int = 0
    readiness: dict = {}
    outcomes: dict = {}
    resolved_outcomes: int = 0
    achievement_rate: Optional[float] = None
