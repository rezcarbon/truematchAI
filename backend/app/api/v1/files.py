"""File endpoints — multipart upload to S3 (boto3, stub credentials)."""
from __future__ import annotations

import logging
import uuid

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select

from app.config import settings
from app.deps import CurrentUser, DBSession
from app.engines.extract import ExtractionError, extract_text
from app.models.resume import Resume

router = APIRouter()
logger = logging.getLogger("truematch.files")

_ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "docx",  # Old .doc format
    "application/x-msword": "docx",  # Alternative MIME type
    "application/vnd.ms-word": "docx",  # Additional Word variant
    "application/vnd.word": "docx",  # Another Word variant
    "text/plain": "txt",
    "text/txt": "txt",  # Alternative plain text type
    "application/octet-stream": None,  # Will be detected by file extension
}

# Map file extensions when MIME type detection fails
_EXTENSION_TO_TYPE = {
    "pdf": "pdf",
    "doc": "docx",
    "docx": "docx",
    "txt": "txt",
}


class UploadResponse(BaseModel):
    resume_id: uuid.UUID
    file_id: str
    file_type: str


def _s3_client():
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


@router.post("/resume", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    user: CurrentUser,
    db: DBSession,
    file: UploadFile = File(...),
) -> UploadResponse:
    # Try to determine file type from MIME type first
    file_type = _ALLOWED_TYPES.get(file.content_type or "")

    # If MIME type detection failed, try to detect from file extension
    if file_type is None and file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        file_type = _EXTENSION_TO_TYPE.get(ext)

    # If still no match, reject the file
    if file_type is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Supported: PDF, Word (.doc, .docx), TXT. Got: {file.content_type}",
        )

    key = f"resumes/{user.id}/{uuid.uuid4()}-{file.filename}"
    body = await file.read()

    if len(body) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.max_upload_bytes} byte limit",
        )

    # Extract text now so the binary is read once and the pipeline works from
    # persisted text. A document that yields no text (e.g. image-only scan) is
    # rejected — the assessment cannot reason over an empty resume.
    try:
        logger.info(
            f"Extracting text from {file_type} file: {file.filename}",
            extra={
                "user_id": str(user.id),
                "file_name": file.filename,
                "file_type": file_type,
                "content_type": file.content_type,
                "file_size": len(body),
            },
        )
        extracted_text = extract_text(body, file_type)
        logger.info(
            f"Successfully extracted {len(extracted_text)} chars from {file_type}",
            extra={"user_id": str(user.id), "extracted_length": len(extracted_text)},
        )
    except ExtractionError as exc:
        logger.error(
            f"Extraction failed: {str(exc)}",
            extra={
                "user_id": str(user.id),
                "file_name": file.filename,
                "file_type": file_type,
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    # Production MUST have real object storage configured; never silently accept
    # a resume we cannot durably (and encrypted-at-rest) store.
    if settings.environment == "production" and not settings.s3_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Object storage is not configured",
        )

    # Upload to S3 with server-side encryption. When object storage isn't
    # configured (local staging/dev), skip the call entirely — the resume's text
    # is already extracted and encrypted in the DB, which is what the pipeline
    # needs. The raw binary just isn't durably stored.
    uploaded = False
    sse_args: dict = (
        {"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": settings.s3_kms_key_id}
        if settings.s3_kms_key_id
        else {"ServerSideEncryption": "AES256"}
    )
    if settings.s3_configured:
        try:
            _s3_client().put_object(
                Bucket=settings.s3_bucket,
                Key=key,
                Body=body,
                ContentType=file.content_type,
                **sse_args,
            )
            uploaded = True
        except (BotoCoreError, ClientError) as exc:
            if settings.environment == "production":
                logger.error("S3 upload failed in production: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to store the uploaded file",
                ) from exc
            logger.warning("S3 upload failed: %s", exc)
    else:
        logger.info("Object storage not configured; storing extracted text only (local mode).")

    resume = Resume(
        user_id=user.id,
        file_id=key,
        file_type=file_type,
        supplementary={
            "original_filename": file.filename,
            "s3_uploaded": uploaded,
            "extracted_text": extracted_text,
        },
    )
    db.add(resume)
    await db.flush()
    return UploadResponse(resume_id=resume.id, file_id=key, file_type=file_type)


class ResumeListItem(BaseModel):
    id: uuid.UUID
    filename: str | None
    file_type: str
    created_at: str


class ResumeListResponse(BaseModel):
    items: list[ResumeListItem]
    total: int


@router.get("/resumes", response_model=ResumeListResponse)
async def list_resumes(user: CurrentUser, db: DBSession) -> ResumeListResponse:
    """List all resumes for the current user."""
    resumes = (
        await db.scalars(
            select(Resume)
            .where(Resume.user_id == user.id)
            .order_by(Resume.created_at.desc())
        )
    ).all()

    items = [
        ResumeListItem(
            id=r.id,
            filename=r.supplementary.get("original_filename") if r.supplementary else None,
            file_type=r.file_type,
            created_at=r.created_at.isoformat(),
        )
        for r in resumes
    ]

    return ResumeListResponse(items=items, total=len(items))


@router.get("/resume/{resume_id}/download-url")
async def get_download_url(
    resume_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> dict:
    resume = await db.get(Resume, resume_id)
    if resume is None or resume.file_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if user.role.value == "candidate" and resume.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    try:
        url = _s3_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket, "Key": resume.file_id},
            ExpiresIn=900,
        )
    except (BotoCoreError, ClientError) as exc:
        logger.warning("Presign failed (likely stub credentials): %s", exc)
        url = None
    return {"resume_id": str(resume.id), "url": url, "key": resume.file_id}
