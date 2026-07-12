# Database Migrations Quick Reference

## Summary of Changes

### Three Sequential Migrations Created

| Migration ID | File | Purpose | Tables | Models |
|---|---|---|---|---|
| `a5f8c1d2e3b7` | `a5f8c1d2e3b7_resume_versioning.py` | Resume version history tracking | `resume_versions` | `resume_version.py` |
| `b7d9e2c1a3f6` | `b7d9e2c1a3f6_saved_jobs_tracking.py` | Job curation and organization | `saved_jobs`, `saved_jobs_lists` | `saved_job.py` |
| `c9a2b5e4f1d3` | `c9a2b5e4f1d3_applications_enhanced_tracking.py` | Pipeline analytics & feedback | `application_events`, `application_feedback` | `application_tracking.py` |

## File Locations

```
backend/
├── alembic/
│   └── versions/
│       ├── a5f8c1d2e3b7_resume_versioning.py
│       ├── b7d9e2c1a3f6_saved_jobs_tracking.py
│       └── c9a2b5e4f1d3_applications_enhanced_tracking.py
├── app/
│   └── models/
│       ├── resume_version.py
│       ├── saved_job.py
│       └── application_tracking.py
└── DATABASE_MIGRATIONS.md
```

## Key Features by Migration

### Migration 1: Resume Versioning

**Problem Solved**: Track all resume changes with complete audit trail

**New Tables**:
- `resume_versions` - Complete version history

**Features**:
- Version numbering (1, 2, 3, ...)
- Current version tracking
- Quality scoring over time
- Change type tracking (upload, edit, ai_enhancement, import)
- Full PII encryption
- Multi-language support

**PII Encrypted**: ✓ parsed_data, raw_narrative, supplementary

**Key Indices**: 8 indices including composite user+current, resume+timestamp

**Use Cases**:
- Roll back to previous resume versions
- Track resume quality improvements
- Compare versions side-by-side
- Audit trail for compliance

---

### Migration 2: Saved Jobs Tracking

**Problem Solved**: Enable candidates to save and organize job opportunities

**New Tables**:
- `saved_jobs` - User's saved job postings
- `saved_jobs_lists` - Custom job organization lists

**Features**:
- Status tracking (saved, viewed, applied, archived, rejected)
- Custom lists for organization (Dream Jobs, Remote Only, etc.)
- Denormalized job data for performance
- Match score and relevance analysis
- Notification preferences
- Default list creation

**PII Encrypted**: ✓ relevance_metadata (match analysis)

**Key Indices**: 9 indices on saved_jobs, 3 on saved_jobs_lists

**Unique Constraints**:
- User can only save each job once
- User can't have duplicate list names

**Use Cases**:
- Candidate job wishlist
- Job categorization and filtering
- Engagement tracking
- Job recommendation engine integration

---

### Migration 3: Enhanced Applications Tracking

**Problem Solved**: Detailed pipeline analytics and structured feedback collection

**New Tables**:
- `application_events` - Activity log for all application events
- `application_feedback` - Structured interviewer feedback

**Enhanced `applications` Table With**:
- Resume version reference (track which version applied)
- Timeline tracking (viewed, interview scheduled, rejected, offer accepted)
- Rejection handling (reason, feedback, reapply eligibility)
- Match scores (initial and current)
- Communication metrics (message count, requires response)
- Custom form answers and cover letters
- Priority and flagging for admin use
- Recruiter assignment tracking

**Features**:
- Comprehensive event logging (14+ event types)
- Multi-interviewer feedback collection
- Rating and recommendation tracking
- Confidence scoring on decisions
- Flexible event metadata (JSONB)
- Actor tracking (system, user, automation, ats_sync)

**PII Encrypted**: ✓ rejection_reason, rejection_feedback, feedback_text, custom_cover_letter

**Key Indices**: 
- `application_events`: 7 indices
- `application_feedback`: 6 indices
- `applications`: 12 new indices

**Use Cases**:
- Pipeline funnel analysis
- Automated workflow triggers
- Compliance and audit trails
- Interview performance tracking
- Communication automation
- Talent intelligence

