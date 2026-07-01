"""Assessment pipeline Celery tasks.

Pipeline: intake (parse resume + analyze JD + traditional simulation)
       -> reasoning (capability + trajectory + JD interrogation + counter-rec)
       -> governance (coherence, consistency, fidelity, bias)
       -> compile + audit.

The worker uses a synchronous SQLAlchemy session derived from the configured
async DATABASE_URL. The engines make real Claude calls when an API key is
configured (``is_live()``), falling back to deterministic mock fixtures only
when no key is set — see ``engines/client.py``.
"""
from __future__ import annotations

import logging
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.core.governance import GovernanceConfig, get_governance_config
from app.engines import (
    corpus,
    decision_engine,
    enrichment,
    governance_engine,
    intake,
    reasoning,
    semantic_match,
    substitution,
    text_utils,
)
from app.core import provenance, scoring
from app.core.timing import phase_timer
from app.models.assessment import Assessment, AssessmentStatus
from app.models.audit import AuditTrail
from app.models.governance_log import GovernanceLog, GateName
from app.models.ingest_queue import IngestQueueItem, IngestSource, IngestStatus, IngestType
from app.models.position import Position
from app.models.resume import Resume
from app.workers.celery_app import celery_app

logger = logging.getLogger("truematch.tasks")

# Synchronous engine for the worker. asyncpg cannot be used from sync code, so we
# map the async URL to the psycopg (v3) sync driver. The engine/session factory
# are built lazily so importing this module does not require the sync DB driver
# to be present (e.g. in the API process, which never executes the task body).
_sync_engine = None
_SyncSessionLocal: sessionmaker[Session] | None = None


def _sync_database_url() -> str:
    """Derive a synchronous SQLAlchemy URL from the configured async URL."""
    url = settings.database_url
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg")
    return url


def _session_factory() -> sessionmaker[Session]:
    global _sync_engine, _SyncSessionLocal
    if _SyncSessionLocal is None:
        _sync_engine = create_engine(_sync_database_url(), pool_pre_ping=True, future=True)
        _SyncSessionLocal = sessionmaker(bind=_sync_engine, expire_on_commit=False)
    return _SyncSessionLocal


def _audit(db: Session, assessment_id: uuid.UUID, event_type: str, data: dict) -> AuditTrail:
    entry = AuditTrail(
        assessment_id=assessment_id,
        event_type=event_type,
        event_data=data,
        actor_type="system",
    )
    db.add(entry)
    db.flush()
    return entry


@celery_app.task(name="app.workers.tasks.run_assessment", bind=True, max_retries=2)
def run_assessment(self, assessment_id: str) -> dict:
    """Run the full assessment pipeline for a single assessment id.

    On failure after max retries, invokes DLQ handler to mark as failed,
    alert admins, and log incident.
    """
    aid = uuid.UUID(assessment_id)
    with _session_factory()() as db:
        assessment = db.get(Assessment, aid)
        if assessment is None:
            logger.error("Assessment %s not found", assessment_id)
            return {"status": "not_found", "assessment_id": assessment_id}

        try:
            governance_cfg = get_governance_config()
        except Exception:  # governance config must be present to govern results
            governance_cfg = None
            logger.warning("Governance config unavailable; governance gates will be skipped.")

        assessment.status = AssessmentStatus.running
        db.commit()
        _audit(db, aid, "pipeline.started", {})
        db.commit()

        try:
            resume = db.get(Resume, assessment.resume_id)
            position = db.get(Position, assessment.position_id)
            if resume is None or position is None:
                raise ValueError("Resume or Position missing for assessment.")

            # Idempotency: identical inputs (same resume text + JD + prompt
            # registry) can reuse a prior completed result — effective
            # determinism and zero LLM cost for repeats.
            if settings.assessment_reuse_identical and _try_reuse(db, assessment):
                db.commit()
                return {
                    "status": assessment.status.value,
                    "assessment_id": assessment_id,
                    "reused": True,
                }

            result = _execute_pipeline(db, assessment, resume, position, governance_cfg)
            # Set status based on decision type:
            # - approval: 'completed' (autonomous decision)
            # - advisory/escalate: 'flagged_for_review' (requires human review)
            decision_type_str = result.get("decision_type")
            if decision_type_str == "approval":
                assessment.status = AssessmentStatus.completed
            else:
                assessment.status = AssessmentStatus.flagged_for_review
            _audit(
                db,
                aid,
                "pipeline.completed",
                {
                    "score_delta": assessment.score_delta,
                    "status": assessment.status.value,
                    "governed": result.get("governed"),
                    "decision_type": result.get("decision_type"),
                    "human_review_required": result.get("human_review_required"),
                },
            )
            db.commit()
            # Selective verification: if inline enrichment is off but the
            # reasoning cited candidate-supplied links, verify just those
            # links asynchronously (targeted, never blocks the result).
            if settings.enrichment_selective and not settings.enrichment_enabled:
                try:
                    verify_cited_evidence.delay(assessment_id)
                except Exception:  # noqa: BLE001 — broker hiccup must not fail the run
                    logger.warning("Could not enqueue selective verification for %s", assessment_id)
            # Auto-report: render candidate + recruiter PDFs for concierge hand-off
            # (off by default; rendering is isolated and never affects the result).
            if settings.auto_report_enabled:
                try:
                    from app.workers.render_reports import render_assessment_reports

                    render_assessment_reports.delay(assessment_id)
                except Exception:  # noqa: BLE001 — broker hiccup must not fail the run
                    logger.warning("Could not enqueue auto-report for %s", assessment_id)
            return {"status": assessment.status.value, "assessment_id": assessment_id, **result}

        except Exception as exc:  # noqa: BLE001
            db.rollback()
            assessment = db.get(Assessment, aid)
            if assessment is not None:
                assessment.status = AssessmentStatus.failed
                _audit(db, aid, "pipeline.failed", {"error": str(exc)})
                db.commit()
            logger.exception("Assessment pipeline failed for %s", assessment_id)

            # Check if we've exhausted retries
            if self.request.retries >= self.max_retries:
                # Invoke DLQ handler with full context
                _invoke_dlq_handler(assessment_id, exc)
                return {
                    "status": "dlq_triggered",
                    "assessment_id": assessment_id,
                    "error": str(exc),
                }

            # Retry with exponential backoff
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)


