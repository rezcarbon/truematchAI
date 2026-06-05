# Job Scraping + Mass Upload Implementation Plan

**Status:** Implementation-Ready  
**Legal Risk Level:** Medium-High (due to direct scraping component)  
**Timeline:** 8-12 weeks for full implementation  
**Architecture:** Hybrid (Safe APIs + Direct Scraping + Mass Upload)

---

## Overview

### What We're Building

1. **Multi-Source Job Ingestion Engine**
   - Safe APIs (USAJOBS, ZipRecruiter, TheirStack)
   - Direct web scraping (LinkedIn, Indeed, Glassdoor) - *with warnings*
   - Mass upload system (CSV, JSON, API, web form)
   - Unified pipeline for all sources

2. **Flexible Mass Upload System**
   - CSV/Excel import with field mapping
   - JSON file batch upload
   - REST API for programmatic bulk import
   - Web form for paste-and-parse

3. **Unified Processing Pipeline**
   - All sources → consistent JD processing
   - Quality analysis, improvement, versioning
   - TF-IDF corpus learning
   - Candidate matching

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    JOB INGESTION SOURCES                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SAFE APIS              DIRECT SCRAPING       MASS UPLOAD       │
│  ─────────              ───────────────       ──────────       │
│  • USAJOBS              • LinkedIn             • CSV/Excel      │
│  • ZipRecruiter         • Indeed               • JSON           │
│  • TheirStack           • Glassdoor            • API POST       │
│  • Direct partners      • Others               • Web form       │
│                                                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  VALIDATION & PARSING  │
        │  ──────────────────    │
        │  • Extract text        │
        │  • Normalize fields    │
        │  • Validate data       │
        │  • Deduplication       │
        └────────────┬───────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │ EXISTING JD PIPELINE   │
        │ ──────────────────────  │
        │ • Quality analysis      │
        │ • Requirement extract   │
        │ • JD improvement        │
        │ • TF-IDF corpus learn   │
        │ • Semantic embeddings   │
        │ • Store in DB           │
        └────────────┬───────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  CANDIDATE MATCHING    │
        │  ──────────────────    │
        │ • Job recommend        │
        │ • Auto-matching        │
        │ • Governance gating    │
        └────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-3)

#### 1.1 Data Models & Database

**New Models:**
- `JobScrapingConfig` - Scraper configuration per source
- `ScrapingJob` - Track each scraping run (started, completed, errors)
- `MassUploadBatch` - Track CSV/JSON upload batches
- `JobDeduplication` - Fingerprints to prevent duplicates
- `UploadMapping` - Field mapping configuration for CSV/JSON

**Database Migrations:**
```sql
-- New tables
CREATE TABLE job_scraping_config (
    id UUID PRIMARY KEY,
    source_type ENUM('usajobs', 'ziprecruiter', 'theirstack', 'linkedin', 'indeed', 'glassdoor'),
    enabled BOOLEAN,
    config JSONB,  -- API keys, filters, etc.
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    created_at TIMESTAMP
);

CREATE TABLE scraping_job (
    id UUID PRIMARY KEY,
    config_id UUID REFERENCES job_scraping_config,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status ENUM('pending', 'running', 'completed', 'failed'),
    jobs_found INT,
    jobs_processed INT,
    errors TEXT[],
    created_at TIMESTAMP
);

CREATE TABLE mass_upload_batch (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES "user"(id),
    upload_type ENUM('csv', 'json', 'api'),
    filename VARCHAR(255),
    status ENUM('pending', 'processing', 'completed', 'failed'),
    total_rows INT,
    processed_rows INT,
    failed_rows INT,
    errors JSONB,
    created_at TIMESTAMP
);
```

**Estimated effort:** 4-6 hours

---

#### 1.2 Base Scraper Infrastructure

Create modular scraper architecture:

