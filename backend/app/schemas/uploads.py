"""
Schemas for upload API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BatchUploadResponse(BaseModel):
    """Response after uploading a batch"""

    batch_id: str = Field(..., description="Unique batch identifier")
    status: str = Field(..., description="Current batch status (pending, processing, completed, failed)")
    message: str = Field(..., description="Status message")


class BatchStatusResponse(BaseModel):
    """Status of an upload batch"""

    batch_id: str = Field(..., description="Unique batch identifier")
    status: str = Field(..., description="Current batch status")
    filename: Optional[str] = Field(None, description="Original filename")
    total_rows: int = Field(..., description="Total rows in upload")
    processed_rows: int = Field(..., description="Successfully processed rows")
    failed_rows: int = Field(..., description="Rows with errors")
    duplicate_rows: int = Field(..., description="Rows identified as duplicates")
    created_at: datetime = Field(..., description="Batch creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Batch completion timestamp")
    errors: dict = Field(default_factory=dict, description="Error details by row")


class FieldMappingResponse(BaseModel):
    """Field mapping configuration"""

    id: str = Field(..., description="Mapping identifier")
    name: str = Field(..., description="Mapping name")
    description: str = Field(..., description="Mapping description")
    field_mapping: dict = Field(..., description="Column-to-field mapping")
    is_system: bool = Field(..., description="Whether this is a system-provided mapping")


class ListFieldMappingsResponse(BaseModel):
    """List of available field mappings"""

    mappings: list[FieldMappingResponse] = Field(..., description="Available mappings")
