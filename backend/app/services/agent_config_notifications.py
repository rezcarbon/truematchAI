"""Email notifications for agent configuration approvals."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, AgentConfig, AgentConfigVersion


class NotificationType(str, Enum):
    """Types of notifications to send."""

    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"
    activated = "activated"


class AgentConfigNotificationService:
    """Send email notifications for agent config events."""

    def __init__(self, db: AsyncSession):
        self.db = db
        # In production, inject email service (SendGrid, AWS SES, etc.)
        # For now, we'll use a placeholder

    async def notify_submission(
        self, config: AgentConfig, submitted_by: User
    ) -> bool:
        """Notify admins that a config was submitted for approval."""
        subject = f"Agent Config Submitted: {config.name}"

        body = self._build_html_email(
            title="Agent Configuration Submitted for Approval",
            sections=[
                ("Configuration", self._format_config_info(config)),
                ("Submitted By", f"{submitted_by.email}"),
                ("Next Steps", "An admin will review this configuration and approve/reject it."),
            ],
            action_url="https://app.truematch.com/admin/approvals",
            action_label="Review Configuration",
        )

        # Send to all admins
        return await self._send_to_admins(subject, body)

    async def notify_approval(
        self, config: AgentConfig, approved_by: User, feedback: Optional[str]
    ) -> bool:
        """Notify recruiter that their config was approved."""
        subject = f"✓ Agent Config Approved: {config.name}"

        feedback_section = f"<p><strong>Feedback:</strong></p><p>{feedback}</p>" if feedback else ""

        body = self._build_html_email(
            title="Your Agent Configuration Has Been Approved",
            sections=[
                ("Configuration", self._format_config_info(config)),
                ("Approved By", f"{approved_by.email}"),
                ("Feedback", feedback or "No feedback provided."),
                (
                    "Next Steps",
                    "Your configuration is approved and ready to activate. Admins will activate it shortly.",
                ),
            ],
            action_url="https://app.truematch.com/admin/approvals",
            action_label="View Details",
        )

        # Send to recruiter who created it
        creator = await self._get_user(config.created_by_id)
        if creator:
            return await self._send_email(creator.email, subject, body)
        return False

    async def notify_rejection(
        self, config: AgentConfig, rejected_by: User, feedback: str
    ) -> bool:
        """Notify recruiter that their config was rejected."""
        subject = f"⚠ Agent Config Rejected: {config.name}"

        body = self._build_html_email(
            title="Your Agent Configuration Requires Changes",
            sections=[
                ("Configuration", self._format_config_info(config)),
                ("Rejected By", f"{rejected_by.email}"),
                ("Feedback", feedback),
                (
                    "Next Steps",
                    "Please make the requested changes and resubmit your configuration for approval.",
                ),
            ],
            action_url="https://app.truematch.com/configs",
            action_label="Edit Configuration",
        )

        # Send to recruiter who created it
        creator = await self._get_user(config.created_by_id)
        if creator:
            return await self._send_email(creator.email, subject, body)
        return False

    async def notify_activation(
        self, config: AgentConfig, activated_by: User
    ) -> bool:
        """Notify recruiters that a config has been activated."""
        subject = f"▶ Agent Config Activated: {config.name}"

        body = self._build_html_email(
            title="Agent Configuration Is Now Active",
            sections=[
                ("Configuration", self._format_config_info(config)),
                ("Activated By", f"{activated_by.email}"),
                (
                    "Impact",
                    "This configuration is now live and will be used for all new chat sessions.",
                ),
                (
                    "View Results",
                    "Monitor agent performance in the analytics dashboard.",
                ),
            ],
            action_url="https://app.truematch.com/analytics",
            action_label="View Analytics",
        )

        # Send to team (creator + admins)
        return await self._send_to_admins(subject, body)

    async def notify_batch_approval(
        self, configs: list[AgentConfig], approved_by: User, count: int
    ) -> bool:
        """Notify about batch approval."""
        subject = f"✓ {count} Agent Configs Approved"

        config_list = "\n".join(
            [f"• {c.name} (v{c.version_number})" for c in configs[:10]]
        )
        if len(configs) > 10:
            config_list += f"\n• ... and {len(configs) - 10} more"

        body = self._build_html_email(
            title=f"{count} Agent Configurations Approved",
            sections=[
                ("Approved By", f"{approved_by.email}"),
                ("Configurations", config_list),
                ("Status", "All configurations are approved and ready for activation."),
            ],
            action_url="https://app.truematch.com/admin/approvals",
            action_label="View All",
        )

        return await self._send_to_admins(subject, body)

    # Helper methods

    def _format_config_info(self, config: AgentConfig) -> str:
        """Format config info for email."""
        return f"""
        <p><strong>Name:</strong> {config.name}</p>
        <p><strong>Agent Type:</strong> {config.agent_type}</p>
        <p><strong>Version:</strong> {config.version_number}</p>
        <p><strong>Status:</strong> {config.status}</p>
        """

    def _build_html_email(
        self,
        title: str,
        sections: list[tuple[str, str]],
        action_url: str = "",
        action_label: str = "View More",
    ) -> str:
        """Build a formatted HTML email."""
        sections_html = ""
        for heading, content in sections:
            sections_html += f"""
            <h3 style="color: #374151; margin-top: 20px; margin-bottom: 10px;">
                {heading}
            </h3>
            <p style="color: #4B5563; line-height: 1.6;">{content}</p>
            """

        action_html = ""
        if action_url:
            action_html = f"""
            <div style="text-align: center; margin-top: 30px; margin-bottom: 30px;">
                <a href="{action_url}"
                   style="background-color: #2563EB; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 6px; font-weight: bold;">
                    {action_label}
                </a>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 style="color: #1F2937; margin-bottom: 20px;">{title}</h1>

                {sections_html}

                {action_html}

                <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 30px 0;">

                <p style="color: #9CA3AF; font-size: 14px;">
                    This is an automated notification from TrueMatch.
                    Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """

    async def _send_email(self, recipient: str, subject: str, html_body: str) -> bool:
        """Send email to single recipient.

        In production, integrate with SendGrid, AWS SES, or similar.
        For now, just log it.
        """
        print(f"EMAIL: {recipient} | {subject}")
        # TODO: Integrate with email service
        return True

    async def _send_to_admins(self, subject: str, html_body: str) -> bool:
        """Send email to all admin users."""
        # TODO: Query all admin users and send
        print(f"EMAIL TO ADMINS: {subject}")
        return True

    async def _get_user(self, user_id) -> Optional[User]:
        """Get user by ID."""
        from sqlalchemy import select

        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


__all__ = ["AgentConfigNotificationService", "NotificationType"]
