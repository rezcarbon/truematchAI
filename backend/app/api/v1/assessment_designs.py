"""Assessment Design API - Phase 2 REST endpoints.

Endpoints for recruiter assessment design workflow:
1. Initiate design (async)
2. Get pending designs (paginated queue)
3. Get design details
4. Approve design
5. Request changes
6. Reject design
7. View fairness report

All endpoints require recruiter role and full audit trail.
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User, UserRole
from app.schemas.assessment_design import (
    AssessmentDesignCreateRequest,
    AssessmentDesignResponse,
    AssessmentDesignPendingResponse,
    AssessmentDesignApproveRequest,
    AssessmentDesignRequestChangesRequest,
    FairnessReportResponse,
)
from app.services.assessment_designer_service import AssessmentDesignerService
from app.workers.assessment_design_queue import design_assessment

logger = logging.getLogger("truematch.assessment_designs_api")

router = APIRouter(prefix="/api/v1/assessments", tags=["assessment_designs"])


def require_recruiter(user: User = Depends(get_current_user)) -> User:
    """Dependency: Require recruiter role."""
    if user.role not in (UserRole.recruiter, UserRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can access assessment design endpoints",
        )
    return user


# ============================================================================
# DESIGN INITIATION
# ============================================================================


@router.post(
    "/design",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate Assessment Design",
    description="Start designing an assessment for a candidate from screening results.",
)
async def initiate_assessment_design(
    request: AssessmentDesignCreateRequest,
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Initiate assessment design for a candidate.

    Agent will design a customized assessment that recruiter validates for fairness.

    Args:
        request: Screening result and position IDs
        recruiter: Current recruiter user
        db: Database session

    Returns:
        202 Accepted with design_id

    Raises:
        404: Screening result or position not found
        403: Unauthorized
    """
    try:
        logger.info(
            f"Recruiter {recruiter.id} initiating design for "
            f"screening {request.screening_result_id}"
        )

        service = AssessmentDesignerService(db)

        # Initiate design
        design = await service.initiate_design(
            screening_result_id=request.screening_result_id,
            position_id=request.position_id,
        )

        # Enqueue Celery task for async processing (if using worker)
        # design_assessment.delay(str(design.id))

        return {
            "design_id": str(design.id),
            "status": design.review_status.value,
            "position_id": str(design.position_id),
            "candidate_id": str(design.candidate_id),
            "created_at": design.created_at.isoformat(),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error initiating design: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error initiating assessment design",
        )


# ============================================================================
# RECRUITER REVIEW INTERFACE
# ============================================================================


@router.get(
    "/designs/pending",
    response_model=AssessmentDesignPendingResponse,
    summary="Get Pending Designs",
    description="Get paginated list of assessment designs awaiting recruiter review.",
)
async def get_pending_designs(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    position_id: Optional[UUID] = Query(None),
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get assessment designs pending recruiter review.

    Args:
        page: Page number (1-indexed)
        limit: Results per page (1-100)
        position_id: Optional filter by position
        recruiter: Current recruiter user
        db: Database session

    Returns:
        Paginated list of pending designs with quick summaries
    """
    try:
        service = AssessmentDesignerService(db)

        designs, pagination = await service.get_pending_designs(
            page=page,
            limit=limit,
            position_id=position_id,
        )

        # Convert to summary cards
        design_cards = []
        for design in designs:
            fairness = design.design_fairness_check or {}
            agent_design = design.agent_design or {}

            card = {
                "design_id": str(design.id),
                "candidate_id": str(design.candidate_id),
                "position_id": str(design.position_id),
                "questions_count": len(agent_design.get("questions", [])),
                "fairness_score": fairness.get("fairness_score", 0),
                "fairness_passed": fairness.get("passed", False),
                "created_at": design.created_at.isoformat(),
            }
            design_cards.append(card)

        return {
            "designs": design_cards,
            "pagination": pagination,
        }

    except Exception as e:
        logger.error(f"Error getting pending designs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting pending designs",
        )


@router.get(
    "/designs/{design_id}",
    summary="Get Design Details",
    description="Get full assessment design for recruiter review (includes all details).",
)
async def get_design_details(
    design_id: UUID,
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get full assessment design with all details.

    Args:
        design_id: AssessmentDesign ID
        recruiter: Current recruiter user
        db: Database session

    Returns:
        Full design details (questions, rubric, guidance, fairness report)

    Raises:
        404: Design not found
    """
    try:
        from sqlalchemy import select
        from app.models.assessment_design import AssessmentDesign

        design = await db.execute(
            select(AssessmentDesign).where(AssessmentDesign.id == design_id)
        )
        design = design.scalar_one_or_none()

        if not design:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Design {design_id} not found",
            )

        agent_design = design.agent_design or {}
        fairness = design.design_fairness_check or {}

        return {
            "design_id": str(design.id),
            "candidate_id": str(design.candidate_id),
            "position_id": str(design.position_id),
            "status": design.review_status.value,
            "questions": agent_design.get("questions", []),
            "interview_guidance": agent_design.get("interview_guidance", {}),
            "evaluation_rubric": agent_design.get("evaluation_rubric", {}),
            "design_rationale": agent_design.get("design_rationale", ""),
            "accessibility_notes": agent_design.get("accessibility_notes", []),
            "fairness_check": fairness,
            "recruiter_feedback": design.recruiter_feedback,
            "recruiter_confidence": design.recruiter_confidence,
            "created_at": design.created_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting design details: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting design details",
        )


# ============================================================================
# RECRUITER DECISIONS
# ============================================================================


