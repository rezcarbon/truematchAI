"""referrals: codes, redemptions, shareable anonymised results

Revision ID: b2e5f8c1a9d3
Revises: a1d4c7b9e2f0
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "b2e5f8c1a9d3"
down_revision = "a1d4c7b9e2f0"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "referral_codes",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("created_at", TS, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TS, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_referral_codes_user"),
        sa.UniqueConstraint("code", name="uq_referral_codes_code"),
    )
    op.create_index("ix_referral_codes_code", "referral_codes", ["code"])

    op.create_table(
        "referral_redemptions",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("code_id", UUID, sa.ForeignKey("referral_codes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("referrer_user_id", UUID, nullable=False),
        sa.Column("referee_user_id", UUID, nullable=False),
        sa.Column("credits_each", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", TS, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("referee_user_id", name="uq_referral_redemptions_referee"),
    )
    op.create_index("ix_referral_redemptions_referrer", "referral_redemptions", ["referrer_user_id"])
    op.create_index("ix_referral_redemptions_code_id", "referral_redemptions", ["code_id"])

    op.create_table(
        "shared_results",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("token", sa.String(48), nullable=False),
        sa.Column("assessment_id", UUID, nullable=False),
        sa.Column("owner_user_id", UUID, nullable=False),
        sa.Column("traditional_score", sa.Integer(), nullable=True),
        sa.Column("semantic_score", sa.Integer(), nullable=True),
        sa.Column("capability_score", sa.Integer(), nullable=True),
        sa.Column("score_delta", sa.Integer(), nullable=True),
        sa.Column("counter_rec", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("referral_code", sa.String(32), nullable=True),
        sa.Column("created_at", TS, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("token", name="uq_shared_results_token"),
    )
    op.create_index("ix_shared_results_token", "shared_results", ["token"])
    op.create_index("ix_shared_results_assessment_id", "shared_results", ["assessment_id"])


def downgrade() -> None:
    op.drop_table("shared_results")
    op.drop_table("referral_redemptions")
    op.drop_index("ix_referral_codes_code", table_name="referral_codes")
    op.drop_table("referral_codes")
