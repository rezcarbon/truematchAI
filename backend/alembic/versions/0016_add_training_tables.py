"""Add Training Simulation System tables.

Revision ID: 0016
Revises: 0015
Create Date: 2026-06-06 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0016'
down_revision = '0015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create feedback_type enum
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'feedback_type') THEN
                CREATE TYPE feedback_type AS ENUM ('hire', 'reject', 'maybe', 'interested', 'not_interested', 'applied');
            END IF;
        END $$;
    """)

    # Create training_feedback table
    op.create_table(
        'training_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('feedback_type', sa.Enum('hire', 'reject', 'maybe', 'interested', 'not_interested', 'applied', name='feedback_type'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('time_to_action_seconds', sa.Integer(), nullable=True),
        sa.Column('outcome', sa.String(50), nullable=True),
        sa.Column('outcome_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('hire_success', sa.Boolean(), nullable=True),
        sa.Column('source', sa.String(50), nullable=False, server_default='web'),
        sa.Column('is_training', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['positions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['candidate_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_training_feedback_user_id', 'training_feedback', ['user_id'])
    op.create_index('ix_training_feedback_job_id', 'training_feedback', ['job_id'])
    op.create_index('ix_training_feedback_candidate_id', 'training_feedback', ['candidate_id'])
    op.create_index('ix_training_feedback_type', 'training_feedback', ['feedback_type'])
    op.create_index('ix_training_feedback_outcome', 'training_feedback', ['outcome'])

    # Create capability_mapping table
    op.create_table(
        'capability_mapping',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cv_keyword', sa.String(255), nullable=False),
        sa.Column('capability', sa.String(255), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('frequency', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('positive_feedback', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('negative_feedback', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('job_category', sa.String(100), nullable=True),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('is_user_added', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('learned_from_feedback', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_capability_mapping_keyword', 'capability_mapping', ['cv_keyword'])
    op.create_index('ix_capability_mapping_capability', 'capability_mapping', ['capability'])
    op.create_index('ix_capability_mapping_confidence', 'capability_mapping', ['confidence_score'])

    # Create credential_mapping table
    op.create_table(
        'credential_mapping',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('credential', sa.String(255), nullable=False),
        sa.Column('requirement', sa.String(255), nullable=False),
        sa.Column('match_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('is_exact_match', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_acceptable_alternative', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('alternative_matches', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('positive_feedback', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('negative_feedback', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_credential_mapping_credential', 'credential_mapping', ['credential'])
    op.create_index('ix_credential_mapping_requirement', 'credential_mapping', ['requirement'])
    op.create_index('ix_credential_mapping_score', 'credential_mapping', ['match_score'])

    # Create success_pattern table
    op.create_table(
        'success_pattern',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('job_category', sa.String(100), nullable=True),
        sa.Column('successful_candidate_profile', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('key_capabilities', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('key_credentials', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('success_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('average_tenure_months', sa.Integer(), nullable=True),
        sa.Column('average_performance_rating', sa.Float(), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('salary_range', sa.String(50), nullable=True),
        sa.Column('confidence_level', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('is_valid', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['positions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_success_pattern_job_id', 'success_pattern', ['job_id'])
    op.create_index('ix_success_pattern_category', 'success_pattern', ['job_category'])
    op.create_index('ix_success_pattern_rate', 'success_pattern', ['success_rate'])

    # Create training_progress table
    op.create_table(
        'training_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('current_value', sa.Float(), nullable=False),
        sa.Column('baseline_value', sa.Float(), nullable=False),
        sa.Column('improvement_percent', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('sample_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('period', sa.String(50), nullable=False, server_default='daily'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_training_progress_metric', 'training_progress', ['metric_name'])
    op.create_index('ix_training_progress_period', 'training_progress', ['period'])
    op.create_index('ix_training_progress_value', 'training_progress', ['current_value'])

    # Create training_insight table
    op.create_table(
        'training_insight',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('insight_type', sa.String(100), nullable=False),
        sa.Column('insight_category', sa.String(100), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('supporting_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_trending', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_training_insight_type', 'training_insight', ['insight_type'])
    op.create_index('ix_training_insight_category', 'training_insight', ['insight_category'])
    op.create_index('ix_training_insight_public', 'training_insight', ['is_public'])

    # Create virtual_brain_state table
    op.create_table(
        'virtual_brain_state',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('total_feedback_samples', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_patterns_learned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('match_accuracy', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('hire_success_prediction_accuracy', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('model_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('performance_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('training_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('training_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_virtual_brain_state_version', 'virtual_brain_state', ['version'])
    op.create_index('ix_virtual_brain_state_active', 'virtual_brain_state', ['is_active'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('virtual_brain_state')
    op.drop_table('training_insight')
    op.drop_table('training_progress')
    op.drop_table('success_pattern')
    op.drop_table('credential_mapping')
    op.drop_table('capability_mapping')
    op.drop_table('training_feedback')

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS feedback_type;")
