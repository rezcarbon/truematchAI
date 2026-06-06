# TrueMatch Agent Operator Dashboard Design

**Purpose:** Unified command center for autonomous agents (similar to OpenClaw)  
**Vision:** Operate the entire system as an autonomous agent capable of helping candidates/recruiters 24/7

---

## Architecture: Agent Operator System

```
┌─────────────────────────────────────────────────────────────┐
│          Admin Agent Operator Dashboard                     │
│  (Unified command center for autonomous system operation)   │
└──────────────┬──────────────────────────────────────────────┘
               │
        ┌──────┴──────────────────────────┐
        │                                 │
        ▼                                 ▼
┌─────────────────────┐      ┌──────────────────────┐
│  Agent Control      │      │  Agent Metrics       │
│  & Commands         │      │  & Intelligence      │
│                     │      │                      │
│ ├─ CV Agent         │      │ ├─ Throughput        │
│ ├─ JD Agent         │      │ ├─ Error Rates       │
│ ├─ Email Agent      │      │ ├─ Match Quality     │
│ ├─ Assessment Agent │      │ ├─ Cost Per Item    │
│ └─ Learning Agent   │      │ └─ Agent Health     │
└─────────────────────┘      └──────────────────────┘
        │                            │
        ▼                            ▼
┌─────────────────────┐      ┌──────────────────────┐
│  Queue Management   │      │  Human-in-Loop      │
│  & Decisions        │      │  Support             │
│                     │      │                      │
│ ├─ Awaiting Review  │      │ ├─ Confidence Score │
│ ├─ Approve/Reject   │      │ ├─ Alt Positions    │
│ ├─ Reassign Pos     │      │ ├─ JD Comparison   │
│ └─ Force Match      │      │ └─ Feedback Loop    │
└─────────────────────┘      └──────────────────────┘
        │                            │
        ▼                            ▼
    REST API              WebSocket Real-Time Feed
    /agents/*             /ws/agent-operator
```

---

## Component 1: Agent Command Panel

### Display:

```
┌─ AGENT CONTROL PANEL ─────────────────────────────────┐
│                                                        │
│  CV INGESTION AGENT                                   │
│  Status: 🟢 Running  |  Uptime: 47h 23m               │
│  Queue: 12 pending   |  Processed: 342 today          │
│  Error Rate: 0.3%    |  Throughput: 7.2 items/hour   │
│  [Pause] [Stats] [Logs]                               │
│                                                        │
│  JD ANALYSIS AGENT                                    │
│  Status: 🟢 Running  |  Uptime: 47h 23m               │
│  Queue: 3 drafts     |  Processed: 28 today           │
│  Error Rate: 0.0%    |  Throughput: 0.6 drafts/hour  │
│  [Pause] [Stats] [Logs]                               │
│                                                        │
│  EMAIL POLLING AGENT                                  │
│  Status: 🟢 Running  |  Uptime: 47h 23m               │
│  Queue: 5 emails     |  Processed: 156 today          │
│  Error Rate: 1.2%    |  Last check: 2 min ago         │
│  [Pause] [Stats] [Logs]                               │
│                                                        │
│  ASSESSMENT AGENT                                     │
│  Status: 🟢 Running  |  Uptime: 47h 23m               │
│  Queue: 8 processing |  Processed: 89 today           │
│  Error Rate: 0.1%    |  Avg. Time: 4.2s per assess    │
│  [Pause] [Stats] [Logs]                               │
│                                                        │
│  LEARNING AGENT                                       │
│  Status: 🟢 Running  |  Last Recal: 18h ago           │
│  Corpus Size: 2,341  |  Next Recal: 6h from now       │
│  Accuracy Gain: +3.2%|  Weights Updated: 147 times    │
│  [Force Recal] [Corpus] [Training]                    │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### Controls:

**Agent Lifecycle:**
```
POST /agents/{agent_type}/pause       → Pause polling
POST /agents/{agent_type}/resume      → Resume polling
POST /agents/{agent_type}/config      → Adjust frequency
  {
    "polling_interval_seconds": 60,
    "batch_size": 10,
    "auto_approve_confidence": 0.85
  }
