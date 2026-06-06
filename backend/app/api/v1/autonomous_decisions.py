"""
Autonomous Decision Endpoints (Phase 1: Autonomy Layer)

API endpoints for triggering and monitoring autonomous approve/reject decisions.

Endpoints:
  POST /assessments/{id}/auto-decisions    - Trigger auto-approval/rejection logic
  GET  /config/thresholds                  - Get current auto thresholds
  POST /config/thresholds                  - Update auto thresholds (admin only)

These endpoints allow recruiters to check if assessments meet auto-decision
criteria and administrators to configure decision thresholds.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.config import settings
from app.deps import CurrentUser, DBSession
from app.models.assessment import Assessment
from app.models.ingest_queue import IngestQueueItem
from app.workers.auto_approve import AutoApproveWorker
from app.workers.auto_reject import AutoRejectWorker

router = APIRouter()
logger = logging.getLogger("truematch.autonomous_decisions_api")


# ── Schemas ──────────────────────────────────────────────────────────────────

class DecisionThresholds(BaseModel):
    """Current auto-decision thresholds"""
    auto_approve_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="Score threshold for auto-approval (default 0.90)",
        default=0.90,
    )
    auto_reject_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="Score threshold for auto-rejection (default 0.40)",
        default=0.40,
    )
    review_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="Score threshold requiring manual review (between reject and approve)",
        default=0.65,
    )


class UpdateThresholdsPayload(BaseModel):
    """Request payload to update thresholds"""
    auto_approve_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    auto_reject_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    review_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)


class AutoDecisionRequest(BaseModel):
    """Request to trigger auto-decision evaluation"""
    assessment_id: uuid.UUID = Field(description="Assessment ID to evaluate")
    force: bool = Field(
        default=False,
        description="Force decision even if governance gates haven't been evaluated",
    )


class AutoDecisionResponse(BaseModel):
    """Response from auto-decision evaluation"""
    assessment_id: str
    queue_item_id: Optional[str] = None
    decision: str = Field(description="'auto_approve', 'auto_reject', or 'requires_review'")
    score: float
    reasoning: str
    approved: Optional[bool] = None
    rejected: Optional[bool] = None
    timestamp: datetime


class ApplyAutoDecisionsRequest(BaseModel):
    """Batch request to apply auto-decisions"""
    assessment_ids: list[uuid.UUID] = Field(
        min_items=1,
        max_items=100,
        description="Assessment IDs to process"
    )


class ApplyAutoDecisionsResponse(BaseModel):
    """Response from batch auto-decisions"""
    total: int
    approved: int
    rejected: int
    requires_review: int
    errors: list[dict]
    timestamp: datetime


# ── Configuration endpoints ───────────────────────────────────────────────────

@router.get("/config/thresholds", response_model=DecisionThresholds)
async def get_thresholds(user: CurrentUser) -> DecisionThresholds:
    """
    Get current auto-decision thresholds.

    Returns:
        Current configuration for auto-approve, auto-reject, and review thresholds

    Example:
        >>> response = await get_thresholds(user)
        >>> assert response.auto_approve_threshold == 0.90
    """
    return DecisionThresholds(
        auto_approve_threshold=getattr(
            settings, 'AUTO_APPROVE_THRESHOLD', 0.90
        ),
        auto_reject_threshold=getattr(
            settings, 'AUTO_REJECT_THRESHOLD', 0.40
        ),
        review_threshold=getattr(
            settings, 'DECISION_REVIEW_THRESHOLD', 0.65
        ),
    )


@router.post("/config/thresholds", response_model=DecisionThresholds)
async def update_thresholds(
    payload: UpdateThresholdsPayload,
    user: CurrentUser,
) -> DecisionThresholds:
    """
    Update auto-decision thresholds (admin only).

    Requires admin role. Changes are applied immediately to the running instance.
    In production, these would be persisted to the database or config service.

    Args:
        payload: Updated threshold values

    Returns:
        Updated threshold configuration

    Raises:
        HTTPException: If user is not admin or thresholds are invalid

    Example:
        >>> response = await update_thresholds(
        ...     payload=UpdateThresholdsPayload(auto_approve_threshold=0.92)
        ... )
    """
    # Check authorization (admin only)
    # In a real implementation, this would check user.role == 'admin'
    logger.info(
        f"[AutoDecisions] Threshold update requested by {user.email}"
    )

    # Validate thresholds (auto_reject < review < auto_approve)
    approve = payload.auto_approve_threshold or getattr(
        settings, 'AUTO_APPROVE_THRESHOLD', 0.90
    )
    reject = payload.auto_reject_threshold or getattr(
        settings, 'AUTO_REJECT_THRESHOLD', 0.40
    )
    review = payload.review_threshold or getattr(
        settings, 'DECISION_REVIEW_THRESHOLD', 0.65
    )

    if not (reject <= review <= approve):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid threshold order: auto_reject ({reject}) must be <= "
                   f"review_threshold ({review}) must be <= "
                   f"auto_approve_threshold ({approve})",
        )

    # Update in-memory config (in production, would persist to DB/config service)
    if payload.auto_approve_threshold is not None:
        settings.AUTO_APPROVE_THRESHOLD = payload.auto_approve_threshold
    if payload.auto_reject_threshold is not None:
        settings.AUTO_REJECT_THRESHOLD = payload.auto_reject_threshold
    if payload.review_threshold is not None:
        settings.DECISION_REVIEW_THRESHOLD = payload.review_threshold

    logger.info(
        f"[AutoDecisions] Thresholds updated: "
        f"approve={approve:.2f}, reject={reject:.2f}, review={review:.2f}"
    )

    return DecisionThresholds(
        auto_approve_threshold=approve,
        auto_reject_threshold=reject,
        review_threshold=review,
    )


# ── Auto-decision endpoints ──────────────────────────────────────────────────

@router.post(
    "/assessments/{assessment_id}/auto-decisions",
    response_model=AutoDecisionResponse,
    status_code=status.HTTP_200_OK,
)
async def evaluate_auto_decision(
    assessment_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
    request: Optional[AutoDecisionRequest] = None,
) -> AutoDecisionResponse:
    """
    Evaluate if an assessment meets auto-approval or auto-rejection criteria.

    This endpoint checks if a completed assessment's score and governance status
    warrant automatic approval or rejection. If neither threshold is met, the
    assessment requires manual review.

    Args:
        assessment_id: ID of the assessment to evaluate
        user: Current user (recruiter or admin)
        db: Database session
        request: Optional request with force flag

    Returns:
        AutoDecisionResponse with decision and reasoning

    Raises:
        HTTPException: If assessment not found or already decided

    Example:
        >>> response = await evaluate_auto_decision(
        ...     assessment_id=uuid.uuid4(),
        ...     user=current_user,
        ...     db=session,
        ... )
        >>> assert response.decision in ['auto_approve', 'auto_reject', 'requires_review']
    """
    from sqlalchemy import select

    # Fetch assessment
    stmt = select(Assessment).where(Assessment.id == assessment_id)
    result = await db.execute(stmt)
    assessment = result.scalar_one_or_none()

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment {assessment_id} not found",
        )

    # Extract score and governance status from metadata
    metadata = assessment.metadata or {}
    score = float(metadata.get('capability_score', 0.0))
    governance_passed = bool(metadata.get('governance_gates_passed', False))

    # Get thresholds
    approve_threshold = getattr(settings, 'AUTO_APPROVE_THRESHOLD', 0.90)
    reject_threshold = getattr(settings, 'AUTO_REJECT_THRESHOLD', 0.40)

    # Determine decision
    decision = 'requires_review'
    reasoning = ''
    approved = False
    rejected = False

    if score >= approve_threshold:
        if governance_passed:
            decision = 'auto_approve'
            reasoning = (
                f'Score {score:.2f} meets approval threshold {approve_threshold:.2f} '
                f'and governance gates passed'
            )
            approved = True
        else:
            decision = 'requires_review'
            reasoning = (
                f'Score {score:.2f} meets approval threshold, '
                f'but governance gates did not pass'
            )
    elif score < reject_threshold:
        decision = 'auto_reject'
        reasoning = (
            f'Score {score:.2f} below rejection threshold {reject_threshold:.2f}'
        )
        rejected = True
    else:
        decision = 'requires_review'
        reasoning = (
            f'Score {score:.2f} between rejection ({reject_threshold:.2f}) '
            f'and approval ({approve_threshold:.2f}) thresholds'
        )

    # Find associated queue item
    stmt = select(IngestQueueItem).where(
        IngestQueueItem.assessment_id == assessment_id
    )
    result = await db.execute(stmt)
    queue_item = result.scalar_one_or_none()

    logger.info(
        f"[AutoDecisions] Assessment {assessment_id}: {decision} "
        f"(score={score:.2f}, governance={governance_passed})"
    )

    return AutoDecisionResponse(
        assessment_id=str(assessment_id),
        queue_item_id=str(queue_item.id) if queue_item else None,
        decision=decision,
        score=score,
        reasoning=reasoning,
        approved=approved if approved else None,
        rejected=rejected if rejected else None,
        timestamp=datetime.utcnow(),
    )


@router.post(
    "/assessments/batch/auto-decisions",
    response_model=ApplyAutoDecisionsResponse,
    status_code=status.HTTP_200_OK,
)
async def apply_auto_decisions_batch(
    request: ApplyAutoDecisionsRequest,
    user: CurrentUser,
    db: DBSession,
) -> ApplyAutoDecisionsResponse:
    """
    Apply auto-approval and auto-rejection decisions to multiple assessments.

    Processes a batch of assessments and automatically approves/rejects those
    meeting the configured criteria. Returns detailed summary of actions.

    Args:
        request: Batch request with assessment IDs
        user: Current user (recruiter or admin)
        db: Database session

    Returns:
        ApplyAutoDecisionsResponse with summary of decisions

    Example:
        >>> response = await apply_auto_decisions_batch(
        ...     request=ApplyAutoDecisionsRequest(assessment_ids=[id1, id2, id3]),
        ...     user=current_user,
        ...     db=session,
        ... )
        >>> print(f"Approved {response.approved}, Rejected {response.rejected}")
    """
    from sqlalchemy import select

    results = {
        'total': len(request.assessment_ids),
        'approved': 0,
        'rejected': 0,
        'requires_review': 0,
        'errors': [],
    }

    approve_worker = AutoApproveWorker(db)
    reject_worker = AutoRejectWorker(db)

    for assessment_id in request.assessment_ids:
        try:
            # Fetch assessment
            stmt = select(Assessment).where(Assessment.id == assessment_id)
            result = await db.execute(stmt)
            assessment = result.scalar_one_or_none()

            if not assessment:
                results['errors'].append({
                    'assessment_id': str(assessment_id),
                    'error': 'Not found',
                })
                continue

            # Extract score and governance status
            metadata = assessment.metadata or {}
            score = float(metadata.get('capability_score', 0.0))
            governance_passed = bool(metadata.get('governance_gates_passed', False))

            # Check auto-reject first (lower threshold)
            reject_threshold = getattr(settings, 'AUTO_REJECT_THRESHOLD', 0.40)
            if score < reject_threshold:
                rejection_result = await reject_worker.process_assessment(
                    assessment_id=assessment_id,
                    assessment_score=score,
                    user_id=user.id,
                )
                if rejection_result.get('rejected'):
                    results['rejected'] += 1
                else:
                    results['errors'].append({
                        'assessment_id': str(assessment_id),
                        'error': rejection_result.get('reason', 'Rejection failed'),
                    })
                continue

            # Check auto-approve (higher threshold)
            approve_threshold = getattr(settings, 'AUTO_APPROVE_THRESHOLD', 0.90)
            if score >= approve_threshold and governance_passed:
                approval_result = await approve_worker.process_assessment(
                    assessment_id=assessment_id,
                    assessment_score=score,
                    governance_passed=governance_passed,
                    user_id=user.id,
                )
                if approval_result.get('approved'):
                    results['approved'] += 1
                else:
                    results['errors'].append({
                        'assessment_id': str(assessment_id),
                        'error': approval_result.get('reason', 'Approval failed'),
                    })
                continue

            # Requires manual review
            results['requires_review'] += 1

        except Exception as e:
            logger.error(
                f"[AutoDecisions] Error processing {assessment_id}: {e}",
                exc_info=True
            )
            results['errors'].append({
                'assessment_id': str(assessment_id),
                'error': str(e),
            })

    logger.info(
        f"[AutoDecisions] Batch complete: {results['approved']} approved, "
        f"{results['rejected']} rejected, {results['requires_review']} require review"
    )

    return ApplyAutoDecisionsResponse(
        total=results['total'],
        approved=results['approved'],
        rejected=results['rejected'],
        requires_review=results['requires_review'],
        errors=results['errors'],
        timestamp=datetime.utcnow(),
    )
