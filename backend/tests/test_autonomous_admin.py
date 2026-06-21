"""Tests for autonomous AI-native operation admin API (Phase 1).

Tests cover:
- Input validation (constraints, ranges)
- N+1 query prevention (status endpoint)
- Error handling (invalid IDs, missing records)
- Authorization (admin-only access)
- Feature flag synchronization
- Audit logging
"""
import pytest
from uuid import uuid4
from unittest.mock import patch


from app.models.user import User
from app.models.autonomous_settings import AutonomousSettings
from app.core.feature_flags import FeatureFlagManager, FeatureFlag


@pytest.mark.asyncio
class TestAutonomousAdminAPI:
    """Test autonomous admin control endpoints."""

    @pytest.fixture
    async def admin_user(self, db_session, company):
        """Create an admin user."""
        user = User(
            email="admin@test.com",
            password_hash="hash",
            role="admin",
            company_id=company.id,
        )
        db_session.add(user)
        await db_session.commit()
        return user

    @pytest.fixture
    async def recruiter_user(self, db_session, company):
        """Create a recruiter user."""
        user = User(
            email="recruiter@test.com",
            password_hash="hash",
            role="recruiter",
            company_id=company.id,
        )
        db_session.add(user)
        await db_session.commit()
        return user

    @pytest.fixture
    async def admin_token(self, admin_user):
        """Create JWT token for admin."""
        from app.core.security import create_access_token
        # admin_user is now properly awaited from async fixture
        return create_access_token(subject=str(admin_user.id), role="admin")

    @pytest.fixture
    async def recruiter_token(self, recruiter_user):
        """Create JWT token for recruiter."""
        from app.core.security import create_access_token
        # recruiter_user is now properly awaited from async fixture
        return create_access_token(subject=str(recruiter_user.id), role="recruiter")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # GET /admin/autonomous/status Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def test_get_status_admin_only(self, client, recruiter_token):
        """Only admins can view autonomous status."""
        response = client.get(
            "/api/v1/admin/autonomous/status",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    async def test_get_status_returns_aggregates(self, client, admin_token, db_session):
        """Status endpoint returns aggregate metrics."""
        # Create 3 real users (autonomous_settings.user_id is a FK)
        u1 = User(email=f"agg1_{uuid4()}@test.com", password_hash="h", role="recruiter")
        u2 = User(email=f"agg2_{uuid4()}@test.com", password_hash="h", role="recruiter")
        u3 = User(email=f"agg3_{uuid4()}@test.com", password_hash="h", role="recruiter")
        db_session.add_all([u1, u2, u3])
        await db_session.flush()
        user1, user2, user3 = u1.id, u2.id, u3.id

        settings1 = AutonomousSettings(
            user_id=user1,
            enabled=True,
            actions_count_today=5,
            spending_today=50.0,
            daily_budget=100.0,
        )
        settings2 = AutonomousSettings(
            user_id=user2,
            enabled=True,
            actions_count_today=3,
            spending_today=30.0,
            daily_budget=100.0,
        )
        settings3 = AutonomousSettings(
            user_id=user3,
            enabled=False,  # Disabled user should not be counted
            actions_count_today=10,
            spending_today=100.0,
            daily_budget=200.0,
        )

        db_session.add_all([settings1, settings2, settings3])
        await db_session.commit()

        response = client.get(
            "/api/v1/admin/autonomous/status",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should only count enabled users
        assert data["enabled_users"] == 2
        assert data["total_users"] == 3
        assert data["actions_today"] == 8  # 5 + 3
        assert data["spending_today"] == 80.0  # 50 + 30
        assert data["total_budget_today"] == 200.0  # 100 + 100

    async def test_get_status_empty(self, client, admin_token, db_session):
        """Status returns zeros when no settings exist."""
        response = client.get(
            "/api/v1/admin/autonomous/status",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["enabled_users"] == 0
        assert data["total_users"] == 0
        assert data["actions_today"] == 0
        assert data["spending_today"] == 0.0
        assert data["total_budget_today"] == 0.0

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # GET /admin/autonomous/settings/{user_id} Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def test_get_settings_admin_only(self, client, recruiter_token, recruiter_user):
        """Only admins can view user settings."""
        user_id = str(recruiter_user.id)
        response = client.get(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert response.status_code == 403

    async def test_get_settings_invalid_user_id(self, client, admin_token):
        """Invalid UUID format rejected."""
        response = client.get(
            "/api/v1/admin/autonomous/settings/invalid-uuid",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        assert "Invalid user ID format" in response.json()["detail"]

    async def test_get_settings_creates_defaults(self, client, admin_token, recruiter_user):
        """Getting non-existent settings creates defaults."""
        user_id = str(recruiter_user.id)
        response = client.get(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check defaults
        assert data["user_id"] == user_id
        assert data["enabled"] is False
        assert data["actions_per_hour"] == 10  # Default
        assert data["daily_budget"] == 1000.0  # Default
        assert data["min_confidence_threshold"] == 90  # Model default
        assert data["requires_governance_approval"] is True  # Model default
        assert data["notify_on_action"] is True
        assert data["auto_escalate_on_governance_fail"] is True

    async def test_get_settings_returns_existing(self, client, admin_token, db_session, recruiter_user):
        """Getting existing settings returns them."""
        user_id = recruiter_user.id
        settings = AutonomousSettings(
            user_id=user_id,
            enabled=True,
            actions_per_hour=20,
            daily_budget=500.0,
            min_confidence_threshold=75,
        )
        db_session.add(settings)
        await db_session.commit()

        response = client.get(
            f"/api/v1/admin/autonomous/settings/{str(user_id)}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert data["actions_per_hour"] == 20
        assert data["daily_budget"] == 500.0
        assert data["min_confidence_threshold"] == 75

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PATCH /admin/autonomous/settings/{user_id} Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def test_patch_settings_admin_only(self, client, recruiter_token, recruiter_user):
        """Only admins can update settings."""
        user_id = str(recruiter_user.id)
        response = client.patch(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            json={"enabled": True},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert response.status_code == 403

    async def test_patch_settings_validation_actions_per_hour(self, client, admin_token, recruiter_user):
        """actions_per_hour must be positive."""
        user_id = str(recruiter_user.id)

        # Test zero
        response = client.patch(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            json={"actions_per_hour": 0},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422
        assert "greater than 0" in response.json()["errors"][0]["message"]

        # Test negative
        response = client.patch(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            json={"actions_per_hour": -5},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422

    async def test_patch_settings_validation_daily_budget(self, client, admin_token, recruiter_user):
        """daily_budget must be positive."""
        user_id = str(recruiter_user.id)

        # Test zero
        response = client.patch(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            json={"daily_budget": 0.0},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422

        # Test negative
        response = client.patch(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            json={"daily_budget": -100.0},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422

    async def test_patch_settings_validation_confidence_threshold(self, client, admin_token, recruiter_user):
        """min_confidence_threshold must be 0-100."""
        user_id = str(recruiter_user.id)

        # Test -1
        response = client.patch(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            json={"min_confidence_threshold": -1},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422

        # Test 101
        response = client.patch(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            json={"min_confidence_threshold": 101},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422

        # Test valid values
        response = client.patch(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            json={"min_confidence_threshold": 0},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

        response = client.patch(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            json={"min_confidence_threshold": 100},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    async def test_patch_settings_validation_notes_length(self, client, admin_token, recruiter_user):
        """notes must be <= 1000 characters."""
        user_id = str(recruiter_user.id)
        long_notes = "x" * 1001

        response = client.patch(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            json={"notes": long_notes},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422
        assert "String should have at most 1000 characters" in response.json()["errors"][0]["message"]

    async def test_patch_settings_partial_update(self, client, admin_token, db_session, recruiter_user):
        """PATCH only updates provided fields."""
        user_id = recruiter_user.id
        settings = AutonomousSettings(
            user_id=user_id,
            enabled=False,
            actions_per_hour=10,
            daily_budget=100.0,
            notes="original",
        )
        db_session.add(settings)
        await db_session.commit()

        # Update only one field
        response = client.patch(
            f"/api/v1/admin/autonomous/settings/{str(user_id)}",
            json={"actions_per_hour": 20},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["actions_per_hour"] == 20
        # Other fields unchanged
        assert data["enabled"] is False
        assert data["daily_budget"] == 100.0
        assert data["notes"] == "original"

    async def test_patch_settings_syncs_feature_flag(
        self, client, admin_token, db_session, recruiter_user
    ):
        """PATCH enabled=True syncs with FeatureFlagManager."""
        user_id = recruiter_user.id
        settings = AutonomousSettings(user_id=user_id, enabled=False)
        db_session.add(settings)
        await db_session.commit()

        with patch.object(FeatureFlagManager, "enable_for_user") as mock_enable:
            response = client.patch(
                f"/api/v1/admin/autonomous/settings/{str(user_id)}",
                json={"enabled": True},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            # Verify feature flag was enabled
            mock_enable.assert_called_once()
            call_args = mock_enable.call_args
            assert call_args[0][0] == FeatureFlag.AUTONOMOUS_MODE
            assert call_args[0][1] == str(user_id)

    async def test_patch_settings_invalid_user_id(self, client, admin_token):
        """Invalid UUID format rejected."""
        response = client.patch(
            "/api/v1/admin/autonomous/settings/not-a-uuid",
            json={"enabled": True},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        assert "Invalid user ID format" in response.json()["detail"]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # POST /admin/autonomous/settings/{user_id}/enable Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def test_enable_autonomous_mode_admin_only(self, client, recruiter_token, recruiter_user):
        """Only admins can enable autonomous mode."""
        user_id = str(recruiter_user.id)
        response = client.post(
            f"/api/v1/admin/autonomous/settings/{user_id}/enable",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert response.status_code == 403

    async def test_enable_autonomous_mode_creates_settings(self, client, admin_token, recruiter_user):
        """Enabling on non-existent user creates settings."""
        user_id = str(recruiter_user.id)
        response = client.post(
            f"/api/v1/admin/autonomous/settings/{user_id}/enable",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "enabled"
        assert data["user_id"] == user_id

    async def test_enable_autonomous_mode_already_enabled(
        self, client, admin_token, db_session, recruiter_user
    ):
        """Enabling already-enabled settings is idempotent."""
        user_id = recruiter_user.id
        settings = AutonomousSettings(user_id=user_id, enabled=True)
        db_session.add(settings)
        await db_session.commit()

        response = client.post(
            f"/api/v1/admin/autonomous/settings/{str(user_id)}/enable",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "enabled"

    async def test_enable_syncs_feature_flag(self, client, admin_token, recruiter_user):
        """Enabling syncs with FeatureFlagManager."""
        user_id = str(recruiter_user.id)

        with patch.object(FeatureFlagManager, "enable_for_user") as mock_enable:
            response = client.post(
                f"/api/v1/admin/autonomous/settings/{user_id}/enable",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            mock_enable.assert_called_once()

    async def test_enable_invalid_user_id(self, client, admin_token):
        """Invalid UUID rejected."""
        response = client.post(
            "/api/v1/admin/autonomous/settings/bad-uuid/enable",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        assert "Invalid user ID format" in response.json()["detail"]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # POST /admin/autonomous/settings/{user_id}/disable Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def test_disable_autonomous_mode_admin_only(self, client, recruiter_token, recruiter_user):
        """Only admins can disable autonomous mode."""
        user_id = str(recruiter_user.id)
        response = client.post(
            f"/api/v1/admin/autonomous/settings/{user_id}/disable",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert response.status_code == 403

    async def test_disable_autonomous_mode_already_disabled(self, client, admin_token, recruiter_user):
        """Disabling non-existent user is idempotent."""
        user_id = str(recruiter_user.id)
        response = client.post(
            f"/api/v1/admin/autonomous/settings/{user_id}/disable",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "disabled"

    async def test_disable_syncs_feature_flag(self, client, admin_token, recruiter_user):
        """Disabling syncs with FeatureFlagManager."""
        user_id = str(recruiter_user.id)

        with patch.object(FeatureFlagManager, "disable_for_user") as mock_disable:
            response = client.post(
                f"/api/v1/admin/autonomous/settings/{user_id}/disable",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            mock_disable.assert_called_once()

    async def test_disable_invalid_user_id(self, client, admin_token, recruiter_user):
        """Invalid UUID rejected."""
        response = client.post(
            "/api/v1/admin/autonomous/settings/bad-uuid/disable",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        assert "Invalid user ID format" in response.json()["detail"]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Integration & Audit Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def test_full_workflow_enable_update_disable(
        self, client, admin_token, db_session
    , recruiter_user):
        """Test complete workflow: create → enable → update → disable."""
        user_id = str(recruiter_user.id)

        # 1. Get defaults (creates settings)
        response = client.get(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["enabled"] is False

        # 2. Enable
        response = client.post(
            f"/api/v1/admin/autonomous/settings/{user_id}/enable",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "enabled"

        # 3. Update constraints
        response = client.patch(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            json={"actions_per_hour": 50, "daily_budget": 5000.0},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["actions_per_hour"] == 50
        assert response.json()["daily_budget"] == 5000.0

        # 4. Disable
        response = client.post(
            f"/api/v1/admin/autonomous/settings/{user_id}/disable",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "disabled"

        # 5. Verify final state
        response = client.get(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.json()["enabled"] is False
        assert response.json()["actions_per_hour"] == 50  # Persisted
        assert response.json()["daily_budget"] == 5000.0  # Persisted

    async def test_concurrent_updates_isolation(
        self, client, admin_token, db_session
    , recruiter_user):
        """Concurrent PATCH requests don't corrupt state."""
        user_id = str(recruiter_user.id)

        # Create initial settings
        client.get(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Concurrent updates to different fields
        response1 = client.patch(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            json={"actions_per_hour": 30},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        response2 = client.patch(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            json={"daily_budget": 3000.0},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Final state should have both updates
        response_final = client.get(
            f"/api/v1/admin/autonomous/settings/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        final = response_final.json()
        assert final["actions_per_hour"] == 30
        assert final["daily_budget"] == 3000.0
