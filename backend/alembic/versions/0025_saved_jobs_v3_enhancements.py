"""Saved jobs v3.0 enhancements with list management and recommendation tracking

Revision ID: 0025
Revises: 0024
Create Date: 2026-07-08 00:00:00.000000

Enhancements for v3.0:
- Add recommendation engine integration tracking
- Add job market insights (salary trends, market demand)
- Add advanced list organization features
- Add notification scheduling and analytics
- Add query performance indices for job discovery flows
- Include data safety backups before schema changes
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0025'
down_revision = '0024'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade: Add v3.0 enhancements to saved jobs.

    Safety: Creates backups before any ALTER operations.
    Pattern: AsyncAlchemy compatible (psycopg3 driver)
    """
    # SAFETY: Backup existing tables before modifications
    op.execute("""
        CREATE TABLE IF NOT EXISTS saved_jobs_backup_0025 AS
        SELECT * FROM saved_jobs;
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS saved_jobs_lists_backup_0025 AS
        SELECT * FROM saved_jobs_lists;
    """)

    # ===== SAVED_JOBS ENHANCEMENTS =====

    # Add recommendation engine tracking
    op.add_column('saved_jobs', sa.Column(
        'recommendation_source',
        sa.String(100),
        nullable=True,
        comment='Source of recommendation (search, ml_engine, recruiter, ats_sync)'
    ))

    op.add_column('saved_jobs', sa.Column(
        'recommendation_score',
        sa.Float(),
        nullable=True,
        comment='ML recommendation confidence score (0.0-1.0)'
    ))

    op.add_column('saved_jobs', sa.Column(
        'recommendation_reason',
        sa.Text(),
        nullable=True,
        comment='Human-readable explanation of recommendation'
    ))

    # Add job market insights
    op.add_column('saved_jobs', sa.Column(
        'salary_min',
        sa.Integer(),
        nullable=True,
        comment='Minimum salary range in job posting'
    ))

    op.add_column('saved_jobs', sa.Column(
        'salary_max',
        sa.Integer(),
        nullable=True,
        comment='Maximum salary range in job posting'
    ))

    op.add_column('saved_jobs', sa.Column(
        'market_demand_level',
        sa.String(50),
        nullable=True,
        comment='Market demand: high, medium, low (for similar roles)'
    ))

    op.add_column('saved_jobs', sa.Column(
        'similar_jobs_count',
        sa.Integer(),
        nullable=True,
        server_default='0',
        comment='Count of similar open positions'
    ))

    # Add advanced engagement tracking
    op.add_column('saved_jobs', sa.Column(
        'interest_level',
        sa.String(50),
        nullable=False,
        server_default='medium',
        comment='User interest: high, medium, low'
    ))

    op.add_column('saved_jobs', sa.Column(
        'reason_saved',
        sa.String(500),
        nullable=True,
        comment='Why user saved this job'
    ))

    op.add_column('saved_jobs', sa.Column(
        'times_viewed',
        sa.Integer(),
        nullable=False,
        server_default='0',
        comment='Count of how many times user viewed this saved job'
    ))

    op.add_column('saved_jobs', sa.Column(
        'last_viewed_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='Timestamp of last view'
    ))

    # Add notification management for saved jobs
    op.add_column('saved_jobs', sa.Column(
        'notification_schedule',
        sa.String(50),
        nullable=False,
        server_default='daily',
        comment='Notification frequency: immediate, daily, weekly, none'
    ))

    op.add_column('saved_jobs', sa.Column(
        'next_notification_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='When next notification about this job should be sent'
    ))

    op.add_column('saved_jobs', sa.Column(
        'notification_count',
        sa.Integer(),
        nullable=False,
        server_default='0',
        comment='Count of notifications sent for this job'
    ))

    # ===== SAVED_JOBS_LISTS ENHANCEMENTS =====

    # Add list organization and sharing features
    op.add_column('saved_jobs_lists', sa.Column(
        'description_extended',
        sa.Text(),
        nullable=True,
        comment='Extended description of the list'
    ))

    op.add_column('saved_jobs_lists', sa.Column(
        'sort_order',
        sa.Integer(),
        nullable=False,
        server_default='0',
        comment='Display order for lists in UI'
    ))

    op.add_column('saved_jobs_lists', sa.Column(
        'is_system_list',
        sa.Boolean(),
        nullable=False,
        server_default='false',
        comment='Whether this is a system-managed list (e.g., Recently Viewed)'
    ))

    op.add_column('saved_jobs_lists', sa.Column(
        'last_job_added_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='Timestamp of last job added to this list'
    ))

    # Add list statistics and analytics
    op.add_column('saved_jobs_lists', sa.Column(
        'total_applications',
        sa.Integer(),
        nullable=False,
        server_default='0',
        comment='Count of jobs in list that user applied to'
    ))

    op.add_column('saved_jobs_lists', sa.Column(
        'avg_match_score',
        sa.Float(),
        nullable=True,
        comment='Average match score of jobs in this list'
    ))

    # ===== PERFORMANCE INDICES FOR V3.0 =====

    # Query: "Get saved jobs with recommendations for user"
    op.create_index(
        'ix_saved_jobs_recommendation_score',
        'saved_jobs',
        ['user_id', 'recommendation_score'],
        postgresql_where=sa.text('recommendation_score IS NOT NULL')
    )

    # Query: "Filter by market demand and salary range"
    op.create_index(
        'ix_saved_jobs_market_insights',
        'saved_jobs',
        ['user_id', 'market_demand_level'],
        postgresql_where=sa.text('market_demand_level IS NOT NULL')
    )

    # Query: "Find high-interest jobs by user"
    op.create_index(
        'ix_saved_jobs_interest_level',
        'saved_jobs',
        ['user_id', 'interest_level'],
        postgresql_where=sa.text('interest_level != \'low\'')
    )

    # Query: "Check notification schedule for batch processing"
    op.create_index(
        'ix_saved_jobs_notification_schedule',
        'saved_jobs',
        ['notification_schedule', 'next_notification_at'],
        postgresql_where=sa.text('notification_schedule != \'none\'')
    )

    # Query: "Get recently viewed saved jobs"
    op.create_index(
        'ix_saved_jobs_last_viewed',
        'saved_jobs',
        ['user_id', 'last_viewed_at'],
        postgresql_where=sa.text('last_viewed_at IS NOT NULL')
    )

    # Query: "Analytics on list engagement"
    op.create_index(
        'ix_saved_jobs_lists_engagement',
        'saved_jobs_lists',
        ['user_id', 'last_job_added_at'],
        postgresql_where=sa.text('last_job_added_at IS NOT NULL')
    )

    # Query: "Find system lists for UI rendering"
    op.create_index(
        'ix_saved_jobs_lists_system',
        'saved_jobs_lists',
        ['user_id', 'is_system_list'],
        postgresql_where=sa.text('is_system_list = true')
    )

    # Query: "Sort lists by user preference"
    op.create_index(
        'ix_saved_jobs_lists_sort_order',
        'saved_jobs_lists',
        ['user_id', 'sort_order']
    )