async def _run_agent_plan_async(plan_id: str) -> dict:
    """Execute (or resume) a durable agent plan with a fresh async session.

    The action handlers are async, so the plan runner needs a real
    AsyncSession — a fresh async engine per run avoids event-loop
    contamination from the worker process (same pattern as the CV/JD workers).
    """
    import asyncio  # noqa: F401 — ensures loop semantics are explicit
    import uuid as _uuid

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.models.agent_plan import AgentPlan
    from app.models.user import User
    from app.services.action_handlers import PlanActionHandler

    engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    try:
        async with factory() as adb:
            plan = await adb.get(AgentPlan, _uuid.UUID(plan_id))
            if plan is None:
                return {"status": "not_found", "plan_id": plan_id}
            if plan.status in ("completed", "failed", "cancelled"):
                return {"status": plan.status, "plan_id": plan_id, "noop": True}
            user = await adb.get(User, plan.user_id)
            if user is None:
                plan.status = "failed"
                plan.error = "Plan owner no longer exists"
                await adb.commit()
                return {"status": "failed", "plan_id": plan_id, "error": plan.error}
            return await PlanActionHandler.execute_plan_steps(plan, user, adb)
    finally:
        await engine.dispose()


@celery_app.task(name="app.workers.tasks.execute_agent_plan", bind=True, max_retries=2)
def execute_agent_plan(self, plan_id: str) -> dict:
    """Run a durable agent plan in the background (resumable across restarts)."""
    import asyncio

    try:
        return asyncio.run(_run_agent_plan_async(plan_id))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Agent plan %s failed", plan_id)
        if self.request.retries >= self.max_retries:
            return {"status": "error", "plan_id": plan_id, "error": str(exc)}
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@celery_app.task(name="app.workers.tasks.resume_stalled_plans")
def resume_stalled_plans() -> dict:
    """Re-enqueue plans stuck 'running' with no progress for too long.

    A plan whose ``updated_at`` is older than ``plan_stall_seconds`` is assumed
    to have lost its worker (crash/restart) and is re-dispatched. Active plans
    commit after every step, so a progressing plan never looks stalled.
    """
    from datetime import datetime, timedelta, timezone

    from app.models.agent_plan import AgentPlan

    cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.plan_stall_seconds)
    with _session_factory()() as db:
        stalled = db.execute(
            select(AgentPlan.id).where(
                AgentPlan.status == "running",
                AgentPlan.updated_at < cutoff,
            )
        ).scalars().all()
    for pid in stalled:
        execute_agent_plan.delay(str(pid))
    if stalled:
        logger.info("Resumed %d stalled agent plan(s)", len(stalled))
    return {"resumed": len(stalled)}


@celery_app.task(name="app.workers.tasks.rebuild_role_taxonomy")
def rebuild_role_taxonomy() -> dict:
    """Recompute the self-learned role taxonomy from current positions."""
    from app.services.role_taxonomy import rebuild_taxonomy

    with _session_factory()() as db:
        return rebuild_taxonomy(db)


async def _sync_ats_connector_async(provider: str, actor_id: str) -> dict:
    """Import a configured ATS connector's jobs + candidates (background sync)."""
    import uuid as _uuid

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.models.user import User
    from app.services.ats_connectors import get_connector
    from app.services.ats_connectors.importer import import_candidates, import_jobs

    connector = get_connector(provider)
    if connector is None or not connector.is_configured:
        return {"status": "skipped", "reason": "not configured", "provider": provider}

    jobs = connector.list_jobs()
    candidates = connector.list_candidates()

    engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    try:
        async with factory() as adb:
            actor = await adb.get(User, _uuid.UUID(actor_id))
            if actor is None:
                return {"status": "failed", "reason": "actor not found"}
            jres = await import_jobs(adb, connector.provider, jobs, actor)
            cres = await import_candidates(adb, connector.provider, candidates, actor)
            await adb.commit()
            return {"status": "completed", **jres, **cres}
    finally:
        await engine.dispose()


@celery_app.task(name="app.workers.tasks.sync_ats_connector")
def sync_ats_connector(provider: str, actor_id: str) -> dict:
    """Background full sync of an external ATS (jobs + candidates)."""
    import asyncio

    return asyncio.run(_sync_ats_connector_async(provider, actor_id))


