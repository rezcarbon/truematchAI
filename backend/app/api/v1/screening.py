"""Screening API - Phase 1 Batch Candidate Screening Endpoints.

Endpoints for:
1. Initiating bulk screening batches
2. Monitoring batch progress
3. Recruiter review of screening results
4. Recording recruiter decisions
5. Analytics and metrics

All endpoints require authentication (recruiter role).
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User, UserRole
from app.schemas.screening import (
    ScreeningBatchCreateRequest,
    ScreeningBatchResponse,
    ScreeningBatchStatusResponse,
    ScreeningResultDetailResponse,
    ScreeningBatchPendingResponse,
    ScreeningResultSummaryCard,
    ScreeningDecisionRequest,
    ScreeningDecisionResponse,
    ScreeningBulkDecisionRequest,
    ScreeningBulkDecisionResponse,
    ScreeningBatchMetricsResponse,
)
from app.services.screening_service import ScreeningService
from app.workers.screening_queue import process_screening_batch

logger = logging.getLogger("truematch.screening_api")

router = APIRouter(prefix="/api/v1/screenings", tags=["screening"])


def require_recruiter(user: User = Depends(get_current_user)) -> User:
    """Dependency: Require recruiter role."""
    if user.role not in (UserRole.recruiter, UserRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can access screening endpoints",
        )
    return user


# ============================================================================
# BATCH MANAGEMENT
# ============================================================================


@router.post(
    "/batches",
    response_model=ScreeningBatchResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate Screening Batch",
    description="Start screening 1000+ candidates for a position. Returns 202 Accepted (async).",
)
async def create_screening_batch(
    request: ScreeningBatchCreateRequest,
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Initiate a screening batch (async).

    Args:
        request: Batch creation request with position_id, resume_ids, config
        recruiter: Current recruiter user
        db: Database session

    Returns:
        202 Accepted with batch_id and initial status

    Raises:
        400: Invalid position_id or resume_ids
        403: Unauthorized
        404: Position not found
    """
    try:
        logger.info(
            f"Recruiter {recruiter.id} initiating screening batch: "
            f"position={request.position_id}, count={len(request.resume_ids)}"
        )

        service = ScreeningService(db)

        # Validate position exists
        from app.models.position import Position
        from sqlalchemy import select

        position = await db.execute(
            select(Position).where(Position.id == request.position_id)
        )
        position = position.scalar_one_or_none()

        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Position {request.position_id} not found",
            )

        # Create batch
        batch = await service.create_screening_batch(
            position_id=request.position_id,
            resume_ids=request.resume_ids,
            batch_config=request.batch_config.dict() if request.batch_config else None,
            recruiter_id=recruiter.id,
        )

        # Enqueue Celery task for async processing
        task = process_screening_batch.delay(
            str(batch.id),
            [str(rid) for rid in request.resume_ids],
            batch.batch_config,
        )

        logger.info(f"Screening batch {batch.id} enqueued: task_id={task.id}")

        return {
            "id": batch.id,
            "position_id": batch.position_id,
            "status": batch.status.value,
            "total_candidates": batch.total_candidates,
            "screened_count": batch.screened_count,
            "pending_review_count": batch.pending_review_count,
            "started_at": batch.started_at,
            "completed_at": batch.completed_at,
            "created_at": batch.created_at,
            "updated_at": batch.updated_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating screening batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating screening batch",
        )


