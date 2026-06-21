"""transition intelligence: candidate transition analyses

Revision ID: a4f1c7e9b2d8
Revises: f3d9b27a1e64
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "a4f1c7e9b2d8"
down_revision = "f3d9b27a1e64"
branch_labels = None
depends_on = None


def upgrade() -> None:
    transition_status = postgresql.ENUM(
        "pending", "analyzing", "completed", "failed",
        name="transition_status", create_type=False,
    )
    postgresql.ENUM(
        "pending", "analyzing", "completed", "failed",
        name="transition_status",
    ).create(op.get_bind(), checkfirst=True)

    op.create_table(
        "transition_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", transition_status, server_default="pending", nullable=False),
        sa.Column("current_role", sa.String(255), nullable=True),
        # PII → Text at rest (encrypted in the application layer)
        sa.Column("target", sa.Text(), nullable=True),
        sa.Column("source_language", sa.String(8), nullable=True),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("capability_score", sa.Integer(), nullable=True),
        sa.Column("provenance", postgresql.JSONB(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_transition_analyses_user_id", "transition_analyses", ["user_id"])
    op.create_index("ix_transition_analyses_status", "transition_analyses", ["status"])


def downgrade() -> None:
    op.drop_index("ix_transition_analyses_status", table_name="transition_analyses")
    op.drop_index("ix_transition_analyses_user_id", table_name="transition_analyses")
    op.drop_table("transition_analyses")
    postgresql.ENUM(name="transition_status").drop(op.get_bind(), checkfirst=True)
