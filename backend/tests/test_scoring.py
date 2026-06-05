"""Match classification tests (final tuning): hidden_gem vs surfaced_strong_match."""
from __future__ import annotations

from app.core.scoring import classify_match


def test_not_surfaced_is_keyword_aligned():
    assert classify_match(False, 90, 60) == "keyword_aligned"
    assert classify_match(False, 10, 60) == "keyword_aligned"


def test_surfaced_with_low_semantic_is_hidden_gem():
    # Keyword AND concept matching miss them; only capability finds them.
    assert classify_match(True, 40, 60) == "hidden_gem"
    assert classify_match(True, None, 60) == "hidden_gem"


def test_surfaced_with_high_semantic_is_strong_match():
    # Concept matching already endorses; capability confirms.
    assert classify_match(True, 83, 60) == "surfaced_strong_match"
    assert classify_match(True, 60, 60) == "surfaced_strong_match"  # boundary inclusive
