"""Extended endpoints for agent config export, batch operations, and notifications."""
from __future__ import annotations

import uuid
from typing import list

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models import User
from app.services.agent_config_service import AgentConfigService
from app.services.agent_config_export import AgentConfigExportService
from app.services.agent_config_notifications import AgentConfigNotificationService
from app.services.agent_config_governance import AgentConfigGovernance

router = APIRouter(prefix="/agent-configs", tags=["agent_configs_extended"])


# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================


@router.get("/{config_id}/export/pdf")
async def export_config_as_pdf(
    config_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export approval checklist as PDF file.

    Returns PDF as attachment ready for download.
    """
    service = AgentConfigService(db)
    config = await service.get_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    # Only allow config creator, admin, or approvers to export
    if (
        current_user.id != config.created_by_id
        and current_user.role.value != "admin"
    ):
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        export_service = AgentConfigExportService(db)
        pdf_bytes = await export_service.export_to_pdf(str(config_id))

        filename = export_service.generate_filename(config)

        return {
            "status": "success",
            "message": "PDF generated successfully",
            "filename": f"{filename}.pdf",
            "size": len(pdf_bytes),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{config_id}/export/details")
async def export_config_details(
    config_id: uuid.UUID,
    format: str = Query("json", regex="^(json|csv)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export config details in requested format (JSON or CSV).

    Returns structured data for import into other systems.
    """
    service = AgentConfigService(db)
    config = await service.get_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    version = await service.get_version_by_number(config_id, config.version_number)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    if format == "json":
        return {
            "config": {
                "id": str(config.id),
                "name": config.name,
                "agent_type": config.agent_type,
                "role": config.role,
                "version": config.version_number,
                "status": config.status,
                "created_at": config.created_at.isoformat(),
            },
            "version": {
                "instructions": version.instructions,
                "tools_enabled": version.tools_enabled,
                "tool_parameters": version.tool_parameters,
                "agent_parameters": version.agent_parameters,
            },
        }

    # CSV format
    export_service = AgentConfigExportService(db)
    csv_data = await export_service.export_to_csv()
    return {"format": "csv", "data": csv_data}


# ============================================================================
# BATCH OPERATIONS
# ============================================================================


class BatchApprovalRequest:
    """Request for batch approval of multiple configs."""

    config_ids: list[uuid.UUID]
    feedback: str = ""


@router.post("/batch/approve")
async def batch_approve_configs(
    config_ids: list[uuid.UUID],
    feedback: str = "",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Batch approve multiple configurations.

    Only admin can use this endpoint.
    """
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Only admins can batch approve")

    service = AgentConfigService(db)
    governance = AgentConfigGovernance(db)
    notifications = AgentConfigNotificationService(db)

    results = {"approved": [], "failed": []}

    for config_id in config_ids:
        try:
            config = await service.get_config_by_id(config_id)
            if not config:
                results["failed"].append(
                    {"id": str(config_id), "reason": "Configuration not found"}
                )
                continue

            version = await service.get_version_by_number(
                config_id, config.version_number
            )

            # Validate
            validation = await governance.validate_version_before_approval(version)
            if not validation["passed"]:
                results["failed"].append(
                    {
                        "id": str(config_id),
                        "reason": f"Validation failed: {validation['errors']}",
                    }
                )
                continue

            # Approve
            await service.approve_config(config_id, current_user.id, feedback)

            # Notify recruiter
            await notifications.notify_approval(config, current_user, feedback)

            results["approved"].append({"id": str(config_id), "name": config.name})

        except Exception as e:
            results["failed"].append(
                {"id": str(config_id), "reason": str(e)}
            )

    await db.commit()

    # Notify admins of batch operation
    approved_configs = [
        await service.get_config_by_id(cid)
        for cid in config_ids
        if any(a["id"] == str(cid) for a in results["approved"])
    ]
    if approved_configs:
        await notifications.notify_batch_approval(
            [c for c in approved_configs if c],
            current_user,
            len(results["approved"]),
        )

    return {
        "status": "partial_success" if results["failed"] else "success",
        "approved_count": len(results["approved"]),
        "failed_count": len(results["failed"]),
        "results": results,
    }


@router.post("/batch/reject")
async def batch_reject_configs(
    config_ids: list[uuid.UUID],
    feedback: str = "Changes required",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Batch reject multiple configurations."""
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Only admins can batch reject")

    service = AgentConfigService(db)
    notifications = AgentConfigNotificationService(db)

    results = {"rejected": [], "failed": []}

    for config_id in config_ids:
        try:
            config = await service.get_config_by_id(config_id)
            if not config:
                results["failed"].append(
                    {"id": str(config_id), "reason": "Configuration not found"}
                )
                continue

            await service.reject_config(config_id, current_user.id, feedback)

            # Notify recruiter
            await notifications.notify_rejection(config, current_user, feedback)

            results["rejected"].append({"id": str(config_id), "name": config.name})

        except Exception as e:
            results["failed"].append(
                {"id": str(config_id), "reason": str(e)}
            )

    await db.commit()

    return {
        "status": "partial_success" if results["failed"] else "success",
        "rejected_count": len(results["rejected"]),
        "failed_count": len(results["failed"]),
        "results": results,
    }


# ============================================================================
# NOTIFICATION ENDPOINTS
# ============================================================================


@router.post("/{config_id}/send-notification")
async def send_notification_manual(
    config_id: uuid.UUID,
    notification_type: str,
    feedback: str = "",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually send notification for a configuration.

    Useful for resending notifications if email failed.
    """
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Only admins can send notifications")

    service = AgentConfigService(db)
    config = await service.get_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    notifications = AgentConfigNotificationService(db)

    try:
        if notification_type == "submitted":
            success = await notifications.notify_submission(config, current_user)
        elif notification_type == "approved":
            success = await notifications.notify_approval(config, current_user, feedback)
        elif notification_type == "rejected":
            if not feedback:
                raise ValueError("Feedback required for rejection notification")
            success = await notifications.notify_rejection(config, current_user, feedback)
        elif notification_type == "activated":
            success = await notifications.notify_activation(config, current_user)
        else:
            raise ValueError(f"Unknown notification type: {notification_type}")

        return {
            "status": "success" if success else "failed",
            "message": f"Notification sent to {notification_type}",
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


__all__ = ["router"]
