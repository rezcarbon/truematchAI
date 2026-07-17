"""Agent Configuration models — Customizable agent instructions and tool access.

This module enables recruiters to customize agent behavior (instructions, tools, parameters)
without code changes. Changes are versioned, audited, and require approval before activation.

Models:
- AgentConfig: Current configuration for an agent within a workspace/role
- AgentConfigVersion: Immutable snapshot of a configuration at a point in time
- AgentConfigAudit: Audit trail of who changed what, when, and why
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk
from app.models._types import EncryptedJSON, EncryptedText


class AgentConfigStatus(str, enum.Enum):
    """Status of an agent configuration."""
    draft = "draft"  # Being edited, not yet submitted
    pending_approval = "pending_approval"  # Submitted, awaiting admin approval
    approved = "approved"  # Approved but not yet active
    active = "active"  # Currently in use
    deprecated = "deprecated"  # Replaced by newer version


class AgentConfigAuditAction(str, enum.Enum):
    """Type of action performed on agent config."""
    created = "created"  # New config created
    modified = "modified"  # Config updated
    submitted = "submitted"  # Submitted for approval
    approved = "approved"  # Admin approved
    rejected = "rejected"  # Admin rejected
    activated = "activated"  # Activated as current config
    deprecated = "deprecated"  # Marked as old version


class AgentConfig(Base, TimestampMixin):
    """Current configuration for an agent (instructions, tools, parameters).

    Agents in TrueMatch can be customized per workspace/role. This table stores
    the latest configuration (either draft or active). Versions are stored separately.
    """
    __tablename__ = "agent_configs"

    id: Mapped[uuid.UUID] = uuid_pk()

    # Company/Organization (who owns this config)
    company_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # recruiter, candidate, admin, etc.
    role: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # recruiter, candidate, admin

    # Status
    status: Mapped[AgentConfigStatus] = mapped_column(
        SAEnum(AgentConfigStatus, name="agent_config_status"),
        default=AgentConfigStatus.draft,
        nullable=False,
    )

    # Configuration (encrypted for sensitivity)
    instructions: Mapped[str] = mapped_column(
        EncryptedText, nullable=False
    )  # System prompt for the agent
    tools_enabled: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )  # Which tools are available: ["analyze", "rank", "schedule", ...]
    tool_parameters: Mapped[dict] = mapped_column(
        EncryptedJSON, nullable=False, default=dict
    )  # Per-tool settings: {"analyze": {"max_length": 5000}, ...}
    agent_parameters: Mapped[dict] = mapped_column(
        EncryptedJSON, nullable=False, default=dict
    )  # Global agent settings: {"temperature": 0.7, "model": "claude-sonnet", ...}

    # Version tracking
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Incremental version (1, 2, 3, ...) for easy reference

    latest_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agent_config_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    # FK to latest AgentConfigVersion (for quick lookup without query)

    # Metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # "Default Recruiter", "Cultural Fit Agent", etc.
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # What this config does
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )  # Who created this config
    approved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )  # Who approved it (admin)
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # When approved

    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # Is this the default config for this role?

    # Relationships
    versions = relationship(
        "AgentConfigVersion",
        back_populates="config",
        cascade="all, delete-orphan",
    )
    audit_logs = relationship(
        "AgentConfigAudit",
        back_populates="config",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_agent_configs_company_id", company_id),
        Index("ix_agent_configs_agent_type", agent_type),
        Index("ix_agent_configs_role", role),
        Index("ix_agent_configs_status", status),
        Index("ix_agent_configs_company_agent", company_id, agent_type),
        Index("ix_agent_configs_company_role", company_id, role),
        Index("ix_agent_configs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"AgentConfig({self.agent_type} v{self.version_number}, status={self.status})"


class AgentConfigVersion(Base, TimestampMixin):
    """Immutable snapshot of an agent configuration at a point in time.

    Each version represents a complete state of the configuration at the time
    it was created. This enables rollback, comparison, and audit trails.
    """
    __tablename__ = "agent_config_versions"

    id: Mapped[uuid.UUID] = uuid_pk()

    # Reference to parent config
    config_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agent_configs.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Version number (immutable, incremental)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    # e.g., 1, 2, 3, ... (paired with config_id for uniqueness)

    # Snapshot of configuration (immutable)
    instructions: Mapped[str] = mapped_column(EncryptedText, nullable=False)
    tools_enabled: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    tool_parameters: Mapped[dict] = mapped_column(EncryptedJSON, nullable=False)
    agent_parameters: Mapped[dict] = mapped_column(EncryptedJSON, nullable=False)

    # Approval status
    status: Mapped[AgentConfigStatus] = mapped_column(
        SAEnum(AgentConfigStatus, name="agent_config_status"),
        default=AgentConfigStatus.draft,
        nullable=False,
    )

    submitted_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    approved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    approval_feedback: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    # Reason for approval/rejection

    # Activation tracking
    activated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # When this version became the active configuration

    # Change reason/description
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Why was this version created? "Updated instructions for clarity", etc.

    # Relationships
    config = relationship("AgentConfig", back_populates="versions")

    __table_args__ = (
        Index("ix_agent_config_versions_config_id", config_id),
        Index("ix_agent_config_versions_status", status),
        Index("ix_agent_config_versions_created_at", "created_at"),
        Index("ix_agent_config_versions_config_version", config_id, version_number),
    )

    def __repr__(self) -> str:
        return f"AgentConfigVersion(config={self.config_id}, v{self.version_number})"


class AgentConfigAudit(Base, TimestampMixin):
    """Audit trail for agent configuration changes.

    Records who changed what, when, why, and what the change was.
    Used for compliance, debugging, and understanding configuration drift.
    """
    __tablename__ = "agent_config_audits"

    id: Mapped[uuid.UUID] = uuid_pk()

    # Reference to config and version
    config_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agent_configs.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agent_config_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    # version_id is None for non-version-creating actions (e.g., approve)

    # Action
    action: Mapped[AgentConfigAuditAction] = mapped_column(
        SAEnum(AgentConfigAuditAction, name="agent_config_audit_action"),
        nullable=False,
    )

    # Who did it
    actor_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # recruiter, admin, etc.

    # What changed (for modified action)
    changes: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    # Format: {
    #   "instructions": {"before": "...", "after": "..."},
    #   "tools_enabled": {"before": [...], "after": [...]},
    #   ...
    # }

    # Why (context)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # User-provided reason for change: "Updated for clarity", "Feedback from team", etc.

    # Context (for debugging)
    metadata: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )  # Additional context: IP address, user agent, etc.

    # Relationships
    config = relationship("AgentConfig", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_agent_config_audits_config_id", config_id),
        Index("ix_agent_config_audits_actor_id", actor_id),
        Index("ix_agent_config_audits_action", action),
        Index("ix_agent_config_audits_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"AgentConfigAudit(config={self.config_id}, action={self.action})"


__all__ = [
    "AgentConfig",
    "AgentConfigVersion",
    "AgentConfigAudit",
    "AgentConfigStatus",
    "AgentConfigAuditAction",
]
