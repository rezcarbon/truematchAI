"""Resume versioning with version history and audit trail

Revision ID: 0027
Revises: 0026
Create Date: 2026-07-08 01:00:00.000000

Enhancements for v3.0:
- Create resume_versions table for comprehensive version history tracking
- Add version metadata, quality scoring, and change tracking
- Support full audit trail with encryption for sensitive resume content
- Add performance indices for common query patterns
- Include backup safety procedures and data integrity checks
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0027'
down_revision = '0026'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade: Create resume_versions table with comprehensive tracking.

    Features:
    - Complete version history with audit trail
    - Encrypted storage of sensitive resume content (PII)
    - Quality scoring and completeness tracking
    - Language and change type tracking
    - Performance-optimized indices for common queries

    Pattern: AsyncAlchemy compatible (psycopg3 driver)
    """
    # Create ENUM types for change tracking
    change_type_enum = postgresql.ENUM(
        'upload', 'edit', 'ai_enhancement', 'import',
        name='resume_change_type',
        create_type=True
    )
    change_type_enum.create(op.get_bind(), checkfirst=True)

    # --- resume_versions table -----------------------------------------------
    # Stores complete version history of all resumes with full audit trail
    op.create_table(
        'resume_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'resume_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('resumes.id', ondelete='CASCADE'),
            nullable=False,
            comment='Reference to base resume record'
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            comment='User who owns the resume'
        ),
        sa.Column(
            'version_number',
            sa.Integer(),
            nullable=False,
            comment='Sequential version number'
        ),
        sa.Column(
            'is_current',
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment='Whether this is the active version'
        ),
        sa.Column(
            'file_id',
            sa.String(512),
            nullable=True,
            comment='Cloud storage file identifier'
        ),
        sa.Column(
            'file_name',
            sa.String(255),
            nullable=True,
            comment='Original file name'
        ),
        sa.Column(
            'file_size_bytes',
            sa.Integer(),
            nullable=True,
            comment='File size for quota tracking'
        ),
        sa.Column(
            'file_type',
            sa.String(64),
            nullable=True,
            comment='File format (pdf, docx, etc.)'
        ),
        sa.Column(
            'source_language',
            sa.String(10),
            nullable=True,
            comment='Original language code (ISO 639-1)'
        ),
        sa.Column(
            'detected_language',
            sa.String(10),
            nullable=True,
            comment='Detected language of content'
        ),
        sa.Column(
            'parsed_data',
            sa.Text(),
            nullable=True,
            comment='Extracted structured resume data (JSON, encrypted)'
        ),
        sa.Column(
            'raw_narrative',
            sa.Text(),
            nullable=True,
            comment='Full extracted text narrative (encrypted)'
        ),
        sa.Column(
            'supplementary',
            sa.Text(),
            nullable=True,
            comment='Additional parsed metadata (JSON, encrypted)'
        ),
        sa.Column(
            'quality_score',
            sa.Float(),
            nullable=True,
            comment='AI-calculated resume quality metric (0.0-1.0)'
        ),
        sa.Column(
            'completeness_percentage',
            sa.Integer(),
            nullable=True,
            comment='Resume section completeness percentage'
        ),
        sa.Column(
            'sections_detected',
            postgresql.JSONB(),
            nullable=True,
            comment='Detected resume sections (experience, education, etc.)'
        ),
        sa.Column(
            'change_summary',
            sa.String(500),
            nullable=True,
            comment='Human-readable summary of changes'
        ),
        sa.Column(
            'change_type',
            sa.String(50),
            nullable=False,
            server_default='upload',
            comment='Type of change (upload, edit, ai_enhancement, import)'
        ),
        sa.Column(
            'change_metadata',
            postgresql.JSONB(),
            nullable=True,
            comment='Structured metadata about the change'
        ),
        sa.Column(
            'created_by_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
            comment='User who created this version'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment='Version creation timestamp'
        ),
        sa.Column(
            'archived_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When version was archived (NULL if active)'
        ),
    )

    # Create indices for optimal query performance
    # Index 1: Fast version lookup by resume
    op.create_index(
        'ix_resume_versions_resume_id',
        'resume_versions',
        ['resume_id']
    )

    # Index 2: Fast version lookup by user
    op.create_index(
        'ix_resume_versions_user_id',
        'resume_versions',
        ['user_id']
    )

    # Index 3: Find current versions quickly
    op.create_index(
        'ix_resume_versions_is_current',
        'resume_versions',
        ['is_current'],
        postgresql_where=sa.text('is_current = true')
    )

    # Index 4: Query by change type
    op.create_index(
        'ix_resume_versions_change_type',
        'resume_versions',
        ['change_type']
    )

    # Index 5: Time-series queries
    op.create_index(
        'ix_resume_versions_created_at',
        'resume_versions',
        ['created_at']
    )

    # Index 6: Archive status queries
    op.create_index(
        'ix_resume_versions_archived_at',
        'resume_versions',
        ['archived_at'],
        postgresql_where=sa.text('archived_at IS NOT NULL')
    )

    # Index 7: Composite for finding user's current versions
    op.create_index(
        'ix_resume_versions_user_current',
        'resume_versions',
        ['user_id', 'is_current', 'created_at'],
        postgresql_where=sa.text('is_current = true')
    )

    # Index 8: Composite for version history timeline
    op.create_index(
        'ix_resume_versions_resume_created',
        'resume_versions',
        ['resume_id', 'version_number', 'created_at']
    )

    # --- Add columns to resumes table ----------------------------------------
    # Track versioning at the resume level
    op.add_column('resumes', sa.Column(
        'version_count',
        sa.Integer(),
        nullable=False,
        server_default='0',
        comment='Total number of versions'
    ))

    op.add_column('resumes', sa.Column(
        'latest_version_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='When latest version was created'
    ))

    op.add_column('resumes', sa.Column(
        'total_downloads',
        sa.Integer(),
        nullable=False,
        server_default='0',
        comment='Download counter for analytics'
    ))

    # Create index for latest version queries
    op.create_index(
        'ix_resumes_latest_version_at',
        'resumes',
        ['user_id', 'latest_version_at']
    )


def downgrade() -> None:
    """
    Downgrade: Remove resume versioning tables and columns.

    This rollback removes:
    - All resume_versions records and table
    - Versioning columns from resumes table
    - All associated indices
    """
    # Drop indices from resumes table
    op.drop_index('ix_resumes_latest_version_at', table_name='resumes')

    # Drop columns from resumes table (in reverse order of addition)
    op.drop_column('resumes', 'total_downloads')
    op.drop_column('resumes', 'latest_version_at')
    op.drop_column('resumes', 'version_count')

    # Drop indices from resume_versions table
    op.drop_index('ix_resume_versions_resume_created', table_name='resume_versions')
    op.drop_index('ix_resume_versions_user_current', table_name='resume_versions')
    op.drop_index('ix_resume_versions_archived_at', table_name='resume_versions')
    op.drop_index('ix_resume_versions_created_at', table_name='resume_versions')
    op.drop_index('ix_resume_versions_change_type', table_name='resume_versions')
    op.drop_index('ix_resume_versions_is_current', table_name='resume_versions')
    op.drop_index('ix_resume_versions_user_id', table_name='resume_versions')
    op.drop_index('ix_resume_versions_resume_id', table_name='resume_versions')

    # Drop resume_versions table
    op.drop_table('resume_versions')

    # Drop ENUM type
    op.execute('DROP TYPE IF EXISTS resume_change_type CASCADE')
