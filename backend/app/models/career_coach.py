"""Career coaching models."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, String, Text, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models._mixins import TimestampMixin, UserScopedMixin
from app.schemas.career_coach import CoachingArea, SessionStatus, GoalStatus


class CareerCoaching(Base, TimestampMixin, UserScopedMixin):
    """Career coaching engagement record."""
    __tablename__ = "career_coachings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    coaching_area: Mapped[CoachingArea] = mapped_column(SQLEnum(CoachingArea), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    current_situation: Mapped[str] = mapped_column(Text, nullable=False)
    goals: Mapped[str] = mapped_column(Text, nullable=False)
    challenges: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferred_format: Mapped[str] = mapped_column(String(50), default="async", nullable=False)
    availability_timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    priority_level: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    coach_assigned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    assigned_coach_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    sessions: Mapped[list[CoachingSession]] = relationship("CoachingSession", back_populates="coaching", cascade="all, delete-orphan")
    questions: Mapped[list[CoachQuestion]] = relationship("CoachQuestion", back_populates="coaching", cascade="all, delete-orphan")


class CareerGoal(Base, TimestampMixin, UserScopedMixin):
    """Career goal tracking."""
    __tablename__ = "career_goals"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    goal_title: Mapped[str] = mapped_column(String(255), nullable=False)
    goal_description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[GoalStatus] = mapped_column(SQLEnum(GoalStatus), default=GoalStatus.NOT_STARTED, nullable=False)
    target_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_criteria: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    milestones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON as string
    progress_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    related_coaching_areas: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)


class PersonalizedCareerPlan(Base, TimestampMixin, UserScopedMixin):
    """Personalized career development plan."""
    __tablename__ = "personalized_career_plans"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    timeframe_months: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_strategy: Mapped[str] = mapped_column(Text, nullable=False)
    immediate_actions: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    skill_development_roadmap: Mapped[str] = mapped_column(Text, nullable=False)  # JSON as string
    networking_recommendations: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    learning_resources: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    industry_insights: Mapped[str] = mapped_column(Text, nullable=False)
    market_positioning_strategy: Mapped[str] = mapped_column(Text, nullable=False)
    short_term_goals: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array of goal IDs
    long_term_goals: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array of goal IDs


class SkillAssessment(Base, TimestampMixin, UserScopedMixin):
    """Skill assessment record."""
    __tablename__ = "skill_assessments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    assessed_skill: Mapped[str] = mapped_column(String(255), nullable=False)
    current_level: Mapped[str] = mapped_column(String(50), nullable=False)  # beginner, intermediate, advanced, expert
    target_level: Mapped[str] = mapped_column(String(50), nullable=False)
    proficiency_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-100
    years_of_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    market_demand: Mapped[str] = mapped_column(String(20), nullable=False)  # high, medium, low
    development_recommendations: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    resources: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    estimated_time_to_master: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    target_role: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class InterviewPrepSession(Base, TimestampMixin, UserScopedMixin):
    """Interview preparation session."""
    __tablename__ = "interview_prep_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str] = mapped_column(String(255), nullable=False)
    interview_type: Mapped[str] = mapped_column(String(100), nullable=False)
    interview_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    preparation_progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0-100
    practice_questions: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    key_talking_points: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    common_challenges: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    resources: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    mock_interview_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recommended_next_steps: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    focus_areas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array as string


class CoachingSession(Base, TimestampMixin):
    """One-on-one coaching session."""
    __tablename__ = "coaching_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    coaching_id: Mapped[UUID] = mapped_column(ForeignKey("career_coachings.id"), nullable=False)
    session_status: Mapped[SessionStatus] = mapped_column(SQLEnum(SessionStatus), default=SessionStatus.SCHEDULED, nullable=False)
    scheduled_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    session_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    session_recording_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    action_items: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array as string
    feedback_from_coach: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    session_format: Mapped[str] = mapped_column(String(50), default="call", nullable=False)  # call, chat, video
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    # Relationships
    coaching: Mapped[CareerCoaching] = relationship("CareerCoaching", back_populates="sessions")


class CoachQuestion(Base, TimestampMixin):
    """Questions asked to the coach."""
    __tablename__ = "coach_questions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    coaching_id: Mapped[UUID] = mapped_column(ForeignKey("career_coachings.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    related_coaching_area: Mapped[Optional[CoachingArea]] = mapped_column(SQLEnum(CoachingArea), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actionable_advice: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array as string
    response_resources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array as string
    follow_up_questions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array as string
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    coaching: Mapped[CareerCoaching] = relationship("CareerCoaching", back_populates="questions")


class CoachingProgressReport(Base, TimestampMixin):
    """Progress report on coaching journey."""
    __tablename__ = "coaching_progress_reports"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    coaching_areas_addressed: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    goals_achieved: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    goals_in_progress: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    skills_developed: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    challenges_identified: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    recommendations_for_next_period: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    overall_progress_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-100
    next_focus_areas: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
