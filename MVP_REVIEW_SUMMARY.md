# Agent Operator Dashboard - Design Review Summary

**Status:** Design Review Complete ✅  
**Next:** Ready to Build (Option 1)  
**Additional:** Autonomous Features to Add (Option 3)

---

## Design Review Results

### Overall Assessment: 70% Aligned ✅

The original design was **good architecture**, but made some assumptions about infrastructure that doesn't exist yet. The good news: **we can build a working MVP in 2-3 days using existing endpoints.**

---

## What the Design Got Right ✅

1. **Queue Management Architecture**
   - Design assumes `IngestQueueItem` with `awaiting_review` status
   - **Reality:** Exact model exists in database
   - **No changes needed:** Can use as-is

2. **WebSocket Infrastructure**
   - Design specifies real-time updates
   - **Reality:** `/ws/agents` endpoint already exists + working
   - **No changes needed:** Just emit additional events

3. **Database Audit Trail**
   - Design assumes `reviewed_by` and `review_notes` fields
   - **Reality:** Both fields exist on IngestQueueItem
   - **No changes needed:** Use existing fields

4. **Control APIs**
   - Design assumes approval workflow
   - **Reality:** `/agents/queue/{id}/approve` endpoint exists
   - **No changes needed:** Works as expected

5. **Assessment Integration**
   - Design assumes approving queues assessment
   - **Reality:** Exactly what happens in existing endpoint
   - **No changes needed:** Pipeline ready

---

## What the Design Missed ❌

1. **Agent Control Endpoints** (Not built yet)
   - Design: `POST /agents/{type}/pause`, `POST /agents/{type}/resume`, `POST /agents/{type}/config`
   - **Reality:** These endpoints don't exist
   - **Impact:** Can't pause/resume agents from dashboard
   - **Solution:** Build Phase 2 (not MVP)

2. **Metrics Collection** (Not built yet)
   - Design: `GET /agents/metrics` with throughput, error rates
   - **Reality:** No metrics infrastructure
   - **Impact:** Can't show "CV Agent: 342 items processed"
   - **Solution:** Build Phase 2 (not MVP)

3. **Confidence Scoring** (Not implemented)
   - Design: Show match confidence on queue items
   - **Reality:** CV agent auto-matches but doesn't score confidence
   - **Impact:** Can't prioritize uncertain matches
   - **Solution:** Enhance CV agent in Phase 2

4. **Alternative Positions** (Not calculated)
   - Design: Show top 5 alternative positions with scores
   - **Reality:** Agent just finds single best match
   - **Impact:** Can't show "Also consider: Senior PM (0.87), Product Lead (0.84)"
   - **Solution:** Extend matching logic in Phase 2

5. **Cost Tracking** (Not in system)
   - Design: Display cost per assessment
   - **Reality:** No cost calculation exists
   - **Impact:** Cost visibility unavailable
   - **Decision:** Deprioritize (not essential for MVP)

---

## What's Actually Available (Unused in Design)

1. **ProgressTracker System**
   - Existing event system for assessment progress
   - Can reuse for agent events instead of building new WebSocket layer

2. **ConnectionManager**
   - WebSocket connection pattern proven on position-scoped subscriptions
   - Can adapt for agent-scoped instead

3. **Detailed Assessment Scoring**
   - Database has: `capability_score`, `traditional_score`, `semantic_score`, `governance_*` fields
   - Design didn't mention exposing these in queue context

4. **Decision Support Data**
   - Assessment model already tracks why decisions were made
   - Can surface in queue detail panel

---

## MVP Scope (What We're Building)

### Will Build ✅
- Queue management UI (list awaiting_review items)
- Approve/Reject/Hold buttons with notes
- Real-time updates via WebSocket
- Live event feed
- Basic agent status visibility

### Won't Build in MVP ❌
- Agent pause/resume controls (Phase 2)
- Metrics dashboard (Phase 2)
- Confidence scoring (Phase 2)
- Alternative positions (Phase 2)
- Training integration UI (Phase 4)
- Cost analysis (Future)