---

## Data Integrity

### Foreign Keys (Cascading Deletes)

```
resume_versions
  ├─→ resumes (ON DELETE CASCADE)
  ├─→ users (ON DELETE CASCADE)
  └─→ users.created_by (ON DELETE SET NULL)

saved_jobs
  ├─→ users (ON DELETE CASCADE)
  ├─→ positions (ON DELETE CASCADE)
  └─→ saved_jobs_lists (ON DELETE SET NULL)

saved_jobs_lists
  └─→ users (ON DELETE CASCADE)

application_events
  ├─→ applications (ON DELETE CASCADE)
  ├─→ users (ON DELETE CASCADE)
  └─→ users.triggered_by (ON DELETE SET NULL)

application_feedback
  ├─→ applications (ON DELETE CASCADE)
  └─→ users.provided_by (ON DELETE CASCADE)

applications (additions)
  ├─→ resume_versions (ON DELETE SET NULL)
  └─→ users.assigned_to (ON DELETE SET NULL)
```

### Encryption Implementation

All PII uses AES-256-GCM via `EncryptedText` and `EncryptedJSON` types:

```python
# Application layer handles transparent encryption/decryption
parsed_data: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
```

No plaintext storage of:
- Resume content (parsed_data, raw_narrative, supplementary)
- Match analysis (relevance_metadata)
- Rejection reasons and feedback
- Interview notes

---

## Migration Execution Commands

### View Current Status
```bash
cd backend
alembic current              # Show current revision
alembic history -v           # Show all revisions
```

### Apply All Migrations
```bash
alembic upgrade head
# Or specifically:
alembic upgrade c9a2b5e4f1d3
```

### Apply Selectively
```bash
# Just resume versioning
alembic upgrade a5f8c1d2e3b7

# Add saved jobs on top
alembic upgrade b7d9e2c1a3f6

# Add enhanced tracking on top
alembic upgrade c9a2b5e4f1d3
```

### Rollback
```bash
# Last 1 migration
alembic downgrade -1

# Last 2 migrations
alembic downgrade -2

# All 3 new migrations
alembic downgrade f3d9b27a1e64

# To specific revision
alembic downgrade b7d9e2c1a3f6
```

---

## Schema Visualization

### Resume Versioning Data Flow

```
User
  ↓
Resume (base record)
  ↓
ResumeVersion 1 (v=1, is_current=true, file_id=...)
  ├─ ResumeVersion 2 (v=2, is_current=false)
  └─ ResumeVersion 3 (v=3, is_current=true)  ← Can switch to old version
```

### Saved Jobs Data Flow

```
User
  ├─ SavedJobsList "Dream Jobs"
  │   ├─ SavedJob (status=saved)
  │   ├─ SavedJob (status=viewed)
  │   └─ SavedJob (status=applied)
  └─ SavedJobsList "Remote Only"
      ├─ SavedJob (status=saved)
      └─ SavedJob (status=archived)
```

### Applications Tracking Data Flow

```
Application
  ├─ Application.resume_version_id → ResumeVersion
  ├─ Application.assigned_to_id → User (recruiter)
  │
  ├─ ApplicationEvent (status_changed)
  ├─ ApplicationEvent (viewed)
  ├─ ApplicationEvent (interview_scheduled)
  ├─ ApplicationEvent (feedback_provided)
  │
  ├─ ApplicationFeedback (phone_screen, rating=4)
  ├─ ApplicationFeedback (technical, rating=5, recommendation=proceed)
  └─ ApplicationFeedback (onsite, rating=4, recommendation=proceed)
```

---

## Performance Optimizations Included

### Composite Indices Strategy

**Resume Versions**:
- `(user_id, is_current)` - Find user's current version O(1)
- `(resume_id, created_at)` - Timeline queries O(1)

**Saved Jobs**:
- `(user_id, status)` - Filter user's jobs by status O(1)
- `(user_id, list_name, status)` - Advanced filtering O(1)

**Applications**:
- `(position_id, stage)` - Funnel analysis O(1)
- `(stage, updated_at)` - Timeline by stage O(1)
- `(user_id, priority)` - Priority filtering O(1)

