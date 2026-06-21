"""Shared helpers for catalog-backed training providers.

A catalog is a JSON file of {keywords:[...], courses:[{...}]} entries. Any number
of providers can be catalog-backed simply by pointing at their own JSON — the
matching logic lives here once.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.services.training.base import CourseMatch

logger = logging.getLogger("truematch.training.catalog")

_CATALOGS_DIR = Path(__file__).resolve().parent / "catalogs"


@lru_cache(maxsize=8)
def load_catalog(filename: str) -> tuple[dict[str, Any], ...]:
    """Load a catalog's entries (cached). Returns () on any error — never raises."""
    try:
        data = json.loads((_CATALOGS_DIR / filename).read_text())
        return tuple(data.get("entries") or [])
    except Exception as exc:  # noqa: BLE001 — a bad catalog must not break the pipeline
        logger.warning("Could not load training catalog %s: %s", filename, exc)
        return ()


def match_catalog(filename: str, capabilities: list[str], default_provider: str) -> list[CourseMatch]:
    """Match gap capabilities against a catalog's keyword entries."""
    out: list[CourseMatch] = []
    entries = load_catalog(filename)
    for cap in capabilities:
        cap_l = (cap or "").lower()
        if not cap_l:
            continue
        for entry in entries:
            if not any(kw in cap_l for kw in (entry.get("keywords") or [])):
                continue
            for c in entry.get("courses") or []:
                out.append(CourseMatch(
                    capability=cap,
                    title=c.get("title", ""),
                    provider=c.get("provider", default_provider),
                    url=c.get("url"),
                    format=c.get("format"),
                    duration_weeks=c.get("duration_weeks"),
                    level=c.get("level"),
                    relevance=c.get("relevance", ""),
                ))
    return out
