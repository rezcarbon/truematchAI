"""Google Drive ingestion agent.

Polls a configured Google Drive folder where **each candidate submission is a
subfolder** containing one CV and one JD (explicit pairing — no auto-matching).
New submissions are pulled, paired, and run through the standard assessment
pipeline (Resume + Position + Assessment → ``run_assessment``), exactly like a
paid self-assessment, but sourced from cloud storage instead of an upload form.

Design notes
------------
* **Disabled-safe:** if ``drive_ingest_enabled`` is false or no folder/token is
  configured, the poll task is a no-op (mirrors the enrichment engine). Nothing
  is fetched and nothing fails.
* **Idempotent:** each submission subfolder id is recorded as the ingest item's
  ``source_ref``; a folder already ingested is skipped on the next poll.
* **Provider-isolated:** all Drive REST access lives in ``DriveClient`` so the
  pipeline logic is unit-testable with a fake client and carries no Google SDK
  dependency (plain Drive v3 REST over httpx + a bearer token).
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.assessment import Assessment
from app.models.ingest_queue import IngestQueueItem, IngestSource, IngestStatus, IngestType
from app.models.position import Position, PositionStatus
from app.models.resume import Resume
from app.workers.agents.ingest_cv import _db, _system_user
from app.workers.celery_app import celery_app

logger = logging.getLogger("truematch.agent.drive")

_DRIVE_API = "https://www.googleapis.com/drive/v3"
# Filename hints used to tell the CV apart from the JD inside a submission folder.
_JD_HINTS = ("jd", "job", "position", "role", "vacancy")
_CV_HINTS = ("cv", "resume", "résumé", "curriculum")


class DriveClient:
    """Thin Google Drive v3 REST client (list + download) over a bearer token.

    Kept deliberately small and side-effect-isolated so the ingestion pipeline can
    be tested with a fake implementing the same three methods.
    """

    def __init__(self, access_token: str):
        self._token = access_token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    def list_children(self, folder_id: str, *, folders_only: bool = False) -> list[dict[str, Any]]:
        import httpx

        q = f"'{folder_id}' in parents and trashed = false"
        if folders_only:
            q += " and mimeType = 'application/vnd.google-apps.folder'"
        with httpx.Client(timeout=30) as c:
            r = c.get(
                f"{_DRIVE_API}/files",
                headers=self._headers(),
                params={"q": q, "fields": "files(id,name,mimeType)", "pageSize": 1000},
            )
            r.raise_for_status()
            return r.json().get("files", [])

    def download(self, file_id: str) -> bytes:
        import httpx

        with httpx.Client(timeout=60) as c:
            r = c.get(
                f"{_DRIVE_API}/files/{file_id}",
                headers=self._headers(),
                params={"alt": "media"},
            )
            r.raise_for_status()
            return r.content


def _ext_for(name: str, mime: str) -> str:
    """Best-effort file type from name/mime for the extractor."""
    lower = name.lower()
    for ext in ("pdf", "docx", "doc", "txt", "md", "rtf"):
        if lower.endswith("." + ext):
            return ext
    if "pdf" in mime:
        return "pdf"
    if "word" in mime or "document" in mime:
        return "docx"
    return "txt"


def _classify(files: list[dict[str, Any]]) -> tuple[dict | None, dict | None]:
    """Return (cv_file, jd_file) from a submission folder's files by name hints.

    Falls back sensibly: if only hints identify one role, the other file takes the
    remaining slot; ties broken so the CV is the non-JD document.
    """
    docs = [f for f in files if f.get("mimeType") != "application/vnd.google-apps.folder"]
    jd = next((f for f in docs if any(h in f["name"].lower() for h in _JD_HINTS)), None)
    cv = next(
        (f for f in docs if any(h in f["name"].lower() for h in _CV_HINTS) and f is not jd),
        None,
    )
    remaining = [f for f in docs if f is not jd and f is not cv]
    if cv is None and remaining:
        cv = remaining.pop(0)
    if jd is None and remaining:
        jd = remaining.pop(0)
    return cv, jd


def _already_ingested(db: Session, source_ref: str) -> bool:
    # Dedup on Position.external_ref (a plain, indexable column). IngestQueueItem
    # .source_ref is EncryptedText and cannot be filtered on, so the created
    # Position carries the submission id as its external_ref.
    return db.scalar(
        select(Position.id).where(Position.external_ref == source_ref).limit(1)
    ) is not None


def process_submission(
    db: Session,
    *,
    submission_ref: str,
    cv_bytes: bytes,
    cv_type: str,
    jd_bytes: bytes,
    jd_type: str,
    submitter_name: str | None = None,
) -> IngestQueueItem:
    """Pair one CV + one JD into a queued assessment (explicit pairing).

    Mirrors the paid self-assessment flow: extract CV, read JD, create
    Resume + Position + Assessment, enqueue ``run_assessment``.
    """
    from app.engines.extract import ExtractionError, extract_text
    from app.engines import intake

    item = IngestQueueItem(
        source=IngestSource.cloud_drive,
        ingest_type=IngestType.cv,
        status=IngestStatus.extracting,
        source_ref=submission_ref,
        sender_meta={"name": submitter_name} if submitter_name else None,
    )
    db.add(item)
    db.flush()

    try:
        cv_text = extract_text(cv_bytes, cv_type)
        jd_text = extract_text(jd_bytes, jd_type)
    except ExtractionError as exc:
        item.status = IngestStatus.failed
        item.last_error = str(exc)
        db.flush()
        logger.warning("Drive submission extraction failed (%s): %s", submission_ref, exc)
        return item

    if not (cv_text or "").strip() or not (jd_text or "").strip():
        item.status = IngestStatus.failed
        item.last_error = "Empty CV or JD text after extraction."
        db.flush()
        return item

    item.extracted_text = cv_text
    item.status = IngestStatus.matching
    db.flush()

    try:
        parsed = intake.parse_resume(cv_text, {})
    except Exception as exc:  # noqa: BLE001 - parsing is best-effort for matching
        parsed = {}
        logger.warning("Resume parse failed for Drive submission %s: %s", submission_ref, exc)

    system_user = _system_user(db)
    resume = Resume(
        user_id=system_user.id,
        file_id=None,
        file_type=cv_type,
        supplementary={
            "extracted_text": cv_text,
            "agent_ingested": True,
            "source": IngestSource.cloud_drive.value,
        },
        raw_narrative=parsed.get("narrative"),
        parsed_data=parsed,
    )
    db.add(resume)
    db.flush()

    # Explicit pairing: the JD that arrived with the CV becomes the position.
    position = Position(
        company_id=None,
        created_by=system_user.id,
        title=(submitter_name and f"Drive submission — {submitter_name}") or "Drive submission",
        description=jd_text,
        status=PositionStatus.open,
        external_ref=submission_ref,  # dedup key for idempotent re-polls
    )
    db.add(position)
    db.flush()

    assessment = Assessment(resume_id=resume.id, position_id=position.id, user_id=system_user.id)
    db.add(assessment)
    db.flush()

    item.resume_id = resume.id
    item.position_id = position.id
    item.assessment_id = assessment.id

    if settings.ingest_require_approval:
        item.status = IngestStatus.awaiting_review
        db.flush()
        logger.info("Drive submission queued for review (ingest_require_approval): %s", item.id)
        return item

    item.status = IngestStatus.processing
    db.flush()
    from app.workers.tasks import run_assessment

    run_assessment.delay(str(assessment.id))
    logger.info("Drive submission %s -> assessment %s enqueued", submission_ref, assessment.id)
    return item


def _poll(db: Session, client: DriveClient, folder_id: str) -> int:
    """Pull new submissions from the Drive folder. Returns count processed."""
    processed = 0
    submissions = client.list_children(folder_id, folders_only=True)
    for sub in submissions:
        ref = f"gdrive:{sub['id']}"
        if _already_ingested(db, ref):
            continue
        files = client.list_children(sub["id"])
        cv, jd = _classify(files)
        if cv is None or jd is None:
            logger.info("Drive submission %s missing CV or JD; skipping", sub["name"])
            continue
        try:
            cv_bytes = client.download(cv["id"])
            jd_bytes = client.download(jd["id"])
        except Exception as exc:  # noqa: BLE001 - one bad submission must not stop the poll
            logger.warning("Drive download failed for %s: %s", sub["name"], exc)
            continue
        process_submission(
            db,
            submission_ref=ref,
            cv_bytes=cv_bytes,
            cv_type=_ext_for(cv["name"], cv.get("mimeType", "")),
            jd_bytes=jd_bytes,
            jd_type=_ext_for(jd["name"], jd.get("mimeType", "")),
            submitter_name=sub["name"],
        )
        db.flush()  # make this submission visible to the next iteration's idempotency check
        processed += 1
    return processed


@celery_app.task(name="app.workers.agents.ingest_drive.poll_drive")
def poll_drive() -> dict[str, Any]:
    """Celery beat entrypoint: poll the configured Drive folder for new submissions."""
    if not settings.drive_ingest_enabled:
        return {"status": "disabled"}
    if not (settings.drive_ingest_folder_id and settings.drive_ingest_access_token):
        logger.warning("Drive ingestion enabled but folder id / access token not configured.")
        return {"status": "unconfigured"}

    client = DriveClient(settings.drive_ingest_access_token)
    session = _db()
    with session() as db:
        try:
            n = _poll(db, client, settings.drive_ingest_folder_id)
            db.commit()
        except Exception as exc:  # noqa: BLE001 - never let a poll crash the worker
            db.rollback()
            logger.error("Drive poll failed: %s", exc, exc_info=True)
            return {"status": "error", "error": str(exc)}
    return {"status": "ok", "processed": n}
