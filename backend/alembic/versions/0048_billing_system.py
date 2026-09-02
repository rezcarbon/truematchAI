"""Add billing system tables: orders, entitlements, credit ledger, coupons, webhooks.

Revision ID: 0048
Revises: 0047
Create Date: 2026-09-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0048"
down_revision = "0047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create billing_orders table
    op.create_table(
        "billing_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False, server_default="0"),  # cents
        sa.Column("currency", sa.String(8), nullable=False, server_default="usd"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", comment="pending, paid, refunded, failed"),
        sa.Column("fulfillment_status", sa.String(20), nullable=False, server_default="pending", comment="pending, processing, delivered"),
        sa.Column("stripe_session_id", sa.String(255), nullable=True),
        sa.Column("stripe_payment_intent", sa.String(255), nullable=True),
        sa.Column("coupon_code", sa.String(64), nullable=True),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.Index("ix_billing_orders_user_id", "user_id"),
        sa.Index("ix_billing_orders_status", "status"),
        sa.Index("ix_billing_orders_stripe_session_id", "stripe_session_id"),
    )

    # Create billing_entitlements table
    op.create_table(
        "billing_entitlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False, comment="founding, subscription"),
        sa.Column("plan", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active", comment="active, expired, canceled"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("monthly_credits", sa.Integer(), nullable=True, comment="None = unlimited"),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("source_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.Index("ix_billing_entitlements_user_id", "user_id"),
        sa.Index("ix_billing_entitlements_status", "status"),
        sa.Index("ix_billing_entitlements_stripe_subscription_id", "stripe_subscription_id"),
    )

    # Create billing_credit_ledger table (append-only)
    op.create_table(
        "billing_credit_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False, comment="+grant / -consume"),
        sa.Column("reason", sa.String(64), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.Index("ix_billing_credit_ledger_user_id", "user_id"),
    )

    # Create billing_coupons table
    op.create_table(
        "billing_coupons",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("percent_off", sa.Integer(), nullable=True, comment="1-100"),
        sa.Column("amount_off", sa.Integer(), nullable=True, comment="cents"),
        sa.Column("grant_credits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_redemptions", sa.Integer(), nullable=True),
        sa.Column("redeemed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Index("ix_billing_coupons_code", "code"),
    )

    # Create billing_webhook_events table
    op.create_table(
        "billing_webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("stripe_event_id", sa.String(255), nullable=False, unique=True),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Index("ix_billing_webhook_events_stripe_event_id", "stripe_event_id"),
    )


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table("billing_webhook_events")
    op.drop_table("billing_coupons")
    op.drop_table("billing_credit_ledger")
    op.drop_table("billing_entitlements")
    op.drop_table("billing_orders")