```python
# /app/workers/agents/job_scraper_base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class JobPosting:
    """Normalized job posting format"""
    title: str
    description: str
    company: str
    location: str | None = None
    job_type: str | None = None  # full-time, contract, etc.
    salary_min: int | None = None
    salary_max: int | None = None
    posted_date: datetime | None = None
    external_url: str | None = None
    external_id: str | None = None  # For deduplication
    source: str = "unknown"  # usajobs, linkedin, indeed, etc.

class JobScraper(ABC):
    """Base class for all job scrapers"""
    
    @abstractmethod
    async def scrape(self, filters: dict) -> list[JobPosting]:
        """Scrape jobs from source. Returns normalized postings."""
        pass
    
    @abstractmethod
    async def validate(self) -> bool:
        """Validate scraper configuration (API keys, etc.)"""
        pass
    
    @abstractmethod
    async def get_rate_limit(self) -> dict:
        """Return rate limit info: requests_per_minute, remaining, etc."""
        pass

# Concrete implementations
class USAJobsScraper(JobScraper):
    """USAJOBS API scraper (safe)"""
    pass

class ZipRecruiterScraper(JobScraper):
    """ZipRecruiter API scraper (safe)"""
    pass

class LinkedInScraper(JobScraper):
    """LinkedIn direct scraper (risky - legal warnings)"""
    pass

class IndeedScraper(JobScraper):
    """Indeed direct scraper (risky - legal warnings)"""
    pass

class GlassdoorScraper(JobScraper):
    """Glassdoor direct scraper (risky - legal warnings)"""
    pass
```

**Estimated effort:** 8-10 hours

---

#### 1.3 Mass Upload System

Create flexible CSV/JSON/API import:

```python
# /app/workers/agents/mass_upload.py

class MassUploadProcessor:
    """Process CSV, JSON, and API-based bulk job uploads"""
    
    async def process_csv(
        self,
        file_path: str,
        field_mapping: dict,  # Maps CSV columns to JobPosting fields
        batch_id: UUID,
    ) -> list[JobPosting]:
        """
        Parse CSV file and convert to JobPosting objects
        field_mapping example:
        {
            "Job Title": "title",
            "Job Description": "description",
            "Company Name": "company",
            "Location": "location",
        }
        """
        pass
    
    async def process_json(
        self,
        file_path: str,
        batch_id: UUID,
    ) -> list[JobPosting]:
        """
        Parse JSON array of job objects
        JSON format:
        [
            {
                "title": "Engineer",
                "description": "...",
                "company": "Acme Corp",
                ...
            }
        ]
        """
        pass
    
    async def process_batch(
        self,
        jobs: list[JobPosting],
        batch_id: UUID,
        skip_duplicates: bool = True,
    ) -> dict:
        """
        Process a batch of jobs through the full pipeline
        Returns: {
            "processed": int,
            "failed": int,
            "errors": list,
            "ingest_queue_items": list[UUID],
        }
        """
        pass
```

**API Endpoints:**
```python
# /app/api/v1/jobs/upload.py

@router.post("/upload/csv")
async def upload_csv(
    file: UploadFile,
    field_mapping: str,  # JSON string of field mapping
    user: CurrentUser,
    db: DBSession,
) -> UploadResponse:
    """
    Upload CSV file with job postings
    Returns batch ID for tracking
    """
    pass

@router.post("/upload/json")
async def upload_json(
    file: UploadFile,
    user: CurrentUser,
    db: DBSession,
) -> UploadResponse:
    """Upload JSON file with job array"""
    pass

@router.post("/upload/bulk")
async def upload_bulk_api(
    jobs: list[JobPosting],
    user: CurrentUser,
    db: DBSession,
) -> UploadResponse:
    """
    Programmatic bulk import via API
    For partners and integrations
    """
    pass

@router.get("/upload/batch/{batch_id}")
async def get_upload_status(
    batch_id: UUID,
    user: CurrentUser,
    db: DBSession,
) -> UploadStatus:
    """Track status of a bulk upload"""
    pass
```

**Estimated effort:** 12-16 hours

---

### Phase 2: Safe Scraping APIs (Weeks 4-6)

#### 2.1 USAJOBS Scraper

