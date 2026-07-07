"""Resume versioning v3.0 enhancements with differential tracking and comparison

Revision ID: 0024
Revises: 0023
Create Date: 2026-07-08 00:00:00.000000

Enhancements for v3.0:
- Add differential/diff storage for efficient version comparison
- Add visibility controls for version management
- Add version tagging and annotations
- Add performance indices for common query patterns
- Include backup safety checks before schema changes
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0024'
down_revision = '0023'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade: Add v3.0 enhancements to resume versioning.

    Safety: Creates backup before any ALTER operations.
    Pattern: AsyncAlchemy compatible (psycopg3 driver)
    """
    # SAFETY: Backup the existing resume_versions table before modifications
    op.execute("""
        CREATE TABLE IF NOT EXISTS resume_versions_backup_0024 AS
        SELECT * FROM resume_versions;
    """)

    # Add differential storage for efficient version comparison
    op.add_column('resume_versions', sa.Column(
        'content_diff',
        sa.Text(),
        nullable=True,
        comment='JSON diff from previous version for efficient comparison'
    ))

    # Add version metadata and visibility controls
    op.add_column('resume_versions', sa.Column(
        'is_visible',
        sa.Boolean(),
        nullable=False,
        server_default=sa.true(),
        comment='Whether version is visible to user (soft-delete)'
    ))

    op.add_column('resume_versions', sa.Column(
        'is_pinned',
        sa.Boolean(),
        nullable=False,
        server_default=sa.false(),
        comment='Whether version is pinned for quick access'
    ))

    # Add version tagging and annotations
    op.add_column('resume_versions', sa.Column(
        'tag',
        sa.String(100),
        nullable=True,
        comment='User-provided tag/label for version (e.g., "Final", "Archive")'
    ))

    op.add_column('resume_versions', sa.Column(
        'annotation',
        sa.String(500),
        nullable=True,
        comment='User-provided notes about why this version was created'
    ))

    # Add comparison support fields
    op.add_column('resume_versions', sa.Column(
        'sections_changed',
        postgresql.JSONB(),
        nullable=True,
        comment='Track which resume sections changed from previous version'
    ))

    op.add_column('resume_versions', sa.Column(
        'similarity_to_current',
        sa.Float(),
        nullable=True,
        comment='Cached similarity score to current version (0.0-1.0)'
    ))

    # Add AI feedback and improvement tracking
    op.add_column('resume_versions', sa.Column(
        'ai_feedback',
        sa.Text(),
        nullable=True,
        comment='AI-generated feedback on this version (encrypted at rest)'
    ))

    op.add_column('resume_versions', sa.Column(
        'improvement_areas',
        postgresql.JSONB(),
        nullable=True,
        comment='Structured list of improvement suggestions'
    ))

    # Performance indices for v3.0 query patterns
    # Query: "Get all visible versions for a user, ordered by creation"
    op.create_index(
        'ix_resume_versions_user_visible_created',
        'resume_versions',
        ['user_id', 'is_visible', 'created_at'],
        postgresql_where=sa.text('is_visible = true')
    )

    # Query: "Get pinned versions for quick access"
    op.create_index(
        'ix_resume_versions_user_pinned',
        'resume_versions',
        ['user_id', 'is_pinned'],
        postgresql_where=sa.text('is_pinned = true')
    )

    # Query: "Find versions by tag"
    op.create_index(
        'ix_resume_versions_tag',
        'resume_versions',
        ['user_id', 'tag'],
        postgresql_where=sa.text('tag IS NOT NULL')
    )

    # Query: "Get versions needing comparison/analysis"
    op.create_index(
        'ix_resume_versions_content_diff',
        'resume_versions',
        ['resume_id', 'version_number'],
        postgresql_where=sa.text('content_diff IS NOT NULL')
    )

    # Query: "Get recent versions with AI feedback"
    op.create_index(
        'ix_resume_versions_ai_feedback_recent',
        'resume_versions',
        ['user_id', 'created_at'],
        postgresql_where=sa.text('ai_feedback IS NOT NULL')
    )


def downgrade() -> None:
    """
    Downgrade: Remove v3.0 enhancements to resume versioning.

    Safety: Backup preserved in resume_versions_backup_0024 table for manual recovery.
    """
    # Drop performance indices
    op.drop_index('ix_resume_versions_ai_feedback_recent', table_name='resume_versions')
    op.drop_index('ix_resume_versions_content_diff', table_name='resume_versions')
    op.drop_index('ix_resume_versions_tag', table_name='resume_versions')
    op.drop_index('ix_resume_versions_user_pinned', table_name='resume_versions')
    op.drop_index('ix_resume_versions_user_visible_created', table_name='resume_versions')

    # Drop v3.0 columns (in reverse order of addition)
    op.drop_column('resume_versions', 'improvement_areas')
    op.drop_column('resume_versions', 'ai_feedback')
    op.drop_column('resume_versions', 'similarity_to_current')
    op.drop_column('resume_versions', 'sections_changed')
    op.drop_column('resume_versions', 'annotation')
    op.drop_column('resume_versions', 'tag')
    op.drop_column('resume_versions', 'is_pinned')
    op.drop_column('resume_versions', 'is_visible')
    op.drop_column('resume_versions', 'content_diff')

    # SAFETY: Backup table left for manual recovery if needed
    # Drop with: DROP TABLE IF EXISTS resume_versions_backup_0024;
