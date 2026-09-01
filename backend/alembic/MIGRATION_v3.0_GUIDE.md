# TrueMatch v3.0 Database Migrations - Comprehensive Guide

## Overview

This document provides comprehensive instructions for deploying, testing, and verifying the three database migrations for TrueMatch v3.0:

1. **0024_resume_versioning_v3_enhancements.py** - Resume version comparison and AI feedback
2. **0025_saved_jobs_v3_enhancements.py** - Job curation, recommendations, and list management
3. **0026_application_timeline_v3_enhancements.py** - Assessment timeline and SLA tracking

## Key Features

### Safety First
- **Automatic backups** created before ALTER operations
- **Reversible** - comprehensive downgrade functions
- **Tested patterns** - follows existing Alembic conventions
- **AsyncAlchemy compatible** - uses psycopg3 patterns

### Performance Optimized
- **Conditional indices** with PostgreSQL WHERE clauses
- **Composite indices** for common query patterns
- **Partial indices** to reduce index size and maintenance overhead
- **Query-specific design** - each index targets documented use cases

### Comprehensive Tracking
- **Timeline fields** for SLA monitoring and progression tracking
- **Audit trails** with reviewer tracking and override history
- **Consistency metrics** for re-assessment comparisons
- **Engagement analytics** for recommendation and notification systems

## Pre-Deployment Checklist

### Development Environment
```bash
# 1. Ensure development database is accessible
export DATABASE_URL="postgresql+psycopg://user:password@localhost/truematch_dev"

# 2. Verify current migration status
cd backend
alembic current

# 3. Check for pending migrations
alembic history

# 4. Review all test data requirements
python -m pytest tests/migrations/test_v3_0_migrations.py
```

### Database Preparation
```bash
# 1. Create full backup before any migrations
pg_dump -Fc truematch_dev > backups/truematch_dev_before_v3.0.dump

# 2. Verify database size (for capacity planning)
du -sh /var/lib/postgresql/data/truematch_dev/

# 3. Check for active connections
psql truematch_dev -c "SELECT datname, usename, application_name FROM pg_stat_activity WHERE datname = 'truematch_dev';"
```

## Migration Execution

### Step 1: Development Testing

```bash
# 1. Run migrations in development
cd backend
alembic upgrade head

# 2. Verify schema changes
alembic current
# Should show: 0026

# 3. Run comprehensive tests
pytest tests/migrations/ -v --tb=short

# 4. Verify backup tables were created
psql truematch_dev -c "\dt backup_*"
# Should list:
#   resume_versions_backup_0024
#   saved_jobs_backup_0025
#   saved_jobs_lists_backup_0025
#   assessments_backup_0026
```

### Step 2: Data Validation

```bash
# 1. Validate no data was lost
python scripts/validate_migration_v3.0.py

# 2. Verify index creation and performance
psql truematch_dev -c "SELECT schemaname, tablename, indexname FROM pg_indexes WHERE tablename IN ('resume_versions', 'saved_jobs', 'assessments');"

# 3. Check index statistics
ANALYZE;

# 4. Test index usage with EXPLAIN ANALYZE
psql truematch_dev -c "EXPLAIN ANALYZE SELECT * FROM resume_versions WHERE user_id = 'xxxx' AND is_visible = true ORDER BY created_at DESC LIMIT 10;"
```

### Step 3: Performance Testing

```bash
# Run performance benchmarks before/after migration
cd backend
python tests/migrations/benchmark_v3.0.py

# Expected results:
# - No regression in query times
# - Indices used for WHERE clause filtering
# - 50-200ms response times for common queries
```

## Migration Details

### 0024: Resume Versioning v3.0 Enhancements

**New Columns:**
- `content_diff` (Text, nullable) - JSON diff from previous version
- `is_visible` (Boolean, default true) - Soft delete support
- `is_pinned` (Boolean, default false) - Quick access
- `tag` (String(100), nullable) - User labels
- `annotation` (String(500), nullable) - User notes
- `sections_changed` (JSONB, nullable) - Track modified sections
- `similarity_to_current` (Float, nullable) - Comparison score
- `ai_feedback` (Text, nullable) - AI suggestions (encrypted)
- `improvement_areas` (JSONB, nullable) - Structured suggestions

**New Indices:**
- `ix_resume_versions_user_visible_created` - Browse visible versions
- `ix_resume_versions_user_pinned` - Quick access pinned versions
- `ix_resume_versions_tag` - Filter by tags
- `ix_resume_versions_content_diff` - Comparison queries
- `ix_resume_versions_ai_feedback_recent` - AI suggestions

**Data Migration:**
- No existing data requires transformation
- All new columns allow NULL values
- Defaults set appropriately

### 0025: Saved Jobs v3.0 Enhancements

