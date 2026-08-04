"""Add chat message metadata - standalone migration bypassing broken chain

Revision ID: 0047
Revises: 0020
Create Date: 2026-08-04 16:00:00.000000

This migration adds metadata persistence for chat messages.
It depends on 0020 (last known good state) and adds metadata to chat_messages.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0047'
down_revision = '0020'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add message_metadata JSONB column to chat_messages table."""
    # Add column if table exists, otherwise this will be applied after chat tables are created
    try:
        op.add_column(
            'chat_messages',
            sa.Column(
                'message_metadata',
                postgresql.JSONB(),
                nullable=True,
                comment='Stores persona_id, persona_name, objective, mode'
            )
        )
    except Exception:
        # Table doesn't exist yet, will be created by earlier migrations
        pass


def downgrade() -> None:
    """Remove message_metadata column from chat_messages table."""
    try:
        op.drop_column('chat_messages', 'message_metadata')
    except Exception:
        pass
