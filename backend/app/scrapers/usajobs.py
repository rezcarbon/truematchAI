"""
USAJOBS.gov API scraper - Safe, official API for US federal job postings.

USAJOBS is the official job board for the US federal government. The API is:
- ✅ Officially supported and documented
- ✅ No legal restrictions
- ✅ Free tier available
- ✅ Stable and reliable

Legal Status: SAFE - No TOS violations
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import httpx

from app.models.job_scraping import JobSourceType
from app.scrapers.base import APIBasedScraper, JobPosting, ScrapingFilters


class USAJobsScraper(APIBasedScraper):
    """
    Scraper for USAJOBS.gov using official API.

    Configuration required:
    {
        "api_key": "your-usajobs-api-key",
        "api_url": "https://data.usajobs.gov/api/search"
    }

    Filters supported:
    - query: Search keywords (e.g., "software engineer", "data scientist")
    - location: Filter by location
    - job_type: E.g., "Full-time", "Part-time"
    """

    def __init__(self, config: dict | None = None):
        super().__init__(JobSourceType.usajobs, config)
        self.api_url = self.config.get(
            "api_url", "https://data.usajobs.gov/api/search"
        )

    async def scrape(self, filters: dict | None = None) -> list[JobPosting]:
        """
        Scrape jobs from USAJOBS API.

        Args:
            filters: Optional filters (query, location, job_type, etc.)

        Returns:
            List of JobPosting objects
        """
        if not filters:
            filters = {}

        await self.validate()

        postings = []

        try:
            async with httpx.AsyncClient() as client:
                # Build query parameters
                params = {
                    "api_key": self.api_key,
                }

                if "query" in filters:
                    params["keyword"] = filters["query"]

                if "location" in filters:
                    params["locationcode"] = filters["location"]

                if "job_type" in filters:
                    params["jobtype"] = filters["job_type"]

                # Pagination
                page_number = 1
                max_pages = filters.get("max_pages", 5)  # Limit to avoid excessive requests

                while page_number <= max_pages:
                    params["page"] = page_number

                    response = await client.get(
                        self.api_url,
                        params=params,
                        timeout=30.0,
                    )
                    response.raise_for_status()

                    data = response.json()

                    # Check if we got results
                    if "SearchResult" not in data or "SearchResultItems" not in data["SearchResult"]:
                        break

                    search_result = data["SearchResult"]
                    items = search_result.get("SearchResultItems", [])

                    if not items:
                        break

                    # Parse each result
                    for item in items:
                        job_data = item.get("MatchedObjectDescriptor", {})

                        # Map USAJOBS fields to standardized format
                        posting = JobPosting(
                            title=job_data.get("JobTitle", "Untitled"),
                            description=job_data.get("JobSummary", ""),
                            company=job_data.get("OrganizationName", "US Government"),
                            location=self._format_location(job_data.get("JobLocation", [])),
                            job_type="Full-time",  # USAJOBS mostly has full-time
                            salary_min=self._parse_salary_min(job_data.get("PositionSalary", {})),
                            salary_max=self._parse_salary_max(job_data.get("PositionSalary", {})),
                            posted_date=self._parse_date(job_data.get("PublicationStartDate")),
                            external_url=job_data.get("ApplyURI", [None])[0] if job_data.get("ApplyURI") else None,
                            external_id=item.get("MatchedObjectId"),
                            source="usajobs",
                            raw_data=job_data,
                        )

                        postings.append(posting)

                    # Check if there are more pages
                    total_results = search_result.get("TotalMatchedCount", 0)
                    if page_number * 25 >= total_results:  # USAJOBS returns 25 per page
                        break

                    page_number += 1

                    # Respect rate limiting
                    self.rate_limit_info["requests_made"] += 1

        except httpx.RequestError as e:
            raise Exception(f"Failed to scrape USAJOBS: {str(e)}")

        return postings

    async def validate(self) -> bool:
        """Validate USAJOBS API configuration"""
        # Call parent validation
        await super().validate()

        # Try a simple search to verify the API is working
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.api_url,
                    params={"api_key": self.api_key, "page": 1},
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

                # Verify we got a valid response
                if "SearchResult" not in data:
                    raise ValueError("Invalid API response format")

                return True
        except Exception as e:
            raise ValueError(f"USAJOBS API validation failed: {str(e)}")

    async def get_rate_limit(self) -> dict:
        """
        Get rate limit status.

        USAJOBS: 15 requests per second (for authenticated users)
        """
        return {
            "requests_remaining": None,  # USAJOBS doesn't return this header
            "requests_total": 15,  # Per second limit
            "reset_at": datetime.now() + timedelta(seconds=1),
            "is_rate_limited": self.rate_limit_info["requests_made"] > 15,
        }

    @staticmethod
    def _format_location(location_data: list | dict) -> str | None:
        """Format USAJOBS location data to string"""
        if isinstance(location_data, list) and location_data:
            loc = location_data[0]
        elif isinstance(location_data, dict):
            loc = location_data
        else:
            return None

        city = loc.get("CityName")
        state = loc.get("StateCode")
        country = loc.get("CountryCode")

        if city and state:
            return f"{city}, {state}"
        elif city:
            return city
        elif state:
            return state
        return None

    @staticmethod
    def _parse_salary_min(salary_data: dict) -> int | None:
        """Extract minimum salary from USAJOBS salary range"""
        if not salary_data:
            return None

        salary_range = salary_data.get("SalaryRangeFrom")
        return int(salary_range) if salary_range else None

    @staticmethod
    def _parse_salary_max(salary_data: dict) -> int | None:
        """Extract maximum salary from USAJOBS salary range"""
        if not salary_data:
            return None

        salary_range = salary_data.get("SalaryRangeTo")
        return int(salary_range) if salary_range else None

    @staticmethod
    def _parse_date(date_str: str | None) -> datetime | None:
        """Parse USAJOBS date format"""
        if not date_str:
            return None

        try:
            # USAJOBS typically uses ISO format
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