@celery_app.task(name="app.workers.tasks.rescore_position_on_drift")
def rescore_position_on_drift(position_id: str) -> dict:
    """Re-run assessments for a position's candidates after its JD drifted.

    Triggered when a JD edit produces deterministic drift signals. Recomputes
    drift itself (so the decision is self-contained/auditable), then creates a
    FRESH assessment for each distinct candidate previously assessed against
    this position and dispatches the normal pipeline. Hash idempotency means a
    candidate whose (resume + new JD + registry) is unchanged replays for free;
    only genuinely affected candidates incur LLM cost. History is preserved —
    new assessments are added, old ones are never mutated.
    """
    from app.engines import jd_evolution
    from app.models.jd_version import JDVersion

    pid = uuid.UUID(position_id)
    with _session_factory()() as db:
        position = db.get(Position, pid)
        if position is None:
            return {"status": "not_found", "position_id": position_id}

        versions = [
            {
                "version": v.version,
                "description": v.description,
                "parsed_requirements": v.parsed_requirements,
            }
            for v in db.execute(
                select(JDVersion)
                .where(JDVersion.position_id == pid)
                .order_by(JDVersion.version)
            ).scalars()
        ]
        drift = jd_evolution.detect_drift(versions)
        if not drift.get("drift_signals"):
            return {"status": "skipped", "reason": "no drift signals", "position_id": position_id}

        # Distinct candidates previously assessed against this position. One
        # fresh assessment per (latest) resume; cap protects against fan-out.
        rows = db.execute(
            select(Assessment.resume_id, Assessment.user_id)
            .where(Assessment.position_id == pid)
            .order_by(Assessment.created_at.desc())
        ).all()
        seen: set = set()
        targets: list[tuple] = []
        for resume_id, user_id in rows:
            if resume_id in seen:
                continue
            seen.add(resume_id)
            targets.append((resume_id, user_id))
            if len(targets) >= settings.auto_rescore_max_candidates:
                break

        dispatched = []
        for resume_id, user_id in targets:
            new = Assessment(resume_id=resume_id, position_id=pid, user_id=user_id)
            db.add(new)
            db.flush()
            dispatched.append(str(new.id))

        _audit(
            db,
            None,
            "position.rescored_on_drift",
            {
                "position_id": position_id,
                "trend": drift.get("trend"),
                "drift_signals": len(drift.get("drift_signals", [])),
                "candidates_rescored": len(dispatched),
                "capped": len(seen) >= settings.auto_rescore_max_candidates,
            },
        )
        db.commit()

    for aid in dispatched:
        run_assessment.delay(aid)
    return {
        "status": "completed",
        "position_id": position_id,
        "candidates_rescored": len(dispatched),
        "assessment_ids": dispatched,
    }


@celery_app.task(name="app.workers.tasks.verify_cited_evidence", max_retries=1)
def verify_cited_evidence(assessment_id: str) -> dict:
    """Selectively verify candidate links the assessment reasoning relied on.

    Inline enrichment may be disabled globally (network kill-switch for the
    scoring path). This task runs AFTER the assessment, targets ONLY links
    that the capability narrative / counter-recommendation / substitution
    profile actually cited, and upgrades their status in verified_evidence.
    Targeted instead of blanket: the network surface stays minimal and the
    blocking pipeline stays network-free.
    """
    import json as _json

    aid = uuid.UUID(assessment_id)
    with _session_factory()() as db:
        assessment = db.get(Assessment, aid)
        if assessment is None:
            return {"status": "not_found", "assessment_id": assessment_id}

        items = (assessment.verified_evidence or {}).get("items") or []
        unverified = [i for i in items if i.get("status") == "unverified" and i.get("ref")]
        if not unverified:
            return {"status": "skipped", "reason": "no unverified evidence"}

        cited_text = " ".join(
            filter(
                None,
                [
                    assessment.capability_narrative or "",
                    assessment.counter_rec_reasoning or "",
                    _json.dumps(assessment.substitutions or {}),
                    _json.dumps(assessment.capability_components or {}),
                ],
            )
        )
        targets = [i for i in unverified if i["ref"] in cited_text]
        if not targets:
            return {"status": "skipped", "reason": "no cited unverified evidence"}

        # classify_ref re-types each ref, so a flat URL list is sufficient.
        verified = enrichment.enrich_supplementary(
            {"portfolio_urls": [i["ref"] for i in targets]}, force=True
        )
        by_ref = {v.get("ref"): v for v in verified}
        upgraded = 0
        for item in items:
            v = by_ref.get(item.get("ref"))
            if v:
                item.update(v)
                if v.get("status") == "verified":
                    upgraded += 1
        assessment.verified_evidence = {"items": list(items)}
        _audit(
            db,
            aid,
            "enrichment.selective",
            {"targeted": len(targets), "verified": upgraded},
        )
        db.commit()
        return {
            "status": "completed",
            "assessment_id": assessment_id,
            "targeted": len(targets),
            "verified": upgraded,
        }


# Result fields copied verbatim when reusing a prior identical assessment.
_REUSE_FIELDS = (
    "traditional_score", "traditional_detail", "semantic_score", "semantic_detail",
    "capability_score", "capability_components", "capability_narrative",
    "capability_evidence", "trajectory_data", "trajectory_narrative",
    "counter_rec_triggered", "counter_rec_reasoning", "counter_rec_evidence",
    "jd_quality_score", "jd_issues", "verified_evidence", "substitutions",
    "governance_coherence", "governance_consistency", "governance_fidelity",
    "governance_bias_flags", "score_delta", "decision_type",
    "human_review_required", "article_14_compliant", "review_reason",
)


