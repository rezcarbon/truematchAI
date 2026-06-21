"""capability_translations: add capability_score (the verdict anchor)

Revision ID: d7b2e4f9a1c6
Revises: c6a1f3d28e7b
"""
import sqlalchemy as sa

from alembic import op

revision = "d7b2e4f9a1c6"
down_revision = "c6a1f3d28e7b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "capability_translations",
        sa.Column("capability_score", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("capability_translations", "capability_score")
