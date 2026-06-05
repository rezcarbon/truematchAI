"""Add ATS core features: pipeline stages, interviews, scorecards

Revision ID: 0013
Revises: 0012
Create Date: 2026-06-05 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create pipeline stage enum using raw SQL to avoid conflicts
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'pipeline_stage') THEN
                CREATE TYPE pipeline_stage AS ENUM ('applied', 'phone_screen', 'technical', 'onsite', 'offer', 'hired', 'rejected');
            END IF;
        END
        $$;
    """)

    # Create applications table
    op.create_table(
        'applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('position_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stage', postgresql.ENUM('applied', 'phone_screen', 'technical', 'onsite', 'offer', 'hired', 'rejected', name='pipeline_stage', create_type=False), nullable=False, server_default='applied'),
        sa.Column('stage_entered_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['position_id'], ['positions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.Index('ix_applications_user_id', 'user_id'),
        sa.Index('ix_applications_position_id', 'position_id'),
        sa.Index('ix_applications_resume_id', 'resume_id'),
    )

    # Create interviews table
    op.create_table(
        'interviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('position_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('interviewer_ids', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('candidate_email', sa.String(255), nullable=True),
        sa.Column('meeting_link', sa.String(500), nullable=True),
        sa.Column('meeting_platform', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='scheduled'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['position_id'], ['positions.id'], ondelete='CASCADE'),
        sa.Index('ix_interviews_application_id', 'application_id'),
        sa.Index('ix_interviews_status', 'status'),
        sa.Index('ix_interviews_scheduled_at', 'scheduled_at'),
    )

    # Create interview slots table (for interviewer availability)
    op.create_table(
        'interview_slots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('interviewer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('available', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['interviewer_id'], ['users.id'], ondelete='CASCADE'),
        sa.Index('ix_interview_slots_interviewer_id', 'interviewer_id'),
        sa.Index('ix_interview_slots_available', 'available'),
    )

    # Create scorecards table
    op.create_table(
        'scorecards',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('interview_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('interviewer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('position_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('competency_scores', postgresql.JSONB(), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('overall_recommendation', sa.String(50), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['interviewer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['position_id'], ['positions.id'], ondelete='CASCADE'),
        sa.Index('ix_scorecards_interview_id', 'interview_id'),
        sa.Index('ix_scorecards_interviewer_id', 'interviewer_id'),
    )

    # Create indices on applications for pipeline queries
    op.create_index('ix_applications_stage', 'applications', ['stage'])
    op.create_index('ix_applications_source', 'applications', ['source'])


def downgrade() -> None:
    op.drop_table('scorecards')
    op.drop_table('interview_slots')
    op.drop_table('interviews')
    op.drop_table('applications')

    stage_enum = postgresql.ENUM('applied', 'phone_screen', 'technical', 'onsite', 'offer', 'hired', 'rejected', name='pipeline_stage')
    stage_enum.drop(op.get_bind())
