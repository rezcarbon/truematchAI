"""File endpoints — multipart upload to S3 (boto3, stub credentials)."""
from __future__ import annotations

import base64
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

_IMAGE_TYPES = {
    "image/jpeg": "image/jpeg",
    "image/jpg": "image/jpeg",
    "image/png": "image/png",
    "image/webp": "image/webp",
    "image/gif": "image/gif",
}

_AUDIO_TYPES = {
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/mp4": "m4a",
    "audio/x-m4a": "m4a",
    "audio/m4a": "m4a",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/webm": "webm",
    "audio/ogg": "ogg",
    "audio/flac": "flac",
}

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


@router.post("/resume/image", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume_image(
    user: CurrentUser,
    db: DBSession,
    file: UploadFile = File(...),
) -> UploadResponse:
    """Multimodal intake: accept a photo/scan of a resume, transcribe it with
    Claude vision, and create a Resume from the extracted text — so a user can
    snap a picture instead of uploading a PDF/DOCX."""
    media_type = _IMAGE_TYPES.get((file.content_type or "").lower())
    if media_type is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported image type. Supported: JPEG, PNG, WEBP, GIF. Got: {file.content_type}",
        )

    body = await file.read()
    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty image")
    if len(body) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds the {settings.max_upload_bytes} byte limit",
        )

    from app.engines.client import extract_text_from_image, is_live, LLMError

    if not is_live():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Image transcription requires the language model to be configured.",
        )
    try:
        image_b64 = base64.b64encode(body).decode("ascii")
        extracted_text = extract_text_from_image(image_b64, media_type)
    except LLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not transcribe the image: {exc}",
        ) from exc
    if not extracted_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable text found in the image.",
        )

    key = f"resumes/{user.id}/{uuid.uuid4()}-{file.filename or 'photo'}"
    resume = Resume(
        user_id=user.id,
        file_id=key,
        file_type="image",
        supplementary={
            "original_filename": file.filename,
            "s3_uploaded": False,
            "intake": "vision",
            "extracted_text": extracted_text,
        },
    )
    db.add(resume)
    await db.flush()
    logger.info(
        "Resume created via vision intake",
        extra={"user_id": str(user.id), "extracted_length": len(extracted_text)},
    )
    return UploadResponse(resume_id=resume.id, file_id=key, file_type="image")


@router.post("/resume/audio", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume_audio(
    user: CurrentUser,
    db: DBSession,
    file: UploadFile = File(...),
) -> UploadResponse:
    """Multimodal intake: accept a spoken resume (audio), transcribe it with a
    speech-to-text provider, and create a Resume from the transcript — so a user
    can record themselves instead of uploading a document."""
    from app.engines.transcription import TranscriptionError, is_configured, transcribe_audio

    ext = _AUDIO_TYPES.get((file.content_type or "").lower())
    if ext is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio type. Supported: mp3, m4a, wav, webm, ogg, flac. Got: {file.content_type}",
        )

    body = await file.read()
    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty audio file")
    if len(body) > settings.transcription_max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio exceeds the {settings.transcription_max_bytes} byte limit",
        )

    if not is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Audio transcription requires a speech-to-text provider to be configured.",
        )
    try:
        transcript = transcribe_audio(body, file.filename or f"audio.{ext}", file.content_type or "")
    except TranscriptionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not transcribe the audio: {exc}",
        ) from exc
    if not transcript.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No speech detected in the audio.",
        )

    key = f"resumes/{user.id}/{uuid.uuid4()}-{file.filename or 'audio'}"
    resume = Resume(
        user_id=user.id,
        file_id=key,
        file_type="audio",
        supplementary={
            "original_filename": file.filename,
            "s3_uploaded": False,
            "intake": "audio",
            "extracted_text": transcript,
        },
    )
    db.add(resume)
    await db.flush()
    logger.info(
        "Resume created via audio intake",
        extra={"user_id": str(user.id), "transcript_length": len(transcript)},
    )
    return UploadResponse(resume_id=resume.id, file_id=key, file_type="audio")


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
