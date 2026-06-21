"""Add experience_years, skills, and education to training_data_items.

Revision ID: 0018
Revises: 0017
Create Date: 2026-06-08 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add new fields to training_data_items."""
    op.add_column(
        "training_data_items",
        sa.Column("experience_years", sa.Integer(), nullable=True),
    )
    op.add_column(
        "training_data_items",
        sa.Column("skills", postgresql.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "training_data_items",
        sa.Column("education", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    """Remove new fields from training_data_items."""
    op.drop_column("training_data_items", "education")
    op.drop_column("training_data_items", "skills")
    op.drop_column("training_data_items", "experience_years")
