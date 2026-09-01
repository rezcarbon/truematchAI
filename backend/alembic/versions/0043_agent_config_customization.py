"""Agent Configuration System - Customizable agent instructions and tools.

Revision ID: 0043
Revises: 0042
Create Date: 2026-07-16 10:00:00.000000

Phase: Agent Customization
- Allows recruiters to customize agent instructions without code changes
- Enables per-workspace agent configuration with versioning
- Provides audit trail for all configuration changes
- Supports approval workflow for agent changes
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0043"
down_revision = "0042"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    """Create agent configuration tables."""

    # Create enums for agent config status and audit actions
    agent_config_status = postgresql.ENUM(
        "draft",
        "pending_approval",
        "approved",
        "active",
        "deprecated",
        name="agent_config_status",
        create_type=False,
    )
    postgresql.ENUM(
        "draft",
        "pending_approval",
        "approved",
        "active",
        "deprecated",
        name="agent_config_status",
    ).create(op.get_bind(), checkfirst=True)

    agent_config_audit_action = postgresql.ENUM(
        "created",
        "modified",
        "submitted",
        "approved",
        "rejected",
        "activated",
        "deprecated",
        name="agent_config_audit_action",
        create_type=False,
    )
    postgresql.ENUM(
        "created",
        "modified",
        "submitted",
        "approved",
        "rejected",
        "activated",
        "deprecated",
        name="agent_config_audit_action",
    ).create(op.get_bind(), checkfirst=True)

    # Create agent_configs table
    op.create_table(
        "agent_configs",
        sa.Column("id", UUID, nullable=False),
        sa.Column(
            "company_id",
            UUID,
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("agent_type", sa.String(50), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("status", agent_config_status, server_default="draft", nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("tools_enabled", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("tool_parameters", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("agent_parameters", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("latest_version_id", UUID, nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_by_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "approved_by_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", TS, nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("created_at", TS, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TS, server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for agent_configs
    op.create_index("ix_agent_configs_company_id", "agent_configs", ["company_id"])
    op.create_index("ix_agent_configs_agent_type", "agent_configs", ["agent_type"])
    op.create_index("ix_agent_configs_role", "agent_configs", ["role"])
    op.create_index("ix_agent_configs_status", "agent_configs", ["status"])
    op.create_index(
        "ix_agent_configs_company_agent", "agent_configs", ["company_id", "agent_type"]
    )
    op.create_index(
        "ix_agent_configs_company_role", "agent_configs", ["company_id", "role"]
    )
    op.create_index("ix_agent_configs_created_at", "agent_configs", ["created_at"])

    # Create agent_config_versions table
    op.create_table(
        "agent_config_versions",
        sa.Column("id", UUID, nullable=False),
        sa.Column(
            "config_id",
            UUID,
            sa.ForeignKey("agent_configs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("tools_enabled", postgresql.JSONB(), nullable=False),
        sa.Column("tool_parameters", postgresql.JSONB(), nullable=False),
        sa.Column("agent_parameters", postgresql.JSONB(), nullable=False),
        sa.Column("status", agent_config_status, server_default="draft", nullable=False),
        sa.Column(
            "submitted_by_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("submitted_at", TS, nullable=True),
        sa.Column(
            "approved_by_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", TS, nullable=True),
        sa.Column("approval_feedback", sa.Text(), nullable=True),
        sa.Column("activated_at", TS, nullable=True),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("created_at", TS, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TS, server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for agent_config_versions
    op.create_index("ix_agent_config_versions_config_id", "agent_config_versions", ["config_id"])
    op.create_index("ix_agent_config_versions_status", "agent_config_versions", ["status"])
    op.create_index("ix_agent_config_versions_created_at", "agent_config_versions", ["created_at"])
    op.create_index(
        "ix_agent_config_versions_config_version",
        "agent_config_versions",
        ["config_id", "version_number"],
    )

    # Add FK from agent_configs.latest_version_id to agent_config_versions
    op.create_foreign_key(
        "fk_agent_configs_latest_version_id",
        "agent_configs",
        "agent_config_versions",
        ["latest_version_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Create agent_config_audits table
    op.create_table(
        "agent_config_audits",
        sa.Column("id", UUID, nullable=False),
        sa.Column(
            "config_id",
            UUID,
            sa.ForeignKey("agent_configs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "version_id",
            UUID,
            sa.ForeignKey("agent_config_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", agent_config_audit_action, nullable=False),
        sa.Column(
            "actor_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actor_role", sa.String(50), nullable=True),
        sa.Column("changes", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("created_at", TS, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TS, server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for agent_config_audits
    op.create_index("ix_agent_config_audits_config_id", "agent_config_audits", ["config_id"])
    op.create_index("ix_agent_config_audits_actor_id", "agent_config_audits", ["actor_id"])
    op.create_index("ix_agent_config_audits_action", "agent_config_audits", ["action"])
    op.create_index("ix_agent_config_audits_created_at", "agent_config_audits", ["created_at"])


def downgrade() -> None:
    """Drop agent configuration tables."""

    # Drop tables in reverse order of creation
    op.drop_table("agent_config_audits")
    op.drop_table("agent_config_versions")
    op.drop_table("agent_configs")

    # Drop enums
    postgresql.ENUM(name="agent_config_audit_action").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="agent_config_status").drop(op.get_bind(), checkfirst=True)
