"""JD corpus term statistics (IDF learning substrate).

Revision ID: 0008
Revises: 0007
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "corpus_term_stats",
        sa.Column("term", sa.String(160), primary_key=True),
        sa.Column("document_frequency", sa.BigInteger(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("corpus_term_stats")
