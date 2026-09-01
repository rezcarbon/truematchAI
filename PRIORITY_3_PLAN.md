# Priority 3 Implementation Plan - Advanced Features

**Status:** PLANNING PHASE  
**Start Date:** June 5, 2026  
**Estimated Duration:** 3-4 weeks  
**Complexity:** High

---

## 📋 Overview

Priority 3 extends TrueMatch ATS with advanced recruiter capabilities, real-time features, and deeper analytics. These features increase recruiter efficiency and provide data-driven insights.

### Success Criteria
- ✅ Advanced filtering working on pipeline
- ✅ Bulk actions operational
- ✅ Recruiter performance metrics visible
- ✅ DEI analytics dashboard functional
- ✅ Real-time updates via WebSocket
- ✅ Notification system working
- ✅ All features tested and documented

---

## 🎯 Priority 3 Features (Phased Approach)

### Phase 3A: Advanced Filtering & Search (Week 1)
**Impact:** HIGH  
**Effort:** MEDIUM  
**Users:** Recruiters

#### Features
1. **Score Range Filter**
   - Filter by keyword score (min/max)
   - Filter by semantic score (min/max)
   - Filter by capability score (min/max)
   - Filter by overall fit score

2. **Multi-Stage Filter**
   - Select multiple stages to display
   - Show only specific pipeline sections
   - Hide rejected candidates option

3. **Source Filter**
   - Filter by single or multiple sources
   - LinkedIn, Referral, Indeed, etc.
   - Custom source tags

4. **Date Range Filter**
   - Filter by application date
   - Filter by stage entry date
   - Last 7 days, 30 days, custom range

5. **Search Functionality**
   - Search by candidate name
   - Search by email
   - Full-text resume search (if enabled)

6. **Saved Filters**
   - Save current filter configuration
   - Named filter presets (e.g., "Top Candidates", "Phone Screen Ready")
   - Load/delete saved filters
   - Share filters with team

#### Implementation
```typescript
// Filter Interface
interface PipelineFilters {
  scoreRange?: {
    keyword?: { min: number; max: number };
    semantic?: { min: number; max: number };
    capability?: { min: number; max: number };
  };
  stages?: string[];
  sources?: string[];
  dateRange?: { start: Date; end: Date };
  searchText?: string;
}

// Hook
const useFilteredPipeline = (positionId, filters) => {
  // Returns filtered candidates
};

// Component
<FilterPanel 
  onFiltersChange={(newFilters) => setFilters(newFilters)}
  savedFilters={savedFilters}
/>
```

#### Files to Create
```
web/src/hooks/useFilteredPipeline.ts
web/src/hooks/useSavedFilters.ts
web/src/components/ats/FilterPanel.tsx
web/src/components/ats/SavedFiltersMenu.tsx
```

---

### Phase 3B: Bulk Actions (Week 1-2)
**Impact:** HIGH  
**Effort:** MEDIUM  
**Users:** Recruiters

#### Features
1. **Multi-Select Mode**
   - Checkbox on each candidate card
   - "Select All in Stage" button
   - Bulk action toolbar

2. **Bulk Stage Update**
   - Move selected candidates to new stage
   - Confirmation dialog
   - Undo functionality

3. **Bulk Tag Assignment**
   - Add tags to multiple candidates
   - Remove tags from multiple candidates
   - Preset tag templates

4. **Bulk Interview Scheduling**
   - Schedule interviews for multiple candidates
   - Same time/platform/interviewers
   - Different times/interviewers (advanced)

5. **Bulk Actions Menu**
   - Change stage
   - Add/remove tags
   - Schedule interviews
   - Move to reject
   - Export to CSV

#### Implementation
```typescript
// Bulk Actions Interface
interface BulkAction {
  type: 'stage' | 'tag' | 'interview' | 'reject';
  candidateIds: string[];
  payload: {
    newStage?: string;
    tags?: string[];
    interviewData?: InterviewData;
  };
}

// Hook
const useBulkActions = () => {
  const updateStages = (candidateIds, newStage) => {};
  const addTags = (candidateIds, tags) => {};
  const scheduleInterviews = (candidateIds, data) => {};
};
```

#### Files to Create
```
web/src/hooks/useBulkActions.ts
web/src/components/ats/BulkActionToolbar.tsx
web/src/components/ats/BulkActionDialog.tsx
web/src/components/ats/CandidateCheckbox.tsx
```

---

### Phase 3C: Recruiter Performance Dashboard (Week 2)
**Impact:** MEDIUM  
**Effort:** MEDIUM  
**Users:** Managers, Admins

