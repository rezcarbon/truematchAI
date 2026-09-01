# Database Migrations: Resume Versioning, Saved Jobs, and Applications Tracking

This document describes three comprehensive database migrations for TrueMatch platform enhancements.

## Overview

Three migrations have been created in sequence:

1. **a5f8c1d2e3b7_resume_versioning.py** - Resume version history tracking
2. **b7d9e2c1a3f6_saved_jobs_tracking.py** - Saved jobs and job lists management
3. **c9a2b5e4f1d3_applications_enhanced_tracking.py** - Enhanced applications pipeline tracking

## Migration 1: Resume Versioning

**File**: `alembic/versions/a5f8c1d2e3b7_resume_versioning.py`

**Model**: `app/models/resume_version.py`

### Purpose
Enables comprehensive resume version history tracking with full audit trail, quality scoring, and version comparison capabilities.

### Tables Created

#### `resume_versions`
Stores all versions of a user's resume with complete history.

**Columns**:
- `id` (UUID, PK): Unique version identifier
- `resume_id` (UUID, FK): Reference to base resume record
- `user_id` (UUID, FK): User who owns the resume
- `version_number` (INT): Sequential version number
- `is_current` (BOOLEAN): Whether this is the active version
- `file_id` (VARCHAR): Cloud storage file identifier
- `file_name` (VARCHAR): Original file name
- `file_size_bytes` (INT): File size for quota tracking
- `file_type` (VARCHAR): File format (pdf, docx, etc.)
- `source_language` (VARCHAR): Original language code (ISO 639-1)
- `detected_language` (VARCHAR): Detected language of content
- `parsed_data` (TEXT, encrypted): Extracted structured resume data (JSON)
- `raw_narrative` (TEXT, encrypted): Full extracted text narrative
- `supplementary` (TEXT, encrypted): Additional parsed metadata (JSON)
- `quality_score` (FLOAT): AI-calculated resume quality metric
- `completeness_percentage` (INT): Resume section completeness %
- `sections_detected` (JSONB): Detected resume sections (experience, education, etc.)
- `change_summary` (VARCHAR): Human-readable summary of changes
- `change_type` (VARCHAR): Type of change (upload, edit, ai_enhancement, import)
- `change_metadata` (JSONB): Structured metadata about the change
- `created_by_id` (UUID, FK): User who created this version
- `created_at` (TIMESTAMP): Version creation timestamp
- `archived_at` (TIMESTAMP): When version was archived (NULL if active)

**Encryption**: PII fields (`parsed_data`, `raw_narrative`, `supplementary`) are encrypted at rest using AES-256-GCM.

**Indices**:
- `ix_resume_versions_resume_id`: Fast version lookup by resume
- `ix_resume_versions_user_id`: Fast version lookup by user
- `ix_resume_versions_is_current`: Find current versions quickly
- `ix_resume_versions_change_type`: Query by change type
- `ix_resume_versions_created_at`: Time-series queries
- `ix_resume_versions_archived_at`: Archive status queries
- `ix_resume_versions_user_current`: Composite for finding user's current versions
- `ix_resume_versions_resume_created`: Composite for version history timeline

### Columns Added to Existing Tables

#### `resumes` Table
- `version_count` (INT): Total number of versions
- `latest_version_at` (TIMESTAMP): When latest version was created
- `total_downloads` (INT): Download counter for analytics

### Key Features
- **Version History**: Complete audit trail of all resume changes
- **Quality Tracking**: AI-calculated quality scores over time
- **Change Tracking**: Detailed metadata about what changed and why
- **PII Encryption**: All sensitive resume content encrypted at rest
- **Multi-language Support**: Original and translated language tracking
- **Rollback Ready**: Easy restore to previous versions

### Usage Examples

```python
# Get current version
current_version = session.query(ResumeVersion).filter(
    ResumeVersion.resume_id == resume_id,
    ResumeVersion.is_current == True
).first()

# Get all versions for a resume
all_versions = session.query(ResumeVersion).filter(
    ResumeVersion.resume_id == resume_id
).order_by(ResumeVersion.version_number.desc()).all()

# Compare two versions
v1 = session.query(ResumeVersion).filter(
    ResumeVersion.resume_id == resume_id,
    ResumeVersion.version_number == 1
).first()

v2 = session.query(ResumeVersion).filter(
    ResumeVersion.resume_id == resume_id,
    ResumeVersion.version_number == 2
).first()
```

