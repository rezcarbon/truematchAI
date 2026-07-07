"""Schemas for job search, applications, and career coaching."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Job Search & Filters
# ============================================================================


class JobFilter(BaseModel):
    """Filter criteria for job search."""

    model_config = ConfigDict(from_attributes=True)

    role: Optional[str] = Field(None, description="Job role/title")
    location: Optional[str] = Field(None, description="Job location")
    salary_min: Optional[int] = Field(None, ge=0, description="Minimum salary")
    salary_max: Optional[int] = Field(None, ge=0, description="Maximum salary")
    match_score: Optional[str] = Field(
        None,
        description="Match score range, e.g. '80-100' or '60'",
    )
    company: Optional[str] = Field(None, description="Company name")
    remote_only: Optional[bool] = Field(None, description="Only remote positions")
    keywords: Optional[list[str]] = Field(
        None,
        description="Keywords to search in title/description",
    )


class JobSearchResponse(BaseModel):
    """Job with match score and metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: Optional[str]
    company_id: Optional[uuid.UUID]
    status: str
    parsed_requirements: Optional[dict]
    jd_quality_score: Optional[int]
    match_score: Optional[int] = Field(None, ge=0, le=100)
    match_reasoning: Optional[str] = None
    capability_gap_areas: Optional[list[str]] = None
    created_at: datetime
    updated_at: datetime


class JobSearchResults(BaseModel):
    """Paginated job search results."""

    items: list[JobSearchResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Saved Jobs
# ============================================================================


class SaveJobRequest(BaseModel):
    """Request to save a job."""

    position_id: uuid.UUID
    list_name: str = Field("Default", description="Name of the list")
    notes: Optional[str] = Field(None, description="Personal notes")


class SaveJobResponse(BaseModel):
    """Saved job response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    position_id: uuid.UUID
    job_title: Optional[str]
    company_name: Optional[str]
    match_score: Optional[float]
    status: str
    list_name: str
    notes: Optional[str]
    viewed_at: Optional[datetime]
    applied_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class SavedJobsList(BaseModel):
    """List of saved jobs with metadata."""

    items: list[SaveJobResponse]
    total: int
    page: int
    page_size: int


class UpdateSavedJobRequest(BaseModel):
    """Request to update a saved job."""

    notes: Optional[str] = None
    list_name: Optional[str] = None
    status: Optional[str] = None


# ============================================================================
# Applications
# ============================================================================


class ApplicationRequest(BaseModel):
    """Request to apply to a position."""

    position_id: uuid.UUID
    resume_id: uuid.UUID
    cover_letter: Optional[str] = None
    source: str = Field("direct", description="Source of application")


class ApplicationResponse(BaseModel):
    """Application response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    position_id: uuid.UUID
    resume_id: uuid.UUID
    user_id: uuid.UUID
    stage: str
    source: Optional[str]
    applied_at: datetime
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Assessment Feedback
# ============================================================================


class FeedbackItem(BaseModel):
    """Individual piece of feedback."""

    category: str = Field(..., description="e.g., 'technical', 'communication'")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating 1-5")
    comment: Optional[str] = Field(None, description="Feedback text")
    timestamp: Optional[datetime] = None


class AssessmentFeedback(BaseModel):
    """Feedback on an assessment shared by recruiter."""

    model_config = ConfigDict(from_attributes=True)

    assessment_id: uuid.UUID
    recruiter_id: Optional[uuid.UUID]
    shared_at: Optional[datetime]
    feedback_items: list[FeedbackItem] = Field(default_factory=list)
    overall_notes: Optional[str] = None
    next_steps: Optional[str] = None


# ============================================================================
# Application Timeline
# ============================================================================


class TimelineEvent(BaseModel):
    """A single timeline event."""

    event_type: str = Field(..., description="Event type")
    timestamp: datetime
    title: str
    description: Optional[str] = None
    metadata: Optional[dict] = None


class AssessmentTimeline(BaseModel):
    """Timeline of events for an assessment/application."""

    model_config = ConfigDict(from_attributes=True)

    assessment_id: uuid.UUID
    application_id: Optional[uuid.UUID]
    events: list[TimelineEvent] = Field(default_factory=list)
    status_summary: Optional[str] = None
    latest_event: Optional[TimelineEvent] = None
    created_at: datetime


# ============================================================================
# Interview Preparation
# ============================================================================


class InterviewPrepTopic(BaseModel):
    """A topic for interview preparation."""

    topic: str
    key_points: list[str]
    sample_questions: list[str]
    tips: list[str]
    resources: Optional[list[str]] = None


class InterviewPrepResponse(BaseModel):
    """Interview preparation tips and resources."""

    assessment_id: uuid.UUID
    position_title: str
    interview_type: str = "general"  # "technical", "behavioral", "general"
    topics: list[InterviewPrepTopic]
    general_tips: list[str]
    candidate_strengths: list[str]
    growth_areas: list[str]
    practice_scenarios: list[str]
    generated_at: datetime


# ============================================================================
# Chat Mode
# ============================================================================


class ChatModeRequest(BaseModel):
    """Chat request with mode selection."""

    session_id: str
    message: str
    mode: str = Field(
        "general",
        description="Chat mode: 'career_coach', 'interview_prep', 'general'",
    )
    history: list[dict] = Field(default_factory=list)


class CandidateContext(BaseModel):
    """Candidate context for career coach mode."""

    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    name: Optional[str]
    current_role: Optional[str]
    target_roles: Optional[list[str]]
    saved_jobs: Optional[int]
    recent_assessments: Optional[int]
    strengths: Optional[list[str]]
    growth_areas: Optional[list[str]]
