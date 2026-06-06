"""Assessment pipeline Celery tasks.

Pipeline: intake (parse resume + analyze JD + traditional simulation)
       -> reasoning (capability + trajectory + JD interrogation + counter-rec)
       -> governance (coherence, consistency, fidelity, bias)
       -> compile + audit.

The worker uses a synchronous SQLAlchemy session derived from the configured
async DATABASE_URL. The Claude-dependent engine calls currently return MOCK
data (see engines/*); swap points are marked `# TODO(live-claude)` there.
"""
from __future__ import annotations

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.core.governance import GovernanceConfig, get_governance_config
from app.engines import (
    corpus,
    enrichment,
    governance_engine,
    intake,
    reasoning,
    semantic_match,
    substitution,
    text_utils,
)
from app.core import provenance, scoring
from app.models.assessment import Assessment, AssessmentStatus
from app.models.audit import AuditTrail
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
    """Run the full assessment pipeline for a single assessment id."""
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

            result = _execute_pipeline(db, assessment, resume, position, governance_cfg)
            if result.get("governance_review_required"):
                assessment.status = AssessmentStatus.flagged_for_review
            else:
                assessment.status = AssessmentStatus.completed
            _audit(
                db,
                aid,
                "pipeline.completed",
                {
                    "score_delta": assessment.score_delta,
                    "status": assessment.status.value,
                    "governed": result.get("governed"),
                },
            )
            db.commit()
            return {"status": assessment.status.value, "assessment_id": assessment_id, **result}

        except Exception as exc:  # noqa: BLE001
            db.rollback()
            assessment = db.get(Assessment, aid)
            if assessment is not None:
                assessment.status = AssessmentStatus.failed
                _audit(db, aid, "pipeline.failed", {"error": str(exc)})
                db.commit()
            logger.exception("Assessment pipeline failed for %s", assessment_id)
            raise


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
    source_text = supplementary.get("extracted_text") or resume.raw_narrative or ""
    # Reproducibility manifest (input hashes + model/prompt/engine versions),
    # recorded before any reasoning runs — the anchor of the audit record.
    _audit(db, aid, "pipeline.provenance", provenance.build_manifest(source_text, position.description))
    if resume.parsed_data:
        parsed_resume = resume.parsed_data
    else:
        parsed_resume = intake.parse_resume(source_text, supplementary)
        # Persist the faithful narrative summary the parser produced.
        narrative = parsed_resume.get("narrative")
        if narrative:
            resume.raw_narrative = narrative
    requirements = position.parsed_requirements or intake.analyze_jd(position.description or "")
    jd_text = position.description or ""
    raw_narrative = resume.raw_narrative
    # IDF weights from the accumulating JD corpus — read on the MAIN thread before
    # the parallel block (the DB session is not thread-safe).
    idf = corpus.idf_map(db, set(text_utils.term_frequencies(jd_text).keys()))

    # --- Parallel fan-out --------------------------------------------------
    # Independent engines run CONCURRENTLY: the deterministic keyword + semantic
    # matchers (instant, no LLM), trajectory + JD-interrogation (LLM), and the
    # enrichment -> substitution -> capability chain (network + LLM). Every engine
    # is a pure function with no DB access, so this is thread-safe; the DB writes
    # all happen below on the main thread.
    def _evidence_chain():
        ev = enrichment.enrich_supplementary(supplementary)
        subs = substitution.build_substitution_profile(
            requirements.get("proxies"), parsed_resume, ev
        )
        cap_ = reasoning.assess_capability(requirements, parsed_resume, raw_narrative, ev, subs)
        return ev, subs, cap_

    with ThreadPoolExecutor(max_workers=5) as ex:
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

    # --- 3. Governance -----------------------------------------------------
    # A run is "governed" only when operational (real, numeric) gate values are
    # present. With placeholder config, gates cannot be evaluated and the result
    # is recorded as ungoverned rather than falsely marked as passing.
    governed = governance_cfg is not None and governance_cfg.is_operational()
    assessment_view = {
        "capability_score": cap,
        "components": capability.get("components"),
        "narrative": capability.get("narrative"),
    }
    if governed:
        assessment.governance_coherence = governance_engine.check_coherence(
            assessment_view, governance_cfg
        )
        assessment.governance_consistency = governance_engine.check_consistency(
            assessment_view, governance_cfg
        )
        assessment.governance_fidelity = governance_engine.check_fidelity(
            parsed_resume, assessment_view, governance_cfg
        )
    # Bias scan is qualitative and always runs.
    assessment.governance_bias_flags = governance_engine.check_bias(parsed_resume, assessment_view)

    coherence_passed = _passed(assessment.governance_coherence)
    consistency_passed = _passed(assessment.governance_consistency)
    fidelity_passed = _passed(assessment.governance_fidelity)
    # Mandatory gate: any explicit failure on a governed run routes to human
    # review. Governance cannot be bypassed.
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
    from app.engines.extract import extract_text
    from app.models.resume import Resume
    from app.models.assessment import Assessment, AssessmentStatus

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
    from app.models.position import Position

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
        f"JD ingest processed and marked for review",
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
        from app.services.email_service import EmailService

        # Send email
        result = celery_app.sync(EmailService.send_notification_email)(
            recipient_email=recipient_email,
            notification_type=notification_type,
            title=title,
            message=message,
            action_url=action_url,
            context=context or {},
        )

        if result:
            # Update notification record with email sent status
            db = _get_sync_session()
            try:
                from app.services.notification_service import NotificationService

                # Mark as email sent
                celery_app.sync(NotificationService.mark_as_email_sent)(
                    db=db,
                    notification_id=uuid.UUID(notification_id),
                )

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
            finally:
                db.close()
        else:
            logger.warning(
                f"Email service returned failure: {notification_type}",
                extra={
                    "notification_id": notification_id,
                    "recipient": recipient_email,
                },
            )
            # Retry
            raise self.retry(exc=Exception("Email service failed"))

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
