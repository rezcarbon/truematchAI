"""Phase 1: Screening agent - create screening_batches and screening_results tables

Revision ID: 0040
Revises: 0029
"""
from alembic import op
from sqlalchemy import text, inspect
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0040"
down_revision = "0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create screening tables for Phase 1 agent implementation."""

    conn = op.get_bind()
    inspector = inspect(conn)

    # Check if tables already exist (handles idempotency)
    existing_tables = inspector.get_table_names()

    if "screening_batches" not in existing_tables:
        # Create screening_batches table
        op.create_table(
            "screening_batches",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("status", postgresql.ENUM("queued", "screening", "pending_review", "completed", name="screening_batch_status"), nullable=False, server_default="queued"),
            sa.Column("total_candidates", sa.Integer(), nullable=False),
            sa.Column("screened_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("pending_review_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("batch_config", sa.Text(), nullable=True),
            sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )

        op.create_index("ix_screening_batches_position_id_status", "screening_batches", ["position_id", "status"])
        op.create_index("ix_screening_batches_created_by", "screening_batches", ["created_by"])
        op.create_index("ix_screening_batches_created_at", "screening_batches", ["created_at"])

    if "screening_results" not in existing_tables:
        # Create screening_results table
        op.create_table(
            "screening_results",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("screening_batch_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("agent_recommendation", postgresql.ENUM("advance", "hold", "review", name="screening_recommendation"), nullable=False),
            sa.Column("confidence_score", sa.Integer(), nullable=False),
            sa.Column("screening_summary", sa.Text(), nullable=False),
            sa.Column("screening_details", sa.Text(), nullable=False),
            sa.Column("bias_flags", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("recruiter_decision", postgresql.ENUM("interview", "hold", "further_review", name="recruiter_decision"), nullable=True),
            sa.Column("recruiter_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("recruiter_notes", sa.Text(), nullable=True),
            sa.Column("recruiter_confidence", sa.Integer(), nullable=True),
            sa.Column("was_overridden", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("override_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["screening_batch_id"], ["screening_batches.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["recruiter_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )

        op.create_index("ix_screening_results_batch_id", "screening_results", ["screening_batch_id"])
        op.create_index("ix_screening_results_position_id", "screening_results", ["position_id"])
        op.create_index("ix_screening_results_resume_id", "screening_results", ["resume_id"])
        op.create_index("ix_screening_results_recruiter_id", "screening_results", ["recruiter_id"])
        op.create_index("ix_screening_results_position_recruiter_decision", "screening_results", ["position_id", "recruiter_decision"])
        op.create_index("ix_screening_results_created_at", "screening_results", ["created_at"])
        op.create_index("ix_screening_results_batch_decision", "screening_results", ["screening_batch_id", "recruiter_decision"])


def downgrade() -> None:
    op.drop_index("ix_screening_results_batch_decision", table_name="screening_results")
    op.drop_index("ix_screening_results_created_at", table_name="screening_results")
    op.drop_index("ix_screening_results_position_recruiter_decision", table_name="screening_results")
    op.drop_index("ix_screening_results_recruiter_id", table_name="screening_results")
    op.drop_index("ix_screening_results_resume_id", table_name="screening_results")
    op.drop_index("ix_screening_results_position_id", table_name="screening_results")
    op.drop_index("ix_screening_results_batch_id", table_name="screening_results")
    op.drop_table("screening_results")
    op.drop_index("ix_screening_batches_created_at", table_name="screening_batches")
    op.drop_index("ix_screening_batches_created_by", table_name="screening_batches")
    op.drop_index("ix_screening_batches_position_id_status", table_name="screening_batches")
    op.drop_table("screening_batches")
