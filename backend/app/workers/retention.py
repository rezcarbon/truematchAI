"""Data lifecycle and compliance tasks for retention and DSAR processing.

This module implements Celery tasks for:
1. Automated data retention policy enforcement (daily sweep)
2. Data Subject Access Requests (DSAR) export and deletion
3. Compliance tombstone creation for audit trails

All tasks run synchronously with the configured database.
"""
from __future__ import annotations

import io
import json
import logging
import uuid
import zipfile
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.assessment import Assessment
from app.models.audit import AuditTrail
from app.models.dsar import DSARRequest, DSARStatus
from app.models.resume import Resume
from app.models.user import User
from app.workers.celery_app import celery_app

logger = logging.getLogger("truematch.retention")

# Synchronous database session factory (shared with tasks.py pattern)
_sync_engine = None
_SyncSessionLocal: sessionmaker[Session] | None = None


def _sync_database_url() -> str:
    """Derive a synchronous SQLAlchemy URL from the configured async URL."""
    url = settings.database_url
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg")
    return url


def _session_factory() -> sessionmaker[Session]:
    """Get or create synchronous session factory."""
    global _sync_engine, _SyncSessionLocal
    if _SyncSessionLocal is None:
        _sync_engine = create_engine(_sync_database_url(), pool_pre_ping=True, future=True)
        _SyncSessionLocal = sessionmaker(bind=_sync_engine, expire_on_commit=False)
    return _SyncSessionLocal


def _audit_compliance(db: Session, dsar_id: uuid.UUID | None, event_type: str, data: dict) -> None:
    """Create compliance audit trail entry for DSAR processing."""
    entry = AuditTrail(
        assessment_id=None,  # DSAR events are not tied to specific assessments
        event_type=event_type,
        event_data=data,
        actor_type="system",
    )
    db.add(entry)
    db.flush()


# ============================================================================
# Data Retention Policy Enforcement
# ============================================================================


