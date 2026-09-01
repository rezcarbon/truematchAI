"""Add training data tables for autonomous AI-native learning.

Revision ID: 0017
Revises: 0016
Create Date: 2026-06-06 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create training data tables."""
    # Create training_data_uploads table
    op.create_table(
        "training_data_uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("format", sa.String(10), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("items_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("insights_extracted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processing_stats", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_training_data_uploads_user_id", "user_id"),
        sa.Index("ix_training_data_uploads_status", "status"),
        sa.Index("ix_training_data_uploads_created_at", "created_at"),
    )

    # Create training_data_items table
    op.create_table(
        "training_data_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("upload_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_name", sa.String(255), nullable=True),
        sa.Column("candidate_email", sa.String(255), nullable=True),
        sa.Column("candidate_profile", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("decision", sa.String(20), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("extracted_capabilities", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("extracted_credentials", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("capability_confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("source_row", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("applied_to_training", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("applied_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["upload_id"], ["training_data_uploads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_training_data_items_upload_id", "upload_id"),
        sa.Index("ix_training_data_items_decision", "decision"),
        sa.Index("ix_training_data_items_applied", "applied_to_training"),
    )

    # Create training_chat_messages table
    op.create_table(
        "training_chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_message", sa.Text(), nullable=False),
        sa.Column("ai_response", sa.Text(), nullable=False),
        sa.Column("extracted_training_signal", postgresql.JSON(), nullable=True),
        sa.Column("feedback_type", sa.String(50), nullable=True),
        sa.Column("applied_to_training", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("applied_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_training_chat_messages_user_id", "user_id"),
        sa.Index("ix_training_chat_messages_session_id", "session_id"),
        sa.Index("ix_training_chat_messages_created_at", "created_at"),
    )

    # Create training_insight_batches table
    op.create_table(
        "training_insight_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("insights", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("new_capabilities", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("updated_mappings", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("updated_credentials", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("new_success_patterns", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("improvement_metrics", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("virtual_brain_state_version", sa.Integer(), nullable=False),
        sa.Column("match_accuracy_before", sa.Float(), nullable=False),
        sa.Column("match_accuracy_after", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("applied_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_training_insight_batches_source", "source"),
        sa.Index("ix_training_insight_batches_created_at", "created_at"),
    )

    # Create training_learning_sessions table
    op.create_table(
        "training_learning_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("insights_extracted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mappings_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("patterns_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_training_learning_sessions_user_id", "user_id"),
        sa.Index("ix_training_learning_sessions_status", "status"),
        sa.Index("ix_training_learning_sessions_created_at", "created_at"),
    )


def downgrade() -> None:
    """Drop training data tables."""
    op.drop_table("training_learning_sessions")
    op.drop_table("training_insight_batches")
    op.drop_table("training_chat_messages")
    op.drop_table("training_data_items")
    op.drop_table("training_data_uploads")