### Denormalization for Speed

Cached at save time to avoid joins:
- `saved_jobs.job_title`, `company_name` - Avoid position join
- `saved_jobs_lists.job_count` - Count without query
- `application_feedback.provided_by_name` - Avoid user lookup

### Archive Strategy

All tables support soft deletes via nullable `archived_at`:
- No permanent data loss
- Compliance-ready data retention
- `WHERE archived_at IS NULL` automatically filters active records

---

## Encryption Security

### Key Derivation

Uses `cryptography` library's AES-256-GCM:
- Key from `ENCRYPTION_KEY` environment variable
- Nonce randomized per encryption (irreversible)
- Authentication tag for integrity verification

### Implementation

```python
# Transparent at ORM layer
from app.models._types import EncryptedText, EncryptedJSON

# Automatic encryption on write
resume.raw_narrative = "sensitive text"  # Auto-encrypted

# Automatic decryption on read
text = resume.raw_narrative  # Transparently decrypted
```

### No Query Access

Encrypted fields cannot be queried:
```python
# ❌ This won't work (field is encrypted)
session.query(Resume).filter(
    Resume.raw_narrative.like("%python%")
).all()

# ✓ Use encrypted fields for display only
# ✓ Use unencrypted categorical fields for queries
```

---

## Testing the Migrations

### Pre-Migration Testing

```bash
# Create test database
createdb truematch_test

# Run migrations
DATABASE_URL="postgresql://user:pass@localhost/truematch_test" \
alembic upgrade head

# Test data insertion
pytest tests/test_migrations.py
```

### Data Consistency Checks

```sql
-- Check resume version consistency
SELECT resume_id, COUNT(*) as version_count, 
       COUNT(CASE WHEN is_current THEN 1 END) as current_count
FROM resume_versions
GROUP BY resume_id
HAVING COUNT(CASE WHEN is_current THEN 1 END) != 1;

-- Check saved jobs uniqueness
SELECT user_id, position_id, COUNT(*)
FROM saved_jobs
WHERE archived_at IS NULL
GROUP BY user_id, position_id
HAVING COUNT(*) > 1;

-- Check event integrity
SELECT COUNT(*) as event_count,
       COUNT(DISTINCT application_id) as app_count
FROM application_events;
```

---

## Common Issues & Solutions

### Issue: Migration Fails with Constraint Error
**Solution**: 
```bash
# Check existing constraints
psql -c "\d applications"

# Manually disable during migration
psql -c "ALTER TABLE applications DISABLE TRIGGER ALL;"
alembic upgrade head
psql -c "ALTER TABLE applications ENABLE TRIGGER ALL;"
```

### Issue: Index Creation Timeout
**Solution**: Use concurrent index creation
```sql
CREATE INDEX CONCURRENTLY ix_name ON table(column);
```

### Issue: Rollback Leaves Orphaned Indices
**Solution**: Verify clean state
```bash
# Check for leftover indices
psql -c "\di resume_versions*"

# Clean up manually if needed
psql -c "DROP INDEX IF EXISTS ix_resume_versions_user_id;"
```

---

## Integration Checklist

- [ ] Run migrations in development
- [ ] Verify schema with `alembic history -v`
- [ ] Create SQLAlchemy models (completed)
- [ ] Create API endpoints for new features
- [ ] Update frontend components
- [ ] Add tests for new tables
- [ ] Test encryption/decryption
- [ ] Load test with realistic data volume
- [ ] Run on staging database
- [ ] Create rollback plan
- [ ] Deploy to production
- [ ] Monitor performance metrics
- [ ] Verify data integrity
- [ ] Update documentation

---

## Additional Resources

- **Full Documentation**: See `DATABASE_MIGRATIONS.md`
- **Models Reference**: `app/models/resume_version.py`, `saved_job.py`, `application_tracking.py`
- **Migration Files**: `alembic/versions/a5f*.py`, `b7d*.py`, `c9a*.py`
- **Encryption Docs**: `app/models/_types.py`

