"""Learning feedback collection endpoints.

Recruiters record hiring outcomes and performance data for learning system.
Endpoints:
- POST /learning/assessment/{assessment_id}/outcome: Record hiring outcome
- GET /learning/assessment/{assessment_id}/feedback-status: Check feedback status
- GET /learning/metrics/today: Get today's learning metrics
"""
from __future__ import annotations

import logging
import uuid
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.clock import utcnow
from app.core.exceptions import AuthorizationError, NotFoundError
from app.deps import CurrentUser, DBSession
from app.models.assessment import Assessment, DecisionType
from app.models.hiring_outcome import HiringDecision, HiringOutcome, PerformanceRating
from app.models.learning_metrics import AssessmentMetrics
from app.models.position import Position
from app.models.user import UserRole

logger = logging.getLogger("truematch.learning_feedback")

router = APIRouter(prefix="/api/v1/learning", tags=["learning"])


class PerformanceDataRequest(BaseModel):
    """Performance data for hired candidate."""

    days_employed: Optional[int] = Field(None, description="Total days employed")
    ramp_up_days: Optional[int] = Field(
        None, description="Days to full productivity"
    )
    skill_utilization: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="% of roles requiring assessed skills",
    )
    interview_stage: Optional[str] = Field(
        None, description="phone, technical, final, offer, etc."
    )
    interview_score: Optional[float] = Field(
        None, ge=0, le=100, description="Quantified interview score"
    )
    peer_feedback_rating: Optional[float] = Field(
        None, ge=0, le=5, description="Peer feedback (0-5 stars)"
    )
    manager_feedback_rating: Optional[float] = Field(
        None, ge=0, le=5, description="Manager feedback (0-5 stars)"
    )
    retention_days: Optional[int] = Field(
        None, description="Days before voluntary exit (if terminated)"
    )
    internal_mobility: Optional[str] = Field(None, description="Moved to different role?")
    skill_match_accuracy: Optional[float] = Field(
        None, ge=0, le=100, description="Did they actually have assessed skills?"
    )


class RecordOutcomeRequest(BaseModel):
    """Request to record hiring outcome for an assessment."""

    outcome: str = Field(
        ..., description="hired, not_hired, offer_declined, withdrawn, pending"
    )
    outcome_reason: str = Field(
        ..., description="Why this outcome (e.g., 'Strong technical fit')"
    )
    performance_data: Optional[PerformanceDataRequest] = Field(
        None, description="Performance data if hired"
    )
    interviewer_notes: Optional[str] = Field(
        None, description="Interviewer observations"
    )
    hiring_manager_rating: Optional[float] = Field(
        None, ge=0, le=5, description="Hiring manager rating (0-5)"
    )
    unexpected_outcome: Optional[str] = Field(
        None, description="If outcome contradicted prediction"
    )
    counter_rec_used: Optional[bool] = Field(None, description="Was counter-rec used?")
    counter_rec_outcome: Optional[str] = Field(None, description="Did counter-rec help?")
    substitution_valid: Optional[bool] = Field(
        None, description="Was credential substitution valid?"
    )
    substitution_notes: Optional[str] = Field(
        None, description="Notes on substitution validity"
    )


class OutcomeResponse(BaseModel):
    """Response after recording outcome."""

    id: uuid.UUID
    assessment_id: uuid.UUID
    recorded_at: datetime
    outcome: str


class FeedbackStatusResponse(BaseModel):
    """Status of feedback for an assessment."""

    assessment_id: uuid.UUID
    has_feedback: bool
    recorded_at: Optional[datetime] = None
    outcome: Optional[str] = None


class MetricsResponse(BaseModel):
    """Today's learning metrics."""

    metric_date: date
    total_assessments: int
    assessments_with_outcome: int
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    false_positive_rate: Optional[float] = None
    false_negative_rate: Optional[float] = None
    avg_confidence: Optional[float] = None
    expected_calibration_error: Optional[float] = None


