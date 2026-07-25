"""Resume upload and management endpoints."""
from __future__ import annotations

import logging
import uuid
from typing import Optional
from io import BytesIO

from fastapi import APIRouter, File, UploadFile, HTTPException, status
from sqlalchemy import select

from app.deps import CurrentUser, DBSession
from app.models.resume import Resume
from app.models.resume_version import ResumeVersion, ChangeType
from app.schemas.resume import ResumeResponse, ResumeListResponse
from app.core.clock import utcnow
from app.core.exceptions import NotFoundError

logger = logging.getLogger("truematch.resume_upload")

router = APIRouter(prefix="/resume", tags=["resumes"])


def _extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF file."""
    try:
        import PyPDF2
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.warning(f"PDF extraction failed: {str(e)}, using raw content")
        return ""


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(..., description="Resume PDF file"),
    user: CurrentUser = None,
    db: DBSession = None,
) -> Resume:
    """Upload a new resume file.

    Accepts PDF files and extracts text for processing.
    Creates a new resume record and initial version.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a name",
        )

    # Validate file type
    if not file.content_type or "pdf" not in file.content_type.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF",
        )

    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty",
            )
        if len(content) > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(
                status_code=status.HTTP_413_PAYLOAD_TOO_LARGE,
                detail="File too large (max 50MB)",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to read file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read file",
        )

    # Extract text from PDF
    extracted_text = _extract_text_from_pdf(content)
    if not extracted_text:
        logger.warning(f"No text extracted from PDF: {file.filename}")

    # Create resume record
    resume = Resume(
        user_id=user.id,
        title=file.filename.replace(".pdf", ""),
        raw_narrative=extracted_text,
        supplementary={"filename": file.filename, "extracted_text": extracted_text},
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db.add(resume)
    await db.flush()

    # Create initial version
    version = ResumeVersion(
        resume_id=resume.id,
        version_number=1,
        change_type=ChangeType.created,
        raw_content=content.decode("utf-8", errors="ignore"),
        metadata={"filename": file.filename, "extracted": bool(extracted_text)},
        created_at=utcnow(),
    )
    db.add(version)
    await db.commit()

    logger.info(f"Resume uploaded: {resume.id} by user {user.id}")
    return resume


@router.get("", response_model=ResumeListResponse)
async def list_resumes(
    user: CurrentUser = None,
    db: DBSession = None,
) -> ResumeListResponse:
    """List all resumes for the current user."""
    stmt = select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc())
    resumes = list((await db.scalars(stmt)).all())
    return ResumeListResponse(
        resumes=[ResumeResponse.model_validate(r) for r in resumes],
        total=len(resumes),
    )


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: uuid.UUID,
    user: CurrentUser = None,
    db: DBSession = None,
) -> Resume:
    """Get a specific resume."""
    resume = await db.get(Resume, resume_id)
    if not resume:
        raise NotFoundError("Resume not found")
    if resume.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: uuid.UUID,
    user: CurrentUser = None,
    db: DBSession = None,
) -> None:
    """Delete a resume."""
    resume = await db.get(Resume, resume_id)
    if not resume:
        raise NotFoundError("Resume not found")
    if resume.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    await db.delete(resume)
    await db.commit()
