"""Add governance fields to CV analysis results.

Revision ID: 0019
Revises: 0018
Create Date: 2026-06-08 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add governance columns to cv_analysis_results table
    op.add_column(
        "cv_analysis_results",
        sa.Column("governance_coherence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "cv_analysis_results",
        sa.Column("governance_consistency", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "cv_analysis_results",
        sa.Column("governance_fidelity", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "cv_analysis_results",
        sa.Column("governance_bias_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "cv_analysis_results",
        sa.Column("governance_passed", sa.Boolean(), nullable=True, server_default="true"),
    )


def downgrade() -> None:
    # Remove governance columns from cv_analysis_results table
    op.drop_column("cv_analysis_results", "governance_passed")
    op.drop_column("cv_analysis_results", "governance_bias_flags")
    op.drop_column("cv_analysis_results", "governance_fidelity")
    op.drop_column("cv_analysis_results", "governance_consistency")
    op.drop_column("cv_analysis_results", "governance_coherence")
