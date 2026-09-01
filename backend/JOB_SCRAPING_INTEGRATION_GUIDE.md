# Job Scraping Integration Guide

**Integration Point:** Connect scraped/uploaded jobs to existing TrueMatch JD ingestion pipeline

---

## Overview

TrueMatch's existing `_process_jd()` pipeline already handles:
- ✅ Text extraction and normalization
- ✅ Semantic embedding generation
- ✅ Corpus learning (TF-IDF weighting)
- ✅ Job detail extraction (title, location, salary, etc.)
- ✅ Evidence enrichment
- ✅ Quality assessment
- ✅ Position creation with job evolution tracking

The job scraping system provides:
- ✅ Multiple data sources (APIs, web, CSV/JSON uploads)
- ✅ Standardized `JobPosting` data structure
- ✅ Deduplication via fingerprints
- ✅ Bulk processing capability

**Integration Strategy:** Feed scraped jobs into the existing pipeline as if they were manually uploaded.

---

## Current Pipeline Architecture

### Existing Flow
```
Resume/JD Upload
    ↓
IngestQueue.item created
    ↓
Autonomous Agent processes:
  - Extract text
  - Generate embeddings
  - Learn corpus patterns
  - Create Position record
    ↓
Position ready for use
```

### With Scraping Integration
```
Scraped/Uploaded Jobs
    ↓
JobPosting objects
    ↓
Deduplication check
    ↓
IngestQueue.item created (source="scraper" or "csv_upload")
    ↓
Autonomous Agent processes (same pipeline)
    ↓
Position ready for use
```

---

## Data Flow Details

### 1. JobPosting → IngestQueue

**File:** `app/tasks/scraping_processor.py` (new, Phase 4)

```python
from app.models.ingest import IngestQueue, IngestItemType
from app.scrapers import JobPosting

async def create_ingest_from_job_posting(
    job: JobPosting,
    batch_id: uuid.UUID | None = None,
    source_type: str = "scraper",  # or "csv_upload", "api_upload"
) -> IngestQueue:
    """
    Convert scraped JobPosting to IngestQueue item for processing.
    
    Args:
        job: JobPosting from scraper or upload
        batch_id: Reference to MassUploadBatch if from upload
        source_type: Source of the job data
    
    Returns:
        Created IngestQueue item
    """
    
    # Check for duplicates
    fingerprint = job.fingerprint_data()
    dedup = await db.execute(
        select(JobDeduplication)
        .where(JobDeduplication.fingerprint == fingerprint)
    )
    existing = dedup.scalar_one_or_none()
    
    if existing:
        # Update external IDs if new source
        if job.external_id and job.source not in existing.external_ids:
            existing.external_ids[job.source] = job.external_id
            existing.seen_count += 1
            existing.last_seen = datetime.now(timezone.utc)
            db.add(existing)
        
        # If already processed, return existing
        if existing.ingest_queue_item_id:
            return await db.get(IngestQueue, existing.ingest_queue_item_id)
    
    # Create new IngestQueue item
    item = IngestQueue(
        type=IngestItemType.jd,
        raw_content=job.description,
        metadata={
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "job_type": job.job_type,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "posted_date": job.posted_date.isoformat() if job.posted_date else None,
            "external_url": job.external_url,
            "external_id": job.external_id,
            "source": job.source,
            "source_type": source_type,
            "batch_id": str(batch_id) if batch_id else None,
        },
        source_reference=job.external_id or job.fingerprint_data(),
    )
    
    db.add(item)
    db.flush()  # Get ID before committing
    
    # Link deduplication record if new
    if not existing:
        dedup = JobDeduplication(
            fingerprint=fingerprint,
            external_ids={job.source: job.external_id} if job.external_id else {},
            ingest_queue_item_id=item.id,
        )
        db.add(dedup)
    else:
        existing.ingest_queue_item_id = item.id
        db.add(existing)
    
    await db.commit()
    return item
```

### 2. Batch Processing Integration

**File:** `app/tasks/upload_processor.py` (new, Phase 4)

