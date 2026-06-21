"""Request/response schemas for Capability Translation."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.models.capability_translation import TranslationStatus


class TranslationStartRequest(BaseModel):
    """Start a capability translation against a target job description."""

    resume_id: UUID = Field(..., description="UUID of the resume to translate")
    jd_text: str = Field(
        ..., min_length=20, max_length=20000,
        description="Target job description the resume should be made legible to",
    )
    target_role: Optional[str] = Field(None, max_length=255)


class TranslationStartResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    translation_id: UUID
    status: TranslationStatus


class TranslationBullet(BaseModel):
    """A single rewritten bullet with its grounding (the no-fabrication trail)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    text: str = ""
    grounding: str = ""
    evidence_strength: str = Field(default="MEDIUM", description="HIGH/MEDIUM/WEAK")


class TranslationResult(BaseModel):
    """Full translation result with measured before→after lift."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    translation_id: UUID
    status: TranslationStatus
    target_role: Optional[str] = None
    # Detected source language when the CV was non-English (an English pivot was
    # rewritten); None/"en" for English. original_text retains the original CV.
    source_language: Optional[str] = None
    original_text: Optional[str] = None

    # The rewrite
    summary: Optional[str] = None
    bullets: list[TranslationBullet] = []
    skills: list[str] = []
    translation_notes: Optional[str] = None
    dropped_ungrounded: int = 0

    # Measured lift (deterministic engines)
    before_keyword_score: Optional[int] = None
    after_keyword_score: Optional[int] = None
    before_semantic_score: Optional[int] = None
    after_semantic_score: Optional[int] = None
    keyword_lift: Optional[int] = None
    semantic_lift: Optional[int] = None
    # The capability verdict (assessment engine) — the constant anchor.
    capability_score: Optional[int] = None
    capability_delta: Optional[int] = None  # capability − before-keyword (hidden-gem gap)

    # Transparency
    matched_keywords_after: list[str] = []
    still_missing_keywords: list[str] = []

    error: Optional[str] = None


class TranslationListItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    translation_id: UUID
    target_role: Optional[str] = None
    status: TranslationStatus
    created_at: str
    keyword_lift: Optional[int] = None
    semantic_lift: Optional[int] = None