---

## Migration 2: Saved Jobs Tracking

**File**: `alembic/versions/b7d9e2c1a3f6_saved_jobs_tracking.py`

**Models**: 
- `app/models/saved_job.py` - SavedJob and SavedJobsList

### Purpose
Enables candidates to save, organize, and track job opportunities with custom lists and engagement metrics.

### Tables Created

#### `saved_jobs`
Candidate-curated job saves with tracking and organization.

**Columns**:
- `id` (UUID, PK): Unique save identifier
- `user_id` (UUID, FK): Candidate who saved the job
- `position_id` (UUID, FK): Saved job position
- `list_id` (UUID, FK): Custom list this job belongs to
- `list_name` (VARCHAR): Quick-access list name
- `notes` (TEXT): User's personal notes about the job
- `job_title` (VARCHAR): Denormalized job title
- `company_name` (VARCHAR): Denormalized company name
- `job_url` (VARCHAR): Direct link to job posting
- `match_score` (FLOAT): AI calculated match percentage
- `relevance_metadata` (TEXT, encrypted): Detailed match analysis (JSON)
- `status` (VARCHAR): saved, viewed, applied, archived, rejected
- `viewed_at` (TIMESTAMP): When candidate viewed the job
- `applied_at` (TIMESTAMP): When application submitted
- `notify_on_update` (BOOLEAN): Alert on job/company updates
- `last_notified_at` (TIMESTAMP): Last notification sent
- `created_at` (TIMESTAMP): When job was saved
- `updated_at` (TIMESTAMP): Last update timestamp
- `archived_at` (TIMESTAMP): When archived (NULL if active)

**Encryption**: `relevance_metadata` contains match analysis encrypted at rest.

**Unique Constraint**: (user_id, position_id) - User can only save a job once

**Indices**:
- `ix_saved_jobs_user_id`: User's saved jobs
- `ix_saved_jobs_position_id`: Which users saved this job
- `ix_saved_jobs_status`: Query by status
- `ix_saved_jobs_list_name`: Group by list
- `ix_saved_jobs_created_at`: Timeline queries
- `ix_saved_jobs_archived_at`: Archive status
- `ix_saved_jobs_user_status`: Composite for status filtering
- `ix_saved_jobs_user_created`: Composite for user timeline
- `ix_saved_jobs_user_list_status`: Composite for list management

#### `saved_jobs_lists`
Custom job organization lists for candidates.

**Columns**:
- `id` (UUID, PK): Unique list identifier
- `user_id` (UUID, FK): List owner
- `name` (VARCHAR): List name (e.g., "Dream Jobs", "Remote Only")
- `description` (VARCHAR): List description
- `icon` (VARCHAR): Icon name for UI
- `color` (VARCHAR): Color code for UI (hex)
- `is_default` (BOOLEAN): System default list
- `is_shared` (BOOLEAN): Shareable with others (future)
- `job_count` (INT): Denormalized count for performance
- `created_at` (TIMESTAMP): Creation timestamp
- `updated_at` (TIMESTAMP): Last update
- `archived_at` (TIMESTAMP): Archive timestamp

**Unique Constraint**: (user_id, name) - User can't have duplicate list names

**Indices**:
- `ix_saved_jobs_lists_user_id`: User's lists
- `ix_saved_jobs_lists_is_default`: Find default list
- `ix_saved_jobs_lists_created_at`: Timeline queries

### Foreign Keys
- `saved_jobs` → `saved_jobs_lists` (list_id): ON DELETE SET NULL
- `saved_jobs` → `positions` (position_id): ON DELETE CASCADE
- `saved_jobs` → `users` (user_id): ON DELETE CASCADE
- `saved_jobs_lists` → `users` (user_id): ON DELETE CASCADE

### Key Features
- **Job Organization**: Custom lists for categorizing opportunities
- **Engagement Tracking**: View and application status
- **Denormalized Data**: Fast access without joins
- **Notifications**: Opt-in job update alerts
- **Notes & Metadata**: Personal observations and AI match scores
- **Encryption**: Match analysis encrypted for privacy

