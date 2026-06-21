"""Add governance review model for failed checks.

Revision ID: 0020
Revises: 0019
Create Date: 2026-06-08 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create governance_reviews table
    op.create_table(
        "governance_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_type", sa.Enum("cv_analysis", "assessment", "jd_simulation", name="review_type"), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("failed_gates", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("gate_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=False),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", "escalated", name="review_status"), nullable=False, server_default="pending"),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("review_decision", sa.Text(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("ix_governance_reviews_status", "governance_reviews", ["status"])
    op.create_index("ix_governance_reviews_user_id", "governance_reviews", ["user_id"])
    op.create_index("ix_governance_reviews_reviewed_by", "governance_reviews", ["reviewed_by"])
    op.create_index("ix_governance_reviews_resource_id", "governance_reviews", ["resource_id"])
    op.create_index("ix_governance_reviews_review_type", "governance_reviews", ["review_type"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_governance_reviews_review_type", "governance_reviews")
    op.drop_index("ix_governance_reviews_resource_id", "governance_reviews")
    op.drop_index("ix_governance_reviews_reviewed_by", "governance_reviews")
    op.drop_index("ix_governance_reviews_user_id", "governance_reviews")
    op.drop_index("ix_governance_reviews_status", "governance_reviews")

    # Drop table
    op.drop_table("governance_reviews")
