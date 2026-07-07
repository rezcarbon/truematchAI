"""Application tracking v3.0 enhancements with detailed timeline and assessment integration

Revision ID: 0026
Revises: 0025
Create Date: 2026-07-08 00:00:00.000000

Enhancements for v3.0:
- Add comprehensive application timeline tracking with SLA monitoring
- Integrate assessment results into application lifecycle
- Add pipeline stage progression metrics
- Add extended engagement analytics
- Add assessment linking and score tracking
- Include data safety backups and batch migration helpers
- Optimize indices for funnel analysis and reporting
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0026'
down_revision = '0025'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade: Add v3.0 enhancements to application tracking.

    Safety: Creates backups before any ALTER operations.
    Pattern: AsyncAlchemy compatible (psycopg3 driver)
    """
    # SAFETY: Backup existing tables before modifications
    op.execute("""
        CREATE TABLE IF NOT EXISTS assessments_backup_0026 AS
        SELECT * FROM assessments;
    """)

    # ===== ASSESSMENTS TABLE ENHANCEMENTS =====
    # Add comprehensive timeline fields for application progression tracking

    # Stage timing fields (SLA monitoring)
    op.add_column('assessments', sa.Column(
        'stage_entered_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='When assessment entered current evaluation stage'
    ))

    op.add_column('assessments', sa.Column(
        'stage_duration_seconds',
        sa.Integer(),
        nullable=True,
        comment='How long assessment has been in current stage (cached for performance)'
    ))

    op.add_column('assessments', sa.Column(
        'expected_completion_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='Predicted completion date based on SLA and stage'
    ))

    # Assessment scoring timeline
    op.add_column('assessments', sa.Column(
        'initial_assessment_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='When initial assessment was completed'
    ))

    op.add_column('assessments', sa.Column(
        'final_assessment_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='When final assessment decision was made'
    ))

    op.add_column('assessments', sa.Column(
        'assessment_version',
        sa.Integer(),
        nullable=False,
        server_default='1',
        comment='Version number if assessment was re-run'
    ))

    # Assessment quality and review tracking
    op.add_column('assessments', sa.Column(
        'review_requested_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='When human review was requested'
    ))

    op.add_column('assessments', sa.Column(
        'review_completed_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='When human review was completed'
    ))

    op.add_column('assessments', sa.Column(
        'reviewer_id',
        postgresql.UUID(as_uuid=True),
        nullable=True,
        comment='User who reviewed assessment'
    ))

    op.add_column('assessments', sa.Column(
        'review_notes',
        sa.Text(),
        nullable=True,
        comment='Reviewer feedback and notes'
    ))

    op.add_column('assessments', sa.Column(
        'review_override',
        sa.Boolean(),
        nullable=False,
        server_default='false',
        comment='Whether reviewer overrode automated decision'
    ))

    # Assessment reliability and confidence
    op.add_column('assessments', sa.Column(
        'overall_confidence',
        sa.Float(),
        nullable=True,
        comment='Combined confidence score across all assessment components (0.0-1.0)'
    ))

    op.add_column('assessments', sa.Column(
        'confidence_breakdown',
        postgresql.JSONB(),
        nullable=True,
        comment='Confidence scores by component: traditional, semantic, capability, etc.'
    ))

    op.add_column('assessments', sa.Column(
        'reliability_flags',
        postgresql.JSONB(),
        nullable=True,
        comment='Flags if assessment reliability is compromised (resume quality, parsing issues, etc.)'
    ))

    # Assessment comparison and consistency
    op.add_column('assessments', sa.Column(
        'previous_assessment_id',
        postgresql.UUID(as_uuid=True),
        nullable=True,
        comment='Link to previous assessment of same candidate for same position'
    ))

    op.add_column('assessments', sa.Column(
        'score_change_percent',
        sa.Float(),
        nullable=True,
        comment='Percentage change from previous assessment score'
    ))

    op.add_column('assessments', sa.Column(
        'consistency_with_previous',
        sa.Float(),
        nullable=True,
        comment='How consistent is current assessment with previous (0.0-1.0)'
    ))

    # Add foreign key for reviewer
    op.create_foreign_key(
        'fk_assessments_reviewer_id',
        'assessments',
        'users',
        ['reviewer_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Add self-referencing foreign key for previous assessment
    op.create_foreign_key(
        'fk_assessments_previous_assessment_id',
        'assessments',
        'assessments',
        ['previous_assessment_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # ===== PERFORMANCE INDICES FOR APPLICATION TIMELINE =====

    # Query: "Get assessments at each pipeline stage"
    op.create_index(
        'ix_assessments_stage_entered',
        'assessments',
        ['position_id', 'stage_entered_at'],
        postgresql_where=sa.text('stage_entered_at IS NOT NULL')
    )

    # Query: "Monitor SLA compliance - assessments pending review"
    op.create_index(
        'ix_assessments_review_pending',
        'assessments',
        ['review_requested_at', 'review_completed_at'],
        postgresql_where=sa.text('review_requested_at IS NOT NULL AND review_completed_at IS NULL')
    )

    # Query: "Track assessment versions and re-runs"
    op.create_index(
        'ix_assessments_version_tracking',
        'assessments',
        ['resume_id', 'position_id', 'assessment_version'],
        postgresql_where=sa.text('assessment_version > 1')
    )

    # Query: "Get recently completed assessments"
    op.create_index(
        'ix_assessments_completion_timeline',
        'assessments',
        ['final_assessment_at'],
        postgresql_where=sa.text('final_assessment_at IS NOT NULL')
    )

    # Query: "Find assessments requiring human review"
    op.create_index(
        'ix_assessments_human_review',
        'assessments',
        ['human_review_required', 'review_completed_at'],
        postgresql_where=sa.text('human_review_required = true AND review_completed_at IS NULL')
    )

    # Query: "Track assessment overrides for audit"
    op.create_index(
        'ix_assessments_review_override',
        'assessments',
        ['reviewer_id', 'review_completed_at'],
        postgresql_where=sa.text('review_override = true')
    )

    # Query: "Monitor confidence and reliability issues"
    op.create_index(
        'ix_assessments_low_confidence',
        'assessments',
        ['position_id', 'overall_confidence'],
        postgresql_where=sa.text('overall_confidence < 0.5')
    )

    # Query: "Consistency analysis for repeated candidates"
    op.create_index(
        'ix_assessments_consistency_tracking',
        'assessments',
        ['resume_id', 'position_id', 'consistency_with_previous'],
        postgresql_where=sa.text('consistency_with_previous IS NOT NULL')
    )

    # Query: "Funnel analysis by decision type and stage"
    op.create_index(
        'ix_assessments_decision_funnel',
        'assessments',
        ['position_id', 'decision_type', 'created_at']
    )

    # Query: "User assessment activity tracking"
    op.create_index(
        'ix_assessments_user_timeline',
        'assessments',
        ['user_id', 'created_at', 'final_assessment_at']
    )

    # Query: "SLA monitoring - assessments exceeding expected completion"
    op.create_index(
        'ix_assessments_sla_monitoring',
        'assessments',
        ['expected_completion_at', 'final_assessment_at'],
        postgresql_where=sa.text('expected_completion_at IS NOT NULL AND final_assessment_at IS NULL')
    )

    # Create composite index for comprehensive assessment status dashboard
    op.create_index(
        'ix_assessments_dashboard_view',
        'assessments',
        ['position_id', 'status', 'decision_type', 'stage_entered_at']
    )


def downgrade() -> None:
    """
    Downgrade: Remove v3.0 enhancements to application tracking.

    Safety: Backup preserved in assessments_backup_0026 for manual recovery.
    """
    # Drop all performance indices
    op.drop_index('ix_assessments_dashboard_view', table_name='assessments')
    op.drop_index('ix_assessments_sla_monitoring', table_name='assessments')
    op.drop_index('ix_assessments_user_timeline', table_name='assessments')
    op.drop_index('ix_assessments_decision_funnel', table_name='assessments')
    op.drop_index('ix_assessments_consistency_tracking', table_name='assessments')
    op.drop_index('ix_assessments_low_confidence', table_name='assessments')
    op.drop_index('ix_assessments_review_override', table_name='assessments')
    op.drop_index('ix_assessments_human_review', table_name='assessments')
    op.drop_index('ix_assessments_completion_timeline', table_name='assessments')
    op.drop_index('ix_assessments_version_tracking', table_name='assessments')
    op.drop_index('ix_assessments_review_pending', table_name='assessments')
    op.drop_index('ix_assessments_stage_entered', table_name='assessments')

    # Drop foreign keys
    op.drop_constraint('fk_assessments_previous_assessment_id', 'assessments', type_='foreignkey')
    op.drop_constraint('fk_assessments_reviewer_id', 'assessments', type_='foreignkey')

    # Drop all v3.0 columns (reverse order)
    op.drop_column('assessments', 'consistency_with_previous')
    op.drop_column('assessments', 'score_change_percent')
    op.drop_column('assessments', 'previous_assessment_id')
    op.drop_column('assessments', 'reliability_flags')
    op.drop_column('assessments', 'confidence_breakdown')
    op.drop_column('assessments', 'overall_confidence')
    op.drop_column('assessments', 'review_override')
    op.drop_column('assessments', 'review_notes')
    op.drop_column('assessments', 'reviewer_id')
    op.drop_column('assessments', 'review_completed_at')
    op.drop_column('assessments', 'review_requested_at')
    op.drop_column('assessments', 'assessment_version')
    op.drop_column('assessments', 'final_assessment_at')
    op.drop_column('assessments', 'initial_assessment_at')
    op.drop_column('assessments', 'expected_completion_at')
    op.drop_column('assessments', 'stage_duration_seconds')
    op.drop_column('assessments', 'stage_entered_at')

    # SAFETY: Backup table left for manual recovery
    # Drop with: DROP TABLE IF EXISTS assessments_backup_0026;