```python
from celery import shared_task
from app.models.job_scraping import MassUploadBatch, BatchStatus

@shared_task
async def process_upload_batch(batch_id: str):
    """
    Process a mass upload batch through the scraping pipeline.
    
    Called by: Celery when batch is created
    """
    batch = await db.get(MassUploadBatch, uuid.UUID(batch_id))
    batch.status = BatchStatus.processing
    await db.commit()
    
    try:
        processor = MassUploadProcessor()
        errors_by_row = {}
        
        async for job, errors in processor.process_upload(
            batch.upload_type,
            read_file_content(batch.filename),  # Read actual file
            batch.field_mapping,
        ):
            batch.total_rows += 1
            
            if errors:
                errors_by_row[batch.total_rows] = errors
                batch.failed_rows += 1
                continue
            
            if not job:
                continue
            
            try:
                # Create IngestQueue item
                ingest_item = await create_ingest_from_job_posting(
                    job,
                    batch_id=batch.id,
                    source_type="csv_upload",
                )
                batch.processed_rows += 1
            except Exception as e:
                errors_by_row[batch.total_rows] = [str(e)]
                batch.failed_rows += 1
        
        batch.errors = errors_by_row
        batch.status = BatchStatus.completed
        
    except Exception as e:
        batch.status = BatchStatus.failed
        batch.errors = {"processing": [str(e)]}
    
    await db.commit()
```

### 3. Scraper Run Processing

**File:** `app/tasks/scraper_processor.py` (new, Phase 2-3)

```python
@shared_task
async def run_scraper(config_id: str):
    """
    Execute a configured scraper.
    
    Called by: Celery Beat on schedule
    """
    config = await db.get(JobScrapingConfig, uuid.UUID(config_id))
    
    run = ScrapingRun(
        config_id=config.id,
        status=BatchStatus.processing,
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    await db.flush()
    
    try:
        # Instantiate scraper
        scraper_class = get_scraper_class(config.source_type)
        scraper = scraper_class(config.config)
        
        # Validate connectivity
        await scraper.validate()
        
        # Scrape jobs
        jobs = await scraper.scrape({})
        run.jobs_found = len(jobs)
        
        # Process each job
        for job in jobs:
            try:
                ingest_item = await create_ingest_from_job_posting(
                    job,
                    source_type="scraper",
                )
                run.jobs_processed += 1
            except Exception as e:
                logger.error(f"Failed to process job: {str(e)}")
                run.jobs_failed += 1
        
        run.status = BatchStatus.completed
        
    except Exception as e:
        logger.error(f"Scraper failed: {str(e)}")
        run.status = BatchStatus.failed
        run.errors = {"scraping": [str(e)]}
    
    finally:
        run.completed_at = datetime.now(timezone.utc)
        db.add(run)
        await db.commit()
        await scraper.cleanup()
```

---

## Metadata Preservation

Key job metadata is stored in `IngestQueue.metadata` JSON field:

```json
{
  "title": "Senior Software Engineer",
  "company": "TechCorp",
  "location": "San Francisco, CA",
  "job_type": "Full-time",
  "salary_min": 120000,
  "salary_max": 180000,
  "posted_date": "2026-06-01T10:00:00Z",
  "external_url": "https://...",
  "external_id": "linkedin_123456",
  "source": "linkedin",
  "source_type": "scraper",
  "batch_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

This metadata is used by the Position creation logic to populate:
- `Position.title`
- `Position.company`
- `Position.location`
- `Position.employment_type`
- `Position.salary_min`
- `Position.salary_max`

---

## Deduplication Strategy

### Double-Check Deduplication

When processing each job:

1. **Fingerprint check** (before IngestQueue creation)
   - Hash of (title + company + description)
   - If exists and already processed → skip

2. **IngestQueue check** (by source_reference)
   - Ensure same external_id not processed twice

3. **Position check** (downstream)
   - Existing _process_jd() logic checks for duplicate JDs

### Tracking Duplicate Detection

```python
# In JobDeduplication record
{
  "fingerprint": "sha256_hash",
  "external_ids": {
    "linkedin": "linkedin_123456",
    "usajobs": "usajobs_789012",
    "csv_upload": "batch_uuid_5"
  },
  "ingest_queue_item_id": "uuid",
  "first_seen": "2026-06-01T10:00:00Z",
  "last_seen": "2026-06-03T14:30:00Z",
  "seen_count": 3
}
```

---

## Error Handling

### Graceful Degradation

If a single job fails, batch continues:

```python
errors_by_row = {
    "5": ["Missing description field"],
    "12": ["Invalid salary format"],
    "18": ["Failed to create IngestQueue: connection timeout"],
}

