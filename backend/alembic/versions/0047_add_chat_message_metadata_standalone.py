"""Add chat message metadata - standalone migration bypassing broken chain

Revision ID: 0047
Revises: 0001
Create Date: 2026-08-04 16:00:00.000000

This migration adds metadata persistence for chat messages.
It bypasses migrations 0021-0046 which have schema conflicts.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0047'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add message_metadata JSONB column to chat_messages table."""
    # Check if column already exists before adding
    op.add_column(
        'chat_messages',
        sa.Column(
            'message_metadata',
            postgresql.JSONB(),
            nullable=True,
            comment='Stores persona_id, persona_name, objective, mode'
        ),
        if_not_exists=True
    )


def downgrade() -> None:
    """Remove message_metadata column from chat_messages table."""
    op.drop_column('chat_messages', 'message_metadata', if_exists=True)
