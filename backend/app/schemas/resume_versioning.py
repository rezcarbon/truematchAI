"""Request and response schemas for resume versioning."""
from __future__ import annotations

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional
from enum import Enum


class ResumeVersionStatus(str, Enum):
    """Status of a resume version."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ResumeVersionType(str, Enum):
    """Type of resume version."""
    GENERAL = "general"
    TAILORED = "tailored"
    ATS_OPTIMIZED = "ats_optimized"
    INDUSTRY_SPECIFIC = "industry_specific"


class CreateResumeVersionRequest(BaseModel):
    """Request to create a new resume version."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    base_resume_id: UUID = Field(..., description="UUID of base resume to version from")
    version_name: str = Field(..., min_length=1, max_length=255, description="Name for this version")
    version_type: ResumeVersionType = Field(..., description="Type of resume version")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")
    is_default: bool = Field(False, description="Set as default version")


class UpdateResumeVersionRequest(BaseModel):
    """Request to update an existing resume version."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    version_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[ResumeVersionStatus] = None
    is_default: Optional[bool] = None


class TailorResumeRequest(BaseModel):
    """Request to tailor a resume for a specific job."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    base_resume_id: UUID = Field(..., description="Base resume to tailor from")
    job_description: str = Field(..., description="Job description to tailor for")
    target_role: str = Field(..., description="Target role title")
    company_name: Optional[str] = Field(None, description="Target company name")
    industry: Optional[str] = Field(None, description="Target industry")
    save_as_version: bool = Field(True, description="Save tailored version")


class OptimizeForATSRequest(BaseModel):
    """Request to optimize resume for ATS parsing."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    resume_id: UUID = Field(..., description="Resume to optimize")
    save_as_version: bool = Field(True, description="Save optimized version")
    target_ats_systems: Optional[list[str]] = Field(None, description="Specific ATS systems to optimize for")


class ResumeVersionResponse(BaseModel):
    """Response for a single resume version."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    version_id: UUID
    base_resume_id: UUID
    version_name: str
    version_type: ResumeVersionType
    status: ResumeVersionStatus
    description: Optional[str] = None
    is_default: bool
    created_at: datetime
    updated_at: datetime
    version_number: int


class ResumeVersionDetailResponse(BaseModel):
    """Detailed response for a resume version."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    version_id: UUID
    base_resume_id: UUID
    version_name: str
    version_type: ResumeVersionType
    status: ResumeVersionStatus
    description: Optional[str] = None
    is_default: bool
    created_at: datetime
    updated_at: datetime
    version_number: int
    content: str  # Full resume content
    file_url: Optional[str] = None


class VersionHistoryItem(BaseModel):
    """Item in version history."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    version_id: UUID
    version_name: str
    version_type: ResumeVersionType
    created_at: datetime
    created_by: Optional[str] = None  # "user" | "ai_tailoring" | "ats_optimization"
    change_summary: Optional[str] = None


class ResumeVersionListResponse(BaseModel):
    """List of resume versions."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    items: list[ResumeVersionResponse]
    total: int
    page: int
    page_size: int
    pages: int


class CompareVersionsRequest(BaseModel):
    """Request to compare two resume versions."""
    version_id_1: UUID
    version_id_2: UUID


class VersionDifference(BaseModel):
    """A difference between two resume versions."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    section: str  # "skills", "experience", "education", etc.
    field: str
    value_in_v1: Optional[str] = None
    value_in_v2: Optional[str] = None
    change_type: str  # "added", "removed", "modified"


class CompareVersionsResponse(BaseModel):
    """Response comparing two resume versions."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    version_1: ResumeVersionResponse
    version_2: ResumeVersionResponse
    differences: list[VersionDifference]
    similarity_score: int = Field(..., ge=0, le=100, description="Similarity percentage")


class DownloadResumeRequest(BaseModel):
    """Request to download a resume version."""
    format: str = Field("pdf", description="pdf, docx, or txt")
    include_cover_letter: bool = Field(False)


class BulkVersionActionRequest(BaseModel):
    """Request for bulk operations on resume versions."""
    version_ids: list[UUID]
    action: str  # "archive", "delete", "set_default"
    target_status: Optional[ResumeVersionStatus] = None


class TailorResumeResponse(BaseModel):
    """Response after tailoring a resume."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    tailored_version_id: Optional[UUID] = None
    preview_content: str
    changes_made: list[str]
    alignment_score: int = Field(..., ge=0, le=100)
    estimated_improvement: Optional[str] = None
    save_version_prompt: bool = True
