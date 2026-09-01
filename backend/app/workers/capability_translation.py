"""Celery task + sync runner for Capability Translation.

The whole pipeline is synchronous (all engines are pure sync functions), so we
run it directly in the Celery worker's sync session — no async/thread dance.
The core is `run_translation_sync`, importable for tests.
"""
from __future__ import annotations

import logging
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.engines import capability_translation as ct
from app.engines import intake, reasoning, semantic_match, substitution
from app.engines.capability_translation import _coerce_str as _as_text
from app.models.capability_translation import CapabilityTranslation, TranslationStatus
from app.models.resume import Resume
from app.workers.celery_app import celery_app

logger = logging.getLogger("truematch.capability_translation")

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


def run_translation_sync(db: Session, translation: CapabilityTranslation) -> None:
    """Execute the translation pipeline and persist results onto `translation`.

    Steps: resolve resume text → parse → analyse JD → score BEFORE →
    capability substitutions → translate (grounded) → score AFTER → persist.
    Re-scoring uses the SAME deterministic engines we sell recruiters, so the
    before→after lift is measured, not asserted.
    """
    translation.status = TranslationStatus.translating
    db.commit()

    resume = db.get(Resume, translation.resume_id)
    if resume is None:
        raise ValueError(f"Resume {translation.resume_id} not found")

    supplementary = resume.supplementary or {}
    original_source_text = supplementary.get("extracted_text") or resume.raw_narrative or ""
    jd_text = translation.target_jd or ""
    if not original_source_text:
        raise ValueError("Resume has no extractable text to translate.")

    # Multilingual intake: a non-English CV is translated to a faithful English
    # PIVOT, which is then parsed, scored and ATS-legibly rewritten (most ATS are
    # English). The JD is pivoted too. The ORIGINAL text is retained for display.
    from app.engines import translation as _xlate

    cv_tr = _xlate.to_english(original_source_text, kind="resume")
    jd_tr = _xlate.to_english(jd_text, kind="job description")
    source_text = cv_tr["english_text"]
    jd_text = jd_tr["english_text"]
    if cv_tr["method"] == "llm":
        translation.source_language = cv_tr["source_language"]

    # Reuse a prior parse only when the CV was English (a cached parse may have
    # been built from the original-language text); otherwise parse the pivot.
    parsed = (resume.parsed_data if cv_tr["method"] != "llm" else None) \
        or intake.parse_resume(source_text, supplementary)
    requirements = intake.analyze_jd(jd_text)

    # BEFORE: score the original resume against the JD.
    before_kw = intake.traditional_ats(jd_text, source_text)
    before_sem = semantic_match.semantic_score(source_text, jd_text)

    # Which legitimate capability equivalences justify the rewrite.
    subs = substitution.build_substitution_profile(
        requirements.get("proxies"), parsed, evidence=None
    )

    # The capability verdict — the rigorous, evidence-grounded judgment of real
    # fit for this role. Computed on the ORIGINAL résumé (translation never
    # changes real ability), so it's the constant anchor in the candidate view.
    capability_score: int | None = None
    try:
        # The LLM occasionally returns `narrative` (or `summary`) as a nested
        # object rather than a string; coerce to clean text so the capability
        # prompt receives a string, not a stringified dict (LLM→string boundary).
        narrative = _as_text(resume.raw_narrative or parsed.get("narrative") or "")
        cap = reasoning.assess_capability(requirements, parsed, narrative, None, subs, "")
        capability_score = int(cap.get("score") or 0)
    except Exception as exc:  # noqa: BLE001 — capability is enrichment; never fail the translation
        logger.warning("capability verdict failed (translation continues): %s", exc)

    # Translate (grounded, no fabrication enforced inside the engine).
    translation_out = ct.translate_capability(
        resume_text=source_text,
        parsed_resume=parsed,
        jd_text=jd_text,
        requirements=requirements,
        substitutions=subs,
    )
    rewritten_text = ct.assemble_resume_text(translation_out, parsed)

    # AFTER: score the rewrite against the same JD.
    after_kw = intake.traditional_ats(jd_text, rewritten_text)
    after_sem = semantic_match.semantic_score(rewritten_text, jd_text)

    translation.original_text = original_source_text
    translation.rewrite = translation_out
    translation.substitutions = subs
    translation.before_keyword_score = int(before_kw.get("score") or 0)
    translation.after_keyword_score = int(after_kw.get("score") or 0)
    translation.before_semantic_score = int(before_sem.get("score") or 0)
    translation.after_semantic_score = int(after_sem.get("score") or 0)
    translation.capability_score = capability_score
    translation.score_detail = {
        "keyword_before": {
            "matched": before_kw.get("matched_keywords", []),
            "missing": before_kw.get("missing_keywords", []),
        },
        "keyword_after": {
            "matched": after_kw.get("matched_keywords", []),
            "missing": after_kw.get("missing_keywords", []),
        },
        "semantic_before_concepts": before_sem.get("matched_concepts", []),
        "semantic_after_concepts": after_sem.get("matched_concepts", []),
    }
    translation.provenance = {
        "keyword_method": after_kw.get("method"),
        "semantic_method": after_sem.get("method"),
        "translation_method": translation_out.get("method"),
        "prompt_registry_version": _registry_version(),
    }
    translation.status = TranslationStatus.completed
    db.commit()
    logger.info(
        "capability translation completed",
        extra={
            "translation_id": str(translation.id),
            "keyword_lift": translation.after_keyword_score - translation.before_keyword_score,
            "semantic_lift": translation.after_semantic_score - translation.before_semantic_score,
        },
    )


def _registry_version() -> str:
    try:
        from app.engines.prompts.registry import PROMPT_REGISTRY_VERSION

        return PROMPT_REGISTRY_VERSION
    except Exception:  # pragma: no cover
        return "unknown"


@celery_app.task(
    name="app.workers.capability_translation.process_translation_task",
    bind=True,
    max_retries=3,
)
def process_translation_task(self, translation_id: str) -> dict:
    """Process a capability translation end-to-end (sync)."""
    tid = uuid.UUID(translation_id)
    with _sync_session_factory()() as db:
        translation = db.get(CapabilityTranslation, tid)
        if translation is None:
            retries = self.request.retries
            if retries < self.max_retries:
                raise self.retry(countdown=2**retries, exc=Exception("translation not found"))
            return {"status": "failed", "error": "not found after retries"}
        try:
            run_translation_sync(db, translation)
            return {"status": "completed", "translation_id": translation_id}
        except Exception as exc:  # noqa: BLE001 — record failure, don't crash the worker
            logger.warning("capability translation failed: %s", exc, exc_info=True)
            db.rollback()
            translation = db.get(CapabilityTranslation, tid)
            if translation:
                translation.status = TranslationStatus.failed
                translation.error = str(exc)[:2000]
                db.commit()
            return {"status": "failed", "translation_id": translation_id, "error": str(exc)}
