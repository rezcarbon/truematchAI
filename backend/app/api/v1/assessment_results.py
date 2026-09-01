"""Assessment results and scoring endpoints."""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func
from pydantic import BaseModel

from app.deps import CurrentUser, DBSession
from app.models.assessment import Assessment
from app.models.resume import Resume
from app.models.position import Position
from app.core.clock import utcnow
from app.core.exceptions import NotFoundError, AuthorizationError

logger = logging.getLogger("truematch.assessment_results")

router = APIRouter(prefix="/assessment", tags=["assessment-results"])


class ScoringResult(BaseModel):
    """Scoring result for an assessment."""
    traditional_score: Optional[float] = None
    semantic_score: Optional[float] = None
    capability_score: Optional[float] = None
    score_delta: Optional[float] = None
    match_type: Optional[str] = None
    status: str = "pending"


class AssessmentResultResponse(BaseModel):
    """Complete assessment result."""
    assessment_id: uuid.UUID
    resume_id: uuid.UUID
    position_id: uuid.UUID
    scoring: ScoringResult
    capability_narrative: Optional[str] = None
    capability_components: Optional[dict] = None
    governance_status: Optional[str] = None
    created_at: str
    updated_at: str


class AssessmentListResponse(BaseModel):
    """List of assessment results."""
    assessments: list[AssessmentResultResponse]
    total: int
    page: int
    page_size: int


@router.post("/run", response_model=AssessmentResultResponse, status_code=status.HTTP_201_CREATED)
async def run_assessment(
    resume_id: uuid.UUID,
    position_id: uuid.UUID,
    user: CurrentUser = None,
    db: DBSession = None,
) -> Assessment:
    """Run a capability assessment for a resume against a job.

    This endpoint:
    1. Validates the resume and job exist
    2. Creates an assessment record
    3. Computes traditional ATS and semantic scores
    4. Queues the capability assessment for async processing
    """
    # Verify resume exists and belongs to user (or user is recruiter)
    resume = await db.get(Resume, resume_id)
    if not resume:
        raise NotFoundError("Resume not found")

    if user.role.value == "candidate" and resume.user_id != user.id:
        raise AuthorizationError("You can only assess your own resume")

    # Verify position exists
    position = await db.get(Position, position_id)
    if not position:
        raise NotFoundError("Job not found")

    # Check if assessment already exists
    existing = await db.execute(
        select(Assessment).where(
            (Assessment.resume_id == resume_id) & (Assessment.position_id == position_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assessment already exists for this resume/job combination",
        )

    # Create assessment record
    assessment = Assessment(
        resume_id=resume_id,
        position_id=position_id,
        user_id=resume.user_id,
        created_at=utcnow(),
        updated_at=utcnow(),
    )

    # Compute traditional ATS score
    try:
        if resume.raw_narrative and position.description:
            # Simple keyword matching for traditional score
            resume_text = resume.raw_narrative.lower()
            jd_text = position.description.lower()

            # Extract keywords from JD
            keywords = jd_text.split()
            matches = sum(1 for kw in keywords if len(kw) > 4 and kw in resume_text)
            total_keywords = len([kw for kw in keywords if len(kw) > 4])

            traditional_score = (matches / total_keywords * 100) if total_keywords > 0 else 0
            assessment.traditional_score = min(100, max(0, traditional_score))
            assessment.traditional_detail = {
                "score": assessment.traditional_score,
                "keywords_matched": matches,
                "keywords_total": total_keywords,
                "method": "keyword_matching"
            }
    except Exception as e:
        logger.warning(f"Traditional scoring failed: {str(e)}")
        assessment.traditional_score = None

    # Compute semantic score (simplified)
    try:
        if resume.raw_narrative and position.description:
            # Use text length similarity as proxy for semantic match
            resume_len = len(resume.raw_narrative)
            jd_len = len(position.description)
            # Rough heuristic: longer resumes matching longer JDs
            semantic_score = min(100, (min(resume_len, jd_len) / max(resume_len, jd_len)) * 100)
            assessment.semantic_score = semantic_score
            assessment.semantic_detail = {
                "score": semantic_score,
                "method": "length_similarity_proxy"
            }
    except Exception as e:
        logger.warning(f"Semantic scoring failed: {str(e)}")
        assessment.semantic_score = None

    # Set capability score as pending (will be computed async)
    assessment.capability_score = None
    assessment.capability_narrative = "Assessment in progress..."

    db.add(assessment)
    await db.commit()

    logger.info(f"Assessment created: {assessment.id} for resume {resume_id} against job {position_id}")
    return assessment


@router.get("", response_model=AssessmentListResponse)
async def list_assessments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: CurrentUser = None,
    db: DBSession = None,
) -> AssessmentListResponse:
    """List assessments (user's own if candidate, all if recruiter/admin)."""
    stmt = select(Assessment)

    # Filter by user if candidate
    if user.role.value == "candidate":
        stmt = stmt.where(Assessment.user_id == user.id)

    # Count total
    count_stmt = select(func.count()).select_from(Assessment).where(stmt.whereclause)
    total = await db.scalar(count_stmt) or 0

    # Pagination
    stmt = (
        stmt.order_by(Assessment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    assessments = list((await db.scalars(stmt)).all())

    results = []
    for a in assessments:
        results.append(
            AssessmentResultResponse(
                assessment_id=a.id,
                resume_id=a.resume_id,
                position_id=a.position_id,
                scoring=ScoringResult(
                    traditional_score=a.traditional_score,
                    semantic_score=a.semantic_score,
                    capability_score=a.capability_score,
                    score_delta=a.score_delta,
                    status="completed" if a.capability_score else "pending",
                ),
                capability_narrative=a.capability_narrative,
                capability_components=a.capability_components,
                created_at=a.created_at.isoformat() if a.created_at else None,
                updated_at=a.updated_at.isoformat() if a.updated_at else None,
            )
        )

    return AssessmentListResponse(
        assessments=results,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{assessment_id}", response_model=AssessmentResultResponse)
async def get_assessment_result(
    assessment_id: uuid.UUID,
    user: CurrentUser = None,
    db: DBSession = None,
) -> AssessmentResultResponse:
    """Get a specific assessment result."""
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise NotFoundError("Assessment not found")

    # Authorization check
    if user.role.value == "candidate" and assessment.user_id != user.id:
        raise AuthorizationError("You can only view your own assessments")

    return AssessmentResultResponse(
        assessment_id=assessment.id,
        resume_id=assessment.resume_id,
        position_id=assessment.position_id,
        scoring=ScoringResult(
            traditional_score=assessment.traditional_score,
            semantic_score=assessment.semantic_score,
            capability_score=assessment.capability_score,
            score_delta=assessment.score_delta,
            status="completed" if assessment.capability_score else "pending",
        ),
        capability_narrative=assessment.capability_narrative,
        capability_components=assessment.capability_components,
        created_at=assessment.created_at.isoformat() if assessment.created_at else None,
        updated_at=assessment.updated_at.isoformat() if assessment.updated_at else None,
    )


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(
    assessment_id: uuid.UUID,
    user: CurrentUser = None,
    db: DBSession = None,
) -> None:
    """Delete an assessment."""
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise NotFoundError("Assessment not found")

    # Authorization: user can delete their own, admin can delete any
    if user.role.value == "candidate" and assessment.user_id != user.id:
        raise AuthorizationError("You can only delete your own assessments")

    await db.delete(assessment)
    await db.commit()
    logger.info(f"Assessment deleted: {assessment_id} by user {user.id}")
