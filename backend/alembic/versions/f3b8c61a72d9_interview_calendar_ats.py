"""interview-content analysis, 2-way calendar, external ATS provenance

Revision ID: f3b8c61a72d9
Revises: e7c2a9d51f34
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "f3b8c61a72d9"
down_revision = "e7c2a9d51f34"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Interview-content analysis: AI-generated scorecards from a transcript.
    op.add_column("scorecards", sa.Column("source", sa.String(length=20), nullable=False, server_default="human"))
    op.add_column("scorecards", sa.Column("transcript", sa.Text(), nullable=True))
    op.add_column("scorecards", sa.Column("ai_analysis", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # 2-way calendar sync: external event mirror.
    op.add_column("interviews", sa.Column("calendar_provider", sa.String(length=50), nullable=True))
    op.add_column("interviews", sa.Column("calendar_event_id", sa.String(length=255), nullable=True))

    # External ATS provenance for idempotent import.
    op.add_column("positions", sa.Column("external_ref", sa.String(length=255), nullable=True))
    op.create_index("ix_positions_external_ref", "positions", ["external_ref"])
    op.add_column("applications", sa.Column("external_ref", sa.String(length=255), nullable=True))
    op.create_index("ix_applications_external_ref", "applications", ["external_ref"])


def downgrade() -> None:
    op.drop_index("ix_applications_external_ref", table_name="applications")
    op.drop_column("applications", "external_ref")
    op.drop_index("ix_positions_external_ref", table_name="positions")
    op.drop_column("positions", "external_ref")
    op.drop_column("interviews", "calendar_event_id")
    op.drop_column("interviews", "calendar_provider")
    op.drop_column("scorecards", "ai_analysis")
    op.drop_column("scorecards", "transcript")
    op.drop_column("scorecards", "source")
