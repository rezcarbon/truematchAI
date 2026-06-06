# Agent Operator Dashboard - Implementation Checklist

## ✅ Already Built (Ready to Use)

### Autonomous Agents
- ✅ **CV Ingestion Agent** (`backend/app/workers/agents/ingest_cv.py`)
  - Monitors `/inbox/cv/` folder
  - Extracts CV text (PDF, DOCX, TXT, EML)
  - Auto-matches to best JD using TF-IDF similarity
  - Creates assessment job automatically
  - Logs all actions in `ingest_queue` table

- ✅ **JD Analysis Agent** (`backend/app/workers/agents/ingest_jd.py`)
  - Monitors `/inbox/jd/` folder  
  - Analyzes JD quality
  - Generates AI-improved drafts
  - Requires recruiter approval before finalizing

- ✅ **Email Polling Agent** (in CV ingestion)
  - IMAP email monitoring
  - Attachment extraction
  - Same flow as folder monitoring

### Agent Control APIs
- ✅ `GET /agents/queue` - List all ingest items
- ✅ `POST /agents/queue/{id}/approve` - Approve awaiting_review items
- ✅ `POST /agents/queue/{id}/reject` - Reject items
- ✅ `POST /agents/queue/{id}/reassign` - Reassign to different JD
- ✅ `POST /agents/jd/draft` - Submit JD for analysis

### Real-Time Monitoring
- ✅ `WS /agents/ws` - Agent event feed (broadcasted, approval/rejection events)
- ✅ `WS /ws/pipeline/{position_id}` - Candidate pipeline updates
- ✅ `WS /api/v1/realtime/ws/assessment/{id}` - Assessment progress (18 event types)

### Data Models
- ✅ `IngestQueueItem` model - Complete audit trail
  - Fields: item_id, type, source, content_hash, status, auto_match, human_decision, notes
  - Status states: pending → extracting → matching → processing → completed/failed/rejected/awaiting_review
  - Perfect for queue management UI

### Admin Dashboard Foundation
- ✅ `/admin/dashboard` - Basic system metrics
- ✅ `/admin` - Compliance, analytics, audit trail views
- ✅ `/recruiter/agents` - Agent command center (partial)

---

## ❌ Missing & Needs to Be Built

### Phase 1: Agent Command Panel (2-3 days)

**Needed:**
- [ ] Dedicated agent control page (`/admin/agents/operator`)
- [ ] Real-time agent status display
  - [ ] Running/Paused status
  - [ ] Queue sizes per agent
  - [ ] Processed count (24h)
  - [ ] Error rates
  - [ ] Uptime tracking

**Backend APIs Required:**
```
GET /agents/status
  → Returns: {cv: {...}, jd: {...}, email: {...}, assessment: {...}}

GET /agents/{agent_type}/config
  → Returns: polling_interval, batch_size, auto_approve_enabled, etc.

POST /agents/{agent_type}/pause
  → Pause agent polling

POST /agents/{agent_type}/resume
  → Resume agent polling

POST /agents/{agent_type}/config
  {
    "polling_interval_seconds": 60,
    "batch_size": 10,
    "auto_approve_confidence": 0.85
  }
```

**Frontend Components:**
```
AgentCommandPanel.tsx
├── AgentStatusCard (for each agent)
│   ├── Status indicator (🟢/🔴)
│   ├── Queue size badge
│   ├── Throughput metric
│   ├── Error rate
│   ├── [Pause/Resume] button
│   └── [Config] modal
├── Overall metrics row
└── [Emergency Stop All] button
```

---

### Phase 2: Queue Management UI (2-3 days)

**Needed:**
- [ ] "Awaiting Review" queue display
- [ ] Show auto-match confidence
- [ ] Display top 3 alternative positions
- [ ] Decision action buttons (Approve, Reject, Reassign)
- [ ] Notes/feedback input
- [ ] Flag for training

**Frontend Components:**
```
QueueManagement.tsx
├── FilterBar
│   ├─ Type (CV/JD/Email)
│   ├─ Status (awaiting_review, etc)
│   └─ Sort (by confidence, date, etc)
├── QueueItemCard (for each item)
│   ├─ Item info (filename, source)
│   ├─ Auto-match position + confidence
│   ├─ Alternative positions (top 3)
│   ├─ Action buttons
│   │   ├─ [Approve → Position]
│   │   ├─ [Override Match]
│   │   ├─ [Reject]
│   │   └─ [Flag for Training]
│   └─ Notes input
└── Batch actions row
```

