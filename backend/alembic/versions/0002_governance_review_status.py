"""Add 'flagged_for_review' value to assessment_status enum.

Governed assessment runs that fail a governance gate are routed to human review
with this status rather than presented as confident results.

Revision ID: 0002
Revises: 0001
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block, so commit
    # the migration's implicit transaction first.
    op.execute("COMMIT")
    op.execute(
        "ALTER TYPE assessment_status ADD VALUE IF NOT EXISTS 'flagged_for_review'"
    )


def downgrade() -> None:
    # PostgreSQL does not support removing a value from an enum type without
    # recreating the type and rewriting every dependent column. Removal is
    # intentionally a no-op; the unused value is harmless.
    pass
