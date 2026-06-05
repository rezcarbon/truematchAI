"""Autonomous ingest queue — tracks every CV/JD dropped by the agents.

Revision ID: 0009
Revises: 0008
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingest_queue",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("ingest_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("source_ref", sa.Text(), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("cover_letter_text", sa.Text(), nullable=True),
        sa.Column("sender_meta", sa.Text(), nullable=True),
        sa.Column("resume_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assessment_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("position_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("jd_improved_draft", sa.Text(), nullable=True),
        sa.Column("jd_agent_output", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ingest_queue_status", "ingest_queue", ["status"])
    op.create_index("ix_ingest_queue_source", "ingest_queue", ["source"])
    op.create_index("ix_ingest_queue_type", "ingest_queue", ["ingest_type"])
    op.create_index("ix_ingest_queue_created", "ingest_queue", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_ingest_queue_created")
    op.drop_index("ix_ingest_queue_type")
    op.drop_index("ix_ingest_queue_source")
    op.drop_index("ix_ingest_queue_status")
    op.drop_table("ingest_queue")