```python
# /app/workers/agents/scrapers/usajobs_scraper.py

class USAJobsScraper(JobScraper):
    """
    USAJOBS API scraper (SAFE)
    Reference: https://developer.usajobs.gov/
    """
    
    async def scrape(self, filters: dict) -> list[JobPosting]:
        """
        Scrape from USAJOBS API
        filters: {
            "keyword": "engineer",
            "location": "San Francisco, CA",
            "agency": optional,
            ...
        }
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.usajobs.gov/api/search",
                params=filters,
                headers={"Authorization-Key": self.config.api_key},
            )
        
        jobs = response.json()["SearchResult"]["SearchResultItems"]
        
        return [
            JobPosting(
                title=job["MatchedObjectDescriptor"]["PositionTitle"],
                description=job["MatchedObjectDescriptor"]["PositionRemuneration"],
                company=job["MatchedObjectDescriptor"]["OrganizationName"],
                location=job["MatchedObjectDescriptor"]["JobLocationCity"],
                external_url=job["MatchedObjectDescriptor"]["ApplyURI"][0],
                external_id=job["MatchedObjectDescriptor"]["PositionID"],
                posted_date=datetime.fromisoformat(job["MatchedObjectDescriptor"]["PublicationStartDate"]),
                source="usajobs",
            )
            for job in jobs
        ]
    
    async def validate(self) -> bool:
        """Validate USAJOBS API key"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.usajobs.gov/api/codelist/countries",
                headers={"Authorization-Key": self.config.api_key},
            )
        return response.status_code == 200
```

**Estimated effort:** 6-8 hours

---

#### 2.2 ZipRecruiter & Aggregator Scrapers

Similar structure to USAJOBS:
- `ZipRecruiterScraper` - Official API
- `TheirStackScraper` - Aggregator with legal partnerships

**Estimated effort:** 8-12 hours

---

### Phase 3: Direct Scraping (Weeks 7-9)

#### 3.1 Direct Web Scrapers

**⚠️ CRITICAL: Add Legal Warnings**

```python
# /app/workers/agents/scrapers/direct_scrapers.py

LEGAL_WARNING = """
⚠️ WARNING: Direct scraping of LinkedIn, Indeed, and Glassdoor violates their
Terms of Service and carries significant legal risk:

1. Breach of Contract: ToS violations are enforceable
2. Litigation Risk: LinkedIn actively enforces (2025 enforcement)
3. Privacy Laws: GDPR/CCPA apply regardless of ToS
4. Settlement Risk: $500K-$1M in potential damages
5. Data Destruction: Settlement typically requires destroying scraped data

This feature is for RESEARCH PURPOSES ONLY. Ensure your legal team has
approved before deploying to production.

Use safe alternatives when possible: USAJOBS API, ZipRecruiter API, etc.
"""

class LinkedInScraper(JobScraper):
    """
    LinkedIn direct scraper (HIGH LEGAL RISK)
    
    ⚠️ This scraper violates LinkedIn's ToS and carries significant
       legal risk. Use only with explicit legal approval.
    """
    
    def __init__(self, config):
        print(LEGAL_WARNING)
        self.config = config
        self.session = None
    
    async def scrape(self, filters: dict) -> list[JobPosting]:
        """
        Scrape LinkedIn jobs page
        Uses Selenium/Playwright to bypass client-side rendering
        """
        # Implementation with rate limiting, delays, user-agent rotation
        # See detailed implementation below
        pass
    
    async def validate(self) -> bool:
        """Validate LinkedIn session"""
        # Check if account can login and isn't rate-limited
        pass

class IndeedScraper(JobScraper):
    """Indeed direct scraper (HIGH LEGAL RISK)"""
    pass

class GlassdoorScraper(JobScraper):
    """Glassdoor direct scraper (VERY HIGH LEGAL RISK)"""
    pass
```

**Implementation Details:**

```python
# Use Playwright for JavaScript-heavy sites
# Install: pip install playwright

class LinkedInScraperImpl(JobScraper):
    
    async def scrape_with_playwright(self, search_url: str) -> list[JobPosting]:
        """
        Scrape using Playwright (headless browser)
        
        Rate limiting:
        - 1 request every 10-15 seconds
        - Respect Retry-After headers
        - Back off on 429 responses
        - Random user agents and delays
        """
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            )
            
            await page.goto(search_url, wait_until="networkidle")
            
            # Scroll to load more results
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(random.uniform(2, 4))
            
            # Extract job listings
            jobs = await page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll('.job-card')).map(el => ({
                        title: el.querySelector('.job-title').innerText,
                        company: el.querySelector('.company-name').innerText,
                        description: el.querySelector('.job-snippet').innerText,
                        url: el.href,
                    }));
                }
            """)
            
            await browser.close()
            return jobs
```