def _try_reuse(db: Session, assessment: Assessment) -> bool:
    """Copy results from a prior COMPLETED assessment with the same input hash."""
    if not assessment.input_hash:
        return False
    prior = db.scalar(
        select(Assessment)
        .where(
            Assessment.input_hash == assessment.input_hash,
            Assessment.id != assessment.id,
            Assessment.capability_score.is_not(None),
            Assessment.status.in_(
                [AssessmentStatus.completed, AssessmentStatus.flagged_for_review]
            ),
        )
        .order_by(Assessment.created_at.desc())
        .limit(1)
    )
    if prior is None:
        return False
    for field in _REUSE_FIELDS:
        setattr(assessment, field, getattr(prior, field))
    assessment.status = prior.status
    _audit(
        db,
        assessment.id,
        "pipeline.reused",
        {"reused_from": str(prior.id), "input_hash": assessment.input_hash},
    )
    logger.info(
        "Assessment reused identical prior result",
        extra={"assessment_id": str(assessment.id), "reused_from": str(prior.id)},
    )
    return True


def _execute_pipeline(
    db: Session,
    assessment: Assessment,
    resume: Resume,
    position: Position,
    governance_cfg: GovernanceConfig | None,
) -> dict:
    aid = assessment.id

    # --- 1. Intake ---------------------------------------------------------
    # Source text comes from the document extracted at upload time (stored in
    # supplementary.extracted_text); fall back to any previously stored narrative.
    supplementary = resume.supplementary or {}
    source_text_original = supplementary.get("extracted_text") or resume.raw_narrative or ""
    jd_text_original = position.description or ""
    # Multilingual intake: translate non-English CV / JD to a faithful ENGLISH
    # PIVOT so the deterministic keyword + corpus-IDF signals (and the English-
    # tuned reasoning prompts) run unchanged. Originals are retained for display
    # and provenance; English input passes through untouched at near-zero cost.
    from app.engines import translation as _xlate

    cv_tr = _xlate.to_english(source_text_original, kind="resume")
    jd_tr = _xlate.to_english(jd_text_original, kind="job description")
    source_text = cv_tr["english_text"]
    jd_text = jd_tr["english_text"]
    if cv_tr["method"] == "llm":
        # Persist the pivot + language so re-runs and the UI can reuse them.
        supplementary = {**supplementary, "english_text": source_text,
                         "source_language": cv_tr["source_language"]}
        resume.supplementary = supplementary
        resume.source_language = cv_tr["source_language"]
    if jd_tr["method"] == "llm":
        position.source_language = jd_tr["source_language"]
        position.description_en = jd_text
    # Idempotency hash is over the ORIGINAL inputs, so an identical upload still
    # reuses its result regardless of translation variance.
    if not assessment.input_hash and source_text_original and jd_text_original:
        import hashlib

        from app.engines.prompts.registry import PROMPT_REGISTRY_VERSION

        assessment.input_hash = hashlib.sha256(
            (source_text_original + "\x1e" + jd_text_original + "\x1e" + PROMPT_REGISTRY_VERSION).encode()
        ).hexdigest()
    # Reproducibility manifest (input hashes + model/prompt/engine versions),
    # recorded before any reasoning runs — the anchor of the audit record.
    _audit(db, aid, "pipeline.provenance", provenance.build_manifest(source_text, jd_text))
    if cv_tr["source_language"] not in ("en", "und") or jd_tr["source_language"] not in ("en", "und"):
        _audit(db, aid, "pipeline.translation", {
            "cv": {"language": cv_tr["source_language"], "method": cv_tr["method"],
                   "confidence": cv_tr["confidence"]},
            "jd": {"language": jd_tr["source_language"], "method": jd_tr["method"],
                   "confidence": jd_tr["confidence"]},
            "pivot": "english", "embedding_model": settings.semantic_embedding_model,
        })
    if resume.parsed_data:
        parsed_resume = resume.parsed_data
    else:
        parsed_resume = intake.parse_resume(source_text, supplementary)
        # Persist the faithful narrative summary the parser produced.
        narrative = parsed_resume.get("narrative")
        if narrative:
            resume.raw_narrative = narrative
    requirements = position.parsed_requirements or intake.analyze_jd(jd_text)
    raw_narrative = resume.raw_narrative
    # IDF weights from the accumulating JD corpus — read on the MAIN thread before
    # the parallel block (the DB session is not thread-safe).
    idf = corpus.idf_map(db, set(text_utils.term_frequencies(jd_text).keys()))
    # Learned context from past hiring decisions for this position (the learning
    # loop). Read on the main thread; "" until decisions have accumulated.
    from app.services.decision_learning import fetch_learned_context_sync
    from app.services.role_taxonomy import fetch_role_context_sync
    learned_context = fetch_learned_context_sync(db, position.id)
    # Self-learned role-family context (taxonomy). Appended to learned context
    # so the capability prompt also weighs what comparable roles require.
    role_context = fetch_role_context_sync(db, position.id)
    if role_context:
        learned_context = (learned_context + "\n\n" + role_context).strip()

    # --- Parallel fan-out --------------------------------------------------
    # Independent engines run CONCURRENTLY: the deterministic keyword + semantic
    # matchers (instant, no LLM), trajectory + JD-interrogation (LLM), and the
    # enrichment -> substitution -> capability chain (network + LLM). Every engine
    # is a pure function with no DB access, so this is thread-safe; the DB writes
    # all happen below on the main thread.
    # Thread the candidate's name into enrichment so publication discovery can
    # find verified works keyed on identity (not just explicitly-listed DOIs).
    _cand_name = ((parsed_resume.get("contact") or {}).get("name") or "").strip()
    _enrich_input = dict(supplementary)
    if _cand_name and _cand_name.lower() != "candidate" and not _enrich_input.get("author_name"):
        _enrich_input["author_name"] = _cand_name

    def _evidence_chain():
        ev = enrichment.enrich_supplementary(_enrich_input)
        subs = substitution.build_substitution_profile(
            requirements.get("proxies"), parsed_resume, ev
        )
        if settings.assessment_high_assurance:
            # High-assurance mode: 3 independent capability judgments in
            # parallel — report the MEDIAN and the SPREAD. Wide spread means
            # the model is genuinely uncertain about this candidate, which is
            # itself a signal (surfaced in components._ensemble).
            with ThreadPoolExecutor(max_workers=3) as ens:
                futures = [
                    ens.submit(
                        reasoning.assess_capability,
                        requirements, parsed_resume, raw_narrative, ev, subs, learned_context,
                    )
                    for _ in range(3)
                ]
                runs = [f.result() for f in futures]
            runs.sort(key=lambda r: r.get("score", 0))
            cap_ = runs[1]  # median-scored run carries the narrative/components
            scores = [r.get("score", 0) for r in runs]
            cap_.setdefault("components", {})["_ensemble"] = {
                "scores": scores,
                "median": scores[1],
                "spread": scores[-1] - scores[0],
                "runs": len(scores),
            }
        else:
            cap_ = reasoning.assess_capability(
                requirements, parsed_resume, raw_narrative, ev, subs, learned_context
            )
        return ev, subs, cap_

    with phase_timer("scoring"), ThreadPoolExecutor(max_workers=5) as ex:
        f_trad = ex.submit(intake.traditional_ats, jd_text, source_text, idf)
        f_sem = ex.submit(semantic_match.semantic_score, source_text, jd_text)
        f_traj = ex.submit(reasoning.analyze_trajectory, parsed_resume)
        f_jd = ex.submit(reasoning.interrogate_jd, jd_text)
        f_chain = ex.submit(_evidence_chain)
        traditional = f_trad.result()
        semantic = f_sem.result()
        trajectory = f_traj.result()
        jd_review = f_jd.result()
        evidence, substitutions, capability = f_chain.result()

    # --- Persist results (main thread) -------------------------------------
    resume.parsed_data = parsed_resume
    position.parsed_requirements = requirements
    assessment.traditional_score = traditional.get("score")
    assessment.traditional_detail = traditional
    assessment.semantic_score = semantic.get("score")
    assessment.semantic_detail = semantic
    _audit(
        db,
        aid,
        "intake.completed",
        {
            "traditional_score": assessment.traditional_score,
            "traditional_idf_weighted": traditional.get("idf_weighted"),
            "semantic_score": assessment.semantic_score,
            "semantic_method": semantic.get("method"),
        },
    )

    assessment.verified_evidence = {"items": evidence}
    assessment.substitutions = substitutions
    _audit(
        db,
        aid,
        "enrichment.completed",
        {
            "evidence_count": len(evidence),
            "verified_count": sum(1 for e in evidence if e.get("status") == "verified"),
            "substitution_count": len(substitutions.get("substitutions", [])),
        },
    )

    assessment.capability_score = capability.get("score")
    assessment.capability_components = capability.get("components")
    assessment.capability_narrative = capability.get("narrative")
    assessment.capability_evidence = {"components": capability.get("components")}
    assessment.trajectory_data = trajectory.get("trajectory")
    assessment.trajectory_narrative = trajectory.get("narrative")
    assessment.jd_quality_score = jd_review.get("quality_score")
    assessment.jd_issues = {"issues": jd_review.get("issues", [])}
    position.jd_quality_score = jd_review.get("quality_score")
    position.jd_issues = {"issues": jd_review.get("issues", [])}

    # Score delta and counter-recommendation gating.
    trad = assessment.traditional_score or 0
    cap = assessment.capability_score or 0
    assessment.score_delta = cap - trad
    if _should_counter_recommend(assessment.score_delta, governance_cfg):
        counter = reasoning.counter_recommendation(
            traditional, capability, requirements, substitutions
        )
        assessment.counter_rec_triggered = True
        assessment.counter_rec_reasoning = counter.get("reasoning")
        assessment.counter_rec_evidence = {"evidence": counter.get("evidence", [])}
    _audit(
        db,
        aid,
        "reasoning.completed",
        {"capability_score": cap, "score_delta": assessment.score_delta},
    )

    # --- 3. Governance with Audit Logging -----------------------------------
    # A run is "governed" only when operational (real, numeric) gate values are
    # present. With placeholder config, gates cannot be evaluated and the result
    # is recorded as ungoverned rather than falsely marked as passing.
    governed = governance_cfg is not None and governance_cfg.is_operational()
    assessment_view = {
        "capability_score": cap,
        "components": capability.get("components"),
        "narrative": capability.get("narrative"),
    }

    # Execute gates in sequence and log to GovernanceLog table
    gate_sequence = 0
    if governed:
        # Gate 1: Coherence
        gate_sequence += 1
        coherence_result = governance_engine.check_coherence(assessment_view, governance_cfg)
        assessment.governance_coherence = coherence_result
        gov_log = GovernanceLog(
            id=uuid.uuid4(),
            assessment_id=aid,
            gate_sequence=gate_sequence,
            gate_name=GateName.coherence,
            passed=_passed(coherence_result),
            observations=coherence_result if isinstance(coherence_result, dict) else {"result": str(coherence_result)}
        )
        db.add(gov_log)
        db.flush()

        # Gate 2: Consistency
        gate_sequence += 1
        consistency_result = governance_engine.check_consistency(assessment_view, governance_cfg)
        assessment.governance_consistency = consistency_result
        gov_log = GovernanceLog(
            id=uuid.uuid4(),
            assessment_id=aid,
            gate_sequence=gate_sequence,
            gate_name=GateName.consistency,
            passed=_passed(consistency_result),
            observations=consistency_result if isinstance(consistency_result, dict) else {"result": str(consistency_result)}
        )
        db.add(gov_log)
        db.flush()

        # Gate 3: Fidelity
        gate_sequence += 1
        fidelity_result = governance_engine.check_fidelity(parsed_resume, assessment_view, governance_cfg)
        assessment.governance_fidelity = fidelity_result
        gov_log = GovernanceLog(
            id=uuid.uuid4(),
            assessment_id=aid,
            gate_sequence=gate_sequence,
            gate_name=GateName.fidelity,
            passed=_passed(fidelity_result),
            observations=fidelity_result if isinstance(fidelity_result, dict) else {"result": str(fidelity_result)}
        )
        db.add(gov_log)
        db.flush()

    # Gate 4: Bias check (always runs, even if ungoverned)
    gate_sequence += 1
    bias_result = governance_engine.check_bias(parsed_resume, assessment_view)
    assessment.governance_bias_flags = bias_result
    # Bias check doesn't have a strict "passed" field; flag presence indicates issues
    bias_passed = not bool((bias_result or {}).get("flags"))
    gov_log = GovernanceLog(
        id=uuid.uuid4(),
        assessment_id=aid,
        gate_sequence=gate_sequence,
        gate_name=GateName.bias_check,
        passed=bias_passed,
        observations=bias_result if isinstance(bias_result, dict) else {"result": str(bias_result)}
    )
    db.add(gov_log)
    db.flush()

    coherence_passed = _passed(assessment.governance_coherence)
    consistency_passed = _passed(assessment.governance_consistency)
    fidelity_passed = _passed(assessment.governance_fidelity)
    # Mandatory gate: any explicit failure on a governed run routes to human
    # review. Governance cannot be bypassed.
    governance_fully_passed = governed and (
        coherence_passed is True
        and consistency_passed is True
        and fidelity_passed is True
    )
    review_required = governed and (
        coherence_passed is False
        or consistency_passed is False
        or fidelity_passed is False
    )

    gov_audit = _audit(
        db,
        aid,
        "governance.completed",
        {
            "governed": governed,
            "coherence_passed": coherence_passed,
            "consistency_passed": consistency_passed,
            "fidelity_passed": fidelity_passed,
            "bias_flag_count": len((assessment.governance_bias_flags or {}).get("flags", [])),
            "review_required": review_required,
        },
    )
    assessment.governance_audit_id = gov_audit.id

    # --- 4. EU AI Act Decision Taxonomy (Article 14) -------------------------
    # Determine decision type and human review requirements based on:
    #   - Capability score (confidence: 0-100)
    #   - Governance gates (coherence, consistency, fidelity all pass)
    capability_score = cap or 0
    decision_type, requires_review = decision_engine.determine_decision_type(
        assessment, capability_score, governance_fully_passed
    )
    decision_engine.apply_decision_to_assessment(
        assessment, decision_type, governance_fully_passed
    )

    # Update assessment status based on decision type:
    #   - approval: set to 'completed' (autonomous decision approved)
    #   - advisory/escalate: set to 'flagged_for_review' (human review required)
    if decision_type == assessment.decision_type and decision_type.value == "approval":
        review_required = False
    if requires_review:
        review_required = True

    _audit(
        db,
        aid,
        "decision.classified",
        {
            "decision_type": decision_type.value,
            "capability_score": capability_score,
            "governance_passed": governance_fully_passed,
            "requires_human_review": requires_review,
            "article_14_compliant": assessment.article_14_compliant,
        },
    )

    # Classify the surfaced candidate using the semantic signal (hidden_gem vs
    # surfaced_strong_match) — the separation the delta gate alone can't make.
    match_type = scoring.classify_match(
        bool(assessment.counter_rec_triggered),
        assessment.semantic_score,
        settings.semantic_confirm_threshold,
    )
    _audit(db, aid, "classification.completed", {"match_type": match_type})

    return {
        "traditional_score": assessment.traditional_score,
        "semantic_score": assessment.semantic_score,
        "capability_score": assessment.capability_score,
        "counter_rec_triggered": assessment.counter_rec_triggered,
        "match_type": match_type,
        "governed": governed,
        "governance_review_required": review_required,
        "decision_type": decision_type.value,
        "human_review_required": requires_review,
        "article_14_compliant": assessment.article_14_compliant,
    }


