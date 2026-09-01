"""Billing & payments domain models.

Five concepts back every TrueMatch payment shape (one-time, packs, founding
12-month access, recurring subscriptions, coupons):

  - Order        : a single Stripe Checkout purchase + its fulfillment state.
  - Entitlement  : time-boxed / recurring access (founding | subscription).
  - CreditLedger : append-only +grant / -consume rows; balance = SUM(delta).
  - Coupon       : promo / NTUC / referral discount or free-credit grant.
  - WebhookEvent : processed Stripe event ids → idempotent webhook handling.

Money is never stored as a card; Stripe-hosted Checkout is the only entry
point. Amounts are integers in the smallest currency unit (cents).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from app.core.clock import utcnow

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk


class Order(Base, TimestampMixin):
    """A one-time Checkout purchase (or the initial subscription checkout)."""
    __tablename__ = "billing_orders"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # cents
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="usd")
    # status: pending → paid → refunded ; or failed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # fulfillment (esp. the 48h manual bridge): pending → processing → delivered
    fulfillment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    stripe_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_payment_intent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    coupon_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_billing_orders_user_id", "user_id"),
        Index("ix_billing_orders_status", "status"),
        Index("ix_billing_orders_stripe_session_id", "stripe_session_id"),
    )


class Entitlement(Base, TimestampMixin):
    """Active access: a one-time founding grant or a recurring subscription."""
    __tablename__ = "billing_entitlements"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)   # founding | subscription
    plan: Mapped[str] = mapped_column(String(40), nullable=False)   # candidate | premium | …
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # active|expired|canceled
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # None monthly_credits ⇒ unlimited while active; else a per-cycle allotment.
    monthly_credits: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_order_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index("ix_billing_entitlements_user_id", "user_id"),
        Index("ix_billing_entitlements_status", "status"),
        Index("ix_billing_entitlements_stripe_subscription_id", "stripe_subscription_id"),
    )


class CreditLedger(Base):
    """Append-only credit movements. Balance = SUM(delta) for a user."""
    __tablename__ = "billing_credit_ledger"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    delta: Mapped[int] = mapped_column(Integer, nullable=False)  # +grant / -consume
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    order_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    __table_args__ = (
        Index("ix_billing_credit_ledger_user_id", "user_id"),
    )


class Coupon(Base, TimestampMixin):
    """Promo / NTUC / referral code: percent or amount off, or free credits."""
    __tablename__ = "billing_coupons"

    id: Mapped[uuid.UUID] = uuid_pk()
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    percent_off: Mapped[int | None] = mapped_column(Integer, nullable=True)   # 1–100
    amount_off: Mapped[int | None] = mapped_column(Integer, nullable=True)    # cents
    grant_credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_redemptions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    redeemed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_billing_coupons_code", "code"),
    )


class WebhookEvent(Base):
    """Processed Stripe event ids — guarantees idempotent webhook handling."""
    __tablename__ = "billing_webhook_events"

    id: Mapped[uuid.UUID] = uuid_pk()
    stripe_event_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    __table_args__ = (
        Index("ix_billing_webhook_events_stripe_event_id", "stripe_event_id"),
    )
