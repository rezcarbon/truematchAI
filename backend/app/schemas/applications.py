"""Request and response schemas for job applications."""
from __future__ import annotations

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from pydantic.alias_generators import to_camel
from typing import Optional
from enum import Enum


class ApplicationStatus(str, Enum):
    """Status of a job application."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    VIEWED = "viewed"
    SHORTLISTED = "shortlisted"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    OFFER_RECEIVED = "offer_received"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ApplicationSource(str, Enum):
    """Source of the job application."""
    MANUAL = "manual"
    DIRECT_APPLY = "direct_apply"
    ATS_INTEGRATION = "ats_integration"
    RECRUITER_INVITE = "recruiter_invite"


class InterviewType(str, Enum):
    """Type of interview."""
    PHONE = "phone"
    VIDEO = "video"
    IN_PERSON = "in_person"
    CODING = "coding"
    CASE_STUDY = "case_study"
    PANEL = "panel"
    GROUP = "group"


class SubmitApplicationRequest(BaseModel):
    """Request to submit a job application."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    job_id: str = Field(..., description="Job ID to apply for")
    resume_version_id: UUID = Field(..., description="Resume version to use")
    cover_letter: Optional[str] = Field(None, description="Cover letter text")
    cover_letter_version_id: Optional[UUID] = Field(None, description="Pre-written cover letter")
    custom_answers: Optional[dict] = Field(None, description="Answers to custom questions")
    source: ApplicationSource = Field(ApplicationSource.DIRECT_APPLY)
    agreed_to_terms: bool = Field(True)


class UpdateApplicationRequest(BaseModel):
    """Request to update an application."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: Optional[ApplicationStatus] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None
    follow_up_date: Optional[datetime] = None


class ScheduleInterviewRequest(BaseModel):
    """Request to schedule an interview."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    interview_type: InterviewType
    scheduled_date: datetime
    duration_minutes: int = Field(60, ge=15, le=480)
    interviewer_name: Optional[str] = None
    interviewer_email: Optional[EmailStr] = None
    meeting_link: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    calendar_invite: bool = Field(True, description="Send calendar invite")


class LogInterviewRequest(BaseModel):
    """Request to log a completed interview."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    interview_type: InterviewType
    interview_date: datetime
    interviewer_name: str
    interview_notes: str
    feedback: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    next_steps: Optional[str] = None
    move_to_next_round: bool = Field(False)


class InterviewFeedback(BaseModel):
    """Interview feedback item."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    category: str  # "technical", "communication", "culture_fit", "experience"
    score: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ApplicationResponse(BaseModel):
    """Response for a single application."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    application_id: UUID
    job_id: str
    job_title: str
    company_name: str
    status: ApplicationStatus
    source: ApplicationSource
    resume_version_id: UUID
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    applied_automatically: bool


class ApplicationDetailResponse(BaseModel):
    """Detailed response for an application."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    application_id: UUID
    job_id: str
    job_title: str
    company_name: str
    job_description: Optional[str] = None
    status: ApplicationStatus
    source: ApplicationSource
    resume_version_id: UUID
    cover_letter: Optional[str] = None
    custom_answers: Optional[dict] = None
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None
    tags: Optional[list[str]] = None
    follow_up_date: Optional[datetime] = None
    applied_automatically: bool


class InterviewScheduleResponse(BaseModel):
    """Response for an interview schedule."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    interview_id: UUID
    application_id: UUID
    interview_type: InterviewType
    scheduled_date: datetime
    duration_minutes: int
    interviewer_name: Optional[str] = None
    interviewer_email: Optional[EmailStr] = None
    meeting_link: Optional[str] = None
    location: Optional[str] = None
    status: str  # "scheduled", "completed", "cancelled", "rescheduled"
    notes: Optional[str] = None
    created_at: datetime


class InterviewLogResponse(BaseModel):
    """Response for an interview log."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    interview_id: UUID
    application_id: UUID
    interview_type: InterviewType
    interview_date: datetime
    interviewer_name: str
    interview_notes: str
    feedback: Optional[list[InterviewFeedback]] = None
    overall_rating: Optional[int] = None
    next_steps: Optional[str] = None
    logged_at: datetime


class ApplicationListResponse(BaseModel):
    """List of applications."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    items: list[ApplicationResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ApplicationStatsResponse(BaseModel):
    """Statistics for applications."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    total_applications: int
    by_status: dict  # {"submitted": 5, "shortlisted": 2, "rejected": 1}
    by_source: dict
    this_week: int
    this_month: int
    interview_rate: float  # percentage
    offer_rate: float  # percentage
    average_time_to_response_days: Optional[float] = None
    success_rate: float  # percentage


class BulkApplicationActionRequest(BaseModel):
    """Request for bulk actions on applications."""
    application_ids: list[UUID]
    action: str  # "update_status", "add_tag", "schedule_follow_up", "withdraw"
    status: Optional[ApplicationStatus] = None
    tags: Optional[list[str]] = None
    follow_up_date: Optional[datetime] = None


class WithdrawApplicationRequest(BaseModel):
    """Request to withdraw an application."""
    reason: Optional[str] = None


class RejectionAnalysisResponse(BaseModel):
    """Analysis of why an application was rejected."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    application_id: UUID
    rejection_reason: Optional[str] = None
    skill_gaps: list[str] = []
    experience_gaps: list[str] = []
    resume_improvement_suggestions: list[str] = []
    interview_feedback: Optional[str] = None
    next_steps_recommendation: Optional[str] = None


class ApplicationHistoryItem(BaseModel):
    """Item in application history."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    application_id: UUID
    status: ApplicationStatus
    changed_at: datetime
    changed_by: str  # "system", "recruiter", "user"
    notes: Optional[str] = None


class ApplicationHistoryResponse(BaseModel):
    """Application history."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    application_id: UUID
    history: list[ApplicationHistoryItem]


class SuggestedFollowUpResponse(BaseModel):
    """Suggested follow-up action."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    suggestion: str
    suggested_date: datetime
    template: Optional[str] = None  # Email or message template
    reason: str