#### Features
1. **KPI Cards**
   - Candidates reviewed (total)
   - Interviews scheduled
   - Offers made
   - Hire rate
   - Average time to hire

2. **Performance Metrics**
   - Applications per recruiter
   - Conversion rates (applied → interview → offer → hire)
   - Average stage duration
   - Interview-to-offer ratio

3. **Recruiter Comparison**
   - Heatmap: recruiter performance comparison
   - Rankings by metric
   - Peer benchmarking

4. **Performance Trends**
   - Charts showing metrics over time
   - Weekly/monthly performance
   - Trend indicators

5. **Source Quality by Recruiter**
   - Which sources produce best candidates
   - Hire rate by source for this recruiter
   - Time to hire by source

#### Implementation
```typescript
// API Response
interface RecruiterPerformance {
  recruiterId: string;
  recruiterName: string;
  metrics: {
    candidatesReviewed: number;
    interviewsScheduled: number;
    offersMade: number;
    hireRate: number;
    avgTimeToHire: number;
  };
  conversionFunnel: {
    applied: number;
    phoneScreen: number;
    technical: number;
    onsite: number;
    offer: number;
    hired: number;
  };
}
```

#### Files to Create
```
web/src/app/admin/analytics/recruiter-performance/page.tsx
web/src/components/analytics/RecruiterKPIs.tsx
web/src/components/analytics/RecruiterComparison.tsx
web/src/hooks/useRecruiterMetrics.ts
```

---

### Phase 3D: DEI Analytics Dashboard (Week 2-3)
**Impact:** MEDIUM  
**Effort:** MEDIUM  
**Users:** Managers, Admins, Compliance

#### Features
1. **Diversity Metrics**
   - Gender distribution in pipeline
   - Underrepresented groups percentage
   - School/university diversity
   - Geographic diversity

2. **Equity Metrics**
   - Equal opportunity metrics
   - Promotion by demographic
   - Pay equity analysis (if integrated)
   - Bias detection in sourcing

3. **Inclusion Metrics**
   - Retention by demographic
   - Team diversity composition
   - Hiring trend analysis

4. **Compliance Reports**
   - EEOC reporting ready
   - Audit trail of hiring decisions
   - Bias alerts (candidates rejected due to score anomalies)

5. **DEI Goals**
   - Set diversity targets
   - Track progress toward goals
   - Recommendations for improvement

#### Implementation
```typescript
// DEI Metrics
interface DEIMetrics {
  diversity: {
    gender: Record<string, number>;
    ethnicity: Record<string, number>;
    age: Record<string, number>;
    geography: Record<string, number>;
  };
  representationByStage: {
    [stage: string]: Record<string, number>;
  };
  hirePipelineEquity: {
    [demographic: string]: number; // percentage
  };
}
```

#### Files to Create
```
web/src/app/admin/analytics/dei/page.tsx
web/src/components/analytics/DiversityMetrics.tsx
web/src/components/analytics/EquityMetrics.tsx
web/src/hooks/useDEIMetrics.ts
```

---

### Phase 3E: Real-Time Updates (WebSocket) (Week 3-4)
**Impact:** MEDIUM  
**Effort:** HIGH  
**Users:** All (recruiters, admins)

#### Features
1. **Live Pipeline Updates**
   - Candidate moves instantly across team
   - New applications appear in real-time
   - Stage changes visible to all users

2. **Interview Notifications**
   - Interview scheduled notification
   - Interview reminder (15 min before)
   - Scorecard submitted notification

3. **Presence Indicators**
   - Show who's viewing pipeline
   - Show who's editing (lock mechanism)

4. **Live Analytics Updates**
   - Dashboard metrics update in real-time
   - Conversion funnel updates live
   - Performance metrics live

#### Implementation
```typescript
// WebSocket Connection
interface WebSocketMessage {
  type: 'pipeline:updated' | 'interview:scheduled' | 'scorecard:submitted';
  payload: any;
  userId: string;
  timestamp: string;
}

// Hook
const useRealtimeUpdates = (positionId) => {
  // Subscribes to WebSocket
  // Updates local state when messages arrive
  // Handles reconnection
};
```

#### Files to Create
```
web/src/hooks/useWebSocket.ts
web/src/hooks/useRealtimeUpdates.ts
web/src/lib/websocket-client.ts
backend/app/websocket/manager.py
```

---

### Phase 3F: Notification System (Week 3-4)
**Impact:** MEDIUM  
**Effort:** MEDIUM  
**Users:** Recruiters, Interviewers

#### Features
1. **In-App Notifications**
   - Interview scheduled
   - Scorecard submitted
   - New application
   - Pipeline updates