def _passed(gate_result: dict | None) -> bool | None:
    if not gate_result:
        return None
    return gate_result.get("passed")


def _should_counter_recommend(
    score_delta: int | None, governance_cfg: "GovernanceConfig | None"
) -> bool:
    """Trigger a counter-recommendation when capability materially exceeds the
    traditional baseline.

    IP-SAFETY: the magnitude threshold is governance-controlled and lives in the
    external config (`COUNTER_REC_DELTA`). When operational config is present we
    apply that numeric gate; otherwise (dev/offline, ungoverned) we fall back to
    a directional check so the feature remains demonstrable. No magnitude value
    is ever hardcoded in source.
    """
    if score_delta is None:
        return False
    if governance_cfg is not None and governance_cfg.is_operational():
        return score_delta >= governance_cfg.counter_rec_delta()
    return score_delta > 0


# ============================================================================
# Ingest Queue Processing Tasks
# ============================================================================


@celery_app.task(name="app.workers.tasks.process_ingest_item", bind=True, max_retries=3, default_retry_delay=60)
def process_ingest_item(
    self,
    item_id: str,
    source: str = "folder",
) -> dict:
    """
    Process an ingested document (CV or JD draft).

    Flow:
    1. Load ingest queue item from database
    2. Extract text if not already done
    3. Create Resume and Assessment (for CV) or improve JD (for JD draft)
    4. Enqueue assessment pipeline or governance review
    5. Update ingest queue status
    6. Send notifications

    Args:
        item_id: UUID of IngestQueueItem
        source: Source type (folder or email)

    Returns:
        Dict with processing result
    """
    try:
        item_uuid = uuid.UUID(item_id)
        with _session_factory()() as db:
            # Load ingest item
            stmt = select(IngestQueueItem).where(IngestQueueItem.id == item_uuid)
            ingest_item = db.scalar(stmt)

            if ingest_item is None:
                logger.error(f"Ingest item {item_id} not found")
                return {"status": "not_found", "item_id": item_id}

            try:
                # Update status to processing
                ingest_item.status = IngestStatus.extracting
                db.commit()
                _audit(db, item_uuid, "ingest.started", {"source": source})

                # Route based on ingest type
                if ingest_item.ingest_type == IngestType.cv:
                    result = _process_cv_ingest(db, ingest_item)
                elif ingest_item.ingest_type == IngestType.jd_draft:
                    result = _process_jd_ingest(db, ingest_item)
                else:
                    raise ValueError(f"Unknown ingest type: {ingest_item.ingest_type}")

                # Update status
                ingest_item.status = IngestStatus.completed
                _audit(
                    db,
                    item_uuid,
                    "ingest.completed",
                    {
                        "result": result.get("status"),
                        "assessment_id": str(result.get("assessment_id")) if result.get("assessment_id") else None,
                    },
                )
                db.commit()

                logger.info(
                    f"Ingest processing completed: {item_id}",
                    extra={
                        "item_id": item_id,
                        "ingest_type": ingest_item.ingest_type.value,
                        "status": "completed",
                    },
                )

                return {
                    "status": "success",
                    "item_id": item_id,
                    "ingest_type": ingest_item.ingest_type.value,
                    **result,
                }

            except Exception as exc:
                # Update status to failed
                db.rollback()
                ingest_item = db.get(IngestQueueItem, item_uuid)
                if ingest_item is not None:
                    ingest_item.status = IngestStatus.failed
                    ingest_item.last_error = str(exc)
                    ingest_item.retry_count = min(ingest_item.retry_count + 1, settings.ingest_max_retries)
                    _audit(db, item_uuid, "ingest.failed", {"error": str(exc)})
                    db.commit()

                logger.error(
                    f"Ingest processing failed: {exc}",
                    extra={
                        "item_id": item_id,
                        "error": str(exc),
                    },
                )

                # Retry if under max retries
                if ingest_item and ingest_item.retry_count < settings.ingest_max_retries:
                    raise self.retry(exc=exc)

                return {
                    "status": "failed",
                    "item_id": item_id,
                    "error": str(exc),
                }

    except Exception as exc:
        logger.exception(f"Unexpected error in process_ingest_item: {exc}")
        raise


