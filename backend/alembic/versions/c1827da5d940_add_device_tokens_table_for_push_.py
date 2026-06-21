"""add device_tokens table for push notifications

Revision ID: c1827da5d940
Revises: 3df0ff081f43
Create Date: 2026-06-13

Only creates the device_tokens table (the new feature). Other drift the
autogenerate detected against a partially-stamped live DB is intentionally left
out — fresh DBs already get those tables from 3df0ff081f43.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1827da5d940'
down_revision: Union[str, None] = '3df0ff081f43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'device_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token', sa.String(length=512), nullable=False),
        sa.Column('platform', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token', name='uq_device_tokens_token'),
    )
    op.create_index('ix_device_tokens_user_id', 'device_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_device_tokens_user_id', table_name='device_tokens')
    op.drop_table('device_tokens')
