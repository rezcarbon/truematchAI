"""Add autonomous operation settings table.

Revision ID: 0023
Revises: 0022
Create Date: 2026-06-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "autonomous_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("actions_per_hour", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("daily_budget", sa.Float(), nullable=False, server_default="1000.0"),
        sa.Column("min_confidence_threshold", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("requires_governance_approval", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_on_action", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("auto_escalate_on_governance_fail", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("actions_count_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("spending_today", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("last_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_reset_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_autonomous_settings_user_id"),
    )
    op.create_index(
        "ix_autonomous_settings_user_id",
        "autonomous_settings",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_autonomous_settings_enabled",
        "autonomous_settings",
        ["enabled"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_autonomous_settings_enabled")
    op.drop_index("ix_autonomous_settings_user_id")
    op.drop_table("autonomous_settings")
