"""Shared deterministic text utilities for the keyword and semantic matchers.

Pure functions, no LLM, no network — so both matchers are byte-for-byte
reproducible from the raw CV and JD text (the property the LLM-based scorers
lacked). These are the building blocks for the independent, deterministic
"signal" engines.
"""
from __future__ import annotations

import re

_WORD_RE = re.compile(r"[a-z0-9][a-z0-9+#./-]*")
_SENT_SPLIT = re.compile(r"(?:[.!?;\n•‣●*]|\s-\s)+")

# Generic + recruiting-boilerplate stopwords. Kept explicit and reviewable.
STOPWORDS: frozenset[str] = frozenset(
    """
    a an the and or of to in for with on at by from as is are be been being this that these those
    it its their our your you we they he she them his her have has had will would should could can may
    experience strong ability skills knowledge years year relevant related etc including across deep
    role roles work working team teams within across using use used must plus preferred required
    excellent proven track record demonstrated understanding familiarity ability able well good
    new other more most across into over under about per via e g i e ie eg
    candidate candidates job description responsibilities requirements qualifications looking seeking
    company companies business across world global region regional based hybrid remote office
    """.split()
)


def tokenize(text: str) -> list[str]:
    """Lowercase content tokens (stopwords and 1-char tokens removed)."""
    return [
        w for w in _WORD_RE.findall((text or "").lower()) if len(w) > 1 and w not in STOPWORDS
    ]


def term_frequencies(text: str, include_bigrams: bool = True) -> dict[str, int]:
    """Content-term frequency map (unigrams + adjacent-content bigrams)."""
    toks = tokenize(text)
    tf: dict[str, int] = {}
    for t in toks:
        tf[t] = tf.get(t, 0) + 1
    if include_bigrams:
        for a, b in zip(toks, toks[1:]):
            bg = f"{a} {b}"
            tf[bg] = tf.get(bg, 0) + 1
    return tf


def sentences(text: str, min_chars: int = 16) -> list[str]:
    """Split text into reasonably-sized spans for embedding (deterministic)."""
    spans = [s.strip() for s in _SENT_SPLIT.split(text or "")]
    return [s for s in spans if len(s) >= min_chars]
