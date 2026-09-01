"""External ATS connector registry."""
from __future__ import annotations

from app.services.ats_connectors.base import (
    ATSConnector,
    NormalizedCandidate,
    NormalizedJob,
)
from app.services.ats_connectors.greenhouse import GreenhouseConnector
from app.services.ats_connectors.lever import LeverConnector

_CONNECTORS: dict[str, type[ATSConnector]] = {
    "greenhouse": GreenhouseConnector,
    "lever": LeverConnector,
}


def get_connector(provider: str) -> ATSConnector | None:
    cls = _CONNECTORS.get((provider or "").lower())
    return cls() if cls else None


def connector_status() -> list[dict]:
    """All known connectors and whether each has credentials configured."""
    out = []
    for name, cls in _CONNECTORS.items():
        out.append({"provider": name, "configured": cls().is_configured})
    return out


__all__ = [
    "ATSConnector",
    "NormalizedJob",
    "NormalizedCandidate",
    "get_connector",
    "connector_status",
]
