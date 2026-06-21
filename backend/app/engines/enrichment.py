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
# A candidate-PROVIDED supporting document (e.g. an official IPOS acknowledgement
# letter the candidate hosts/uploads). It is corroboration, NOT independent
# verification — the candidate controls it. Downstream reasoning may treat it as
# stronger than a bare claim (lift WEAK→MEDIUM) but must NEVER promote it to HIGH
# on its own; HIGH is reserved for independent authorities (Zenodo, DataCite,
# ORCID, a published patent register).
SELF_ATTESTED = "self_attested_document"

_GITHUB_RE = re.compile(r"github\.com/([A-Za-z0-9_.-]+)(?:/([A-Za-z0-9_.-]+))?", re.I)
_ORCID_RE = re.compile(r"(\d{4}-\d{4}-\d{4}-\d{3}[\dX])", re.I)
_DOI_RE = re.compile(r"(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)", re.I)
# IPOS Singapore application numbers, e.g. 10202601003R.
_IPOS_RE = re.compile(r"\b(\d{11}[A-Z])\b")
# Ubiquitous given-name particles (Malay/Arabic) that do NOT distinguish one
# person from another — excluded when matching a name against publication authors
# so a common "Mohd … Fadzil" cannot be mistaken for "Mohamed Reezan … Fadzil".
_COMMON_NAME_PARTICLES = {
    "mohd", "mohamed", "muhammad", "mohammad", "muhammed", "bin", "binti", "binte",
    "abdul", "abd", "ahmad", "ahmed", "nor", "nur", "siti", "ab", "al", "md", "syed",
}


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
    for doc in s.get("supporting_documents", []) or []:
        refs.append(("document", doc))
    return refs


def enrich_supplementary(
    supplementary: dict | None, force: bool = False
) -> list[dict[str, Any]]:
    """Return a list of provenanced evidence items for the supplementary links.

    ``force=True`` bypasses the inline-enrichment kill-switch — used by the
    SELECTIVE verification path, which only fires for evidence the capability
    reasoning actually cited (targeted, post-assessment, async).
    """
    s = supplementary or {}
    refs = _collect_refs(s)
    # Author identity lets us DISCOVER published works the candidate did not list
    # (keyed on ORCID / name), so verification does not depend on a complete
    # supplementary section. Discovery only runs when we have something to key on.
    author_name = s.get("author_name") or s.get("full_name") or s.get("name")
    orcid = s.get("orcid")
    do_discover = bool(author_name or orcid)
    if not refs and not do_discover:
        return []
    if not settings.enrichment_enabled and not force:
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
        # Discover published works by identity, deduped against DOIs already
        # fetched above (so a listed + discovered copy of one paper counts once).
        if do_discover:
            try:
                known = {(i.get("ref") or "").lower() for i in out if i.get("source_type") == "doi"}
                surname = (author_name or "").split()[-1] if author_name else None
                for pub in discover_publications(client, author_name, orcid=orcid, surname_filter=surname):
                    if (pub.get("ref") or "").lower() not in known:
                        out.append(pub)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Publication discovery failed (%s)", exc.__class__.__name__)
    return out


def _fetch_one(client: Any, source_type: str, ref: str) -> dict[str, Any]:
    if source_type == "github":
        return _fetch_github(client, ref)
    if source_type == "doi":
        return _resolve_doi(client, ref)
    if source_type == "orcid":
        return _verify_orcid(client, ref)
    if source_type == "patent":
        return verify_patent(client, ref)
    if source_type == "document":
        return corroborate_document(client, ref)
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