### Usage Examples

```python
# Get candidate's saved jobs
saved_jobs = session.query(SavedJob).filter(
    SavedJob.user_id == user_id,
    SavedJob.status != "archived"
).order_by(SavedJob.created_at.desc()).all()

# Find unsaved jobs (for recommendations)
saved_job_ids = session.query(SavedJob.position_id).filter(
    SavedJob.user_id == user_id
).subquery()

unsaved = session.query(Position).filter(
    Position.id.notin_(saved_job_ids)
).all()

# Get jobs from specific list
list_jobs = session.query(SavedJob).filter(
    SavedJob.list_id == list_id,
    SavedJob.status == "saved"
).all()
```

---

## Migration 3: Enhanced Applications Tracking

**File**: `alembic/versions/c9a2b5e4f1d3_applications_enhanced_tracking.py`

**Models**: `app/models/application_tracking.py` - ApplicationEvent, ApplicationFeedback

### Purpose
Comprehensive pipeline analytics with detailed funnel tracking, engagement metrics, and structured feedback collection.

### Tables Created

#### `application_events`
Detailed activity log for every application lifecycle event.

**Columns**:
- `id` (UUID, PK): Event identifier
- `application_id` (UUID, FK): Associated application
- `user_id` (UUID, FK): User context
- `event_type` (VARCHAR): Type of event (see enum below)
- `event_data` (JSONB): Flexible event metadata
- `description` (VARCHAR): Human-readable event description
- `triggered_by_id` (UUID, FK): User who triggered event
- `actor_type` (VARCHAR): Who triggered (system, user, automation, ats_sync)
- `created_at` (TIMESTAMP): Event timestamp

**Indices**:
- `ix_application_events_application_id`: Events for an application
- `ix_application_events_user_id`: User's events
- `ix_application_events_event_type`: Events by type
- `ix_application_events_created_at`: Timeline queries
- `ix_application_events_triggered_by_id`: Events by actor
- `ix_application_events_app_type`: Composite for app event types
- `ix_application_events_app_created`: Composite for app timeline

**Event Types**:
- `status_changed`: Pipeline stage change
- `message_sent`: Outgoing communication
- `message_received`: Incoming communication
- `viewed`: Recruiter viewed application
- `interview_scheduled`: Interview booking
- `interview_completed`: Interview completion
- `offer_extended`: Offer sent
- `offer_accepted`: Offer accepted
- `offer_rejected`: Offer declined
- `rejected`: Application rejected
- `withdrawn`: Candidate withdrew
- `feedback_provided`: Feedback submitted
- `reassigned`: Reassigned to different recruiter
- `flagged`: Application flagged
- `unflagged`: Flag removed

#### `application_feedback`
Structured feedback from interviews and assessments.

**Columns**:
- `id` (UUID, PK): Feedback identifier
- `application_id` (UUID, FK): Associated application
- `feedback_stage` (VARCHAR): Pipeline stage (phone_screen, technical, onsite, etc.)
- `overall_rating` (INT): 1-5 scale rating
- `feedback_text` (TEXT, encrypted): Interviewer notes
- `structured_feedback` (JSONB): Structured rating criteria
- `provided_by_id` (UUID, FK): Interviewer/evaluator
- `provided_by_name` (VARCHAR): Cached name for performance
- `recommendation` (VARCHAR): proceed, maybe, reject
- `confidence_score` (FLOAT): Confidence in recommendation
- `created_at` (TIMESTAMP): Submission time
- `updated_at` (TIMESTAMP): Last update time

**Encryption**: `feedback_text` contains sensitive interviewer comments encrypted at rest.

**Indices**:
- `ix_application_feedback_application_id`: Feedback for app
- `ix_application_feedback_stage`: Feedback by stage
- `ix_application_feedback_provided_by_id`: Interviewer's feedback
- `ix_application_feedback_recommendation`: Feedback by decision
- `ix_application_feedback_created_at`: Timeline queries
- `ix_application_feedback_app_stage`: Composite for stage analysis

### Columns Added to Existing `applications` Table

