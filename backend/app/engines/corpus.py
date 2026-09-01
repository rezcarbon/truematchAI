"""JD corpus learning service — records analysed JDs and computes IDF.

`record_jd` (async, called when a JD is created/updated) increments the document
frequency of each unique term plus the total document count. `idf_map` (sync,
called in the worker) returns inverse-document-frequency weights for a set of
terms, so the keyword matcher can emphasise role-distinctive terms over common
ones — and the weighting improves as the corpus grows.
"""
from __future__ import annotations

import math

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.engines import text_utils
from app.models.corpus import CorpusTermStat

# Reserved row holding the total number of analysed JDs (keeps this to one
# table). Underscores never appear in a real term (the tokenizer regex excludes
# them), so this sentinel cannot collide with a JD term.
_N_KEY = "__total_documents__"
_MAX_TERM = 160


def _jd_terms(jd_text: str) -> set[str]:
    return {t[:_MAX_TERM] for t in text_utils.term_frequencies(jd_text).keys()}


async def record_jd(db, jd_text: str) -> None:
    """Record one analysed JD into the corpus (async session)."""
    rows = _record_rows(jd_text)
    if rows is None:
        return
    stmt = pg_insert(CorpusTermStat).values(rows).on_conflict_do_update(
        index_elements=[CorpusTermStat.term],
        set_={"document_frequency": CorpusTermStat.document_frequency + 1},
    )
    await db.execute(stmt)


def _record_rows(jd_text: str) -> list[dict] | None:
    terms = _jd_terms(jd_text)
    if not terms:
        return None
    rows = [{"term": t, "document_frequency": 1} for t in terms]
    rows.append({"term": _N_KEY, "document_frequency": 1})
    return rows


def record_jd_sync(db, jd_text: str) -> None:
    """Record one analysed JD into the corpus (sync session)."""
    rows = _record_rows(jd_text)
    if rows is None:
        return
    stmt = pg_insert(CorpusTermStat).values(rows).on_conflict_do_update(
        index_elements=[CorpusTermStat.term],
        set_={"document_frequency": CorpusTermStat.document_frequency + 1},
    )
    db.execute(stmt)
    db.flush()


def idf_map(db, terms: set[str]) -> dict[str, float]:
    """IDF weights for `terms` from the corpus (sync session).

    Returns {} when the corpus is empty (matcher then falls back to plain TF).
    idf(t) = ln((N+1)/(df+1)) + 1  — smoothed, always positive.
    """
    n = db.scalar(
        select(CorpusTermStat.document_frequency).where(CorpusTermStat.term == _N_KEY)
    )
    if not n:
        return {}
    lookup = {t[:_MAX_TERM] for t in terms}
    rows = db.execute(
        select(CorpusTermStat.term, CorpusTermStat.document_frequency).where(
            CorpusTermStat.term.in_(list(lookup))
        )
    ).all()
    df = {term: freq for term, freq in rows}
    return {t: math.log((n + 1) / (df.get(t[:_MAX_TERM], 0) + 1)) + 1.0 for t in terms}
