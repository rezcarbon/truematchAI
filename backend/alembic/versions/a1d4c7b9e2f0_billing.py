"""billing & payments: orders, entitlements, credit ledger, coupons, webhook events

Revision ID: a1d4c7b9e2f0
Revises: f3b8c61a72d9
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "a1d4c7b9e2f0"
down_revision = "f3b8c61a72d9"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
TS = sa.DateTime(timezone=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "billing_orders",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="usd"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("fulfillment_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("stripe_session_id", sa.String(255), nullable=True),
        sa.Column("stripe_payment_intent", sa.String(255), nullable=True),
        sa.Column("coupon_code", sa.String(64), nullable=True),
        sa.Column("extra", JSONB, nullable=True),
        sa.Column("created_at", TS, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TS, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_billing_orders_user_id", "billing_orders", ["user_id"])
    op.create_index("ix_billing_orders_status", "billing_orders", ["status"])
    op.create_index("ix_billing_orders_stripe_session_id", "billing_orders", ["stripe_session_id"])

    op.create_table(
        "billing_entitlements",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("plan", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("starts_at", TS, nullable=False),
        sa.Column("expires_at", TS, nullable=True),
        sa.Column("monthly_credits", sa.Integer(), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("source_order_id", UUID, nullable=True),
        sa.Column("created_at", TS, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TS, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_billing_entitlements_user_id", "billing_entitlements", ["user_id"])
    op.create_index("ix_billing_entitlements_status", "billing_entitlements", ["status"])
    op.create_index("ix_billing_entitlements_stripe_subscription_id", "billing_entitlements", ["stripe_subscription_id"])

    op.create_table(
        "billing_credit_ledger",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(64), nullable=False),
        sa.Column("order_id", UUID, nullable=True),
        sa.Column("assessment_id", UUID, nullable=True),
        sa.Column("created_at", TS, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_billing_credit_ledger_user_id", "billing_credit_ledger", ["user_id"])

    op.create_table(
        "billing_coupons",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("percent_off", sa.Integer(), nullable=True),
        sa.Column("amount_off", sa.Integer(), nullable=True),
        sa.Column("grant_credits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_redemptions", sa.Integer(), nullable=True),
        sa.Column("redeemed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("expires_at", TS, nullable=True),
        sa.Column("created_at", TS, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TS, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("code", name="uq_billing_coupons_code"),
    )
    op.create_index("ix_billing_coupons_code", "billing_coupons", ["code"])

    op.create_table(
        "billing_webhook_events",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("stripe_event_id", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("processed_at", TS, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("stripe_event_id", name="uq_billing_webhook_events_event_id"),
    )
    op.create_index("ix_billing_webhook_events_stripe_event_id", "billing_webhook_events", ["stripe_event_id"])


def downgrade() -> None:
    op.drop_table("billing_webhook_events")
    op.drop_table("billing_coupons")
    op.drop_index("ix_billing_credit_ledger_user_id", table_name="billing_credit_ledger")
    op.drop_table("billing_credit_ledger")
    op.drop_table("billing_entitlements")
    op.drop_table("billing_orders")