def downgrade() -> None:
    """
    Downgrade: Remove v3.0 enhancements to saved jobs.

    Safety: Backups preserved in saved_jobs_backup_0025 and saved_jobs_lists_backup_0025.
    """
    # Drop list organization indices
    op.drop_index('ix_saved_jobs_lists_sort_order', table_name='saved_jobs_lists')
    op.drop_index('ix_saved_jobs_lists_system', table_name='saved_jobs_lists')
    op.drop_index('ix_saved_jobs_lists_engagement', table_name='saved_jobs_lists')

    # Drop saved_jobs indices
    op.drop_index('ix_saved_jobs_last_viewed', table_name='saved_jobs')
    op.drop_index('ix_saved_jobs_notification_schedule', table_name='saved_jobs')
    op.drop_index('ix_saved_jobs_interest_level', table_name='saved_jobs')
    op.drop_index('ix_saved_jobs_market_insights', table_name='saved_jobs')
    op.drop_index('ix_saved_jobs_recommendation_score', table_name='saved_jobs')

    # Drop saved_jobs_lists columns (reverse order)
    op.drop_column('saved_jobs_lists', 'avg_match_score')
    op.drop_column('saved_jobs_lists', 'total_applications')
    op.drop_column('saved_jobs_lists', 'last_job_added_at')
    op.drop_column('saved_jobs_lists', 'is_system_list')
    op.drop_column('saved_jobs_lists', 'sort_order')
    op.drop_column('saved_jobs_lists', 'description_extended')

    # Drop saved_jobs columns (reverse order)
    op.drop_column('saved_jobs', 'notification_count')
    op.drop_column('saved_jobs', 'next_notification_at')
    op.drop_column('saved_jobs', 'notification_schedule')
    op.drop_column('saved_jobs', 'last_viewed_at')
    op.drop_column('saved_jobs', 'times_viewed')
    op.drop_column('saved_jobs', 'reason_saved')
    op.drop_column('saved_jobs', 'interest_level')
    op.drop_column('saved_jobs', 'similar_jobs_count')
    op.drop_column('saved_jobs', 'market_demand_level')
    op.drop_column('saved_jobs', 'salary_max')
    op.drop_column('saved_jobs', 'salary_min')
    op.drop_column('saved_jobs', 'recommendation_reason')
    op.drop_column('saved_jobs', 'recommendation_score')
    op.drop_column('saved_jobs', 'recommendation_source')

    # SAFETY: Backup tables left for manual recovery
    # Drop with: DROP TABLE IF EXISTS saved_jobs_backup_0025, saved_jobs_lists_backup_0025;
