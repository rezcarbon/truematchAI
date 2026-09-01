"""Training-provider contract.

A TrainingProvider maps a candidate's *upskilling gap* (capabilities to acquire)
to concrete learning options. Providers are pluggable: a new partner (NTUC
LearningHub, SkillsFuture, Coursera, an internal L&D catalog, …) is added by
implementing this protocol, registering it, and gating it with a config flag —
no changes to the engine or the transition pipeline.

Providers must be SAFE NO-OPS when unconfigured (return []), mirroring the rest
of the platform's gated integrations.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass
class CourseMatch:
    """A single learning option that addresses a gap capability."""

    capability: str           # the gap capability this addresses (verbatim)
    title: str
    provider: str             # human-readable provider/partner name
    url: str | None = None
    format: str | None = None         # "online" | "in-person" | "hybrid"
    duration_weeks: int | None = None
    level: str | None = None          # "foundational" | "intermediate" | "advanced"
    relevance: str = ""               # one line: why this matches the gap

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@runtime_checkable
class TrainingProvider(Protocol):
    """The plug-in contract. Implement these three members to add a partner."""

    name: str

    def enabled(self) -> bool:
        """True only when this provider is configured and switched on."""
        ...

    def match(self, capabilities: list[str], context: dict[str, Any]) -> list[CourseMatch]:
        """Return learning options for the given gap capabilities (may be []).

        Must never raise for normal input; the registry guards anyway, but a
        well-behaved provider degrades to [] rather than throwing.
        """
        ...
