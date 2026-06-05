"""JD corpus / IDF tests (the learning substrate). No real DB."""
from __future__ import annotations

from app.engines import corpus


class _FakeDB:
    def __init__(self, n, df_rows):
        self._n = n
        self._df_rows = df_rows

    def scalar(self, stmt):
        return self._n

    def execute(self, stmt):
        rows = self._df_rows

        class _R:
            def all(self_inner):
                return rows

        return _R()


def test_reserved_key_is_postgres_safe():
    # Must not contain a NUL byte (Postgres TEXT rejects 0x00) and cannot collide
    # with a real term (tokenizer never emits underscores).
    assert "\x00" not in corpus._N_KEY
    assert "_" in corpus._N_KEY


def test_idf_empty_corpus_returns_empty():
    assert corpus.idf_map(_FakeDB(None, []), {"a", "b"}) == {}


def test_idf_rare_term_outweighs_common_and_unseen_highest():
    # N=10 documents; "kubernetes" in 1, "management" in 9, "unseen" in 0.
    db = _FakeDB(10, [("kubernetes", 1), ("management", 9)])
    m = corpus.idf_map(db, {"kubernetes", "management", "unseen"})
    assert m["kubernetes"] > m["management"]  # rarer term weighted higher
    assert m["unseen"] > m["kubernetes"]  # never-seen term highest IDF