```

**Example: Adjust CV Agent**
```bash
POST /agents/cv/config
{
  "polling_interval_seconds": 30,        # Check inbox every 30s
  "batch_size": 5,                       # Process 5 CVs per cycle
  "auto_approve_confidence": 0.90,       # Only auto-approve high-confidence matches
  "min_match_score": 0.75                # Skip if match score < 0.75
}
```

---

## Component 2: Real-Time Agent Metrics Dashboard

### Display:

```
┌─ AGENT METRICS & PERFORMANCE ─────────────────────────┐
│                                                        │
│  24-HOUR PERFORMANCE                                  │
│  ┌─────────────────────────────────────────────────┐  │
│  │ CV Agent:        ████████████░░░ 342 items      │  │
│  │ JD Agent:        ████░░░░░░░░░░░  28 items      │  │
│  │ Email Agent:     ██████████████░░ 156 items     │  │
│  │ Assessment Agent:██████████░░░░░░  89 items     │  │
│  └─────────────────────────────────────────────────┘  │
│                                                        │
│  ERROR TRENDS (7-day)                                 │
│  CV Agent:        ▁▁▂▂▂▁▁  (avg: 0.3%)               │
│  JD Agent:        ▁▁▁▁▁▁▁  (avg: 0.0%)               │
│  Email Agent:     ▃▂▄▂▂▃▂  (avg: 1.2%)               │
│  Assessment:      ▁▁▁▁▁▁▁  (avg: 0.1%)               │
│                                                        │
│  MATCH QUALITY IMPROVEMENT                            │
│  Auto-Match Success: 87.3% (↑ 2.1% from yesterday)   │
│  Avg. Match Confidence: 0.83 (↑ 0.05 from 7d avg)    │
│  Human Override Rate: 12.7% (↓ 0.8% from 7d avg)     │
│                                                        │
│  COST METRICS                                         │
│  Cost per Assessment: $0.012                          │
│  Cost per CV Processed: $0.008                        │
│  Cost per JD Analyzed: $0.045                         │
│  Daily Cost: $4.23 (342 + 28 + 156 items)            │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## Component 3: Unified Queue Management

### Current State - Awaiting Review Items:

```
┌─ INGEST QUEUE (Awaiting Human Decision) ──────────────┐
│                                                        │
│ [Filter: Type▼] [Status▼] [Source▼] [Sort▼]          │
│                                                        │
│ RESUME: john_doe.pdf (CV Agent - auto-matched)       │
│   Source: Gmail attachment                            │
│   Auto-Match: Chief Product Manager (confidence: 0.91)│
│   Top 3 Alternatives:                                 │
│     2. Senior PM (0.87)                              │
│     3. Product Lead (0.84)                            │
│   [Approve → Chief PM] [Approve → Senior PM]         │
│   [Override Match] [Reject] [Review]                 │
│                                                        │
│ JD DRAFT: backend-engineer-senior (JD Agent)         │
│   Source: Recruiter paste                             │
│   Quality Score: 78/100                               │
│   Issues Found:                                       │
│     • Requirement creep detected (asking for 15+ YOE) │
│     • 3 missing sections (benefits, culture, team)    │
│   AI-Generated Improved Draft:                        │
│     [Show] [Compare] [Use] [Reject]                   │
│                                                        │
│ RESUME: jane_smith.docx (Email Agent - parsed)       │
│   Source: Email submission                             │
│   Extract Status: ✓ Complete (2000+ words)           │
│   Auto-Match: Senior Backend Engineer (confidence: 0.78)│
│   [Approve] [Override Match] [Reject] [Hold for Review]│
│                                                        │
└────────────────────────────────────────────────────────┘
```

### Queue Actions:

```
POST /agents/queue/{item_id}/approve
{
  "notes": "Perfect fit for backend team",
  "force_position_id": null  # Use auto-match
}

POST /agents/queue/{item_id}/approve
{
  "notes": "Better fit for this team",
  "force_position_id": "position-456"  # Override auto-match
}

POST /agents/queue/{item_id}/reject
{
  "reason": "Does not meet minimum requirements",
  "feedback": "Lacking required Kubernetes experience"
}

POST /agents/queue/{item_id}/flag-for-training
{
  "reason": "Edge case: Good match but low confidence",
  "suggestion": "Improve System Design capability weights"
}
```

---

## Component 4: Human-in-Loop Decision Support

### Problem: Current System Auto-Decides Too Much

