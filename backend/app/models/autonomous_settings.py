"""Autonomous operation settings model."""
from __future__ import annotations

import uuid
from datetime import datetime
from app.core.clock import utcnow

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk


class AutonomousSettings(Base, TimestampMixin):
    """Settings controlling autonomous AI operation per user."""

    __tablename__ = "autonomous_settings"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Enable/disable autonomous mode for this user
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Operational constraints
    actions_per_hour: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    daily_budget: Mapped[float] = mapped_column(Float, default=1000.0, nullable=False)
    min_confidence_threshold: Mapped[int] = mapped_column(Integer, default=90, nullable=False)

    # Governance requirements
    requires_governance_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_on_action: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_escalate_on_governance_fail: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Tracking
    actions_count_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    spending_today: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_reset_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    # Admin notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_autonomous_settings_user_id", "user_id"),
        Index("ix_autonomous_settings_enabled", "enabled"),
    )

    def reset_daily_counters(self) -> None:
        """Reset daily counters (call once per day)."""
        self.actions_count_today = 0
        self.spending_today = 0.0
        self.last_reset_at = utcnow()

    def can_execute_action(self, estimated_cost: float = 0.0) -> tuple[bool, str]:
        """Check if user can execute another action today.

        Returns:
            (can_execute, reason)
        """
        if not self.enabled:
            return False, "Autonomous mode disabled for this user"

        if self.actions_count_today >= self.actions_per_hour:
            return False, f"Daily action limit reached ({self.actions_per_hour}/day)"

        if self.spending_today + estimated_cost > self.daily_budget:
            return (
                False,
                f"Daily budget exceeded ({self.spending_today + estimated_cost:.2f} > {self.daily_budget:.2f})",
            )

        return True, "OK"

    def record_action(self, cost: float = 0.0) -> None:
        """Record an executed action."""
        self.actions_count_today += 1
        self.spending_today += cost
        self.last_action_at = utcnow()
