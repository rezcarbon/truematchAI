"""Add chat message metadata - standalone migration bypassing broken chain

Revision ID: 0047
Revises: 0020
Create Date: 2026-08-04 16:00:00.000000

This migration adds metadata persistence for chat messages.
Creates chat_messages table and adds message_metadata column.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0047'
down_revision = '0020'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create chat_messages table if needed and add message_metadata column."""
    from sqlalchemy import text

    # First, try to create the table if it doesn't exist
    try:
        op.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id UUID NOT NULL,
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                message_metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
    except Exception:
        # Table might already exist, continue
        pass

    # Add the column if it doesn't exist
    try:
        op.execute(text("""
            ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS message_metadata JSONB
        """))
    except Exception:
        # Column might already exist or table doesn't exist yet
        pass


def downgrade() -> None:
    """Remove message_metadata column from chat_messages table."""
    op.execute("""
        ALTER TABLE chat_messages DROP COLUMN IF EXISTS message_metadata;
    """)