@router.post("/assessment/{assessment_id}/outcome", response_model=OutcomeResponse)
async def record_hiring_outcome(
    assessment_id: uuid.UUID,
    feedback: RecordOutcomeRequest,
    user: CurrentUser,
    db: DBSession,
) -> OutcomeResponse:
    """
    Record hiring outcome for an assessment.

    Only recruiters and admins can record outcomes.
    Triggers nightly learning job when sufficient data accumulated.

    Args:
        assessment_id: UUID of assessment
        feedback: Hiring outcome and performance data
        user: Current authenticated user (must be recruiter)
        db: Database session

    Returns:
        Stored outcome record

    Raises:
        NotFoundError: Assessment not found
        AuthorizationError: User not authorized
        ValueError: Invalid outcome type
    """
    # Authorization: only recruiters and admins
    if user.role not in (UserRole.recruiter, UserRole.admin):
        raise AuthorizationError(
            "Only recruiters and admins can record hiring outcomes"
        )

    # Get assessment
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise NotFoundError("Assessment not found")

    # Check recruiter has access to position's company
    position = await db.get(Position, assessment.position_id)
    if not position:
        raise NotFoundError("Position not found")

    if (
        position.company_id != user.company_id
        and user.role != UserRole.admin
    ):
        raise AuthorizationError(
            "You don't have access to this position's company"
        )

    # Validate outcome
    try:
        decision = HiringDecision(feedback.outcome)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid outcome. Must be one of: {[e.value for e in HiringDecision]}",
        )

    # Check if outcome already exists for this assessment
    stmt = select(HiringOutcome).where(
        HiringOutcome.position_id == assessment.position_id
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing and existing.hiring_decision != HiringDecision.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Outcome already recorded for this assessment",
        )

    # Determine if hired
    hired = decision in (HiringDecision.hired, HiringDecision.offer_declined)

    # Create or update HiringOutcome
    if existing:
        outcome = existing
    else:
        outcome = HiringOutcome(
            position_id=assessment.position_id,
            candidate_id=assessment.user_id,
            candidate_match_id=uuid.uuid4(),  # Placeholder
        )
        db.add(outcome)

    # Update outcome fields
    outcome.hiring_decision = decision
    outcome.decision_made_at = utcnow()
    outcome.decision_rationale = feedback.outcome_reason
    outcome.hired = hired

    # Performance data
    if feedback.performance_data:
        perf_data = feedback.performance_data.model_dump(exclude_none=True)
        outcome.performance_details = perf_data

        if feedback.performance_data.days_employed:
            outcome.tenure_days = feedback.performance_data.days_employed

    # Optional fields
    if feedback.hiring_manager_rating:
        outcome.performance_rating = _rating_to_enum(
            feedback.hiring_manager_rating
        )
    outcome.recruiter_notes = feedback.interviewer_notes

    # Learning feedback
    learning_feedback = {
        "counter_rec_used": feedback.counter_rec_used,
        "counter_rec_outcome": feedback.counter_rec_outcome,
        "substitution_valid": feedback.substitution_valid,
        "unexpected_outcome": feedback.unexpected_outcome,
    }
    outcome.learning_feedback = learning_feedback

    outcome.updated_at = utcnow()

    await db.flush()

    logger.info(
        f"Recorded outcome for assessment {assessment_id}: "
        f"decision={decision.value}, "
        f"performance_rating={outcome.performance_rating}"
    )

    return OutcomeResponse(
        id=outcome.id,
        assessment_id=assessment_id,
        recorded_at=outcome.updated_at,
        outcome=decision.value,
    )


@router.get("/assessment/{assessment_id}/feedback-status", response_model=FeedbackStatusResponse)
async def get_feedback_status(
    assessment_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> FeedbackStatusResponse:
    """
    Check if hiring outcome feedback exists for an assessment.

    Args:
        assessment_id: UUID of assessment
        user: Current user
        db: Database session

    Returns:
        Feedback status (has_feedback, outcome, recorded_at)

    Raises:
        NotFoundError: Assessment not found
        AuthorizationError: User not authorized
    """
    # Get assessment
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise NotFoundError("Assessment not found")

    # Authorization: candidate can see own, recruiter/admin can see all
    if (
        user.role.value == "candidate"
        and assessment.user_id != user.id
    ):
        raise AuthorizationError("You can only view your own assessments")

    # Get outcome
    stmt = select(HiringOutcome).where(
        HiringOutcome.position_id == assessment.position_id
    )
    result = await db.execute(stmt)
    outcome = result.scalar_one_or_none()

    return FeedbackStatusResponse(
        assessment_id=assessment_id,
        has_feedback=outcome is not None
        and outcome.hiring_decision != HiringDecision.pending,
        recorded_at=outcome.updated_at if outcome else None,
        outcome=outcome.hiring_decision.value if outcome else None,
    )


@router.get("/metrics/today", response_model=Optional[MetricsResponse])
async def get_today_metrics(
    user: CurrentUser,
    db: DBSession,
) -> Optional[MetricsResponse]:
    """
    Get today's learning metrics (for dashboards).

    Available to all authenticated users.

    Args:
        user: Current user
        db: Database session

    Returns:
        Today's metrics if computed, None otherwise
    """
    from datetime import date as date_class

    today = date_class.today()

    stmt = select(AssessmentMetrics).where(
        AssessmentMetrics.metric_date == today
    )
    result = await db.execute(stmt)
    metrics = result.scalar_one_or_none()

    if not metrics:
        return None

    return MetricsResponse(
        metric_date=metrics.metric_date,
        total_assessments=metrics.total_assessments,
        assessments_with_outcome=metrics.assessments_with_outcome,
        accuracy=metrics.accuracy,
        precision=metrics.precision,
        recall=metrics.recall,
        f1_score=metrics.f1_score,
        false_positive_rate=metrics.false_positive_rate,
        false_negative_rate=metrics.false_negative_rate,
        avg_confidence=metrics.avg_confidence,
        expected_calibration_error=metrics.expected_calibration_error,
    )


def _rating_to_enum(rating: float) -> PerformanceRating:
    """Convert numeric rating to performance rating enum."""
    if rating >= 4.0:
        return PerformanceRating.exceeding
    elif rating >= 3.0:
        return PerformanceRating.meeting
    elif rating >= 2.0:
        return PerformanceRating.developing
    else:
        return PerformanceRating.underperforming


__all__ = [
    "router",
    "RecordOutcomeRequest",
    "OutcomeResponse",
    "FeedbackStatusResponse",
    "MetricsResponse",
]
