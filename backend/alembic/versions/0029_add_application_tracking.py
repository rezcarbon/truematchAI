"""Application tracking with detailed events and feedback

Revision ID: 0029
Revises: 0028
Create Date: 2026-07-08 03:00:00.000000

Enhancements for v3.0:
- Create application_events table for detailed activity logging
- Create application_feedback table for structured interview feedback
- Add comprehensive timeline tracking for applications
- Support rejection reason tracking and encrypted feedback storage
- Add resume version linking for version-specific applications
- Include performance indices for funnel analysis and reporting
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0029'
down_revision = '0028'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade: Create application tracking tables with detailed event logging.

    Features:
    - Complete audit trail of all application activity
    - Detailed pipeline stage tracking with SLA monitoring
    - Structured feedback collection from multiple interviewers
    - Engagement metrics (view, message, response tracking)
    - PII protection with encrypted sensitive fields
    - Performance-optimized indices for funnel analytics

    Pattern: AsyncAlchemy compatible (psycopg3 driver)
    """
    # Create ENUM types for application tracking
    event_type_enum = postgresql.ENUM(
        'status_changed', 'message_sent', 'message_received', 'viewed',
        'interview_scheduled', 'interview_completed', 'offer_extended',
        'offer_accepted', 'offer_rejected', 'rejected', 'withdrawn',
        'feedback_provided', 'reassigned', 'flagged', 'unflagged',
        name='application_event_type',
        create_type=True
    )
    event_type_enum.create(op.get_bind(), checkfirst=True)

    actor_type_enum = postgresql.ENUM(
        'system', 'user', 'automation', 'ats_sync',
        name='application_actor_type',
        create_type=True
    )
    actor_type_enum.create(op.get_bind(), checkfirst=True)

    feedback_stage_enum = postgresql.ENUM(
        'phone_screen', 'technical', 'onsite', 'final', 'other',
        name='application_feedback_stage',
        create_type=True
    )
    feedback_stage_enum.create(op.get_bind(), checkfirst=True)

    recommendation_enum = postgresql.ENUM(
        'proceed', 'maybe', 'reject',
        name='application_recommendation',
        create_type=True
    )
    recommendation_enum.create(op.get_bind(), checkfirst=True)

    priority_enum = postgresql.ENUM(
        'high', 'normal', 'low',
        name='application_priority',
        create_type=True
    )
    priority_enum.create(op.get_bind(), checkfirst=True)

    # --- application_events table -------------------------------------------
    # Detailed activity log for every application lifecycle event
    op.create_table(
        'application_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'application_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('applications.id', ondelete='CASCADE'),
            nullable=False,
            comment='Associated application'
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            comment='User context'
        ),
        sa.Column(
            'event_type',
            sa.String(50),
            nullable=False,
            comment='Type of event (status_changed, message_sent, etc.)'
        ),
        sa.Column(
            'event_data',
            postgresql.JSONB(),
            nullable=True,
            comment='Flexible event metadata'
        ),
        sa.Column(
            'description',
            sa.String(500),
            nullable=True,
            comment='Human-readable event description'
        ),
        sa.Column(
            'triggered_by_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
            comment='User who triggered event'
        ),
        sa.Column(
            'actor_type',
            sa.String(50),
            nullable=False,
            server_default='system',
            comment='Who triggered (system, user, automation, ats_sync)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment='Event timestamp'
        ),
    )

    # Create indices for application_events
    op.create_index(
        'ix_application_events_application_id',
        'application_events',
        ['application_id']
    )

    op.create_index(
        'ix_application_events_user_id',
        'application_events',
        ['user_id']
    )

    op.create_index(
        'ix_application_events_event_type',
        'application_events',
        ['event_type']
    )

    op.create_index(
        'ix_application_events_created_at',
        'application_events',
        ['created_at']
    )

    op.create_index(
        'ix_application_events_triggered_by_id',
        'application_events',
        ['triggered_by_id']
    )

    op.create_index(
        'ix_application_events_app_type',
        'application_events',
        ['application_id', 'event_type', 'created_at']
    )

    op.create_index(
        'ix_application_events_app_created',
        'application_events',
        ['application_id', 'created_at']
    )

    # --- application_feedback table -----------------------------------------
    # Structured feedback from interviews and assessments
    op.create_table(
        'application_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'application_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('applications.id', ondelete='CASCADE'),
            nullable=False,
            comment='Associated application'
        ),
        sa.Column(
            'feedback_stage',
            sa.String(50),
            nullable=False,
            comment='Pipeline stage (phone_screen, technical, onsite, etc.)'
        ),
        sa.Column(
            'overall_rating',
            sa.Integer(),
            nullable=True,
            comment='1-5 scale rating'
        ),
        sa.Column(
            'feedback_text',
            sa.Text(),
            nullable=True,
            comment='Interviewer notes (encrypted)'
        ),
        sa.Column(
            'structured_feedback',
            postgresql.JSONB(),
            nullable=True,
            comment='Structured rating criteria'
        ),
        sa.Column(
            'provided_by_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            comment='Interviewer/evaluator'
        ),
        sa.Column(
            'provided_by_name',
            sa.String(255),
            nullable=True,
            comment='Cached name for performance'
        ),
        sa.Column(
            'recommendation',
            sa.String(50),
            nullable=True,
            comment='proceed, maybe, reject'
        ),
        sa.Column(
            'confidence_score',
            sa.Float(),
            nullable=True,
            comment='Confidence in recommendation (0.0-1.0)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment='Submission time'
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment='Last update time'
        ),
    )

    # Create indices for application_feedback
    op.create_index(
        'ix_application_feedback_application_id',
        'application_feedback',
        ['application_id']
    )

    op.create_index(
        'ix_application_feedback_stage',
        'application_feedback',
        ['feedback_stage']
    )

    op.create_index(
        'ix_application_feedback_provided_by_id',
        'application_feedback',
        ['provided_by_id']
    )

    op.create_index(
        'ix_application_feedback_recommendation',
        'application_feedback',
        ['recommendation']
    )

    op.create_index(
        'ix_application_feedback_created_at',
        'application_feedback',
        ['created_at']
    )

    op.create_index(
        'ix_application_feedback_app_stage',
        'application_feedback',
        ['application_id', 'feedback_stage']
    )

    # --- Add columns to applications table -----------------------------------
    # Resume version tracking
    op.add_column('applications', sa.Column(
        'resume_version_id',
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey('resume_versions.id', ondelete='SET NULL'),
        nullable=True,
        comment='Specific resume version applied with'
    ))

    op.create_index(
        'ix_applications_resume_version_id',
        'applications',
        ['resume_version_id']
    )

    # Timeline tracking
    op.add_column('applications', sa.Column(
        'viewed_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='When recruiter first viewed'
    ))

    op.add_column('applications', sa.Column(
        'interview_scheduled_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='When interview was booked'
    ))

    op.add_column('applications', sa.Column(
        'rejected_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='When rejection sent'
    ))

    op.add_column('applications', sa.Column(
        'withdrawn_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='When candidate withdrew'
    ))

    op.add_column('applications', sa.Column(
        'offer_extended_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='When offer sent'
    ))

    op.add_column('applications', sa.Column(
        'offer_accepted_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='When offer accepted'
    ))

    # Rejection handling
    op.add_column('applications', sa.Column(
        'rejection_reason',
        sa.Text(),
        nullable=True,
        comment='Why candidate was rejected (encrypted)'
    ))

    op.add_column('applications', sa.Column(
        'rejection_feedback',
        sa.Text(),
        nullable=True,
        comment='Detailed feedback (encrypted)'
    ))

    op.add_column('applications', sa.Column(
        'can_reapply',
        sa.Boolean(),
        nullable=True,
        server_default=sa.true(),
        comment='Whether candidate can reapply'
    ))

    op.add_column('applications', sa.Column(
        'reapply_after',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='Earliest reapplication date'
    ))

    # Scoring & Assessment
    op.add_column('applications', sa.Column(
        'initial_match_score',
        sa.Float(),
        nullable=True,
        comment='Initial AI match score'
    ))

    op.add_column('applications', sa.Column(
        'current_match_score',
        sa.Float(),
        nullable=True,
        comment='Updated match score'
    ))

    op.add_column('applications', sa.Column(
        'fit_assessment',
        postgresql.JSONB(),
        nullable=True,
        comment='Structured fit analysis'
    ))

    # Communication
    op.add_column('applications', sa.Column(
        'messages_count',
        sa.Integer(),
        nullable=False,
        server_default='0',
        comment='Total messages exchanged'
    ))

    op.add_column('applications', sa.Column(
        'last_message_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='Last message timestamp'
    ))

    op.add_column('applications', sa.Column(
        'requires_response',
        sa.Boolean(),
        nullable=False,
        server_default=sa.false(),
        comment='Awaiting candidate response'
    ))

    # Application customization
    op.add_column('applications', sa.Column(
        'custom_cover_letter',
        sa.Text(),
        nullable=True,
        comment="Candidate's cover letter (encrypted)"
    ))

    op.add_column('applications', sa.Column(
        'application_answers',
        postgresql.JSONB(),
        nullable=True,
        comment='Answers to custom form questions'
    ))

    # Admin & Organization
    op.add_column('applications', sa.Column(
        'stage_notes',
        sa.String(500),
        nullable=True,
        comment='Notes about current stage'
    ))

    op.add_column('applications', sa.Column(
        'priority',
        sa.String(50),
        nullable=False,
        server_default='normal',
        comment='high, normal, low'
    ))

    op.add_column('applications', sa.Column(
        'is_flagged',
        sa.Boolean(),
        nullable=False,
        server_default=sa.false(),
        comment='Flagged for attention'
    ))

    op.add_column('applications', sa.Column(
        'assigned_to_id',
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment='Assigned recruiter'
    ))

    # Create additional indices for applications table
    op.create_index(
        'ix_applications_assigned_to_id',
        'applications',
        ['assigned_to_id']
    )

    op.create_index(
        'ix_applications_viewed_at',
        'applications',
        ['viewed_at']
    )

    op.create_index(
        'ix_applications_interview_scheduled_at',
        'applications',
        ['interview_scheduled_at']
    )

    op.create_index(
        'ix_applications_rejected_at',
        'applications',
        ['rejected_at']
    )

    op.create_index(
        'ix_applications_priority',
        'applications',
        ['priority']
    )

    op.create_index(
        'ix_applications_is_flagged',
        'applications',
        ['is_flagged'],
        postgresql_where=sa.text('is_flagged = true')
    )

    op.create_index(
        'ix_applications_requires_response',
        'applications',
        ['requires_response'],
        postgresql_where=sa.text('requires_response = true')
    )

    op.create_index(
        'ix_applications_position_stage',
        'applications',
        ['position_id', 'status']
    )

    op.create_index(
        'ix_applications_stage_updated',
        'applications',
        ['status', 'updated_at']
    )

    op.create_index(
        'ix_applications_user_priority',
        'applications',
        ['user_id', 'priority', 'created_at']
    )


