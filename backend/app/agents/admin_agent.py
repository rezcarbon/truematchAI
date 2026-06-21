"""System Admin Agent for platform management and governance."""
import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.enhanced_agent import EnhancedBaseAgent
from app.models.user import User
from app.models.governance_review import GovernanceReview

logger = logging.getLogger(__name__)


ADMIN_INSTRUCTIONS = """You are the TrueMatch System Admin Assistant. You help administrators manage the platform.

You can help with:
1. **System Monitoring**: Check system health, metrics, and status
2. **Governance Management**: Review pending governance failures, approve/reject
3. **User Management**: Manage users, roles, and access
4. **Configuration**: Configure system settings and thresholds
5. **Analytics**: View hiring metrics, platform usage, AI performance
6. **Troubleshooting**: Diagnose issues, investigate failures
7. **Reporting**: Generate reports and insights

CAPABILITIES:
- View real-time system health and metrics
- List and manage pending governance reviews
- View user accounts and roles
- Configure governance thresholds and settings
- Generate hiring analytics and reports
- Investigate assessment failures
- View LLM performance metrics
- Track system performance and errors

PROACTIVE BEHAVIORS:
- Always provide current system metrics without waiting to be asked
- Flag issues (pending reviews, high error rates, system slowdowns)
- Alert about governance gate failures requiring review
- Suggest optimizations based on usage patterns
- Recommend threshold adjustments based on trends

COMMUNICATION STYLE:
- Be concise and data-focused
- Use metrics and numbers
- Prioritize critical issues
- Suggest improvements based on data
- Ask for confirmation before making changes
- Explain the impact of configuration changes

When an admin logs in:
1. Provide current system status snapshot
2. Highlight any critical issues
3. Show pending action items
4. Suggest optimizations

When discussing metrics:
1. Show relevant data
2. Explain trends
3. Suggest optimizations
4. Answer specific questions

When managing governance:
1. Show pending reviews with details
2. Explain failure reasons
3. Ask for decision (approve/reject/escalate)
4. Log decision in audit trail

When changing configuration:
1. Explain what will change
2. Show impact
3. Ask for confirmation
4. Apply change
5. Show results

Be the platform's steward - make sure everything is running smoothly and the system is improving."""


class AdminAgent(EnhancedBaseAgent):
    """Agent that helps administrators manage the TrueMatch platform."""

    def __init__(self):
        super().__init__(
            role="admin",
            instructions=ADMIN_INSTRUCTIONS,
        )

    async def _load_role_context(self, user: User, db: AsyncSession) -> dict:
        """Load admin-specific context: system metrics, governance data, user counts.

        Args:
            user: User object
            db: Database session

        Returns:
            Dict with admin context
        """
        context = {
            "capabilities": [
                "system_monitoring",
                "governance_management",
                "user_administration",
                "configuration",
                "analytics",
                "troubleshooting",
            ],
        }

        try:
            # Load governance review stats
            stmt = select(
                GovernanceReview.status,
                func.count(GovernanceReview.id),
            ).group_by(GovernanceReview.status)
            result = await db.execute(stmt)
            governance_stats = {row[0]: row[1] for row in result.all()}

            context["governance"] = {
                "pending": governance_stats.get("pending", 0),
                "approved": governance_stats.get("approved", 0),
                "rejected": governance_stats.get("rejected", 0),
                "escalated": governance_stats.get("escalated", 0),
                "total": sum(governance_stats.values()),
            }

            # Load user count by role
            stmt = select(User.role, func.count(User.id)).group_by(User.role)
            result = await db.execute(stmt)
            user_by_role = {row[0]: row[1] for row in result.all()}

            context["users"] = {
                "admin": user_by_role.get("admin", 0),
                "recruiter": user_by_role.get("recruiter", 0),
                "candidate": user_by_role.get("candidate", 0),
                "total": sum(user_by_role.values()),
            }

            logger.info(
                "Loaded admin context",
                extra={
                    "user_id": str(user.id),
                    "governance_pending": context["governance"]["pending"],
                    "users_total": context["users"]["total"],
                },
            )

        except Exception as e:
            logger.error(f"Failed to load admin context: {e}")
            context["governance"] = {
                "pending": 0,
                "approved": 0,
                "rejected": 0,
                "escalated": 0,
                "total": 0,
            }
            context["users"] = {
                "admin": 0,
                "recruiter": 0,
                "candidate": 0,
                "total": 0,
            }

        return context

    def _format_context(self, user_context: dict) -> str:
        """Format admin context for system prompt."""
        capabilities = user_context.get("capabilities", [])
        governance = user_context.get("governance", {})
        return f"""
- Capabilities Available: {', '.join(capabilities)}
- Governance Reviews Status:
  - Pending: {governance.get('pending', 0)}
  - Approved: {governance.get('approved', 0)}
  - Rejected: {governance.get('rejected', 0)}
  - Escalated: {governance.get('escalated', 0)}
- Total Users: {user_context.get('user_count', 'N/A')}

Focus on system health, governance management, and platform optimization."""
