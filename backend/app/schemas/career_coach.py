"""Request and response schemas for career coaching."""
from __future__ import annotations

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional
from enum import Enum


class CoachingArea(str, Enum):
    """Areas of career coaching."""
    SKILL_DEVELOPMENT = "skill_development"
    CAREER_TRANSITION = "career_transition"
    INTERVIEW_PREP = "interview_prep"
    SALARY_NEGOTIATION = "salary_negotiation"
    LEADERSHIP = "leadership"
    WORK_LIFE_BALANCE = "work_life_balance"
    NETWORKING = "networking"
    EXECUTIVE_PRESENCE = "executive_presence"
    PERSONAL_BRANDING = "personal_branding"


class SessionStatus(str, Enum):
    """Status of a coaching session."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class GoalStatus(str, Enum):
    """Status of a career goal."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    COMPLETED = "completed"
    PAUSED = "paused"


class RequestCareerCoachingRequest(BaseModel):
    """Request to start career coaching."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    coaching_area: CoachingArea = Field(..., description="Area of coaching needed")
    current_situation: str = Field(..., min_length=10, description="Describe your current situation")
    goals: str = Field(..., min_length=10, description="What do you want to achieve?")
    challenges: Optional[str] = Field(None, description="What are your main challenges?")
    preferred_format: str = Field("async", description="async, scheduled_call, or both")
    availability_timezone: Optional[str] = None
    priority_level: str = Field("medium", description="low, medium, high")


class CareerGoalRequest(BaseModel):
    """Request to set a career goal."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    goal_title: str = Field(..., min_length=1, max_length=255)
    goal_description: str = Field(..., description="Detailed description of the goal")
    target_date: datetime = Field(..., description="When do you want to achieve this?")
    related_coaching_areas: list[CoachingArea] = Field(..., description="Related coaching areas")
    success_criteria: list[str] = Field(..., description="How will you measure success?")
    milestones: Optional[list[dict]] = Field(None, description="Key milestones")
    priority: str = Field("medium", description="low, medium, high")


class UpdateCareerGoalRequest(BaseModel):
    """Request to update a career goal."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    goal_title: Optional[str] = None
    goal_description: Optional[str] = None
    target_date: Optional[datetime] = None
    status: Optional[GoalStatus] = None
    success_criteria: Optional[list[str]] = None
    milestones: Optional[list[dict]] = None
    progress_notes: Optional[str] = None


class PersonalizedPlanRequest(BaseModel):
    """Request for a personalized career plan."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    timeframe_months: int = Field(..., ge=1, le=60, description="Planning timeframe in months")
    career_goals: list[str] = Field(..., description="Your career goals")
    current_skills: list[str] = Field(..., description="Your current skills")
    target_roles: list[str] = Field(..., description="Target roles")
    industries: Optional[list[str]] = Field(None, description="Target industries")
    constraints: Optional[list[str]] = Field(None, description="Any constraints or limitations")


class SkillAssessmentRequest(BaseModel):
    """Request for skill assessment."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    skills_to_assess: list[str] = Field(..., description="Skills to assess")
    target_role: Optional[str] = None
    self_assessed_levels: Optional[dict] = None  # {"python": "intermediate", "sql": "beginner"}


class InterviewPrepSessionRequest(BaseModel):
    """Request for interview preparation session."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    company: str = Field(..., description="Company name")
    position: str = Field(..., description="Position title")
    interview_type: str = Field(..., description="Phone, video, technical, etc.")
    interview_date: Optional[datetime] = None
    focus_areas: Optional[list[str]] = Field(None, description="Areas to focus on")
    common_questions: Optional[list[str]] = Field(None, description="Specific questions to practice")


class CareerCoachingResponse(BaseModel):
    """Response for career coaching request."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    coaching_id: UUID
    coaching_area: CoachingArea
    status: str  # "pending", "active", "paused", "completed"
    created_at: datetime
    updated_at: datetime
    coach_assigned: bool
    next_step: Optional[str] = None


class CareerGoalResponse(BaseModel):
    """Response for a career goal."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    goal_id: UUID
    goal_title: str
    goal_description: str
    status: GoalStatus
    target_date: datetime
    progress_percentage: int = Field(..., ge=0, le=100)
    related_coaching_areas: list[CoachingArea]
    created_at: datetime
    updated_at: datetime
    completion_date: Optional[datetime] = None


