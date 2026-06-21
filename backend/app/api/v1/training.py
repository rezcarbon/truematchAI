"""Training Simulation System API endpoints for virtual brain management.

This module provides admin-only endpoints to:
- Submit training feedback (recruiter/candidate actions)
- View training progress metrics
- Get insights from learned patterns
- Manage capability/credential mappings
- Monitor virtual brain intelligence

Admin-only access required for all endpoints.
"""
import logging
from app.core.clock import utcnow
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session, get_current_user
from app.models import User, UserRole
from app.models.training import (
    TrainingFeedback,
    CapabilityMapping,
    CredentialMapping,
    SuccessPattern,
    TrainingProgress,
    TrainingInsight,
    VirtualBrainState,
)
from app.schemas.training import (
    TrainingFeedbackCreate,
    TrainingFeedbackResponse,
    CapabilityMappingResponse,
    CredentialMappingResponse,
    SuccessPatternResponse,
    TrainingProgressResponse,
    TrainingInsightResponse,
    VirtualBrainStateResponse,
    TrainingStatsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/training", tags=["training"])


async def verify_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verify user is admin. All training endpoints require admin access."""
    if current_user.role != UserRole.admin:
        logger.warning(
            f"Non-admin user {current_user.id} attempted to access training endpoints"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for training system",
        )
    return current_user


# ============================================================================
# FEEDBACK ENDPOINTS - For collecting training data
# ============================================================================


@router.post(
    "/feedback",
    response_model=TrainingFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit training feedback (recruiter/candidate action)",
)
async def submit_training_feedback(
    feedback: TrainingFeedbackCreate,
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> TrainingFeedback:
    """
    Submit training feedback to the virtual brain.

    The system learns from every recruiter hiring decision and candidate action:
    - Recruiter hires a candidate → "hire" feedback
    - Recruiter rejects a candidate → "reject" feedback
    - Candidate applies to a job → "applied" feedback
    - Candidate skips a job → "not_interested" feedback

    This feedback trains the virtual brain to improve future matches.

    Args:
        feedback: TrainingFeedbackCreate - The feedback data

    Returns:
        TrainingFeedback: Created feedback record with ID

    Access: Admin only (can submit on behalf of recruiters/candidates)
    """
    training_feedback = TrainingFeedback(
        user_id=feedback.user_id,
        match_id=feedback.match_id,
        job_id=feedback.job_id,
        candidate_id=feedback.candidate_id,
        feedback_type=feedback.feedback_type,
        rating=feedback.rating,
        comments=feedback.comments,
        time_to_action_seconds=feedback.time_to_action_seconds,
        source=feedback.source or "web",
    )

    db.add(training_feedback)
    await db.commit()
    await db.refresh(training_feedback)

    logger.info(
        f"Training feedback submitted: {feedback.feedback_type}",
        extra={
            "feedback_id": str(training_feedback.id),
            "user_id": str(feedback.user_id),
            "type": feedback.feedback_type,
            "admin_id": str(admin.id),
        },
    )

    return training_feedback


@router.get(
    "/feedback",
    response_model=List[TrainingFeedbackResponse],
    summary="Get recent training feedback",
)
async def get_training_feedback(
    limit: int = 100,
    feedback_type: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> List[TrainingFeedback]:
    """
    Get recent training feedback records.

    Returns the most recent feedback submissions that train the virtual brain.

    Args:
        limit: Max number of feedback records to return
        feedback_type: Filter by feedback type (hire, reject, applied, etc)

    Returns:
        List of TrainingFeedback records

    Access: Admin only
    """
    query = select(TrainingFeedback)

    if feedback_type:
        query = query.where(TrainingFeedback.feedback_type == feedback_type)

    query = query.order_by(desc(TrainingFeedback.created_at)).limit(limit)

    result = await db.execute(query)
    feedback_records = result.scalars().all()

    logger.info(
        f"Retrieved {len(feedback_records)} training feedback records",
        extra={"admin_id": str(admin.id), "type": feedback_type},
    )

    return feedback_records


@router.patch(
    "/feedback/{feedback_id}/outcome",
    response_model=TrainingFeedbackResponse,
    summary="Update feedback outcome (hired/success tracking)",
)
async def update_feedback_outcome(
    feedback_id: UUID,
    outcome: str,  # "hired", "rejected", "pending"
    hire_success: Optional[bool] = None,  # Was the hire successful after 6mo?
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> TrainingFeedback:
    """
    Update feedback outcome after hiring decision is finalized.

    Used to track long-term success of hires:
    - After 6 months: Was this hire successful? (hire_success=True/False)
    - Helps train success prediction model

    Args:
        feedback_id: ID of feedback to update
        outcome: "hired", "rejected", or "pending"
        hire_success: Whether the hire lasted 6+ months

    Returns:
        Updated TrainingFeedback

    Access: Admin only
    """
    result = await db.execute(
        select(TrainingFeedback).where(TrainingFeedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    feedback.outcome = outcome
    feedback.outcome_date = utcnow()
    if hire_success is not None:
        feedback.hire_success = hire_success

    await db.commit()
    await db.refresh(feedback)

    logger.info(
        f"Updated feedback outcome: {outcome}",
        extra={
            "feedback_id": str(feedback_id),
            "hire_success": hire_success,
            "admin_id": str(admin.id),
        },
    )

    return feedback


# ============================================================================
# CAPABILITY & CREDENTIAL MAPPING ENDPOINTS - For virtual brain knowledge
# ============================================================================


@router.get(
    "/capabilities",
    response_model=List[CapabilityMappingResponse],
    summary="Get learned capability mappings",
)
async def get_capability_mappings(
    limit: int = 100,
    min_confidence: float = 0.0,
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> List[CapabilityMapping]:
    """
    Get learned capability mappings from the virtual brain.

    Shows what the system has learned about CV keywords and their
    corresponding capabilities.

    Example:
    - CV Keyword: "Led team of engineers"
    - Capability: "Leadership"
    - Confidence: 0.92
    - Learned From: 87 successful matches

    Args:
        limit: Max mappings to return
        min_confidence: Only show mappings above this confidence (0-1)

    Returns:
        List of CapabilityMapping records

    Access: Admin only
    """
    query = (
        select(CapabilityMapping)
        .where(CapabilityMapping.confidence_score >= min_confidence)
        .order_by(desc(CapabilityMapping.confidence_score))
        .limit(limit)
    )

    result = await db.execute(query)
    mappings = result.scalars().all()

    logger.info(
        f"Retrieved {len(mappings)} capability mappings",
        extra={
            "admin_id": str(admin.id),
            "min_confidence": min_confidence,
        },
    )

    return mappings


@router.post(
    "/capabilities",
    response_model=CapabilityMappingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add/validate capability mapping",
)
async def create_capability_mapping(
    keyword: str,
    capability: str,
    is_correct: bool = True,
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> CapabilityMapping:
    """
    Add a new capability mapping or validate an existing one.

    Admin can provide feedback on capability mappings to improve
    the virtual brain's understanding.

    Args:
        keyword: CV keyword/phrase
        capability: Corresponding capability name
        is_correct: Whether this mapping is correct

    Returns:
        CapabilityMapping record

    Access: Admin only
    """
    # Check if mapping already exists
    result = await db.execute(
        select(CapabilityMapping).where(
            and_(
                CapabilityMapping.cv_keyword == keyword,
                CapabilityMapping.capability == capability,
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update confidence based on feedback
        if is_correct:
            existing.positive_feedback += 1
        else:
            existing.negative_feedback += 1

        # Recalculate confidence
        total = existing.positive_feedback + existing.negative_feedback
        existing.confidence_score = (
            existing.positive_feedback / total if total > 0 else 0.5
        )

        await db.commit()
        await db.refresh(existing)
        return existing

    # Create new mapping
    mapping = CapabilityMapping(
        cv_keyword=keyword,
        capability=capability,
        confidence_score=0.8 if is_correct else 0.2,
        positive_feedback=1 if is_correct else 0,
        negative_feedback=0 if is_correct else 1,
        is_user_added=True,
    )

    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)

    logger.info(
        f"Created capability mapping: {keyword} → {capability}",
        extra={"admin_id": str(admin.id), "is_correct": is_correct},
    )

    return mapping


@router.get(
    "/credentials",
    response_model=List[CredentialMappingResponse],
    summary="Get learned credential mappings",
)
async def get_credential_mappings(
    limit: int = 100,
    min_score: float = 0.0,
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> List[CredentialMapping]:
    """
    Get learned credential mappings from the virtual brain.

    Shows what the system has learned about credential-to-requirement matches.

    Example:
    - Credential: "BS Computer Science"
    - Requirement: "Bachelor's degree in CS or related field"
    - Match Score: 0.95
    - Learned From: 143 successful matches

    Args:
        limit: Max mappings to return
        min_score: Only show mappings above this score (0-1)

    Returns:
        List of CredentialMapping records

    Access: Admin only
    """
    query = (
        select(CredentialMapping)
        .where(CredentialMapping.match_score >= min_score)
        .order_by(desc(CredentialMapping.match_score))
        .limit(limit)
    )

    result = await db.execute(query)
    mappings = result.scalars().all()

    logger.info(
        f"Retrieved {len(mappings)} credential mappings",
        extra={"admin_id": str(admin.id), "min_score": min_score},
    )

    return mappings


# ============================================================================
# SUCCESS PATTERN ENDPOINTS - For prediction models
# ============================================================================


@router.get(
    "/success-patterns",
    response_model=List[SuccessPatternResponse],
    summary="Get learned success patterns",
)
async def get_success_patterns(
    limit: int = 50,
    min_sample_size: int = 5,
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> List[SuccessPattern]:
    """
    Get learned success patterns for job types.

    The virtual brain learns what makes successful hires for each job type:
    - Which capabilities matter most
    - Which credentials are required
    - What's the success rate
    - Who succeeds longest

    Args:
        limit: Max patterns to return
        min_sample_size: Only show patterns with this many hire examples

    Returns:
        List of SuccessPattern records

    Access: Admin only
    """
    query = (
        select(SuccessPattern)
        .where(SuccessPattern.sample_size >= min_sample_size)
        .order_by(desc(SuccessPattern.success_rate))
        .limit(limit)
    )

    result = await db.execute(query)
    patterns = result.scalars().all()

    logger.info(
        f"Retrieved {len(patterns)} success patterns",
        extra={"admin_id": str(admin.id)},
    )

    return patterns


# ============================================================================
# TRAINING PROGRESS & INSIGHTS ENDPOINTS
# ============================================================================


@router.get(
    "/progress",
    response_model=List[TrainingProgressResponse],
    summary="Get virtual brain training progress",
)
async def get_training_progress(
    metric_name: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> List[TrainingProgress]:
    """
    Get training progress metrics showing how smart the virtual brain is.

    Metrics tracked:
    - match_accuracy: % of matches that lead to hire
    - hire_success_rate: % of hires retained 6+ months
    - user_satisfaction: Average rating of matches
    - prediction_confidence: How confident are we in predictions

    Args:
        metric_name: Filter by specific metric
        limit: Max records to return

    Returns:
        List of TrainingProgress records

    Access: Admin only
    """
    query = select(TrainingProgress)

    if metric_name:
        query = query.where(TrainingProgress.metric_name == metric_name)

    query = query.order_by(desc(TrainingProgress.created_at)).limit(limit)

    result = await db.execute(query)
    progress = result.scalars().all()

    logger.info(
        f"Retrieved {len(progress)} progress metrics",
        extra={"admin_id": str(admin.id), "metric": metric_name},
    )

    return progress


@router.get(
    "/insights",
    response_model=List[TrainingInsightResponse],
    summary="Get insights from virtual brain learnings",
)
async def get_training_insights(
    insight_type: Optional[str] = None,
    is_trending: bool = False,
    limit: int = 50,
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> List[TrainingInsight]:
    """
    Get generated insights from what the virtual brain has learned.

    Example insights:
    - "Python is the most requested skill (127 open positions)"
    - "Full-stack engineers have 94% success rate"
    - "Candidates from top 10 universities average 18-month tenure"
    - "Companies in tech hubs prefer distributed-system experience"

    Args:
        insight_type: Filter by type (skill_demand, success_factor, trend, etc)
        is_trending: Only show trending insights
        limit: Max insights to return

    Returns:
        List of TrainingInsight records

    Access: Admin only
    """
    query = select(TrainingInsight).where(TrainingInsight.is_public.is_(True))

    if insight_type:
        query = query.where(TrainingInsight.insight_type == insight_type)

    if is_trending:
        query = query.where(TrainingInsight.is_trending.is_(True))

    query = query.order_by(desc(TrainingInsight.created_at)).limit(limit)

    result = await db.execute(query)
    insights = result.scalars().all()

    logger.info(
        f"Retrieved {len(insights)} insights",
        extra={
            "admin_id": str(admin.id),
            "type": insight_type,
            "trending": is_trending,
        },
    )

    return insights


# ============================================================================
# VIRTUAL BRAIN STATE ENDPOINTS - For monitoring system health
# ============================================================================


@router.get(
    "/brain/state",
    response_model=VirtualBrainStateResponse,
    summary="Get current virtual brain state",
)
async def get_virtual_brain_state(
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> VirtualBrainStateResponse:
    """
    Get the current state of the virtual brain.

    Shows:
    - Current model version
    - Total training samples received
    - Patterns learned
    - Match accuracy
    - Hire success prediction accuracy
    - Model health metrics

    Args: None

    Returns:
        Current VirtualBrainState

    Access: Admin only
    """
    result = await db.execute(
        select(VirtualBrainState)
        .where(VirtualBrainState.is_active.is_(True))
        .order_by(desc(VirtualBrainState.created_at))
    )
    state = result.scalar_one_or_none()

    if not state:
        # Return empty state if no model yet
        import uuid
        from datetime import datetime, timezone
        return VirtualBrainStateResponse(
            id=uuid.uuid4(),
            version=0,
            is_active=False,
            total_feedback_samples=0,
            total_patterns_learned=0,
            match_accuracy=0.0,
            hire_success_prediction_accuracy=0.0,
            model_data={},
            performance_metrics={},
            training_started_at=None,
            training_completed_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            notes="Initial model state - no training data yet",
        )

    logger.info(
        f"Retrieved virtual brain state v{state.version}",
        extra={
            "admin_id": str(admin.id),
            "version": state.version,
            "accuracy": state.match_accuracy,
        },
    )

    return VirtualBrainStateResponse.model_validate(state)


@router.get(
    "/stats",
    response_model=TrainingStatsResponse,
    summary="Get comprehensive training statistics",
)
async def get_training_stats(
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> dict:
    """
    Get comprehensive statistics on virtual brain training.

    Returns:
    - Total feedback samples
    - Feedback breakdown by type
    - Mappings learned (capabilities, credentials)
    - Success patterns discovered
    - Current model accuracy
    - Learning trends

    Args: None

    Returns:
        TrainingStatsResponse with all metrics

    Access: Admin only
    """
    # Count feedback by type
    result = await db.execute(select(TrainingFeedback))
    feedback_records = result.scalars().all()
    total_feedback = len(feedback_records)

    feedback_by_type = {}
    for record in feedback_records:
        feedback_by_type[record.feedback_type] = (
            feedback_by_type.get(record.feedback_type, 0) + 1
        )

    # Count mappings
    result = await db.execute(select(CapabilityMapping))
    capabilities = len(result.scalars().all())

    result = await db.execute(select(CredentialMapping))
    credentials = len(result.scalars().all())

    # Count patterns
    result = await db.execute(select(SuccessPattern))
    patterns = len(result.scalars().all())

    # Get current brain state
    result = await db.execute(
        select(VirtualBrainState).where(VirtualBrainState.is_active.is_(True))
    )
    brain_state = result.scalar_one_or_none()

    stats = {
        "total_feedback": total_feedback,
        "feedback_by_type": feedback_by_type,
        "capability_mappings_learned": capabilities,
        "credential_mappings_learned": credentials,
        "success_patterns_discovered": patterns,
        "current_model": {
            "version": brain_state.version if brain_state else 0,
            "match_accuracy": brain_state.match_accuracy if brain_state else 0.0,
            "hire_success_accuracy": (
                brain_state.hire_success_prediction_accuracy if brain_state else 0.0
            ),
            "total_patterns": brain_state.total_patterns_learned if brain_state else 0,
        },
    }

    logger.info(
        "Retrieved training statistics",
        extra={
            "admin_id": str(admin.id),
            "total_feedback": total_feedback,
            "patterns": patterns,
        },
    )

    return stats
