"""Governance configuration + gate evaluation tests (A2)."""
from __future__ import annotations

import json

import pytest

from app.core.governance import (
    COHERENCE_THRESHOLD,
    CONSISTENCY_BOUND,
    COUNTER_REC_DELTA,
    FIDELITY_THRESHOLD,
    GovernanceConfig,
    GovernanceConfigError,
)


def _numeric_cfg() -> GovernanceConfig:
    return GovernanceConfig(
        {
            COHERENCE_THRESHOLD: 0.8,
            CONSISTENCY_BOUND: 0.15,
            FIDELITY_THRESHOLD: 0.9,
            COUNTER_REC_DELTA: 25,
        }
    )


def test_placeholder_config_is_not_operational():
    cfg = GovernanceConfig(
        {
            COHERENCE_THRESHOLD: "<encrypted-server-side>",
            CONSISTENCY_BOUND: "<encrypted-server-side>",
            FIDELITY_THRESHOLD: "<encrypted-server-side>",
            COUNTER_REC_DELTA: "<encrypted-server-side>",
        }
    )
    assert cfg.is_placeholder() is True
    assert cfg.is_operational() is False


def test_numeric_config_is_operational():
    cfg = _numeric_cfg()
    assert cfg.is_operational() is True
    assert cfg.is_placeholder() is False


def test_bool_is_not_treated_as_numeric():
    cfg = GovernanceConfig(
        {
            COHERENCE_THRESHOLD: True,
            CONSISTENCY_BOUND: 0.1,
            FIDELITY_THRESHOLD: 0.9,
            COUNTER_REC_DELTA: 20,
        }
    )
    assert cfg.is_operational() is False


def test_gate_evaluation_boundaries():
    cfg = _numeric_cfg()
    # Coherence: measured >= threshold
    assert cfg.passes_coherence(0.8) is True
    assert cfg.passes_coherence(0.79) is False
    # Consistency: |deviation| <= bound
    assert cfg.passes_consistency(0.15) is True
    assert cfg.passes_consistency(-0.15) is True
    assert cfg.passes_consistency(0.16) is False
    # Fidelity: measured >= threshold
    assert cfg.passes_fidelity(0.9) is True
    assert cfg.passes_fidelity(0.89) is False


def test_counter_rec_delta_accessor():
    assert _numeric_cfg().counter_rec_delta() == 25


def test_load_missing_keys_fails_closed(tmp_path):
    cfg_file = tmp_path / "gov.json"
    cfg_file.write_text(json.dumps({COHERENCE_THRESHOLD: 0.8}))
    with pytest.raises(GovernanceConfigError):
        GovernanceConfig.load(str(cfg_file))


def test_env_overrides_take_precedence(tmp_path, monkeypatch):
    cfg_file = tmp_path / "gov.json"
    cfg_file.write_text(
        json.dumps(
            {
                COHERENCE_THRESHOLD: "<encrypted-server-side>",
                CONSISTENCY_BOUND: "<encrypted-server-side>",
                FIDELITY_THRESHOLD: "<encrypted-server-side>",
                COUNTER_REC_DELTA: "<encrypted-server-side>",
            }
        )
    )
    monkeypatch.setenv("GOVERNANCE_COHERENCE_THRESHOLD", "0.82")
    monkeypatch.setenv("GOVERNANCE_CONSISTENCY_BOUND", "0.1")
    monkeypatch.setenv("GOVERNANCE_FIDELITY_THRESHOLD", "0.95")
    monkeypatch.setenv("GOVERNANCE_COUNTER_REC_DELTA", "30")
    cfg = GovernanceConfig.load(str(cfg_file))
    assert cfg.is_operational() is True
    assert cfg.counter_rec_delta() == 30
    assert cfg.passes_fidelity(0.95) is True


def test_missing_file_with_full_env_overrides_loads(tmp_path, monkeypatch):
    monkeypatch.setenv("GOVERNANCE_COHERENCE_THRESHOLD", "0.8")
    monkeypatch.setenv("GOVERNANCE_CONSISTENCY_BOUND", "0.15")
    monkeypatch.setenv("GOVERNANCE_FIDELITY_THRESHOLD", "0.9")
    monkeypatch.setenv("GOVERNANCE_COUNTER_REC_DELTA", "25")
    cfg = GovernanceConfig.load(str(tmp_path / "does-not-exist.json"))
    assert cfg.is_operational() is True
