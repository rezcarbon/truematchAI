"""Workable ATS connector for job and candidate sync.

Workable (https://www.workable.com) is a cloud-based ATS platform.
This connector uses Workable's REST API for importing jobs and candidates.
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.services.ats_connectors.base import ATSConnector, NormalizedCandidate, NormalizedJob

logger = logging.getLogger(__name__)


class WorkableConnector(ATSConnector):
    """Connector for Workable ATS."""

    def __init__(self, api_key: str, account_id: str, base_url: str = "https://api.workable.com/v1"):
        """Initialize Workable connector.

        Args:
            api_key: Workable API bearer token
            account_id: Workable account subdomain
            base_url: API base URL (default: production Workable API)
        """
        self.api_key = api_key
        self.account_id = account_id
        self.base_url = base_url
        self.provider = "workable"

    def _headers(self) -> dict[str, str]:
        """Return authenticated headers for Workable API."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "TrueMatch/1.0",
            "Content-Type": "application/json",
        }

    async def fetch_jobs(self, limit: int = 100) -> list[NormalizedJob]:
        """Fetch jobs from Workable."""
        jobs = []
        offset = 0
        max_pages = 10

        async with httpx.AsyncClient(timeout=30) as client:
            for page in range(max_pages):
                url = f"{self.base_url}/accounts/{self.account_id}/jobs"
                params = {"limit": min(limit, 100), "offset": offset}

                try:
                    response = await client.get(url, headers=self._headers(), params=params)
                    response.raise_for_status()
                    data = response.json()

                    for job_data in data.get("jobs", []):
                        job = NormalizedJob(
                            id=job_data["id"],
                            title=job_data.get("title", ""),
                            description=self._clean_html(job_data.get("description", "")),
                            status=self._map_job_status(job_data.get("state")),
                            location=job_data.get("location", ""),
                            external_ref=f"workable:job:{job_data['id']}",
                        )
                        jobs.append(job)

                    if len(data.get("jobs", [])) < limit:
                        break

                    offset += limit
                except httpx.HTTPError as e:
                    logger.error(f"Error fetching Workable jobs: {e}")
                    break

        return jobs

    async def fetch_candidates(self, limit: int = 100) -> list[NormalizedCandidate]:
        """Fetch candidates from Workable."""
        candidates = []
        offset = 0
        max_pages = 10

        async with httpx.AsyncClient(timeout=30) as client:
            for page in range(max_pages):
                url = f"{self.base_url}/accounts/{self.account_id}/candidates"
                params = {"limit": min(limit, 100), "offset": offset}

                try:
                    response = await client.get(url, headers=self._headers(), params=params)
                    response.raise_for_status()
                    data = response.json()

                    for candidate_data in data.get("candidates", []):
                        # Extract first email
                        email = None
                        for contact in candidate_data.get("contact_info", {}).get("emails", []):
                            if isinstance(contact, dict):
                                email = contact.get("email")
                            else:
                                email = contact
                            if email:
                                break

                        candidate = NormalizedCandidate(
                            id=candidate_data["id"],
                            name=candidate_data.get("name", "Unknown"),
                            email=email,
                            phone=candidate_data.get("phone"),
                            resume_url=candidate_data.get("resume_url"),
                            external_ref=f"workable:candidate:{candidate_data['id']}",
                            tags=[],
                        )
                        candidates.append(candidate)

                    if len(data.get("candidates", [])) < limit:
                        break

                    offset += limit
                except httpx.HTTPError as e:
                    logger.error(f"Error fetching Workable candidates: {e}")
                    break

        return candidates

    def _map_job_status(self, status: str) -> str:
        """Map Workable job status to normalized status."""
        mapping = {
            "published": "open",
            "draft": "draft",
            "closed": "closed",
            "archived": "archived",
        }
        return mapping.get(status, "open")

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        if not text:
            return ""
        import re
        return re.sub(r"<[^>]+>", "", text).strip()