def _process_cv_ingest(db: Session, ingest_item: IngestQueueItem) -> dict:
    """Process CV ingestion: create Resume and Assessment."""
    from app.models.resume import Resume

    # Extract text if needed
    if not ingest_item.extracted_text:
        logger.info("Text extraction required for CV ingest")
        # For email attachments, would need the raw content
        # For now, mark as error if no extracted text
        if ingest_item.source == IngestSource.email:
            raise ValueError("Email attachments require pre-extracted text")
        ingest_item.extracted_text = ""

    cv_text = ingest_item.extracted_text or ""

    # Create Resume record
    resume = Resume(
        user_id=None,  # System ingestion
        file_name=ingest_item.source_ref or "ingested_cv",
        raw_narrative=cv_text,
        supplementary={
            "extracted_text": cv_text,
            "agent_ingested": True,
            "ingest_source": ingest_item.source.value,
            "sender_meta": ingest_item.sender_meta,
        },
    )
    db.add(resume)
    db.flush()

    ingest_item.resume_id = resume.id

    # TODO: Auto-match to best open position (if needed)
    # For now, assessments are created via API endpoints

    # Mark as awaiting review if configured
    if settings.ingest_require_approval:
        ingest_item.status = IngestStatus.awaiting_review
    else:
        ingest_item.status = IngestStatus.processing

    db.commit()

    logger.info(
        f"CV ingest processed: created Resume {resume.id}",
        extra={"resume_id": str(resume.id), "ingest_item_id": str(ingest_item.id)},
    )

    return {
        "status": "resume_created",
        "resume_id": str(resume.id),
        "assessment_id": None,
    }


