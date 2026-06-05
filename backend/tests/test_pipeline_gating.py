"""Pipeline gating logic tests (A2): counter-rec gate + governance review."""
from __future__ import annotations

from app.core.governance import (
    COHERENCE_THRESHOLD,
    CONSISTENCY_BOUND,
    COUNTER_REC_DELTA,
    FIDELITY_THRESHOLD,
    GovernanceConfig,
)
from app.workers.tasks import _passed, _should_counter_recommend


def _operational_cfg(delta: int = 25) -> GovernanceConfig:
    return GovernanceConfig(
        {
            COHERENCE_THRESHOLD: 0.8,
            CONSISTENCY_BOUND: 0.15,
            FIDELITY_THRESHOLD: 0.9,
            COUNTER_REC_DELTA: delta,
        }
    )


def _placeholder_cfg() -> GovernanceConfig:
    return GovernanceConfig(
        {
            COHERENCE_THRESHOLD: "<x>",
            CONSISTENCY_BOUND: "<x>",
            FIDELITY_THRESHOLD: "<x>",
            COUNTER_REC_DELTA: "<x>",
        }
    )


def test_counter_rec_uses_config_delta_when_operational():
    cfg = _operational_cfg(delta=25)
    assert _should_counter_recommend(30, cfg) is True
    assert _should_counter_recommend(25, cfg) is True
    assert _should_counter_recommend(24, cfg) is False


def test_counter_rec_directional_when_ungoverned():
    # Placeholder config => fall back to directional (>0) so dev still demos it.
    cfg = _placeholder_cfg()
    assert _should_counter_recommend(1, cfg) is True
    assert _should_counter_recommend(0, cfg) is False
    # No config at all behaves the same.
    assert _should_counter_recommend(5, None) is True


def test_counter_rec_none_delta():
    assert _should_counter_recommend(None, _operational_cfg()) is False


def test_passed_helper():
    assert _passed(None) is None
    assert _passed({}) is None
    assert _passed({"passed": True}) is True
    assert _passed({"passed": False}) is False