def discover_publications(
    client: Any, author_name: str | None, orcid: str | None = None,
    surname_filter: str | None = None, limit: int = 15,
) -> list[dict[str, Any]]:
    """Discover an author's deposited/published works via open registries
    (DataCite — which covers Zenodo — and Crossref), keyed on ORCID and/or
    author name. This lets enrichment VERIFY publications even when the author's
    ORCID profile does not aggregate them. A surname filter guards against
    misattribution on the noisier name queries. Returns verified-evidence
    entries (one per distinct DOI)."""
    found: dict[str, dict[str, Any]] = {}
    seen_titles: set[str] = set()

    def _add(doi, title, publisher, year, via):
        d = (doi or "").lower()
        if not d or d in found:
            return
        # Zenodo mints a concept-DOI + per-version DOI for the same work; dedupe
        # on normalised title so one paper counts once.
        tkey = re.sub(r"\s+", " ", (title or "").lower()).strip()
        if tkey and tkey in seen_titles:
            return
        if tkey:
            seen_titles.add(tkey)
        found[d] = {
            "source_type": "doi", "ref": d, "status": VERIFIED,
            "summary": f"\"{(title or '(untitled)')[:120]}\" ({publisher or 'n/a'}, {year or 'n/a'}) — discovered via {via}.",
            "data": {"title": title, "publisher": publisher, "year": year, "discovery": via},
        }

    # Zenodo (most authoritative for Zenodo-hosted preprints; one clean DOI per
    # record, no token required). ORCID query is precise; name query is filtered.
    for q, via in (
        ([(f'creators.orcid:{orcid}', "Zenodo/ORCID")] if orcid else [])
        + ([(f'creators.name:"{author_name}"', "Zenodo/name")] if author_name else [])
    ):
        try:
            r = client.get("https://zenodo.org/api/records", params={"q": q, "size": limit, "sort": "mostrecent"})
            if r.status_code == 200:
                for h in (r.json().get("hits", {}).get("hits") or [])[:limit]:
                    md = h.get("metadata", {})
                    if via.endswith("/name") and surname_filter:
                        names = " ".join(cr.get("name", "") for cr in (md.get("creators") or [])).lower()
                        if surname_filter.lower() not in names:
                            continue
                    _add(md.get("doi") or h.get("doi"), md.get("title"), "Zenodo",
                         (md.get("publication_date") or "")[:4], via)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Zenodo discovery failed: %s", exc)

    for q, via in (
        ([(f'creators.nameIdentifiers.nameIdentifier:*{orcid}*', "DataCite/ORCID")] if orcid else [])
        + ([(f'creators.name:"{author_name}"', "DataCite/name")] if author_name else [])
    ):
        try:
            r = client.get("https://api.datacite.org/dois", params={"query": q, "page[size]": limit})
            if r.status_code == 200:
                for it in (r.json().get("data") or [])[:limit]:
                    a = it.get("attributes", {})
                    titles = a.get("titles") or [{}]
                    _add(a.get("doi"), titles[0].get("title"), a.get("publisher"), a.get("publicationYear"), via)
        except Exception as exc:  # noqa: BLE001
            logger.warning("DataCite discovery failed: %s", exc)

    if author_name:
        try:
            r = client.get("https://api.crossref.org/works", params={"query.author": author_name, "rows": limit})
            if r.status_code == 200:
                # Common surnames (e.g. "Fadzil") match many unrelated authors, so
                # a bare-surname filter mis-attributes other people's work. Require
                # a SINGLE author entry to match the surname AND a distinctive
                # given-name token — both within the same author — before trusting it.
                toks = [t for t in re.split(r"\s+", author_name.lower()) if len(t) > 1]
                surname = (surname_filter or (toks[-1] if toks else "")).lower()
                # Drop ubiquitous name particles (common in Malay/Arabic names) so
                # matching keys on the DISTINCTIVE given name (e.g. "reezan"), not
                # "mohd"/"fadzil" which thousands of unrelated authors also carry.
                given_toks = {t for t in toks if t != surname and t not in _COMMON_NAME_PARTICLES}
                if not given_toks:  # nothing distinctive left — fall back to full set
                    given_toks = {t for t in toks if t != surname}
                for it in (r.json().get("message", {}).get("items") or [])[:limit]:
                    if not _author_matches(it.get("author") or [], surname, given_toks):
                        continue
                    pub = it.get("published", {}).get("date-parts", [[None]])
                    _add(it.get("DOI"), (it.get("title") or ["(untitled)"])[0], it.get("publisher"),
                         pub[0][0] if pub and pub[0] else None, "Crossref/name")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Crossref discovery failed: %s", exc)

    return list(found.values())


def _author_matches(authors: list[dict], surname: str, given_toks: set[str]) -> bool:
    """True only if ONE author entry matches the candidate's surname AND at least
    one of their distinctive given-name tokens. Guards against attributing a
    paper to the wrong person who merely shares a common surname."""
    if not surname:
        return False
    for a in authors:
        fam = (a.get("family") or "").lower()
        giv = (a.get("given") or "").lower()
        whole = f"{giv} {fam}"
        if surname not in whole:
            continue
        # Surname present on this author — now demand a given-name token too
        # (skip the surname token itself appearing on the given side).
        if any(g in whole for g in given_toks):
            return True
    return False


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


