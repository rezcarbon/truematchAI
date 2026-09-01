# PHASE 1: SCREENING AGENT - COMPREHENSIVE IMPLEMENTATION PLAN

## Quick Navigation
- [Architecture Overview](#1-architecture-overview)
- [Data Model Changes](#2-data-model-changes)
- [API/Service Layer](#3-apisservice-layer-design)
- [Screening Agent Implementation](#4-screening-agent-implementation)
- [Recruiter Review Interface](#5-recruiter-review-interface-flow)
- [Integration Points](#6-integration-points)
- [Conscience Implementation](#7-conscience-implementation)
- [Implementation Steps](#8-implementation-steps-detailed-checklist)
- [Success Criteria](#9-success-criteria)
- [Risk Mitigation](#10-risk-mitigation)
- [Critical Files](#11-critical-files-for-implementation)

---

## 1. ARCHITECTURE OVERVIEW

### 1.1 Component Placement & Integration

**ScreeningAgent Location:**
- **File**: `/backend/app/agents/screening_agent.py`
- **Type**: Autonomous agent (non-conversational, decision-making)
- **Role**: Batch CV screening without recruiter interaction during processing
- **Inherits from**: `EnhancedBaseAgent` (like `RecruiterAgent`)

**Key Design Principle - "Conscience by Default":**
- Agent generates screening RECOMMENDATIONS, never final decisions
- Agent cannot exclude candidates from pipeline (fail-safe)
- Recruiter MUST make the final interview/reject decision
- All agent screening logic is logged for audit trail

### 1.2 Decision Boundaries

| Decision Type | Agent | Recruiter |
|---|---|---|
| CV parsing + extraction | Agent ✓ | Review |
| Screening recommendation (advance/hold/review) | Agent ✓ | Override |
| Candidate exclusion (reject) | ✗ RECRUITER ONLY | Recruiter ✓ |
| Interview scheduling | ✗ | Recruiter ✓ |
| Final hire decision | ✗ | Recruiter ✓ |
| Override rationale recording | Agent logs | Recruiter explains |

---

## 2. DATA MODEL CHANGES

### 2.1 New Tables Required

**screening_results** (new)
```
├── id (UUID, PK)
├── position_id (UUID, FK → positions)
├── resume_id (UUID, FK → resumes)
├── user_id (UUID, FK → users) [candidate]
├── screening_batch_id (UUID, FK → screening_batches)
├── agent_recommendation (enum: advance/hold/review)
├── confidence_score (int 0-100)
├── screening_summary (encrypted text) [5-min summary for recruiter]
├── screening_details (encrypted JSON) [full analysis]
├── bias_flags (encrypted JSON) [conscience checks]
├── recruiter_decision (enum: interview/hold/further_review/null)
├── recruiter_id (UUID, FK → users)
├── recruiter_notes (encrypted text)
├── was_overridden (boolean)
├── override_reason (encrypted text)
├── created_at (timestamp)
├── updated_at (timestamp)
└── indexes: (position_id, recruiter_decision), (position_id, created_at), (resume_id, position_id)
```

**screening_batches** (new)
```
├── id (UUID, PK)
├── position_id (UUID, FK → positions)
├── created_by (UUID, FK → users) [recruiter who initiated]
├── total_candidates (int)
├── screened_count (int)
├── pending_review_count (int)
├── status (enum: queued/screening/pending_review/completed)
├── started_at (timestamp)
├── completed_at (timestamp nullable)
├── batch_config (JSON)
├── metadata (JSON)
```

### 2.2 Extended Models

**assessments** table - Add:
```
├── screening_result_id (UUID, FK → screening_results, nullable)
├── screening_initiated_at (timestamp, nullable)
└── screening_phase (enum: initial/full_assessment/review, default: initial)
```

**decisions** table - Add:
```
├── screening_override_reason (encrypted text, nullable)
├── recruiter_confidence (int 0-100, nullable)
└── is_screening_decision (boolean, default: false)
```

---

## 3. API/SERVICE LAYER DESIGN

### 3.1 New API Endpoints

```
POST /api/v1/screenings/batches
  - Initiate bulk CV screening (1000+ candidates)
  - Returns: 202 Accepted with batch_id

GET /api/v1/screenings/batches/{batch_id}
  - Get batch status and progress

GET /api/v1/screenings/batches/{batch_id}/pending
  - Get paginated screening results for recruiter review

GET /api/v1/screenings/results/{screening_result_id}
  - Get full screening details (5-min summary + analysis)

PATCH /api/v1/screenings/results/{screening_result_id}/decide
  - Record recruiter decision (override point)

POST /api/v1/screenings/batches/{batch_id}/bulk-decide
  - Bulk recruiter decisions for efficiency

GET /api/v1/screenings/batches/{batch_id}/metrics
  - Analytics dashboard (distribution, override rate, bias alerts)
```

### 3.2 Key Services

**ScreeningService**
- create_screening_batch()
- get_pending_reviews()
- process_recruiter_decision()
- get_screening_metrics()

---

## 4. SCREENING AGENT IMPLEMENTATION

### 4.1 ScreeningAgent Class

**Key Features:**
- NOT conversational (no chat interface)
- Autonomous, batch-oriented
- Generates RECOMMENDATIONS only (advance/hold/review)
- Conscience checks built-in (no exclusion logic)

**Main Pipeline:**
1. Conscience Check (BEFORE evaluation) - Detect demographic indicators
2. Skill Matching (Pillar 1 - Traditional)
3. Experience Fit (Pillar 2)
4. Career Trajectory (Pillar 3)
5. Red Flags (concerns, not exclusions)
6. Recommendation Generation
7. Summary Generation (5-min brief for recruiter)
8. Learning Signal Capture

### 4.2 Recommendation Logic

```
CRITICAL: Never returns "exclude" or "reject"
Only output space: ["advance", "hold", "review"]

Scoring:
- Advance (75+): clear fit, move to interview
- Hold (50-75): potential fit, needs recruiter review
- Review (<50): unclear, route to recruiter for decision

If conscience check triggered OR red flags detected:
  → Always recommend "review" (human oversight)
```

### 4.3 Summary Generation

5-minute recruiter brief (~300-400 words):
- Top 1-2 sentences: recommendation + confidence
- Key matches: top 3 aligned skills/experience
- Gaps: missing skills (not disqualifying)
- Signals: career progression, stability
- Concerns: red flags (if any) with context
- Conscience notes: fairness considerations
- Recruiter action: "Schedule interview" | "Further review recommended"

---

## 5. RECRUITER REVIEW INTERFACE FLOW

### 5.1 UX Flow

1. **INITIATE SCREENING**
   - Upload 1000 CVs for position
   - Optional batch config (min years, skills, etc.)
   - Submit → Batch queued (202 Accepted)

2. **MONITOR PROGRESS**
   - Shows: "750/1000 screened (75%)", ETA, status

3. **REVIEW QUEUE**
   - Paginated list (10 per page)
   - Sorted by confidence_score DESC
   - Quick summary cards

4. **DECIDE ON EACH CANDIDATE**
   - Full screening_summary (5-min read)
   - Recruiter decision buttons
   - [Schedule Interview] [Hold for Later] [Request Further Review]

5. **BULK DECISIONS**
   - Multi-select + batch action
   - Multi-decide for efficiency

### 5.2 Override Detection & Learning

When recruiter overrides agent recommendation:
- Record Decision with is_screening_decision=true
- Capture override reason and recruiter confidence
- Log in AgentLearningLog for feedback loop
- Trigger reinforcement learning

---

## 6. INTEGRATION POINTS

### 6.1 Hook into CV Upload Workflow

Current: Resume Upload → CV Parsing → [Stored]
New: ... → [IF position has screening batch] → Enqueue screening task

### 6.2 Trigger After Resume Extraction

on_resume_extracted() hook:
- Check if position has active screening batch
- If yes, enqueue screening task

### 6.3 Link to Decision Tracking

When recruiter decides:
- Create Decision record linked to ScreeningResult
- Set ai_recommendation_followed flag
- Trigger learning loop

### 6.4 Governance Gate Integration

Before recruiter sees screening result:
- Run governance gates (disparate impact, bias indicators)
- If triggered: escalate to "review" (never hide)
- Flag for human review

---

## 7. CONSCIENCE IMPLEMENTATION

### 7.1 Preventing Unfair Exclusion

**Defense in Depth:**

1. **ARCHITECTURE LEVEL**: Agent cannot output "exclude"
   - Output space: ["advance", "hold", "review"] only

2. **GATE LEVEL**: Governance checks before recruiter sees result
   - Disparate impact check (80% rule)
   - Demographic indicator check
   - Fairness distribution check

3. **PROCESS LEVEL**: Recruiter sees all flags
   - Conscience notes in 5-min summary
   - Red flags flagged as "concerns" not "disqualifications"

4. **AUDIT LEVEL**: All decisions are traceable
   - Screening result logged
   - Recruiter decision logged
   - Override reason logged
   - Governance flags logged

5. **MONITORING LEVEL**: Disparate impact tracking
   - Weekly analysis by demographic group
   - Four-fifths ratio calculation
   - Alerts if <0.8 for any group

### 7.2 Red Flag vs Exclusion

Red Flags = Information, Not Decision:
- Employment gaps (not excluding, just noting)
- Frequent job changes (for discussion, not rejection)
- Skills atrophy (upskilling opportunity)
- Overqualified (retention discussion)

All red flags are non-blocking. Recruiter decides.

### 7.3 Recruiter Catches Unfair Patterns

Monitor recruiter's decision patterns:
- Consistent rejection of certain demographic groups
- Override patterns (always overriding for certain groups)
- Inconsistent application of red flags

If 80% rule violated: Flag disparate impact for review.

---

## 8. IMPLEMENTATION STEPS (DETAILED CHECKLIST)

### Phase 1a: Data Models (Week 1)

- [ ] Create migration: create_screening_results_table.py
- [ ] Create migration: screening_batches_table.py
- [ ] Create migration: extend_assessments_table.py
- [ ] Create migration: extend_decisions_table.py
- [ ] Create models in /backend/app/models/
  - [ ] screening_result.py
  - [ ] screening_batch.py
- [ ] Create schemas in /backend/app/schemas/
  - [ ] screening.py

### Phase 1b: Agent Core Logic (Week 1-2)

- [ ] Create /backend/app/agents/screening_agent.py
  - [ ] ScreeningAgent class
  - [ ] screen_resume() main method
  - [ ] _run_conscience_check()
  - [ ] _evaluate_skill_match()
  - [ ] _evaluate_experience()
  - [ ] _evaluate_trajectory()
  - [ ] _identify_red_flags()
  - [ ] _generate_recommendation()
  - [ ] _generate_summary()
  - [ ] _capture_learning_signals()

- [ ] Create /backend/app/services/screening_service.py
- [ ] Unit tests for agent logic (30+ tests)

### Phase 1c: Worker/Queue System (Week 2)

- [ ] Create /backend/app/workers/screening_queue.py
  - [ ] process_screening_batch() Celery task
- [ ] Create /backend/app/workers/screening_governance.py
- [ ] Integrate with existing workers
- [ ] Integration tests

### Phase 1d: API Layer (Week 2-3)

- [ ] Create /backend/app/api/v1/screening.py
  - [ ] POST /screenings/batches
  - [ ] GET /screenings/batches/{batch_id}
  - [ ] GET /screenings/batches/{batch_id}/pending
  - [ ] GET /screenings/results/{result_id}
  - [ ] PATCH /screenings/results/{result_id}/decide
  - [ ] POST /screenings/batches/{batch_id}/bulk-decide
  - [ ] GET /screenings/batches/{batch_id}/metrics

- [ ] Authentication & authorization
- [ ] Error handling
- [ ] API tests

### Phase 1e: Integration & Linking (Week 3)

- [ ] Decision tracking integration
- [ ] Learning loop integration
- [ ] Governance integration
- [ ] Realtime updates (optional)

### Phase 1f: Frontend/UX (Week 3-4)

- [ ] Batch initiation screen
- [ ] Batch status monitor
- [ ] Recruiter review interface
- [ ] Screening result detail view
- [ ] Bulk decision interface
- [ ] Analytics dashboard (optional)

### Phase 1g: Testing & Validation (Week 4)

- [ ] Unit tests (80+ tests)
- [ ] Integration tests
- [ ] Performance tests (1000 CVs in <2 days)
- [ ] Conscience validation
- [ ] E2E scenarios

---

## 9. SUCCESS CRITERIA

### 9.1 Performance Targets

| Metric | Target | Validation |
|--------|--------|-----------|
| Bulk screening throughput | 1000 CVs in <2 days | Load test |
| Screening latency per CV | <10 seconds | P95 latency |
| Recruiter review UX | <5 min per candidate | Task timing |
| Bulk decisions throughput | 500 decisions in <5 sec | Batch API timing |
| Summary latency | <3 seconds | Response time |
| Query performance | Review queue <100ms | Index + profiling |

### 9.2 Recruiter Trust Metrics

| Metric | Target | How to Measure |
|--------|--------|---------------|
| Override rate | 20-40% | (decision != recommendation) / total |
| Confidence alignment | >70% match | Recruiter vs. agent confidence |
| Summary readability | >90% helpful | Post-decision feedback |
| Decision velocity | 10+ per minute | Frontend tracking |
| Bulk action adoption | >50% usage | Feature usage analytics |

### 9.3 Agent Quality Metrics

| Metric | Target | How to Measure |
|--------|--------|---------------|
| Recommendation accuracy | >80% match with hire | Track: recommendation → decision → outcome |
| Confidence calibration | >75% interview rate | If agent advance (75% confidence), >75% should interview |
| Red flag relevance | >70% correlation | Spot-check: flags vs. recruiter notes |
| Summary relevance | >80% alignment | Analyze override_reasoning |
| No false exclusions | 0 excluded by agent | Verify: output never "exclude" |

### 9.4 Conscience Validation

| Check | Success Criteria | Testing Method |
|-------|------------------|-----------------|
| Agent never excludes | 100% advance/hold/review | Code review + output validation |
| Red flags informational | Recruiter can interview despite flags | UX testing |
| Governance gates function | Disparate impact detected <24h | Mock batch test |
| Recruiter can override | 100% of overrides recorded | Decision.ai_recommendation_followed |
| Bias monitoring active | Weekly reports generated | DisparateImpactAnalysis records |
| Audit trail complete | Every decision traceable | Spot-check 50 decisions |

### 9.5 Learning Validation

| Mechanism | Success Criteria | Testing Method |
|-----------|------------------|-----------------|
| Override capture | All overrides in AgentLearningLog | Query all non-following decisions |
| Feedback loop | Every decision generates TrainingFeedback | Query DecisionLearning post-100 decisions |
| Pattern learning | Next batch uses learned patterns | Compare before/after hiring feedback |
| Confidence improvement | Scores improve over time | Track avg confidence over time |
| No forgetting | All past decisions in training set | Verify: TrainingFeedback history |

---

## 10. RISK MITIGATION

### 10.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Batch fails mid-way | Medium | High | Idempotent tasks, resume from last |
| Agent hallucination | Low | Medium | Validate against resume text |
| DB constraint violation | Low | High | Migrations + transaction safety |
| Concurrency issue | Medium | High | Lock batch, enforce single recruiter |
| Memory leak | Low | High | Test memory, stream processing |

### 10.2 Bias/Fairness Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Agent learns recruiter bias | Medium | Critical | Separate learning paths |
| Demographic proxy in skills | Medium | High | Audit prompts, blind resume option |
| Red flags correlate with protected class | Medium | High | Track distribution, flag disparate impact |
| Recruiter overrides expose bias | High | Medium | Monitor patterns, flag inconsistency |
| System learns to exclude groups | Low | Critical | Weekly disparate impact analysis |

### 10.3 Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Recruiter overwhelmed | High | Medium | Pagination, sorting, bulk actions |
| Recruiter forgets batch | Medium | Medium | Notifications, dashboard prominence |
| Accidental bulk decision | Low | High | Confirmation dialogs |
| Summary wrong length | Medium | Low | A/B test, iterate |
| Learning slows next iteration | Low | Medium | Async learning, caching |

---

## 11. CRITICAL FILES FOR IMPLEMENTATION

1. `/backend/app/agents/screening_agent.py` (NEW)
   - Core agent logic

2. `/backend/app/api/v1/screening.py` (NEW)
   - API endpoints

3. `/backend/app/services/screening_service.py` (NEW)
   - High-level orchestration

4. `/backend/app/workers/screening_queue.py` (NEW)
   - Celery bulk processing

5. `/backend/app/models/screening_result.py` (NEW)
   - SQLAlchemy ORM model

---

## SUMMARY

This Phase 1 implementation establishes a **conscientious screening agent** that respects recruiter decision authority while dramatically improving hiring velocity (1000 CVs in 2 days vs 2 weeks).

**Core Principles:**
1. **Conscience**: Agent recommends but never excludes; recruiter has final say
2. **Transparency**: All screening logic logged and auditable
3. **Fairness**: Built-in bias detection and recruiter pattern monitoring
4. **Learning**: Feedback loop captures override patterns for agent improvement
5. **Scale**: Batch processing handles 1000+ CVs efficiently

**Timeline:** 4 weeks (Weeks 1-4)
**Success Metric:** 5x recruiter productivity (200+ hires/quarter vs 50 before)
