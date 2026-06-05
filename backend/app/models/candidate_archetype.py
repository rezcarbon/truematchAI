"""Candidate archetype model for recruiter testing."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk
from app.models.cv_analysis import SeniorityLevel
from sqlalchemy import Enum as SAEnum


class CandidateArchetype(Base, TimestampMixin):
    """Pre-built candidate profile archetypes for testing JDs."""
    __tablename__ = "candidate_archetypes"

    id: Mapped[uuid.UUID] = uuid_pk()
    # Optional: company-specific archetypes. Null = TrueMatch system archetype
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True,
    )
    role_level: Mapped[SeniorityLevel] = mapped_column(
        SAEnum(SeniorityLevel, name="seniority_level"),
        nullable=False,
    )
    role_title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Typical profile: years_experience, key_capabilities, preferred_tech_stack, nice_to_have_skills
    typical_profile: Mapped[dict] = mapped_column(JSONB, nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # True = TrueMatch pre-built, False = company-created
    is_system: Mapped[bool] = mapped_column(default=True, nullable=False)

    __table_args__ = (
        Index("ix_candidate_archetypes_company_id", "company_id"),
        Index("ix_candidate_archetypes_is_system", "is_system"),
        Index("ix_candidate_archetypes_role_level", "role_level"),
    )
