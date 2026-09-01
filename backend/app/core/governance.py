"""Governance engine — runtime configuration loader and named-constant registry.

IP-SAFETY:
  * This module defines ONLY named constants (string keys) for governance gates.
  * Threshold VALUES are never present in source. They are loaded at runtime from
    the external / encrypted configuration referenced by settings.governance_config_path.
  * No numeric threshold ever appears in source, comments, logs, or API responses.
  * The loaded values stay inside the process and are used solely for boolean
    gate evaluation. Raw values are never returned to clients or written to logs.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger("truematch.governance")

# ---------------------------------------------------------------------------
# Named constants only. These are the *keys* used to look up server-side values.
# The actual values live exclusively in the external governance configuration
# (file referenced by GOVERNANCE_CONFIG_PATH) or in matching `GOVERNANCE_<KEY>`
# environment variables. No numeric value ever appears in source.
# ---------------------------------------------------------------------------
COHERENCE_THRESHOLD = "COHERENCE_THRESHOLD"
CONSISTENCY_BOUND = "CONSISTENCY_BOUND"
FIDELITY_THRESHOLD = "FIDELITY_THRESHOLD"
COUNTER_REC_DELTA = "COUNTER_REC_DELTA"

# Gate names referenced by the pipeline and admin tooling.
GATE_KEYS: tuple[str, ...] = (
    COHERENCE_THRESHOLD,
    CONSISTENCY_BOUND,
    FIDELITY_THRESHOLD,
    COUNTER_REC_DELTA,
)

# Environment-variable prefix for per-key value overrides (preferred for secrets
# managers / encrypted env injection over an on-disk config file).
_ENV_PREFIX = "GOVERNANCE_"


class GovernanceConfigError(RuntimeError):
    """Raised when the governance configuration cannot be loaded or is incomplete."""


def _coerce_number(value: str) -> Any:
    """Coerce an env-string to int or float; leave non-numeric strings as-is so
    placeholder detection still flags them."""
    try:
        if "." in value or "e" in value.lower():
            return float(value)
        return int(value)
    except ValueError:
        return value


class GovernanceConfig:
    """Holds server-side governance values loaded from the external config.

    Values are kept private and exposed only through boolean evaluation helpers.
    They are intentionally never serialized back out.
    """

    def __init__(self, values: dict[str, Any]) -> None:
        self._values = values

    @classmethod
    def load(cls, path: str | None = None) -> "GovernanceConfig":
        cfg_path = Path(path or settings.governance_config_path)
        raw: dict[str, Any] = {}
        if cfg_path.exists():
            try:
                raw = json.loads(cfg_path.read_text())
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                raise GovernanceConfigError("Governance configuration is not valid JSON") from exc

        # Environment-variable overrides take precedence over the file. This lets
        # production inject real values via a secrets manager without an on-disk
        # file, while keeping the example file's placeholders out of the way.
        for key in GATE_KEYS:
            env_val = os.environ.get(f"{_ENV_PREFIX}{key}")
            if env_val is not None and env_val.strip() != "":
                raw[key] = _coerce_number(env_val)

        missing = [k for k in GATE_KEYS if k not in raw]
        if missing:
            # Fail closed: without configuration, gates cannot be evaluated.
            raise GovernanceConfigError(
                f"Governance configuration missing required keys: {', '.join(missing)}"
            )
        return cls(raw)

    # --- Boolean gate evaluation (never returns raw values) ------------------

    def passes_coherence(self, measured: float) -> bool:
        return measured >= float(self._values[COHERENCE_THRESHOLD])

    def passes_consistency(self, measured: float) -> bool:
        # Consistency is bounded: deviation must stay within the configured bound.
        return abs(measured) <= float(self._values[CONSISTENCY_BOUND])

    def passes_fidelity(self, measured: float) -> bool:
        return measured >= float(self._values[FIDELITY_THRESHOLD])

    def counter_rec_delta(self) -> int:
        """Minimum capability-minus-traditional delta that warrants a
        counter-recommendation. Magnitude is governance-controlled, never
        hardcoded in source."""
        return int(self._values[COUNTER_REC_DELTA])

    def is_operational(self) -> bool:
        """True when every gate holds a real numeric value (not a placeholder)."""
        return not self.is_placeholder()

    def is_placeholder(self) -> bool:
        """True when the loaded config still contains placeholder (non-numeric) values."""
        for key in GATE_KEYS:
            val = self._values.get(key)
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                return True
        return False

    def configured_gates(self) -> list[str]:
        """Return the names of configured gates (keys only, never values)."""
        return list(GATE_KEYS)


_cached: GovernanceConfig | None = None


def get_governance_config() -> GovernanceConfig:
    """Return a process-cached GovernanceConfig instance."""
    global _cached
    if _cached is None:
        _cached = GovernanceConfig.load()
        if _cached.is_placeholder():
            logger.warning(
                "Governance configuration is using placeholder values; "
                "gate evaluation is non-operational until real config is provided."
            )
    return _cached


def reload_governance_config() -> GovernanceConfig:
    """Force a reload of the governance configuration (e.g. after admin update)."""
    global _cached
    _cached = None
    return get_governance_config()
