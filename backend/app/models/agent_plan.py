"""Multi-step agent plans (plan-then-execute).

A plan is an ordered list of tool steps the conversational agent proposed for a
single user goal. The user approves the WHOLE plan once (via the existing
action-confirmation flow); a runner then executes the steps sequentially through
the same validated action handlers, chaining step outputs into later steps'
parameters.
"""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk


class AgentPlan(Base, TimestampMixin):
    __tablename__ = "agent_plans"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Agent plan")
    # [{"order": 1, "tool": "rank", "parameters": {...}, "status": "pending",
    #   "result": {...}}] — parameters may contain "{{step_N.PATH}}" references
    # resolved from earlier steps' results at execution time.
    steps: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # pending_approval | running | completed | failed | cancelled
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending_approval")
    current_step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    __table_args__ = (
        Index("ix_agent_plans_user_id", "user_id"),
        Index("ix_agent_plans_status", "status"),
    )
