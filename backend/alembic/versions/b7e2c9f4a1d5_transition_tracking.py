"""phase 3: transition longitudinal tracking + outcomes

Revision ID: b7e2c9f4a1d5
Revises: a4f1c7e9b2d8
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "b7e2c9f4a1d5"
down_revision = "a4f1c7e9b2d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tracking fields on the analysis (snapshots accumulate over time).
    op.add_column("transition_analyses",
                  sa.Column("track", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("transition_analyses",
                  sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_transition_analyses_resume_id", "transition_analyses", ["resume_id"])
    op.create_index("ix_transition_analyses_review", "transition_analyses", ["track", "next_review_at"])

    # Outcomes table.
    outcome_status = postgresql.ENUM(
        "predicted", "pursuing", "achieved", "not_pursued",
        name="outcome_status", create_type=False,
    )
    postgresql.ENUM(
        "predicted", "pursuing", "achieved", "not_pursued",
        name="outcome_status",
    ).create(op.get_bind(), checkfirst=True)

    op.create_table(
        "transition_outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("transition_analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("predicted_role", sa.String(255), nullable=False),
        sa.Column("status", outcome_status, server_default="predicted", nullable=False),
        sa.Column("actual_role", sa.String(255), nullable=True),
        sa.Column("recorded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_transition_outcomes_user_id", "transition_outcomes", ["user_id"])
    op.create_index("ix_transition_outcomes_analysis_id", "transition_outcomes", ["analysis_id"])
    op.create_index("ix_transition_outcomes_status", "transition_outcomes", ["status"])


def downgrade() -> None:
    op.drop_table("transition_outcomes")
    postgresql.ENUM(name="outcome_status").drop(op.get_bind(), checkfirst=True)
    op.drop_index("ix_transition_analyses_review", table_name="transition_analyses")
    op.drop_index("ix_transition_analyses_resume_id", table_name="transition_analyses")
    op.drop_column("transition_analyses", "next_review_at")
    op.drop_column("transition_analyses", "track")
