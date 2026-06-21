"""capability translation: candidate-facing ATS rewrite with measured lift

Revision ID: c6a1f3d28e7b
Revises: b2e5f8c1a9d3
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "c6a1f3d28e7b"
down_revision = "b2e5f8c1a9d3"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    # create_type=False: we create the type explicitly below so the table DDL
    # does not also emit a CREATE TYPE (which would 'already exists' on re-run).
    translation_status = postgresql.ENUM(
        "pending", "translating", "completed", "failed",
        name="translation_status", create_type=False,
    )
    postgresql.ENUM(
        "pending", "translating", "completed", "failed",
        name="translation_status",
    ).create(op.get_bind(), checkfirst=True)

    op.create_table(
        "capability_translations",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "user_id", UUID,
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "resume_id", UUID,
            sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "status", translation_status,
            server_default="pending", nullable=False,
        ),
        sa.Column("target_role", sa.String(255), nullable=True),
        # PII columns are application-encrypted (EncryptedText/JSON → Text at rest).
        sa.Column("target_jd", sa.Text(), nullable=True),
        sa.Column("original_text", sa.Text(), nullable=True),
        sa.Column("rewrite", sa.Text(), nullable=True),
        sa.Column("substitutions", sa.Text(), nullable=True),
        sa.Column("score_detail", sa.Text(), nullable=True),
        sa.Column("before_keyword_score", sa.Integer(), nullable=True),
        sa.Column("after_keyword_score", sa.Integer(), nullable=True),
        sa.Column("before_semantic_score", sa.Integer(), nullable=True),
        sa.Column("after_semantic_score", sa.Integer(), nullable=True),
        sa.Column("provenance", postgresql.JSONB(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", TS, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TS, server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_capability_translations_user_id", "capability_translations", ["user_id"]
    )
    op.create_index(
        "ix_capability_translations_status", "capability_translations", ["status"]
    )


def downgrade() -> None:
    op.drop_index("ix_capability_translations_status", table_name="capability_translations")
    op.drop_index("ix_capability_translations_user_id", table_name="capability_translations")
    op.drop_table("capability_translations")
    postgresql.ENUM(name="translation_status").drop(op.get_bind(), checkfirst=True)
