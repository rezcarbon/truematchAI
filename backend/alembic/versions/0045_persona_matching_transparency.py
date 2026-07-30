"""Add persona matching and match notification timeline support

Revision ID: 0045
Revises: 0044
Create Date: 2026-07-30 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


# revision identifiers, used by Alembic.
revision = "0045"
down_revision = "0044"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add persona-aware matching columns to candidate_matches
    op.add_column(
        "candidate_matches",
        sa.Column(
            "matched_by_persona",
            sa.Text(),
            nullable=True,
            comment="Persona ID that generated this match (career_coach, interview_coach, etc.)",
        ),
    )
    op.add_column(
        "candidate_matches",
        sa.Column(
            "persona_confidence",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="0-100 confidence in persona-based match",
        ),
    )
    op.add_column(
        "candidate_matches",
        sa.Column(
            "persona_reasoning",
            sa.Text(),
            nullable=True,
            comment="Explanation of why this persona matched candidate to role",
        ),
    )

    # Create match_notifications table for transparency timeline
    op.create_table(
        "match_notifications",
        sa.Column("id", PG_UUID(as_uuid=True), nullable=False),
        sa.Column(
            "candidate_match_id",
            PG_UUID(as_uuid=True),
            nullable=False,
            comment="Reference to candidate_matches",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "profile_sent",
                "profile_viewed",
                "interview_scheduled",
                "interview_completed",
                "offer_received",
                "rejected",
                name="notification_status",
            ),
            nullable=False,
            comment="Status of match in the pipeline",
        ),
        sa.Column(
            "message",
            sa.Text(),
            nullable=True,
            comment="Human-readable status message",
        ),
        sa.Column(
            "status_timestamp",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            comment="When this status occurred",
        ),
        sa.Column(
            "email_sent",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Whether email notification was sent",
        ),
        sa.Column(
            "email_sent_at",
            sa.DateTime(),
            nullable=True,
            comment="When email was sent",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["candidate_match_id"], ["candidate_matches.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_match_notifications_candidate_match_id", "candidate_match_id"),
        sa.Index("ix_match_notifications_status", "status"),
        sa.Index("ix_match_notifications_timestamp", "status_timestamp"),
    )


def downgrade() -> None:
    # Drop match_notifications table
    op.drop_table("match_notifications")

    # Remove persona columns from candidate_matches
    op.drop_column("candidate_matches", "persona_reasoning")
    op.drop_column("candidate_matches", "persona_confidence")
    op.drop_column("candidate_matches", "matched_by_persona")
