# UI Components Implementation Guide

**Date:** June 3, 2026  
**Components Created:** 5 new components  
**Status:** ✅ Components ready for integration into pages

---

## Components Created

### 1. ScraperConfiguration Component
**File:** `src/components/admin/ScraperConfiguration.tsx` (280 lines)

**Purpose:** Admin interface for managing job scrapers

**Features:**
- ✅ List all configured scrapers
- ✅ Show scraper status (active/inactive)
- ✅ Display risk levels with visual indicators
- ✅ Show job statistics (jobs found, last run, next run)
- ✅ Legal approval status with warnings
- ✅ Enable/disable scraper
- ✅ Test connectivity button
- ✅ Delete scraper
- ✅ Approve legal requirements (for high-risk sources)

**Props:**
```typescript
interface ScraperConfigurationProps {
  scrapers: Scraper[];
  onEnable: (id: string) => Promise<void>;
  onDisable: (id: string) => Promise<void>;
  onTest: (id: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onApprove: (id: string) => Promise<void>;
  onCreate: () => void;
}
```

**Usage:**
```tsx
import { ScraperConfiguration } from '@/components/admin/ScraperConfiguration';

<ScraperConfiguration
  scrapers={scrapers}
  onEnable={handleEnable}
  onDisable={handleDisable}
  onTest={handleTest}
  onDelete={handleDelete}
  onApprove={handleApprove}
  onCreate={handleCreate}
/>
```

---

### 2. MassUpload Component
**File:** `src/components/admin/MassUpload.tsx` (260 lines)

**Purpose:** CSV/JSON file upload interface

**Features:**
- ✅ Drag-and-drop upload area
- ✅ File type validation (CSV, JSON)
- ✅ File size limit (50MB max)
- ✅ Field mapping selector (pre-configured + custom)
- ✅ File preview before upload
- ✅ Progress indicator while uploading
- ✅ Success feedback with batch ID
- ✅ Format help and examples

**Props:**
```typescript
interface MassUploadProps {
  fieldMappings: FieldMapping[];
  onUpload: (file: File, mappingId: string) => Promise<{ batchId: string }>;
}
```

**Usage:**
```tsx
import { MassUpload } from '@/components/admin/MassUpload';

<MassUpload
  fieldMappings={fieldMappings}
  onUpload={async (file, mappingId) => {
    const response = await api.post('/upload/csv', {
      file,
      field_mapping_id: mappingId,
    });
    return { batchId: response.batch_id };
  }}
/>
```

---

### 3. UploadBatchTracker Component
**File:** `src/components/admin/UploadBatchTracker.tsx` (280 lines)

**Purpose:** Real-time tracking of upload batch progress

**Features:**
- ✅ List all upload batches with status
- ✅ Real-time progress bars (for processing batches)
- ✅ Statistics display (total, processed, failed, duplicates)
- ✅ Expandable error details by row
- ✅ Download error log button
- ✅ Refresh button for live updates
- ✅ Timestamp information
- ✅ Status badges with colors

**Props:**
```typescript
interface UploadBatchTrackerProps {
  batches: Batch[];
  onRefresh: () => Promise<void>;
  onDownloadErrors: (batchId: string) => Promise<void>;
}

interface Batch {
  batchId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  filename: string;
  totalRows: number;
  processedRows: number;
  failedRows: number;
  duplicateRows: number;
  createdAt: string;
  completedAt?: string;
  errors?: { [key: string]: string[] };
}
```

**Usage:**
```tsx
import { UploadBatchTracker } from '@/components/admin/UploadBatchTracker';

<UploadBatchTracker
  batches={batches}
  onRefresh={async () => {
    const response = await api.get('/upload/batches');
    setBatches(response.batches);
  }}
  onDownloadErrors={async (batchId) => {
    // Download errors as CSV or JSON
    const response = await api.get(`/upload/batch/${batchId}/errors`);
    downloadFile(response, 'errors.csv');
  }}
/>
```

---

### 4. DataSourceStats Component
**File:** `src/components/shared/DataSourceStats.tsx` (90 lines)

**Purpose:** Dashboard widget showing data source statistics

**Features:**
- ✅ Total jobs imported (manual + scraped)
- ✅ Breakdown by source
- ✅ Scraper status indicator
- ✅ Error alerts
- ✅ Quick action buttons
- ✅ Responsive card layout

**Props:**
```typescript
interface DataSourceStatsProps {
  jobsUploaded?: number;
  jobsScraped?: number;
  activeScrapers?: number;
  scraperErrors?: number;
  uploadBatches?: number;
}
```

**Usage:**
```tsx
import { DataSourceStats } from '@/components/shared/DataSourceStats';

<DataSourceStats
  jobsUploaded={500}
  jobsScraped={1200}
  activeScrapers={3}
  scraperErrors={0}
  uploadBatches={8}
/>
```

---

