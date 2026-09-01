"""
Schemas for scraper management API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ScraperConfigResponse(BaseModel):
    """Scraper configuration response"""

    id: str = Field(..., description="Configuration ID")
    source_type: str = Field(..., description="Source type (usajobs, linkedin, indeed, etc.)")
    enabled: bool = Field(..., description="Whether scraper is enabled")
    poll_hours: int = Field(..., description="Hours between polls")
    last_run: Optional[datetime] = Field(None, description="Last execution time")
    next_run: Optional[datetime] = Field(None, description="Next scheduled execution time")
    legal_approved: bool = Field(..., description="Whether legal approval has been given")
    has_api_key: bool = Field(..., description="Whether API key is configured (for API-based scrapers)")


class ScraperConfigCreateRequest(BaseModel):
    """Request to create scraper configuration"""

    source_type: str = Field(
        ...,
        description="Source type (usajobs, ziprecruiter, linkedin, indeed, glassdoor, theirstack)",
    )
    enabled: bool = Field(default=False, description="Enable immediately")
    poll_hours: int = Field(default=24, description="Poll interval in hours")
    config: dict = Field(
        default_factory=dict,
        description="Source-specific configuration (API keys, filters, etc.)",
    )


class ListScrapersResponse(BaseModel):
    """List of scraper configurations"""

    scrapers: list[ScraperConfigResponse] = Field(..., description="Configured scrapers")


class ScraperRunResponse(BaseModel):
    """Single scraper run result"""

    id: str = Field(..., description="Run ID")
    status: str = Field(..., description="Status (pending, processing, completed, failed)")
    started_at: Optional[datetime] = Field(None, description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    jobs_found: int = Field(..., description="Jobs discovered")
    jobs_processed: int = Field(..., description="Jobs successfully added")
    jobs_failed: int = Field(..., description="Jobs with errors")


class ListScraperRunsResponse(BaseModel):
    """List of scraper runs"""

    config_id: str = Field(..., description="Configuration ID")
    runs: list[ScraperRunResponse] = Field(..., description="Recent runs")
