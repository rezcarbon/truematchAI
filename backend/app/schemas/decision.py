"""Decision-related schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.decision import DecisionOutcome


class DecisionCreate(BaseModel):
    assessment_id: uuid.UUID
    position_id: uuid.UUID
    decision: DecisionOutcome
    ai_recommendation_followed: bool | None = None
    override_reasoning: str | None = None
    cultural_fit_notes: str | None = None
    interview_notes: str | None = None


class DecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assessment_id: uuid.UUID
    position_id: uuid.UUID
    recruiter_id: uuid.UUID | None
    decision: DecisionOutcome
    ai_recommendation_followed: bool | None
    override_reasoning: str | None
    cultural_fit_notes: str | None
    interview_notes: str | None
    created_at: datetime