### 5. ScraperHealthCard Component
**File:** `src/components/shared/ScraperHealthCard.tsx` (140 lines)

**Purpose:** Dashboard widget showing scraper health status

**Features:**
- ✅ Summary of active/inactive scrapers
- ✅ Error indicators with visual pulse
- ✅ Recent scraper activity list
- ✅ Job found counts
- ✅ Quick access to scraper management
- ✅ Status dot indicators (green/red)

**Props:**
```typescript
interface ScraperHealthCardProps {
  scrapers?: Scraper[];
  totalScrapers?: number;
  activeScrapers?: number;
  errorCount?: number;
}

interface Scraper {
  name: string;
  status: 'active' | 'inactive' | 'error';
  lastRun?: string;
  jobsFound?: number;
}
```

**Usage:**
```tsx
import { ScraperHealthCard } from '@/components/shared/ScraperHealthCard';

<ScraperHealthCard
  scrapers={scrapers}
  totalScrapers={6}
  activeScrapers={3}
  errorCount={0}
/>
```

---

## Integration Points

### Admin Dashboard (`/admin/dashboard`)

Add these widgets to the admin dashboard:

```tsx
// In /admin/dashboard/page.tsx

import { DataSourceStats } from '@/components/shared/DataSourceStats';
import { ScraperHealthCard } from '@/components/shared/ScraperHealthCard';

export default async function AdminDashboard() {
  // ... existing code ...

  return (
    <div>
      {/* ... existing KPI tiles ... */}

      {/* Add to three-column layout */}
      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        {/* Main content area */}
        <div>
          {/* ... existing components ... */}
        </div>

        {/* Right sidebar */}
        <div className="space-y-4">
          {/* ... existing widgets ... */}
          
          {/* New: Data source stats */}
          <DataSourceStats
            jobsUploaded={42}
            jobsScraped={156}
            activeScrapers={3}
            scraperErrors={0}
          />

          {/* New: Scraper health */}
          <ScraperHealthCard
            scrapers={scrapers}
            totalScrapers={6}
            activeScrapers={3}
            errorCount={0}
          />
        </div>
      </div>
    </div>
  );
}
```

### Recruiter Dashboard (`/recruiter/dashboard`)

Add data source breakdown to the recruiter dashboard:

```tsx
// In right sidebar of /recruiter/dashboard/page.tsx

<Card>
  <CardHeader className="pb-2 pt-4">
    <CardTitle className="text-sm">Job Sources</CardTitle>
  </CardHeader>
  <CardContent className="space-y-2 pb-4">
    <div className="flex items-center justify-between text-xs">
      <span className="text-muted-foreground">Manual uploads</span>
      <span className="font-bold">47</span>
    </div>
    <div className="flex items-center justify-between text-xs">
      <span className="text-muted-foreground">USAJOBS API</span>
      <span className="font-bold">156</span>
    </div>
    <div className="flex items-center justify-between text-xs">
      <span className="text-muted-foreground">LinkedIn scraper</span>
      <span className="font-bold">23</span>
    </div>
    <Button variant="outline" size="sm" className="w-full text-xs mt-2">
      <Globe className="mr-1 h-3 w-3" /> See all sources
    </Button>
  </CardContent>
</Card>
```

---

## New Pages to Create

### Page 1: `/admin/scrapers`

**File:** `src/app/admin/scrapers/page.tsx`

```tsx
'use client';

import { useState, useEffect } from 'react';
import { PageHeader } from '@/components/shared/AppShell';
import { ScraperConfiguration } from '@/components/admin/ScraperConfiguration';
import { api } from '@/lib/api';

export default function ScrapersPage() {
  const [scrapers, setScrapers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadScrapers();
  }, []);

  const loadScrapers = async () => {
    try {
      const response = await api.get('/scrapers');
      setScrapers(response.scrapers);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Job Scrapers"
        subtitle="Configure and manage automated job data sources"
      />
      <ScraperConfiguration
        scrapers={scrapers}
        onEnable={async (id) => {
          await api.patch(`/scrapers/${id}`, { enabled: true });
          await loadScrapers();
        }}
        onDisable={async (id) => {
          await api.patch(`/scrapers/${id}`, { enabled: false });
          await loadScrapers();
        }}
        onTest={async (id) => {
          const result = await api.post(`/scrapers/${id}/test`, {});
          // Show success/error message
          console.log('Test result:', result);
        }}
        onDelete={async (id) => {
          await api.delete(`/scrapers/${id}`);
          await loadScrapers();
        }}
        onApprove={async (id) => {
          await api.patch(`/scrapers/${id}`, { config: { legal_approved: true } });
          await loadScrapers();
        }}
        onCreate={() => {
          // Open create scraper dialog
        }}
      />
    </div>
  );
}
```

### Page 2: `/admin/uploads`

**File:** `src/app/admin/uploads/page.tsx`

