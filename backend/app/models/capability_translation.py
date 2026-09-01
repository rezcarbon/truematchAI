"""Capability Translation request/result model.

One row per translation job. Candidate-facing: take a resume + a target JD,
re-express evidenced capability into ATS-legible language, and record the
before/after keyword + semantic scores so the lift is measured, not claimed.

PII (resume text, the rewrite, the pasted JD) is encrypted at rest via the
EncryptedText/EncryptedJSON type decorators, exactly like Assessment.
"""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk
from app.models._types import EncryptedJSON, EncryptedText


class TranslationStatus(str, enum.Enum):
    pending = "pending"
    translating = "translating"
    completed = "completed"
    failed = "failed"


class CapabilityTranslation(Base, TimestampMixin):
    """A capability-to-ATS translation job and its result."""

    __tablename__ = "capability_translations"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False
    )

    status: Mapped[TranslationStatus] = mapped_column(
        SAEnum(TranslationStatus, name="translation_status"),
        default=TranslationStatus.pending,
        nullable=False,
    )

    # Inputs (PII → encrypted)
    target_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_jd: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    # The original (possibly non-English) résumé text, retained for display.
    original_text: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    # Detected source language (ISO code) when the CV was non-English and an
    # English pivot was scored/rewritten; NULL/`en` for English input.
    source_language: Mapped[str | None] = mapped_column(String(8), nullable=True)

    # Output: {summary, bullets[{text,grounding,evidence_strength}], skills[], translation_notes, ...}
    rewrite: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    # The capability equivalences that justified the rewrite (HIGH/MED/WEAK).
    substitutions: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    # Matched/missing keywords + concepts, before and after, for transparency.
    score_detail: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)

    # Measured before→after lift (deterministic engines).
    before_keyword_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    after_keyword_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    before_semantic_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    after_semantic_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # The capability verdict for this role (assessment engine). Constant across
    # the rewrite — translation never inflates real ability — so it's the anchor
    # the legibility signals climb toward. Null until computed.
    capability_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Reproducibility manifest (non-PII): methods, prompt registry version, hashes.
    provenance: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)

    __table_args__ = (
        Index("ix_capability_translations_user_id", "user_id"),
        Index("ix_capability_translations_status", "status"),
    )
