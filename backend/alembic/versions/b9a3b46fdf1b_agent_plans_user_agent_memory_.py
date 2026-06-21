"""agent plans, user agent memory, assessment input_hash

Revision ID: b9a3b46fdf1b
Revises: c1827da5d940
Create Date: 2026-06-13

Hand-written (autogenerate also emitted index-rename noise from cosmetic
index-name differences; those are intentionally excluded).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'b9a3b46fdf1b'
down_revision: Union[str, None] = 'c1827da5d940'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'agent_plans',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('steps', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('current_step', sa.Integer(), nullable=False),
        sa.Column('error', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_plans_user_id', 'agent_plans', ['user_id'])
    op.create_index('ix_agent_plans_status', 'agent_plans', ['status'])

    op.create_table(
        'user_agent_memory',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('memory', sa.Text(), nullable=True),  # EncryptedJSON (impl=Text)
        sa.Column('merge_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_user_agent_memory_user'),
    )

    op.add_column('assessments', sa.Column('input_hash', sa.String(length=64), nullable=True))
    op.create_index('ix_assessments_input_hash', 'assessments', ['input_hash'])


def downgrade() -> None:
    op.drop_index('ix_assessments_input_hash', table_name='assessments')
    op.drop_column('assessments', 'input_hash')
    op.drop_table('user_agent_memory')
    op.drop_index('ix_agent_plans_status', table_name='agent_plans')
    op.drop_index('ix_agent_plans_user_id', table_name='agent_plans')
    op.drop_table('agent_plans')
