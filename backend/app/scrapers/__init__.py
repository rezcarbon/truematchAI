"""
Job scraping and mass upload infrastructure.
"""

from app.scrapers.base import (
    JobPosting,
    JobScraper,
    APIBasedScraper,
    WebScraperBase,
    ScrapingFilters,
)
from app.scrapers.mass_upload import (
    MassUploadProcessor,
    CSVUploadProcessor,
    JSONUploadProcessor,
    FieldMappingValidator,
    DEFAULT_FIELD_MAPPINGS,
)

__all__ = [
    "JobPosting",
    "JobScraper",
    "APIBasedScraper",
    "WebScraperBase",
    "ScrapingFilters",
    "MassUploadProcessor",
    "CSVUploadProcessor",
    "JSONUploadProcessor",
    "FieldMappingValidator",
    "DEFAULT_FIELD_MAPPINGS",
]
