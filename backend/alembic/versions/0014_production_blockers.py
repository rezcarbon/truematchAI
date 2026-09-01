"""Add production blocker support tables.

Revision ID: 0014
Revises: 0013
Create Date: 2026-06-07

Adds governance logging, DSAR request tracking, and compliance infrastructure.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create governance_logs table
    op.create_table(
        'governance_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gate_sequence', sa.Integer(), nullable=False),
        sa.Column('gate_name', sa.String(), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('observations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assessment_id', 'gate_sequence', name='uq_governance_logs_assessment_sequence'),
    )
    op.create_index('ix_governance_logs_assessment_id', 'governance_logs', ['assessment_id'])
    op.create_index('ix_governance_logs_created_at', 'governance_logs', ['created_at'])
    op.create_index('ix_governance_logs_gate_name', 'governance_logs', ['gate_name'])

    # Create dsar_requests table
    op.create_table(
        'dsar_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('data_export_url', sa.String(length=500), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_dsar_requests_user_id', 'dsar_requests', ['user_id'])
    op.create_index('ix_dsar_requests_status', 'dsar_requests', ['status'])

    # Add governance tracking columns to assessments table
    op.add_column('assessments', sa.Column('gates_passed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('assessments', sa.Column('governance_status', sa.String(length=50), nullable=True, server_default='pending'))


def downgrade() -> None:
    # Drop new columns from assessments
    op.drop_column('assessments', 'governance_status')
    op.drop_column('assessments', 'gates_passed_at')

    # Drop dsar_requests table
    op.drop_index('ix_dsar_requests_status')
    op.drop_index('ix_dsar_requests_user_id')
    op.drop_table('dsar_requests')

    # Drop governance_logs table
    op.drop_index('ix_governance_logs_gate_name')
    op.drop_index('ix_governance_logs_created_at')
    op.drop_index('ix_governance_logs_assessment_id')
    op.drop_table('governance_logs')
