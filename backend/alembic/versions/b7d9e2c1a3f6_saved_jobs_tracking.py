"""Saved jobs tracking for candidates to curate job opportunities

Revision ID: b7d9e2c1a3f6
Revises: a5f8c1d2e3b7
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "b7d9e2c1a3f6"
down_revision = "a5f8c1d2e3b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create saved_jobs table for job curation and tracking."""
    # Create the saved_jobs table
    op.create_table(
        "saved_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),

        # Save metadata
        sa.Column("list_name", sa.String(length=255), nullable=False, server_default="Default"),
        sa.Column("notes", sa.Text(), nullable=True),  # User-provided notes about the job

        # Job snapshot (denormalized for fast access without joins)
        sa.Column("job_title", sa.String(length=512), nullable=True),
        sa.Column("company_name", sa.String(length=512), nullable=True),
        sa.Column("job_url", sa.String(length=2048), nullable=True),

        # Relevance and matching scores (encrypted - PII)
        sa.Column("match_score", sa.Float(), nullable=True),
        sa.Column("relevance_metadata", sa.Text(), nullable=True),  # Encrypted JSON

        # Status tracking
        sa.Column("status", sa.String(length=50), nullable=False, server_default="saved"),  # saved, viewed, applied, archived, rejected
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),

        # Notification preferences
        sa.Column("notify_on_update", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_notified_at", sa.DateTime(timezone=True), nullable=True),

        # Audit trail
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="CASCADE"),

        # Ensure users can only save a job once
        sa.UniqueConstraint("user_id", "position_id", name="uq_saved_jobs_user_position"),
    )

    # Indices for performance
    op.create_index("ix_saved_jobs_user_id", "saved_jobs", ["user_id"])
    op.create_index("ix_saved_jobs_position_id", "saved_jobs", ["position_id"])
    op.create_index("ix_saved_jobs_status", "saved_jobs", ["status"])
    op.create_index("ix_saved_jobs_list_name", "saved_jobs", ["list_name"])
    op.create_index("ix_saved_jobs_created_at", "saved_jobs", ["created_at"])
    op.create_index("ix_saved_jobs_archived_at", "saved_jobs", ["archived_at"])

    # Composite indices for common queries
    op.create_index(
        "ix_saved_jobs_user_status",
        "saved_jobs",
        ["user_id", "status"],
    )
    op.create_index(
        "ix_saved_jobs_user_created",
        "saved_jobs",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_saved_jobs_user_list_status",
        "saved_jobs",
        ["user_id", "list_name", "status"],
    )

    # Create saved_jobs_lists table for organizing saves into custom lists/folders
    op.create_table(
        "saved_jobs_lists",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),

        # List metadata
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("color", sa.String(length=7), nullable=True),

        # List configuration
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_shared", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("job_count", sa.Integer(), nullable=False, server_default="0"),

        # Audit trail
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),

        # Each user should have unique list names (but allow one default per user)
        sa.UniqueConstraint("user_id", "name", name="uq_saved_jobs_list_user_name"),
    )

    # Indices for saved_jobs_lists
    op.create_index("ix_saved_jobs_lists_user_id", "saved_jobs_lists", ["user_id"])
    op.create_index("ix_saved_jobs_lists_is_default", "saved_jobs_lists", ["is_default"])
    op.create_index("ix_saved_jobs_lists_created_at", "saved_jobs_lists", ["created_at"])

    # Add list_id foreign key to saved_jobs
    op.add_column(
        "saved_jobs",
        sa.Column("list_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_saved_jobs_list_id",
        "saved_jobs",
        "saved_jobs_lists",
        ["list_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_saved_jobs_list_id", "saved_jobs", ["list_id"])


def downgrade() -> None:
    """Rollback: remove saved jobs tracking infrastructure."""
    # Drop foreign key and column from saved_jobs
    op.drop_index("ix_saved_jobs_list_id", table_name="saved_jobs")
    op.drop_constraint("fk_saved_jobs_list_id", "saved_jobs", type_="foreignkey")
    op.drop_column("saved_jobs", "list_id")

    # Drop indices from saved_jobs_lists
    op.drop_index("ix_saved_jobs_lists_created_at", table_name="saved_jobs_lists")
    op.drop_index("ix_saved_jobs_lists_is_default", table_name="saved_jobs_lists")
    op.drop_index("ix_saved_jobs_lists_user_id", table_name="saved_jobs_lists")

    # Drop saved_jobs_lists table
    op.drop_table("saved_jobs_lists")

    # Drop indices from saved_jobs
    op.drop_index("ix_saved_jobs_user_list_status", table_name="saved_jobs")
    op.drop_index("ix_saved_jobs_user_created", table_name="saved_jobs")
    op.drop_index("ix_saved_jobs_user_status", table_name="saved_jobs")
    op.drop_index("ix_saved_jobs_archived_at", table_name="saved_jobs")
    op.drop_index("ix_saved_jobs_created_at", table_name="saved_jobs")
    op.drop_index("ix_saved_jobs_list_name", table_name="saved_jobs")
    op.drop_index("ix_saved_jobs_status", table_name="saved_jobs")
    op.drop_index("ix_saved_jobs_position_id", table_name="saved_jobs")
    op.drop_index("ix_saved_jobs_user_id", table_name="saved_jobs")

    # Drop saved_jobs table
    op.drop_table("saved_jobs")