**New Columns (saved_jobs table):**
- `recommendation_source` - ML/search/recruiter source
- `recommendation_score` - Confidence 0.0-1.0
- `recommendation_reason` - Explanation text
- `salary_min/max` - Salary range tracking
- `market_demand_level` - Market competition
- `similar_jobs_count` - Market saturation
- `interest_level` - User categorization
- `reason_saved` - Why user saved
- `times_viewed` - Engagement metric
- `last_viewed_at` - Temporal tracking
- `notification_schedule` - Frequency control
- `next_notification_at` - Batch processing
- `notification_count` - Analytics

**New Columns (saved_jobs_lists table):**
- `description_extended` - Richer metadata
- `sort_order` - UI ordering
- `is_system_list` - System vs user lists
- `last_job_added_at` - Activity tracking
- `total_applications` - List statistics
- `avg_match_score` - Quality metric

**New Indices:**
- Query-specific indices for recommendations, market insights, engagement
- Partial indices for active notifications and high-interest items

### 0026: Application Timeline v3.0 Enhancements

**New Columns (assessments table):**
- `stage_entered_at` - Timeline tracking
- `stage_duration_seconds` - SLA calculation
- `expected_completion_at` - SLA forecasting
- `initial_assessment_at` - First evaluation time
- `final_assessment_at` - Decision time
- `assessment_version` - Re-run tracking
- `review_requested_at` - Review workflow
- `review_completed_at` - Review completion
- `reviewer_id` - Audit trail (FK to users)
- `review_notes` - Structured feedback
- `review_override` - Decision overrides
- `overall_confidence` - Composite scoring
- `confidence_breakdown` - Component scoring
- `reliability_flags` - Data quality issues
- `previous_assessment_id` - Self-referencing FK
- `score_change_percent` - Comparison metric
- `consistency_with_previous` - Validation metric

**New Indices:**
- SLA monitoring and funnel analysis
- Review workflow tracking
- Assessment version history
- Confidence and reliability monitoring
- Consistency validation for repeat assessments

## Rollback Procedures

### Automatic Rollback (Safest)

```bash
# Using Alembic to rollback one migration at a time
cd backend

# Step 1: Rollback 0026 (Application Timeline)
alembic downgrade 0025
# Wait for completion and verify

# Step 2: Rollback 0025 (Saved Jobs)
alembic downgrade 0024
# Wait for completion and verify

# Step 3: Rollback 0024 (Resume Versioning)
alembic downgrade 0023
# Wait for completion and verify
```

### Manual Recovery from Backup

If automatic rollback fails, use the backup tables created during upgrade:

```bash
# Tables created as backups:
# - resume_versions_backup_0024
# - saved_jobs_backup_0025
# - saved_jobs_lists_backup_0025
# - assessments_backup_0026

# Recovery procedure:
BEGIN TRANSACTION;

-- Check backup integrity
SELECT COUNT(*) FROM resume_versions_backup_0024;

-- If needed, restore from backup:
DROP TABLE resume_versions CASCADE;
ALTER TABLE resume_versions_backup_0024 RENAME TO resume_versions;

-- Recreate constraints (indices will need to be recreated)
ALTER TABLE resume_versions ADD PRIMARY KEY (id);
ALTER TABLE resume_versions ADD CONSTRAINT fk_resume_id 
  FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE;
-- ... recreate other constraints ...

COMMIT;

-- Clean up backup
DROP TABLE IF EXISTS resume_versions_backup_0024;
```

## Testing Procedures

### Unit Tests

```bash
# Run all migration tests
pytest tests/migrations/test_v3_0_migrations.py -v

# Test specific migration
pytest tests/migrations/test_v3_0_migrations.py::TestResumeVersioningV3 -v

# Test data integrity
pytest tests/migrations/test_v3_0_migrations.py::TestDataIntegrity -v
```

### Integration Tests

```bash
# Test the complete upgrade/downgrade cycle
pytest tests/migrations/test_migration_cycle.py -v

# Test with sample data
pytest tests/migrations/test_v3_0_with_data.py -v
```

### Performance Tests

```bash
# Baseline performance before migration
python tests/migrations/benchmark_baseline.py

# Performance after migration
python tests/migrations/benchmark_v3.0.py

# Compare results
python tests/migrations/compare_benchmarks.py
```

## Verification Queries

### Resume Versioning

```sql
-- Verify v3.0 columns exist
SELECT COUNT(*) AS version_count,
       COUNT(content_diff) AS with_diffs,
       COUNT(ai_feedback) AS with_ai_feedback,
       COUNT(NULLIF(is_pinned, false)) AS pinned_versions
FROM resume_versions;

-- Verify indices
SELECT indexname FROM pg_indexes 
WHERE tablename = 'resume_versions' AND indexname LIKE 'ix_resume%';

-- Test index usage
EXPLAIN ANALYZE 
SELECT * FROM resume_versions 
WHERE user_id = '00000000-0000-0000-0000-000000000001' 
  AND is_visible = true 
ORDER BY created_at DESC;
```

### Saved Jobs

