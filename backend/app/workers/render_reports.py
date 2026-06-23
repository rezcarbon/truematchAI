"""Auto-render candidate + recruiter PDFs when an assessment completes.

Closes the concierge loop: instead of an operator running a report script by
hand, a completed assessment drops finished PDFs into ``auto_report_output_dir``
(local disk, or an S3 bucket when configured) for the operator to send back.

Triggered from ``run_assessment`` on completion. Rendering is best-effort and
fully isolated — a report failure never affects the assessment result.
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.config import settings
from app.models.assessment import Assessment
from app.models.position import Position
from app.models.resume import Resume
from app.services.report_render import render_reports
from app.workers.agents.ingest_cv import _db  # shared sync sessionmaker factory
from app.workers.celery_app import celery_app

logger = logging.getLogger("truematch.report")


def _candidate_name(resume: Resume | None) -> str:
    if resume is None:
        return "Candidate"
    parsed = resume.parsed_data or {}
    name = (parsed.get("name") or parsed.get("full_name") or "").strip()
    if not name:
        supp = resume.supplementary or {}
        name = (supp.get("sender_name") or "").strip()
    return name or "Candidate"


def _deposit(assessment_id: str, pdfs: dict[str, bytes]) -> list[str]:
    """Write the PDFs to the configured sink. Returns the locations written."""
    written: list[str] = []
    if settings.s3_enabled:  # object storage when configured (volume / multi-worker)
        import boto3

        s3 = boto3.client("s3", region_name=getattr(settings, "aws_region", None) or None)
        for kind, data in pdfs.items():
            key = f"reports/{assessment_id}/{kind}.pdf"
            extra = {"ContentType": "application/pdf", "ServerSideEncryption": "AES256"}
            if getattr(settings, "s3_kms_key_id", ""):
                extra = {"ContentType": "application/pdf", "ServerSideEncryption": "aws:kms",
                         "SSEKMSKeyId": settings.s3_kms_key_id}
            s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=data, **extra)
            written.append(f"s3://{settings.s3_bucket}/{key}")
        return written

    out = Path(settings.auto_report_output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for kind, data in pdfs.items():
        path = out / f"{assessment_id}_{kind}.pdf"
        path.write_bytes(data)
        written.append(str(path))
    return written


@celery_app.task(name="app.workers.render_reports.render_assessment_reports")
def render_assessment_reports(assessment_id: str) -> dict:
    """Render + deposit the candidate/recruiter PDFs for a finished assessment."""
    if not settings.auto_report_enabled:
        return {"status": "disabled"}
    session = _db()
    with session() as db:
        a = db.get(Assessment, assessment_id)
        if a is None:
            return {"status": "not_found"}
        if a.capability_score is None:  # pipeline didn't produce a verdict (failed run)
            return {"status": "skipped_no_verdict"}
        resume = db.get(Resume, a.resume_id) if a.resume_id else None
        position = db.get(Position, a.position_id) if a.position_id else None
        source_language = getattr(resume, "source_language", None) if resume else None
        target = (position.title if position else None) or "this role"
        try:
            pdfs = render_reports(
                a,
                candidate_name=_candidate_name(resume),
                target_title=target,
                source_language=source_language,
            )
            locations = _deposit(str(a.id), pdfs)
        except Exception as exc:  # noqa: BLE001 - report failures must not affect the assessment
            logger.error("Auto-report rendering failed for %s: %s", assessment_id, exc, exc_info=True)
            return {"status": "error", "error": str(exc)}
    logger.info("Auto-report generated for %s -> %s", assessment_id, locations)
    return {"status": "ok", "written": locations}