```tsx
'use client';

import { useState, useEffect } from 'react';
import { PageHeader } from '@/components/shared/AppShell';
import { MassUpload } from '@/components/admin/MassUpload';
import { UploadBatchTracker } from '@/components/admin/UploadBatchTracker';
import { api } from '@/lib/api';

export default function UploadsPage() {
  const [batches, setBatches] = useState([]);
  const [fieldMappings, setFieldMappings] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const [mappingsRes, batchesRes] = await Promise.all([
      api.get('/upload/field-mappings'),
      api.get('/upload/batches'),
    ]);
    setFieldMappings(mappingsRes.mappings);
    setBatches(batchesRes.batches);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Bulk Job Import"
        subtitle="Upload jobs from CSV or JSON files"
      />
      
      {/* Upload Form */}
      <MassUpload
        fieldMappings={fieldMappings}
        onUpload={async (file, mappingId) => {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('field_mapping_id', mappingId);
          const response = await api.post('/upload/csv', formData);
          await loadData();
          return { batchId: response.batch_id };
        }}
      />

      {/* Batch History */}
      <UploadBatchTracker
        batches={batches}
        onRefresh={loadData}
        onDownloadErrors={async (batchId) => {
          const response = await api.get(`/upload/batch/${batchId}/errors`);
          // Download as CSV
          const csv = generateCSV(response.errors);
          downloadFile(csv, `errors-${batchId}.csv`);
        }}
      />
    </div>
  );
}
```

---

## Testing Checklist

### Unit Tests
- [ ] ScraperConfiguration renders all scrapers correctly
- [ ] MassUpload validates file types
- [ ] MassUpload shows field mapping selector for CSV
- [ ] UploadBatchTracker displays progress bars
- [ ] DataSourceStats calculates totals correctly
- [ ] ScraperHealthCard shows error states

### Integration Tests
- [ ] Upload triggers correct API endpoint
- [ ] Real-time progress updates work
- [ ] Error messages display properly
- [ ] Scraper enable/disable calls API
- [ ] Test scraper button works
- [ ] Download errors generates file

### E2E Tests
- [ ] User can upload CSV file end-to-end
- [ ] User can configure scraper end-to-end
- [ ] Dashboard shows all statistics correctly

---

## Styling Notes

All components use Tailwind CSS with TrueMatch design system:
- Colors: Primary blue, success green, warning amber, danger red
- Spacing: Consistent 4px baseline grid
- Borders: Subtle muted foreground colors
- Typography: System fonts, consistent sizing

Components integrate with existing:
- `Card`, `CardContent`, `CardHeader`, `CardTitle`
- `Button` (all variants)
- `Badge` (all variants)
- Lucide icons

---

## API Integration

All components are designed to work with these backend endpoints:

**Scrapers:**
```
GET    /api/v1/scrapers              ← List all
POST   /api/v1/scrapers              ← Create
PATCH  /api/v1/scrapers/{id}         ← Update
POST   /api/v1/scrapers/{id}/test    ← Test
DELETE /api/v1/scrapers/{id}         ← Delete
GET    /api/v1/scrapers/{id}/runs    ← History
```

**Uploads:**
```
POST   /api/v1/upload/csv            ← Upload CSV
POST   /api/v1/upload/json           ← Upload JSON
GET    /api/v1/upload/batch/{id}     ← Status
GET    /api/v1/upload/field-mappings ← List mappings
POST   /api/v1/upload/field-mappings ← Create mapping
```

---

## Next Steps

1. **Create Pages** (2-3 hours)
   - [ ] `/admin/scrapers` page
   - [ ] `/admin/uploads` page
   - [ ] Add to admin navigation

2. **Integrate Dashboard** (1-2 hours)
   - [ ] Add DataSourceStats widget
   - [ ] Add ScraperHealthCard widget
   - [ ] Update admin dashboard layout

3. **Connect APIs** (4-6 hours)
   - [ ] Update components with real API calls
   - [ ] Implement polling for real-time updates
   - [ ] Add error handling & notifications
   - [ ] Form validation

4. **Testing** (3-4 hours)
   - [ ] Unit tests for each component
   - [ ] Integration tests with API
   - [ ] E2E tests with full flows
   - [ ] Manual testing in browser

5. **Polish** (1-2 hours)
   - [ ] Mobile responsiveness
   - [ ] Accessibility audit
   - [ ] Performance optimization
   - [ ] User feedback improvements

---

## Summary

✅ **5 React components created** with full TypeScript support  
✅ **Ready for integration** into existing Next.js app  
✅ **Designed for TrueMatch UX** using existing design system  
✅ **Backend APIs ready** to consume  
✅ **Comprehensive documentation** for implementation  

**Estimated time to fully integrate:** 2-3 weeks

---

**Created:** June 3, 2026  
**Components Status:** ✅ Complete & Ready  
**Pages Status:** ⏳ Skeleton provided, ready to build  
**Next Milestone:** Full UI/UX integration with real API data