@celery_app.task(
    name="app.workers.retention.retention_daily_sweep",
    bind=True,
    max_retries=1,
)
def retention_daily_sweep(self) -> dict:
    """
    Daily automated data retention sweep.

    Deletes assessments and associated candidate data older than the configured
    retention period (default 30 days). This task enforces the data minimization
    principle and reduces storage costs.

    Schedule: Daily at 02:00 UTC via Celery Beat

    Returns:
        Dict with deletion counts and status
    """
    try:
        with _session_factory()() as db:
            # Calculate retention cutoff (default 30 days ago)
            retention_days = getattr(settings, "data_retention_days", 30)
            cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

            logger.info(
                f"Starting retention sweep with cutoff: {cutoff.isoformat()}",
                extra={"retention_days": retention_days},
            )

            # Count existing assessments that will be deleted
            stmt_count = select(Assessment).where(Assessment.created_at < cutoff)
            old_assessments = db.scalars(stmt_count).all()
            assessment_count = len(old_assessments)

            if assessment_count == 0:
                logger.info("No assessments to delete - data within retention period")
                return {
                    "status": "success",
                    "assessments_deleted": 0,
                    "cutoff_date": cutoff.isoformat(),
                }

            # Delete all assessments older than cutoff (cascade deletes related audit records)
            delete_stmt = delete(Assessment).where(Assessment.created_at < cutoff)
            result = db.execute(delete_stmt)
            deleted_count = result.rowcount
            db.commit()

            # Log compliance record
            _audit_compliance(
                db,
                None,
                "retention.sweep_completed",
                {
                    "cutoff_date": cutoff.isoformat(),
                    "retention_days": retention_days,
                    "assessments_deleted": deleted_count,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            db.commit()

            logger.info(
                f"Retention sweep completed: deleted {deleted_count} assessments",
                extra={
                    "assessments_deleted": deleted_count,
                    "cutoff_date": cutoff.isoformat(),
                    "retention_days": retention_days,
                },
            )

            return {
                "status": "success",
                "assessments_deleted": deleted_count,
                "cutoff_date": cutoff.isoformat(),
                "retention_days": retention_days,
            }

    except Exception as exc:
        logger.exception(f"Retention sweep failed: {exc}")
        raise self.retry(exc=exc, countdown=300)  # Retry in 5 minutes


# ============================================================================
# DSAR Export (Data Subject Access Request - Article 15)
# ============================================================================


@celery_app.task(
    name="app.workers.retention.export_dsar_data",
    bind=True,
    max_retries=2,
)
def export_dsar_data(self, dsar_id: str) -> dict:
    """
    Export all user data for a Data Subject Access Request (GDPR Article 15).

    Collects all personal data associated with the user, packages it as JSON
    in a ZIP file, uploads to S3, and sends a secure download link to the user.

    Args:
        dsar_id: UUID of DSARRequest record

    Returns:
        Dict with export status and S3 URL

    Raises:
        Exception: If export or upload fails (retryable)
    """
    try:
        dsar_uuid = uuid.UUID(dsar_id)
        with _session_factory()() as db:
            # Fetch DSAR request and user
            dsar = db.get(DSARRequest, dsar_uuid)
            if not dsar:
                logger.error(f"DSAR request {dsar_id} not found")
                return {"status": "not_found", "dsar_id": dsar_id}

            user = db.get(User, dsar.user_id)
            if not user:
                logger.error(f"User {dsar.user_id} not found for DSAR {dsar_id}")
                return {"status": "user_not_found", "dsar_id": dsar_id}

            logger.info(
                f"Starting DSAR export for user {dsar.user_id}",
                extra={"dsar_id": dsar_id, "user_id": str(dsar.user_id)},
            )

            # Update status to processing
            dsar.status = DSARStatus.processing
            db.commit()
            _audit_compliance(
                db,
                dsar_uuid,
                "dsar.export_started",
                {"user_id": str(dsar.user_id), "request_type": dsar.request_type},
            )
            db.commit()

            # Collect all user data
            data_export = {
                "export_date": datetime.now(timezone.utc).isoformat(),
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "role": user.role.value,
                    "display_name": user.display_name,
                    "location": user.location,
                    "headline": user.headline,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                },
                "assessments": [],
                "resumes": [],
                "audit_trail": [],
            }

            # Fetch all assessments for the user
            assessments_stmt = select(Assessment).where(Assessment.user_id == dsar.user_id)
            assessments = db.scalars(assessments_stmt).all()
            for assessment in assessments:
                data_export["assessments"].append({
                    "id": str(assessment.id),
                    "resume_id": str(assessment.resume_id),
                    "position_id": str(assessment.position_id),
                    "status": assessment.status.value,
                    "traditional_score": assessment.traditional_score,
                    "semantic_score": assessment.semantic_score,
                    "capability_score": assessment.capability_score,
                    "counter_rec_triggered": assessment.counter_rec_triggered,
                    "created_at": assessment.created_at.isoformat() if assessment.created_at else None,
                    "updated_at": assessment.updated_at.isoformat() if assessment.updated_at else None,
                })

            # Fetch all resumes for the user
            resumes_stmt = select(Resume).where(Resume.user_id == dsar.user_id)
            resumes = db.scalars(resumes_stmt).all()
            for resume in resumes:
                data_export["resumes"].append({
                    "id": str(resume.id),
                    "file_id": resume.file_id,
                    "file_type": resume.file_type,
                    "created_at": resume.created_at.isoformat() if resume.created_at else None,
                    "updated_at": resume.updated_at.isoformat() if resume.updated_at else None,
                    "note": "Resume content encrypted at rest; metadata only",
                })

            # Fetch audit trail entries related to user assessments
            assessment_ids = [str(a.id) for a in assessments]
            if assessment_ids:
                audit_stmt = select(AuditTrail).where(
                    AuditTrail.assessment_id.in_(assessment_ids)
                )
                audit_entries = db.scalars(audit_stmt).all()
            else:
                audit_entries = []

            for entry in audit_entries:
                data_export["audit_trail"].append({
                    "id": str(entry.id),
                    "assessment_id": str(entry.assessment_id) if entry.assessment_id else None,
                    "event_type": entry.event_type,
                    "actor_type": entry.actor_type,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                })

            logger.info(
                f"Collected DSAR data: {len(assessments)} assessments, {len(resumes)} resumes",
                extra={
                    "dsar_id": dsar_id,
                    "assessment_count": len(assessments),
                    "resume_count": len(resumes),
                    "audit_entries": len(audit_entries),
                },
            )

            # Create ZIP file with JSON exports
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                # Main export file
                zf.writestr(
                    "dsar_export.json",
                    json.dumps(data_export, indent=2, default=str),
                )
                # Manifest
                manifest = {
                    "dsar_id": dsar_id,
                    "user_id": str(dsar.user_id),
                    "export_date": datetime.now(timezone.utc).isoformat(),
                    "assessment_count": len(assessments),
                    "resume_count": len(resumes),
                    "audit_entries": len(audit_entries),
                }
                zf.writestr(
                    "manifest.json",
                    json.dumps(manifest, indent=2),
                )

            zip_buffer.seek(0)
            zip_data = zip_buffer.getvalue()

            # Upload to S3
            if settings.s3_enabled:
                s3_url = _upload_dsar_to_s3(dsar_uuid, zip_data)
            else:
                logger.warning("S3 not enabled; DSAR export cannot be uploaded")
                s3_url = None

            # Update DSAR record with S3 URL
            if s3_url:
                dsar.data_export_url = s3_url
                dsar.status = DSARStatus.ready_for_download
                db.commit()
                _audit_compliance(
                    db,
                    dsar_uuid,
                    "dsar.export_completed",
                    {
                        "user_id": str(dsar.user_id),
                        "s3_url": s3_url,
                        "zip_size_bytes": len(zip_data),
                        "assessment_count": len(assessments),
                    },
                )
                db.commit()

                # Send email to user with download link
                _send_dsar_download_email(user.email, s3_url, dsar)

                logger.info(
                    f"DSAR export completed and uploaded for user {dsar.user_id}",
                    extra={
                        "dsar_id": dsar_id,
                        "s3_url": s3_url,
                        "zip_size_bytes": len(zip_data),
                    },
                )

                return {
                    "status": "success",
                    "dsar_id": dsar_id,
                    "s3_url": s3_url,
                    "zip_size_bytes": len(zip_data),
                }
            else:
                logger.error(f"Failed to upload DSAR export to S3 for {dsar_id}")
                return {
                    "status": "upload_failed",
                    "dsar_id": dsar_id,
                    "error": "S3 upload failed",
                }

    except Exception as exc:
        logger.exception(f"DSAR export failed for {dsar_id}: {exc}")
        # Mark DSAR as failed on persistent errors
        try:
            with _session_factory()() as db:
                dsar = db.get(DSARRequest, uuid.UUID(dsar_id))
                if dsar:
                    _audit_compliance(
                        db,
                        uuid.UUID(dsar_id),
                        "dsar.export_failed",
                        {"error": str(exc)},
                    )
                    db.commit()
        except Exception:
            pass
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=600)


