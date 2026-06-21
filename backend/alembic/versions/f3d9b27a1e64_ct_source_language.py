"""capability_translations: add source_language (multilingual pivot)

Revision ID: f3d9b27a1e64
Revises: e8c3a1d6b4f2
"""
import sqlalchemy as sa

from alembic import op

revision = "f3d9b27a1e64"
down_revision = "e8c3a1d6b4f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "capability_translations",
        sa.Column("source_language", sa.String(length=8), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("capability_translations", "source_language")
