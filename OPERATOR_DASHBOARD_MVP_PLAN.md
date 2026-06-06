# Agent Operator Dashboard - MVP Implementation Plan

**Status:** Ready to Build  
**Effort:** 2-3 Days (Full Team)  
**Value:** Operators can see and approve queue items in real-time

---

## MVP Scope (What We're Building)

### What's Included ✅
- Queue management UI (view awaiting_review items)
- Approve/Reject/Hold actions with notes
- Real-time queue updates via WebSocket
- Agent status visibility (basic)

### What's Excluded ❌ (Phase 2+)
- Agent pause/resume controls (backend endpoints don't exist yet)
- Agent configuration UI (Celery Beat integration needed)
- Metrics dashboard (metrics collection doesn't exist yet)
- Confidence scoring (CV agent doesn't compute match confidence yet)
- Alternative position ranking (match system only finds best)
- Training feedback integration (Phase 4)

---

## MVP Architecture

```
┌────────────────────────────────────────────────────┐
│         OPERATOR DASHBOARD MVP                     │
│      (Simplified, uses existing APIs)              │
└──────────────────┬─────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌──────────────────┐   ┌────────────────┐
│  Queue List      │   │ Real-Time Feed │
│  (React Table)   │   │ (WebSocket)    │
│                  │   │                │
│ ✓ Shows items    │   │ ✓ Live updates │
│ ✓ Filter/Sort    │   │ ✓ Auto-refresh │
│ ✓ Action buttons │   │                │
└────────┬─────────┘   └────────────────┘
         │
         ├─────────────────────┐
         │                     │
         ▼                     ▼
  POST /agents/queue/{id}/approve
  POST /agents/queue/{id}/reject
  POST /agents/queue/{id}/reassign
  
  WS /agents (existing endpoint)
```

---

## Phase 1: Backend - Minimal Changes (2-3 Hours)

### What We're Reusing
- ✅ `/agents/queue` GET endpoint (already exists)
- ✅ `/agents/queue/{id}` GET endpoint (already exists)
- ✅ `/agents/queue/{id}/approve` POST endpoint (already exists)
- ✅ `/agents/queue/{id}/reject` POST endpoint (already exists)
- ✅ `/ws/agents` WebSocket endpoint (already exists)
- ✅ `IngestQueueItem` model (already has all needed fields)

### What We're Adding

**1. Extend Queue Response Model**

```python
# File: backend/app/schemas/ingest_queue.py

class QueueItemDetail(BaseModel):
    """Extended queue item with decision support"""
    id: UUID
    type: IngestItemType  # cv, jd, email
    source: str  # email, folder_drop
    content_hash: str  # SHA256 of content
    status: IngestStatus
    extracted_text: str | None  # First 500 chars for preview
    sender_meta: dict  # {name, email} if email
    auto_match_position_id: UUID | None
    created_at: datetime
    updated_at: datetime
    
    # NEW FIELDS
    awaiting_review: bool  # true if status == awaiting_review
    decision_deadline: datetime | None  # Optional, for SLA
    notes_history: list[str]  # Previous notes
```

**2. Add Backend Event Broadcasting**

```python
# File: backend/app/api/v1/agents.py

# When approving an item, broadcast event
async def approve_item(item_id: UUID, ...):
    item = await queue.approve(item_id, ...)
    
    # Broadcast to all connected operators
    await ws_manager.broadcast({
        "type": "queue_item_action",
        "action": "approved",
        "item_id": item_id,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {"status": "approved"}
```

**3. Add Queue Filtering Endpoint**

```python
# Extend existing GET /agents/queue

GET /agents/queue?status=awaiting_review&sort=created_at&limit=50
Response:
{
  "items": [
    {item_detail},
    ...
  ],
  "total": 3,
  "page": 1
}
```

**Estimated Time:** 2-3 hours
- Response model extension: 30 min
- Event broadcasting: 30 min
- Testing: 1-2 hours

---

## Phase 2: Frontend - Queue Management UI (8-10 Hours)

### New Pages & Components

**Page: `/admin/agents/operator`**

```
Main layout:
├─ Sidebar
│  ├─ Queue (awaiting_review)
│  ├─ Settings
│  └─ Help
├─ Header
│  ├─ Breadcrumb: Admin > Agents > Operator
│  ├─ Live status: "3 items awaiting decision"
│  └─ Refresh button
└─ Content
   ├─ QueueTable
   │  ├─ Columns: Name, Type, Source, Created, Actions
   │  └─ Sorting/Filtering
   ├─ SelectedItemPanel (when row clicked)
   │  ├─ Full item details
   │  ├─ Extracted text preview
   │  ├─ Action buttons
   │  └─ Notes input
   └─ EventFeed (right sidebar)
      ├─ Real-time events
      └─ Auto-scroll to latest
```

### Component Structure

```
AdminOperatorPage.tsx (Main page)
├── useAgentOperator() hook (WebSocket subscription)
├── QueueTable
│   ├── uses TanStack Table (sorting, filtering)
│   ├── Column renderers
│   └── Row selection
├── QueueItemDetail
│   ├── ItemInfo (display)
│   ├── ExtractedTextPreview
│   ├── ActionPanel
│   │   ├── ApproveButton
│   │   ├── RejectButton
│   │   ├── HoldButton
│   │   └── NotesInput
│   └── DecisionHistory
└── LiveEventFeed
    ├── EventCard (per event)
    └── Auto-scroll container
```

### Detailed Components

**QueueTable.tsx**
```typescript
interface Props {
  items: QueueItemDetail[];
  isLoading: boolean;
  onSelectItem: (item: QueueItemDetail) => void;
  onRefresh: () => void;
}

// Columns: name | type | source | created | status badge | actions quick
// Sorting: by created_at (newest first), by type
// Filtering: awaiting_review only (hardcoded for MVP)
// Selection: single click expands detail panel
```

**QueueItemDetail.tsx**
```typescript
interface Props {
  item: QueueItemDetail;
  onApprove: (notes: string) => Promise<void>;
  onReject: (reason: string) => Promise<void>;
  onHold: () => Promise<void>;
}

// Shows:
// - Item type (CV/JD/Email)
// - Source (folder, email, API)
// - Extracted text (first 1000 chars, scrollable)
// - Sender info (if email)
// - Previous notes/decisions (timeline)
// - Action buttons with loading states
```

**ActionPanel.tsx**
```typescript
interface Props {
  item: QueueItemDetail;
  onApprove: (notes: string) => void;
  onReject: (reason: string) => void;
  onHold: () => void;
}

// Three buttons: [Approve] [Hold] [Reject]
// Each has a modal/inline form:
//   Approve: optional notes field
//   Reject: required reason dropdown + notes
//   Hold: modal asking "Until when? What needs review?"
```

**LiveEventFeed.tsx**
```typescript
interface Props {
  events: AgentEvent[];
}

// Shows recent events:
// - 14:32 John Doe approved (by Admin)
// - 14:33 Assessment queued
// - 14:34 Assessment complete (score 0.87)
// - 14:34 Notifications sent
// 
// Auto-scrolls to latest
// Colors: green for approval, blue for process, red for error
```

**useAgentOperator.ts (Hook)**
```typescript
// Manages WebSocket subscription to /ws/agents
// Subscribes on mount, unsubscribes on unmount
// Broadcasts events to subscribers

export function useAgentOperator() {
  const [queueItems, setQueueItems] = useState<QueueItemDetail[]>([]);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  
  // Subscribe to WebSocket
  useEffect(() => {
    const ws = new WebSocket(`ws://.../agents`);
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === 'queue_item_action') {
        // Refresh queue, add to event feed
      }
    };
    return () => ws.close();
  }, []);
  
  // Approve/reject functions
  const approve = async (item_id, notes) => {
    const response = await fetch(`/agents/queue/${item_id}/approve`, {...});
    // Event will come via WebSocket
  };
  
  return { queueItems, events, approve, reject, hold };
}
```

**Estimated Time:** 8-10 hours
- Component structure & layout: 2 hours
- QueueTable with sorting/filtering: 2 hours
- QueueItemDetail panel: 2 hours
- Action buttons & forms: 2 hours
- WebSocket hook: 1-2 hours
- Testing & polish: 2 hours

---

## Phase 3: Basic Agent Status (Optional, adds 2 hours)

### What to Add (if time permits)

**Simple Agent Status Card**
```
CV INGESTION AGENT
Status: 🟢 Running
Queue Size: 12 items
Processed Today: 342
Last Check: 2 min ago
```

**How to Build (2 hours)**
1. Query database: `SELECT COUNT(*) FROM ingest_queue WHERE type='cv' AND status != 'completed'`
2. Query Celery Beat: check if `poll_folder` task is scheduled
3. Aggregate from IngestQueueItem: count processed items today
4. Display on dashboard header or right sidebar

**Backend (30 min):**
```python
GET /agents/status/quick
Response: {
  "cv": {"running": true, "queue": 12, "processed_24h": 342},
  "jd": {"running": true, "queue": 3, "processed_24h": 28},
  ...
}
```

**Frontend (1.5 hours):**
- AgentStatusCard component
- Simple layout in dashboard header
- No charts, no drill-down

---

## Build Sequence (Day-by-Day)

### Day 1: Setup + Backend (3-4 hours)

**Morning (2 hours):**
- [ ] Extend QueueItemDetail schema
- [ ] Add event broadcasting to `/agents/queue/{id}/approve`
- [ ] Test response models

**Afternoon (1-2 hours):**
- [ ] Create `useAgentOperator` hook (TypeScript)
- [ ] Test WebSocket connection
- [ ] Set up component structure

### Day 2: Frontend - Queue UI (6-8 hours)

**Morning (3-4 hours):**
- [ ] Build QueueTable with TanStack Table
- [ ] Implement sorting/filtering
- [ ] Row selection and detail panel expansion

**Afternoon (3-4 hours):**
- [ ] Build QueueItemDetail component
- [ ] Implement action buttons (Approve, Reject, Hold)
- [ ] Add notes input with validation

### Day 3: Polish + WebSocket Integration (2-4 hours)

**Morning (2 hours):**
- [ ] Integrate WebSocket into components
- [ ] Auto-refresh queue on item_action event
- [ ] Add loading states and error handling

**Afternoon (2 hours):**
- [ ] Add LiveEventFeed component
- [ ] Polish styling and animations
- [ ] Test end-to-end: approve item → see event → queue updates

**Optional (if time):**
- [ ] Add agent status cards
- [ ] Basic metrics display

---

## File Structure (After MVP)

```
backend/
  app/
    api/v1/
      agents.py              [MODIFY - add event broadcast]
    schemas/
      ingest_queue.py        [MODIFY - extend response model]

