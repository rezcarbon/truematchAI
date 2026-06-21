"""multilingual intake: source_language + JD english pivot

Adds source-language metadata for non-English résumés and job descriptions, and
the English pivot column for JDs (résumé pivots live in the encrypted
supplementary JSON). All nullable — existing rows default to English (NULL).

Revision ID: e8c3a1d6b4f2
Revises: d7b2e4f9a1c6
"""
import sqlalchemy as sa

from alembic import op

revision = "e8c3a1d6b4f2"
down_revision = "d7b2e4f9a1c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resumes", sa.Column("source_language", sa.String(length=8), nullable=True))
    op.add_column("positions", sa.Column("source_language", sa.String(length=8), nullable=True))
    op.add_column("positions", sa.Column("description_en", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("positions", "description_en")
    op.drop_column("positions", "source_language")
    op.drop_column("resumes", "source_language")
