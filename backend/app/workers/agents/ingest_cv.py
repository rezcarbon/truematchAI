"""CV ingestion agent — the system's autonomous hiring front door.

Two entry points, both called by Celery Beat:

  poll_folder  — scans the local `inbox/cv/` directory for PDF/DOCX/TXT files
                 and email .eml files dropped there.
  poll_email   — connects to an IMAP mailbox and ingests CV attachments and
                 body text from unread messages.

For each discovered document the agent:
  1. Extracts raw text (via engines/extract.py).
  2. Extracts any cover letter present (second attachment or email body).
  3. Parses the resume (LLM, or deterministic if no key).
  4. Auto-matches the best open position from the corpus using TF-IDF similarity.
  5. Creates a Resume + IngestQueueItem in the DB.
  6. Either enqueues run_assessment.delay() immediately, or marks the item
     `awaiting_review` if INGEST_REQUIRE_APPROVAL=true.
  7. Emits a push notification to the recruiter/admin.

The ingest_queue row is the audit record for every autonomous action.
"""
from __future__ import annotations

import email
import imaplib
import logging
import pathlib
import uuid
from email.message import Message
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.engines import intake, text_utils
from app.models.ingest_queue import IngestQueueItem, IngestSource, IngestStatus, IngestType
from app.models.position import Position, PositionStatus
from app.models.resume import Resume
from app.models.user import User, UserRole
from app.workers.celery_app import celery_app

logger = logging.getLogger("truematch.agent.cv")

_SUPPORTED_EXTS = {".pdf", ".docx", ".txt", ".doc"}
_CONTENT_TYPE_MAP = {"application/pdf": "pdf",
                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
                     "text/plain": "txt"}

# ── DB ──────────────────────────────────────────────────────────────────────

_engine = None
_SessionFactory: sessionmaker | None = None


def _db() -> sessionmaker:
    global _engine, _SessionFactory
    if _SessionFactory is None:
        url = settings.database_url.replace("+asyncpg", "+psycopg")
        _engine = create_engine(url, pool_pre_ping=True, future=True)
        _SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False)
    return _SessionFactory


# ── Matching ─────────────────────────────────────────────────────────────────

def _best_position(db: Session, resume_text: str) -> Position | None:
    """Return the open position whose JD text best matches the CV (TF overlap)."""
    positions = db.scalars(
        select(Position).where(Position.status == PositionStatus.open).limit(50)
    ).all()
    if not positions:
        return None
    resume_terms = set(text_utils.term_frequencies(resume_text).keys())
    best_pos, best_score = None, 0.0
    for p in positions:
        jd_tf = text_utils.term_frequencies(p.description or "")
        if not jd_tf:
            continue
        overlap = sum(w for t, w in jd_tf.items() if t in resume_terms)
        score = overlap / sum(jd_tf.values())
        if score > best_score:
            best_score, best_pos = score, p
    return best_pos


# ── System user ───────────────────────────────────────────────────────────────

def _system_user(db: Session) -> User:
    """Return or create a system agent user for programmatic candidates."""
    user = db.scalar(select(User).where(User.email == "agent@truematch.system"))
    if user is None:
        user = User(email="agent@truematch.system", role=UserRole.candidate,
                    display_name="TrueMatch Ingest Agent")
        db.add(user)
        db.flush()
    return user


# ── Core processor ───────────────────────────────────────────────────────────

