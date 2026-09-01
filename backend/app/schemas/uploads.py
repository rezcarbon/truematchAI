"""
Schemas for upload API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

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


class VersionMetadata(BaseModel):
    """Metadata for a resume version."""
    version_number: int = Field(..., description="Sequential version number")
    is_current: bool = Field(..., description="Whether this is the active version")
    file_name: Optional[str] = Field(None, description="Original filename")
    file_type: Optional[str] = Field(None, description="MIME type")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    quality_score: Optional[float] = Field(None, ge=0, le=100, description="Quality score 0-100")
    completeness_percentage: Optional[int] = Field(None, ge=0, le=100, description="Completeness %")
    change_type: str = Field(..., description="Type of change: upload/edit/ai_enhancement/import")
    change_summary: Optional[str] = Field(None, description="Summary of changes")
    created_at: datetime = Field(..., description="Version creation timestamp")
    created_by_id: Optional[UUID] = Field(None, description="User who created this version")


class VersionResponse(BaseModel):
    """Response for a resume version."""
    id: UUID = Field(..., description="Version ID")
    resume_id: UUID = Field(..., description="Parent resume ID")
    metadata: VersionMetadata = Field(..., description="Version metadata")


class ListVersionsResponse(BaseModel):
    """Response listing all versions of a resume."""
    resume_id: UUID = Field(..., description="Resume ID")
    versions: list[VersionResponse] = Field(..., description="List of versions")
    total_versions: int = Field(..., description="Total number of versions")


class CreateVersionRequest(BaseModel):
    """Request to create a new resume version."""
    change_type: str = Field(
        default="edit",
        description="Type of change: upload/edit/ai_enhancement/import"
    )
    change_summary: Optional[str] = Field(
        None,
        max_length=512,
        description="Summary of changes made"
    )
    change_metadata: Optional[dict] = Field(
        None,
        description="Additional metadata about the change"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "change_type": "ai_enhancement",
                "change_summary": "Enhanced with AI-generated bullet points",
                "change_metadata": {"enhancement_type": "bullet_points", "sections_modified": 3}
            }
        }


class RevertVersionRequest(BaseModel):
    """Request to revert to a previous version."""
    reason: Optional[str] = Field(None, max_length=512, description="Reason for reverting")

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Previous version had better formatting"
            }
        }


class VersionComparisonResponse(BaseModel):
    """Response comparing two resume versions."""
    version_1_id: UUID = Field(..., description="First version ID")
    version_2_id: UUID = Field(..., description="Second version ID")
    unified_diff: str = Field(..., description="Unified diff format")
    summary: dict = Field(..., description="Summary of changes")
    quality_delta: Optional[float] = Field(None, description="Change in quality score")
    completeness_delta: Optional[int] = Field(None, description="Change in completeness %")
    sections_changed: list[str] = Field(default_factory=list, description="Sections that changed")

    class Config:
        json_schema_extra = {
            "example": {
                "version_1_id": "550e8400-e29b-41d4-a716-446655440000",
                "version_2_id": "550e8400-e29b-41d4-a716-446655440001",
                "unified_diff": "--- version 1\n+++ version 2\n@@ ... @@",
                "summary": {"added": 2, "removed": 1, "modified": 3},
                "quality_delta": 5.5,
                "completeness_delta": 10,
                "sections_changed": ["experience", "skills"]
            }
        }