batch.errors = errors_by_row
batch.failed_rows = 3
batch.processed_rows = 97
```

### Retry Strategy

For scraper failures:
- Transient errors (network, timeouts) → Auto-retry (3 attempts)
- Permanent errors (config, auth) → Log and alert admin
- Rate limiting → Back off and retry next scheduled run

---

## Corpusviz Learning Integration

When jobs are processed through `_process_jd()`:

1. **Corpus Learning Phase**
   - Job description is parsed
   - TF-IDF weights learned for job-specific terms
   - Patterns stored in `CorpusPattern` table

2. **Candidate Matching Phase**
   - Resume processed against learned corpus patterns
   - Skill matches weighted by TF-IDF importance
   - Semantic embeddings compared

**Effect:** Each scraped job enriches the matching model.

---

## Implementation Checklist

### Phase 1 (Foundation) ✅
- [x] Database models
- [x] Scraper base classes
- [x] Mass upload processor
- [x] API endpoints
- [x] Unit tests

### Phase 2-3 (Scrapers)
- [ ] API-based scrapers (USAJOBS, ZipRecruiter)
- [ ] Web scrapers (LinkedIn, Indeed, Glassdoor - legal review required)
- [ ] Celery Beat integration

### Phase 4 (Integration)
- [ ] `create_ingest_from_job_posting()` function
- [ ] `process_upload_batch()` Celery task
- [ ] `run_scraper()` Celery Beat task
- [ ] Integration tests
- [ ] End-to-end testing

### Deployment
- [ ] Database migrations
- [ ] Celery worker configuration
- [ ] Celery Beat scheduler configuration
- [ ] Error monitoring setup
- [ ] Admin UI integration

---

## Example: Processing a CSV Upload

```
1. User uploads jobs.csv with field mapping
   ↓
2. MassUploadBatch created (status=pending)
   ↓
3. process_upload_batch(batch_id) Celery task started
   ↓
4. For each row in CSV:
   a. Parse and validate fields
   b. Convert to JobPosting
   c. Check fingerprint for duplicates
   d. Create IngestQueue item with metadata
   e. Update batch progress
   ↓
5. Autonomous agent processes IngestQueue:
   a. Extracts text
   b. Generates embeddings
   c. Learns corpus patterns
   d. Creates Position with salary, location, etc.
   ↓
6. Position available for assessments
   ↓
7. Batch status updated to "completed"
```

---

## Configuration for Celery

### `app/celery_app.py` Addition

```python
from celery.schedules import crontab
from app.models.job_scraping import JobSourceType

# Beat schedule for automated scraping
app.conf.beat_schedule = {
    # Existing tasks...
    
    # Job scraping tasks (Phase 2+)
    'scrape-usajobs-hourly': {
        'task': 'app.tasks.scraper_processor.run_scraper',
        'schedule': crontab(minute=0),  # Every hour
        'kwargs': {'config_id': 'USAJOBS_CONFIG_ID'},
    },
    
    'scrape-linkedin-daily': {
        'task': 'app.tasks.scraper_processor.run_scraper',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        'kwargs': {'config_id': 'LINKEDIN_CONFIG_ID'},
    },
    
    'cleanup-old-runs': {
        'task': 'app.tasks.scraper_processor.cleanup_old_runs',
        'schedule': crontab(hour=3, minute=0),  # Daily cleanup
    },
}
```

---

## Monitoring & Observability

### Key Metrics to Track

```python
# In logging/monitoring
logger.info("Job scraped", extra={
    "batch_id": batch_id,
    "source": job.source,
    "jobs_found": jobs_found,
    "jobs_processed": jobs_processed,
    "duplicates_detected": duplicates,
    "processing_time_ms": elapsed_ms,
})
```

### Alerts

1. **High failure rate** (>10% of batch failing)
2. **Scraper connectivity** (429 rate limit, 403 forbidden)
3. **Deduplication issues** (duplicate fingerprints)
4. **IngestQueue backup** (queue size > 1000)

---

## Security Considerations

### Data Privacy
- PII (phone numbers, emails) in job descriptions should be handled per existing encryption policy
- Salary information encrypted at rest

### Rate Limiting
- Respect `get_rate_limit()` responses from scrapers
- Enforce min request delays (15 seconds for web scrapers)
- Auto-disable scrapers after repeated 429/403 responses

### Legal Compliance
- Track legal approval status
- Log all scraping activity
- Maintain audit trail of data sources
- Support opt-out per job board

---

## Summary

Integration points between scraping system and existing pipeline:

✅ **Input:** JobPosting objects from scrapers/uploads  
✅ **Processing:** Existing `_process_jd()` pipeline  
✅ **Output:** Position records ready for assessments  
✅ **Deduplication:** Fingerprint-based tracking  
✅ **Metadata:** Preserved in IngestQueue for later reference  
✅ **Monitoring:** Full audit trail and error tracking  

**Key Implementation Files (Phase 4):**
- `app/tasks/scraping_processor.py` — Convert JobPosting → IngestQueue
- `app/tasks/upload_processor.py` — Celery task for batch processing
- `app/tasks/scraper_processor.py` — Celery Beat task for scheduled scraping

---

**Last Updated:** June 3, 2026