def _process_cv(
    db: Session,
    raw_bytes: bytes,
    file_type: str,
    source: IngestSource,
    source_ref: str,
    cover_letter_text: str | None = None,
    sender_meta: dict | None = None,
) -> IngestQueueItem:
    """Extract, match, create records, enqueue — returns the queue item."""
    from app.engines.extract import ExtractionError, extract_text

    item = IngestQueueItem(
        source=source,
        ingest_type=IngestType.cv,
        status=IngestStatus.extracting,
        source_ref=source_ref,
        sender_meta=sender_meta,
    )
    db.add(item)
    db.flush()

    try:
        cv_text = extract_text(raw_bytes, file_type)
        item.extracted_text = cv_text
        item.cover_letter_text = cover_letter_text
    except ExtractionError as exc:
        item.status = IngestStatus.failed
        item.last_error = str(exc)
        db.flush()
        logger.warning("CV extraction failed (%s): %s", source_ref, exc)
        return item

    # Parse resume to get skills / experience for matching.
    item.status = IngestStatus.matching
    db.flush()
    try:
        parsed = intake.parse_resume(cv_text, {})
    except Exception as exc:  # noqa: BLE001
        parsed = {}
        logger.warning("Resume parse failed during matching: %s", exc)

    # Auto-match to best open position.
    position = _best_position(db, cv_text)

    # Build supplementary payload.
    supplementary: dict[str, Any] = {
        "extracted_text": cv_text,
        "agent_ingested": True,
        "source": source.value,
    }
    if cover_letter_text:
        supplementary["additional_context"] = f"Cover letter:\n{cover_letter_text[:3000]}"
    if sender_meta:
        supplementary["sender_name"] = sender_meta.get("name", "")

    # Create a Resume record owned by the system agent user.
    system_user = _system_user(db)
    resume = Resume(
        user_id=system_user.id,
        file_id=None,
        file_type=file_type,
        supplementary=supplementary,
        raw_narrative=parsed.get("narrative"),
        parsed_data=parsed,
    )
    db.add(resume)
    db.flush()
    item.resume_id = resume.id

    if position:
        item.position_id = position.id

    if settings.ingest_require_approval:
        item.status = IngestStatus.awaiting_review
        logger.info("CV queued for review (ingest_require_approval=true): %s", item.id)
    else:
        item.status = IngestStatus.processing
        _enqueue(item, resume.id, position)

    db.flush()
    _notify_recruiter(db, item, position)
    return item


def _enqueue(item: IngestQueueItem, resume_id: uuid.UUID, position: Position | None) -> None:
    if position is None:
        logger.info("No open position matched for ingest item %s — holding.", item.id)
        item.status = IngestStatus.awaiting_review
        return
    from app.models.assessment import Assessment

    with _db()() as db2:
        system_user = _system_user(db2)
        assessment = Assessment(
            resume_id=resume_id, position_id=position.id, user_id=system_user.id
        )
        db2.add(assessment)
        db2.flush()
        item.assessment_id = assessment.id
        db2.commit()
        from app.workers.tasks import run_assessment
        run_assessment.delay(str(assessment.id))


