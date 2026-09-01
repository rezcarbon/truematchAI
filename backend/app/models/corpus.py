"""Accumulating JD corpus statistics — the system's learning substrate.

Every analysed job description contributes its terms here. Document frequencies
let the keyword matcher compute TF-IDF: terms common across many JDs (e.g.
"management", "team") are down-weighted, role-distinctive terms (e.g.
"kubernetes", "ecosystem") up-weighted. As more JDs are analysed, the weighting
sharpens — the system literally learns from each analysis.

The total document count is stored as a reserved term row (see engines/corpus.py)
to keep this to a single table.
"""
from __future__ import annotations

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CorpusTermStat(Base):
    __tablename__ = "corpus_term_stats"

    term: Mapped[str] = mapped_column(String(160), primary_key=True)
    document_frequency: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
