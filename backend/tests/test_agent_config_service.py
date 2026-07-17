"""Unit tests for agent configuration service."""
import pytest
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentConfig, AgentConfigVersion, AgentConfigAudit, User, UserRole
from app.services.agent_config_service import AgentConfigService
from app.models.agent_config import AgentConfigStatus


@pytest.mark.asyncio
class TestAgentConfigService:
    """Test AgentConfigService CRUD operations."""

    async def test_create_config_starts_in_draft(self, db_session: AsyncSession):
        """New configs start in DRAFT status."""
        service = AgentConfigService(db_session)

        config = await service.create_config(
            company_id=uuid4(),
            agent_type="recruiter",
            role="recruiter",
            name="Test Recruiter Agent",
            instructions="You are a helpful recruiter agent.",
            tools_enabled=["analyze", "rank"],
            tool_parameters={"analyze": {"max_length": 5000}},
            agent_parameters={"temperature": 0.7},
            created_by_id=uuid4(),
        )

        assert config.status == AgentConfigStatus.draft
        assert config.version_number == 1
        assert config.name == "Test Recruiter Agent"

    async def test_update_config_increments_version(self, db_session: AsyncSession):
        """Updating config creates new version with incremented number."""
        service = AgentConfigService(db_session)

        config = await service.create_config(
            company_id=uuid4(),
            agent_type="recruiter",
            role="recruiter",
            name="Test Config",
            instructions="Original instructions.",
            tools_enabled=["analyze"],
            tool_parameters={},
            agent_parameters={},
            created_by_id=uuid4(),
        )

        version = await service.update_config(
            config_id=config.id,
            instructions="Updated instructions.",
            updated_by_id=uuid4(),
            change_reason="Clarity improvement",
        )

        assert version.version_number == 2
        assert config.version_number == 2
        assert version.instructions == "Updated instructions."

    async def test_submit_for_approval_changes_status(self, db_session: AsyncSession):
        """Submitting config moves it to PENDING_APPROVAL status."""
        service = AgentConfigService(db_session)

        config = await service.create_config(
            company_id=uuid4(),
            agent_type="recruiter",
            role="recruiter",
            name="Test Config",
            instructions="Test",
            tools_enabled=[],
            tool_parameters={},
            agent_parameters={},
            created_by_id=uuid4(),
        )

        await service.submit_for_approval(config.id, uuid4())

        updated_config = await service.get_config_by_id(config.id)
        assert updated_config.status == AgentConfigStatus.pending_approval

    async def test_approve_config_requires_pending_status(self, db_session: AsyncSession):
        """Can only approve configs in PENDING_APPROVAL status."""
        service = AgentConfigService(db_session)

        config = await service.create_config(
            company_id=uuid4(),
            agent_type="recruiter",
            role="recruiter",
            name="Test Config",
            instructions="Test",
            tools_enabled=[],
            tool_parameters={},
            agent_parameters={},
            created_by_id=uuid4(),
        )

        with pytest.raises(ValueError, match="Can only approve PENDING_APPROVAL"):
            await service.approve_config(config.id, uuid4())

    async def test_activate_config_deactivates_others(self, db_session: AsyncSession):
        """Activating config deactivates other active configs for same role."""
        service = AgentConfigService(db_session)

        company_id = uuid4()

        # Create and activate first config
        config1 = await service.create_config(
            company_id=company_id,
            agent_type="recruiter",
            role="recruiter",
            name="Config 1",
            instructions="Test 1",
            tools_enabled=[],
            tool_parameters={},
            agent_parameters={},
            created_by_id=uuid4(),
        )
        await service.submit_for_approval(config1.id, uuid4())
        await service.approve_config(config1.id, uuid4())
        await service.activate_config(config1.id, uuid4())

        # Create and activate second config
        config2 = await service.create_config(
            company_id=company_id,
            agent_type="recruiter",
            role="recruiter",
            name="Config 2",
            instructions="Test 2",
            tools_enabled=[],
            tool_parameters={},
            agent_parameters={},
            created_by_id=uuid4(),
        )
        await service.submit_for_approval(config2.id, uuid4())
        await service.approve_config(config2.id, uuid4())
        await service.activate_config(config2.id, uuid4())

        # Verify config1 is now deprecated
        config1_updated = await service.get_config_by_id(config1.id)
        assert config1_updated.status == AgentConfigStatus.deprecated
        assert config1_updated.is_default is False

    async def test_get_active_config_returns_active_only(self, db_session: AsyncSession):
        """get_active_config returns only ACTIVE config."""
        service = AgentConfigService(db_session)

        company_id = uuid4()

        config = await service.create_config(
            company_id=company_id,
            agent_type="recruiter",
            role="recruiter",
            name="Test Config",
            instructions="Test",
            tools_enabled=[],
            tool_parameters={},
            agent_parameters={},
            created_by_id=uuid4(),
        )

        # Not active yet, should return None
        active = await service.get_active_config(company_id, "recruiter")
        assert active is None

        # Activate it
        await service.submit_for_approval(config.id, uuid4())
        await service.approve_config(config.id, uuid4())
        await service.activate_config(config.id, uuid4())

        # Now should return it
        active = await service.get_active_config(company_id, "recruiter")
        assert active is not None
        assert active.id == config.id

    async def test_list_versions_returns_in_descending_order(self, db_session: AsyncSession):
        """list_versions returns versions in descending version_number order."""
        service = AgentConfigService(db_session)

        config = await service.create_config(
            company_id=uuid4(),
            agent_type="recruiter",
            role="recruiter",
            name="Test Config",
            instructions="V1",
            tools_enabled=[],
            tool_parameters={},
            agent_parameters={},
            created_by_id=uuid4(),
        )

        # Create version 2
        await service.update_config(
            config.id,
            instructions="V2",
            updated_by_id=uuid4(),
        )

        # Create version 3
        await service.update_config(
            config.id,
            instructions="V3",
            updated_by_id=uuid4(),
        )

        versions = await service.list_versions_for_config(config.id)
        assert len(versions) == 3
        assert versions[0].version_number == 3
        assert versions[1].version_number == 2
        assert versions[2].version_number == 1

    async def test_audit_logs_all_actions(self, db_session: AsyncSession):
        """Audit logs record all configuration actions."""
        service = AgentConfigService(db_session)

        config = await service.create_config(
            company_id=uuid4(),
            agent_type="recruiter",
            role="recruiter",
            name="Test Config",
            instructions="Test",
            tools_enabled=[],
            tool_parameters={},
            agent_parameters={},
            created_by_id=uuid4(),
        )

        logs = await service.get_audit_logs(config.id)

        # Should have "created" log at minimum
        assert len(logs) >= 1
        assert logs[0].action.value == "created"


__all__ = ["TestAgentConfigService"]
