"""Transition Intelligence endpoints (candidate-facing).

From a candidate's evidenced capability, predict the adjacent / higher-complexity
roles they could move into, the upskilling gap, and an honest timeline. Async job
+ poll, mirroring Capability Translation. Access-gated by billing (default off)
and by the `transition_intelligence_enabled` feature flag.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.config import settings
from app.core.exceptions import NotFoundError
from app.deps import CurrentUser, DBSession
from app.models.resume import Resume
from app.models.transition_analysis import (
    OutcomeStatus,
    TransitionAnalysis,
    TransitionOutcome,
    TransitionStatus,
)
from app.schemas.transition_intelligence import (
    OutcomeDTO,
    OutcomeRecordRequest,
    TrackRequest,
    TrajectoryPoint,
    TransitionListItem,
    TransitionMetrics,
    TransitionOption,
    TransitionResult,
    TransitionStartRequest,
    TransitionStartResponse,
    TransitionTimeline,
    UpskillingItem,
)

router = APIRouter(prefix="/candidates/transition-intelligence", tags=["transition-intelligence"])
logger = logging.getLogger("truematch.transition_intelligence")


def _require_enabled() -> None:
    if not settings.transition_intelligence_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transition Intelligence is not enabled.",
        )


async def _require_access(user, db) -> None:
    if not settings.billing_enforce:
        return
    from app.services.billing import entitlements as billing_ent

    if not await billing_ent.has_access(db, user.id):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="No credits or active plan. Purchase credits to use Transition Intelligence.",
        )


async def _consume_credit(user, db, ref_id) -> None:
    if not settings.billing_enforce:
        return
    from app.services.billing import entitlements as billing_ent

    await billing_ent.consume_credit(db, user.id, ref_id)


@router.post(
    "",
    response_model=TransitionStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start a transition-intelligence analysis",
)
async def start_transition(
    payload: TransitionStartRequest, user: CurrentUser, db: DBSession
) -> TransitionStartResponse:
    _require_enabled()
    resume = await db.get(Resume, payload.resume_id)
    # Owner, or a recruiter/admin running internal-mobility on a candidate's CV.
    from app.models.user import UserRole

    is_staff = user.role in (UserRole.recruiter, UserRole.admin)
    if resume is None or (resume.user_id != user.id and not is_staff):
        raise NotFoundError(
            f"Resume {payload.resume_id} not found",
            instance="/api/v1/candidates/transition-intelligence",
        )

    await _require_access(user, db)

    analysis = TransitionAnalysis(
        id=uuid.uuid4(),
        user_id=user.id,
        resume_id=payload.resume_id,
        current_role=payload.current_role,
        target=payload.target,
        status=TransitionStatus.pending,
    )
    db.add(analysis)
    await db.flush()
    await _consume_credit(user, db, analysis.id)
    await db.commit()

    try:
        from app.workers.transition_intelligence import process_transition_task

        process_transition_task.delay(str(analysis.id))
    except Exception as e:  # noqa: BLE001 — Celery may be down in dev
        logger.warning(
            "Failed to enqueue transition task (Celery down?)",
            extra={"error": str(e), "analysis_id": str(analysis.id)},
        )

    return TransitionStartResponse(analysis_id=analysis.id, status=analysis.status)


@router.get("/{analysis_id}", response_model=TransitionResult, summary="Get transition result")
async def get_transition(
    analysis_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> TransitionResult:
    a = await db.get(TransitionAnalysis, analysis_id)
    if a is None or a.user_id != user.id:
        raise NotFoundError(
            f"Transition analysis {analysis_id} not found",
            instance="/api/v1/candidates/transition-intelligence",
        )

    if a.status != TransitionStatus.completed:
        return TransitionResult(
            analysis_id=a.id, status=a.status, current_role=a.current_role,
            source_language=a.source_language, error=a.error,
        )

    result = a.result or {}
    options = []
    for o in result.get("transition_options") or []:
        tl = o.get("timeline") or {}
        options.append(TransitionOption(
            role=o.get("role", ""),
            direction=o.get("direction", "adjacent"),
            feasibility=o.get("feasibility", "STRETCH"),
            rationale=o.get("rationale", ""),
            transferable_strengths=list(o.get("transferable_strengths") or []),
            upskilling_gap=[UpskillingItem(**g) for g in (o.get("upskilling_gap") or [])],
            timeline=TransitionTimeline(**tl) if tl else None,
            evidence_strength=o.get("evidence_strength", "MEDIUM"),
        ))

    return TransitionResult(
        analysis_id=a.id,
        status=a.status,
        current_role=a.current_role,
        source_language=a.source_language,
        capability_score=a.capability_score,
        readiness_summary=result.get("readiness_summary"),
        transition_options=options,
        honesty_notes=result.get("honesty_notes"),
        dropped_ungrounded=int(result.get("dropped_ungrounded") or 0),
    )


@router.get("", response_model=list[TransitionListItem], summary="List my transition analyses")
async def list_transitions(user: CurrentUser, db: DBSession) -> list[TransitionListItem]:
    rows = (
        await db.execute(
            select(TransitionAnalysis)
            .where(TransitionAnalysis.user_id == user.id)
            .order_by(TransitionAnalysis.created_at.desc())
            .limit(50)
        )
    ).scalars().all()
    return [
        TransitionListItem(
            analysis_id=r.id, current_role=r.current_role, status=r.status,
            created_at=r.created_at.isoformat() if r.created_at else "",
            capability_score=r.capability_score,
        )
        for r in rows
    ]


# --- Phase 3: longitudinal tracking ----------------------------------------


def _is_staff(user) -> bool:
    from app.models.user import UserRole

    return user.role in (UserRole.recruiter, UserRole.admin)


@router.post("/{analysis_id}/track", summary="Enable/disable quarterly re-assessment")
async def set_tracking(
    analysis_id: uuid.UUID, payload: TrackRequest, user: CurrentUser, db: DBSession
) -> dict:
    from app.services.transition_tracking import next_review_at

    a = await db.get(TransitionAnalysis, analysis_id)
    if a is None or (a.user_id != user.id and not _is_staff(user)):
        raise NotFoundError(f"Transition analysis {analysis_id} not found")
    a.track = bool(payload.enabled)
    a.next_review_at = next_review_at() if payload.enabled else None
    await db.commit()
    return {"tracking": a.track, "next_review_at": a.next_review_at.isoformat() if a.next_review_at else None}


@router.get("/trajectory/by-resume/{resume_id}", response_model=list[TrajectoryPoint],
            summary="Capability/readiness trajectory for a résumé")
async def get_trajectory(
    resume_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> list[TrajectoryPoint]:
    from app.services.transition_tracking import build_trajectory

    q = select(TransitionAnalysis).where(TransitionAnalysis.resume_id == resume_id)
    if not _is_staff(user):
        q = q.where(TransitionAnalysis.user_id == user.id)
    rows = (await db.execute(q)).scalars().all()
    return [TrajectoryPoint(**p) for p in build_trajectory(list(rows))]


@router.post("/outcome", response_model=OutcomeDTO, summary="Record a transition outcome")
async def record_outcome(
    payload: OutcomeRecordRequest, user: CurrentUser, db: DBSession
) -> OutcomeDTO:
    a = await db.get(TransitionAnalysis, payload.analysis_id)
    if a is None or (a.user_id != user.id and not _is_staff(user)):
        raise NotFoundError(f"Transition analysis {payload.analysis_id} not found")
    try:
        st = OutcomeStatus(payload.status)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid status '{payload.status}'.")
    outcome = TransitionOutcome(
        id=uuid.uuid4(),
        user_id=a.user_id,
        analysis_id=a.id,
        predicted_role=payload.predicted_role,
        status=st,
        actual_role=payload.actual_role,
        recorded_by=user.id,
        note=payload.note,
    )
    db.add(outcome)
    await db.commit()
    return OutcomeDTO(
        id=outcome.id, analysis_id=outcome.analysis_id, predicted_role=outcome.predicted_role,
        status=outcome.status.value, actual_role=outcome.actual_role, note=outcome.note,
        created_at=outcome.created_at.isoformat() if outcome.created_at else None,
    )


@router.get("/cohort/metrics", response_model=TransitionMetrics,
            summary="Cohort transition metrics (recruiter/admin)")
async def get_metrics(user: CurrentUser, db: DBSession) -> TransitionMetrics:
    if not _is_staff(user):
        raise HTTPException(status_code=403, detail="Recruiter or admin role required.")
    from app.services.transition_tracking import aggregate_metrics

    analyses = (await db.execute(select(TransitionAnalysis))).scalars().all()
    outcomes = (await db.execute(select(TransitionOutcome))).scalars().all()
    return TransitionMetrics(**aggregate_metrics(list(analyses), list(outcomes)))
