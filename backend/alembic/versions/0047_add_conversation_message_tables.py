"""Add conversation and message tables for chat endpoints.

Revision ID: 0047
Revises: 0046
Create Date: 2026-08-30 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0047"
down_revision = "0046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    conversation_status_enum = postgresql.ENUM("active", "archived", "closed", name="conversationstatus", create_type=True)
    message_role_enum = postgresql.ENUM("user", "assistant", "system", name="messagerole", create_type=True)

    op.execute("CREATE TYPE IF NOT EXISTS conversationstatus AS ENUM ('active', 'archived', 'closed')")
    op.execute("CREATE TYPE IF NOT EXISTS messagerole AS ENUM ('user', 'assistant', 'system')")

    # Create conversations table
    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", conversation_status_enum, nullable=False, server_default="active", comment="active, archived, or closed"),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.Index("ix_conversations_user_id", "user_id"),
        sa.Index("ix_conversations_status", "status"),
        sa.Index("ix_conversations_updated_at", "updated_at"),
    )

    # Create messages table
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", message_role_enum, nullable=False, comment="user, assistant, or system"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("message_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment="Additional message metadata"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.Index("ix_messages_conversation_id", "conversation_id"),
        sa.Index("ix_messages_user_id", "user_id"),
        sa.Index("ix_messages_created_at", "created_at"),
    )


def downgrade() -> None:
    # Drop messages table
    op.drop_table("messages")

    # Drop conversations table
    op.drop_table("conversations")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS messagerole CASCADE")
    op.execute("DROP TYPE IF EXISTS conversationstatus CASCADE")
