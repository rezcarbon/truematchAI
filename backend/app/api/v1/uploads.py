"""
Mass upload API endpoints for job data and resume versioning.
"""

from __future__ import annotations

import logging
import uuid
from typing import Annotated, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, status
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, AuthorizationError, ValidationError
from app.deps import get_current_user, get_db, CurrentUser, DBSession, require_role
from app.models.job_scraping import (
    MassUploadBatch,
    UploadType,
    BatchStatus,
    UploadFieldMapping,
)
from app.models.resume import Resume
from app.models.resume_version import ResumeVersion, ChangeType
from app.models.user import User, UserRole
from app.schemas.uploads import (
    BatchUploadResponse,
    BatchStatusResponse,
    CreateVersionRequest,
    FieldMappingResponse,
    ListFieldMappingsResponse,
    ListVersionsResponse,
    RevertVersionRequest,
    VersionComparisonResponse,
    VersionMetadata,
    VersionResponse,
)

logger = logging.getLogger("truematch.uploads")

router = APIRouter(prefix="/upload", tags=["uploads"])


@router.post(
    "/csv",
    summary="Upload CSV job data",
    description="Upload a CSV file with job postings. Requires field mapping to specify column-to-field relationships.",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_csv(
    file: UploadFile = File(..., description="CSV file with job data"),
    field_mapping_id: Optional[str] = Form(None, description="ID of pre-configured field mapping"),
    custom_field_mapping: Optional[str] = Form(None, description="Custom field mapping as JSON"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BatchUploadResponse:
    """
    Upload job data via CSV file.

    Supports two field mapping options:
    1. Use a pre-configured mapping: pass field_mapping_id
    2. Use custom mapping: pass custom_field_mapping as JSON string

    Example field mapping:
    ```json
    {
        "Job Title": "title",
        "Job Description": "description",
        "Company Name": "company",
        "Location": "location"
    }
    ```
    """
    # Validate file type
    if file.content_type not in {"text/csv", "application/vnd.ms-excel", "text/plain"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be CSV format",
        )

    # Get field mapping
    field_mapping = None

    if field_mapping_id:
        # Load from database
        result = await db.execute(
            select(UploadFieldMapping).where(UploadFieldMapping.id == uuid.UUID(field_mapping_id))
        )
        mapping_obj = result.scalar_one_or_none()
        if not mapping_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Field mapping not found",
            )
        field_mapping = mapping_obj.field_mapping

    elif custom_field_mapping:
        # Parse custom mapping
        import json

        try:
            field_mapping = json.loads(custom_field_mapping)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="custom_field_mapping must be valid JSON",
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either field_mapping_id or custom_field_mapping required",
        )

    # Read file content
    try:
        content = await file.read()
        content.decode("utf-8")  # validate UTF-8; raises -> 400 below
    except Exception as e:
        logger.error(f"Failed to read CSV file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read file",
        )

    # Create batch record
    batch = MassUploadBatch(
        id=uuid.uuid4(),
        upload_type=UploadType.csv,
        user_id=user.id,
        filename=file.filename,
        field_mapping=field_mapping,
        status=BatchStatus.pending,
    )

    db.add(batch)
    await db.commit()
    await db.refresh(batch)

    logger.info(
        "CSV upload batch created",
        extra={"batch_id": str(batch.id), "user_id": str(user.id), "filename": file.filename},
    )

    # Queue for processing (would be handled by Celery task)
    # For now, just return the batch ID
    return BatchUploadResponse(
        batch_id=str(batch.id),
        status=batch.status,
        message="Upload queued for processing",
    )


@router.post(
    "/json",
    summary="Upload JSON job data",
    description="Upload JSON file with job postings. Accepts either array or single object format.",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_json(
    file: UploadFile = File(..., description="JSON file with job data"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BatchUploadResponse:
    """
    Upload job data via JSON file.

    Supports two formats:
    1. Array of objects: [{"title": "...", "description": "...", ...}]
    2. Single object: {"title": "...", "description": "...", ...}

    Required fields: title, description, company
    """
    # Validate file type
    if file.content_type not in {"application/json", "text/plain"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be JSON format",
        )

    # Read file content
    try:
        content = await file.read()
        content.decode("utf-8")  # validate UTF-8; raises -> 400 below
    except Exception as e:
        logger.error(f"Failed to read JSON file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read file",
        )

    # Create batch record
    batch = MassUploadBatch(
        id=uuid.uuid4(),
        upload_type=UploadType.json,
        user_id=user.id,
        filename=file.filename,
        status=BatchStatus.pending,
    )

    db.add(batch)
    await db.commit()
    await db.refresh(batch)

    logger.info(
        "JSON upload batch created",
        extra={"batch_id": str(batch.id), "user_id": str(user.id), "filename": file.filename},
    )

    return BatchUploadResponse(
        batch_id=str(batch.id),
        status=batch.status,
        message="Upload queued for processing",
    )


@router.get(
    "/batch/{batch_id}",
    summary="Get upload batch status",
    description="Check the status and progress of a mass upload batch.",
    response_model=BatchStatusResponse,
)
async def get_batch_status(
    batch_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BatchStatusResponse:
    """
    Get the status of a mass upload batch.

    Returns processing progress and any errors encountered.
    """
    try:
        batch_uuid = uuid.UUID(batch_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid batch_id format",
        )

    result = await db.execute(
        select(MassUploadBatch).where(
            and_(
                MassUploadBatch.id == batch_uuid,
                MassUploadBatch.user_id == user.id,
            )
        )
    )
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found",
        )

    return BatchStatusResponse(
        batch_id=str(batch.id),
        status=batch.status,
        filename=batch.filename,
        total_rows=batch.total_rows,
        processed_rows=batch.processed_rows,
        failed_rows=batch.failed_rows,
        duplicate_rows=batch.duplicate_rows,
        created_at=batch.created_at,
        completed_at=batch.completed_at,
        errors=batch.errors if batch.errors else {},
    )


@router.get(
    "/field-mappings",
    summary="List available field mappings",
    description="Get all available field mappings for CSV uploads.",
    response_model=ListFieldMappingsResponse,
)
async def list_field_mappings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ListFieldMappingsResponse:
    """
    List all available field mappings.

    Returns system-provided mappings plus any custom mappings created by the user.
    """
    result = await db.execute(
        select(UploadFieldMapping).order_by(UploadFieldMapping.is_system.desc(), UploadFieldMapping.name)
    )
    mappings = result.scalars().all()

    mapping_list = [
        FieldMappingResponse(
            id=str(m.id),
            name=m.name,
            description=m.description or "",
            field_mapping=m.field_mapping,
            is_system=m.is_system,
        )
        for m in mappings
    ]

    return ListFieldMappingsResponse(mappings=mapping_list)


@router.post(
    "/field-mappings",
    summary="Create custom field mapping",
    description="Create a custom field mapping for CSV uploads.",
    response_model=FieldMappingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_field_mapping(
    name: str = Form(..., description="Mapping name"),
    description: Optional[str] = Form(None, description="Mapping description"),
    field_mapping_json: str = Form(..., description="Field mapping as JSON"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FieldMappingResponse:
    """
    Create a custom field mapping for CSV uploads.

    Example field_mapping_json:
    ```json
    {
        "Job Title": "title",
        "Job Description": "description",
        "Company": "company",
        "Location": "location"
    }
    ```
    """
    import json

    try:
        field_mapping = json.loads(field_mapping_json)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="field_mapping_json must be valid JSON",
        )

    # Check if mapping already exists
    result = await db.execute(
        select(UploadFieldMapping).where(UploadFieldMapping.name == name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A mapping with this name already exists",
        )

    mapping = UploadFieldMapping(
        id=uuid.uuid4(),
        name=name,
        description=description,
        field_mapping=field_mapping,
        is_system=False,
        created_by=user.id,
    )

    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)

    logger.info(
        "Custom field mapping created",
        extra={"mapping_id": str(mapping.id), "user_id": str(user.id), "name": name},
    )

    return FieldMappingResponse(
        id=str(mapping.id),
        name=mapping.name,
        description=mapping.description or "",
        field_mapping=mapping.field_mapping,
        is_system=False,
    )


# ────────────────────────────────────────────────────────────────────────────
# Resume Versioning Endpoints
# ────────────────────────────────────────────────────────────────────────────


@router.post(
    "/resumes/{resume_id}/versions",
    response_model=VersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new resume version",
    description="Create a new version of a resume with change tracking.",
)
async def create_resume_version(
    resume_id: uuid.UUID,
    payload: CreateVersionRequest,
    user: CurrentUser,
    db: DBSession,
) -> VersionResponse:
    """Create a new version of a resume.

    Creates a new version entry tracking changes to the resume.
    Supports different change types: upload, edit, ai_enhancement, import.

    Args:
        resume_id: ID of the parent resume
        payload: Version creation details
        user: Current authenticated user
        db: Database session

    Returns:
        VersionResponse with the new version details

    Raises:
        NotFoundError: If resume doesn't exist or user doesn't own it
        ValidationError: If payload is invalid
    """
    # Verify resume ownership
    resume = await db.get(Resume, resume_id)
    if resume is None:
        raise NotFoundError(
            f"Resume {resume_id} not found",
            instance=f"/api/v1/upload/resumes/{resume_id}/versions",
        )

    if resume.user_id != user.id:
        raise AuthorizationError("You do not have permission to access this resume")

    # Validate change_type
    try:
        change_type = ChangeType(payload.change_type)
    except ValueError:
        raise ValidationError(
            message=f"Invalid change_type. Must be one of: {', '.join([ct.value for ct in ChangeType])}",
            instance=f"/api/v1/upload/resumes/{resume_id}/versions",
        )

    # Get the next version number
    max_version = await db.scalar(
        select(func.max(ResumeVersion.version_number)).where(
            ResumeVersion.resume_id == resume_id
        )
    )
    next_version_number = (max_version or 0) + 1

    # Mark previous version as not current
    await db.execute(
        select(ResumeVersion).where(
            and_(
                ResumeVersion.resume_id == resume_id,
                ResumeVersion.is_current == True,
            )
        )
    )
    prev_versions = (await db.scalars(
        select(ResumeVersion).where(
            and_(
                ResumeVersion.resume_id == resume_id,
                ResumeVersion.is_current == True,
            )
        )
    )).all()

    for pv in prev_versions:
        pv.is_current = False

    # Create new version
    new_version = ResumeVersion(
        id=uuid.uuid4(),
        resume_id=resume_id,
        user_id=user.id,
        version_number=next_version_number,
        is_current=True,
        change_type=change_type,
        change_summary=payload.change_summary,
        change_metadata=payload.change_metadata,
        created_by_id=user.id,
    )

    db.add(new_version)
    await db.commit()
    await db.refresh(new_version)

    logger.info(
        "Resume version created",
        extra={
            "resume_id": str(resume_id),
            "version_id": str(new_version.id),
            "version_number": next_version_number,
            "user_id": str(user.id),
            "change_type": payload.change_type,
        },
    )

    metadata = VersionMetadata(
        version_number=new_version.version_number,
        is_current=new_version.is_current,
        file_name=new_version.file_name,
        file_type=new_version.file_type,
        file_size_bytes=new_version.file_size_bytes,
        quality_score=new_version.quality_score,
        completeness_percentage=new_version.completeness_percentage,
        change_type=new_version.change_type.value,
        change_summary=new_version.change_summary,
        created_at=new_version.created_at,
        created_by_id=new_version.created_by_id,
    )

    return VersionResponse(
        id=new_version.id,
        resume_id=new_version.resume_id,
        metadata=metadata,
    )


@router.get(
    "/resumes/{resume_id}/versions",
    response_model=ListVersionsResponse,
    status_code=status.HTTP_200_OK,
    summary="List resume versions",
    description="Get all versions of a resume with metadata.",
)
async def list_resume_versions(
    resume_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> ListVersionsResponse:
    """List all versions of a resume.

    Returns all versions with metadata sorted by version number descending.

    Args:
        resume_id: ID of the resume
        user: Current authenticated user
        db: Database session

    Returns:
        ListVersionsResponse with all versions

    Raises:
        NotFoundError: If resume doesn't exist or user doesn't own it
    """
    # Verify resume ownership
    resume = await db.get(Resume, resume_id)
    if resume is None:
        raise NotFoundError(
            f"Resume {resume_id} not found",
            instance=f"/api/v1/upload/resumes/{resume_id}/versions",
        )

    if resume.user_id != user.id:
        raise AuthorizationError("You do not have permission to access this resume")

    # Get all versions
    stmt = (
        select(ResumeVersion)
        .where(ResumeVersion.resume_id == resume_id)
        .order_by(ResumeVersion.version_number.desc())
    )
    versions = (await db.scalars(stmt)).all()

    version_responses = []
    for version in versions:
        metadata = VersionMetadata(
            version_number=version.version_number,
            is_current=version.is_current,
            file_name=version.file_name,
            file_type=version.file_type,
            file_size_bytes=version.file_size_bytes,
            quality_score=version.quality_score,
            completeness_percentage=version.completeness_percentage,
            change_type=version.change_type.value if isinstance(version.change_type, ChangeType) else version.change_type,
            change_summary=version.change_summary,
            created_at=version.created_at,
            created_by_id=version.created_by_id,
        )
        version_responses.append(
            VersionResponse(
                id=version.id,
                resume_id=version.resume_id,
                metadata=metadata,
            )
        )

    logger.info(
        "Resume versions listed",
        extra={
            "resume_id": str(resume_id),
            "user_id": str(user.id),
            "total_versions": len(versions),
        },
    )

    return ListVersionsResponse(
        resume_id=resume_id,
        versions=version_responses,
        total_versions=len(versions),
    )


@router.get(
    "/resumes/{resume_id}/versions/{version_id}",
    response_model=VersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get specific resume version",
    description="Fetch a specific version of a resume.",
)
async def get_resume_version(
    resume_id: uuid.UUID,
    version_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> VersionResponse:
    """Get a specific version of a resume.

    Args:
        resume_id: ID of the parent resume
        version_id: ID of the specific version
        user: Current authenticated user
        db: Database session

    Returns:
        VersionResponse with version details

    Raises:
        NotFoundError: If resume or version doesn't exist, or user doesn't own it
    """
    # Verify resume ownership
    resume = await db.get(Resume, resume_id)
    if resume is None:
        raise NotFoundError(
            f"Resume {resume_id} not found",
            instance=f"/api/v1/upload/resumes/{resume_id}/versions/{version_id}",
        )

    if resume.user_id != user.id:
        raise AuthorizationError("You do not have permission to access this resume")

    # Get specific version
    version = await db.get(ResumeVersion, version_id)
    if version is None or version.resume_id != resume_id:
        raise NotFoundError(
            f"Version {version_id} not found for resume {resume_id}",
            instance=f"/api/v1/upload/resumes/{resume_id}/versions/{version_id}",
        )

    logger.info(
        "Resume version retrieved",
        extra={
            "resume_id": str(resume_id),
            "version_id": str(version_id),
            "user_id": str(user.id),
        },
    )

    metadata = VersionMetadata(
        version_number=version.version_number,
        is_current=version.is_current,
        file_name=version.file_name,
        file_type=version.file_type,
        file_size_bytes=version.file_size_bytes,
        quality_score=version.quality_score,
        completeness_percentage=version.completeness_percentage,
        change_type=version.change_type.value if isinstance(version.change_type, ChangeType) else version.change_type,
        change_summary=version.change_summary,
        created_at=version.created_at,
        created_by_id=version.created_by_id,
    )

    return VersionResponse(
        id=version.id,
        resume_id=version.resume_id,
        metadata=metadata,
    )


@router.post(
    "/resumes/{resume_id}/versions/{version_id}/revert",
    response_model=VersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Revert to previous version",
    description="Revert a resume to a previous version.",
)
async def revert_resume_version(
    resume_id: uuid.UUID,
    version_id: uuid.UUID,
    payload: RevertVersionRequest,
    user: CurrentUser,
    db: DBSession,
) -> VersionResponse:
    """Revert a resume to a previous version.

    Marks the target version as current and deactivates the current version.
    Creates an audit trail with the revert reason.

    Args:
        resume_id: ID of the parent resume
        version_id: ID of the version to revert to
        payload: Revert request details
        user: Current authenticated user
        db: Database session

    Returns:
        VersionResponse with the reverted version

    Raises:
        NotFoundError: If resume or version doesn't exist, or user doesn't own it
    """
    # Verify resume ownership
    resume = await db.get(Resume, resume_id)
    if resume is None:
        raise NotFoundError(
            f"Resume {resume_id} not found",
            instance=f"/api/v1/upload/resumes/{resume_id}/versions/{version_id}/revert",
        )

    if resume.user_id != user.id:
        raise AuthorizationError("You do not have permission to access this resume")

    # Get target version
    target_version = await db.get(ResumeVersion, version_id)
    if target_version is None or target_version.resume_id != resume_id:
        raise NotFoundError(
            f"Version {version_id} not found for resume {resume_id}",
            instance=f"/api/v1/upload/resumes/{resume_id}/versions/{version_id}/revert",
        )

    # Get current version
    current_version = (await db.scalars(
        select(ResumeVersion).where(
            and_(
                ResumeVersion.resume_id == resume_id,
                ResumeVersion.is_current == True,
            )
        )
    )).first()

    # Mark current as not current
    if current_version:
        current_version.is_current = False

    # Mark target as current
    target_version.is_current = True

    await db.commit()
    await db.refresh(target_version)

    logger.info(
        "Resume reverted to previous version",
        extra={
            "resume_id": str(resume_id),
            "target_version_id": str(version_id),
            "user_id": str(user.id),
            "reason": payload.reason,
        },
    )

    metadata = VersionMetadata(
        version_number=target_version.version_number,
        is_current=target_version.is_current,
        file_name=target_version.file_name,
        file_type=target_version.file_type,
        file_size_bytes=target_version.file_size_bytes,
        quality_score=target_version.quality_score,
        completeness_percentage=target_version.completeness_percentage,
        change_type=target_version.change_type.value if isinstance(target_version.change_type, ChangeType) else target_version.change_type,
        change_summary=target_version.change_summary,
        created_at=target_version.created_at,
        created_by_id=target_version.created_by_id,
    )

    return VersionResponse(
        id=target_version.id,
        resume_id=target_version.resume_id,
        metadata=metadata,
    )


@router.get(
    "/resumes/compare/{version_id_1}/{version_id_2}",
    response_model=VersionComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare two resume versions",
    description="Get unified diff and assessment comparison between two versions.",
)
async def compare_resume_versions(
    version_id_1: uuid.UUID,
    version_id_2: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> VersionComparisonResponse:
    """Compare two resume versions.

    Returns a unified diff and detailed comparison of changes between versions.

    Args:
        version_id_1: First version ID
        version_id_2: Second version ID
        user: Current authenticated user
        db: Database session

    Returns:
        VersionComparisonResponse with diff and comparison

    Raises:
        NotFoundError: If either version doesn't exist or user doesn't own them
    """
    # Get both versions
    version_1 = await db.get(ResumeVersion, version_id_1)
    version_2 = await db.get(ResumeVersion, version_id_2)

    if version_1 is None:
        raise NotFoundError(
            f"Version {version_id_1} not found",
            instance=f"/api/v1/upload/resumes/compare/{version_id_1}/{version_id_2}",
        )

    if version_2 is None:
        raise NotFoundError(
            f"Version {version_id_2} not found",
            instance=f"/api/v1/upload/resumes/compare/{version_id_1}/{version_id_2}",
        )

    # Verify both versions belong to user and same resume
    if version_1.user_id != user.id or version_2.user_id != user.id:
        raise AuthorizationError("You do not have permission to access these versions")

    if version_1.resume_id != version_2.resume_id:
        raise ValidationError(
            message="Versions must be from the same resume",
            instance=f"/api/v1/upload/resumes/compare/{version_id_1}/{version_id_2}",
        )

    # Calculate quality delta
    quality_delta = None
    if version_1.quality_score is not None and version_2.quality_score is not None:
        quality_delta = version_2.quality_score - version_1.quality_score

    # Calculate completeness delta
    completeness_delta = None
    if version_1.completeness_percentage is not None and version_2.completeness_percentage is not None:
        completeness_delta = version_2.completeness_percentage - version_1.completeness_percentage

    # TODO: Generate actual unified diff from raw_narrative
    # This is a placeholder implementation
    unified_diff = (
        f"--- version {version_id_1}\n"
        f"+++ version {version_id_2}\n"
        "@@ -1,10 +1,10 @@\n"
        " Content comparison between versions\n"
    )

    # Extract sections changed from content_diff if available
    sections_changed = []
    if version_1.content_diff and isinstance(version_1.content_diff, dict):
        sections_changed = version_1.content_diff.get("sections_modified", [])

    logger.info(
        "Resume versions compared",
        extra={
            "version_1_id": str(version_id_1),
            "version_2_id": str(version_id_2),
            "user_id": str(user.id),
        },
    )

    return VersionComparisonResponse(
        version_1_id=version_id_1,
        version_2_id=version_id_2,
        unified_diff=unified_diff,
        summary={
            "version_1_number": version_1.version_number,
            "version_2_number": version_2.version_number,
            "version_1_created": version_1.created_at.isoformat(),
            "version_2_created": version_2.created_at.isoformat(),
        },
        quality_delta=quality_delta,
        completeness_delta=completeness_delta,
        sections_changed=sections_changed,
    )
