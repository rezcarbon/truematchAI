"""Lever connector.

Auth: HTTP Basic with the API key as the username (blank password).
Docs: https://hire.lever.co/developer/documentation
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

logger = logging.getLogger("truematch.ats.lever")


class LeverConnector(ATSConnector):
    provider = "lever"

    @property
    def is_configured(self) -> bool:
        return bool(settings.lever_api_key)

    def _client(self):
        import httpx

        return httpx.Client(
            base_url=settings.lever_api_base.rstrip("/"),
            auth=(settings.lever_api_key, ""),
            timeout=30.0,
            headers={"User-Agent": "TrueMatch-ATS/1.0"},
        )

    def list_jobs(self) -> list[NormalizedJob]:
        out: list[NormalizedJob] = []
        with self._client() as client:
            resp = client.get("/postings", params={"limit": 100})
            resp.raise_for_status()
            for p in (resp.json() or {}).get("data", []):
                pid = str(p.get("id"))
                title = p.get("text") or "Untitled role"
                content = p.get("content") or {}
                description = content.get("descriptionPlain") or strip_html(content.get("description"))
                out.append(NormalizedJob(external_id=pid, title=title, description=description or title))
        return out

    def list_candidates(self, job_external_id: str | None = None) -> list[NormalizedCandidate]:
        out: list[NormalizedCandidate] = []
        with self._client() as client:
            params = {"limit": 100}
            if job_external_id:
                params["posting_id"] = job_external_id
            resp = client.get("/opportunities", params=params)
            resp.raise_for_status()
            for o in (resp.json() or {}).get("data", []):
                oid = str(o.get("id"))
                name = o.get("name") or "Candidate"
                emails = o.get("emails") or []
                email = emails[0] if emails else None
                headline = o.get("headline") or ""
                postings = o.get("postings") or []
                job_id = str(postings[0]) if postings else job_external_id
                summary = ". ".join(filter(None, [name, headline])) or name
                out.append(
                    NormalizedCandidate(
                        external_id=oid,
                        name=name,
                        email=email,
                        summary=summary,
                        job_external_id=str(job_id) if job_id else None,
                        tags=[str(t) for t in (o.get("tags") or [])],
                    )
                )
        return out
