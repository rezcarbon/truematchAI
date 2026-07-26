"""Add learning metrics and cognitive state tables for self-learning system.

Revision ID: 0044
Revises: 0043
Create Date: 2026-07-26 00:00:00.000000

Creates three tables for the learning pipeline:
- assessment_metrics: Daily aggregated model performance (precision, recall, F1)
- cognitive_state: Learned weights, thresholds, biases
- cognitive_evolution_log: Audit trail of learned state changes
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0044"
down_revision: Union[str, None] = "0043"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create assessment_metrics table
    op.create_table(
        "assessment_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("model_version", sa.String(32), nullable=False),
        sa.Column("total_assessments", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assessments_with_outcome", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("true_positives", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("true_negatives", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("false_positives", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("false_negatives", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("precision", sa.Float(), nullable=True),
        sa.Column("recall", sa.Float(), nullable=True),
        sa.Column("f1_score", sa.Float(), nullable=True),
        sa.Column("false_positive_rate", sa.Float(), nullable=True),
        sa.Column("false_negative_rate", sa.Float(), nullable=True),
        sa.Column("avg_confidence", sa.Float(), nullable=True),
        sa.Column("expected_calibration_error", sa.Float(), nullable=True),
        sa.Column("metrics_by_role", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("thresholds_tested", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assessment_metrics_date", "assessment_metrics", ["metric_date"])
    op.create_index("ix_assessment_metrics_model_version", "assessment_metrics", ["model_version"])
    op.create_index("ix_assessment_metrics_accuracy", "assessment_metrics", ["accuracy"])

    # Create cognitive_state table
    op.create_table(
        "cognitive_state",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_type", sa.String(64), nullable=False, server_default="system"),
        sa.Column("decision_weights", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("gate_thresholds", postgresql.JSON(), nullable=False, server_default='{"capability_hire": 60}'),
        sa.Column("verification_confidence", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("known_biases", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("bias_corrections", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("heuristics", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("decision_rules", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("performance_insights", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("edge_cases", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("reasoning_confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cognitive_state_agent_type", "cognitive_state", ["agent_type"])
    op.create_index("ix_cognitive_state_reasoning_confidence", "cognitive_state", ["reasoning_confidence"])

    # Create cognitive_evolution_log table
    op.create_table(
        "cognitive_evolution_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_type", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("before_state", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("after_state", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("change_reason", sa.String(512), nullable=False),
        sa.Column("expected_improvement", sa.Float(), nullable=True),
        sa.Column("actual_improvement", sa.Float(), nullable=True),
        sa.Column("triggered_by_assessment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("triggered_by_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cognitive_evolution_log_agent_type", "cognitive_evolution_log", ["agent_type"])
    op.create_index("ix_cognitive_evolution_log_event_type", "cognitive_evolution_log", ["event_type"])
    op.create_index("ix_cognitive_evolution_log_created_at", "cognitive_evolution_log", ["created_at"])


def downgrade() -> None:
    op.drop_table("cognitive_evolution_log")
    op.drop_table("cognitive_state")
    op.drop_table("assessment_metrics")
