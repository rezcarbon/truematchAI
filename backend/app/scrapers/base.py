"""
Base classes for job scraping from various sources.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.models.job_scraping import JobSourceType


@dataclass
class JobPosting:
    """Standardized job posting data structure"""
    title: str
    description: str
    company: str
    location: Optional[str] = None
    job_type: Optional[str] = None  # Full-time, Part-time, Contract, etc.
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    posted_date: Optional[datetime] = None
    external_url: Optional[str] = None
    external_id: Optional[str] = None
    source: str = "unknown"
    raw_data: dict = field(default_factory=dict)

    def fingerprint_data(self) -> str:
        """Generate deduplication fingerprint"""
        import hashlib

        # Normalize text for comparison
        normalized_title = self.title.lower().strip()
        normalized_company = self.company.lower().strip()

        # Create a fingerprint from title + company + first 500 chars of description
        fingerprint_text = f"{normalized_title}|{normalized_company}|{self.description[:500]}"
        return hashlib.sha256(fingerprint_text.encode()).hexdigest()


class JobScraper(ABC):
    """Abstract base class for all job scrapers"""

    def __init__(self, source_type: JobSourceType, config: dict | None = None):
        self.source_type = source_type
        self.config = config or {}
        self.rate_limit_info = {
            "requests_made": 0,
            "requests_remaining": None,
            "reset_at": None,
        }

    @abstractmethod
    async def scrape(self, filters: dict | None = None) -> list[JobPosting]:
        """
        Scrape job postings from the source.

        Args:
            filters: Optional filters (query, location, company, etc.)

        Returns:
            List of JobPosting objects

        Raises:
            ValueError: If configuration is invalid
            Exception: If scraping fails (network, auth, etc.)
        """
        pass

    @abstractmethod
    async def validate(self) -> bool:
        """
        Validate that the scraper is properly configured and can reach the source.

        Returns:
            True if validation passes

        Raises:
            ValueError: With details about what's misconfigured
        """
        pass

    @abstractmethod
    async def get_rate_limit(self) -> dict:
        """
        Get current rate limit status.

        Returns:
            {
                "requests_remaining": int or None,
                "requests_total": int or None,
                "reset_at": datetime or None,
                "is_rate_limited": bool,
            }
        """
        pass

    async def handle_rate_limit(self, wait_seconds: int | None = None) -> None:
        """
        Handle rate limiting by waiting or raising an error.

        Args:
            wait_seconds: Optional wait time before retry

        Raises:
            RuntimeError: If rate limited and wait not allowed
        """
        if wait_seconds:
            import asyncio
            await asyncio.sleep(wait_seconds)
        else:
            raise RuntimeError("Rate limit exceeded")

    async def cleanup(self) -> None:
        """Cleanup resources (browser sessions, connections, etc.)"""
        pass


class APIBasedScraper(JobScraper):
    """Base class for scrapers using official APIs"""

    def __init__(self, source_type: JobSourceType, config: dict | None = None):
        super().__init__(source_type, config)
        self.api_key = self.config.get("api_key")
        self.api_url = self.config.get("api_url")

    async def validate(self) -> bool:
        """Validate API key and connectivity"""
        if not self.api_key:
            raise ValueError(f"API key required for {self.source_type}")
        if not self.api_url:
            raise ValueError(f"API URL required for {self.source_type}")

        # Test connectivity
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.head(self.api_url, timeout=5.0)
                return response.status_code < 500
        except Exception as e:
            raise ValueError(f"Cannot reach API: {str(e)}")


class WebScraperBase(JobScraper):
    """Base class for web scrapers using Playwright"""

    def __init__(self, source_type: JobSourceType, config: dict | None = None):
        super().__init__(source_type, config)
        self.browser = None
        self.context = None

        # Legal approval required for direct scrapers
        self.requires_legal_approval = source_type in [
            JobSourceType.linkedin,
            JobSourceType.indeed,
            JobSourceType.glassdoor,
        ]

        # Rate limiting (respectful delays in seconds)
        self.min_request_delay = self.config.get("min_request_delay", 15)

    async def validate(self) -> bool:
        """Validate web scraper setup"""
        # Check if legal approval is required
        if self.requires_legal_approval:
            if not self.config.get("legal_approved"):
                raise ValueError(
                    f"{self.source_type} scraping requires legal approval. "
                    f"This is flagged as HIGH/VERY HIGH legal risk."
                )

        # Try to initialize browser
        try:
            from playwright.async_api import async_playwright

            p = await async_playwright().start()
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            await context.close()
            await browser.close()
            await p.stop()
            return True
        except Exception as e:
            raise ValueError(f"Cannot initialize Playwright: {str(e)}")

    async def get_browser_context(self):
        """Get or create a Playwright browser context"""
        if not self.browser:
            from playwright.async_api import async_playwright

            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"
            )

        return self.context

    async def cleanup(self) -> None:
        """Clean up browser resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


# Example filter schema for scraping requests
class ScrapingFilters:
    """Common filters for scraping requests"""

    def __init__(
        self,
        query: str | None = None,
        location: str | None = None,
        company: str | None = None,
        job_type: str | None = None,
        min_salary: int | None = None,
        max_salary: int | None = None,
        limit: int | None = None,
    ):
        self.query = query
        self.location = location
        self.company = company
        self.job_type = job_type
        self.min_salary = min_salary
        self.max_salary = max_salary
        self.limit = limit or 50  # Default limit

    def to_dict(self) -> dict:
        return {
            k: v for k, v in self.__dict__.items() if v is not None
        }
