"""Request and response schemas for job search."""
from __future__ import annotations

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional
from enum import Enum


class JobSearchStatus(str, Enum):
    """Status of a job search."""
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    COMPLETED = "completed"


class SearchScope(str, Enum):
    """Scope of job search."""
    LOCAL = "local"
    REMOTE = "remote"
    HYBRID = "hybrid"
    ANY = "any"


class SeniorityLevel(str, Enum):
    """Seniority levels for job search."""
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class CreateJobSearchRequest(BaseModel):
    """Request to create a new job search."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    search_name: str = Field(..., min_length=1, max_length=255, description="Name for this search")
    keywords: list[str] = Field(..., description="Keywords to search for")
    target_roles: Optional[list[str]] = Field(None, description="Specific role titles")
    seniority_levels: Optional[list[SeniorityLevel]] = Field(None, description="Target seniority levels")
    industries: Optional[list[str]] = Field(None, description="Target industries")
    companies: Optional[list[str]] = Field(None, description="Companies to focus on")
    locations: Optional[list[str]] = Field(None, description="Geographic locations")
    scope: SearchScope = Field(SearchScope.ANY, description="Remote/local/hybrid preference")
    salary_min: Optional[int] = Field(None, ge=0, description="Minimum salary in USD")
    salary_max: Optional[int] = Field(None, ge=0, description="Maximum salary in USD")
    skills_required: Optional[list[str]] = Field(None, description="Must-have skills")
    skills_preferred: Optional[list[str]] = Field(None, description="Nice-to-have skills")
    years_experience_min: Optional[int] = Field(None, ge=0, description="Minimum years of experience")
    years_experience_max: Optional[int] = Field(None, description="Maximum years of experience")
    exclude_keywords: Optional[list[str]] = Field(None, description="Keywords to exclude")
    exclude_companies: Optional[list[str]] = Field(None, description="Companies to exclude")
    is_active: bool = Field(True, description="Start search as active")


class UpdateJobSearchRequest(BaseModel):
    """Request to update a job search."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    search_name: Optional[str] = None
    keywords: Optional[list[str]] = None
    target_roles: Optional[list[str]] = None
    seniority_levels: Optional[list[SeniorityLevel]] = None
    industries: Optional[list[str]] = None
    companies: Optional[list[str]] = None
    locations: Optional[list[str]] = None
    scope: Optional[SearchScope] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    skills_required: Optional[list[str]] = None
    skills_preferred: Optional[list[str]] = None
    is_active: Optional[bool] = None


class JobPosting(BaseModel):
    """A single job posting."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    job_id: str = Field(..., description="External job ID from source")
    title: str
    company: str
    location: str
    scope: SearchScope
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    description: str
    requirements: Optional[list[str]] = None
    benefits: Optional[list[str]] = None
    source: str  # "linkedin", "indeed", "glassdoor", "company_website", etc.
    posted_date: datetime
    apply_url: str
    match_score: int = Field(..., ge=0, le=100, description="Match score with your profile")


class SearchResultItem(BaseModel):
    """Item in job search results."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    job_posting: JobPosting
    match_reason: str
    matching_skills: list[str]
    missing_skills: list[str]
    matched_resume_version_id: Optional[UUID] = None


class JobSearchResponse(BaseModel):
    """Response for a job search."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    search_id: UUID
    search_name: str
    status: JobSearchStatus
    created_at: datetime
    updated_at: datetime
    total_results: int
    saved_count: int
    applied_count: int
    is_active: bool


class JobSearchDetailResponse(BaseModel):
    """Detailed response for a job search."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    search_id: UUID
    search_name: str
    status: JobSearchStatus
    created_at: datetime
    updated_at: datetime
    keywords: list[str]
    target_roles: Optional[list[str]] = None
    seniority_levels: Optional[list[SeniorityLevel]] = None
    scope: SearchScope
    salary_range: Optional[dict] = None
    total_results: int
    saved_count: int
    applied_count: int
    is_active: bool


class SearchResultsResponse(BaseModel):
    """Paginated search results."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    search_id: UUID
    results: list[SearchResultItem]
    total: int
    page: int
    page_size: int
    pages: int
    filters_applied: dict
    sort_by: str  # "match_score", "posted_date", "salary"


class SaveJobRequest(BaseModel):
    """Request to save a job."""
    job_id: str
    notes: Optional[str] = None


class SavedJobResponse(BaseModel):
    """Response for a saved job."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    saved_job_id: UUID
    job_posting: JobPosting
    saved_at: datetime
    notes: Optional[str] = None
    tagged: bool


class SearchStatsResponse(BaseModel):
    """Statistics for a job search."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    search_id: UUID
    total_results: int
    results_by_source: dict  # {"linkedin": 45, "indeed": 30}
    average_match_score: float
    salary_range_stats: dict  # {"min": 80000, "max": 150000, "avg": 115000}
    top_matching_roles: list[str]
    top_companies: list[str]
    created_at: datetime
    last_updated: datetime


class BulkSaveJobsRequest(BaseModel):
    """Request to bulk save jobs."""
    job_ids: list[str]
    tag_as: Optional[str] = None


class AlertSettingsRequest(BaseModel):
    """Request to set up search alerts."""
    search_id: UUID
    frequency: str  # "immediate", "daily", "weekly"
    notification_channel: str  # "email", "sms", "in_app"
    min_match_score: int = Field(50, ge=0, le=100, description="Alert only for jobs with this match score or higher")


class AlertSettingsResponse(BaseModel):
    """Response for alert settings."""
    alert_id: UUID
    search_id: UUID
    frequency: str
    notification_channel: str
    min_match_score: int
    is_active: bool
    created_at: datetime


class SearchListResponse(BaseModel):
    """List of job searches."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    items: list[JobSearchResponse]
    total: int
    page: int
    page_size: int
    pages: int
