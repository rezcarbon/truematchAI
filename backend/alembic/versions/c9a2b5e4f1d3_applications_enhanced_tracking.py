"""Enhanced applications tracking with detailed funnel analytics and engagement metrics

Revision ID: c9a2b5e4f1d3
Revises: b7d9e2c1a3f6
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "c9a2b5e4f1d3"
down_revision = "b7d9e2c1a3f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enhance applications table with detailed tracking and funnel analytics."""

    # Add engagement and funnel tracking columns to applications table
    op.add_column(
        "applications",
        sa.Column("resume_version_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_applications_resume_version_id",
        "applications",
        "resume_versions",
        ["resume_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_applications_resume_version_id", "applications", ["resume_version_id"])

    # Engagement tracking
    op.add_column("applications", sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("applications", sa.Column("interview_scheduled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("applications", sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("applications", sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("applications", sa.Column("offer_extended_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("applications", sa.Column("offer_accepted_at", sa.DateTime(timezone=True), nullable=True))

    # Rejection tracking - PII should be encrypted
    op.add_column("applications", sa.Column("rejection_reason", sa.Text(), nullable=True))  # Encrypted
    op.add_column("applications", sa.Column("rejection_feedback", sa.Text(), nullable=True))  # Encrypted
    op.add_column("applications", sa.Column("can_reapply", sa.Boolean(), nullable=True, server_default="false"))
    op.add_column("applications", sa.Column("reapply_after", sa.DateTime(timezone=True), nullable=True))

    # Matching and quality metrics
    op.add_column("applications", sa.Column("initial_match_score", sa.Float(), nullable=True))
    op.add_column("applications", sa.Column("current_match_score", sa.Float(), nullable=True))
    op.add_column("applications", sa.Column("fit_assessment", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # Communication tracking
    op.add_column("applications", sa.Column("messages_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("applications", sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("applications", sa.Column("requires_response", sa.Boolean(), nullable=False, server_default="false"))

    # Application customization
    op.add_column("applications", sa.Column("custom_cover_letter", sa.Text(), nullable=True))  # Encrypted
    op.add_column("applications", sa.Column("application_answers", postgresql.JSONB(astext_type=sa.Text()), nullable=True))  # Custom form answers

    # Application status enhancements
    op.add_column("applications", sa.Column("stage_notes", sa.String(length=1024), nullable=True))
    op.add_column("applications", sa.Column("priority", sa.String(length=20), nullable=False, server_default="normal"))  # high, normal, low
    op.add_column("applications", sa.Column("is_flagged", sa.Boolean(), nullable=False, server_default="false"))

    # Recruiter assignment
    op.add_column("applications", sa.Column("assigned_to_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_applications_assigned_to_id",
        "applications",
        "users",
        ["assigned_to_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_applications_assigned_to_id", "applications", ["assigned_to_id"])

    # Enhanced indices for common queries
    op.create_index("ix_applications_viewed_at", "applications", ["viewed_at"])
    op.create_index("ix_applications_interview_scheduled_at", "applications", ["interview_scheduled_at"])
    op.create_index("ix_applications_rejected_at", "applications", ["rejected_at"])
    op.create_index("ix_applications_priority", "applications", ["priority"])
    op.create_index("ix_applications_is_flagged", "applications", ["is_flagged"])
    op.create_index("ix_applications_requires_response", "applications", ["requires_response"])

    # Composite indices for funnel analysis
    op.create_index(
        "ix_applications_position_stage",
        "applications",
        ["position_id", "stage"],
    )
    op.create_index(
        "ix_applications_stage_updated",
        "applications",
        ["stage", "updated_at"],
    )
    op.create_index(
        "ix_applications_user_priority",
        "applications",
        ["user_id", "priority"],
    )


    # Create application_events table for detailed activity tracking
    op.create_table(
        "application_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),

        # Event details
        sa.Column("event_type", sa.String(length=100), nullable=False),  # status_changed, message_sent, viewed, interview_scheduled, etc.
        sa.Column("event_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # Flexible event metadata
        sa.Column("description", sa.String(length=512), nullable=True),

        # Actor tracking (who triggered the event)
        sa.Column("triggered_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_type", sa.String(length=50), nullable=False, server_default="system"),  # system, user, automation, ats_sync

        # Audit trail
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["triggered_by_id"], ["users.id"], ondelete="SET NULL"),
    )

    # Indices for application_events
    op.create_index("ix_application_events_application_id", "application_events", ["application_id"])
    op.create_index("ix_application_events_user_id", "application_events", ["user_id"])
    op.create_index("ix_application_events_event_type", "application_events", ["event_type"])
    op.create_index("ix_application_events_created_at", "application_events", ["created_at"])
    op.create_index("ix_application_events_triggered_by_id", "application_events", ["triggered_by_id"])

    # Composite indices
    op.create_index(
        "ix_application_events_app_type",
        "application_events",
        ["application_id", "event_type"],
    )
    op.create_index(
        "ix_application_events_app_created",
        "application_events",
        ["application_id", "created_at"],
    )


    # Create application_feedback table for structured feedback at each stage
    op.create_table(
        "application_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feedback_stage", sa.String(length=50), nullable=False),  # phone_screen, technical, onsite, etc.

        # Feedback content - PII should be encrypted
        sa.Column("overall_rating", sa.Integer(), nullable=True),  # 1-5 scale
        sa.Column("feedback_text", sa.Text(), nullable=True),  # Encrypted
        sa.Column("structured_feedback", postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Interviewer/reviewer info
        sa.Column("provided_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provided_by_name", sa.String(length=512), nullable=True),

        # Decision tracking
        sa.Column("recommendation", sa.String(length=50), nullable=True),  # proceed, maybe, reject
        sa.Column("confidence_score", sa.Float(), nullable=True),

        # Audit trail
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["provided_by_id"], ["users.id"], ondelete="CASCADE"),
    )

    # Indices for application_feedback
    op.create_index("ix_application_feedback_application_id", "application_feedback", ["application_id"])
    op.create_index("ix_application_feedback_stage", "application_feedback", ["feedback_stage"])
    op.create_index("ix_application_feedback_provided_by_id", "application_feedback", ["provided_by_id"])
    op.create_index("ix_application_feedback_recommendation", "application_feedback", ["recommendation"])
    op.create_index("ix_application_feedback_created_at", "application_feedback", ["created_at"])

    # Composite index
    op.create_index(
        "ix_application_feedback_app_stage",
        "application_feedback",
        ["application_id", "feedback_stage"],
    )


def downgrade() -> None:
    """Rollback: remove enhanced applications tracking."""

    # Drop application_feedback table
    op.drop_index("ix_application_feedback_app_stage", table_name="application_feedback")
    op.drop_index("ix_application_feedback_created_at", table_name="application_feedback")
    op.drop_index("ix_application_feedback_recommendation", table_name="application_feedback")
    op.drop_index("ix_application_feedback_provided_by_id", table_name="application_feedback")
    op.drop_index("ix_application_feedback_stage", table_name="application_feedback")
    op.drop_index("ix_application_feedback_application_id", table_name="application_feedback")
    op.drop_table("application_feedback")

    # Drop application_events table
    op.drop_index("ix_application_events_app_created", table_name="application_events")
    op.drop_index("ix_application_events_app_type", table_name="application_events")
    op.drop_index("ix_application_events_triggered_by_id", table_name="application_events")
    op.drop_index("ix_application_events_created_at", table_name="application_events")
    op.drop_index("ix_application_events_event_type", table_name="application_events")
    op.drop_index("ix_application_events_user_id", table_name="application_events")
    op.drop_index("ix_application_events_application_id", table_name="application_events")
    op.drop_table("application_events")

    # Drop enhanced indices from applications
    op.drop_index("ix_applications_user_priority", table_name="applications")
    op.drop_index("ix_applications_stage_updated", table_name="applications")
    op.drop_index("ix_applications_position_stage", table_name="applications")
    op.drop_index("ix_applications_requires_response", table_name="applications")
    op.drop_index("ix_applications_is_flagged", table_name="applications")
    op.drop_index("ix_applications_priority", table_name="applications")
    op.drop_index("ix_applications_rejected_at", table_name="applications")
    op.drop_index("ix_applications_interview_scheduled_at", table_name="applications")
    op.drop_index("ix_applications_viewed_at", table_name="applications")

    # Drop foreign keys and indices from applications
    op.drop_index("ix_applications_assigned_to_id", table_name="applications")
    op.drop_constraint("fk_applications_assigned_to_id", "applications", type_="foreignkey")
    op.drop_column("applications", "assigned_to_id")

    op.drop_index("ix_applications_resume_version_id", table_name="applications")
    op.drop_constraint("fk_applications_resume_version_id", "applications", type_="foreignkey")

    # Drop columns from applications
    op.drop_column("applications", "resume_version_id")
    op.drop_column("applications", "requires_response")
    op.drop_column("applications", "last_message_at")
    op.drop_column("applications", "messages_count")
    op.drop_column("applications", "application_answers")
    op.drop_column("applications", "custom_cover_letter")
    op.drop_column("applications", "fit_assessment")
    op.drop_column("applications", "current_match_score")
    op.drop_column("applications", "initial_match_score")
    op.drop_column("applications", "reapply_after")
    op.drop_column("applications", "can_reapply")
    op.drop_column("applications", "rejection_feedback")
    op.drop_column("applications", "rejection_reason")
    op.drop_column("applications", "offer_accepted_at")
    op.drop_column("applications", "offer_extended_at")
    op.drop_column("applications", "withdrawn_at")
    op.drop_column("applications", "rejected_at")
    op.drop_column("applications", "interview_scheduled_at")
    op.drop_column("applications", "viewed_at")
    op.drop_column("applications", "is_flagged")
    op.drop_column("applications", "priority")
    op.drop_column("applications", "stage_notes")
