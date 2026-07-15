"""Phase 2: Assessment Designer - create assessment_designs table

Revision ID: 0041
Revises: 0040
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0041"
down_revision = "0040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create assessment_designs table for Phase 2 agent implementation."""

    # Create assessment design review status enum
    review_status_enum = postgresql.ENUM(
        "pending_review", "approved", "changes_requested", "rejected",
        name="assessment_design_review_status"
    )
    review_status_enum.create(op.get_bind(), checkfirst=True)

    # Create assessment_designs table
    op.create_table(
        "assessment_designs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("screening_result_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("agent_designed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("agent_design", sa.Text(), nullable=False),  # Encrypted JSON
        sa.Column("design_fairness_check", sa.Text(), nullable=False, server_default="{}"),  # Encrypted JSON
        sa.Column("review_status", sa.Enum("pending_review", "approved", "changes_requested", "rejected", name="assessment_design_review_status"), nullable=False, server_default="pending_review"),
        sa.Column("recruiter_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recruiter_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recruiter_feedback", sa.Text(), nullable=True),  # Encrypted
        sa.Column("recruiter_confidence", sa.Integer(), nullable=True),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["candidate_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["screening_result_id"], ["screening_results.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recruiter_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("ix_assessment_designs_position_id", "assessment_designs", ["position_id"])
    op.create_index("ix_assessment_designs_candidate_id", "assessment_designs", ["candidate_id"])
    op.create_index("ix_assessment_designs_review_status", "assessment_designs", ["review_status"])
    op.create_index("ix_assessment_designs_recruiter_id", "assessment_designs", ["recruiter_id"])
    op.create_index("ix_assessment_designs_created_at", "assessment_designs", ["created_at"])
    op.create_index("ix_assessment_designs_position_status", "assessment_designs", ["position_id", "review_status"])

    # Extend assessments table with design fields
    op.add_column(
        "assessments",
        sa.Column("assessment_design_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        "fk_assessments_assessment_design_id",
        "assessments",
        "assessment_designs",
        ["assessment_design_id"],
        ["id"],
        ondelete="SET NULL"
    )
    op.create_index("ix_assessments_assessment_design_id", "assessments", ["assessment_design_id"])

    op.add_column(
        "assessments",
        sa.Column("design_approved_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    """Drop assessment_designs table and revert extensions."""

    # Drop indexes
    op.drop_index("ix_assessment_designs_position_status")
    op.drop_index("ix_assessment_designs_created_at")
    op.drop_index("ix_assessment_designs_recruiter_id")
    op.drop_index("ix_assessment_designs_review_status")
    op.drop_index("ix_assessment_designs_candidate_id")
    op.drop_index("ix_assessment_designs_position_id")

    # Drop table
    op.drop_table("assessment_designs")

    # Drop enum
    op.execute("DROP TYPE assessment_design_review_status")

    # Revert assessment extensions
    op.drop_index("ix_assessments_assessment_design_id")
    op.drop_constraint("fk_assessments_assessment_design_id", "assessments", type_="foreignkey")
    op.drop_column("assessments", "design_approved_at")
    op.drop_column("assessments", "assessment_design_id")
