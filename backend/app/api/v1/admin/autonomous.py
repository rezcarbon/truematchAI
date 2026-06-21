"""Admin API for autonomous AI-native operation control."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, field_validator

from app.deps import get_current_user
from app.database import get_session
from app.models.user import User
from app.models.autonomous_settings import AutonomousSettings
from app.core.feature_flags import FeatureFlagManager, FeatureFlag

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/autonomous", tags=["admin", "autonomous"])


# Request/Response Models
class AutonomousSettingsUpdate(BaseModel):
    """Update autonomous settings for a user.

    All fields are optional. Only provided fields will be updated.
    """

    enabled: bool | None = None
    actions_per_hour: int | None = Field(None, gt=0, description="Must be positive integer")
    daily_budget: float | None = Field(None, gt=0, description="Must be positive float")
    min_confidence_threshold: int | None = Field(None, ge=0, le=100, description="Must be 0-100")
    requires_governance_approval: bool | None = None
    notify_on_action: bool | None = None
    auto_escalate_on_governance_fail: bool | None = None
    notes: str | None = Field(None, max_length=1000, description="Max 1000 characters")

    @field_validator('actions_per_hour')
    @classmethod
    def validate_actions_per_hour(cls, v):
        """Validate actions_per_hour is positive and reasonable."""
        if v is not None and v > 1000:
            raise ValueError("actions_per_hour must be <= 1000")
        return v

    @field_validator('daily_budget')
    @classmethod
    def validate_daily_budget(cls, v):
        """Validate daily_budget is reasonable."""
        if v is not None and v > 1000000:
            raise ValueError("daily_budget must be <= 1,000,000")
        return v


class AutonomousSettingsResponse(BaseModel):
    """Response with autonomous settings."""

    user_id: str
    enabled: bool
    actions_per_hour: int
    daily_budget: float
    min_confidence_threshold: int
    requires_governance_approval: bool
    notify_on_action: bool
    auto_escalate_on_governance_fail: bool
    actions_count_today: int
    spending_today: float
    notes: str | None


class AutonomousStatusResponse(BaseModel):
    """System-wide autonomous status."""

    enabled_users: int
    total_users: int
    actions_today: int
    total_budget_today: float
    spending_today: float


async def _require_admin(
    user: User = Depends(get_current_user),
) -> User:
    """Ensure user is admin."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


