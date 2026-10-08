"""Add Phase 2 tables for interview intelligence and retention prediction.

Migration for:
- interview_analysis: Interview analysis and feedback
- interview_prep: Interview preparation materials
- retention_predictions: Post-hire retention risk predictions
- intervention_records: Manager coaching interventions
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "phase2_001_interview_retention"
down_revision = "phase1_001_forecasting_salary"
branch_labels = None
depends_on = None


def upgrade():
    """Create Phase 2 tables."""

    # Interview analysis table
    op.create_table(
        "interview_analysis",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interview_id", sa.String(100), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("interview_date", sa.DateTime(), nullable=False),
        sa.Column("has_transcript", sa.Boolean(), default=False),
        sa.Column("transcript_text", sa.Text(), nullable=True),
        sa.Column("communication_score", sa.Integer(), nullable=True),
        sa.Column("technical_score", sa.Integer(), nullable=True),
        sa.Column("cultural_fit_score", sa.Integer(), nullable=True),
        sa.Column("overall_score", sa.Integer(), nullable=True),
        sa.Column("recommendation", sa.String(50), nullable=True),
        sa.Column("strengths", postgresql.JSON(), nullable=True),
        sa.Column("concerns", postgresql.JSON(), nullable=True),
        sa.Column("preparation_quality", sa.Float(), nullable=True),
        sa.Column("communication_effectiveness", sa.Float(), nullable=True),
        sa.Column("skills_alignment", sa.Float(), nullable=True),
        sa.Column("recommended_next_step", sa.String(50), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["candidate_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interview_analysis_candidate_id", "interview_analysis", ["candidate_id"])
    op.create_index("ix_interview_analysis_position_id", "interview_analysis", ["position_id"])
    op.create_index("ix_interview_analysis_interview_date", "interview_analysis", ["interview_date"])

    # Retention predictions table
    op.create_table(
        "retention_predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hire_id", sa.String(100), nullable=False, unique=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hire_date", sa.DateTime(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(50), nullable=False),
        sa.Column("detected_signals", postgresql.JSON(), nullable=True),
        sa.Column("primary_risk_factor", sa.String(100), nullable=True),
        sa.Column("days_to_attrition", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("strengths", postgresql.JSON(), nullable=True),
        sa.Column("challenges", postgresql.JSON(), nullable=True),
        sa.Column("assessment_period", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["candidate_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_retention_predictions_candidate_id", "retention_predictions", ["candidate_id"])
    op.create_index("ix_retention_predictions_position_id", "retention_predictions", ["position_id"])
    op.create_index("ix_retention_predictions_risk_level", "retention_predictions", ["risk_level"])
    op.create_index("ix_retention_predictions_hire_date", "retention_predictions", ["hire_date"])

    # Intervention records table
    op.create_table(
        "intervention_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hire_id", sa.String(100), nullable=False),
        sa.Column("retention_prediction_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("intervention_type", sa.String(100), nullable=False),
        sa.Column("priority", sa.String(50), nullable=False),
        sa.Column("target_audience", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("action_steps", postgresql.JSON(), nullable=True),
        sa.Column("completed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("outcome", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["retention_prediction_id"], ["retention_predictions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["completed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_intervention_records_hire_id", "intervention_records", ["hire_id"])
    op.create_index("ix_intervention_records_intervention_type", "intervention_records", ["intervention_type"])
    op.create_index("ix_intervention_records_created_at", "intervention_records", ["created_at"])


def downgrade():
    """Drop Phase 2 tables."""
    op.drop_table("intervention_records")
    op.drop_table("retention_predictions")
    op.drop_table("interview_analysis")
