"""Schemas for ATS features: pipeline, interviews, scorecards."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Application / Pipeline Schemas
# ============================================================================

class ApplicationCreate(BaseModel):
    """Create a new application."""
    resume_id: uuid.UUID
    position_id: uuid.UUID
    source: Optional[str] = Field(None, description="Application source (linkedin, referral, indeed, etc)")
    tags: Optional[dict] = Field(None, description="Custom tags for this application")


class ApplicationUpdate(BaseModel):
    """Update an application (stage, tags, source)."""
    stage: Optional[str] = Field(None, description="Pipeline stage")
    tags: Optional[dict] = Field(None, description="Custom tags")
    source: Optional[str] = Field(None, description="Application source")


class ApplicationResponse(BaseModel):
    """Application response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resume_id: uuid.UUID
    position_id: uuid.UUID
    user_id: uuid.UUID
    stage: str
    stage_entered_at: datetime
    source: Optional[str]
    tags: Optional[dict]
    applied_at: datetime
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Interview Schemas
# ============================================================================

class InterviewSlotCreate(BaseModel):
    """Create an available interview slot."""
    start_time: datetime
    end_time: datetime


class InterviewCreate(BaseModel):
    """Schedule an interview."""
    application_id: uuid.UUID
    position_id: uuid.UUID
    interviewer_ids: list[uuid.UUID] = Field(description="List of interviewer user IDs")
    meeting_platform: Optional[str] = Field(None, description="zoom, google_meet, teams")
    meeting_link: Optional[str] = Field(None)


class InterviewUpdate(BaseModel):
    """Update interview details."""
    scheduled_at: Optional[datetime] = None
    interviewer_ids: Optional[list[uuid.UUID]] = None
    meeting_platform: Optional[str] = None
    meeting_link: Optional[str] = None
    status: Optional[str] = None  # scheduled, completed, cancelled


class InterviewResponse(BaseModel):
    """Interview response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    position_id: uuid.UUID
    scheduled_at: Optional[datetime]
    interviewer_ids: list[uuid.UUID]
    candidate_email: Optional[str]
    meeting_link: Optional[str]
    meeting_platform: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime


class InterviewListResponse(BaseModel):
    """Interview list response with pagination."""
    items: list[InterviewResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Scorecard Schemas
# ============================================================================

class ScorecardCreate(BaseModel):
    """Submit a scorecard."""
    interview_id: uuid.UUID
    competency_scores: dict = Field(description="{competency_name: score}")
    feedback: Optional[str] = None
    overall_recommendation: Optional[str] = Field(None, description="strong_yes, yes, no, strong_no")


class ScorecardUpdate(BaseModel):
    """Update scorecard (before submission)."""
    competency_scores: Optional[dict] = None
    feedback: Optional[str] = None
    overall_recommendation: Optional[str] = None


class ScorecardResponse(BaseModel):
    """Scorecard response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    interview_id: uuid.UUID
    interviewer_id: uuid.UUID
    position_id: uuid.UUID
    competency_scores: dict
    feedback: Optional[str]
    overall_recommendation: Optional[str]
    submitted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ScorecardListResponse(BaseModel):
    """Scorecard list response."""
    items: list[ScorecardResponse]
    total: int


# ============================================================================
# Pipeline Analytics Schemas
# ============================================================================

class PipelineStageMetrics(BaseModel):
    """Metrics for a single pipeline stage."""
    stage: str
    count: int
    average_days_in_stage: float
    median_days_in_stage: float


class PipelineAnalyticsResponse(BaseModel):
    """Pipeline analytics data."""
    position_id: uuid.UUID
    total_applications: int
    by_stage: list[PipelineStageMetrics]
    conversion_rates: dict  # {stage_from -> stage_to: percentage}
    average_time_to_hire: float  # days


class SourceMetrics(BaseModel):
    """Metrics by application source."""
    source: str
    applications: int
    hires: int
    hire_rate: float
    average_time_to_hire: float


class SourceAnalyticsResponse(BaseModel):
    """Source effectiveness analytics."""
    position_id: Optional[uuid.UUID]  # None = all positions
    by_source: list[SourceMetrics]
