"""Self-learned role taxonomy.

The platform clusters its own positions by JD embedding into role *families*
(e.g. "backend / distributed-systems", "data / ML"). Each cluster keeps a
centroid (so new positions can be assigned without a full rebuild) and the
capabilities that recur across its members. The assessment pipeline injects a
cluster's recurring capabilities as additional context — so a candidate is
judged against what the role family has historically valued, learned from the
org's own JDs rather than a hand-authored taxonomy.
"""
from __future__ import annotations

import uuid

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk


class RoleCluster(Base, TimestampMixin):
    __tablename__ = "role_clusters"

    id: Mapped[uuid.UUID] = uuid_pk()
    label: Mapped[str] = mapped_column(String(255), nullable=False, default="role family")
    # Mean unit-vector of member JD embeddings (list[float]); used to assign
    # new positions by cosine similarity without re-clustering everything.
    centroid: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Capabilities that recur across member JDs, most-frequent first.
    top_capabilities: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # Provenance: embedding model + clustering method.
    method: Mapped[str | None] = mapped_column(String(128), nullable=True)
