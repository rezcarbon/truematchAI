"""Greenhouse (Harvest API) connector.

Auth: HTTP Basic with the API key as the username and an empty password.
Docs: https://developers.greenhouse.io/harvest.html
"""
from __future__ import annotations

import logging

from app.config import settings
from app.services.ats_connectors.base import (
    ATSConnector,
    NormalizedCandidate,
    NormalizedJob,
    strip_html,
)

logger = logging.getLogger("truematch.ats.greenhouse")


class GreenhouseConnector(ATSConnector):
    provider = "greenhouse"

    @property
    def is_configured(self) -> bool:
        return bool(settings.greenhouse_api_key)

    def _client(self):
        import httpx

        # Harvest uses Basic auth: API key as username, blank password.
        return httpx.Client(
            base_url=settings.greenhouse_api_base.rstrip("/"),
            auth=(settings.greenhouse_api_key, ""),
            timeout=30.0,
            headers={"User-Agent": "TrueMatch-ATS/1.0"},
        )

    def list_jobs(self) -> list[NormalizedJob]:
        out: list[NormalizedJob] = []
        with self._client() as client:
            resp = client.get("/jobs", params={"per_page": 100})
            resp.raise_for_status()
            jobs = resp.json()
            for j in jobs:
                jid = str(j.get("id"))
                title = j.get("name") or "Untitled role"
                # Job description lives on the job's public posting.
                description = ""
                try:
                    jp = client.get(f"/jobs/{jid}/job_post")
                    if jp.status_code == 200:
                        description = strip_html((jp.json() or {}).get("content"))
                except Exception:  # noqa: BLE001 — posting is optional
                    pass
                out.append(NormalizedJob(external_id=jid, title=title, description=description or title))
        return out

    def list_candidates(self, job_external_id: str | None = None) -> list[NormalizedCandidate]:
        out: list[NormalizedCandidate] = []
        with self._client() as client:
            resp = client.get("/candidates", params={"per_page": 100})
            resp.raise_for_status()
            for c in resp.json():
                cid = str(c.get("id"))
                name = " ".join(filter(None, [c.get("first_name"), c.get("last_name")])) or "Candidate"
                emails = c.get("email_addresses") or []
                email = emails[0].get("value") if emails else None
                # Which job(s) this candidate applied to.
                job_id = None
                for app in c.get("applications") or []:
                    for job in app.get("jobs") or []:
                        job_id = str(job.get("id"))
                        break
                    if job_id:
                        break
                if job_external_id and job_id != str(job_external_id):
                    continue
                title = c.get("title") or ""
                company = c.get("company") or ""
                summary = ". ".join(filter(None, [name, title, company])) or name
                out.append(
                    NormalizedCandidate(
                        external_id=cid,
                        name=name,
                        email=email,
                        summary=summary,
                        job_external_id=job_id,
                        tags=[str(t) for t in (c.get("tags") or [])],
                    )
                )
        return out
