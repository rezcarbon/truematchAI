"""Capability Translation endpoints (candidate-facing).

Re-express a candidate's evidenced capability into ATS-legible, JD-targeted
language and report the measured before→after keyword + semantic lift. Async
job + poll, mirroring CV analysis. Access-gated by billing (default off).
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.config import settings
from app.core.exceptions import NotFoundError
from app.deps import CurrentUser, DBSession
from app.models.capability_translation import CapabilityTranslation, TranslationStatus
from app.models.resume import Resume
from app.schemas.capability_translation import (
    TranslationBullet,
    TranslationListItem,
    TranslationResult,
    TranslationStartRequest,
    TranslationStartResponse,
)

router = APIRouter(prefix="/candidates/capability-translation", tags=["capability-translation"])
logger = logging.getLogger("truematch.capability_translation")


async def _require_translation_access(user, db) -> None:
    """Gate on a paid entitlement or available credit — only when enforcement on."""
    if not settings.billing_enforce:
        return
    from app.services.billing import entitlements as billing_ent

    if not await billing_ent.has_access(db, user.id):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="No credits or active plan. Purchase credits to use Capability Translation.",
        )


async def _consume_credit(user, db, ref_id) -> None:
    if not settings.billing_enforce:
        return
    from app.services.billing import entitlements as billing_ent

    await billing_ent.consume_credit(db, user.id, ref_id)


@router.post(
    "",
    response_model=TranslationStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start a capability translation",
)
async def start_translation(
    payload: TranslationStartRequest, user: CurrentUser, db: DBSession
) -> TranslationStartResponse:
    resume = await db.get(Resume, payload.resume_id)
    if resume is None or resume.user_id != user.id:
        raise NotFoundError(
            f"Resume {payload.resume_id} not found",
            instance="/api/v1/candidates/capability-translation",
        )

    await _require_translation_access(user, db)

    translation = CapabilityTranslation(
        id=uuid.uuid4(),
        user_id=user.id,
        resume_id=payload.resume_id,
        target_role=payload.target_role,
        target_jd=payload.jd_text,
        status=TranslationStatus.pending,
    )
    db.add(translation)
    await db.flush()
    await _consume_credit(user, db, translation.id)
    await db.commit()

    try:
        from app.workers.capability_translation import process_translation_task

        process_translation_task.delay(str(translation.id))
    except Exception as e:  # noqa: BLE001 — Celery may be down in dev
        logger.warning(
            "Failed to enqueue translation task (Celery down?)",
            extra={"error": str(e), "translation_id": str(translation.id)},
        )

    return TranslationStartResponse(translation_id=translation.id, status=translation.status)


@router.get("/{translation_id}", response_model=TranslationResult, summary="Get translation result")
async def get_translation(
    translation_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> TranslationResult:
    t = await db.get(CapabilityTranslation, translation_id)
    if t is None or t.user_id != user.id:
        raise NotFoundError(
            f"Translation {translation_id} not found",
            instance=f"/api/v1/candidates/capability-translation/{translation_id}",
        )

    if t.status != TranslationStatus.completed:
        return TranslationResult(
            translation_id=t.id, status=t.status, target_role=t.target_role,
            error=t.error,
        )

    rewrite = t.rewrite or {}
    bullets = [
        TranslationBullet(
            text=b.get("text", ""),
            grounding=b.get("grounding", ""),
            evidence_strength=b.get("evidence_strength", "MEDIUM"),
        )
        for b in (rewrite.get("bullets") or [])
        if isinstance(b, dict)
    ]
    detail = t.score_detail or {}
    after_kw = detail.get("keyword_after", {})
    kw_lift = _lift(t.after_keyword_score, t.before_keyword_score)
    sem_lift = _lift(t.after_semantic_score, t.before_semantic_score)

    return TranslationResult(
        translation_id=t.id,
        status=t.status,
        target_role=t.target_role,
        source_language=t.source_language,
        original_text=t.original_text,
        summary=rewrite.get("summary"),
        bullets=bullets,
        skills=[str(s) for s in (rewrite.get("skills") or [])],
        translation_notes=rewrite.get("translation_notes"),
        dropped_ungrounded=int(rewrite.get("dropped_ungrounded") or 0),
        before_keyword_score=t.before_keyword_score,
        after_keyword_score=t.after_keyword_score,
        before_semantic_score=t.before_semantic_score,
        after_semantic_score=t.after_semantic_score,
        keyword_lift=kw_lift,
        semantic_lift=sem_lift,
        capability_score=t.capability_score,
        capability_delta=_lift(t.capability_score, t.before_keyword_score),
        matched_keywords_after=list(after_kw.get("matched", []))[:20],
        still_missing_keywords=list(after_kw.get("missing", []))[:20],
    )


@router.get("", response_model=list[TranslationListItem], summary="List my translations")
async def list_translations(
    user: CurrentUser, db: DBSession, limit: int = 20
) -> list[TranslationListItem]:
    rows = (
        await db.scalars(
            select(CapabilityTranslation)
            .where(CapabilityTranslation.user_id == user.id)
            .order_by(CapabilityTranslation.created_at.desc())
            .limit(max(1, min(limit, 100)))
        )
    ).all()
    return [
        TranslationListItem(
            translation_id=t.id,
            target_role=t.target_role,
            status=t.status,
            created_at=t.created_at.isoformat() if t.created_at else "",
            keyword_lift=_lift(t.after_keyword_score, t.before_keyword_score),
            semantic_lift=_lift(t.after_semantic_score, t.before_semantic_score),
        )
        for t in rows
    ]


def _lift(after: int | None, before: int | None) -> int | None:
    if after is None or before is None:
        return None
    return after - before
