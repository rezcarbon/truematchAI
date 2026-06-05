"""
Mass upload API endpoints for job data.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.job_scraping import (
    MassUploadBatch,
    UploadType,
    BatchStatus,
    UploadFieldMapping,
)
from app.models.user import User
from app.scrapers import MassUploadProcessor, DEFAULT_FIELD_MAPPINGS
from app.schemas.uploads import (
    BatchUploadResponse,
    BatchStatusResponse,
    FieldMappingResponse,
    ListFieldMappingsResponse,
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
        text_content = content.decode("utf-8")
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
        text_content = content.decode("utf-8")
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
