"""Match classification — separates a surfaced candidate's nature.

The counter-recommendation fires whenever capability materially exceeds the
keyword baseline. This adds the SECOND dimension the semantic signal provides:

- hidden_gem          : surfaced, but the concept-level (semantic) match is also
                        low — keyword AND concept matching miss them; only deep
                        capability reasoning finds them.
- surfaced_strong_match: surfaced, and the semantic match is high — concept
                        matching already endorses them; capability confirms it.
- keyword_aligned     : not surfaced — the keyword baseline already captured them.
"""
from __future__ import annotations


def classify_match(
    counter_rec_triggered: bool,
    semantic_score: int | None,
    confirm_threshold: int,
) -> str:
    if not counter_rec_triggered:
        return "keyword_aligned"
    if (semantic_score or 0) >= confirm_threshold:
        return "surfaced_strong_match"
    return "hidden_gem"