class CareerGoalListResponse(BaseModel):
    """List of career goals."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    items: list[CareerGoalResponse]
    total: int
    page: int
    page_size: int
    pages: int


class PersonalizedCareerPlan(BaseModel):
    """Personalized career development plan."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    plan_id: UUID
    timeframe_months: int
    overall_strategy: str
    immediate_actions: list[str]
    short_term_goals: list[CareerGoalResponse]
    long_term_goals: list[CareerGoalResponse]
    skill_development_roadmap: dict  # Skills to develop and timeline
    networking_recommendations: list[str]
    learning_resources: list[dict]  # {"title": "...", "type": "course/book/podcast", "url": "..."}
    industry_insights: str
    market_positioning_strategy: str
    created_at: datetime
    updated_at: datetime


class SkillAssessmentResult(BaseModel):
    """Result of skill assessment."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    assessment_id: UUID
    assessed_skill: str
    current_level: str  # "beginner", "intermediate", "advanced", "expert"
    target_level: str
    proficiency_score: int = Field(..., ge=0, le=100)
    years_of_experience: Optional[int] = None
    market_demand: str  # "high", "medium", "low"
    development_recommendations: list[str]
    resources: list[dict]  # {"type": "course", "title": "...", "url": "..."}
    estimated_time_to_master: Optional[str] = None  # e.g., "3-6 months"


class SkillAssessmentListResponse(BaseModel):
    """List of skill assessments."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    items: list[SkillAssessmentResult]
    total: int
    strengths: list[str]
    gaps: list[str]
    recommended_focus_areas: list[str]


class CoachingSessionResponse(BaseModel):
    """Response for a coaching session."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    session_id: UUID
    coaching_id: UUID
    coaching_area: CoachingArea
    status: SessionStatus
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    session_notes: Optional[str] = None
    session_recording_url: Optional[str] = None
    action_items: Optional[list[str]] = None
    feedback_from_coach: Optional[str] = None
    session_format: str  # "call", "chat", "video"


class InterviewPrepSessionResponse(BaseModel):
    """Response for interview prep session."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    session_id: UUID
    company: str
    position: str
    interview_type: str
    interview_date: Optional[datetime] = None
    preparation_progress: int = Field(..., ge=0, le=100, description="Percentage of prep completed")
    practice_questions: list[str]
    key_talking_points: list[str]
    common_challenges: list[str]
    resources: list[dict]
    mock_interview_available: bool
    recommended_next_steps: list[str]
    created_at: datetime
    updated_at: datetime


class AskCoachQuestion(BaseModel):
    """Request to ask coach a question."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    question: str = Field(..., min_length=10, description="Your question")
    context: Optional[str] = Field(None, description="Additional context")
    related_coaching_area: Optional[CoachingArea] = None
    priority: str = Field("medium", description="low, medium, high")


class CoachResponse(BaseModel):
    """Coach's response to a question."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    response_id: UUID
    question_id: UUID
    response: str
    actionable_advice: list[str]
    resources: Optional[list[dict]] = None
    follow_up_questions: Optional[list[str]] = None
    responded_at: datetime


class CoachingProgressReport(BaseModel):
    """Progress report on coaching journey."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    report_id: UUID
    period_start: datetime
    period_end: datetime
    coaching_areas_addressed: list[CoachingArea]
    goals_achieved: list[str]
    goals_in_progress: list[str]
    skills_developed: list[str]
    challenges_identified: list[str]
    recommendations_for_next_period: list[str]
    overall_progress_score: int = Field(..., ge=0, le=100)
    next_focus_areas: list[CoachingArea]
    generated_at: datetime


class ScheduleCoachingSessionRequest(BaseModel):
    """Request to schedule a coaching session."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    coaching_id: UUID
    session_date: datetime
    duration_minutes: int = Field(60, ge=30, le=120)
    session_format: str  # "call", "video", "chat"
    topic: Optional[str] = None
    preparation_notes: Optional[str] = None
