"""Add verified_evidence + substitutions columns (Pillars 5 & 6).

Both are encrypted-at-rest (stored as TEXT via the EncryptedJSON type).

Revision ID: 0006
Revises: 0005
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("assessments", sa.Column("verified_evidence", sa.Text(), nullable=True))
    op.add_column("assessments", sa.Column("substitutions", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("assessments", "substitutions")
    op.drop_column("assessments", "verified_evidence")