**Backend Enhancements:**
```
Extend POST /agents/queue/{id}/approve
  {
    "confidence_override": 0.70,  # Allow lower scores
    "force_position_id": "pos-456",
    "notes": "Good fit despite score"
  }

New: POST /agents/queue/{id}/flag-for-training
  {
    "reason": "Edge case",
    "suggestion": "Improve mapping X",
    "severity": "medium"
  }
```

---

### Phase 3: Metrics Dashboard (2 days)

**Needed:**
- [ ] 24h performance metrics
- [ ] 7d and 30d trends
- [ ] Error rate graphs
- [ ] Cost per operation tracking
- [ ] Match quality metrics
- [ ] Human override rates

**Backend Metrics Collection:**
```
Create: backend/app/workers/agent_metrics_collector.py
├── Collect metrics every minute
├── Track per agent:
│   ├─ Items processed
│   ├─ Errors (count + types)
│   ├─ Average processing time
│   ├─ Auto-match confidence avg
│   └─ Human override rate
└── Store in: agent_metrics table (time-series)

New API:
GET /agents/metrics?period=24h|7d|30d
  Response: {
    cv: {processed: 342, errors: 1, error_rate: 0.3%, ...},
    jd: {...},
    email: {...}
  }

GET /agents/cost-analysis
  Response: {cost_per_cv: 0.008, cost_per_jd: 0.045, ...}
```

**Frontend Components:**
```
AgentMetricsDashboard.tsx
├── MetricsCards (24h overview)
│   ├─ Total processed
│   ├─ Error rate
│   ├─ Avg throughput
│   └─ Cost total
├── Charts
│   ├─ Throughput trend (7d, 30d)
│   ├─ Error rate trend
│   ├─ Processing time trend
│   └─ Cost trend
└── Detailed breakdown by agent
```

---

### Phase 4: WebSocket Real-Time Feed (1-2 days)

**Needed:**
- [ ] New `/ws/agent-operator` endpoint
- [ ] Broadcast agent events to dashboard
- [ ] Real-time queue updates
- [ ] Live error notifications

**Backend:**
```
Create: backend/app/websocket/agent_operator.py
├── ConnectionManager for agent operator
├── Broadcast message types:
│   ├─ agent_status (polling, processing, error)
│   ├─ queue_item (new items in queue)
│   ├─ assessment_complete (assessment finished)
│   ├─ agent_error (error occurred)
│   └─ metrics_update (periodic metrics)
└── Handler logic for subscription

Integration Points:
├─ IngestCV agent → emit "queue_item" on new CV
├─ AssessmentProcessor → emit "assessment_complete"
├─ Error handlers → emit "agent_error"
└─ Metrics collector → emit "metrics_update" every 60s
```

**Frontend Hook:**
```typescript
useAgentOperator.ts
├── Connect to WS endpoint
├── Subscribe to message types
├── Auto-reconnect with backoff
├── Provide hooks for components:
│   ├─ onQueueItemAdded()
│   ├─ onAssessmentComplete()
│   ├─ onAgentError()
│   └─ onMetricsUpdate()
└── Unsubscribe on unmount
```

---

### Phase 5: Training Integration (1-2 days)

**Needed:**
- [ ] Flag edge cases for curriculum improvement
- [ ] Send decision data to training system
- [ ] Track feedback impact on accuracy
- [ ] Display feedback loop metrics

**Backend:**
```
Create: backend/app/workers/agent_feedback_loop.py
├── When item is approved/rejected:
│   ├─ Extract decision rationale
│   ├─ Calculate confidence delta (expected vs actual)
│   ├─ Send to Training System for analysis
│   └─ Flag for curriculum improvement if edge case
│
└── When item is flagged for training:
    ├─ Send full context to training system
    ├─ Suggest capability weight improvement
    └─ Track impact on future assessments

New API:
POST /agents/training/feedback
  {
    "ingest_item_id": "item-789",
    "decision": "approved",
    "human_confidence": 0.95,
    "system_confidence": 0.67,
    "reason": "Manager feedback - actually strong leader",
    "suggested_improvements": ["Improve leadership detection"]
  }

GET /agents/training/impact
  Response: {
    feedback_count: 47,
    avg_accuracy_improvement: 0.031,
    weights_updated: 12,
    next_recalibration: "2026-06-08T00:00:00Z"
  }
```

