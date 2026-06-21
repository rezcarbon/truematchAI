"""Assessment endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.config import settings
from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.scoring import classify_match
from app.engines import reasoning
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


def _progressive_scores(assessment: Assessment, resume: Resume, position: Position) -> None:
    """Progressive scoring: the two DETERMINISTIC signals are pure functions
    that compute in milliseconds — set them at creation time so the caller gets
    an instant keyword + semantic read while the LLM capability judgment streams
    in asynchronously. Also stamps the idempotency input hash.

    Best-effort: any failure leaves the fields for the pipeline to fill.
    """
    try:
        import hashlib

        from app.engines import intake, semantic_match
        from app.engines.prompts.registry import PROMPT_REGISTRY_VERSION

        supplementary = resume.supplementary or {}
        source_text = supplementary.get("extracted_text") or resume.raw_narrative or ""
        jd_text = position.description or ""
        if not source_text or not jd_text:
            return

        assessment.input_hash = hashlib.sha256(
            (source_text + "\x1e" + jd_text + "\x1e" + PROMPT_REGISTRY_VERSION).encode()
        ).hexdigest()

        traditional = intake.traditional_ats(jd_text, source_text)
        semantic = semantic_match.semantic_score(source_text, jd_text)
        assessment.traditional_score = traditional.get("score")
        assessment.traditional_detail = traditional
        assessment.semantic_score = semantic.get("score")
        assessment.semantic_detail = semantic
    except Exception:  # noqa: BLE001 — the async pipeline recomputes regardless
        pass


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


async def _require_assessment_access(user, db) -> None:
    """Gate assessment creation on a paid entitlement or available credit.

    No-op unless billing enforcement is switched on (settings.billing_enforce),
    so the platform/tests run unmetered by default. The caller (whoever
    initiates the assessment) is the one billed.
    """
    if not settings.billing_enforce:
        return
    from app.services.billing import entitlements as billing_ent

    if not await billing_ent.has_access(db, user.id):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="No assessment credits or active plan. Purchase credits to continue.",
        )


async def _consume_assessment_credit(user, db, assessment_id) -> None:
    if not settings.billing_enforce:
        return
    from app.services.billing import entitlements as billing_ent

    await billing_ent.consume_credit(db, user.id, assessment_id)


@router.post("", response_model=AssessmentDetail, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    payload: AssessmentCreate, user: CurrentUser, db: DBSession
) -> Assessment:
    await _require_assessment_access(user, db)
    resume = await db.get(Resume, payload.resume_id)
    position = await db.get(Position, payload.position_id)
    if resume is None:
        raise NotFoundError("Resume not found", instance="/api/v1/assessments")
    if position is None:
        raise NotFoundError("Position not found", instance="/api/v1/assessments")

    assessment = Assessment(
        resume_id=payload.resume_id,
        position_id=payload.position_id,
        user_id=resume.user_id,
    )
    _progressive_scores(assessment, resume, position)
    db.add(assessment)
    await db.flush()
    await _consume_assessment_credit(user, db, assessment.id)
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
    await _require_assessment_access(user, db)
    resume = await db.get(Resume, payload.resume_id)
    if resume is None:
        raise NotFoundError("Resume not found", instance="/api/v1/assessments/self")
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
    _progressive_scores(assessment, resume, position)
    db.add(assessment)
    await db.flush()
    await _consume_assessment_credit(user, db, assessment.id)
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
    a = await _get_owned_assessment(assessment_id, user, db)
    # Surface the detected source languages (for the "translated from …" badge).
    # These live on the related resume/position; attach as transient attributes
    # the from_attributes serializer reads.
    resume = await db.get(Resume, a.resume_id)
    position = await db.get(Position, a.position_id)
    a.source_language = getattr(resume, "source_language", None)
    a.jd_source_language = getattr(position, "source_language", None)
    return a


@router.post("/{assessment_id}/share")
async def share_assessment(
    assessment_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> dict:
    """Create a shareable, anonymised result page for an owned assessment.

    Returns an opaque token + public URL carrying the owner's referral code.
    The shared page exposes ONLY scores/delta — never the narrative or any PII.
    """
    a = await _get_owned_assessment(assessment_id, user, db)
    from app.services.billing import referral

    share = await referral.create_share(db, a, user.id)
    return {
        "token": share.token,
        "share_url": f"{settings.share_base_url}/{share.token}",
        "referral_code": share.referral_code,
    }


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


@router.get("/{assessment_id}/explain")
async def explain_assessment(
    assessment_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> dict:
    """On-demand 'why this score?' explanation for ANY assessment.

    The counter-recommendation reasoning is normally computed only when the
    score delta trips the governance threshold; this endpoint makes the same
    reasoning available conversationally for any completed assessment — a core
    explainability affordance for an AI-native system. Cached on the assessment
    after first computation.
    """
    a = await _get_owned_assessment(assessment_id, user, db)
    if a.capability_score is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assessment has not completed yet.",
        )

    # Reuse the stored reasoning when the pipeline (or a prior call) produced it.
    if a.counter_rec_reasoning:
        return {
            "assessment_id": str(a.id),
            "score_delta": a.score_delta,
            "reasoning": a.counter_rec_reasoning,
            "evidence": a.counter_rec_evidence,
            "source": "stored",
        }

    position = await db.get(Position, a.position_id)
    requirements = (position.parsed_requirements if position else None) or {}
    counter = reasoning.counter_recommendation(
        a.traditional_detail or {"score": a.traditional_score},
        {
            "score": a.capability_score,
            "components": a.capability_components,
            "narrative": a.capability_narrative,
        },
        requirements,
        a.substitutions,
    )
    # Cache so repeat asks don't re-spend LLM tokens.
    a.counter_rec_reasoning = counter.get("reasoning", "")
    a.counter_rec_evidence = {"evidence": counter.get("evidence", [])}
    await db.commit()
    return {
        "assessment_id": str(a.id),
        "score_delta": a.score_delta,
        "reasoning": a.counter_rec_reasoning,
        "evidence": a.counter_rec_evidence,
        "source": "computed",
    }


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(
    assessment_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> None:
    a = await _get_owned_assessment(assessment_id, user, db)
    await db.delete(a)
    return None