```sql
-- Verify v3.0 columns
SELECT COUNT(*) AS saved_jobs_count,
       COUNT(recommendation_score) AS recommended,
       COUNT(NULLIF(interest_level, 'low')) AS high_interest,
       COUNT(CASE WHEN notification_schedule != 'none' THEN 1 END) AS notifications_enabled
FROM saved_jobs;

-- Verify list enhancements
SELECT COUNT(*) AS list_count,
       COUNT(NULLIF(is_system_list, false)) AS system_lists,
       AVG(CAST(job_count AS NUMERIC)) AS avg_jobs_per_list
FROM saved_jobs_lists;

-- Test composite index performance
EXPLAIN ANALYZE
SELECT * FROM saved_jobs
WHERE user_id = '00000000-0000-0000-0000-000000000001'
  AND interest_level != 'low'
  AND status = 'saved'
ORDER BY created_at DESC;
```

### Application Timeline

```sql
-- Verify assessment enhancements
SELECT COUNT(*) AS assessment_count,
       COUNT(final_assessment_at) AS completed,
       COUNT(review_completed_at) AS reviewed,
       COUNT(CASE WHEN review_override THEN 1 END) AS overrides,
       AVG(overall_confidence) AS avg_confidence
FROM assessments;

-- Verify timeline consistency
SELECT assessment_version, COUNT(*) as count
FROM assessments
WHERE assessment_version > 1
GROUP BY assessment_version;

-- Test SLA monitoring index
EXPLAIN ANALYZE
SELECT * FROM assessments
WHERE status = 'running'
  AND expected_completion_at < NOW()
ORDER BY expected_completion_at ASC;
```

## Production Deployment

### Pre-Flight Checks

```bash
# 1. Verify migrations are tested
alembic history | grep "v3.0"

# 2. Backup production database
pg_dump -Fc truematch_prod > backups/truematch_prod_before_v3.0.dump

# 3. Verify backup size
du -sh backups/truematch_prod_before_v3.0.dump

# 4. Test restore on staging
pg_restore -C -d staging < backups/truematch_prod_before_v3.0.dump

# 5. Run migrations on staging
FLASK_ENV=staging alembic upgrade head

# 6. Run full test suite on staging
pytest tests/ -m "not slow"
```

### Deployment Steps

```bash
# 1. Put application in maintenance mode
# Disable all write operations via API

# 2. Wait for connections to close
psql truematch_prod -c "SELECT COUNT(*) FROM pg_stat_activity WHERE datname = 'truematch_prod' AND pid <> pg_backend_pid();"

# 3. Run migrations (one at a time, with monitoring)
cd backend
alembic upgrade 0024
# Monitor: SELECT * FROM pg_stat_activity;
# Verify backup table created

alembic upgrade 0025
# Verify indices created

alembic upgrade 0026
# Verify all changes applied

# 4. Verify migration status
alembic current
# Should show: 0026

# 5. Run validation queries (from Testing Procedures section)

# 6. Enable write operations
# Take application out of maintenance mode

# 7. Monitor for errors
tail -f /var/log/app/error.log
```

### Post-Deployment Monitoring

```bash
# Monitor query performance
SELECT query, calls, mean_time, total_time FROM pg_stat_statements 
WHERE query LIKE '%resume_versions%'
ORDER BY mean_time DESC;

# Monitor index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename IN ('resume_versions', 'saved_jobs', 'assessments')
ORDER BY idx_scan DESC;

# Check for table bloat
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE tablename IN ('resume_versions', 'saved_jobs', 'assessments');

# Monitor application logs for errors
grep "ERROR\|CRITICAL" /var/log/app/*.log | head -20
```

## Troubleshooting

### Migration Hangs

```bash
# Check for active transactions blocking the migration
SELECT pid, usename, application_name, state FROM pg_stat_activity 
WHERE state = 'active' AND datname = 'truematch_prod';

# Kill blocking connections (if safe)
SELECT pg_terminate_backend(pid) FROM pg_stat_activity
WHERE datname = 'truematch_prod' AND pid <> pg_backend_pid()
AND state != 'idle';
```

### Index Creation Failures

```bash
-- Check existing indices
SELECT * FROM pg_stat_user_indexes WHERE tablename = 'resume_versions';

-- Check index bloat
SELECT schemaname, tablename, indexname, pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;

-- Reindex if needed
REINDEX TABLE resume_versions;
```

### Foreign Key Issues

```sql
-- Verify referential integrity
SELECT COUNT(*) FROM resume_versions WHERE user_id NOT IN (SELECT id FROM users);

-- Fix orphaned records before adding constraints
DELETE FROM resume_versions WHERE user_id NOT IN (SELECT id FROM users);
```

## Documentation References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Indices](https://www.postgresql.org/docs/current/indexes.html)
- [SQLAlchemy AsyncAlchemy](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Project Database Architecture](../docs/database.md)
- [Migration Best Practices](../docs/migrations.md)

## Support

For issues or questions:

1. Check the backup tables (not dropped during rollback)
2. Review logs: `alembic upgrade --sql 0024` to see raw SQL
3. Test in development first
4. Reach out to database team for production deployments
