"""Saved jobs tracking with custom organization lists

Revision ID: 0028
Revises: 0027
Create Date: 2026-07-08 02:00:00.000000

Enhancements for v3.0:
- Create saved_jobs table for candidate job saves and tracking
- Create saved_jobs_lists table for custom job organization
- Support engagement tracking (view, applied, archived statuses)
- Include denormalized data for performance optimization
- Add encrypted match analysis and notification tracking
- Include performance indices for common query patterns
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0028'
down_revision = '0027'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade: Create saved_jobs tables for job organization and tracking.

    Features:
    - Candidate-curated job saves with custom lists
    - Engagement tracking (viewed, applied, archived)
    - AI match scoring and relevance analysis
    - Notification preferences and history
    - Denormalized company/job data for fast access
    - Performance-optimized indices for filtering and sorting

    Pattern: AsyncAlchemy compatible (psycopg3 driver)
    """
    # Create ENUM types for saved jobs
    saved_job_status_enum = postgresql.ENUM(
        'saved', 'viewed', 'applied', 'archived', 'rejected',
        name='saved_job_status',
        create_type=True
    )
    saved_job_status_enum.create(op.get_bind(), checkfirst=True)

    # --- saved_jobs_lists table ----------------------------------------------
    # Custom job organization lists for candidates
    op.create_table(
        'saved_jobs_lists',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            comment='List owner'
        ),
        sa.Column(
            'name',
            sa.String(255),
            nullable=False,
            comment='List name (e.g., "Dream Jobs", "Remote Only")'
        ),
        sa.Column(
            'description',
            sa.String(500),
            nullable=True,
            comment='List description'
        ),
        sa.Column(
            'icon',
            sa.String(50),
            nullable=True,
            comment='Icon name for UI'
        ),
        sa.Column(
            'color',
            sa.String(7),
            nullable=True,
            comment='Color code for UI (hex)'
        ),
        sa.Column(
            'is_default',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment='System default list'
        ),
        sa.Column(
            'is_shared',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment='Shareable with others (future feature)'
        ),
        sa.Column(
            'job_count',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Denormalized count for performance'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment='Creation timestamp'
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment='Last update'
        ),
        sa.Column(
            'archived_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Archive timestamp'
        ),
        sa.UniqueConstraint('user_id', 'name', name='uq_saved_jobs_lists_user_name'),
    )

    # Create indices for saved_jobs_lists
    op.create_index(
        'ix_saved_jobs_lists_user_id',
        'saved_jobs_lists',
        ['user_id']
    )

    op.create_index(
        'ix_saved_jobs_lists_is_default',
        'saved_jobs_lists',
        ['is_default'],
        postgresql_where=sa.text('is_default = true')
    )

    op.create_index(
        'ix_saved_jobs_lists_created_at',
        'saved_jobs_lists',
        ['user_id', 'created_at']
    )

    # --- saved_jobs table ---------------------------------------------------
    # Candidate-curated job saves with tracking and organization
    op.create_table(
        'saved_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            comment='Candidate who saved the job'
        ),
        sa.Column(
            'position_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('positions.id', ondelete='CASCADE'),
            nullable=False,
            comment='Saved job position'
        ),
        sa.Column(
            'list_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('saved_jobs_lists.id', ondelete='SET NULL'),
            nullable=True,
            comment='Custom list this job belongs to'
        ),
        sa.Column(
            'list_name',
            sa.String(255),
            nullable=True,
            comment='Quick-access list name (denormalized)'
        ),
        sa.Column(
            'notes',
            sa.Text(),
            nullable=True,
            comment="User's personal notes about the job"
        ),
        sa.Column(
            'job_title',
            sa.String(255),
            nullable=True,
            comment='Denormalized job title'
        ),
        sa.Column(
            'company_name',
            sa.String(255),
            nullable=True,
            comment='Denormalized company name'
        ),
        sa.Column(
            'job_url',
            sa.String(2048),
            nullable=True,
            comment='Direct link to job posting'
        ),
        sa.Column(
            'match_score',
            sa.Float(),
            nullable=True,
            comment='AI calculated match percentage'
        ),
        sa.Column(
            'relevance_metadata',
            sa.Text(),
            nullable=True,
            comment='Detailed match analysis (JSON, encrypted)'
        ),
        sa.Column(
            'status',
            sa.String(50),
            nullable=False,
            server_default='saved',
            comment='saved, viewed, applied, archived, rejected'
        ),
        sa.Column(
            'viewed_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When candidate viewed the job'
        ),
        sa.Column(
            'applied_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When application submitted'
        ),
        sa.Column(
            'notify_on_update',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment='Alert on job/company updates'
        ),
        sa.Column(
            'last_notified_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Last notification sent'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment='When job was saved'
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment='Last update timestamp'
        ),
        sa.Column(
            'archived_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When archived (NULL if active)'
        ),
        sa.UniqueConstraint('user_id', 'position_id', name='uq_saved_jobs_user_position'),
    )

    # Create indices for saved_jobs (critical for query performance)
    # Index 1: User's saved jobs
    op.create_index(
        'ix_saved_jobs_user_id',
        'saved_jobs',
        ['user_id']
    )

    # Index 2: Which users saved this job
    op.create_index(
        'ix_saved_jobs_position_id',
        'saved_jobs',
        ['position_id']
    )

    # Index 3: Query by status
    op.create_index(
        'ix_saved_jobs_status',
        'saved_jobs',
        ['status']
    )

    # Index 4: Group by list
    op.create_index(
        'ix_saved_jobs_list_name',
        'saved_jobs',
        ['list_name']
    )

    # Index 5: Timeline queries
    op.create_index(
        'ix_saved_jobs_created_at',
        'saved_jobs',
        ['created_at']
    )

    # Index 6: Archive status
    op.create_index(
        'ix_saved_jobs_archived_at',
        'saved_jobs',
        ['archived_at'],
        postgresql_where=sa.text('archived_at IS NOT NULL')
    )

    # Index 7: Composite for status filtering by user
    op.create_index(
        'ix_saved_jobs_user_status',
        'saved_jobs',
        ['user_id', 'status', 'created_at']
    )

    # Index 8: Composite for user timeline
    op.create_index(
        'ix_saved_jobs_user_created',
        'saved_jobs',
        ['user_id', 'created_at']
    )

    # Index 9: Composite for list management
    op.create_index(
        'ix_saved_jobs_user_list_status',
        'saved_jobs',
        ['user_id', 'list_id', 'status'],
        postgresql_where=sa.text('archived_at IS NULL')
    )


