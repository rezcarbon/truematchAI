"""Scoring regression eval — guards the deterministic matching engines.

Runs offline (no LLM/credits): the traditional keyword matcher and the semantic
matcher are pure functions of the raw documents. Asserts:
  1. Determinism — identical inputs produce identical scores across runs.
  2. Ranking — a strong-match resume out-scores a weak one for the same JD.
  3. Prompt-registry guard — flags an unannounced prompt change.

Run directly (`python -m tests.eval.test_scoring_eval`) as a CI gate, or via
pytest.
"""
from __future__ import annotations

from app.engines import intake, semantic_match
from app.engines.prompts.registry import PROMPT_REGISTRY_VERSION
from tests.eval.golden_fixtures import GOLDEN_PAIRS, EXPECTED_PROMPT_REGISTRY


def _traditional(jd: str, resume: str) -> int:
    return int(intake.traditional_ats(jd, resume).get("score", 0))


def _semantic(jd: str, resume: str) -> int:
    return int(semantic_match.semantic_score(resume, jd).get("score", 0))


def _pair(pair_id: str) -> dict:
    return next(p for p in GOLDEN_PAIRS if p["id"] == pair_id)


def test_deterministic_traditional_score():
    """Same input → identical traditional score (byte-stable engine)."""
    for p in GOLDEN_PAIRS:
        a = _traditional(p["jd"], p["resume"])
        b = _traditional(p["jd"], p["resume"])
        assert a == b, f"traditional_ats non-deterministic for {p['id']}: {a} != {b}"


def test_deterministic_semantic_score():
    """Same input → identical semantic score."""
    for p in GOLDEN_PAIRS:
        a = _semantic(p["jd"], p["resume"])
        b = _semantic(p["jd"], p["resume"])
        assert a == b, f"semantic_score non-deterministic for {p['id']}: {a} != {b}"


def test_traditional_ranking_strong_beats_weak():
    """For the backend JD, the strong resume must out-score the weak one."""
    strong = _pair("backend_strong")
    weak = _pair("backend_weak")
    s = _traditional(strong["jd"], strong["resume"])
    w = _traditional(weak["jd"], weak["resume"])
    assert s > w, f"traditional ranking broken: strong={s} not > weak={w}"


def test_semantic_ranking_strong_beats_weak():
    """The semantic signal must also rank the strong resume above the weak one."""
    strong = _pair("backend_strong")
    weak = _pair("backend_weak")
    s = _semantic(strong["jd"], strong["resume"])
    w = _semantic(weak["jd"], weak["resume"])
    assert s > w, f"semantic ranking broken: strong={s} not > weak={w}"


def test_weak_resume_fits_its_own_domain_better():
    """The designer resume should match the design JD better than the backend JD
    on the semantic axis — a sanity check that the signal tracks meaning."""
    backend = _semantic(_pair("backend_weak")["jd"], _pair("backend_weak")["resume"])
    design = _semantic(_pair("design_match")["jd"], _pair("design_match")["resume"])
    assert design > backend, f"semantic domain check failed: design={design} not > backend-mismatch={backend}"


def test_prompt_registry_unchanged():
    """A prompt change should bump the registry version; surface it here so the
    score impact is reviewed deliberately rather than slipping in silently."""
    assert PROMPT_REGISTRY_VERSION == EXPECTED_PROMPT_REGISTRY, (
        f"Prompt registry changed ({PROMPT_REGISTRY_VERSION} != {EXPECTED_PROMPT_REGISTRY}). "
        f"If intentional, re-baseline EXPECTED_PROMPT_REGISTRY after reviewing score impact."
    )


def _run_cli() -> int:
    """Lightweight runner that prints a scorecard and returns an exit code."""
    failures = 0
    print(f"Prompt registry: {PROMPT_REGISTRY_VERSION}")
    print(f"{'pair':<18} {'traditional':>12} {'semantic':>10}")
    scores: dict[str, tuple[int, int]] = {}
    for p in GOLDEN_PAIRS:
        t = _traditional(p["jd"], p["resume"])
        s = _semantic(p["jd"], p["resume"])
        scores[p["id"]] = (t, s)
        print(f"{p['id']:<18} {t:>12} {s:>10}")
    checks = [
        ("traditional strong>weak", scores["backend_strong"][0] > scores["backend_weak"][0]),
        ("semantic strong>weak", scores["backend_strong"][1] > scores["backend_weak"][1]),
        ("prompt registry pinned", PROMPT_REGISTRY_VERSION == EXPECTED_PROMPT_REGISTRY),
    ]
    print("\nchecks:")
    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        failures += (not ok)
    return 1 if failures else 0


if __name__ == "__main__":
    import sys

    sys.exit(_run_cli())