def _notify_recruiter(db: Session, item: IngestQueueItem, position: Position | None) -> None:
    """Push a notification to any recruiter/admin in the system."""
    try:
        from app.models.user import UserRole
        recruiter = db.scalar(select(User).where(User.role.in_([UserRole.recruiter, UserRole.admin])))
        if not recruiter:
            return
        # Notification payload is stored as an audit event; APNs delivery happens
        # via the real push system. Here we log the intent — the full APNs path
        # requires the running push server (addressed in the push-notification layer).
        logger.info(
            "Agent: CV ingested [%s] → position '%s'. Recruiter notified: %s",
            item.id, position.title if position else "unmatched", recruiter.email,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Recruiter notification skipped: %s", exc)


# ── Cover letter extraction ───────────────────────────────────────────────────

def _extract_cover_letter(msg: Message) -> str | None:
    """Extract the email body as a cover letter (text/plain part)."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode("utf-8", errors="replace")[:4000]
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode("utf-8", errors="replace")[:4000]
    return None


# ── Folder poller ─────────────────────────────────────────────────────────────

@celery_app.task(name="app.workers.agents.ingest_cv.poll_folder")
def poll_folder() -> dict:
    """Scan inbox/cv/ for new documents and process them."""
    folder = pathlib.Path(settings.ingest_cv_folder)
    folder.mkdir(parents=True, exist_ok=True)
    processed, skipped, errors = 0, 0, 0
    files = [f for f in folder.iterdir() if f.is_file() and not f.name.startswith(".")]
    for f in files:
        suffix = f.suffix.lower()
        if suffix == ".eml":
            # Email dropped as a file — parse as email message.
            try:
                with open(f, "rb") as fh:
                    msg = email.message_from_bytes(fh.read())
                _process_eml_file(f, msg)
                f.rename(f.parent / "processed" / f.name)
                processed += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to process .eml %s: %s", f.name, exc)
                errors += 1
        elif suffix in _SUPPORTED_EXTS:
            try:
                raw = f.read_bytes()
                file_type = suffix.lstrip(".")
                with _db()() as db:
                    _process_cv(db, raw, file_type, IngestSource.folder, str(f.name))
                    db.commit()
                _move_processed(f)
                processed += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to process CV file %s: %s", f.name, exc)
                errors += 1
        else:
            skipped += 1
    if processed or errors:
        logger.info("CV folder poll: %d processed, %d skipped, %d errors", processed, skipped, errors)
    return {"processed": processed, "skipped": skipped, "errors": errors}


def _move_processed(f: pathlib.Path) -> None:
    done = f.parent / "processed"
    done.mkdir(exist_ok=True)
    dest = done / f.name
    if dest.exists():
        dest = done / f"{f.stem}_{uuid.uuid4().hex[:6]}{f.suffix}"
    f.rename(dest)


def _process_eml_file(path: pathlib.Path, msg: Message) -> None:
    cover = _extract_cover_letter(msg)
    sender = email.utils.parseaddr(msg.get("From", ""))
    sender_meta = {"name": sender[0], "email": sender[1]}
    for part in msg.walk():
        fn = part.get_filename()
        if not fn:
            continue
        suffix = pathlib.Path(fn).suffix.lower()
        if suffix not in _SUPPORTED_EXTS:
            continue
        raw = part.get_payload(decode=True) or b""
        file_type = suffix.lstrip(".")
        with _db()() as db:
            _process_cv(db, raw, file_type, IngestSource.folder,
                        str(path.name), cover, sender_meta)
            db.commit()


# ── Email (IMAP) poller ───────────────────────────────────────────────────────

@celery_app.task(name="app.workers.agents.ingest_cv.poll_email")
def poll_email() -> dict:
    """Poll IMAP inbox for unread messages containing CV attachments."""
    if not settings.ingest_imap_host:
        return {"skipped": "IMAP not configured"}

    processed, errors = 0, 0
    try:
        imap = imaplib.IMAP4_SSL(settings.ingest_imap_host, settings.ingest_imap_port)
        imap.login(settings.ingest_imap_user, settings.ingest_imap_password)
        imap.select(settings.ingest_imap_folder)
        _, data = imap.search(None, "UNSEEN")
        msg_ids = data[0].split() if data[0] else []
        for mid in msg_ids:
            try:
                _, msg_data = imap.fetch(mid, "(RFC822)")
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                cover = _extract_cover_letter(msg)
                sender = email.utils.parseaddr(msg.get("From", ""))
                sender_meta = {"name": sender[0], "email": sender[1]}
                found_cv = False
                for part in msg.walk():
                    fn = part.get_filename()
                    if not fn:
                        continue
                    suffix = pathlib.Path(fn).suffix.lower()
                    if suffix not in _SUPPORTED_EXTS:
                        continue
                    raw = part.get_payload(decode=True) or b""
                    file_type = suffix.lstrip(".")
                    with _db()() as db:
                        _process_cv(db, raw, file_type, IngestSource.email,
                                    f"imap:{mid.decode()}", cover, sender_meta)
                        db.commit()
                    found_cv = True
                if found_cv:
                    # Mark as seen so we don't reprocess.
                    imap.store(mid, "+FLAGS", "\\Seen")
                    processed += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("IMAP message %s failed: %s", mid, exc)
                errors += 1
        imap.logout()
    except Exception as exc:  # noqa: BLE001
        logger.error("IMAP connection failed: %s", exc)
        errors += 1

    if processed or errors:
        logger.info("CV email poll: %d processed, %d errors", processed, errors)
    return {"processed": processed, "errors": errors}
