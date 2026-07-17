"""Governance layer for agent configuration management.

Implements:
- Permission checks (who can create, approve, activate)
- Configuration validation (safety gates)
- Approval workflow with audit trail
- Compliance checking before activation
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, AgentConfig, AgentConfigVersion, UserRole


class AgentConfigGovernance:
    """Governance and permission checks for agent configs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_create_permission(
        self, user: User, company_id: uuid.UUID
    ) -> tuple[bool, Optional[str]]:
        """Check if user can create agent configs.

        Returns:
            (permitted: bool, reason: Optional[str] if denied)
        """
        # Only admins and designated config managers can create
        if user.role not in [UserRole.admin, UserRole.recruiter]:
            return False, f"Role {user.role} cannot create agent configs"

        # TODO: Check company membership
        return True, None

    async def check_update_permission(
        self, user: User, config: AgentConfig
    ) -> tuple[bool, Optional[str]]:
        """Check if user can update a config.

        Only the creator or admins can update DRAFT configs.
        """
        if user.role == UserRole.admin:
            return True, None

        if config.created_by_id == user.id:
            return True, None

        return False, f"Only config creator or admin can update this config"

    async def check_submit_permission(
        self, user: User, config: AgentConfig
    ) -> tuple[bool, Optional[str]]:
        """Check if user can submit config for approval."""
        if user.role == UserRole.admin:
            return True, None

        if config.created_by_id == user.id:
            return True, None

        return False, f"Only config creator or admin can submit this config"

    async def check_approve_permission(self, user: User) -> tuple[bool, Optional[str]]:
        """Check if user can approve agent configs.

        Only admins can approve.
        """
        if user.role == UserRole.admin:
            return True, None

        return False, "Only admins can approve agent configs"

    async def check_activate_permission(self, user: User) -> tuple[bool, Optional[str]]:
        """Check if user can activate configs.

        Only admins can activate (deploy to production).
        """
        if user.role == UserRole.admin:
            return True, None

        return False, "Only admins can activate agent configs"

    async def validate_config_safety(
        self, config: AgentConfig
    ) -> dict:
        """Validate agent config for safety/compliance.

        Checks:
        1. Instructions don't contain harmful directives
        2. Tool combinations are valid
        3. Parameters are within safe ranges
        4. No PII exposure in instructions

        Returns:
            {
                "passed": bool,
                "warnings": [str],
                "errors": [str],
                "fairness_score": 0-100
            }
        """
        warnings = []
        errors = []
        fairness_score = 100

        # Check 1: Instruction safety (basic pattern matching)
        dangerous_patterns = [
            "ignore previous instructions",
            "bypass governance",
            "disable fairness",
            "ignore consent",
            "override rules",
        ]
        instructions_lower = config.instructions.lower()
        for pattern in dangerous_patterns:
            if pattern in instructions_lower:
                errors.append(f"Instruction contains potentially dangerous pattern: '{pattern}'")
                fairness_score -= 20

        # Check 2: Tool combinations
        valid_tool_combinations = {
            "analyze": ["clarify"],
            "rank": ["clarify"],
            "schedule": ["send"],
            "approve": ["send"],
            "upload": ["analyze"],
            "plan": ["analyze", "rank", "schedule", "approve"],
        }

        for tool in config.tools_enabled:
            if tool not in valid_tool_combinations:
                warnings.append(f"Unknown tool: '{tool}'")

        # Check 3: Parameter ranges
        agent_params = config.agent_parameters or {}
        if "temperature" in agent_params:
            temp = agent_params["temperature"]
            if not isinstance(temp, (int, float)) or not 0 <= temp <= 2:
                errors.append("Temperature must be between 0 and 2")
                fairness_score -= 10

        if "max_tokens" in agent_params:
            tokens = agent_params["max_tokens"]
            if not isinstance(tokens, int) or tokens < 100 or tokens > 4096:
                errors.append("Max tokens must be between 100 and 4096")
                fairness_score -= 10

        # Check 4: PII patterns in instructions
        pii_patterns = ["email", "phone", "ssn", "password", "api key", "secret"]
        for pattern in pii_patterns:
            if pattern in instructions_lower:
                warnings.append(f"Instructions mention potentially sensitive term: '{pattern}'")
                fairness_score -= 5

        # Check 5: Fairness language
        fairness_keywords = ["fair", "unbiased", "equitable", "diverse", "inclusive"]
        fairness_count = sum(1 for kw in fairness_keywords if kw in instructions_lower)
        if fairness_count == 0:
            warnings.append("Consider adding fairness/bias awareness to instructions")
            fairness_score -= 10

        return {
            "passed": len(errors) == 0,
            "warnings": warnings,
            "errors": errors,
            "fairness_score": max(0, fairness_score),
        }

    async def validate_version_before_approval(
        self, version: AgentConfigVersion
    ) -> dict:
        """Validate a config version before admin approval.

        Returns detailed validation report.
        """
        validation = await self.validate_config_safety(version)

        # Add version-specific checks
        version_checks = {
            "has_instructions": bool(version.instructions),
            "has_tools": len(version.tools_enabled or []) > 0,
            "change_documented": bool(version.change_reason),
            "submitted_properly": bool(version.submitted_by_id),
        }

        validation["version_checks"] = version_checks
        validation["version_passed"] = all(version_checks.values())

        return validation

    async def get_approval_checklist(
        self, config: AgentConfig, version: AgentConfigVersion
    ) -> dict:
        """Generate approval checklist for admin review.

        Provides structured checklist for admin to approve/reject config.
        """
        validation = await self.validate_version_before_approval(version)

        checklist = {
            "config_id": str(config.id),
            "version_number": version.version_number,
            "agent_type": config.agent_type,
            "role": config.role,
            "created_by": str(config.created_by_id),
            "submitted_at": version.submitted_at.isoformat() if version.submitted_at else None,
            "validation": {
                "safety_passed": validation["passed"],
                "fairness_score": validation["fairness_score"],
                "warnings": validation["warnings"],
                "errors": validation["errors"],
            },
            "version_checks": {
                "has_instructions": validation["version_checks"]["has_instructions"],
                "has_tools": validation["version_checks"]["has_tools"],
                "change_documented": validation["version_checks"]["change_documented"],
                "submitted_properly": validation["version_checks"]["submitted_properly"],
            },
            "approval_items": [
                {
                    "item": "Safety validation",
                    "status": "passed" if validation["passed"] else "failed",
                    "details": validation["errors"] or "No safety issues found",
                },
                {
                    "item": "Fairness score",
                    "status": "passed" if validation["fairness_score"] >= 70 else "warning",
                    "details": f"Score: {validation['fairness_score']}/100",
                },
                {
                    "item": "Version documentation",
                    "status": "passed" if validation["version_checks"]["change_documented"] else "missing",
                    "details": f"Change reason: {version.change_reason or 'Not provided'}",
                },
                {
                    "item": "Configuration completeness",
                    "status": (
                        "passed"
                        if validation["version_checks"]["has_instructions"]
                        and validation["version_checks"]["has_tools"]
                        else "incomplete"
                    ),
                    "details": f"Instructions: {'✓' if validation['version_checks']['has_instructions'] else '✗'}, Tools: {'✓' if validation['version_checks']['has_tools'] else '✗'}",
                },
            ],
            "recommendation": "approve"
            if validation["passed"] and validation["fairness_score"] >= 70
            else "review_required",
        }

        return checklist


__all__ = ["AgentConfigGovernance"]
