"""Pillar 1 semantic score + Pillar 3 JD version history.

Adds assessments.semantic_score/semantic_detail and the jd_versions table.

Revision ID: 0007
Revises: 0006
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Pillar 1 — semantic match signal (detail is encrypted-at-rest TEXT).
    op.add_column("assessments", sa.Column("semantic_score", sa.Integer(), nullable=True))
    op.add_column("assessments", sa.Column("semantic_detail", sa.Text(), nullable=True))

    # Pillar 3 — JD version history.
    op.create_table(
        "jd_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "position_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("positions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parsed_requirements", postgresql.JSONB(), nullable=True),
        sa.Column("jd_quality_score", sa.Integer(), nullable=True),
        sa.Column("jd_issues", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_jd_versions_position_id", "jd_versions", ["position_id"])
    op.create_index(
        "ix_jd_versions_position_version", "jd_versions", ["position_id", "version"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_jd_versions_position_version", table_name="jd_versions")
    op.drop_index("ix_jd_versions_position_id", table_name="jd_versions")
    op.drop_table("jd_versions")
    op.drop_column("assessments", "semantic_detail")
    op.drop_column("assessments", "semantic_score")
