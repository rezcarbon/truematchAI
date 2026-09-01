"""JD version history (Pillar 3 — JD evolution).

Every change to a position's job description is snapshotted here, giving the
JD-evolution engine the longitudinal record it needs to detect requirement drift
(e.g. years-of-experience creep) and to recommend how the role should evolve.
Also serves as an immutable audit record of how a posting's requirements changed
over time — relevant to hiring-fairness record-keeping.
"""
from __future__ import annotations

import uuid

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import uuid_pk


class JDVersion(Base):
    __tablename__ = "jd_versions"

    id: Mapped[uuid.UUID] = uuid_pk()
    position_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("positions.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_requirements: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    jd_quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    jd_issues: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_jd_versions_position_id", "position_id"),
        Index("ix_jd_versions_position_version", "position_id", "version", unique=True),
    )