def _process_jd_ingest(db: Session, ingest_item: IngestQueueItem) -> dict:
    """Process JD draft ingestion: improve JD using agent."""

    # Extract text if needed
    if not ingest_item.extracted_text:
        logger.info("Text extraction required for JD ingest")
        ingest_item.extracted_text = ""

    jd_text = ingest_item.extracted_text or ""

    # TODO: Call JD improvement agent (reasoning.improve_jd or similar)
    # For now, just store the draft
    ingest_item.jd_improved_draft = jd_text
    ingest_item.jd_agent_output = {
        "status": "pending",
        "message": "JD improvement not yet implemented",
    }

    ingest_item.status = IngestStatus.awaiting_review

    db.commit()

    logger.info(
        "JD ingest processed and marked for review",
        extra={"ingest_item_id": str(ingest_item.id)},
    )

    return {
        "status": "jd_draft_created",
        "resume_id": None,
        "assessment_id": None,
    }


# ============================================================================
# Email Notification Tasks
# ============================================================================


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # Retry after 60 seconds
)
def send_notification_email(
    self,
    user_id: str,
    notification_id: str,
    recipient_email: str,
    notification_type: str,
    title: str,
    message: str,
    action_url: str = None,
    context: dict = None,
) -> dict:
    """
    Send notification email asynchronously.

    Args:
        user_id: User ID
        notification_id: Notification record ID
        recipient_email: Recipient email address
        notification_type: Type of notification
        title: Email title
        message: Email message
        action_url: Optional action URL
        context: Optional context variables

    Returns:
        Dict with send status
    """
    try:
        import asyncio

        from app.services.email_service import EmailService

        # Both service methods are async; run them to completion inside this
        # synchronous Celery task via asyncio.run (the same idiom used by the
        # other async-backed tasks in this module).
        result = asyncio.run(
            EmailService.send_notification_email(
                recipient_email=recipient_email,
                notification_type=notification_type,
                title=title,
                message=message,
                action_url=action_url,
                context=context or {},
            )
        )

        if result:
            # Mark the notification as email-sent. mark_as_email_sent expects an
            # AsyncSession, so use an async session (NOT the sync one).
            from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

            from app.services.notification_service import NotificationService

            async def _mark_sent() -> None:
                engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True)
                try:
                    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
                    async with factory() as adb:
                        await NotificationService.mark_as_email_sent(
                            db=adb, notification_id=uuid.UUID(notification_id)
                        )
                        await adb.commit()
                finally:
                    await engine.dispose()

            asyncio.run(_mark_sent())

            logger.info(
                f"Notification email sent successfully: {notification_type}",
                extra={
                    "notification_id": notification_id,
                    "user_id": user_id,
                    "recipient": recipient_email,
                },
            )
            return {
                "success": True,
                "notification_id": notification_id,
                "recipient": recipient_email,
            }
        elif EmailService._is_configured():
            # Email IS configured but the send genuinely failed → retry.
            logger.warning(
                f"Email send failed; will retry: {notification_type}",
                extra={"notification_id": notification_id, "recipient": recipient_email},
            )
            raise self.retry(exc=Exception("Email service failed"))
        else:
            # Email intentionally not configured (e.g. local/dev). Skip quietly
            # instead of retrying — a best-effort notification email is optional.
            logger.info(
                "Email service not configured; skipping notification email",
                extra={"notification_id": notification_id, "recipient": recipient_email},
            )
            return {
                "success": False,
                "skipped": True,
                "reason": "email_not_configured",
                "notification_id": notification_id,
            }

    except Exception as exc:
        logger.error(
            f"Error sending notification email: {str(exc)}",
            extra={
                "notification_id": notification_id,
                "user_id": user_id,
                "recipient": recipient_email,
            },
        )
        # Retry up to max_retries times
        raise self.retry(exc=exc)


