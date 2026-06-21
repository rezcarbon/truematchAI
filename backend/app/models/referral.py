"""Referral + shareable-result models.

The growth loop from the launch strategy: every completed assessment yields a
shareable, ANONYMISED result page (scores + delta only — never the narrative or
any PII) carrying the owner's referral code. When a new user redeems that code,
BOTH sides get a free credit. A user can only be referred once (anti-abuse).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from app.core.clock import utcnow

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk


class ReferralCode(Base, TimestampMixin):
    """One stable, shareable code per user."""
    __tablename__ = "referral_codes"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)

    __table_args__ = (
        Index("ix_referral_codes_code", "code"),
    )


class ReferralRedemption(Base):
    """A successful referral. referee_user_id is globally unique → a user can
    only ever be referred once."""
    __tablename__ = "referral_redemptions"

    id: Mapped[uuid.UUID] = uuid_pk()
    code_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("referral_codes.id", ondelete="CASCADE"), nullable=False
    )
    referrer_user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    referee_user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, unique=True)
    credits_each: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_referral_redemptions_referrer", "referrer_user_id"),
        Index("ix_referral_redemptions_code_id", "code_id"),
    )


class SharedResult(Base):
    """A public, anonymised snapshot of an assessment's scores (NO narrative,
    NO candidate identity, NO résumé text) addressable by an opaque token."""
    __tablename__ = "shared_results"

    id: Mapped[uuid.UUID] = uuid_pk()
    token: Mapped[str] = mapped_column(String(48), nullable=False, unique=True)
    assessment_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    traditional_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    semantic_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capability_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_delta: Mapped[int | None] = mapped_column(Integer, nullable=True)
    counter_rec: Mapped[bool] = mapped_column(default=False, nullable=False)
    referral_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_shared_results_token", "token"),
        Index("ix_shared_results_assessment_id", "assessment_id"),
    )
