"""Curated catalog provider — built-in, offline-safe, always available.

Maps gap capabilities to courses via a data-driven catalog
(`catalogs/curated_catalog.json`). To extend the curriculum, edit that JSON —
no code change. Guarantees Transition Intelligence always returns *some* grounded
learning options even when no external partner is configured.
"""
from __future__ import annotations

from typing import Any

from app.config import settings
from app.services.training.base import CourseMatch
from app.services.training.catalog import match_catalog


class CuratedCatalogProvider:
    name = "curated"

    def enabled(self) -> bool:
        return bool(getattr(settings, "training_curated_enabled", True))

    def match(self, capabilities: list[str], context: dict[str, Any]) -> list[CourseMatch]:
        return match_catalog("curated_catalog.json", capabilities, default_provider="Curated")