**Resume Version Tracking**:
- `resume_version_id` (UUID, FK): Specific resume version applied with
- Index: `ix_applications_resume_version_id`

**Timeline Tracking**:
- `viewed_at` (TIMESTAMP): When recruiter first viewed
- `interview_scheduled_at` (TIMESTAMP): When interview was booked
- `rejected_at` (TIMESTAMP): When rejection sent
- `withdrawn_at` (TIMESTAMP): When candidate withdrew
- `offer_extended_at` (TIMESTAMP): When offer sent
- `offer_accepted_at` (TIMESTAMP): When offer accepted

**Rejection Handling**:
- `rejection_reason` (TEXT, encrypted): Why candidate was rejected
- `rejection_feedback` (TEXT, encrypted): Detailed feedback
- `can_reapply` (BOOLEAN): Whether candidate can reapply
- `reapply_after` (TIMESTAMP): Earliest reapplication date

**Scoring & Assessment**:
- `initial_match_score` (FLOAT): Initial AI match score
- `current_match_score` (FLOAT): Updated match score
- `fit_assessment` (JSONB): Structured fit analysis

**Communication**:
- `messages_count` (INT): Total messages exchanged
- `last_message_at` (TIMESTAMP): Last message timestamp
- `requires_response` (BOOLEAN): Awaiting candidate response

**Application Customization**:
- `custom_cover_letter` (TEXT, encrypted): Candidate's cover letter
- `application_answers` (JSONB): Answers to custom form questions

**Admin & Organization**:
- `stage_notes` (VARCHAR): Notes about current stage
- `priority` (VARCHAR): high, normal, low
- `is_flagged` (BOOLEAN): Flagged for attention
- `assigned_to_id` (UUID, FK): Assigned recruiter
- Index: `ix_applications_assigned_to_id`

**Additional Indices**:
- `ix_applications_viewed_at`: Timeline queries
- `ix_applications_interview_scheduled_at`: Interview scheduling
- `ix_applications_rejected_at`: Rejection tracking
- `ix_applications_priority`: Priority filtering
- `ix_applications_is_flagged`: Flagged items
- `ix_applications_requires_response`: Response tracking
- `ix_applications_position_stage`: Funnel analysis
- `ix_applications_stage_updated`: Timeline by stage
- `ix_applications_user_priority`: Priority by owner

### Foreign Keys
- `application_events.application_id` → `applications`: ON DELETE CASCADE
- `application_events.triggered_by_id` → `users`: ON DELETE SET NULL
- `application_feedback.application_id` → `applications`: ON DELETE CASCADE
- `application_feedback.provided_by_id` → `users`: ON DELETE CASCADE
- `applications.resume_version_id` → `resume_versions`: ON DELETE SET NULL
- `applications.assigned_to_id` → `users`: ON DELETE SET NULL

### Key Features
- **Event Logging**: Complete audit trail of all application activity
- **Pipeline Analytics**: Detailed funnel tracking at each stage
- **Engagement Metrics**: View, message, and response tracking
- **Feedback Management**: Structured feedback from multiple interviewers
- **PII Protection**: Sensitive feedback and rejection reasons encrypted
- **Performance Optimization**: Composite indices for common queries
- **Audit Trail**: Complete history of all changes

### Usage Examples

```python
# Get funnel metrics for a position
events = session.query(ApplicationEvent).filter(
    ApplicationEvent.event_type.in_([
        "status_changed",
        "interview_scheduled",
        "offer_extended"
    ]),
    Application.position_id == position_id
).join(Application).all()

# Get all feedback for an application
feedback = session.query(ApplicationFeedback).filter(
    ApplicationFeedback.application_id == application_id
).order_by(ApplicationFeedback.feedback_stage).all()

# Find applications requiring attention
pending = session.query(Application).filter(
    Application.requires_response == True,
    Application.user_id == user_id
).order_by(Application.priority.desc()).all()

# Timeline for single application
timeline = session.query(ApplicationEvent).filter(
    ApplicationEvent.application_id == application_id
).order_by(ApplicationEvent.created_at).all()
```

---

## Running Migrations

### Upgrade to Latest Version

```bash
cd backend
alembic upgrade head
```