web/
  src/
    app/admin/agents/
      operator/
        page.tsx             [NEW - main page]
    components/admin/
      operators/
        QueueTable.tsx       [NEW]
        QueueItemDetail.tsx  [NEW]
        ActionPanel.tsx      [NEW]
        LiveEventFeed.tsx    [NEW]
        AgentStatusCard.tsx  [NEW - optional]
    hooks/
      useAgentOperator.ts    [NEW]
```

---

## Acceptance Criteria (MVP is Done When)

- ✅ Admin can navigate to `/admin/agents/operator`
- ✅ Page shows list of awaiting_review items from database
- ✅ Admin can click item → see details (extracted text, source, metadata)
- ✅ Admin can approve item → backend approves + enqueues assessment
- ✅ Admin can reject item → backend rejects + logs reason
- ✅ Admin can hold item → marks for later review
- ✅ Notes are stored and shown in history
- ✅ Queue table refreshes on approval/rejection (via WebSocket or polling)
- ✅ Live event feed shows recent actions in real-time
- ✅ Error handling (network error → show toast, retry button)

---

## Phase 2+ Features (Not in MVP)

### Phase 2 (Week 2): Agent Control
- Agent pause/resume buttons
- Polling frequency config UI
- Agent health metrics

### Phase 3 (Week 3): Confidence & Alternatives
- Add confidence score to queue items
- Show alternative positions for uncertain matches
- Reappear/reassign functionality

### Phase 4 (Week 4): Training Integration
- Flag for training button
- Feedback loop metrics
- Impact tracking

### Phase 5+: Advanced
- Metrics dashboard (throughput, error trends)
- Cost analysis
- Performance optimizations

---

## Database Queries Needed (for reference)

```sql
-- Get awaiting_review items
SELECT * FROM ingest_queue 
WHERE status = 'awaiting_review' 
ORDER BY created_at DESC 
LIMIT 50;

