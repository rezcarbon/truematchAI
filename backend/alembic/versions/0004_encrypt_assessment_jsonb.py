"""Encrypt candidate-derived assessment JSONB columns (convert to TEXT).

Completes field-level encryption: the assessment columns that quote or derive
from the resume (traditional detail, capability components/evidence, trajectory,
governance results) move to TEXT for encryption-at-rest. `jd_issues` is JD
analysis (not candidate PII) and stays JSONB.

Revision ID: 0004
Revises: 0003
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels = None
depends_on = None

_COLUMNS = [
    "traditional_detail",
    "capability_components",
    "capability_evidence",
    "trajectory_data",
    "counter_rec_evidence",
    "governance_coherence",
    "governance_consistency",
    "governance_fidelity",
    "governance_bias_flags",
]


def upgrade() -> None:
    for col in _COLUMNS:
        op.alter_column(
            "assessments",
            col,
            type_=sa.Text(),
            postgresql_using=f"{col}::text",
            existing_nullable=True,
        )


def downgrade() -> None:
    for col in _COLUMNS:
        op.alter_column(
            "assessments",
            col,
            type_=postgresql.JSONB(),
            postgresql_using=f"{col}::jsonb",
            existing_nullable=True,
        )