### Upgrade to Specific Revision

```bash
# Apply just resume versioning
alembic upgrade a5f8c1d2e3b7

# Apply through saved jobs
alembic upgrade b7d9e2c1a3f6

# Apply all enhancements
alembic upgrade c9a2b5e4f1d3
```

### Rollback Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade a5f8c1d2e3b7

# Rollback all new migrations
alembic downgrade f3d9b27a1e64  # Previous base revision
```

### Check Migration Status

```bash
alembic current
alembic history --verbose
```

---

## Data Migration Strategies

### Resume Versions Migration

If migrating from existing resumes:

```python
from app.models.resume import Resume
from app.models.resume_version import ResumeVersion

# Create version 1 for each existing resume
for resume in session.query(Resume).all():
    version = ResumeVersion(
        resume_id=resume.id,
        user_id=resume.user_id,
        version_number=1,
        is_current=True,
        file_id=resume.file_id,
        file_type=resume.file_type,
        source_language=resume.source_language,
        parsed_data=resume.parsed_data,
        raw_narrative=resume.raw_narrative,
        supplementary=resume.supplementary,
        change_type="import",
        created_at=resume.created_at,
    )
    session.add(version)

session.commit()
```

### Saved Jobs Migration

New feature - no existing data to migrate. Initialize default lists for users:

```python
from app.models.saved_job import SavedJobsList
from app.models.user import User

for user in session.query(User).all():
    default_list = SavedJobsList(
        user_id=user.id,
        name="Default",
        is_default=True,
    )
    session.add(default_list)

session.commit()
```

---

## Performance Considerations

### Query Optimization

All migrations include composite indices for common queries:
- User + status combinations (saved jobs, applications)
- Timeline-based queries (created_at, stage transitions)
- Pipeline funnel analysis (position + stage)

### Encryption Overhead

PII fields use AES-256-GCM encryption:
- ~5-10% query overhead for encrypted fields
- Consider caching decrypted values in application layer
- Use DeterministicEncryptedText for queryable PII (if needed in future)

### Archive Considerations

All tables include nullable `archived_at` timestamp:
- Soft deletes preserve data for compliance
- Archived records automatically filtered in queries
- Regular archival cleanup for old records

---

## Security & Compliance

### PII Encryption

All personally identifiable information uses AES-256-GCM:
- **Resume versions**: parsed_data, raw_narrative, supplementary
- **Saved jobs**: relevance_metadata (match analysis)
- **Applications**: rejection_reason, rejection_feedback, custom_cover_letter
- **Feedback**: feedback_text (interviewer notes)

### Data Retention

- Active records: No purge
- Archived records: Keep per compliance requirements
- Events: Keep indefinitely for audit trail
- Feedback: Keep indefinitely per hiring compliance

### Access Control

Implement at application layer:
- Resume versions: Only user and authorized recruiters
- Saved jobs: Only user (private)
- Applications: Assigned recruiter + hiring team
- Feedback: Only hiring team and provided_by user

---

## Troubleshooting

### Migration Fails Due to Existing Constraints

If you encounter foreign key constraint errors:
```bash
# Check existing constraints
psql -U postgres -d truematch -c "\d applications"

# Disable constraint checks during migration (PostgreSQL)
ALTER TABLE applications DISABLE TRIGGER ALL;
alembic upgrade head
ALTER TABLE applications ENABLE TRIGGER ALL;
```

### Index Creation Timeout

For large existing tables, index creation can be slow:
```sql
-- Create indices concurrently without locking
CREATE INDEX CONCURRENTLY ix_large_table_new_column
ON large_table(new_column);
```

### Rollback Issues

If a rollback fails:
```bash
# Mark migration as complete without running downgrade
alembic stamp f3d9b27a1e64

# Manual cleanup of tables
psql -U postgres -d truematch -c "DROP TABLE IF EXISTS resume_versions CASCADE;"
```

---

## Next Steps

1. **Run migrations** in development environment first
2. **Test data access patterns** with new schema
3. **Create API endpoints** for new features
4. **Update frontend** to use new capabilities
5. **Deploy to staging** and validate with users
6. **Production deployment** with rollback plan
7. **Monitor performance** and adjust indices if needed