@router.get(
    "/batches/{batch_id}",
    response_model=ScreeningBatchStatusResponse,
    summary="Get Batch Status",
    description="Get current status and progress of a screening batch.",
)
async def get_batch_status(
    batch_id: UUID,
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get batch processing status and progress.

    Args:
        batch_id: Screening batch ID
        recruiter: Current recruiter user
        db: Database session

    Returns:
        Batch status with progress percentage and ETA

    Raises:
        403: Not authorized to view batch
        404: Batch not found
    """
    try:
        service = ScreeningService(db)
        status_dict = await service.get_batch_status(batch_id)

        return {
            "batch_id": batch_id,
            "position_id": UUID(status_dict["position_id"]),
            "status": status_dict["status"],
            "total_candidates": status_dict["total_candidates"],
            "screened_count": status_dict["screened_count"],
            "pending_review_count": status_dict["pending_review_count"],
            "progress_percentage": status_dict["progress_percentage"],
            "estimated_completion_seconds": status_dict["estimated_completion_seconds"],
        }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found",
        )
    except Exception as e:
        logger.error(f"Error getting batch status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting batch status",
        )


# ============================================================================
# RECRUITER REVIEW INTERFACE
# ============================================================================


@router.get(
    "/batches/{batch_id}/pending",
    response_model=ScreeningBatchPendingResponse,
    summary="Get Pending Screenings",
    description="Get paginated list of screening results awaiting recruiter review.",
)
async def get_pending_reviews(
    batch_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("confidence_desc", regex="^(confidence_desc|created_asc)$"),
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get paginated screening results pending recruiter review.

    Args:
        batch_id: Screening batch ID
        page: Page number (1-indexed)
        limit: Results per page (1-100)
        sort_by: Sort order (confidence_desc or created_asc)
        recruiter: Current recruiter user
        db: Database session

    Returns:
        Paginated list of screening results with quick summaries

    Raises:
        404: Batch not found
    """
    try:
        service = ScreeningService(db)

        results, pagination = await service.get_pending_reviews(
            batch_id=batch_id,
            page=page,
            limit=limit,
            sort_by=sort_by,
        )

        # Convert to summary cards
        cards = []
        for result in results:
            card = ScreeningResultSummaryCard(
                screening_result_id=result.id,
                candidate_name=f"{result.user_id}",  # TODO: Get from user model
                candidate_email="",  # TODO: Get from user model
                resume_id=result.resume_id,
                agent_recommendation=result.agent_recommendation,
                confidence_score=result.confidence_score,
                screening_summary_preview=(
                    result.screening_summary[:150] if result.screening_summary else ""
                ),
                has_bias_alerts=result.bias_flags.get("should_be_reviewed", False),
            )
            cards.append(card)

        return {
            "results": cards,
            "pagination": pagination,
        }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found",
        )
    except Exception as e:
        logger.error(f"Error getting pending reviews: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting pending reviews",
        )


@router.get(
    "/results/{screening_result_id}",
    response_model=ScreeningResultDetailResponse,
    summary="Get Screening Details",
    description="Get full screening analysis for recruiter review (5-min brief).",
)
async def get_screening_details(
    screening_result_id: UUID,
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get full screening result with 5-minute recruiter brief.

    Args:
        screening_result_id: ScreeningResult ID
        recruiter: Current recruiter user
        db: Database session

    Returns:
        Full screening details with analysis and conscience checks

    Raises:
        404: Screening result not found
    """
    try:
        from app.models.screening import ScreeningResult
        from sqlalchemy import select

        result = await db.execute(
            select(ScreeningResult).where(
                ScreeningResult.id == screening_result_id
            )
        )
        result = result.scalar_one_or_none()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Screening result {screening_result_id} not found",
            )

        details = result.screening_details or {}

        return {
            "screening_result_id": result.id,
            "candidate_id": result.user_id,
            "candidate_name": f"{result.user_id}",  # TODO: Get from user model
            "candidate_email": "",  # TODO: Get from user model
            "resume_id": result.resume_id,
            "agent_recommendation": result.agent_recommendation,
            "confidence_score": result.confidence_score,
            "screening_summary": result.screening_summary,
            "skills_matched": details.get("skills_matched", []),
            "skills_missing": details.get("skills_missing", []),
            "experience_fit": details.get("experience_fit", {}),
            "career_trajectory": details.get("career_trajectory", {}),
            "red_flags": details.get("red_flags", []),
            "bias_flags": result.bias_flags,
            "recruiter_decision": result.recruiter_decision,
            "recruiter_notes": result.recruiter_notes,
            "was_overridden": result.was_overridden,
            "created_at": result.created_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting screening details: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting screening details",
        )


# ============================================================================
# RECRUITER DECISIONS (Override Point)
# ============================================================================


@router.patch(
    "/results/{screening_result_id}/decide",
    response_model=ScreeningDecisionResponse,
    summary="Record Recruiter Decision",
    description="Record recruiter's decision on screening result (override point).",
)
async def record_recruiter_decision(
    screening_result_id: UUID,
    request: ScreeningDecisionRequest,
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Record recruiter decision on a screening result.

    Captures override patterns for learning loop.

    Args:
        screening_result_id: ScreeningResult ID
        request: Decision with decision, notes, confidence
        recruiter: Current recruiter user
        db: Database session

    Returns:
        Decision recorded confirmation

    Raises:
        404: Screening result not found
        409: Already decided
    """
    try:
        from app.models.screening import ScreeningResult
        from sqlalchemy import select

        result = await db.execute(
            select(ScreeningResult).where(
                ScreeningResult.id == screening_result_id
            )
        )
        result = result.scalar_one_or_none()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Screening result {screening_result_id} not found",
            )

        if result.recruiter_decision:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Screening result {screening_result_id} already decided",
            )

        service = ScreeningService(db)

        decision = await service.process_recruiter_decision(
            screening_result_id=screening_result_id,
            recruiter_decision=request.recruiter_decision,
            recruiter_id=recruiter.id,
            recruiter_notes=request.recruiter_notes,
            recruiter_confidence=request.recruiter_confidence,
        )

        logger.info(
            f"Recruiter {recruiter.id} decided {request.recruiter_decision.value} "
            f"for screening result {screening_result_id}"
        )

        return {
            "status": "recorded",
            "decision_id": decision.id,
            "screening_result_id": screening_result_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording recruiter decision: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error recording recruiter decision",
        )