**Estimated effort:** 16-20 hours

**⚠️ NOTE:** Direct scraping implementation should include:
- Comprehensive legal warnings
- Rate limiting and respectful request patterns
- Error handling and retry logic
- IP rotation capabilities (optional, risky)
- Account lockout detection
- User consent requirements

---

### Phase 4: Unified Pipeline & Scheduling (Weeks 10-12)

#### 4.1 Unified Job Processing

```python
# /app/workers/agents/job_processor.py

class UnifiedJobProcessor:
    """
    Process jobs from ANY source through the existing JD pipeline
    Reuses: _process_jd, corpus learning, semantic embeddings, etc.
    """
    
    async def process_jobs(
        self,
        jobs: list[JobPosting],
        source_config: JobScrapingConfig,
        batch_id: UUID,
    ) -> dict:
        """
        Process batch of jobs through full pipeline
        Returns: {
            "processed": int,
            "failed": int,
            "ingest_items": list[IngestQueueItem],
        }
        """
        
        for job in jobs:
            # Deduplication
            if await self.is_duplicate(job):
                continue
            
            # Convert to JD text + metadata
            jd_text = self._format_jd(job)
            
            # Reuse existing _process_jd from ingest pipeline
            from app.workers.agents.ingest_jd import _process_jd
            
            await _process_jd(
                db=self.db,
                jd_text=jd_text,
                source=IngestSource.scrape,
                source_ref=job.external_url,
                source_config_id=source_config.id,
                batch_id=batch_id,
                title_hint=job.title,
                company_hint=job.company,
            )
```

#### 4.2 Celery Beat Scheduling

```python
# /app/workers/celery_app.py

beat_schedule = {
    # ... existing ...
    
    # Safe scrapers (run frequently)
    "scrape-usajobs": {
        "task": "app.workers.agents.job_scraper_scheduler.scrape_source",
        "schedule": 21600,  # Every 6 hours
        "kwargs": {"source_type": "usajobs"},
    },
    "scrape-ziprecruiter": {
        "task": "app.workers.agents.job_scraper_scheduler.scrape_source",
        "schedule": 21600,  # Every 6 hours
        "kwargs": {"source_type": "ziprecruiter"},
    },
    
    # Direct scrapers (run less frequently, if enabled)
    "scrape-linkedin": {
        "task": "app.workers.agents.job_scraper_scheduler.scrape_source",
        "schedule": 86400,  # Once per day
        "kwargs": {"source_type": "linkedin", "require_legal_approval": True},
    },
    "scrape-indeed": {
        "task": "app.workers.agents.job_scraper_scheduler.scrape_source",
        "schedule": 86400,  # Once per day
        "kwargs": {"source_type": "indeed", "require_legal_approval": True},
    },
}
```

**Estimated effort:** 8-10 hours

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] Database migrations (IngestQueueItem extensions, new models)
- [ ] Job scraper base classes
- [ ] Mass upload CSV processor
- [ ] Mass upload JSON processor
- [ ] Mass upload API endpoints
- [ ] Upload batch tracking & status API
- [ ] Tests for data models

### Phase 2: Safe Scraping
- [ ] USAJOBS scraper implementation
- [ ] ZipRecruiter scraper implementation
- [ ] TheirStack aggregator integration
- [ ] Scraper configuration UI
- [ ] Celery Beat scheduling
- [ ] Tests for each scraper

### Phase 3: Direct Scraping
- [ ] LinkedIn scraper (with legal warnings)
- [ ] Indeed scraper (with legal warnings)
- [ ] Glassdoor scraper (with legal warnings)
- [ ] Rate limiting & respectful patterns
- [ ] Account lockout detection
- [ ] Legal disclaimer UI
- [ ] Tests for direct scrapers

### Phase 4: Integration
- [ ] Unified job processor
- [ ] Deduplication logic
- [ ] Celery Beat scheduling for all sources
- [ ] Admin dashboard for scraper management
- [ ] Monitoring & alerting
- [ ] E2E tests

