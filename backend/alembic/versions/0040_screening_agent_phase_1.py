"""Phase 1: Screening agent - create screening_batches and screening_results tables

Revision ID: 0040
Revises: 0039
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0040"
down_revision = "0039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create screening tables for Phase 1 agent implementation."""

    # Create screening batch status enum
    screening_batch_status = postgresql.ENUM(
        "queued", "screening", "pending_review", "completed",
        name="screening_batch_status"
    )
    screening_batch_status.create(op.get_bind(), checkfirst=True)

    # Create screening recommendation enum
    screening_recommendation = postgresql.ENUM(
        "advance", "hold", "review",
        name="screening_recommendation"
    )
    screening_recommendation.create(op.get_bind(), checkfirst=True)

    # Create recruiter decision enum
    recruiter_decision = postgresql.ENUM(
        "interview", "hold", "further_review",
        name="recruiter_decision"
    )
    recruiter_decision.create(op.get_bind(), checkfirst=True)

    # Create screening_batches table
    op.create_table(
        "screening_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Enum("queued", "screening", "pending_review", "completed", name="screening_batch_status"), nullable=False, server_default="queued"),
        sa.Column("total_candidates", sa.Integer(), nullable=False),
        sa.Column("screened_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pending_review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("batch_config", sa.Text(), nullable=True),  # Encrypted JSON
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create screening_batches indexes
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
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("agent_recommendation", sa.Enum("advance", "hold", "review", name="screening_recommendation"), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=False),
        sa.Column("screening_summary", sa.Text(), nullable=False),  # Encrypted
        sa.Column("screening_details", sa.Text(), nullable=False),  # Encrypted JSON
        sa.Column("bias_flags", sa.Text(), nullable=False, server_default="{}"),  # Encrypted JSON
        sa.Column("recruiter_decision", sa.Enum("interview", "hold", "further_review", name="recruiter_decision"), nullable=True),
        sa.Column("recruiter_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recruiter_notes", sa.Text(), nullable=True),  # Encrypted
        sa.Column("recruiter_confidence", sa.Integer(), nullable=True),
        sa.Column("was_overridden", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("override_reason", sa.Text(), nullable=True),  # Encrypted
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

    # Create screening_results indexes
    op.create_index("ix_screening_results_batch_id", "screening_results", ["screening_batch_id"])
    op.create_index("ix_screening_results_position_id", "screening_results", ["position_id"])
    op.create_index("ix_screening_results_resume_id", "screening_results", ["resume_id"])
    op.create_index("ix_screening_results_recruiter_id", "screening_results", ["recruiter_id"])
    op.create_index("ix_screening_results_position_recruiter_decision", "screening_results", ["position_id", "recruiter_decision"])
    op.create_index("ix_screening_results_created_at", "screening_results", ["created_at"])
    op.create_index("ix_screening_results_batch_decision", "screening_results", ["screening_batch_id", "recruiter_decision"])

    # Extend assessments table with screening fields
    op.add_column(
        "assessments",
        sa.Column("screening_result_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        "fk_assessments_screening_result_id",
        "assessments",
        "screening_results",
        ["screening_result_id"],
        ["id"],
        ondelete="SET NULL"
    )
    op.create_index("ix_assessments_screening_result_id", "assessments", ["screening_result_id"])

    op.add_column(
        "assessments",
        sa.Column("screening_initiated_at", sa.DateTime(timezone=True), nullable=True)
    )

    op.add_column(
        "assessments",
        sa.Column("screening_phase", sa.String(50), nullable=True, server_default="initial")
    )

    # Extend decisions table with screening fields
    op.add_column(
        "decisions",
        sa.Column("screening_override_reason", sa.Text(), nullable=True)  # Encrypted
    )

    op.add_column(
        "decisions",
        sa.Column("recruiter_confidence", sa.Integer(), nullable=True)
    )

    op.add_column(
        "decisions",
        sa.Column("is_screening_decision", sa.Boolean(), nullable=False, server_default="false")
    )

    op.create_index("ix_decisions_is_screening_decision", "decisions", ["is_screening_decision"])


def downgrade() -> None:
    """Drop screening tables and revert assessment/decision extensions."""

    # Drop indexes
    op.drop_index("ix_screening_results_batch_decision")
    op.drop_index("ix_screening_results_created_at")
    op.drop_index("ix_screening_results_position_recruiter_decision")
    op.drop_index("ix_screening_results_recruiter_id")
    op.drop_index("ix_screening_results_resume_id")
    op.drop_index("ix_screening_results_position_id")
    op.drop_index("ix_screening_results_batch_id")

    op.drop_index("ix_screening_batches_created_at")
    op.drop_index("ix_screening_batches_created_by")
    op.drop_index("ix_screening_batches_position_id_status")

    # Drop tables
    op.drop_table("screening_results")
    op.drop_table("screening_batches")

    # Drop enums
    op.execute("DROP TYPE screening_batch_status")
    op.execute("DROP TYPE screening_recommendation")
    op.execute("DROP TYPE recruiter_decision")

    # Revert assessment extensions
    op.drop_index("ix_assessments_screening_result_id")
    op.drop_constraint("fk_assessments_screening_result_id", "assessments", type_="foreignkey")
    op.drop_column("assessments", "screening_phase")
    op.drop_column("assessments", "screening_initiated_at")
    op.drop_column("assessments", "screening_result_id")

    # Revert decision extensions
    op.drop_index("ix_decisions_is_screening_decision")
    op.drop_column("decisions", "is_screening_decision")
    op.drop_column("decisions", "recruiter_confidence")
    op.drop_column("decisions", "screening_override_reason")