@router.patch(
    "/designs/{design_id}/approve",
    summary="Approve Design",
    description="Recruiter approves assessment design. Assessment is created and ready to use.",
)
async def approve_design(
    design_id: UUID,
    request: AssessmentDesignApproveRequest,
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Recruiter approves assessment design.

    Creates Assessment record and links design.

    Args:
        design_id: AssessmentDesign ID
        request: Approval request with optional notes
        recruiter: Current recruiter user
        db: Database session

    Returns:
        Approval confirmation

    Raises:
        404: Design not found
        409: Design already reviewed
    """
    try:
        from app.models.assessment_design import AssessmentDesignReviewStatus

        service = AssessmentDesignerService(db)

        # Check design exists and is pending
        from sqlalchemy import select
        from app.models.assessment_design import AssessmentDesign

        design = await db.execute(
            select(AssessmentDesign).where(AssessmentDesign.id == design_id)
        )
        design = design.scalar_one_or_none()

        if not design:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Design {design_id} not found",
            )

        if design.review_status != AssessmentDesignReviewStatus.pending_review:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Design already {design.review_status.value}",
            )

        # Approve design
        approved_design = await service.approve_design(
            design_id=design_id,
            recruiter_id=recruiter.id,
            recruiter_notes=request.recruiter_notes,
            recruiter_confidence=request.recruiter_confidence,
        )

        logger.info(
            f"Recruiter {recruiter.id} approved design {design_id} "
            f"with confidence {request.recruiter_confidence}"
        )

        return {
            "status": "approved",
            "design_id": str(design_id),
            "assessment_created": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving design: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error approving design",
        )


@router.patch(
    "/designs/{design_id}/request-changes",
    summary="Request Changes",
    description="Recruiter requests changes to assessment design. Agent will redesign.",
)
async def request_design_changes(
    design_id: UUID,
    request: AssessmentDesignRequestChangesRequest,
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Recruiter requests changes to assessment design.

    Args:
        design_id: AssessmentDesign ID
        request: Feedback and specific issues
        recruiter: Current recruiter user
        db: Database session

    Returns:
        Change request confirmation

    Raises:
        404: Design not found
        409: Design already reviewed
    """
    try:
        from app.models.assessment_design import AssessmentDesignReviewStatus

        service = AssessmentDesignerService(db)

        # Check design status
        from sqlalchemy import select
        from app.models.assessment_design import AssessmentDesign

        design = await db.execute(
            select(AssessmentDesign).where(AssessmentDesign.id == design_id)
        )
        design = design.scalar_one_or_none()

        if not design:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Design {design_id} not found",
            )

        if design.review_status != AssessmentDesignReviewStatus.pending_review:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Design already {design.review_status.value}",
            )

        # Request changes
        updated_design = await service.request_changes(
            design_id=design_id,
            recruiter_id=recruiter.id,
            feedback=request.feedback,
            specific_issues=request.specific_issues,
        )

        logger.info(
            f"Recruiter {recruiter.id} requested changes for design {design_id}: "
            f"{len(request.specific_issues)} issues"
        )

        return {
            "status": "changes_requested",
            "design_id": str(design_id),
            "issues_count": len(request.specific_issues),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting changes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error requesting changes",
        )


@router.patch(
    "/designs/{design_id}/reject",
    summary="Reject Design",
    description="Recruiter rejects design (will create manual assessment).",
)
async def reject_design(
    design_id: UUID,
    reason: str = Query(..., description="Reason for rejection"),
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Recruiter rejects assessment design.

    Args:
        design_id: AssessmentDesign ID
        reason: Reason for rejection
        recruiter: Current recruiter user
        db: Database session

    Returns:
        Rejection confirmation

    Raises:
        404: Design not found
        409: Design already reviewed
    """
    try:
        from app.models.assessment_design import AssessmentDesignReviewStatus

        service = AssessmentDesignerService(db)

        # Check design status
        from sqlalchemy import select
        from app.models.assessment_design import AssessmentDesign

        design = await db.execute(
            select(AssessmentDesign).where(AssessmentDesign.id == design_id)
        )
        design = design.scalar_one_or_none()

        if not design:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Design {design_id} not found",
            )

        if design.review_status != AssessmentDesignReviewStatus.pending_review:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Design already {design.review_status.value}",
            )

        # Reject design
        rejected_design = await service.reject_design(
            design_id=design_id,
            recruiter_id=recruiter.id,
            reason=reason,
        )

        logger.info(
            f"Recruiter {recruiter.id} rejected design {design_id}: {reason}"
        )

        return {
            "status": "rejected",
            "design_id": str(design_id),
            "reason": reason,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting design: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error rejecting design",
        )


# ============================================================================
# ANALYTICS & REPORTING
# ============================================================================


@router.get(
    "/designs/{design_id}/fairness-report",
    response_model=FairnessReportResponse,
    summary="Fairness Report",
    description="Get detailed fairness analysis for assessment design.",
)
async def get_fairness_report(
    design_id: UUID,
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get fairness analysis report for assessment design.

    Shows bias detection, cognitive load, relevance, and equity checks.

    Args:
        design_id: AssessmentDesign ID
        recruiter: Current recruiter user
        db: Database session

    Returns:
        Fairness report with recommendations

    Raises:
        404: Design not found
    """
    try:
        service = AssessmentDesignerService(db)

        report = await service.get_fairness_report(design_id)

        logger.info(f"Recruiter {recruiter.id} viewed fairness report for {design_id}")

        return report

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error getting fairness report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting fairness report",
        )


__all__ = ["router"]