---

## Implementation Priority

### Must Have (Week 1):
1. Agent Command Panel (pause/resume/config)
2. Queue Management (approve/reject/reassign)
3. WebSocket event feed

### Nice to Have (Week 2):
4. Metrics Dashboard
5. Training Integration

### Future Enhancements:
6. Agent performance tuning UI
7. Cost optimization suggestions
8. Automated workflow templates
9. Custom agent rules engine

---

## File Structure (After Implementation)

```
backend/
  app/
    api/v1/
      agents.py                    [EXTEND with new endpoints]
      agents_extended.py           [NEW - config, pause/resume]
    websocket/
      agent_operator.py            [NEW - operator event broadcaster]
    workers/
      agent_metrics_collector.py   [NEW - metrics collection]
      agent_feedback_loop.py       [NEW - training integration]
    models/
      agent_metrics.py             [NEW - metrics time-series table]

web/
  src/
    app/admin/agents/
      operator/
        page.tsx                   [NEW - Main operator dashboard]
    components/admin/
      AgentCommandPanel.tsx        [NEW - Agent control]
      QueueManagement.tsx          [NEW - Queue UI]
      AgentMetricsDashboard.tsx    [NEW - Metrics visualization]
      DecisionSupport.tsx          [NEW - Confidence-based hints]
      FeedbackTracker.tsx          [NEW - Training integration UI]
    hooks/
      useAgentOperator.ts          [NEW - WebSocket hook]
```

---

## Database Schema Additions

### agent_metrics table (time-series)
```sql
CREATE TABLE agent_metrics (
  id UUID PRIMARY KEY,
  agent_type VARCHAR(50),  -- 'cv', 'jd', 'email', 'assessment'
  period_start TIMESTAMP,
  period_end TIMESTAMP,
  items_processed INT,
  items_failed INT,
  avg_processing_time_ms FLOAT,
  error_rate FLOAT,
  throughput_per_hour FLOAT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agent_metrics_type_period 
  ON agent_metrics(agent_type, period_start DESC);
```

### agent_feedback table
```sql
CREATE TABLE agent_feedback (
  id UUID PRIMARY KEY,
  ingest_item_id UUID REFERENCES ingest_queue(id),
  human_decision VARCHAR(50),  -- approved, rejected
  human_confidence FLOAT,
  system_confidence FLOAT,
  decision_reason TEXT,
  feedback_type VARCHAR(50),  -- curriculum_improvement, edge_case, etc
  flagged_for_training BOOLEAN,
  training_impact FLOAT,  -- Updated post-training
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Rollout Plan

### Phase 1a (3 days): Command Panel
```
Day 1: Backend APIs (pause/resume/config)
Day 2: Frontend dashboard + components
Day 3: QA + deployment
```

### Phase 1b (3 days): Queue Management  
```
Day 1: Backend decision tracking
Day 2: Frontend queue UI
Day 3: QA + deployment
```

### Phase 2 (2 days): WebSocket
```
Day 1: Backend broadcaster
Day 2: Frontend hook + integration
```

### Phase 3 (2 days): Metrics
```
Day 1: Metrics collection + API
Day 2: Frontend visualization
```

### Phase 4 (2 days): Training
```
Day 1: Feedback loop implementation
Day 2: UI + integration
```

**Total: ~12 days to full Agent Operator system**

---

## How This Enables True Autonomy

### Without Agent Operator:
```
Agent runs in background
Recruiter doesn't see what it's doing
Recruiter manually checks queue
Recruiter doesn't know throughput/errors
System improves slowly (no feedback loop)
```

### With Agent Operator:
```
Agent runs in background
Recruiter/Admin watches real-time on dashboard
Auto-decisions shown with confidence
Edge cases flagged for human review
Feedback automatically improves system
Operator can pause/adjust on the fly
Transparency + Control + Learning
```

This is **OpenClaw-style autonomy**: The system operates independently but with complete visibility and human oversight.