---

## Configuration Example

```python
# /app/config.py

# Job Scraping Configuration
class JobScrapingSettings:
    # Safe scrapers
    usajobs_enabled: bool = True
    usajobs_api_key: str = ""
    usajobs_poll_hours: int = 6
    
    ziprecruiter_enabled: bool = False
    ziprecruiter_api_key: str = ""
    ziprecruiter_poll_hours: int = 6
    
    theirstack_enabled: bool = False
    theirstack_api_key: str = ""
    theirstack_poll_hours: int = 6
    
    # Direct scrapers (RISKY - requires legal approval)
    linkedin_scraping_enabled: bool = False
    linkedin_legal_approved: bool = False  # Must be True to enable
    linkedin_poll_hours: int = 24
    linkedin_rate_limit_delay_seconds: int = 15
    
    indeed_scraping_enabled: bool = False
    indeed_legal_approved: bool = False
    indeed_poll_hours: int = 24
    
    glassdoor_scraping_enabled: bool = False
    glassdoor_legal_approved: bool = False
    glassdoor_poll_hours: int = 24
    
    # Mass upload
    mass_upload_max_file_size_mb: int = 50
    mass_upload_max_batch_size: int = 10000
    mass_upload_allowed_formats: list = ["csv", "json"]
```

---

## Admin Dashboard Requirements

```
Job Scraping Management Dashboard
├─ Scraper Configuration
│  ├─ Enable/disable per source
│  ├─ Set API keys
│  ├─ Configure poll intervals
│  └─ ⚠️ Legal approval checkbox for direct scrapers
│
├─ Scraping Runs
│  ├─ View all scraping jobs (history)
│  ├─ Current run status
│  ├─ Jobs found vs. processed
│  └─ Error logs
│
├─ Mass Uploads
│  ├─ View upload batches
│  ├─ Track processing status
│  ├─ Download error reports
│  └─ Field mapping templates (CSV)
│
└─ Deduplication & Quality
   ├─ View duplicate detection stats
   ├─ Manual duplicate resolution
   └─ Job quality metrics
```

---

## Testing Strategy

### Unit Tests
- Scraper classes (mocked API responses)
- CSV/JSON parsing
- Deduplication logic
- Field mapping

### Integration Tests
- Full pipeline: scrape → process → ingest
- Mass upload: CSV → processing → DB
- Candidate matching with scraped jobs

### Load Tests
- Bulk import 10K+ jobs
- Parallel scraping from multiple sources
- Rate limiting under load

---

## Deployment Checklist

### Before Going Live
- [ ] Legal team review & approval
- [ ] Comprehensive legal disclaimers in UI
- [ ] Admin must explicitly approve direct scrapers
- [ ] Rate limiting configured
- [ ] Monitoring & alerting set up
- [ ] Backup and recovery procedures
- [ ] Terms of Service updated

### Production Safeguards
- [ ] Log all scraping activity
- [ ] Alert on 429 (rate limit) responses
- [ ] Auto-disable scraper on 403 (forbidden)
- [ ] Track data destruction for legal holds
- [ ] Monitor for cease-and-desist notices

---

## Cost Estimate

| Component | Time | Risk |
|-----------|------|------|
| Phase 1 (Foundation) | 24-32 hrs | Low |
| Phase 2 (Safe APIs) | 14-20 hrs | Zero |
| Phase 3 (Direct Scraping) | 16-20 hrs | HIGH |
| Phase 4 (Integration) | 8-10 hrs | Low |
| **TOTAL** | **62-82 hrs** | **Medium** |

---

## Recommendations

1. **Start with Phase 1 + Phase 2** (Safe Foundation)
   - 38-52 hours
   - Zero legal risk
   - Get 50K+ jobs in system
   - Prove concept

2. **Phase 3 Optional** (Direct Scraping)
   - Only after legal approval
   - Keep disabled by default
   - Requires admin to explicitly enable
   - Add legal disclaimers everywhere

3. **Phase 4** (Full Integration)
   - After validating Phases 1-2
   - Complete unified platform

---

**Next Steps:**
1. Confirm Phase 1-2 timeline
2. Get legal review (especially for Phase 3)
3. Set up development environment
4. Begin implementation