def downgrade() -> None:
    """
    Downgrade: Remove saved jobs tables and associated indices.

    This rollback removes:
    - All saved_jobs records and table
    - All saved_jobs_lists records and table
    - All associated indices and constraints
    """
    # Drop indices from saved_jobs table
    op.drop_index('ix_saved_jobs_user_list_status', table_name='saved_jobs')
    op.drop_index('ix_saved_jobs_user_created', table_name='saved_jobs')
    op.drop_index('ix_saved_jobs_user_status', table_name='saved_jobs')
    op.drop_index('ix_saved_jobs_archived_at', table_name='saved_jobs')
    op.drop_index('ix_saved_jobs_created_at', table_name='saved_jobs')
    op.drop_index('ix_saved_jobs_list_name', table_name='saved_jobs')
    op.drop_index('ix_saved_jobs_status', table_name='saved_jobs')
    op.drop_index('ix_saved_jobs_position_id', table_name='saved_jobs')
    op.drop_index('ix_saved_jobs_user_id', table_name='saved_jobs')

    # Drop saved_jobs table (this also removes unique constraints automatically)
    op.drop_table('saved_jobs')

    # Drop indices from saved_jobs_lists table
    op.drop_index('ix_saved_jobs_lists_created_at', table_name='saved_jobs_lists')
    op.drop_index('ix_saved_jobs_lists_is_default', table_name='saved_jobs_lists')
    op.drop_index('ix_saved_jobs_lists_user_id', table_name='saved_jobs_lists')

    # Drop saved_jobs_lists table
    op.drop_table('saved_jobs_lists')

    # Drop ENUM type
    op.execute('DROP TYPE IF EXISTS saved_job_status CASCADE')
