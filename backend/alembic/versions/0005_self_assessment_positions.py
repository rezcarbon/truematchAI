"""Allow positions with no owning company (candidate self-assessments).

Revision ID: 0005
Revises: 0004
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("positions", "company_id", existing_type=sa.dialects.postgresql.UUID(), nullable=True)


def downgrade() -> None:
    op.alter_column("positions", "company_id", existing_type=sa.dialects.postgresql.UUID(), nullable=False)
