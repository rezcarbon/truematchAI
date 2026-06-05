"""Assessment endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status
from sqlalchemy import func, select

from app.config import settings
from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.scoring import classify_match
from app.deps import CurrentUser, DBSession
from app.models.assessment import Assessment
from app.models.position import Position, PositionStatus
from app.models.resume import Resume
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentDetail,
    AssessmentSummary,
    ComparisonResponse,
    GovernanceResponse,
    NarrativeResponse,
    PaginatedAssessments,
    SelfAssessmentCreate,
    TraditionalResponse,
    TrajectoryResponse,
)

router = APIRouter()


async def _get_owned_assessment(
    assessment_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> Assessment:
    assessment = await db.get(Assessment, assessment_id)
    if assessment is None:
        raise NotFoundError("Assessment not found", instance=f"/api/v1/assessments/{assessment_id}")
    # Candidates may only see their own; recruiters/admins have broader access.
    if user.role.value == "candidate" and assessment.user_id != user.id:
        raise AuthorizationError("You do not have permission to access this assessment")
    return assessment


@router.post("", response_model=AssessmentDetail, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    payload: AssessmentCreate, user: CurrentUser, db: DBSession
) -> Assessment:
    resume = await db.get(Resume, payload.resume_id)
    position = await db.get(Position, payload.position_id)
    if resume is None:
        raise NotFoundError("Resume not found", instance=f"/api/v1/assessments")
    if position is None:
        raise NotFoundError("Position not found", instance=f"/api/v1/assessments")

    assessment = Assessment(
        resume_id=payload.resume_id,
        position_id=payload.position_id,
        user_id=resume.user_id,
    )
    db.add(assessment)
    await db.flush()
    await db.commit()

    # Enqueue the async pipeline. Imported lazily so the API process need not
    # import Celery/worker dependencies at module load time.
    from app.workers.tasks import run_assessment

    run_assessment.delay(str(assessment.id))
    return assessment


@router.post("/self", response_model=AssessmentDetail, status_code=status.HTTP_201_CREATED)
async def create_self_assessment(
    payload: SelfAssessmentCreate, user: CurrentUser, db: DBSession
) -> Assessment:
    """Candidate self-serve assessment: own resume + a pasted job description.

    Creates an internal, company-less position from the JD and runs the standard
    pipeline. The candidate may only assess their own resume.
    """
    resume = await db.get(Resume, payload.resume_id)
    if resume is None:
        raise NotFoundError("Resume not found", instance=f"/api/v1/assessments/self")
    if resume.user_id != user.id:
        raise AuthorizationError("You can only assess your own resume")

    position = Position(
        company_id=None,
        created_by=user.id,
        title=payload.position_title or "Self-assessment",
        description=payload.jd_text,
        status=PositionStatus.open,
    )
    db.add(position)
    await db.flush()

    assessment = Assessment(
        resume_id=resume.id, position_id=position.id, user_id=user.id
    )
    db.add(assessment)
    await db.flush()
    await db.commit()

    from app.workers.tasks import run_assessment

    run_assessment.delay(str(assessment.id))
    return assessment


@router.get("", response_model=PaginatedAssessments)
async def list_assessments(
    user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedAssessments:
    stmt = select(Assessment)
    count_stmt = select(func.count()).select_from(Assessment)
    if user.role.value == "candidate":
        stmt = stmt.where(Assessment.user_id == user.id)
        count_stmt = count_stmt.where(Assessment.user_id == user.id)

    total = await db.scalar(count_stmt) or 0
    stmt = (
        stmt.order_by(Assessment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list((await db.scalars(stmt)).all())
    return PaginatedAssessments(
        items=[AssessmentSummary.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{assessment_id}", response_model=AssessmentDetail)
async def get_assessment(
    assessment_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> Assessment:
    return await _get_owned_assessment(assessment_id, user, db)


@router.get("/{assessment_id}/narrative", response_model=NarrativeResponse)
async def get_narrative(
    assessment_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> NarrativeResponse:
    a = await _get_owned_assessment(assessment_id, user, db)
    return NarrativeResponse(
        assessment_id=a.id,
        capability_narrative=a.capability_narrative,
        capability_components=a.capability_components,
        capability_evidence=a.capability_evidence,
    )


@router.get("/{assessment_id}/trajectory", response_model=TrajectoryResponse)
async def get_trajectory(
    assessment_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> TrajectoryResponse:
    a = await _get_owned_assessment(assessment_id, user, db)
    return TrajectoryResponse(
        assessment_id=a.id,
        trajectory_data=a.trajectory_data,
        trajectory_narrative=a.trajectory_narrative,
    )


@router.get("/{assessment_id}/governance", response_model=GovernanceResponse)
async def get_governance(
    assessment_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> GovernanceResponse:
    a = await _get_owned_assessment(assessment_id, user, db)
    # IP-SAFETY: only pass/fail + qualitative notes are returned; no thresholds.
    return GovernanceResponse(
        assessment_id=a.id,
        coherence=a.governance_coherence,
        consistency=a.governance_consistency,
        fidelity=a.governance_fidelity,
        bias_flags=a.governance_bias_flags,
        audit_id=a.governance_audit_id,
    )


@router.get("/{assessment_id}/traditional", response_model=TraditionalResponse)
async def get_traditional(
    assessment_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> TraditionalResponse:
    a = await _get_owned_assessment(assessment_id, user, db)
    return TraditionalResponse(
        assessment_id=a.id,
        traditional_score=a.traditional_score,
        traditional_detail=a.traditional_detail,
    )


@router.get("/{assessment_id}/comparison", response_model=ComparisonResponse)
async def get_comparison(
    assessment_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> ComparisonResponse:
    a = await _get_owned_assessment(assessment_id, user, db)
    match_type = classify_match(
        bool(a.counter_rec_triggered), a.semantic_score, settings.semantic_confirm_threshold
    )
    return ComparisonResponse(
        assessment_id=a.id,
        traditional_score=a.traditional_score,
        semantic_score=a.semantic_score,
        capability_score=a.capability_score,
        score_delta=a.score_delta,
        counter_rec_triggered=a.counter_rec_triggered,
        match_type=match_type,
        counter_rec_reasoning=a.counter_rec_reasoning,
        summary="Three-signal comparison: keyword baseline -> semantic -> capability.",
    )


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(
    assessment_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> None:
    a = await _get_owned_assessment(assessment_id, user, db)
    await db.delete(a)
    return None