def downgrade() -> None:
    """
    Downgrade: Remove application tracking tables and columns.

    This rollback removes:
    - All application_events records and table
    - All application_feedback records and table
    - All new columns from applications table
    - All associated indices
    """
    # Drop indices from applications table (new ones)
    op.drop_index('ix_applications_user_priority', table_name='applications')
    op.drop_index('ix_applications_stage_updated', table_name='applications')
    op.drop_index('ix_applications_position_stage', table_name='applications')
    op.drop_index('ix_applications_requires_response', table_name='applications')
    op.drop_index('ix_applications_is_flagged', table_name='applications')
    op.drop_index('ix_applications_priority', table_name='applications')
    op.drop_index('ix_applications_rejected_at', table_name='applications')
    op.drop_index('ix_applications_interview_scheduled_at', table_name='applications')
    op.drop_index('ix_applications_viewed_at', table_name='applications')
    op.drop_index('ix_applications_assigned_to_id', table_name='applications')

    # Drop columns from applications table (in reverse order of addition)
    op.drop_column('applications', 'assigned_to_id')
    op.drop_column('applications', 'is_flagged')
    op.drop_column('applications', 'priority')
    op.drop_column('applications', 'stage_notes')
    op.drop_column('applications', 'application_answers')
    op.drop_column('applications', 'custom_cover_letter')
    op.drop_column('applications', 'requires_response')
    op.drop_column('applications', 'last_message_at')
    op.drop_column('applications', 'messages_count')
    op.drop_column('applications', 'fit_assessment')
    op.drop_column('applications', 'current_match_score')
    op.drop_column('applications', 'initial_match_score')
    op.drop_column('applications', 'reapply_after')
    op.drop_column('applications', 'can_reapply')
    op.drop_column('applications', 'rejection_feedback')
    op.drop_column('applications', 'rejection_reason')
    op.drop_column('applications', 'offer_accepted_at')
    op.drop_column('applications', 'offer_extended_at')
    op.drop_column('applications', 'withdrawn_at')
    op.drop_column('applications', 'rejected_at')
    op.drop_column('applications', 'interview_scheduled_at')
    op.drop_column('applications', 'viewed_at')
    op.drop_index('ix_applications_resume_version_id', table_name='applications')
    op.drop_column('applications', 'resume_version_id')

    # Drop indices from application_feedback table
    op.drop_index('ix_application_feedback_app_stage', table_name='application_feedback')
    op.drop_index('ix_application_feedback_created_at', table_name='application_feedback')
    op.drop_index('ix_application_feedback_recommendation', table_name='application_feedback')
    op.drop_index('ix_application_feedback_provided_by_id', table_name='application_feedback')
    op.drop_index('ix_application_feedback_stage', table_name='application_feedback')
    op.drop_index('ix_application_feedback_application_id', table_name='application_feedback')

    # Drop application_feedback table
    op.drop_table('application_feedback')

    # Drop indices from application_events table
    op.drop_index('ix_application_events_app_created', table_name='application_events')
    op.drop_index('ix_application_events_app_type', table_name='application_events')
    op.drop_index('ix_application_events_triggered_by_id', table_name='application_events')
    op.drop_index('ix_application_events_created_at', table_name='application_events')
    op.drop_index('ix_application_events_event_type', table_name='application_events')
    op.drop_index('ix_application_events_user_id', table_name='application_events')
    op.drop_index('ix_application_events_application_id', table_name='application_events')

    # Drop application_events table
    op.drop_table('application_events')

    # Drop ENUM types
    op.execute('DROP TYPE IF EXISTS application_priority CASCADE')
    op.execute('DROP TYPE IF EXISTS application_recommendation CASCADE')
    op.execute('DROP TYPE IF EXISTS application_feedback_stage CASCADE')
    op.execute('DROP TYPE IF EXISTS application_actor_type CASCADE')
    op.execute('DROP TYPE IF EXISTS application_event_type CASCADE')
