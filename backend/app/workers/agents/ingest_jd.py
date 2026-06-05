"""JD draft ingestion agent — autonomous JD quality review and improvement.

Two entry points called by Celery Beat:

  poll_folder  — scans inbox/jd/ for dropped .txt/.docx/.pdf draft JDs.
  process_draft — public API called directly when a JD draft is submitted via
                  POST /agents/jd/draft (no folder needed for API workflow).

For each discovered JD the agent:
  1. Extracts raw text.
  2. Runs the JD analysis suite (analyze_jd → interrogate_jd → JD_EVOLUTION prompt).
  3. Generates an improved draft that fixes the identified issues.
  4. Scores quality, classifies issues, stores everything in IngestQueueItem.
  5. Snapshots a JD version (Pillar 3 history) if linked to an existing position.
  6. Pushes a notification to recruiter/admin to review the improved draft.
  7. Only creates/updates the Position once the recruiter approves.
"""
from __future__ import annotations

import logging
import pathlib
import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.engines import reasoning
from app.engines.intake import analyze_jd
from app.engines.client import call_claude_json, is_live
from app.models.ingest_queue import IngestQueueItem, IngestSource, IngestStatus, IngestType
from app.models.user import User, UserRole
from app.workers.celery_app import celery_app

logger = logging.getLogger("truematch.agent.jd")

_SUPPORTED_EXTS = {".txt", ".pdf", ".docx"}

_engine = None
_SessionFactory: sessionmaker | None = None


def _db() -> sessionmaker:
    global _engine, _SessionFactory
    if _SessionFactory is None:
        url = settings.database_url.replace("+asyncpg", "+psycopg")
        _engine = create_engine(url, pool_pre_ping=True, future=True)
        _SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False)
    return _SessionFactory


def _improve_jd(jd_text: str, jd_review: dict) -> str:
    """Ask Claude to rewrite the JD fixing the identified issues."""
    if not is_live():
        return f"[MOCK improved draft — live reasoning required]\n\n{jd_text}"
    data = call_claude_json(
        system=(
            "You are a JD improvement agent. Given the original JD and a quality "
            "analysis with identified issues, rewrite the JD to fix all flagged "
            "problems: remove proxy/credential-inflation requirements, clarify "
            "vague scoping, remove exclusionary phrasing, and make the real "
            "business need explicit. Return JSON: "
            "{improved_draft, summary_of_changes[]}."
        ),
        user_content=(
            f"ORIGINAL JD:\n{jd_text}\n\n"
            f"QUALITY ANALYSIS:\n"
            f"Score: {jd_review.get('quality_score')}/100\n"
            f"Issues: {jd_review.get('issues', [])}"
        ),
        max_tokens=3000,
    )
    return data.get("improved_draft") or jd_text


def _process_jd(
    db: Session,
    jd_text: str,
    source: IngestSource,
    source_ref: str,
    position_id: uuid.UUID | None = None,
    title: str | None = None,
) -> IngestQueueItem:
    """Analyse, improve, and store a JD draft."""
    item = IngestQueueItem(
        source=source,
        ingest_type=IngestType.jd_draft,
        status=IngestStatus.extracting,
        source_ref=source_ref,
        extracted_text=jd_text,
        position_id=position_id,
    )
    db.add(item)
    db.flush()

    try:
        # Run the full JD analysis suite.
        item.status = IngestStatus.processing
        db.flush()
        requirements = analyze_jd(jd_text)
        jd_review = reasoning.interrogate_jd(jd_text)
        improved_draft = _improve_jd(jd_text, jd_review)

        item.jd_improved_draft = improved_draft
        item.jd_agent_output = {
            "quality_score": jd_review.get("quality_score"),
            "issues": jd_review.get("issues", []),
            "requirements": requirements,
            "title_hint": title,
        }
        item.status = IngestStatus.awaiting_review
        db.flush()

        # If linked to an existing position, snapshot the version for Pillar 3.
        if position_id:
            _snapshot_version(db, position_id, jd_text, requirements, jd_review)

        _notify_recruiter_jd(db, item, title)
        logger.info(
            "JD agent: processed draft '%s' (quality %s/100, %d issues). "
            "Awaiting human review.",
            source_ref, jd_review.get("quality_score"), len(jd_review.get("issues", [])),
        )
    except Exception as exc:  # noqa: BLE001
        item.status = IngestStatus.failed
        item.last_error = str(exc)
        db.flush()
        logger.error("JD agent failed for %s: %s", source_ref, exc)

    return item


