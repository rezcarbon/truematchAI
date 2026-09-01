"""Celery task + sync runner for Transition Intelligence.

Pipeline (all sync engines): resolve résumé text → multilingual English pivot →
parse → analyse a light role frame → capability verdict (the anchor) → transition
options grounded in that verdict. The core is `run_transition_sync`, importable
for tests.
"""
from __future__ import annotations

import logging
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.engines import intake, reasoning, substitution
from app.engines import transition_intelligence as ti
from app.models.resume import Resume
from app.models.transition_analysis import TransitionAnalysis, TransitionStatus
from app.workers.celery_app import celery_app

logger = logging.getLogger("truematch.transition_intelligence")

_sync_engine = None
_SyncSessionLocal: sessionmaker[Session] | None = None


def _sync_database_url() -> str:
    url = settings.database_url
    return url.replace("+asyncpg", "+psycopg") if "+asyncpg" in url else url


def _sync_session_factory() -> sessionmaker[Session]:
    global _sync_engine, _SyncSessionLocal
    if _SyncSessionLocal is None:
        _sync_engine = create_engine(_sync_database_url(), pool_pre_ping=True, future=True)
        _SyncSessionLocal = sessionmaker(bind=_sync_engine, expire_on_commit=False)
    return _SyncSessionLocal


def _registry_version() -> str:
    try:
        from app.engines.prompts.registry import PROMPT_REGISTRY_VERSION

        return PROMPT_REGISTRY_VERSION
    except Exception:  # pragma: no cover
        return "unknown"


def run_transition_sync(db: Session, analysis: TransitionAnalysis) -> None:
    """Execute the transition-intelligence pipeline (sync; called from Celery)."""
    analysis.status = TransitionStatus.analyzing
    db.commit()

    resume = db.get(Resume, analysis.resume_id)
    if resume is None:
        raise ValueError(f"Resume {analysis.resume_id} not found")

    supplementary = resume.supplementary or {}
    original_text = supplementary.get("extracted_text") or resume.raw_narrative or ""
    if not original_text:
        raise ValueError("Resume has no extractable text to analyse.")

    # Multilingual intake: translate non-English CV to an English pivot so the
    # English-tuned reasoning runs unchanged; the original language is recorded.
    from app.engines import translation as _xlate

    cv_tr = _xlate.to_english(original_text, kind="resume")
    source_text = cv_tr["english_text"]
    if cv_tr["method"] == "llm":
        analysis.source_language = cv_tr["source_language"]

    parsed = (resume.parsed_data if cv_tr["method"] != "llm" else None) \
        or intake.parse_resume(source_text, supplementary)
    narrative = resume.raw_narrative or parsed.get("narrative", "")
    current_role = analysis.current_role or ""

    # Anchor: the capability verdict. We frame "requirements" from the candidate's
    # CURRENT role so the verdict reflects demonstrated ability, then predict
    # transitions FROM that anchor. Capability never fabricates ability.
    requirements = intake.analyze_jd(current_role) if current_role else {}
    subs = substitution.build_substitution_profile(
        requirements.get("proxies") if requirements else None, parsed, evidence=None
    )
    capability: dict = {}
    capability_score: int | None = None
    try:
        capability = reasoning.assess_capability(requirements, parsed, narrative, None, subs, "")
        capability_score = int(capability.get("score") or 0)
    except Exception as exc:  # noqa: BLE001 — anchor is best-effort; analysis continues
        logger.warning("capability verdict failed (transition continues): %s", exc)

    result = ti.assess_transition(
        parsed_resume=parsed,
        capability=capability,
        current_role=current_role,
        target=analysis.target or "",
        role_context="",
    )

    # Phase 2: attach concrete learning options to each upskilling-gap item via
    # the modular training-provider registry (no-op if disabled / no match).
    from app.services import training

    result = training.enrich_transition_result(result)

    analysis.result = result
    analysis.capability_score = capability_score
    analysis.provenance = {
        "method": result.get("method"),
        "capability_anchored": capability_score is not None,
        "source_language": analysis.source_language,
        "prompt_registry_version": _registry_version(),
    }
    analysis.status = TransitionStatus.completed
    db.commit()


@celery_app.task(name="app.workers.transition_intelligence.reassess_due_transitions")
def reassess_due_transitions(limit: int = 50) -> dict:
    """Phase 3: re-run tracked analyses whose review is due, snapshotting a fresh
    row each time so the candidate's trajectory accumulates. Gated + bounded."""
    if not settings.transition_tracking_enabled:
        return {"status": "disabled"}
    from sqlalchemy import select

    from app.core.clock import utcnow
    from app.services.transition_tracking import next_review_at

    reassessed = 0
    with _sync_session_factory()() as db:
        due = db.execute(
            select(TransitionAnalysis)
            .where(
                TransitionAnalysis.track.is_(True),
                TransitionAnalysis.status == TransitionStatus.completed,
                TransitionAnalysis.next_review_at.isnot(None),
                TransitionAnalysis.next_review_at <= utcnow(),
            )
            .limit(limit)
        ).scalars().all()
        for old in due:
            snapshot = TransitionAnalysis(
                user_id=old.user_id, resume_id=old.resume_id,
                current_role=old.current_role, target=old.target,
                status=TransitionStatus.pending,
                track=True, next_review_at=next_review_at(),
            )
            old.track = False  # hand tracking to the newest snapshot
            db.add(snapshot)
            db.flush()
            try:
                run_transition_sync(db, snapshot)
                reassessed += 1
            except Exception as exc:  # noqa: BLE001 — one bad row must not stop the batch
                logger.warning("reassessment failed for %s: %s", snapshot.id, exc)
                db.rollback()
        db.commit()
    return {"status": "ok", "reassessed": reassessed}


@celery_app.task(
    name="app.workers.transition_intelligence.process_transition_task",
    bind=True,
    max_retries=3,
)
def process_transition_task(self, analysis_id: str) -> dict:
    """Process a transition analysis end-to-end (sync)."""
    aid = uuid.UUID(analysis_id)
    with _sync_session_factory()() as db:
        analysis = db.get(TransitionAnalysis, aid)
        if analysis is None:
            retries = self.request.retries
            if retries < self.max_retries:
                raise self.retry(countdown=2**retries, exc=Exception("analysis not found"))
            return {"status": "failed", "error": "not found after retries"}
        try:
            run_transition_sync(db, analysis)
            return {"status": "completed", "analysis_id": analysis_id}
        except Exception as exc:  # noqa: BLE001 — record failure, don't crash the worker
            logger.warning("transition analysis failed: %s", exc)
            db.rollback()
            analysis = db.get(TransitionAnalysis, aid)
            if analysis:
                analysis.status = TransitionStatus.failed
                analysis.error = str(exc)[:2000]
                db.commit()
            return {"status": "failed", "analysis_id": analysis_id, "error": str(exc)}