def _upload_dsar_to_s3(dsar_id: uuid.UUID, zip_data: bytes) -> str | None:
    """Upload DSAR ZIP file to S3 and return signed download URL."""
    try:
        import boto3

        s3_client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )

        # Create object key with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        object_key = f"dsar-exports/{dsar_id}/{timestamp}_dsar_export.zip"

        # Upload with server-side encryption
        s3_client.put_object(
            Bucket=settings.s3_bucket,
            Key=object_key,
            Body=zip_data,
            ContentType="application/zip",
            ServerSideEncryption="AES256",
            Metadata={
                "dsar_id": str(dsar_id),
                "export_date": datetime.now(timezone.utc).isoformat(),
            },
        )

        # Generate pre-signed URL (valid for 7 days)
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket, "Key": object_key},
            ExpiresIn=7 * 24 * 3600,  # 7 days
        )

        logger.info(
            "DSAR export uploaded to S3",
            extra={"dsar_id": str(dsar_id), "object_key": object_key},
        )

        return url

    except Exception as exc:
        logger.error(f"S3 upload failed for DSAR {dsar_id}: {exc}")
        return None


def _send_dsar_download_email(recipient_email: str, download_url: str, dsar: DSARRequest) -> None:
    """Email the user their DSAR export download link.

    Dispatches the shared notification-email task (which routes through the
    gated EmailService — a no-op when no provider is configured, a real send
    when one is). Previously this only *composed* the email and never sent it.
    """
    subject = "Your Data Export is Ready"
    message = (
        "Your Data Subject Access Request (DSAR) has been processed.\n\n"
        f"Your data export is ready for download:\n{download_url}\n\n"
        "This link expires in 7 days.\n\n"
        f"Request Type: {dsar.request_type}\n"
        f"Request ID: {dsar.id}\n\n"
        "If you did not request this export, please contact us immediately."
    )
    try:
        from app.workers.tasks import send_notification_email

        send_notification_email.delay(
            user_id=str(dsar.user_id),
            notification_id=str(dsar.id),
            recipient_email=recipient_email,
            notification_type="dsar_export",
            title=subject,
            message=message,
            action_url=download_url,
        )
        logger.info(
            "DSAR download email dispatched",
            extra={"dsar_id": str(dsar.id)},
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Failed to send DSAR download email to {recipient_email}: {exc}")


# ============================================================================
# DSAR Deletion (Data Subject Access Request - Article 17)
# ============================================================================


@celery_app.task(
    name="app.workers.retention.delete_user_data",
    bind=True,
    max_retries=1,
)
def delete_user_data(self, user_id: str, dsar_id: str) -> dict:
    """
    Permanently delete all user data (Right to be Forgotten - GDPR Article 17).

    Creates a compliance tombstone before deletion to preserve audit trail,
    then cascading deletes all user records and related data.

    Args:
        user_id: UUID of User to delete
        dsar_id: UUID of associated DSARRequest

    Returns:
        Dict with deletion status

    Raises:
        Exception: If deletion fails (retryable only on transient errors)
    """
    try:
        user_uuid = uuid.UUID(user_id)
        dsar_uuid = uuid.UUID(dsar_id)

        with _session_factory()() as db:
            # Fetch user to verify existence
            user = db.get(User, user_uuid)
            if not user:
                logger.error(f"User {user_id} not found for deletion")
                return {"status": "user_not_found", "user_id": user_id}

            dsar = db.get(DSARRequest, dsar_uuid)
            if not dsar:
                logger.error(f"DSAR request {dsar_id} not found")
                return {"status": "dsar_not_found", "dsar_id": dsar_id}

            logger.info(
                f"Starting DSAR deletion for user {user_id}",
                extra={"user_id": user_id, "dsar_id": dsar_id},
            )

            # Create compliance tombstone before deletion
            _create_compliance_tombstone(db, user_uuid, dsar_uuid)

            # Count records before deletion
            assessments_stmt = select(Assessment).where(Assessment.user_id == user_uuid)
            assessment_count = len(db.scalars(assessments_stmt).all())

            resumes_stmt = select(Resume).where(Resume.user_id == user_uuid)
            resume_count = len(db.scalars(resumes_stmt).all())

            # Delete all assessments (cascades to audit trail)
            delete_assessments = delete(Assessment).where(Assessment.user_id == user_uuid)
            db.execute(delete_assessments)

            # Delete all resumes
            delete_resumes = delete(Resume).where(Resume.user_id == user_uuid)
            db.execute(delete_resumes)

            # Delete the user record (this cascades to dependent records)
            db.delete(user)
            db.commit()

            # Update DSAR status to completed
            dsar.status = DSARStatus.completed
            dsar.completed_at = datetime.now(timezone.utc)
            db.commit()

            _audit_compliance(
                db,
                dsar_uuid,
                "dsar.deletion_completed",
                {
                    "user_id": user_id,
                    "user_email": user.email,
                    "assessments_deleted": assessment_count,
                    "resumes_deleted": resume_count,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            db.commit()

            # Send notification to admin Slack channel
            _notify_admin_slack(user, dsar, assessment_count, resume_count)

            logger.info(
                f"DSAR deletion completed for user {user_id}",
                extra={
                    "dsar_id": dsar_id,
                    "assessments_deleted": assessment_count,
                    "resumes_deleted": resume_count,
                },
            )

            return {
                "status": "success",
                "user_id": user_id,
                "dsar_id": dsar_id,
                "assessments_deleted": assessment_count,
                "resumes_deleted": resume_count,
            }

    except Exception as exc:
        logger.exception(f"DSAR deletion failed for user {user_id}: {exc}")
        raise self.retry(exc=exc, countdown=300)


def _create_compliance_tombstone(
    db: Session, user_id: uuid.UUID, dsar_id: uuid.UUID
) -> None:
    """Create compliance tombstone before user deletion."""
    _audit_compliance(
        db,
        dsar_id,
        "compliance.user_tombstone_created",
        {
            "user_id": str(user_id),
            "deletion_reason": "GDPR Article 17 - Right to be Forgotten",
            "tombstone_created": datetime.now(timezone.utc).isoformat(),
        },
    )


def _notify_admin_slack(
    user: User, dsar: DSARRequest, assessment_count: int, resume_count: int
) -> None:
    """Notify admin Slack channel of user deletion."""
    try:
        if not settings.slack_webhook_url or not settings.slack_notifications_enabled:
            logger.debug("Slack notifications disabled; skipping admin notification")
            return

        message = {
            "attachments": [
                {
                    "color": "#FF6600",
                    "title": "GDPR Article 17 - User Deletion Completed",
                    "fields": [
                        {"title": "User ID", "value": str(user.id), "short": True},
                        {"title": "User Email", "value": user.email, "short": True},
                        {"title": "DSAR ID", "value": str(dsar.id), "short": True},
                        {"title": "Assessments Deleted", "value": str(assessment_count), "short": True},
                        {"title": "Resumes Deleted", "value": str(resume_count), "short": True},
                        {
                            "title": "Deletion Time",
                            "value": datetime.now(timezone.utc).isoformat(),
                            "short": False,
                        },
                    ],
                }
            ]
        }

        import aiohttp
        import asyncio

        async def _send():
            async with aiohttp.ClientSession() as session:
                async with session.post(settings.slack_webhook_url, json=message) as resp:
                    if resp.status == 200:
                        logger.info(f"Admin Slack notification sent for user deletion {user.id}")
                    else:
                        logger.warning(f"Failed to send admin notification: {resp.status}")

        # Run async function in sync context
        try:
            asyncio.run(_send())
        except RuntimeError:
            # Event loop already running; log warning instead
            logger.warning("Cannot send Slack notification - event loop already running")

    except Exception as exc:
        logger.error(f"Failed to send admin Slack notification: {exc}")
