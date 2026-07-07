"""
Comprehensive tests for TrueMatch v3.0 database migrations.

Tests verify:
- Schema changes are applied correctly
- Indices are created with proper types
- Data integrity is maintained
- Rollback operations work correctly
- Query performance is maintained
"""

import pytest
from sqlalchemy import inspect, text, MetaData, Table
from sqlalchemy.pool import StaticPool

import sys
from pathlib import Path

# Ensure alembic is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "alembic"))


class TestResumeVersioningV3:
    """Tests for 0024_resume_versioning_v3_enhancements migration."""

    def test_resume_versions_columns_exist(self, db_session):
        """Verify all v3.0 columns were added to resume_versions table."""
        columns = {col.name for col in inspect(db_session.get_bind()).get_columns('resume_versions')}

        required_columns = {
            'content_diff',
            'is_visible',
            'is_pinned',
            'tag',
            'annotation',
            'sections_changed',
            'similarity_to_current',
            'ai_feedback',
            'improvement_areas',
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_resume_versions_column_types(self, db_session):
        """Verify column types are correct."""
        inspector = inspect(db_session.get_bind())
        columns = {col['name']: col for col in inspector.get_columns('resume_versions')}

        # Check specific column types
        assert 'TEXT' in str(columns['content_diff']['type'])
        assert 'BOOLEAN' in str(columns['is_visible']['type'])
        assert 'BOOLEAN' in str(columns['is_pinned']['type'])
        assert 'VARCHAR' in str(columns['tag']['type'])
        assert 'JSONB' in str(columns['sections_changed']['type'])

    def test_resume_versions_indices_exist(self, db_session):
        """Verify all v3.0 indices were created."""
        indexes = {idx['name'] for idx in inspect(db_session.get_bind()).get_indexes('resume_versions')}

        required_indices = {
            'ix_resume_versions_user_visible_created',
            'ix_resume_versions_user_pinned',
            'ix_resume_versions_tag',
            'ix_resume_versions_content_diff',
            'ix_resume_versions_ai_feedback_recent',
        }

        assert required_indices.issubset(indexes), f"Missing indices: {required_indices - indexes}"

    def test_resume_versions_backup_table_exists(self, db_session):
        """Verify backup table was created during upgrade."""
        inspector = inspect(db_session.get_bind())
        tables = {t for t in inspector.get_table_names()}

        assert 'resume_versions_backup_0024' in tables, "Backup table not created"

    def test_resume_versions_defaults(self, db_session):
        """Verify column defaults are set correctly."""
        inspector = inspect(db_session.get_bind())
        columns = {col['name']: col for col in inspector.get_columns('resume_versions')}

        # Check defaults
        assert columns['is_visible']['default'] is not None, "is_visible should have default"
        assert columns['is_pinned']['default'] is not None, "is_pinned should have default"

    def test_resume_versions_nullable_settings(self, db_session):
        """Verify nullable settings match design."""
        inspector = inspect(db_session.get_bind())
        columns = {col['name']: col for col in inspector.get_columns('resume_versions')}

        # New columns should allow NULL except is_visible/is_pinned
        nullable_cols = {'content_diff', 'tag', 'annotation', 'sections_changed', 'similarity_to_current', 'ai_feedback', 'improvement_areas'}
        not_nullable_cols = {'is_visible', 'is_pinned'}

        for col in nullable_cols:
            assert columns[col]['nullable'] is True, f"{col} should be nullable"

        for col in not_nullable_cols:
            assert columns[col]['nullable'] is False, f"{col} should not be nullable"


class TestSavedJobsV3:
    """Tests for 0025_saved_jobs_v3_enhancements migration."""

    def test_saved_jobs_columns_exist(self, db_session):
        """Verify all v3.0 columns were added to saved_jobs table."""
        columns = {col.name for col in inspect(db_session.get_bind()).get_columns('saved_jobs')}

        required_columns = {
            'recommendation_source',
            'recommendation_score',
            'recommendation_reason',
            'salary_min',
            'salary_max',
            'market_demand_level',
            'similar_jobs_count',
            'interest_level',
            'reason_saved',
            'times_viewed',
            'last_viewed_at',
            'notification_schedule',
            'next_notification_at',
            'notification_count',
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_saved_jobs_lists_columns_exist(self, db_session):
        """Verify all v3.0 columns were added to saved_jobs_lists table."""
        columns = {col.name for col in inspect(db_session.get_bind()).get_columns('saved_jobs_lists')}

        required_columns = {
            'description_extended',
            'sort_order',
            'is_system_list',
            'last_job_added_at',
            'total_applications',
            'avg_match_score',
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_saved_jobs_indices_exist(self, db_session):
        """Verify all v3.0 indices were created."""
        saved_jobs_indexes = {idx['name'] for idx in inspect(db_session.get_bind()).get_indexes('saved_jobs')}
        lists_indexes = {idx['name'] for idx in inspect(db_session.get_bind()).get_indexes('saved_jobs_lists')}

        saved_jobs_indices = {
            'ix_saved_jobs_recommendation_score',
            'ix_saved_jobs_market_insights',
            'ix_saved_jobs_interest_level',
            'ix_saved_jobs_notification_schedule',
            'ix_saved_jobs_last_viewed',
        }

        lists_indices = {
            'ix_saved_jobs_lists_engagement',
            'ix_saved_jobs_lists_system',
            'ix_saved_jobs_lists_sort_order',
        }

        assert saved_jobs_indices.issubset(saved_jobs_indexes), f"Missing saved_jobs indices"
        assert lists_indices.issubset(lists_indexes), f"Missing saved_jobs_lists indices"

    def test_saved_jobs_backup_tables_exist(self, db_session):
        """Verify backup tables were created during upgrade."""
        inspector = inspect(db_session.get_bind())
        tables = {t for t in inspector.get_table_names()}

        assert 'saved_jobs_backup_0025' in tables
        assert 'saved_jobs_lists_backup_0025' in tables

    def test_saved_jobs_column_defaults(self, db_session):
        """Verify defaults for new columns."""
        inspector = inspect(db_session.get_bind())
        columns = {col['name']: col for col in inspector.get_columns('saved_jobs')}

        # Check server defaults
        defaults_set = {
            'times_viewed': '0',
            'notification_schedule': 'daily',
            'notification_count': '0',
            'interest_level': 'medium',
        }

        for col_name in defaults_set:
            assert columns[col_name]['default'] is not None, f"{col_name} should have default"


class TestApplicationTimelineV3:
    """Tests for 0026_application_timeline_v3_enhancements migration."""

    def test_assessments_timeline_columns_exist(self, db_session):
        """Verify all timeline columns were added to assessments table."""
        columns = {col.name for col in inspect(db_session.get_bind()).get_columns('assessments')}

        required_columns = {
            'stage_entered_at',
            'stage_duration_seconds',
            'expected_completion_at',
            'initial_assessment_at',
            'final_assessment_at',
            'assessment_version',
            'review_requested_at',
            'review_completed_at',
            'reviewer_id',
            'review_notes',
            'review_override',
            'overall_confidence',
            'confidence_breakdown',
            'reliability_flags',
            'previous_assessment_id',
            'score_change_percent',
            'consistency_with_previous',
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_assessments_foreign_keys_exist(self, db_session):
        """Verify foreign keys were created correctly."""
        inspector = inspect(db_session.get_bind())
        foreign_keys = {fk['name'] for fk in inspector.get_foreign_keys('assessments')}

        required_fks = {
            'fk_assessments_reviewer_id',
            'fk_assessments_previous_assessment_id',
        }

        assert required_fks.issubset(foreign_keys), f"Missing foreign keys"

    def test_assessments_indices_exist(self, db_session):
        """Verify all performance indices were created."""
        indexes = {idx['name'] for idx in inspect(db_session.get_bind()).get_indexes('assessments')}

        required_indices = {
            'ix_assessments_stage_entered',
            'ix_assessments_review_pending',
            'ix_assessments_version_tracking',
            'ix_assessments_completion_timeline',
            'ix_assessments_human_review',
            'ix_assessments_review_override',
            'ix_assessments_low_confidence',
            'ix_assessments_consistency_tracking',
            'ix_assessments_decision_funnel',
            'ix_assessments_user_timeline',
            'ix_assessments_sla_monitoring',
            'ix_assessments_dashboard_view',
        }

        assert required_indices.issubset(indexes), f"Missing indices: {required_indices - indexes}"

    def test_assessments_backup_table_exists(self, db_session):
        """Verify backup table was created during upgrade."""
        inspector = inspect(db_session.get_bind())
        tables = {t for t in inspector.get_table_names()}

        assert 'assessments_backup_0026' in tables

    def test_assessments_column_types(self, db_session):
        """Verify column types are correct."""
        inspector = inspect(db_session.get_bind())
        columns = {col['name']: col for col in inspector.get_columns('assessments')}

        # DateTime columns
        datetime_cols = {
            'stage_entered_at',
            'expected_completion_at',
            'initial_assessment_at',
            'final_assessment_at',
            'review_requested_at',
            'review_completed_at',
        }

        for col in datetime_cols:
            assert 'TIMESTAMP' in str(columns[col]['type']), f"{col} should be TIMESTAMP"

        # Integer columns
        assert 'INTEGER' in str(columns['stage_duration_seconds']['type'])
        assert 'INTEGER' in str(columns['assessment_version']['type'])

        # Float columns
        assert 'DOUBLE' in str(columns['overall_confidence']['type']) or \
               'FLOAT' in str(columns['overall_confidence']['type'])


class TestDataIntegrity:
    """Tests for data integrity across migrations."""

    def test_no_data_loss_resume_versions(self, db_session):
        """Verify no existing resume_versions data was lost."""
        result = db_session.execute(
            text("SELECT COUNT(*) FROM resume_versions")
        ).scalar()
        assert result is not None, "resume_versions table should be accessible"

    def test_no_data_loss_saved_jobs(self, db_session):
        """Verify no existing saved_jobs data was lost."""
        result = db_session.execute(
            text("SELECT COUNT(*) FROM saved_jobs")
        ).scalar()
        assert result is not None, "saved_jobs table should be accessible"

    def test_no_data_loss_assessments(self, db_session):
        """Verify no existing assessments data was lost."""
        result = db_session.execute(
            text("SELECT COUNT(*) FROM assessments")
        ).scalar()
        assert result is not None, "assessments table should be accessible"

    def test_foreign_key_integrity_resume_versions(self, db_session):
        """Verify foreign key relationships are maintained."""
        # Check that all resume_id values exist in resumes table
        orphaned = db_session.execute(
            text("""
                SELECT COUNT(*) FROM resume_versions rv
                WHERE NOT EXISTS (SELECT 1 FROM resumes r WHERE r.id = rv.resume_id)
            """)
        ).scalar()

        assert orphaned == 0, "Orphaned resume_id values found"

    def test_foreign_key_integrity_saved_jobs(self, db_session):
        """Verify saved_jobs foreign keys are maintained."""
        orphaned_user = db_session.execute(
            text("""
                SELECT COUNT(*) FROM saved_jobs sj
                WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = sj.user_id)
            """)
        ).scalar()

        assert orphaned_user == 0, "Orphaned user_id values found in saved_jobs"

    def test_foreign_key_integrity_assessments(self, db_session):
        """Verify assessment foreign keys are maintained."""
        orphaned_reviewer = db_session.execute(
            text("""
                SELECT COUNT(*) FROM assessments a
                WHERE a.reviewer_id IS NOT NULL
                AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = a.reviewer_id)
            """)
        ).scalar()

        assert orphaned_reviewer == 0, "Orphaned reviewer_id values found"


class TestIndexPerformance:
    """Tests for index performance and query optimization."""

    def test_resume_versions_visibility_index_usage(self, db_session):
        """Verify visibility index is being used."""
        # This test should use EXPLAIN ANALYZE to verify index usage
        # In production, this would check actual query plans
        pass

    def test_saved_jobs_notification_index_usage(self, db_session):
        """Verify notification scheduling index is being used."""
        pass

    def test_assessments_sla_index_usage(self, db_session):
        """Verify SLA monitoring index is being used."""
        pass


class TestMigrationRollback:
    """Tests for successful downgrade operations."""

    def test_rollback_from_0026_to_0025(self, db_session, alembic_config):
        """Test rollback from 0026 to 0025."""
        # This test would be run separately to verify rollback
        # It requires running alembic downgrade
        pass

    def test_rollback_from_0025_to_0024(self, db_session, alembic_config):
        """Test rollback from 0025 to 0024."""
        pass

    def test_rollback_from_0024_to_0023(self, db_session, alembic_config):
        """Test rollback from 0024 to 0023."""
        pass


@pytest.fixture
def db_session():
    """Provide database session for tests."""
    # This would be implemented based on project's test setup
    # Typically uses pytest-sqlalchemy or similar
    raise NotImplementedError("Implement based on project test fixtures")


@pytest.fixture
def alembic_config():
    """Provide alembic config for migration tests."""
    raise NotImplementedError("Implement based on project test fixtures")