Current flow:
```
CV arrives → Agent auto-matches → Assessment runs → Decision made → Done
             ↑
      What if confidence < threshold?
```

### Solution: Decision Confidence Scoring

```
┌─ AWAITING DECISION (High Value Cases) ─────────────────┐
│                                                         │
│ CANDIDATE: Alexander Chen                              │
│ Match Confidence: 67% ⚠️  (Below auto-approve)         │
│                                                         │
│ Position 1: Senior Backend Engineer (0.67 match)       │
│ Position 2: Staff Engineer (0.65 match)                │
│ Position 3: Tech Lead (0.62 match)                     │
│                                                         │
│ Why uncertain:                                          │
│   • CV emphasizes frontend more than backend           │
│   • Team leadership is strong but not in CV explicitly │
│   • Experience duration matches but domain is adjacent │
│                                                         │
│ Recruiter Notes:                                       │
│   "Talked to Alexander - very interested in backend"   │
│   "Mentioned leading 5-person team (not on CV)"        │
│                                                         │
│ [Auto-Proceed to Senior Backend] [Manual Review]      │
│ [Archive & Suggest for Next Role] [Hold for Training] │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Training Integration:

```
POST /agents/queue/{item_id}/flag-for-training
{
  "reason": "Edge case - good candidate but system uncertain",
  "suggestion": "Improve 'software-to-swe-manager' capability mapping",
  "flag_type": "curriculum_improvement"
}

This sends the case to:
1. Training System for curriculum analysis
2. Learning Loop for weight recalibration
3. Feedback tracking for next recalibration cycle
```

---

## Component 5: WebSocket Event Stream

### New WebSocket Endpoint:

```
WS /ws/agent-operator
```

### Message Types:

**Agent Status Update:**
```json
{
  "type": "agent_status",
  "agent": "cv",
  "status": "processing",
  "queue_size": 12,
  "processed_today": 342,
  "error_rate": 0.003,
  "timestamp": "2026-06-07T14:32:10Z"
}
```

**Queue Item Event:**
```json
{
  "type": "queue_item",
  "action": "added",
  "item_id": "ingest-789",
  "item_type": "resume",
  "source": "email",
  "auto_match_position": "position-456",
  "confidence": 0.89,
  "status": "awaiting_review",
  "timestamp": "2026-06-07T14:32:15Z"
}
```

**Assessment Completion:**
```json
{
  "type": "assessment_complete",
  "assessment_id": "assess-123",
  "ingest_item_id": "ingest-789",
  "decision": "AUTO_APPROVE",
  "score": 0.87,
  "governance_passed": true,
  "timestamp": "2026-06-07T14:32:42Z"
}
```

**Agent Error:**
```json
{
  "type": "agent_error",
  "agent": "jd",
  "error": "Failed to parse JD PDF",
  "item_id": "ingest-790",
  "retry_count": 1,
  "next_retry": "2026-06-07T14:35:10Z",
  "timestamp": "2026-06-07T14:32:50Z"
}
```

**Learning Update:**
```json
{
  "type": "learning_update",
  "event": "recalibration_started",
  "corpus_size": 2341,
  "holdout_size": 234,
  "timestamp": "2026-06-07T18:00:00Z"
}
```

---

## Implementation Roadmap

### Phase 1: Agent Command Panel (2-3 days)
- Display agent status (running, paused, error)
- Show real-time metrics (queue size, throughput, error rate)
- Implement pause/resume controls
- Add configuration interface for polling intervals

**Files to Create:**
- `web/src/app/admin/agents/operator/page.tsx` - Main dashboard
- `web/src/components/admin/AgentCommandPanel.tsx` - Agent controls
- `web/src/components/admin/AgentMetrics.tsx` - Real-time metrics
- `backend/app/api/v1/agents_extended.py` - New agent control APIs

### Phase 2: Queue Management UI (2-3 days)
- Display awaiting_review items
- Show auto-match confidence + alternatives
- Implement approve/reject/reassign actions
- Add notes/feedback collection

**Files to Create:**
- `web/src/components/admin/QueueManagement.tsx` - Queue display
- `web/src/components/admin/DecisionSupport.tsx` - Confidence-based hints
- Extend `backend/app/api/v1/agents.py` with decision tracking

### Phase 3: Metrics Dashboard (2 days)
- Display 24h, 7d, 30d performance metrics
- Show error trends
- Track cost per operation
- Display match quality improvements

**Files to Create:**
- `web/src/components/admin/AgentMetricsDashboard.tsx`
- `backend/app/workers/agent_metrics_collector.py` - Metric collection

### Phase 4: WebSocket Integration (1-2 days)
- Create `/ws/agent-operator` endpoint
- Broadcast agent events to dashboard
- Implement real-time queue updates
- Show live error notifications

**Files to Create:**
- `backend/app/websocket/agent_operator.py` - WS handler
- `web/src/hooks/useAgentOperator.ts` - Frontend WS hook

### Phase 5: Training Integration (1-2 days)
- Flag edge cases for curriculum improvement
- Send decision data to training system
- Track how feedback improves future decisions
- Display feedback impact in metrics

**Files to Create:**
- `backend/app/workers/agent_feedback_loop.py`
- `web/src/components/admin/FeedbackTracker.tsx`

---

## API Additions Required

### 1. Agent Control

```
POST /agents/{agent_type}/pause
POST /agents/{agent_type}/resume
POST /agents/{agent_type}/config
  {
    "polling_interval_seconds": 60,
    "batch_size": 10,
    "auto_approve_confidence": 0.85,
    "enable_auto_approve": true
  }

