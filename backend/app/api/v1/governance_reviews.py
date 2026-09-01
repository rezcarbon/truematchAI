"""API endpoints for governance reviews."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func
from pydantic import BaseModel, Field

from app.models.governance_review import GovernanceReview, ReviewStatus
from app.deps import CurrentUser, DBSession

router = APIRouter(prefix="/governance-reviews", tags=["governance"])


class GovernanceReviewDetail(BaseModel):
    """Detail view of a governance review."""
    id: str = Field(description="Review ID")
    review_type: str = Field(description="Type of review (cv_analysis, assessment, jd_simulation)")
    resource_id: str = Field(description="ID of the resource being reviewed")
    user_id: str = Field(description="ID of the user who created the resource")
    failed_gates: list[str] = Field(description="List of gates that failed")
    gate_details: dict = Field(description="Detailed results from each failed gate")
    failure_reason: str = Field(description="Human-readable reason for the review")
    status: str = Field(description="Review status (pending, approved, rejected, escalated)")
    reviewed_by: Optional[str] = Field(description="ID of the reviewer")
    review_decision: Optional[str] = Field(description="Decision made by reviewer")
    review_notes: Optional[str] = Field(description="Notes from reviewer")
    created_at: str = Field(description="When the review was created")
    updated_at: str = Field(description="When the review was last updated")

    class Config:
        from_attributes = True


class ReviewList(BaseModel):
    """List of governance reviews."""
    items: list[GovernanceReviewDetail]
    total: int
    pending: int
    approved: int
    rejected: int
    escalated: int


class ApproveReviewRequest(BaseModel):
    """Request to approve a review."""
    decision: str = Field(description="Approval decision (approved, rejected, escalated)")
    notes: Optional[str] = Field(None, description="Optional notes from reviewer")


@router.get("", response_model=ReviewList)
async def list_governance_reviews(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    review_type: Optional[str] = None,
    db: DBSession = None,
    current_user: CurrentUser = None,
) -> ReviewList:
    """List governance reviews (admin/reviewer only)."""
    # Check if user is admin or reviewer
    if current_user.role not in ("admin", "reviewer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and reviewers can access governance reviews",
        )

    query = select(GovernanceReview)

    # Apply filters
    if status_filter:
        query = query.where(GovernanceReview.status == status_filter)
    if review_type:
        query = query.where(GovernanceReview.review_type == review_type)

    # Order by created_at descending (newest first)
    query = query.order_by(GovernanceReview.created_at.desc())

    # Count total
    count_result = await db.execute(select(func.count(GovernanceReview.id)))
    total = count_result.scalar() or 0

    # Paginate
    reviews = await db.execute(query.offset(skip).limit(limit))
    items = reviews.scalars().all()

    # Count by status
    status_counts = {}
    for status_val in ["pending", "approved", "rejected", "escalated"]:
        count_result = await db.execute(
            select(func.count(GovernanceReview.id)).where(
                GovernanceReview.status == status_val
            )
        )
        status_counts[status_val] = count_result.scalar() or 0

    return ReviewList(
        items=[GovernanceReviewDetail.from_orm(r) for r in items],
        total=total,
        pending=status_counts["pending"],
        approved=status_counts["approved"],
        rejected=status_counts["rejected"],
        escalated=status_counts["escalated"],
    )


@router.get("/{review_id}", response_model=GovernanceReviewDetail)
async def get_governance_review(
    review_id: UUID,
    db: DBSession = None,
    current_user: CurrentUser = None,
) -> GovernanceReviewDetail:
    """Get a specific governance review."""
    # Check if user is admin/reviewer or the owner
    if current_user.role not in ("admin", "reviewer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and reviewers can access governance reviews",
        )

    review = await db.get(GovernanceReview, review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    return GovernanceReviewDetail.from_orm(review)


@router.post("/{review_id}/approve", response_model=GovernanceReviewDetail)
async def approve_governance_review(
    review_id: UUID,
    request: ApproveReviewRequest,
    db: DBSession = None,
    current_user: CurrentUser = None,
) -> GovernanceReviewDetail:
    """Approve or reject a governance review."""
    # Check if user is admin/reviewer
    if current_user.role not in ("admin", "reviewer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and reviewers can approve reviews",
        )

    review = await db.get(GovernanceReview, review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    # Check if already reviewed
    if review.status != ReviewStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Review already {review.status}",
        )

    # Update review
    review.status = ReviewStatus(request.decision)
    review.reviewed_by = current_user.id
    review.review_decision = request.decision
    review.review_notes = request.notes

    await db.commit()

    return GovernanceReviewDetail.from_orm(review)