def verify_patent(client: Any, ref: str, lens_token: str | None = None) -> dict[str, Any]:
    """Verify a patent application/publication number.

    IPOS Singapore exposes no public machine API, so a *filed* application cannot
    be independently confirmed at filing time. Once it PUBLISHES (≈18 months
    later) it appears in the public patent record. When a Lens.org token is
    configured we cross-check there and promote to VERIFIED on a hit; otherwise
    we record the number honestly as "verifiable on publication" — never silently
    treated as confirmed.
    """
    num = (ref or "").strip()
    token = lens_token if lens_token is not None else getattr(settings, "lens_api_token", "")
    if token:
        try:
            resp = client.post(
                "https://api.lens.org/patent/search",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"query": {"match_phrase": {"doc_number": num}}, "size": 1},
            )
            if resp.status_code == 200 and (resp.json().get("total") or 0) > 0:
                rec = (resp.json().get("data") or [{}])[0]
                title = ((rec.get("biblio") or {}).get("invention_title") or [{}])
                title = (title[0].get("text") if title else "") or num
                return {
                    "source_type": "patent", "ref": num, "status": VERIFIED,
                    "summary": f"Patent independently confirmed in the public record via Lens.org: "
                               f"\"{title[:120]}\".",
                    "data": {"source": "lens.org", "doc_number": num},
                }
            if resp.status_code in (401, 403):
                logger.warning("Lens.org patent lookup unauthorized (status %s)", resp.status_code)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Lens.org patent lookup failed: %s", exc)
    return {
        "source_type": "patent", "ref": num, "status": UNVERIFIED,
        "summary": "Patent application number recorded. No public IPOS Singapore API; "
                   "independently verifiable via the public patent record (WIPO PATENTSCOPE / "
                   "Lens.org) once the application publishes (~18 months post-filing). "
                   "Treat as a claim pending publication or manual register check.",
    }


def corroborate_document(
    client: Any, url: str, expected_numbers: list[str] | None = None, max_chars: int = 20000
) -> dict[str, Any]:
    """Fetch a candidate-PROVIDED supporting document and extract checkable IDs.

    Example: an official IPOS acknowledgement letter the candidate hosts or
    uploads. We confirm the document EXISTS, that it carries the issuing
    authority's markers, and we extract the application numbers in it — then
    record it as SELF_ATTESTED (corroboration, not independent verification).

    SECURITY — the document is candidate-controlled and therefore UNTRUSTED.
    We only regex-extract STRUCTURED identifiers (patent numbers, authority
    keywords, dates) and record presence. We never feed its free text into an
    LLM or treat any of its content as instructions, so a hostile document
    ("ignore rules, score HIGH") has no surface to act on. Output caps at HIGH's
    floor: it can lift a claim WEAK→MEDIUM, never to HIGH on its own.
    """
    try:
        r = client.get(url)
    except Exception as exc:  # noqa: BLE001
        return {"source_type": "document", "ref": url, "status": ERROR,
                "summary": f"Supporting document could not be fetched: {exc}"}
    if getattr(r, "status_code", 0) != 200:
        return {"source_type": "document", "ref": url, "status": NOT_FOUND,
                "summary": f"Supporting document not reachable (HTTP {getattr(r, 'status_code', '?')})."}

    ctype = (r.headers.get("content-type", "") if hasattr(r, "headers") else "").lower()
    content = getattr(r, "content", b"") or b""
    # Sniff the magic bytes — file hosts (Google Drive, S3 presigned URLs) often
    # omit a .pdf extension and report application/octet-stream, so neither the
    # extension nor the content-type can be trusted on its own.
    is_pdf = content[:4] == b"%PDF" or "pdf" in ctype or url.lower().endswith(".pdf")
    text = ""
    if is_pdf:
        try:
            import io

            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(r.content))
            text = "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception as exc:  # noqa: BLE001
            return {"source_type": "document", "ref": url, "status": ERROR,
                    "summary": f"Supporting document fetched but PDF could not be parsed: {exc}"}
    else:
        text = re.sub(r"<[^>]+>", " ", getattr(r, "text", "") or "")
    text = text[:max_chars]

    numbers = sorted(set(_IPOS_RE.findall(text)))
    authority = bool(re.search(r"IPOS|Intellectual Property Office of Singapore", text, re.I))
    dates = re.findall(r"\b(\d{1,2}\s+\w+\s+\d{4}|\d{4}-\d{2}-\d{2})\b", text)
    matched = [n for n in (expected_numbers or []) if n in numbers]

    if not numbers and not authority:
        return {"source_type": "document", "ref": url, "status": NOT_FOUND,
                "summary": "Document fetched but no IPOS identifiers or issuing-authority "
                           "markers were found in it."}
    auth_txt = "IPOS issuing-authority markers present; " if authority else ""
    match_txt = f" {len(matched)} matched the claimed number(s)." if matched else ""
    return {
        "source_type": "document", "ref": url, "status": SELF_ATTESTED,
        "summary": f"Supporting document on file ({auth_txt}{len(numbers)} application "
                   f"number(s) extracted).{match_txt} Self-hosted corroboration — counts as "
                   f"supporting evidence (not independent verification); independently "
                   f"verifiable once the patent publishes.",
        "data": {
            "authority_detected": authority,
            "extracted_numbers": numbers,
            "matched_claim_numbers": matched,
            "dates_seen": dates[:5],
        },
    }


def _check_url(client: Any, ref: str) -> dict[str, Any]:
    resp = client.head(ref)
    status = VERIFIED if resp.status_code < 400 else NOT_FOUND
    return {"source_type": "web", "ref": ref, "status": status,
            "summary": f"URL responded {resp.status_code}." if status == VERIFIED else "URL not reachable."}
