"""Resume versioning with full history tracking and encryption for PII

Revision ID: a5f8c1d2e3b7
Revises: f3d9b27a1e64
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "a5f8c1d2e3b7"
down_revision = "f3d9b27a1e64"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create resume_versions table for full version history tracking."""
    # Create the resume_versions table to track all versions of a resume
    op.create_table(
        "resume_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),

        # Version tracking
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),

        # File and parsing information
        sa.Column("file_id", sa.String(length=512), nullable=True),
        sa.Column("file_name", sa.String(length=512), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("file_type", sa.String(length=64), nullable=True),

        # Language and content
        sa.Column("source_language", sa.String(length=8), nullable=True),
        sa.Column("detected_language", sa.String(length=8), nullable=True),

        # PII at rest — encrypted using AES-256-GCM
        sa.Column("parsed_data", sa.Text(), nullable=True),  # Encrypted JSON
        sa.Column("raw_narrative", sa.Text(), nullable=True),  # Encrypted text
        sa.Column("supplementary", sa.Text(), nullable=True),  # Encrypted JSON

        # Metadata and quality scoring
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("completeness_percentage", sa.Integer(), nullable=True),
        sa.Column("sections_detected", postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Change tracking
        sa.Column("change_summary", sa.String(length=512), nullable=True),
        sa.Column("change_type", sa.String(length=50), nullable=False, server_default="upload"),  # upload, edit, ai_enhancement, import
        sa.Column("change_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Audit trail
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),

        sa.UniqueConstraint("resume_id", "version_number", name="uq_resume_version_number"),
    )

    # Indices for performance
    op.create_index("ix_resume_versions_resume_id", "resume_versions", ["resume_id"])
    op.create_index("ix_resume_versions_user_id", "resume_versions", ["user_id"])
    op.create_index("ix_resume_versions_is_current", "resume_versions", ["is_current"])
    op.create_index("ix_resume_versions_change_type", "resume_versions", ["change_type"])
    op.create_index("ix_resume_versions_created_at", "resume_versions", ["created_at"])
    op.create_index("ix_resume_versions_archived_at", "resume_versions", ["archived_at"])

    # Composite indices for common queries
    op.create_index(
        "ix_resume_versions_user_current",
        "resume_versions",
        ["user_id", "is_current"],
    )
    op.create_index(
        "ix_resume_versions_resume_created",
        "resume_versions",
        ["resume_id", "created_at"],
    )

    # Add tracking columns to existing resumes table
    op.add_column("resumes", sa.Column("version_count", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("resumes", sa.Column("latest_version_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("resumes", sa.Column("total_downloads", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    """Rollback: remove resume versioning infrastructure."""
    # Drop columns from resumes table
    op.drop_column("resumes", "total_downloads")
    op.drop_column("resumes", "latest_version_at")
    op.drop_column("resumes", "version_count")

    # Drop indices
    op.drop_index("ix_resume_versions_resume_created", table_name="resume_versions")
    op.drop_index("ix_resume_versions_user_current", table_name="resume_versions")
    op.drop_index("ix_resume_versions_archived_at", table_name="resume_versions")
    op.drop_index("ix_resume_versions_created_at", table_name="resume_versions")
    op.drop_index("ix_resume_versions_change_type", table_name="resume_versions")
    op.drop_index("ix_resume_versions_is_current", table_name="resume_versions")
    op.drop_index("ix_resume_versions_user_id", table_name="resume_versions")
    op.drop_index("ix_resume_versions_resume_id", table_name="resume_versions")

    # Drop table
    op.drop_table("resume_versions")
