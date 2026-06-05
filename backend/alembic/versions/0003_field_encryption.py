"""Field-level encryption: convert encrypted columns to TEXT, add singpass blind index.

Encrypted values are opaque text, so JSONB PII columns become TEXT. A keyed
blind-index column replaces the (now useless) plaintext index on singpass_id.

Revision ID: 0003
Revises: 0002
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels = None
depends_on = None

# (table, column) pairs whose JSONB becomes TEXT for encryption-at-rest.
_JSONB_TO_TEXT = [
    ("resumes", "parsed_data"),
    ("resumes", "supplementary"),
    ("audit_trail", "event_data"),
    ("capability_profiles", "trajectory_summary"),
    ("capability_profiles", "top_capabilities"),
]


def upgrade() -> None:
    for table, col in _JSONB_TO_TEXT:
        op.alter_column(
            table, col, type_=sa.Text(), postgresql_using=f"{col}::text", existing_nullable=True
        )

    # singpass_id: widen to TEXT (holds ciphertext) and swap the index for a
    # keyed blind index used by equality lookups.
    op.alter_column("users", "singpass_id", type_=sa.Text(), existing_nullable=True)
    op.add_column("users", sa.Column("singpass_id_bidx", sa.String(64), nullable=True))
    op.drop_index("ix_users_singpass_id", table_name="users")
    op.create_index("ix_users_singpass_id_bidx", "users", ["singpass_id_bidx"])


def downgrade() -> None:
    op.drop_index("ix_users_singpass_id_bidx", table_name="users")
    op.create_index("ix_users_singpass_id", "users", ["singpass_id"])
    op.drop_column("users", "singpass_id_bidx")
    op.alter_column(
        "users", "singpass_id", type_=sa.String(64), existing_nullable=True
    )

    for table, col in _JSONB_TO_TEXT:
        op.alter_column(
            table,
            col,
            type_=postgresql.JSONB(),
            postgresql_using=f"{col}::jsonb",
            existing_nullable=True,
        )
