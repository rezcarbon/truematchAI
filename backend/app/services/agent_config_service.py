"""Service layer for agent configuration management.

Handles all business logic for:
- Creating and modifying agent configurations
- Versioning and rollback
- Approval workflows
- Audit trail logging
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    AgentConfig,
    AgentConfigVersion,
    AgentConfigAudit,
    AgentConfigStatus,
    AgentConfigAuditAction,
    User,
)


class AgentConfigService:
    """Service for managing agent configurations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_config(
        self, company_id: uuid.UUID, agent_type: str
    ) -> Optional[AgentConfig]:
        """Get the currently active configuration for an agent."""
        stmt = select(AgentConfig).where(
            and_(
                AgentConfig.company_id == company_id,
                AgentConfig.agent_type == agent_type,
                AgentConfig.status == AgentConfigStatus.active,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_config_by_id(self, config_id: uuid.UUID) -> Optional[AgentConfig]:
        """Get a configuration by ID."""
        stmt = select(AgentConfig).where(AgentConfig.id == config_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_configs_for_company(
        self, company_id: uuid.UUID, agent_type: Optional[str] = None
    ) -> list[AgentConfig]:
        """List all configurations for a company, optionally filtered by agent type."""
        stmt = select(AgentConfig).where(AgentConfig.company_id == company_id)
        if agent_type:
            stmt = stmt.where(AgentConfig.agent_type == agent_type)
        stmt = stmt.order_by(AgentConfig.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def list_versions_for_config(self, config_id: uuid.UUID) -> list[AgentConfigVersion]:
        """List all versions for a configuration."""
        stmt = (
            select(AgentConfigVersion)
            .where(AgentConfigVersion.config_id == config_id)
            .order_by(AgentConfigVersion.version_number.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_version_by_number(
        self, config_id: uuid.UUID, version_number: int
    ) -> Optional[AgentConfigVersion]:
        """Get a specific version by number."""
        stmt = select(AgentConfigVersion).where(
            and_(
                AgentConfigVersion.config_id == config_id,
                AgentConfigVersion.version_number == version_number,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_config(
        self,
        company_id: uuid.UUID,
        agent_type: str,
        role: str,
        name: str,
        instructions: str,
        tools_enabled: list[str],
        tool_parameters: dict,
        agent_parameters: dict,
        created_by_id: uuid.UUID,
        description: Optional[str] = None,
    ) -> AgentConfig:
        """Create a new agent configuration in DRAFT status."""
        config = AgentConfig(
            id=uuid.uuid4(),
            company_id=company_id,
            agent_type=agent_type,
            role=role,
            name=name,
            instructions=instructions,
            tools_enabled=tools_enabled,
            tool_parameters=tool_parameters,
            agent_parameters=agent_parameters,
            created_by_id=created_by_id,
            description=description,
            status=AgentConfigStatus.draft,
            version_number=1,
        )
        self.db.add(config)
        await self.db.flush()

        # Create initial version
        version = AgentConfigVersion(
            id=uuid.uuid4(),
            config_id=config.id,
            version_number=1,
            instructions=instructions,
            tools_enabled=tools_enabled,
            tool_parameters=tool_parameters,
            agent_parameters=agent_parameters,
            status=AgentConfigStatus.draft,
            change_reason="Initial version",
        )
        config.latest_version_id = version.id
        self.db.add(version)
        await self.db.flush()

        # Audit log
        await self._audit(
            config.id,
            version.id,
            AgentConfigAuditAction.created,
            created_by_id,
            reason="Created new configuration",
        )

        return config

    async def update_config(
        self,
        config_id: uuid.UUID,
        instructions: Optional[str] = None,
        tools_enabled: Optional[list[str]] = None,
        tool_parameters: Optional[dict] = None,
        agent_parameters: Optional[dict] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        updated_by_id: Optional[uuid.UUID] = None,
        change_reason: Optional[str] = None,
    ) -> AgentConfigVersion:
        """Update a configuration and create a new version.

        Only works if config is in DRAFT status.
        """
        config = await self.get_config_by_id(config_id)
        if not config:
            raise ValueError(f"Config {config_id} not found")

        if config.status != AgentConfigStatus.draft:
            raise ValueError(f"Can only update configs in DRAFT status, current: {config.status}")

        # Build changes dict for audit
        changes = {}
        if instructions is not None:
            changes["instructions"] = {"before": config.instructions, "after": instructions}
            config.instructions = instructions
        if tools_enabled is not None:
            changes["tools_enabled"] = {"before": config.tools_enabled, "after": tools_enabled}
            config.tools_enabled = tools_enabled
        if tool_parameters is not None:
            changes["tool_parameters"] = {"before": config.tool_parameters, "after": tool_parameters}
            config.tool_parameters = tool_parameters
        if agent_parameters is not None:
            changes["agent_parameters"] = {
                "before": config.agent_parameters,
                "after": agent_parameters,
            }
            config.agent_parameters = agent_parameters
        if name is not None:
            changes["name"] = {"before": config.name, "after": name}
            config.name = name
        if description is not None:
            changes["description"] = {"before": config.description, "after": description}
            config.description = description

        await self.db.flush()

        # Create new version
        new_version_number = config.version_number + 1
        version = AgentConfigVersion(
            id=uuid.uuid4(),
            config_id=config.id,
            version_number=new_version_number,
            instructions=config.instructions,
            tools_enabled=config.tools_enabled,
            tool_parameters=config.tool_parameters,
            agent_parameters=config.agent_parameters,
            status=AgentConfigStatus.draft,
            change_reason=change_reason or "Configuration updated",
        )
        config.latest_version_id = version.id
        config.version_number = new_version_number
        self.db.add(version)
        await self.db.flush()

        # Audit log
        await self._audit(
            config.id,
            version.id,
            AgentConfigAuditAction.modified,
            updated_by_id,
            changes=changes,
            reason=change_reason,
        )

        return version

    async def submit_for_approval(
        self, config_id: uuid.UUID, submitted_by_id: uuid.UUID
    ) -> AgentConfigVersion:
        """Submit a configuration for admin approval."""
        config = await self.get_config_by_id(config_id)
        if not config:
            raise ValueError(f"Config {config_id} not found")

        if config.status != AgentConfigStatus.draft:
            raise ValueError(f"Can only submit DRAFT configs, current: {config.status}")

        config.status = AgentConfigStatus.pending_approval
        latest_version = await self.get_version_by_number(config_id, config.version_number)
        if latest_version:
            latest_version.status = AgentConfigStatus.pending_approval
            latest_version.submitted_by_id = submitted_by_id
            latest_version.submitted_at = datetime.utcnow()

        await self.db.flush()

        # Audit log
        await self._audit(
            config_id,
            latest_version.id if latest_version else None,
            AgentConfigAuditAction.submitted,
            submitted_by_id,
            reason="Submitted for approval",
        )

        return latest_version

    async def approve_config(
        self,
        config_id: uuid.UUID,
        approved_by_id: uuid.UUID,
        approval_feedback: Optional[str] = None,
    ) -> AgentConfig:
        """Admin approves a configuration."""
        config = await self.get_config_by_id(config_id)
        if not config:
            raise ValueError(f"Config {config_id} not found")

        if config.status != AgentConfigStatus.pending_approval:
            raise ValueError(
                f"Can only approve PENDING_APPROVAL configs, current: {config.status}"
            )

        config.status = AgentConfigStatus.approved
        config.approved_by_id = approved_by_id
        config.approved_at = datetime.utcnow()

        latest_version = await self.get_version_by_number(config_id, config.version_number)
        if latest_version:
            latest_version.status = AgentConfigStatus.approved
            latest_version.approved_by_id = approved_by_id
            latest_version.approved_at = datetime.utcnow()
            latest_version.approval_feedback = approval_feedback

        await self.db.flush()

        # Audit log
        await self._audit(
            config_id,
            latest_version.id if latest_version else None,
            AgentConfigAuditAction.approved,
            approved_by_id,
            reason=approval_feedback,
        )

        return config

    async def reject_config(
        self,
        config_id: uuid.UUID,
        rejected_by_id: uuid.UUID,
        rejection_reason: str,
    ) -> AgentConfig:
        """Admin rejects a configuration."""
        config = await self.get_config_by_id(config_id)
        if not config:
            raise ValueError(f"Config {config_id} not found")

        if config.status != AgentConfigStatus.pending_approval:
            raise ValueError(
                f"Can only reject PENDING_APPROVAL configs, current: {config.status}"
            )

        config.status = AgentConfigStatus.draft

        latest_version = await self.get_version_by_number(config_id, config.version_number)
        if latest_version:
            latest_version.status = AgentConfigStatus.draft
            latest_version.approval_feedback = rejection_reason

        await self.db.flush()

        # Audit log
        await self._audit(
            config_id,
            latest_version.id if latest_version else None,
            AgentConfigAuditAction.rejected,
            rejected_by_id,
            reason=rejection_reason,
        )

        return config

    async def activate_config(
        self, config_id: uuid.UUID, activated_by_id: uuid.UUID
    ) -> AgentConfig:
        """Activate a configuration (deactivate others in workspace/role)."""
        config = await self.get_config_by_id(config_id)
        if not config:
            raise ValueError(f"Config {config_id} not found")

        if config.status != AgentConfigStatus.approved:
            raise ValueError(f"Can only activate APPROVED configs, current: {config.status}")

        # Deactivate other active configs for this company/role
        stmt = select(AgentConfig).where(
            and_(
                AgentConfig.company_id == config.company_id,
                AgentConfig.agent_type == config.agent_type,
                AgentConfig.status == AgentConfigStatus.active,
                AgentConfig.id != config.id,
            )
        )
        result = await self.db.execute(stmt)
        other_configs = result.scalars().all()
        for other_config in other_configs:
            other_config.status = AgentConfigStatus.deprecated
            other_config.is_default = False

        # Activate this config
        config.status = AgentConfigStatus.active
        config.is_default = True

        latest_version = await self.get_version_by_number(config_id, config.version_number)
        if latest_version:
            latest_version.status = AgentConfigStatus.active
            latest_version.activated_at = datetime.utcnow()

        await self.db.flush()

        # Audit log
        await self._audit(
            config_id,
            latest_version.id if latest_version else None,
            AgentConfigAuditAction.activated,
            activated_by_id,
            reason="Activated as current configuration",
        )

        return config

    async def get_audit_logs(
        self, config_id: uuid.UUID, limit: int = 100
    ) -> list[AgentConfigAudit]:
        """Get audit logs for a configuration."""
        stmt = (
            select(AgentConfigAudit)
            .where(AgentConfigAudit.config_id == config_id)
            .order_by(AgentConfigAudit.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _audit(
        self,
        config_id: uuid.UUID,
        version_id: Optional[uuid.UUID],
        action: AgentConfigAuditAction,
        actor_id: Optional[uuid.UUID],
        changes: Optional[dict] = None,
        reason: Optional[str] = None,
    ) -> AgentConfigAudit:
        """Create an audit log entry."""
        # Get actor role if available
        actor_role = None
        if actor_id:
            stmt = select(User).where(User.id == actor_id)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                actor_role = user.role.value if hasattr(user.role, "value") else str(user.role)

        audit = AgentConfigAudit(
            id=uuid.uuid4(),
            config_id=config_id,
            version_id=version_id,
            action=action,
            actor_id=actor_id,
            actor_role=actor_role,
            changes=changes or {},
            reason=reason,
            metadata={},
        )
        self.db.add(audit)
        await self.db.flush()
        return audit


__all__ = ["AgentConfigService"]