-- Get queue size by type
SELECT type, COUNT(*) as count 
FROM ingest_queue 
WHERE status IN ('pending', 'extracting', 'matching', 'processing') 
GROUP BY type;

-- Get processed count for agent (last 24h)
SELECT COUNT(*) FROM ingest_queue 
WHERE type = 'cv' 
AND status IN ('completed', 'failed', 'rejected') 
AND updated_at > NOW() - INTERVAL '24 hours';
```

---

## Risk Assessment

**Low Risk:**
- ✅ Reusing existing endpoints (no new infrastructure)
- ✅ WebSocket already works (just reusing)
- ✅ Frontend is isolated (no complex integrations)

**Medium Risk:**
- ⚠️ Real-time sync: If WebSocket connection drops, queue stales
  - *Mitigation*: Add manual refresh button, show last-update timestamp

**Mitigation Plan:**
- Implement polling fallback (refresh every 30s if WebSocket disconnected)
- Show connection status indicator
- Add error toast for failed actions
- Comprehensive testing before shipping

---

## Success Metrics

**Launch Criteria:**
- ✅ Can approve/reject queue items without manual SQL
- ✅ Real-time updates (within 2 seconds of action)
- ✅ <2 second page load time
- ✅ <1 second approve/reject response time
- ✅ 99% uptime (WebSocket auto-reconnects)

**Business Impact:**
- Operators can make decisions faster
- Candidate response time improves
- System learns from human feedback loop
- Foundation for Phase 2+ features

---

## Team Allocation

**Backend (1 person, Days 1-2):**
- Response model extension
- Event broadcasting
- Quick agent status endpoint (optional)

**Frontend (1-2 people, Days 2-3):**
- Queue table component
- Detail panel component
- Action buttons + forms
- WebSocket hook

**QA/Testing (1 person, Day 3):**
- End-to-end testing
- Load testing (many queue items)
- Edge cases (network disconnection, rapid approvals)

---

## Next Steps

1. ✅ **Review this plan** (estimate effort)
2. 🔄 **Get feedback** from team
3. ✅ **Assign roles** (backend lead, frontend leads)
4. 🚀 **Start Day 1: Backend setup**

Ready to begin? Let's start with the backend changes.