def _snapshot_version(db: Session, position_id: uuid.UUID, jd_text: str,
                       requirements: dict, jd_review: dict) -> None:
    from app.models.jd_version import JDVersion
    from sqlalchemy import func
    count = db.scalar(
        select(func.count()).select_from(JDVersion).where(JDVersion.position_id == position_id)
    ) or 0
    db.add(JDVersion(
        position_id=position_id,
        version=count + 1,
        description=jd_text,
        parsed_requirements=requirements,
        jd_quality_score=jd_review.get("quality_score"),
        jd_issues={"issues": jd_review.get("issues", [])},
    ))
    db.flush()


def _notify_recruiter_jd(db: Session, item: IngestQueueItem, title: str | None) -> None:
    try:
        recruiter = db.scalar(
            select(User).where(User.role.in_([UserRole.recruiter, UserRole.admin]))
        )
        if recruiter:
            logger.info(
                "JD agent: draft '%s' ready for review by %s (item %s)",
                title or "untitled", recruiter.email, item.id,
            )
    except Exception as exc:  # noqa: BLE001
        logger.debug("JD notification skipped: %s", exc)


# ── Folder poller ─────────────────────────────────────────────────────────────

@celery_app.task(name="app.workers.agents.ingest_jd.poll_folder")
def poll_folder() -> dict:
    """Scan inbox/jd/ for dropped JD draft files."""
    folder = pathlib.Path(settings.ingest_jd_folder)
    folder.mkdir(parents=True, exist_ok=True)
    processed, skipped, errors = 0, 0, 0
    for f in folder.iterdir():
        if not f.is_file() or f.name.startswith("."):
            continue
        suffix = f.suffix.lower()
        if suffix not in _SUPPORTED_EXTS:
            skipped += 1
            continue
        try:
            if suffix == ".txt":
                jd_text = f.read_text(encoding="utf-8", errors="replace")
            else:
                from app.engines.extract import extract_text
                jd_text = extract_text(f.read_bytes(), suffix.lstrip("."))
            with _db()() as db:
                _process_jd(db, jd_text, IngestSource.folder, f.name)
                db.commit()
            _move_processed(f)
            processed += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("JD folder file %s failed: %s", f.name, exc)
            errors += 1
    if processed or errors:
        logger.info("JD folder poll: %d processed, %d skipped, %d errors",
                    processed, skipped, errors)
    return {"processed": processed, "skipped": skipped, "errors": errors}


def _move_processed(f: pathlib.Path) -> None:
    done = f.parent / "processed"
    done.mkdir(exist_ok=True)
    dest = done / f.name
    if dest.exists():
        import uuid as _uuid
        dest = done / f"{f.stem}_{_uuid.uuid4().hex[:6]}{f.suffix}"
    f.rename(dest)


# ── Public API entry point ────────────────────────────────────────────────────

@celery_app.task(name="app.workers.agents.ingest_jd.process_draft")
def process_draft(jd_text: str, position_id_str: str | None, title: str | None) -> str:
    """Celery task triggered by POST /agents/jd/draft. Returns the queue item id."""
    pos_id = uuid.UUID(position_id_str) if position_id_str else None
    with _db()() as db:
        item = _process_jd(db, jd_text, IngestSource.api, "api-draft", pos_id, title)
        db.commit()
        return str(item.id)