@router.get("/status", response_model=AutonomousStatusResponse)
async def get_autonomous_status(
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Get system-wide autonomous operation status.

    Returns counts and aggregates for enabled autonomous users only.
    Optimized with COUNT and SUM queries to avoid N+1 problems.
    """
    try:
        # Get count of enabled users (single COUNT query, not N+1)
        stmt = select(func.count(AutonomousSettings.id)).where(
            AutonomousSettings.enabled.is_(True)
        )
        result = await db.execute(stmt)
        enabled_users = result.scalar() or 0

        # Get total users count (single query)
        stmt = select(func.count(AutonomousSettings.id))
        result = await db.execute(stmt)
        total_users = result.scalar() or 0

        # Get aggregates for enabled users (single SUM query, not N+1)
        stmt = select(
            func.sum(AutonomousSettings.actions_count_today).label("actions_today"),
            func.sum(AutonomousSettings.spending_today).label("spending_today"),
            func.sum(AutonomousSettings.daily_budget).label("total_budget_today"),
        ).where(AutonomousSettings.enabled.is_(True))
        result = await db.execute(stmt)
        row = result.one()

        return {
            "enabled_users": enabled_users,
            "total_users": total_users,
            "actions_today": row.actions_today or 0,
            "total_budget_today": row.total_budget_today or 0.0,
            "spending_today": row.spending_today or 0.0,
        }
    except Exception as e:
        logger.error(f"Failed to get autonomous status: {e}", extra={
            "error_type": type(e).__name__,
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get status",
        )


@router.get("/settings/{user_id}", response_model=AutonomousSettingsResponse)
async def get_autonomous_settings(
    user_id: str,
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Get autonomous settings for a user.

    Creates default settings if none exist.
    Default values:
    - enabled: False
    - actions_per_hour: 10
    - daily_budget: 1000.0
    - min_confidence_threshold: 90
    - requires_governance_approval: True
    - notify_on_action: True
    - auto_escalate_on_governance_fail: True
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        logger.warning(f"Invalid user ID format: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user ID format. Expected UUID, got: {user_id}",
        )

    try:
        stmt = select(AutonomousSettings).where(AutonomousSettings.user_id == user_uuid)
        result = await db.execute(stmt)
        settings = result.scalar_one_or_none()

        if not settings:
            # The user must exist before defaults can be created — otherwise the
            # FK insert blows up as a 500. Return a clean 404 instead.
            target = await db.get(User, user_uuid)
            if target is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {user_id} not found",
                )
            # Create default settings if none exist (defensive)
            settings = AutonomousSettings(user_id=user_uuid)
            db.add(settings)
            await db.commit()
            logger.info(
                "Created default autonomous settings for user",
                extra={"user_id": str(user_uuid)},
            )

        return {
            "user_id": str(settings.user_id),
            "enabled": settings.enabled,
            "actions_per_hour": settings.actions_per_hour,
            "daily_budget": settings.daily_budget,
            "min_confidence_threshold": settings.min_confidence_threshold,
            "requires_governance_approval": settings.requires_governance_approval,
            "notify_on_action": settings.notify_on_action,
            "auto_escalate_on_governance_fail": settings.auto_escalate_on_governance_fail,
            "actions_count_today": settings.actions_count_today,
            "spending_today": settings.spending_today,
            "notes": settings.notes,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get autonomous settings for user {user_id}: {e}",
            extra={"user_id": user_id, "error_type": type(e).__name__},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve settings",
        )


@router.patch("/settings/{user_id}", response_model=AutonomousSettingsResponse)
async def update_autonomous_settings(
    user_id: str,
    updates: AutonomousSettingsUpdate,
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Update autonomous settings for a user.

    PATCH allows partial updates - only provided fields are modified.
    All validation constraints are enforced:
    - actions_per_hour: must be > 0 and <= 1000
    - daily_budget: must be > 0 and <= 1,000,000
    - min_confidence_threshold: must be 0-100
    - notes: max 1000 characters
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        logger.warning(f"Invalid user ID format in PATCH: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user ID format. Expected UUID, got: {user_id}",
        )

    try:
        stmt = select(AutonomousSettings).where(AutonomousSettings.user_id == user_uuid)
        result = await db.execute(stmt)
        settings = result.scalar_one_or_none()

        if not settings:
            # The user must exist before settings can be created (FK) — 404
            # cleanly rather than 500 on the constraint violation.
            target = await db.get(User, user_uuid)
            if target is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {user_id} not found",
                )
            settings = AutonomousSettings(user_id=user_uuid)
            db.add(settings)
            logger.info(
                "Created new autonomous settings during PATCH",
                extra={"user_id": str(user_uuid)},
            )

        # Track what was actually updated for logging
        updated_fields = []

        # Update fields only if provided
        if updates.enabled is not None:
            old_value = settings.enabled
            settings.enabled = updates.enabled
            updated_fields.append(f"enabled: {old_value} → {updates.enabled}")
            # Sync with feature flag manager
            if updates.enabled:
                FeatureFlagManager.enable_for_user(FeatureFlag.AUTONOMOUS_MODE, str(user_uuid))
                logger.warning(
                    "Autonomous mode ENABLED for user",
                    extra={"user_id": str(user_uuid), "admin_id": str(admin.id)},
                )
            else:
                FeatureFlagManager.disable_for_user(FeatureFlag.AUTONOMOUS_MODE, str(user_uuid))
                logger.warning(
                    "Autonomous mode DISABLED for user",
                    extra={"user_id": str(user_uuid), "admin_id": str(admin.id)},
                )

        if updates.actions_per_hour is not None:
            old_value = settings.actions_per_hour
            settings.actions_per_hour = updates.actions_per_hour
            updated_fields.append(f"actions_per_hour: {old_value} → {updates.actions_per_hour}")

        if updates.daily_budget is not None:
            old_value = settings.daily_budget
            settings.daily_budget = updates.daily_budget
            updated_fields.append(f"daily_budget: {old_value} → {updates.daily_budget}")

        if updates.min_confidence_threshold is not None:
            old_value = settings.min_confidence_threshold
            settings.min_confidence_threshold = updates.min_confidence_threshold
            updated_fields.append(
                f"min_confidence_threshold: {old_value} → {updates.min_confidence_threshold}"
            )

        if updates.requires_governance_approval is not None:
            settings.requires_governance_approval = updates.requires_governance_approval
            updated_fields.append(
                f"requires_governance_approval: {updates.requires_governance_approval}"
            )

        if updates.notify_on_action is not None:
            settings.notify_on_action = updates.notify_on_action
            updated_fields.append(f"notify_on_action: {updates.notify_on_action}")

        if updates.auto_escalate_on_governance_fail is not None:
            settings.auto_escalate_on_governance_fail = updates.auto_escalate_on_governance_fail
            updated_fields.append(
                f"auto_escalate_on_governance_fail: {updates.auto_escalate_on_governance_fail}"
            )

        if updates.notes is not None:
            settings.notes = updates.notes
            updated_fields.append("notes updated")

        await db.commit()

        # Only log if something was actually changed
        if updated_fields:
            logger.info(
                "Updated autonomous settings for user",
                extra={
                    "user_id": str(user_uuid),
                    "admin_id": str(admin.id),
                    "updated_fields": updated_fields,
                },
            )
        else:
            logger.debug(
                "PATCH request had no changes",
                extra={"user_id": str(user_uuid)},
            )

        return {
            "user_id": str(settings.user_id),
            "enabled": settings.enabled,
            "actions_per_hour": settings.actions_per_hour,
            "daily_budget": settings.daily_budget,
            "min_confidence_threshold": settings.min_confidence_threshold,
            "requires_governance_approval": settings.requires_governance_approval,
            "notify_on_action": settings.notify_on_action,
            "auto_escalate_on_governance_fail": settings.auto_escalate_on_governance_fail,
            "actions_count_today": settings.actions_count_today,
            "spending_today": settings.spending_today,
            "notes": settings.notes,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to update autonomous settings for user {user_id}: {e}",
            extra={"user_id": user_id, "error_type": type(e).__name__},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update settings",
        )


@router.post("/settings/{user_id}/enable", response_model=dict)
async def enable_autonomous_mode(
    user_id: str,
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Enable autonomous mode for a user.

    Convenience endpoint equivalent to:
    PATCH /admin/autonomous/settings/{user_id} with {"enabled": true}

    This is a critical operation - triggers detailed audit logging.
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        logger.warning(f"Invalid user ID format in enable request: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user ID format. Expected UUID, got: {user_id}",
        )

    try:
        stmt = select(AutonomousSettings).where(AutonomousSettings.user_id == user_uuid)
        result = await db.execute(stmt)
        settings = result.scalar_one_or_none()

        if not settings:
            # The user must exist (FK) — 404 cleanly rather than 500.
            target = await db.get(User, user_uuid)
            if target is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {user_id} not found",
                )
            # Create new settings with autonomous enabled
            settings = AutonomousSettings(user_id=user_uuid, enabled=True)
            db.add(settings)
            logger.info(
                "Created autonomous settings with autonomous mode enabled",
                extra={"user_id": str(user_uuid)},
            )
        elif not settings.enabled:
            # Only log the change if it was actually disabled before
            settings.enabled = True
            logger.debug(
                "Changed autonomous mode from disabled to enabled",
                extra={"user_id": str(user_uuid)},
            )
        else:
            # Already enabled - no change needed
            logger.debug(
                "Autonomous mode already enabled",
                extra={"user_id": str(user_uuid)},
            )

        # Always sync with feature flag manager
        FeatureFlagManager.enable_for_user(FeatureFlag.AUTONOMOUS_MODE, str(user_uuid))
        await db.commit()

        # Critical security event - always log at WARNING level
        logger.warning(
            "Autonomous mode ENABLED for user by admin",
            extra={
                "user_id": str(user_uuid),
                "admin_id": str(admin.id),
                "admin_email": admin.email,
            },
        )

        return {
            "status": "enabled",
            "user_id": str(user_uuid),
            "message": "Autonomous mode is now active for this user",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to enable autonomous mode for user {user_id}: {e}",
            extra={
                "user_id": user_id,
                "admin_id": str(admin.id),
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable autonomous mode",
        )


@router.post("/settings/{user_id}/disable", response_model=dict)
async def disable_autonomous_mode(
    user_id: str,
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Disable autonomous mode for a user.

    Convenience endpoint equivalent to:
    PATCH /admin/autonomous/settings/{user_id} with {"enabled": false}

    This is a critical operation - triggers detailed audit logging.
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        logger.warning(f"Invalid user ID format in disable request: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user ID format. Expected UUID, got: {user_id}",
        )

    try:
        stmt = select(AutonomousSettings).where(AutonomousSettings.user_id == user_uuid)
        result = await db.execute(stmt)
        settings = result.scalar_one_or_none()

        if settings and settings.enabled:
            # Only log the change if it was actually enabled before
            settings.enabled = False
            logger.debug(
                "Changed autonomous mode from enabled to disabled",
                extra={"user_id": str(user_uuid)},
            )
        elif not settings or not settings.enabled:
            # Already disabled - no change needed
            logger.debug(
                "Autonomous mode already disabled",
                extra={"user_id": str(user_uuid)},
            )

        # Always sync with feature flag manager
        FeatureFlagManager.disable_for_user(FeatureFlag.AUTONOMOUS_MODE, str(user_uuid))
        if settings:
            await db.commit()

        # Critical security event - always log at WARNING level
        logger.warning(
            "Autonomous mode DISABLED for user by admin",
            extra={
                "user_id": str(user_uuid),
                "admin_id": str(admin.id),
                "admin_email": admin.email,
            },
        )

        return {
            "status": "disabled",
            "user_id": str(user_uuid),
            "message": "Autonomous mode is now inactive for this user",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to disable autonomous mode for user {user_id}: {e}",
            extra={
                "user_id": user_id,
                "admin_id": str(admin.id),
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable autonomous mode",
        )
