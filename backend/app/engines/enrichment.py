"""External-evidence enrichment (Pillar 5).

Turns supplementary links/identifiers a candidate provides (portfolio URLs,
GitHub, ORCID, publication DOIs, patent numbers) from UNVERIFIED CLAIMS into
PROVENANCED EVIDENCE the reasoning engine can weigh and the recruiter can trust.

Each item is fetched from its primary source and tagged with a verification
status. When `settings.enrichment_enabled` is False (default — keeps the
pipeline offline/test-safe), nothing is fetched and every item is recorded as
`unverified` with a reason, so downstream reasoning still knows the link exists
but must not treat it as confirmed.

No candidate PII or secrets are logged. Each fetch is independently guarded so
one bad link never fails the batch.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from app.config import settings

logger = logging.getLogger("truematch.enrichment")

# Verification statuses surfaced to the reasoner and recruiter.
VERIFIED = "verified"
UNVERIFIED = "unverified"
NOT_FOUND = "not_found"
ERROR = "error"

_GITHUB_RE = re.compile(r"github\.com/([A-Za-z0-9_.-]+)(?:/([A-Za-z0-9_.-]+))?", re.I)
_ORCID_RE = re.compile(r"(\d{4}-\d{4}-\d{4}-\d{3}[\dX])", re.I)
_DOI_RE = re.compile(r"(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)", re.I)
# IPOS Singapore application numbers, e.g. 10202601003R.
_IPOS_RE = re.compile(r"\b(\d{11}[A-Z])\b")


def classify_ref(ref: str) -> str:
    """Classify a supplementary reference into a source type."""
    r = ref.strip()
    low = r.lower()
    if "github.com" in low:
        return "github"
    if "orcid.org" in low or _ORCID_RE.fullmatch(r):
        return "orcid"
    if "linkedin.com" in low:
        return "linkedin"
    if _DOI_RE.search(r) or "doi.org" in low or "zenodo" in low:
        return "doi"
    if _IPOS_RE.fullmatch(r):
        return "patent"
    return "web"


def _collect_refs(supplementary: dict | None) -> list[tuple[str, str]]:
    """Flatten supplementary into (source_type, ref) pairs."""
    s = supplementary or {}
    refs: list[tuple[str, str]] = []
    for url in s.get("portfolio_urls", []) or []:
        refs.append((classify_ref(url), url))
    for orcid in ([s.get("orcid")] if s.get("orcid") else []):
        refs.append(("orcid", orcid))
    for doi in s.get("publication_dois", []) or []:
        refs.append(("doi", doi))
    for pat in s.get("patent_numbers", []) or []:
        refs.append(("patent", pat))
    return refs


def enrich_supplementary(supplementary: dict | None) -> list[dict[str, Any]]:
    """Return a list of provenanced evidence items for the supplementary links."""
    refs = _collect_refs(supplementary)
    if not refs:
        return []
    if not settings.enrichment_enabled:
        return [
            {
                "source_type": st,
                "ref": ref,
                "status": UNVERIFIED,
                "summary": "Not fetched (enrichment disabled in this environment).",
            }
            for st, ref in refs
        ]

    import httpx  # lazy: only needed when enrichment is enabled

    out: list[dict[str, Any]] = []
    with httpx.Client(
        timeout=settings.enrichment_timeout_seconds,
        headers={"User-Agent": "TrueMatch-Enrichment/1.0"},
        follow_redirects=True,
    ) as client:
        for source_type, ref in refs:
            try:
                out.append(_fetch_one(client, source_type, ref))
            except Exception as exc:  # noqa: BLE001 - never let one link fail the batch
                logger.warning("Enrichment failed for %s (%s)", source_type, exc.__class__.__name__)
                out.append(
                    {"source_type": source_type, "ref": ref, "status": ERROR,
                     "summary": "Could not retrieve this source."}
                )
    return out


def _fetch_one(client: Any, source_type: str, ref: str) -> dict[str, Any]:
    if source_type == "github":
        return _fetch_github(client, ref)
    if source_type == "doi":
        return _resolve_doi(client, ref)
    if source_type == "orcid":
        return _verify_orcid(client, ref)
    if source_type == "patent":
        return _note_patent(ref)
    return _check_url(client, ref)


def _fetch_github(client: Any, ref: str) -> dict[str, Any]:
    m = _GITHUB_RE.search(ref)
    if not m:
        return {"source_type": "github", "ref": ref, "status": NOT_FOUND, "summary": "Unparseable GitHub URL."}
    user, repo = m.group(1), m.group(2)
    if repo:
        resp = client.get(f"https://api.github.com/repos/{user}/{repo}")
        if resp.status_code == 200:
            d = resp.json()
            return {
                "source_type": "github", "ref": ref, "status": VERIFIED,
                "summary": f"Repo {d.get('full_name')} — {d.get('stargazers_count', 0)} stars, "
                           f"primary language {d.get('language') or 'n/a'}.",
                "data": {"stars": d.get("stargazers_count"), "forks": d.get("forks_count"),
                         "language": d.get("language"), "updated_at": d.get("updated_at")},
            }
    else:
        resp = client.get(f"https://api.github.com/users/{user}")
        if resp.status_code == 200:
            d = resp.json()
            return {
                "source_type": "github", "ref": ref, "status": VERIFIED,
                "summary": f"GitHub user {d.get('login')} — {d.get('public_repos', 0)} public repos, "
                           f"{d.get('followers', 0)} followers.",
                "data": {"public_repos": d.get("public_repos"), "followers": d.get("followers")},
            }
    return {"source_type": "github", "ref": ref, "status": NOT_FOUND, "summary": "GitHub resource not found."}


def _resolve_doi(client: Any, ref: str) -> dict[str, Any]:
    m = _DOI_RE.search(ref)
    doi = m.group(1) if m else ref
    # Crossref first; DataCite (covers Zenodo) as a fallback.
    cr = client.get(f"https://api.crossref.org/works/{doi}")
    if cr.status_code == 200:
        msg = cr.json().get("message", {})
        title = (msg.get("title") or ["(untitled)"])[0]
        return {
            "source_type": "doi", "ref": doi, "status": VERIFIED,
            "summary": f"Published work: \"{title}\" ({msg.get('type', 'n/a')}).",
            "data": {"title": title, "type": msg.get("type"),
                     "container": (msg.get("container-title") or [None])[0]},
        }
    dc = client.get(f"https://api.datacite.org/dois/{doi}")
    if dc.status_code == 200:
        attrs = dc.json().get("data", {}).get("attributes", {})
        titles = attrs.get("titles") or [{}]
        return {
            "source_type": "doi", "ref": doi, "status": VERIFIED,
            "summary": f"Registered work: \"{titles[0].get('title', '(untitled)')}\" "
                       f"via {attrs.get('publisher', 'n/a')}.",
            "data": {"publisher": attrs.get("publisher"), "year": attrs.get("publicationYear")},
        }
    return {"source_type": "doi", "ref": doi, "status": NOT_FOUND, "summary": "DOI did not resolve."}


def _verify_orcid(client: Any, ref: str) -> dict[str, Any]:
    m = _ORCID_RE.search(ref)
    if not m:
        return {"source_type": "orcid", "ref": ref, "status": NOT_FOUND, "summary": "Unparseable ORCID."}
    orcid = m.group(1)
    resp = client.get(f"https://pub.orcid.org/v3.0/{orcid}", headers={"Accept": "application/json"})
    if resp.status_code == 200:
        d = resp.json()
        name = (((d.get("person") or {}).get("name") or {}).get("credit-name") or {}).get("value")
        works = ((d.get("activities-summary") or {}).get("works") or {}).get("group") or []
        return {
            "source_type": "orcid", "ref": orcid, "status": VERIFIED,
            "summary": f"ORCID profile{' for ' + name if name else ''} with {len(works)} registered works.",
            "data": {"works_count": len(works)},
        }
    return {"source_type": "orcid", "ref": orcid, "status": NOT_FOUND, "summary": "ORCID not found."}


def _note_patent(ref: str) -> dict[str, Any]:
    # No public machine API for the IPOS Singapore register; record for manual
    # verification rather than claiming we confirmed it.
    return {
        "source_type": "patent", "ref": ref, "status": UNVERIFIED,
        "summary": "Patent application number recorded; verify on the IPOS Singapore register "
                   "(no public API). Treat as a claim pending manual confirmation.",
    }


def _check_url(client: Any, ref: str) -> dict[str, Any]:
    resp = client.head(ref)
    status = VERIFIED if resp.status_code < 400 else NOT_FOUND
    return {"source_type": "web", "ref": ref, "status": status,
            "summary": f"URL responded {resp.status_code}." if status == VERIFIED else "URL not reachable."}