GET /agents/metrics
  Response:
  {
    "cv": {
      "processed_24h": 342,
      "error_rate": 0.003,
      "throughput": 7.2,
      "uptime_hours": 47.38
    },
    "jd": {...},
    "email": {...},
    "assessment": {...}
  }

GET /agents/health
  Response:
  {
    "agents": [
      {
        "type": "cv",
        "status": "running",
        "last_check": "2026-06-07T14:32:10Z",
        "queue_size": 12,
        "next_check": "2026-06-07T14:33:10Z"
      },
      ...
    ]
  }
```

### 2. Queue Decision Support

```
GET /agents/queue?awaiting_review=true&sort_by_confidence=asc
  Response: Items sorted by decision confidence

GET /agents/queue/{item_id}/alternatives
  Response: Top 5 alternative positions with scores

POST /agents/queue/{item_id}/flag-for-training
  {
    "reason": "Edge case - uncertain match",
    "suggestion": "Improve mapping X",
    "severity": "medium"
  }
```

### 3. Metrics & Analytics

```
GET /agents/metrics/24h
GET /agents/metrics/7d
GET /agents/metrics/30d

GET /agents/cost-analysis
  Response: Cost per item, per operation type

GET /agents/quality-analysis
  Response: Match accuracy, override rates, etc.
```

---

## OpenClaw-Style Autonomy: What This Enables

### Before:
```
Recruiter manually uploads CV
→ System auto-matches
→ Recruiter reviews match
→ Assessment runs
→ Recruiter views result
```

### After (Agent Operator Mode):
```
System runs fully autonomous 24/7:
├─ Monitors inbox/email continuously
├─ Auto-matches CVs to best JDs
├─ Runs assessments
├─ Auto-approves high-confidence candidates
├─ Flags edge cases for human review
├─ Processes feedback for training
└─ Improves matching with each cycle

Recruiter/Admin can:
├─ Watch in real-time via dashboard
├─ Pause/resume agents
├─ Adjust confidence thresholds
├─ Override edge cases
├─ Provide feedback for learning
└─ Monitor cost/quality metrics
```

**Result:** True AI-native autonomous recruitment system operating like an OpenClaw agent.

---

## Why This Matters

1. **Autonomous 24/7:** System works while team sleeps
2. **Human-in-Loop:** Edge cases go to humans for decision
3. **Learning Feedback:** Each human decision improves system
4. **Transparency:** Dashboard shows exactly what agents are doing
5. **Control:** Admins can adjust thresholds, pause agents, override decisions
6. **Cost Visibility:** Track actual cost per hire

---

## Success Metrics

**System Should Achieve:**
- ✅ Auto-approve rate: 75%+ (high confidence matches)
- ✅ Human override rate: <15% (edge cases only)
- ✅ Error rate: <1% across all agents
- ✅ Processing latency: <5 seconds per CV
- ✅ Cost per assessment: <$0.02
- ✅ Match accuracy: >85% (validated by hires)
- ✅ Learning improvement: +2-5% accuracy per month
