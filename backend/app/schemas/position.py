"""Position-related schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.position import PositionStatus


class PositionCreate(BaseModel):
    title: str
    description: str | None = None
    company_id: uuid.UUID | None = None


class PositionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: PositionStatus | None = None


class PositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    # Nullable: candidate self-assessment positions have no owning company.
    company_id: uuid.UUID | None
    created_by: uuid.UUID | None
    title: str
    description: str | None
    parsed_requirements: dict | None
    jd_quality_score: int | None
    jd_issues: dict | None
    status: PositionStatus
    created_at: datetime
    updated_at: datetime


class PositionList(BaseModel):
    items: list[PositionResponse]
    total: int