### Why MVP Scope Works
- Uses 100% existing endpoints (no new backend work beyond 2-3 hours)
- Can ship in 2-3 days (frontend focused)
- Solves immediate problem (operators need to approve edge cases)
- Foundation for future phases

---

## Build Plan (2-3 Days)

### Day 1: Backend (2-3 hours)
```python
# Extend response models to include decision context
# Add event broadcasting for queue actions
# Test response format

Files: backend/app/schemas/ingest_queue.py
       backend/app/api/v1/agents.py
```

### Day 2: Frontend (6-8 hours)
```typescript
// Build queue table with sorting/filtering
// Build item detail panel
// Build action buttons (approve/reject/hold)
// Build WebSocket subscription hook

Files: web/src/app/admin/agents/operator/page.tsx
       web/src/components/admin/operators/QueueTable.tsx
       web/src/components/admin/operators/QueueItemDetail.tsx
       web/src/components/admin/operators/ActionPanel.tsx
       web/src/components/admin/operators/LiveEventFeed.tsx
       web/src/hooks/useAgentOperator.ts
```

### Day 3: Integration & Polish (2-4 hours)
```typescript
// Wire WebSocket to components
// Test end-to-end
// Add error handling
// Performance optimization

Testing: approve item → see event → queue updates
```

---

## Team Effort

**Backend:** 1 person × 2-3 hours = 2-3 hours  
**Frontend:** 1-2 people × 6-8 hours = 6-8 hours  
**QA:** 1 person × 2-3 hours = 2-3 hours  
**Total:** ~12-14 hours (roughly 1.5 days for 2 people working in parallel)

---

## What This Enables

### Immediately (MVP)
```
Admin sees: Dashboard with 3 awaiting decisions
Admin clicks: Item detail panel
Admin decides: Approve/Reject/Hold
System does: Updates database, notifies, enqueues assessment
Admin sees: Live event feed with action
```

Result: **Humans can make decisions in real-time on uncertain cases**

### Short Term (Phase 2)
```
Admin can pause CV agent (stops folder monitoring)
Admin adjusts confidence thresholds (only auto-approve if >0.85)
Admin sees metrics (342 CVs processed, 1 error)
```

Result: **Operators have controls over agent behavior**

### Medium Term (Phase 3)
```
Admin sees: "CV uncertain (67% match) - Top 3 positions listed"
Admin overrides: Selects position #2 instead
System learns: Used alternative for similar cases next time
```

Result: **System learns from operator decisions**

### Long Term (Phase 4+)
```
Admin flags edge case: "Improve leadership detection"
System learns: Updates capability weights
Recalibration: Tests on 100 past assessments
Result: +3% accuracy improvement
Admin sees: Feedback impact metrics
```

Result: **Autonomous system improving continuously from feedback**

---

## Success Metrics (MVP)

**System Performance:**
- ✅ Page load: <2 seconds
- ✅ Approve/reject: <1 second response
- ✅ WebSocket updates: <2 seconds from action to display
- ✅ 99% uptime (auto-reconnect on disconnect)

**User Experience:**
- ✅ Can approve/reject without writing SQL
- ✅ Can see why item is awaiting review
- ✅ Can add notes for future reference
- ✅ Can see action history

**Business:**
- ✅ Faster recruiter response time
- ✅ Faster candidate notifications
- ✅ Operators have visibility into queue
- ✅ Foundation for learning feedback loop

---

## Transition to Phase 2+ Features

### Phase 2: Agent Control (Week 2)
- Requires backend work (Celery Beat integration)
- Build agent pause/resume endpoints
- Build agent config endpoints
- Estimated: 3-4 days

### Phase 3: Confidence & Alternatives (Week 3)
- Requires CV agent enhancement (match confidence scoring)
- Requires matching algorithm work (find top-5 positions)
- Estimated: 3-4 days

