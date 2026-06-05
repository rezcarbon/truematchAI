"""Add job scraping and mass upload tables

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-03 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create job_scraping_config table
    op.create_table(
        "job_scraping_config",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("poll_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("last_run", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run", sa.DateTime(timezone=True), nullable=True),
        sa.Column("legal_approved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("legal_approval_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_job_scraping_config_source_type", "source_type"),
        sa.Index("ix_job_scraping_config_enabled", "enabled"),
    )

    # Create scraping_run table
    op.create_table(
        "scraping_run",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("config_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("jobs_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("jobs_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("jobs_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["config_id"],
            ["job_scraping_config.id"],
            ondelete="CASCADE",
        ),
        sa.Index("ix_scraping_run_status", "status"),
        sa.Index("ix_scraping_run_config_id", "config_id"),
    )

    # Create mass_upload_batch table
    op.create_table(
        "mass_upload_batch",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("upload_type", sa.String(50), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("filename", sa.String(255), nullable=True),
        sa.Column("field_mapping", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicate_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.Index("ix_mass_upload_batch_status", "status"),
        sa.Index("ix_mass_upload_batch_user_id", "user_id"),
    )

    # Create job_deduplication table
    op.create_table(
        "job_deduplication",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("fingerprint", sa.String(256), nullable=False, unique=True),
        sa.Column("external_ids", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("ingest_queue_item_id", sa.UUID(), nullable=True),
        sa.Column(
            "first_seen",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_seen",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("seen_count", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_job_deduplication_fingerprint", "fingerprint"),
        sa.Index("ix_job_deduplication_ingest_queue_item_id", "ingest_queue_item_id"),
    )

    # Create upload_field_mapping table
    op.create_table(
        "upload_field_mapping",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("field_mapping", sa.JSON(), nullable=False),
        sa.Column("required_fields", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.Index("ix_upload_field_mapping_name", "name"),
        sa.Index("ix_upload_field_mapping_is_system", "is_system"),
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("upload_field_mapping")
    op.drop_table("job_deduplication")
    op.drop_table("mass_upload_batch")
    op.drop_table("scraping_run")
    op.drop_table("job_scraping_config")
