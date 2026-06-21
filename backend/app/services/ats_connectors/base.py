"""External ATS connector interface + normalized shapes.

Each connector talks to one external ATS (Greenhouse, Lever, …) over its REST
API and normalizes jobs/candidates into the shapes below. Connectors are gated
on their own API key: unconfigured → ``is_configured`` is False and the import
endpoints report it rather than calling out. The DB import logic lives in
``ats_connectors.importer`` and is connector-agnostic (it consumes these shapes),
so it is fully testable without any external network.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str | None) -> str:
    """Best-effort HTML → text for job-post bodies."""
    if not text:
        return ""
    no_tags = _TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", no_tags).strip()


@dataclass
class NormalizedJob:
    external_id: str
    title: str
    description: str = ""


@dataclass
class NormalizedCandidate:
    external_id: str
    name: str
    email: str | None = None
    summary: str = ""  # free-text used as the resume narrative
    job_external_id: str | None = None
    tags: list[str] = field(default_factory=list)


class ATSConnector(ABC):
    """One external ATS. Subclasses implement the REST calls + normalization."""

    provider: str = "base"

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        ...

    @abstractmethod
    def list_jobs(self) -> list[NormalizedJob]:
        ...

    @abstractmethod
    def list_candidates(self, job_external_id: str | None = None) -> list[NormalizedCandidate]:
        ...
