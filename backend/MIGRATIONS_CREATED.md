# TrueMatch v3.0 Database Migrations - Created Files

## Summary
Three comprehensive database migrations have been successfully created for TrueMatch v3.0, implementing resume versioning, saved jobs tracking, and enhanced application tracking.

## Created Migration Files

### 1. Migration 0027: Resume Versioning
**File**: `alembic/versions/0027_add_resume_versioning.py`

**Tables Created**:
- `resume_versions` - Complete version history of all resumes with full audit trail

**Columns Added**:
- `resumes.version_count` - Total number of versions
- `resumes.latest_version_at` - When latest version was created
- `resumes.total_downloads` - Download counter for analytics

**Key Features**:
- UUID primary key with composite indices for performance
- Encrypted fields: `parsed_data`, `raw_narrative`, `supplementary` (PII protection)
- Change tracking: `change_type`, `change_summary`, `change_metadata`
- Quality scoring: `quality_score`, `completeness_percentage`
- Language support: `source_language`, `detected_language`
- Archive support: `archived_at` for soft deletes
- 8 performance-optimized indices including composite indices

**Foreign Keys**:
- `resume_id` → `resumes.id` (CASCADE)
- `user_id` → `users.id` (CASCADE)
- `created_by_id` → `users.id` (SET NULL)

---

### 2. Migration 0028: Saved Jobs Tracking
**File**: `alembic/versions/0028_add_saved_jobs.py`

**Tables Created**:
- `saved_jobs` - Candidate-curated job saves with engagement tracking
- `saved_jobs_lists` - Custom job organization lists for candidates

**Columns - saved_jobs**:
- Status tracking: `status` (saved, viewed, applied, archived, rejected)
- User notes and metadata: `notes`, `list_name`, `job_title`, `company_name`, `job_url`
- AI matching: `match_score`, `relevance_metadata` (encrypted)
- Timeline: `viewed_at`, `applied_at`, `created_at`, `updated_at`, `archived_at`
- Notifications: `notify_on_update`, `last_notified_at`

**Columns - saved_jobs_lists**:
- Organization: `name`, `description`, `icon`, `color`
- Flags: `is_default`, `is_shared`
- Performance: `job_count` (denormalized)
- Timeline: `created_at`, `updated_at`, `archived_at`

**Constraints**:
- Unique: `(user_id, position_id)` on saved_jobs
- Unique: `(user_id, name)` on saved_jobs_lists
- 9 performance-optimized indices including composite indices

**Foreign Keys**:
- `saved_jobs.user_id` → `users.id` (CASCADE)
- `saved_jobs.position_id` → `positions.id` (CASCADE)
- `saved_jobs.list_id` → `saved_jobs_lists.id` (SET NULL)
- `saved_jobs_lists.user_id` → `users.id` (CASCADE)

---

### 3. Migration 0029: Application Tracking
**File**: `alembic/versions/0029_add_application_tracking.py`

**Tables Created**:
- `application_events` - Detailed activity log for application lifecycle events
- `application_feedback` - Structured feedback from interviews and assessments

**Columns - application_events**:
- Event tracking: `event_type`, `event_data` (JSONB), `description`
- Actor tracking: `triggered_by_id`, `actor_type`
- Timeline: `created_at`

**Columns - application_feedback**:
- Feedback: `feedback_stage`, `overall_rating`, `feedback_text` (encrypted)
- Structured data: `structured_feedback` (JSONB)
- Recommendation: `recommendation`, `confidence_score`
- Metadata: `provided_by_id`, `provided_by_name`, `created_at`, `updated_at`

**Columns Added to applications**:
- Resume tracking: `resume_version_id` (FK to resume_versions)
- Timeline fields: `viewed_at`, `interview_scheduled_at`, `rejected_at`, `withdrawn_at`, `offer_extended_at`, `offer_accepted_at`
- Rejection data: `rejection_reason`, `rejection_feedback` (both encrypted), `can_reapply`, `reapply_after`
- Scoring: `initial_match_score`, `current_match_score`, `fit_assessment` (JSONB)
- Communication: `messages_count`, `last_message_at`, `requires_response`
- Application data: `custom_cover_letter` (encrypted), `application_answers` (JSONB)
- Admin: `stage_notes`, `priority`, `is_flagged`, `assigned_to_id`

**Enums Created**:
- `application_event_type` - Event types (status_changed, message_sent, etc.)
- `application_actor_type` - Actor types (system, user, automation, ats_sync)
- `application_feedback_stage` - Feedback stages (phone_screen, technical, etc.)
- `application_recommendation` - Recommendations (proceed, maybe, reject)
- `application_priority` - Priority levels (high, normal, low)

**Constraints**:
- 11 performance-optimized indices including composite indices

**Foreign Keys**:
- `application_events.application_id` → `applications.id` (CASCADE)
- `application_events.user_id` → `users.id` (CASCADE)
- `application_events.triggered_by_id` → `users.id` (SET NULL)
- `application_feedback.application_id` → `applications.id` (CASCADE)
- `application_feedback.provided_by_id` → `users.id` (CASCADE)
- `applications.resume_version_id` → `resume_versions.id` (SET NULL)
- `applications.assigned_to_id` → `users.id` (SET NULL)

---

## Usage

### Apply Migrations
```bash
cd backend
# Apply all three migrations
alembic upgrade head

# Or apply individually
alembic upgrade 0027  # Resume versioning
alembic upgrade 0028  # Saved jobs
alembic upgrade 0029  # Application tracking
```

### Check Status
```bash
alembic current       # Show current revision
alembic history       # Show all migrations
```

### Rollback
```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade 0027
```

---

## Implementation Notes

### Security & Encryption
All PII fields are marked with `(encrypted)` in comments and should be encrypted at rest using the application's encryption layer:
- Resume versions: `parsed_data`, `raw_narrative`, `supplementary`
- Saved jobs: `relevance_metadata`
- Applications: `rejection_reason`, `rejection_feedback`, `custom_cover_letter`
- Feedback: `feedback_text`

### Performance Optimization
Each migration includes:
- Single UUID primary keys for efficient lookups
- Composite indices for common query patterns
- Partial indices with `WHERE` clauses for filtered queries
- Foreign key indices for join operations

### Data Integrity
- Cascading deletes where child records are dependent on parent
- Soft deletes via `archived_at` nullable timestamp
- Referential integrity through foreign key constraints
- Unique constraints to prevent duplicate saves/lists

### AsyncAlchemy Compatibility
All migrations use standard SQLAlchemy patterns compatible with async drivers (psycopg3).

---

## Files Generated

```
backend/alembic/versions/
├── 0027_add_resume_versioning.py    (9.5 KB)
├── 0028_add_saved_jobs.py           (11 KB)
└── 0029_add_application_tracking.py (19 KB)
```

**Total**: 39.5 KB of migration code

---

## Next Steps

1. **Test Migrations**: Run in development environment first
2. **Verify Schema**: Check that all tables and indices are created correctly
3. **Performance Testing**: Test common query patterns with new indices
4. **Data Migration**: If migrating existing data, create data migration scripts
5. **Documentation**: Update API documentation with new endpoints/fields
6. **Deployment**: Deploy to staging and production with rollback plan

---

## Revision History

- **Revision 0027**: Resume versioning (depends on 0026)
- **Revision 0028**: Saved jobs (depends on 0027)
- **Revision 0029**: Application tracking (depends on 0028)

Each migration can be rolled back independently to its previous revision.