2. **Email Notifications**
   - Interview confirmation to candidate
   - Scorecard reminder to interviewer
   - Weekly summary to recruiter

3. **Notification Preferences**
   - Choose notification types
   - Choose channels (email, in-app)
   - Quiet hours (don't notify)

4. **Notification History**
   - View past notifications
   - Mark as read/unread
   - Archive old notifications

#### Implementation
```typescript
// Notification Service
interface Notification {
  id: string;
  userId: string;
  type: 'interview' | 'scorecard' | 'application' | 'pipeline';
  title: string;
  message: string;
  actionUrl?: string;
  channels: ('email' | 'inapp')[];
  read: boolean;
  createdAt: string;
}
```

#### Files to Create
```
web/src/hooks/useNotifications.ts
web/src/components/NotificationCenter.tsx
web/src/components/NotificationBell.tsx
backend/app/services/notification_service.py
```

---

## 📊 Implementation Roadmap

### Week 1
```
Mon-Tue: Advanced Filtering UI & API integration
Wed-Thu: Bulk Actions UI & API integration
Fri:     Testing & bug fixes
```

### Week 2
```
Mon-Tue: Recruiter Performance Dashboard
Wed-Thu: DEI Analytics Dashboard
Fri:     Testing & refinement
```

### Week 3-4
```
Mon-Tue: WebSocket infrastructure & implementation
Wed-Thu: Notification system & email integration
Fri:     Full system testing, documentation
```

---

## 🛠️ Technical Architecture

### Advanced Filtering
```
Frontend Component (FilterPanel)
  ↓
useFilteredPipeline Hook
  ↓
API: GET /api/proxy/ats/positions/{id}/pipeline?filters=...
  ↓
Backend: Filter logic in SQLAlchemy
  ↓
Return filtered candidates
```

### Bulk Actions
```
Frontend Component (BulkActionToolbar)
  ↓
useBulkActions Hook
  ↓
API: POST /api/proxy/ats/bulk-actions
  ↓
Backend: Process bulk operation
  ↓
Emit WebSocket updates
```

### Real-Time Updates
```
Frontend: useRealtimeUpdates Hook
  ↓
WebSocket Connection
  ↓
Backend: WebSocket Manager
  ↓
Emit events on data changes
  ↓
Frontend: Update local state
```

---

## 📋 Database Changes Needed

### New Tables
```sql
-- Saved filters
CREATE TABLE saved_filters (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  position_id UUID,
  name VARCHAR(255),
  filters JSONB,
  created_at TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Notifications
CREATE TABLE notifications (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  type VARCHAR(50),
  title VARCHAR(255),
  message TEXT,
  action_url VARCHAR(255),
  channels VARCHAR(50)[], -- ['email', 'inapp']
  read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Recruiter metrics (cached)
CREATE TABLE recruiter_metrics (
  id UUID PRIMARY KEY,
  recruiter_id UUID NOT NULL,
  position_id UUID,
  metrics JSONB, -- KPIs as JSON
  calculated_at TIMESTAMP,
  FOREIGN KEY (recruiter_id) REFERENCES users(id)
);
```

### New Indexes
```sql
CREATE INDEX idx_saved_filters_user_id ON saved_filters(user_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_read ON notifications(user_id, read);
CREATE INDEX idx_recruiter_metrics_recruiter_id ON recruiter_metrics(recruiter_id);
```

---

## 🔌 New API Endpoints

### Filtering
```
GET  /api/proxy/ats/positions/{id}/pipeline?filters=JSON
POST /api/proxy/ats/saved-filters
GET  /api/proxy/ats/saved-filters
DELETE /api/proxy/ats/saved-filters/{id}
```

### Bulk Actions
```
POST /api/proxy/ats/bulk-actions/stage
POST /api/proxy/ats/bulk-actions/tags
POST /api/proxy/ats/bulk-actions/interviews
```

### Analytics
```
GET /api/proxy/ats/recruiter-metrics/{recruiterId}
GET /api/proxy/ats/recruiter-comparison
GET /api/proxy/ats/dei-metrics
```

### WebSocket
```
ws://localhost:8000/ws/pipeline/{positionId}
ws://localhost:8000/ws/notifications
```

### Notifications
```
GET  /api/proxy/ats/notifications
PATCH /api/proxy/ats/notifications/{id}
DELETE /api/proxy/ats/notifications/{id}
```

---

## 📦 Component Hierarchy

### Phase 3A: Filtering
```
PipelineBoard (updated)
├── FilterPanel (new)
│   ├── ScoreRangeFilter
│   ├── StageFilter
│   ├── SourceFilter
│   ├── DateRangeFilter
│   └── SearchBox
└── SavedFiltersMenu (new)
```

### Phase 3B: Bulk Actions
```
PipelineBoard (updated)
├── BulkActionToolbar (new)
│   ├── SelectAllButton
│   ├── DeselectAllButton
│   └── BulkActionMenu
├── CandidateCard (updated)
│   └── Checkbox (new)
└── BulkActionDialog (new)
```

### Phase 3C: Recruiter Performance
```
/admin/analytics/recruiter-performance/
├── RecruiterKPIs (new)
├── RecruiterComparison (new)
├── PerformanceTrends (new)
└── SourceQualityByRecruiter (new)
```

### Phase 3D: DEI Analytics
```
/admin/analytics/dei/
├── DiversityMetrics (new)
├── EquityMetrics (new)
├── InclusionMetrics (new)
└── ComplianceReports (new)
```

### Phase 3E/F: Real-Time & Notifications
```
NotificationCenter (new)
├── NotificationBell (new)
├── NotificationPanel (new)
└── NotificationItem (new)
```

---

## 🧪 Testing Strategy

### Unit Tests
- Filter logic
- Bulk action validation
- Metrics calculation
- Notification generation

### Integration Tests
- API endpoint testing
- WebSocket connection
- Real-time updates
- Email sending

### E2E Tests
- Filter → view results
- Bulk select → execute action → verify
- Real-time update visible across users
- Notification received and displayed

### Performance Tests
- Filter 1000+ candidates
- Bulk update 100 candidates
- 50 concurrent WebSocket connections
- Notification delivery under load

---

## 📚 Documentation Plan

### User Documentation
- Filtering user guide
- Bulk actions tutorial
- Dashboard explanations
- Notification preferences

### Technical Documentation
- API endpoint docs
- WebSocket protocol
- Database schema
- Architecture diagrams

### Deployment Documentation
- Database migration steps
- Environment variables
- Service configuration
- Rollback procedures

---

## ⏱️ Effort Estimation

| Feature | Effort | Priority |
|---------|--------|----------|
| Advanced Filtering | 12 hours | 🔴 HIGH |
| Bulk Actions | 10 hours | 🔴 HIGH |
| Recruiter Dashboard | 10 hours | 🟡 MEDIUM |
| DEI Analytics | 10 hours | 🟡 MEDIUM |
| WebSocket/Real-Time | 16 hours | 🟡 MEDIUM |
| Notifications | 10 hours | 🟡 MEDIUM |
| Testing | 12 hours | 🔴 HIGH |
| Documentation | 6 hours | 🟢 LOW |

**Total Estimated Effort:** 86 hours ≈ 2.5-3 weeks (1 senior engineer)

---

## 🎯 Success Metrics

### Adoption
- % of recruiters using filters
- Avg bulk actions per day
- Dashboard view frequency

### Performance
- Filter response time < 200ms
- Bulk action completion < 5 seconds
- WebSocket latency < 100ms

### Quality
- Error rate < 0.1%
- Test coverage > 85%
- Notification delivery rate > 99%

---

## 🚀 Deployment Strategy

### Phase 3A-3B (Week 1-2)
1. Deploy filtering & bulk actions
2. A/B test with subset of users
3. Monitor performance
4. Full rollout

### Phase 3C-3D (Week 2-3)
1. Deploy recruiter & DEI dashboards
2. Internal testing
3. Gradual rollout

### Phase 3E-3F (Week 3-4)
1. WebSocket staging deployment
2. Notification system testing
3. Full production rollout
4. Monitor real-time updates

---

## 🔄 Rollback Plan

### If filtering breaks:
- Disable filter UI
- Return to full pipeline view
- Revert API changes

### If bulk actions fail:
- Stop accepting bulk requests
- Show error to users
- Revert partial updates

### If WebSocket crashes:
- Fall back to polling
- Show warning to users
- Restart service

---

## 📖 Next Steps

1. ✅ Approve Priority 3 plan
2. 🔄 Implement Phase 3A (Filtering) - 12 hours
3. 🔄 Implement Phase 3B (Bulk Actions) - 10 hours
4. 🔄 Implement Phase 3C (Recruiter Dashboard) - 10 hours
5. 🔄 Implement Phase 3D (DEI Analytics) - 10 hours
6. 🔄 Implement Phase 3E-F (Real-Time & Notifications) - 26 hours
7. ✅ Testing & Documentation - 18 hours

---

**Status:** Ready to implement  
**Estimated Start:** Immediately  
**Estimated Completion:** 2.5-3 weeks  
**Total Lines of Code:** 3,000-4,000  
**Success Criteria:** All features functional and tested
