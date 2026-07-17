"""REST API for agent configuration management.

Endpoints for:
- CRUD operations on agent configurations
- Approval workflow (submit, approve, reject, activate)
- Version history and rollback
- Audit trail queries
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models import User, AgentConfigStatus, AgentConfigAuditAction
from app.services.agent_config_service import AgentConfigService
from app.services.agent_config_governance import AgentConfigGovernance

router = APIRouter(prefix="/agent-configs", tags=["agent_configs"])


# Schemas
class AgentConfigCreateRequest(BaseModel):
    """Request to create a new agent configuration."""

    company_id: uuid.UUID = Field(..., description="Company ID")
    agent_type: str = Field(..., description="Type of agent (recruiter, candidate, admin)")
    role: str = Field(..., description="User role this config applies to")
    name: str = Field(..., description="Human-readable name")
    instructions: str = Field(..., description="System prompt for the agent")
    tools_enabled: list[str] = Field(default=[], description="Available tools")
    tool_parameters: dict = Field(default={}, description="Per-tool settings")
    agent_parameters: dict = Field(default={}, description="Agent-wide settings")
    description: Optional[str] = Field(None, description="What this config does")


class AgentConfigUpdateRequest(BaseModel):
    """Request to update an agent configuration."""

    instructions: Optional[str] = Field(None, description="Updated system prompt")
    tools_enabled: Optional[list[str]] = Field(None, description="Updated tools")
    tool_parameters: Optional[dict] = Field(None, description="Updated tool settings")
    agent_parameters: Optional[dict] = Field(None, description="Updated agent settings")
    name: Optional[str] = Field(None, description="Updated name")
    description: Optional[str] = Field(None, description="Updated description")
    change_reason: Optional[str] = Field(None, description="Why this change was made")


class AgentConfigApprovalRequest(BaseModel):
    """Request to approve or reject a configuration."""

    feedback: Optional[str] = Field(None, description="Approval/rejection feedback")


class AgentConfigResponse(BaseModel):
    """Response containing agent configuration."""

    id: uuid.UUID
    company_id: uuid.UUID
    agent_type: str
    role: str
    name: str
    status: str
    version_number: int
    description: Optional[str]
    is_default: bool
    created_at: str
    approved_at: Optional[str]

    class Config:
        from_attributes = True


class AgentConfigVersionResponse(BaseModel):
    """Response containing a specific version of a configuration."""

    id: uuid.UUID
    config_id: uuid.UUID
    version_number: int
    status: str
    instructions: str
    tools_enabled: list[str]
    tool_parameters: dict
    agent_parameters: dict
    change_reason: Optional[str]
    submitted_at: Optional[str]
    approved_at: Optional[str]
    activated_at: Optional[str]

    class Config:
        from_attributes = True


class AgentConfigAuditResponse(BaseModel):
    """Response containing audit log entry."""

    id: uuid.UUID
    action: str
    actor_id: Optional[uuid.UUID]
    actor_role: Optional[str]
    reason: Optional[str]
    changes: dict
    created_at: str

    class Config:
        from_attributes = True


class ValidationCheckItem(BaseModel):
    """Single validation check result."""

    item: str
    status: str  # passed, failed, warning, missing, incomplete
    details: str


class AgentConfigValidationResponse(BaseModel):
    """Response containing governance validation results."""

    config_id: uuid.UUID
    version_number: int
    validation: dict  # safety_passed, fairness_score, warnings, errors
    version_checks: dict  # completeness checks
    approval_items: list[ValidationCheckItem]
    recommendation: str  # approve, review_required


class ApprovalChecklistResponse(BaseModel):
    """Full approval checklist for admins reviewing a config."""

    config_id: str
    version_number: int
    agent_type: str
    role: str
    created_by: str
    submitted_at: Optional[str]
    validation: dict
    version_checks: dict
    approval_items: list[dict]
    recommendation: str


# Routes

@router.post("/", response_model=AgentConfigResponse)
async def create_agent_config(
    req: AgentConfigCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentConfigResponse:
    """Create a new agent configuration in DRAFT status."""
    governance = AgentConfigGovernance(db)

    # Check permissions
    permitted, reason = await governance.check_create_permission(current_user, req.company_id)
    if not permitted:
        raise HTTPException(status_code=403, detail=reason)

    service = AgentConfigService(db)
    config = await service.create_config(
        company_id=req.company_id,
        agent_type=req.agent_type,
        role=req.role,
        name=req.name,
        instructions=req.instructions,
        tools_enabled=req.tools_enabled,
        tool_parameters=req.tool_parameters,
        agent_parameters=req.agent_parameters,
        created_by_id=current_user.id,
        description=req.description,
    )
    await db.commit()
    return AgentConfigResponse.from_orm(config)


@router.get("/{config_id}", response_model=AgentConfigResponse)
async def get_agent_config(
    config_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentConfigResponse:
    """Get a specific agent configuration."""
    service = AgentConfigService(db)
    config = await service.get_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    # TODO: Check user has access to this config
    return AgentConfigResponse.from_orm(config)


@router.put("/{config_id}", response_model=AgentConfigVersionResponse)
async def update_agent_config(
    config_id: uuid.UUID,
    req: AgentConfigUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentConfigVersionResponse:
    """Update an agent configuration (only works if in DRAFT status)."""
    service = AgentConfigService(db)
    governance = AgentConfigGovernance(db)

    config = await service.get_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    # Check permissions
    permitted, reason = await governance.check_update_permission(current_user, config)
    if not permitted:
        raise HTTPException(status_code=403, detail=reason)

    try:
        version = await service.update_config(
            config_id=config_id,
            instructions=req.instructions,
            tools_enabled=req.tools_enabled,
            tool_parameters=req.tool_parameters,
            agent_parameters=req.agent_parameters,
            name=req.name,
            description=req.description,
            updated_by_id=current_user.id,
            change_reason=req.change_reason,
        )
        await db.commit()
        return AgentConfigVersionResponse.from_orm(version)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{config_id}/submit-for-approval")
async def submit_for_approval(
    config_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentConfigResponse:
    """Submit a configuration for admin approval."""
    service = AgentConfigService(db)
    governance = AgentConfigGovernance(db)

    config = await service.get_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    # Check permissions
    permitted, reason = await governance.check_submit_permission(current_user, config)
    if not permitted:
        raise HTTPException(status_code=403, detail=reason)

    try:
        await service.submit_for_approval(config_id, current_user.id)
        await db.commit()
        updated_config = await service.get_config_by_id(config_id)
        return AgentConfigResponse.from_orm(updated_config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{config_id}/approve")
async def approve_config(
    config_id: uuid.UUID,
    req: AgentConfigApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentConfigResponse:
    """Admin approves a configuration."""
    service = AgentConfigService(db)
    governance = AgentConfigGovernance(db)

    # Check permissions
    permitted, reason = await governance.check_approve_permission(current_user)
    if not permitted:
        raise HTTPException(status_code=403, detail=reason)

    config = await service.get_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    # Get version for validation
    version = await service.get_version_by_number(config_id, config.version_number)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    # Run governance validation
    validation = await governance.validate_version_before_approval(version)
    if not validation["passed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Config failed governance validation: {validation['errors']}",
        )

    try:
        config = await service.approve_config(config_id, current_user.id, req.feedback)
        await db.commit()
        return AgentConfigResponse.from_orm(config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{config_id}/reject")
async def reject_config(
    config_id: uuid.UUID,
    req: AgentConfigApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentConfigResponse:
    """Admin rejects a configuration."""
    governance = AgentConfigGovernance(db)

    # Check permissions
    permitted, reason = await governance.check_approve_permission(current_user)
    if not permitted:
        raise HTTPException(status_code=403, detail=reason)

    service = AgentConfigService(db)
    try:
        config = await service.reject_config(
            config_id, current_user.id, req.feedback or "Rejected"
        )
        await db.commit()
        return AgentConfigResponse.from_orm(config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{config_id}/activate")
async def activate_config(
    config_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentConfigResponse:
    """Activate a configuration (deactivate others)."""
    governance = AgentConfigGovernance(db)

    # Check permissions
    permitted, reason = await governance.check_activate_permission(current_user)
    if not permitted:
        raise HTTPException(status_code=403, detail=reason)

    service = AgentConfigService(db)
    try:
        config = await service.activate_config(config_id, current_user.id)
        await db.commit()
        return AgentConfigResponse.from_orm(config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{config_id}/versions", response_model=list[AgentConfigVersionResponse])
async def list_versions(
    config_id: uuid.UUID,
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AgentConfigVersionResponse]:
    """List all versions of a configuration."""
    service = AgentConfigService(db)
    versions = await service.list_versions_for_config(config_id)
    return [AgentConfigVersionResponse.from_orm(v) for v in versions[:limit]]


@router.get("/{config_id}/versions/{version_number}", response_model=AgentConfigVersionResponse)
async def get_version(
    config_id: uuid.UUID,
    version_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentConfigVersionResponse:
    """Get a specific version of a configuration."""
    service = AgentConfigService(db)
    version = await service.get_version_by_number(config_id, version_number)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return AgentConfigVersionResponse.from_orm(version)


@router.get("/{config_id}/audit", response_model=list[AgentConfigAuditResponse])
async def get_audit_logs(
    config_id: uuid.UUID,
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AgentConfigAuditResponse]:
    """Get audit trail for a configuration."""
    service = AgentConfigService(db)
    logs = await service.get_audit_logs(config_id, limit)
    return [AgentConfigAuditResponse.from_orm(log) for log in logs]


@router.get("/{config_id}/validate", response_model=AgentConfigValidationResponse)
async def validate_config(
    config_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentConfigValidationResponse:
    """Validate a configuration for governance and safety.

    Runs safety checks, fairness validation, and completeness checks.
    """
    service = AgentConfigService(db)
    governance = AgentConfigGovernance(db)

    config = await service.get_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    version = await service.get_version_by_number(config_id, config.version_number)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    validation = await governance.validate_version_before_approval(version)

    return AgentConfigValidationResponse(
        config_id=config.id,
        version_number=config.version_number,
        validation=validation["validation"],
        version_checks=validation["version_checks"],
        approval_items=[
            ValidationCheckItem(**item) for item in validation["approval_items"]
        ],
        recommendation=validation["recommendation"],
    )


@router.get("/{config_id}/approval-checklist", response_model=ApprovalChecklistResponse)
async def get_approval_checklist(
    config_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApprovalChecklistResponse:
    """Get approval checklist for admin review.

    Provides structured checklist with validation results and recommendation.
    Only admins should see this.
    """
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view approval checklists")

    service = AgentConfigService(db)
    governance = AgentConfigGovernance(db)

    config = await service.get_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    version = await service.get_version_by_number(config_id, config.version_number)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    checklist = await governance.get_approval_checklist(config, version)
    return ApprovalChecklistResponse(**checklist)


__all__ = ["router"]
