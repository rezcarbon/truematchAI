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
    # SAFETY: Backup the existing resume_versions table before modifications (if it exists)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'resume_versions') THEN
                CREATE TABLE IF NOT EXISTS resume_versions_backup_0024 AS
                SELECT * FROM resume_versions;
            END IF;
        END $$;
    """)

    # Only add columns if the table exists (fresh databases may skip this)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'resume_versions') THEN
                -- Add differential storage for efficient version comparison
                IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name='resume_versions' AND column_name='content_diff') THEN
                    ALTER TABLE resume_versions ADD COLUMN content_diff TEXT;
                END IF;

                -- Add version metadata and visibility controls
                IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name='resume_versions' AND column_name='is_visible') THEN
                    ALTER TABLE resume_versions ADD COLUMN is_visible BOOLEAN NOT NULL DEFAULT true;
                END IF;

                IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name='resume_versions' AND column_name='is_pinned') THEN
                    ALTER TABLE resume_versions ADD COLUMN is_pinned BOOLEAN NOT NULL DEFAULT false;
                END IF;

                -- Add version tagging and annotations
                IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name='resume_versions' AND column_name='tag') THEN
                    ALTER TABLE resume_versions ADD COLUMN tag VARCHAR(100);
                END IF;

                IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name='resume_versions' AND column_name='annotation') THEN
                    ALTER TABLE resume_versions ADD COLUMN annotation VARCHAR(500);
                END IF;

                -- Add comparison support fields
                IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name='resume_versions' AND column_name='sections_changed') THEN
                    ALTER TABLE resume_versions ADD COLUMN sections_changed JSONB;
                END IF;

                IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name='resume_versions' AND column_name='similarity_to_current') THEN
                    ALTER TABLE resume_versions ADD COLUMN similarity_to_current REAL;
                END IF;

                -- Add AI feedback and improvement tracking
                IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name='resume_versions' AND column_name='ai_feedback') THEN
                    ALTER TABLE resume_versions ADD COLUMN ai_feedback TEXT;
                END IF;

                IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name='resume_versions' AND column_name='improvement_areas') THEN
                    ALTER TABLE resume_versions ADD COLUMN improvement_areas JSONB;
                END IF;
            END IF;
        END $$;
    """)

    # Performance indices for v3.0 query patterns (only if table exists)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'resume_versions') THEN
                -- Query: "Get all visible versions for a user, ordered by creation"
                IF NOT EXISTS (SELECT FROM information_schema.statistics WHERE tablename = 'resume_versions' AND indexname = 'ix_resume_versions_user_visible_created') THEN
                    CREATE INDEX ix_resume_versions_user_visible_created ON resume_versions (user_id, is_visible, created_at) WHERE is_visible = true;
                END IF;

                -- Query: "Get pinned versions for quick access"
                IF NOT EXISTS (SELECT FROM information_schema.statistics WHERE tablename = 'resume_versions' AND indexname = 'ix_resume_versions_user_pinned') THEN
                    CREATE INDEX ix_resume_versions_user_pinned ON resume_versions (user_id, is_pinned) WHERE is_pinned = true;
                END IF;

                -- Query: "Find versions by tag"
                IF NOT EXISTS (SELECT FROM information_schema.statistics WHERE tablename = 'resume_versions' AND indexname = 'ix_resume_versions_tag') THEN
                    CREATE INDEX ix_resume_versions_tag ON resume_versions (user_id, tag) WHERE tag IS NOT NULL;
                END IF;

                -- Query: "Get versions needing comparison/analysis"
                IF NOT EXISTS (SELECT FROM information_schema.statistics WHERE tablename = 'resume_versions' AND indexname = 'ix_resume_versions_content_diff') THEN
                    CREATE INDEX ix_resume_versions_content_diff ON resume_versions (resume_id, version_number) WHERE content_diff IS NOT NULL;
                END IF;

                -- Query: "Get recent versions with AI feedback"
                IF NOT EXISTS (SELECT FROM information_schema.statistics WHERE tablename = 'resume_versions' AND indexname = 'ix_resume_versions_ai_feedback_recent') THEN
                    CREATE INDEX ix_resume_versions_ai_feedback_recent ON resume_versions (user_id, created_at) WHERE ai_feedback IS NOT NULL;
                END IF;
            END IF;
        END $$;
    """)


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