### Phase 4: Training Integration (Week 4)
- Feedback loop with learning system
- Curriculum improvement tracking
- Estimated: 2-3 days

### Phase 5+: Advanced Metrics & Optimization
- Throughput dashboards
- Error trend analysis
- Cost optimization
- Estimated: Ongoing

---

## Risk Mitigation

**Risk:** WebSocket connection drops
- **Mitigation:** Add manual refresh button, auto-reconnect with backoff

**Risk:** Multiple admins approving same item
- **Mitigation:** Show "Processing..." state, disable after approval

**Risk:** Item disappears from queue (old browser cache)
- **Mitigation:** Show "Item no longer awaiting decision" message

**Risk:** Slow assessment pipeline (approvals queue up)
- **Mitigation:** Phase 2 adds pause/resume, can stop ingestion if backlog grows

---

## Architecture Diagram (After MVP)

```
                    TRUEMATCH OPERATOR SYSTEM
    
    ┌─────────────────────────────────────────────────────┐
    │   Admin opens /admin/agents/operator                 │
    └────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴────────────┐
         │                        │
         ▼                        ▼
    ┌─────────────┐        ┌────────────────┐
    │ Load Queue  │        │ Connect WS     │
    │ (REST API)  │        │ to /ws/agents  │
    └──────┬──────┘        └────────┬───────┘
           │                        │
           ├─ GET /agents/queue     │
           │  ?status=awaiting_     │
           │   review&limit=50      │
           │                        │
           ▼                        ▼
    ┌──────────────────────────────────────┐
    │    Queue List (React Table)          │
    │  ├─ name, type, source, created     │
    │  ├─ Sorting/Filtering                │
    │  └─ Click row → detail panel         │
    └──────────────┬───────────────────────┘
                   │
         ┌─────────┴──────────┐
         │                    │
    [User clicks]         [WS broadcasts]
         │                    │
         ▼                    ▼
    ┌──────────────┐   ┌────────────────┐
    │ Detail Panel │   │ Event Feed     │
    │             │   │                │
    │ [Approve]   │   │ - Item added   │
    │ [Reject]    │   │ - Item approved│
    │ [Hold]      │   │ - Assess. done │
    └──────┬──────┘   └────────────────┘
           │
           ├─ POST /agents/queue/{id}/approve
           │
           ▼
    ┌──────────────────────────────────────┐
    │ Backend approves → enqueues assessment│
    │ Broadcasts: queue_item_action event   │
    └──────────────────────────────────────┘
```

---

## Ready to Build?

**Option 1: Build MVP Operator Dashboard**
- Start with Day 1 backend work
- Parallel frontend development
- Launch in 2-3 days

**Option 3: Identify Additional Autonomous Features**
- While building dashboard, what else should agents do?
- What manual processes could be automated?
- What feedback loops would improve matching?

---

## Next Steps

1. ✅ **Design review complete** - Plans are refined and realistic
2. 🔄 **Option 1:** Ready to start building (Day 1: backend)
3. 🔄 **Option 3:** Identify other autonomous features to add
4. 📋 **Detailed docs created:**
   - AGENT_OPERATOR_DASHBOARD_DESIGN.md (full architecture)
   - AGENT_OPERATOR_IMPLEMENTATION_CHECKLIST.md (tasks)
   - AGENT_AUTONOMY_STATUS.md (current state)
   - OPERATOR_DASHBOARD_MVP_PLAN.md (this plan)

---

## Recommendation

**Start building the MVP immediately:**
- Day 1: Backend changes (easy, unblocks frontend)
- Day 2-3: Frontend development (parallel possible)
- By end of week: Working operator dashboard

This gives you:
- ✅ Visibility into queue (what agents are doing)
- ✅ Control over approvals (human-in-loop)
- ✅ Foundation for Phase 2+ features
- ✅ Closes the gap: 70% → 100% autonomous system

**Shall we start with Day 1 backend work?**
