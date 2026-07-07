#!/usr/bin/env python3
"""
Validation script for TrueMatch v3.0 database migrations.

This script verifies:
1. Schema changes were applied correctly
2. All indices were created
3. Data integrity is maintained
4. No data was lost during migration
5. Backup tables exist for recovery
6. Foreign key relationships are valid
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from typing import Dict, List, Tuple
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.pool import NullPool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationValidator:
    """Validates TrueMatch v3.0 migrations."""

    def __init__(self, database_url: str):
        """Initialize validator with database connection."""
        self.database_url = database_url
        self.engine = create_engine(database_url, poolclass=NullPool)
        self.inspector = inspect(self.engine)
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> bool:
        """Run all validation checks."""
        logger.info("Starting v3.0 migration validation...")

        checks = [
            ("Resume Versioning v3.0", self.validate_resume_versioning),
            ("Saved Jobs v3.0", self.validate_saved_jobs),
            ("Application Timeline v3.0", self.validate_application_timeline),
            ("Backup Tables", self.validate_backup_tables),
            ("Data Integrity", self.validate_data_integrity),
            ("Foreign Keys", self.validate_foreign_keys),
        ]

        results = {}
        for check_name, check_func in checks:
            logger.info(f"\nRunning: {check_name}")
            try:
                results[check_name] = check_func()
            except Exception as e:
                logger.error(f"Error during {check_name}: {e}")
                self.errors.append(f"{check_name} failed: {e}")
                results[check_name] = False

        return self._report_results(results)

    def validate_resume_versioning(self) -> bool:
        """Validate resume versioning v3.0 enhancements."""
        logger.info("  Checking resume_versions table...")

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

        required_indices = {
            'ix_resume_versions_user_visible_created',
            'ix_resume_versions_user_pinned',
            'ix_resume_versions_tag',
            'ix_resume_versions_content_diff',
            'ix_resume_versions_ai_feedback_recent',
        }

        return self._validate_schema('resume_versions', required_columns, required_indices)

    def validate_saved_jobs(self) -> bool:
        """Validate saved jobs v3.0 enhancements."""
        logger.info("  Checking saved_jobs table...")

        saved_jobs_columns = {
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

        saved_jobs_indices = {
            'ix_saved_jobs_recommendation_score',
            'ix_saved_jobs_market_insights',
            'ix_saved_jobs_interest_level',
            'ix_saved_jobs_notification_schedule',
            'ix_saved_jobs_last_viewed',
        }

        result_jobs = self._validate_schema('saved_jobs', saved_jobs_columns, saved_jobs_indices)

        logger.info("  Checking saved_jobs_lists table...")

        lists_columns = {
            'description_extended',
            'sort_order',
            'is_system_list',
            'last_job_added_at',
            'total_applications',
            'avg_match_score',
        }

        lists_indices = {
            'ix_saved_jobs_lists_engagement',
            'ix_saved_jobs_lists_system',
            'ix_saved_jobs_lists_sort_order',
        }

        result_lists = self._validate_schema('saved_jobs_lists', lists_columns, lists_indices)

        return result_jobs and result_lists

    def validate_application_timeline(self) -> bool:
        """Validate application timeline v3.0 enhancements."""
        logger.info("  Checking assessments table...")

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

        schema_valid = self._validate_schema('assessments', required_columns, required_indices)

        # Verify foreign keys
        logger.info("  Checking foreign keys...")
        fks = self.inspector.get_foreign_keys('assessments')
        fk_names = {fk['name'] for fk in fks}

        required_fks = {
            'fk_assessments_reviewer_id',
            'fk_assessments_previous_assessment_id',
        }

        fk_valid = True
        for fk in required_fks:
            if fk not in fk_names:
                logger.warning(f"    Missing foreign key: {fk}")
                self.warnings.append(f"Missing FK: {fk}")
                fk_valid = False
            else:
                logger.info(f"    ✓ FK {fk}")

        return schema_valid and fk_valid

    def validate_backup_tables(self) -> bool:
        """Validate backup tables exist."""
        logger.info("  Checking backup tables...")

        backup_tables = {
            'resume_versions_backup_0024',
            'saved_jobs_backup_0025',
            'saved_jobs_lists_backup_0025',
            'assessments_backup_0026',
        }

        all_tables = set(self.inspector.get_table_names())
        all_valid = True

        for table in backup_tables:
            if table in all_tables:
                # Verify table is not empty
                with self.engine.connect() as conn:
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    logger.info(f"    ✓ {table} ({count} rows)")
            else:
                logger.error(f"    ✗ Missing backup table: {table}")
                self.errors.append(f"Missing backup table: {table}")
                all_valid = False

        return all_valid

    def validate_data_integrity(self) -> bool:
        """Validate data integrity after migration."""
        logger.info("  Checking data integrity...")

        all_valid = True

        # Check resume_versions data
        with self.engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM resume_versions")).scalar()
            logger.info(f"    resume_versions: {count} rows")

            count_backup = conn.execute(text("SELECT COUNT(*) FROM resume_versions_backup_0024")).scalar()
            if count == count_backup:
                logger.info(f"    ✓ resume_versions data preserved ({count} rows)")
            else:
                logger.error(f"    ✗ Data mismatch: current={count}, backup={count_backup}")
                self.errors.append(f"Data mismatch in resume_versions")
                all_valid = False

        # Check saved_jobs data
        with self.engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM saved_jobs")).scalar()
            logger.info(f"    saved_jobs: {count} rows")

            count_backup = conn.execute(text("SELECT COUNT(*) FROM saved_jobs_backup_0025")).scalar()
            if count == count_backup:
                logger.info(f"    ✓ saved_jobs data preserved ({count} rows)")
            else:
                logger.error(f"    ✗ Data mismatch in saved_jobs")
                self.errors.append("Data mismatch in saved_jobs")
                all_valid = False

        # Check assessments data
        with self.engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM assessments")).scalar()
            logger.info(f"    assessments: {count} rows")

            count_backup = conn.execute(text("SELECT COUNT(*) FROM assessments_backup_0026")).scalar()
            if count == count_backup:
                logger.info(f"    ✓ assessments data preserved ({count} rows)")
            else:
                logger.error(f"    ✗ Data mismatch in assessments")
                self.errors.append("Data mismatch in assessments")
                all_valid = False

        return all_valid

    def validate_foreign_keys(self) -> bool:
        """Validate foreign key relationships."""
        logger.info("  Checking foreign key relationships...")

        all_valid = True

        # Check resume_versions FK references
        with self.engine.connect() as conn:
            orphaned = conn.execute(text("""
                SELECT COUNT(*) FROM resume_versions rv
                WHERE NOT EXISTS (SELECT 1 FROM resumes r WHERE r.id = rv.resume_id)
            """)).scalar()

            if orphaned == 0:
                logger.info("    ✓ resume_versions.resume_id - no orphaned records")
            else:
                logger.error(f"    ✗ resume_versions has {orphaned} orphaned resume_id records")
                self.errors.append(f"Orphaned resume_versions.resume_id: {orphaned}")
                all_valid = False

        # Check saved_jobs FK references
        with self.engine.connect() as conn:
            orphaned = conn.execute(text("""
                SELECT COUNT(*) FROM saved_jobs sj
                WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = sj.user_id)
            """)).scalar()

            if orphaned == 0:
                logger.info("    ✓ saved_jobs.user_id - no orphaned records")
            else:
                logger.error(f"    ✗ saved_jobs has {orphaned} orphaned user_id records")
                self.errors.append(f"Orphaned saved_jobs.user_id: {orphaned}")
                all_valid = False

        # Check assessments reviewer FK references
        with self.engine.connect() as conn:
            orphaned = conn.execute(text("""
                SELECT COUNT(*) FROM assessments a
                WHERE a.reviewer_id IS NOT NULL
                AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = a.reviewer_id)
            """)).scalar()

            if orphaned == 0:
                logger.info("    ✓ assessments.reviewer_id - no orphaned records")
            else:
                logger.error(f"    ✗ assessments has {orphaned} orphaned reviewer_id records")
                all_valid = False

        return all_valid

    def _validate_schema(self, table_name: str, columns: set, indices: set) -> bool:
        """Validate table schema - columns and indices."""
        all_valid = True

        # Check table exists
        if table_name not in self.inspector.get_table_names():
            logger.error(f"    ✗ Table {table_name} does not exist")
            self.errors.append(f"Missing table: {table_name}")
            return False

        # Check columns
        existing_columns = {col['name'] for col in self.inspector.get_columns(table_name)}
        missing_columns = columns - existing_columns

        if missing_columns:
            logger.error(f"    ✗ Missing columns: {missing_columns}")
            self.errors.append(f"{table_name}: missing columns {missing_columns}")
            all_valid = False
        else:
            logger.info(f"    ✓ All {len(columns)} required columns present")

        # Check indices
        existing_indices = {idx['name'] for idx in self.inspector.get_indexes(table_name)}
        missing_indices = indices - existing_indices

        if missing_indices:
            logger.error(f"    ✗ Missing indices: {missing_indices}")
            self.errors.append(f"{table_name}: missing indices {missing_indices}")
            all_valid = False
        else:
            logger.info(f"    ✓ All {len(indices)} required indices present")

        return all_valid

    def _report_results(self, results: Dict[str, bool]) -> bool:
        """Report validation results."""
        logger.info("\n" + "="*70)
        logger.info("VALIDATION SUMMARY")
        logger.info("="*70)

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for check_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"{status}: {check_name}")

        logger.info("="*70)
        logger.info(f"Results: {passed}/{total} checks passed")

        if self.errors:
            logger.error(f"\nErrors ({len(self.errors)}):")
            for error in self.errors:
                logger.error(f"  - {error}")

        if self.warnings:
            logger.warning(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")

        success = passed == total and not self.errors
        logger.info(f"\nOverall Status: {'SUCCESS' if success else 'FAILED'}")

        return success


def main():
    """Main entry point."""
    # Get database URL from environment or use default
    database_url = os.getenv(
        'DATABASE_URL',
        'postgresql://localhost/truematch_dev'
    )

    logger.info(f"Validating migrations for: {database_url}")

    validator = MigrationValidator(database_url)
    success = validator.validate_all()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