@router.post(
    "/batches/{batch_id}/bulk-decide",
    response_model=ScreeningBulkDecisionResponse,
    summary="Bulk Recruiter Decisions",
    description="Record multiple recruiter decisions at once for efficiency.",
)
async def record_bulk_decisions(
    batch_id: UUID,
    request: ScreeningBulkDecisionRequest,
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Record multiple recruiter decisions in one request.

    Args:
        batch_id: Screening batch ID (for validation)
        request: List of decisions
        recruiter: Current recruiter user
        db: Database session

    Returns:
        Count and IDs of recorded decisions

    Raises:
        400: Invalid decisions
        404: Batch not found
    """
    try:
        if not request.decisions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No decisions provided",
            )

        if len(request.decisions) > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 500 decisions per request",
            )

        service = ScreeningService(db)
        decision_ids = []

        for decision_dict in request.decisions:
            try:
                decision = await service.process_recruiter_decision(
                    screening_result_id=UUID(decision_dict["screening_result_id"]),
                    recruiter_decision=decision_dict["recruiter_decision"],
                    recruiter_id=recruiter.id,
                    recruiter_notes=decision_dict.get("recruiter_notes"),
                )
                decision_ids.append(decision.id)
            except Exception as e:
                logger.warning(f"Error recording decision: {e}")
                # Continue with next decision on error

        logger.info(
            f"Recruiter {recruiter.id} bulk-decided {len(decision_ids)} results "
            f"for batch {batch_id}"
        )

        return {
            "status": "recorded",
            "count": len(decision_ids),
            "decision_ids": decision_ids,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording bulk decisions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error recording bulk decisions",
        )


# ============================================================================
# ANALYTICS
# ============================================================================


@router.get(
    "/batches/{batch_id}/metrics",
    response_model=ScreeningBatchMetricsResponse,
    summary="Batch Analytics",
    description="Get analytics dashboard for screening batch.",
)
async def get_batch_metrics(
    batch_id: UUID,
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get analytics for screening batch.

    Shows: recommendations distribution, override rate, bias alerts, etc.

    Args:
        batch_id: Screening batch ID
        recruiter: Current recruiter user
        db: Database session

    Returns:
        Metrics with recommendations, decisions, rates, alerts

    Raises:
        404: Batch not found
    """
    try:
        service = ScreeningService(db)
        metrics = await service.get_screening_metrics(batch_id)

        return {
            "batch_id": batch_id,
            "position_id": UUID(metrics["position_id"]),
            "total_screened": metrics["total_screened"],
            "recommendations": metrics["recommendations"],
            "recruiter_decisions": metrics["recruiter_decisions"],
            "override_rate": metrics["override_rate"],
            "avg_confidence_score": metrics["avg_confidence_score"],
            "bias_alerts_count": metrics["bias_alerts_count"],
            "time_to_complete_minutes": metrics["time_to_complete_minutes"],
            "avg_recruiter_review_time_seconds": metrics["avg_recruiter_review_time_seconds"],
        }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found",
        )
    except Exception as e:
        logger.error(f"Error getting batch metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting batch metrics",
        )


__all__ = ["router"]
