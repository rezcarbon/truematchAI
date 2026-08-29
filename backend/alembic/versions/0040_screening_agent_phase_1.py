"""Phase 1: Screening agent - screening tables

Revision ID: 0040
Revises: 0029
"""
from alembic import op
from sqlalchemy import text
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0040"
down_revision = "0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create screening batch status enum with DO block for idempotency
    op.execute("""
    DO $$
    BEGIN
        CREATE TYPE screening_batch_status AS ENUM ('queued', 'screening', 'pending_review', 'completed');
    EXCEPTION WHEN duplicate_object THEN
        NULL;
    END
    $$;
    """)

    # Create screening recommendation enum
    op.execute("""
    DO $$
    BEGIN
        CREATE TYPE screening_recommendation AS ENUM ('advance', 'hold', 'review');
    EXCEPTION WHEN duplicate_object THEN
        NULL;
    END
    $$;
    """)

    # Create recruiter decision enum
    op.execute("""
    DO $$
    BEGIN
        CREATE TYPE recruiter_decision AS ENUM ('interview', 'hold', 'further_review');
    EXCEPTION WHEN duplicate_object THEN
        NULL;
    END
    $$;
    """)

    # Create screening_batches table
    op.create_table(
        "screening_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", postgresql.ENUM("queued", "screening", "pending_review", "completed", name="screening_batch_status", create_type=False), default="queued", nullable=False),
        sa.Column("total_candidates", sa.Integer(), nullable=False),
        sa.Column("screened_count", sa.Integer(), default=0, nullable=False),
        sa.Column("pending_review_count", sa.Integer(), default=0, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("batch_config", sa.Text(), nullable=True),  # Encrypted JSON
        sa.Column("batch_metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_screening_batches_position_id_status", "screening_batches", ["position_id", "status"])
    op.create_index("ix_screening_batches_created_by", "screening_batches", ["created_by"])
    op.create_index("ix_screening_batches_created_at", "screening_batches", ["created_at"])

    # Create screening_results table
    op.create_table(
        "screening_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("screening_batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommendation", postgresql.ENUM("advance", "hold", "review", name="screening_recommendation", create_type=False), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=False),
        sa.Column("analysis", sa.Text(), nullable=False),  # Encrypted JSON
        sa.Column("governance_check_results", sa.Text(), nullable=True),  # Encrypted JSON
        sa.Column("recruiter_decision", postgresql.ENUM("interview", "hold", "further_review", name="recruiter_decision", create_type=False), nullable=True),
        sa.Column("recruiter_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recruiter_feedback", sa.Text(), nullable=True),  # Encrypted
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["screening_batch_id"], ["screening_batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["candidate_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recruiter_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_screening_results_batch_id", "screening_results", ["screening_batch_id"])
    op.create_index("ix_screening_results_position_id", "screening_results", ["position_id"])
    op.create_index("ix_screening_results_resume_id", "screening_results", ["resume_id"])
    op.create_index("ix_screening_results_candidate_id", "screening_results", ["candidate_id"])
    op.create_index("ix_screening_results_recruiter_id", "screening_results", ["recruiter_id"])
    op.create_index("ix_screening_results_created_at", "screening_results", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_screening_results_created_at", "screening_results")
    op.drop_index("ix_screening_results_recruiter_id", "screening_results")
    op.drop_index("ix_screening_results_candidate_id", "screening_results")
    op.drop_index("ix_screening_results_resume_id", "screening_results")
    op.drop_index("ix_screening_results_position_id", "screening_results")
    op.drop_index("ix_screening_results_batch_id", "screening_results")
    op.drop_table("screening_results")

    op.drop_index("ix_screening_batches_created_at", "screening_batches")
    op.drop_index("ix_screening_batches_created_by", "screening_batches")
    op.drop_index("ix_screening_batches_position_id_status", "screening_batches")
    op.drop_table("screening_batches")

    op.execute("DROP TYPE IF EXISTS recruiter_decision CASCADE")
    op.execute("DROP TYPE IF EXISTS screening_recommendation CASCADE")
    op.execute("DROP TYPE IF EXISTS screening_batch_status CASCADE")