def _get_sync_session() -> Session:
    """Get a synchronous database session."""
    global _sync_engine, _SyncSessionLocal
    if _sync_engine is None:
        _sync_engine = create_engine(
            _sync_database_url(),
            echo=False,
            pool_size=5,
            max_overflow=5,
        )
        _SyncSessionLocal = sessionmaker(bind=_sync_engine, autocommit=False, autoflush=False)

    return _SyncSessionLocal()


def _invoke_dlq_handler(assessment_id: str, exc: Exception) -> None:
    """Invoke DLQ handler after max retries exhausted.

    Sends assessment to Dead Letter Queue with full error context for:
    - Marking as failed
    - Storing error and context
    - Alerting admins via Slack
    - Logging incident to audit system

    Args:
        assessment_id: UUID string of failed assessment
        exc: The exception that caused failure
    """
    from app.workers.dlq import invoke_dlq

    # Build detailed error context
    context = {
        "retry_count": 2,  # max_retries from run_assessment decorator
        "last_exception": str(exc),
        "traceback": traceback.format_exc(),
        "task_name": "app.workers.tasks.run_assessment",
    }

    # Invoke DLQ handler asynchronously
    try:
        invoke_dlq(assessment_id, str(exc), context, retry=True)
    except Exception as dlq_error:
        # If DLQ invocation fails, log but don't raise — we're already in error state
        logger.error(f"Failed to invoke DLQ handler for {assessment_id}: {dlq_error}", exc_info=True)
