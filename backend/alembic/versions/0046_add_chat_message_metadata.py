"""Add metadata column to chat_messages for persona and mode tracking.

Revision ID: 0046
Revises: 0045
Create Date: 2026-08-04 06:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0046"
down_revision = "0045"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add metadata column to chat_messages table
    # Stores persona info, objective, and conversation mode
    op.add_column(
        "chat_messages",
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Persona info, objective, and conversation mode"
        ),
    )


def downgrade() -> None:
    # Remove metadata column
    op.drop_column("chat_messages", "metadata")
