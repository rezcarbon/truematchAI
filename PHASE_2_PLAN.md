# PHASE 2: ASSESSMENT DESIGNER AGENT - IMPLEMENTATION PLAN

**Version**: 2.0  
**Date**: July 15, 2026  
**Status**: Ready for Implementation  
**Duration**: Weeks 5-8 (4 weeks)  

---

## EXECUTIVE SUMMARY

**Phase 2 Goal**: Agent designs customized assessments that recruiter validates for fairness.

**The Problem**: Assessment design takes 4 hours per candidate. Recruiters must design tests from scratch for each unique profile.

**The Solution**: Agent analyzes candidate profile + JD requirements → designs fair, relevant assessment → recruiter validates fairness.

**The Result**:
- Assessment design: 30 min (vs 4 hours)
- Fair design validation: Built-in
- Interview guidance: Auto-generated
- Recruiter control: Maintained (approves all assessments)

---

## OVERVIEW: PHASE 2 WORKFLOW

```
PHASE 1 COMPLETE: Candidates screened, ranked by confidence
                  ↓
        [RECRUITER SELECTS FOR INTERVIEW]
                  ↓
        PHASE 2: ASSESSMENT DESIGN
          - Agent analyzes candidate profile deeply
          - Maps to role requirements accurately
          - Designs fair, relevant assessment
          - Recruiter validates fairness
          - Assessment ready for use
                  ↓
PHASE 2 OUTPUT: Assessment designs awaiting recruiter approval
```

---

## CORE RESPONSIBILITIES

### Assessment Designer Agent Will:

1. **Analyze Candidate Profile** (Deep)
   - Skills (technical + soft)
   - Experience (years, relevance)
   - Career trajectory (patterns)
   - Strengths (infer from resume)
   - Gaps (learning opportunities)
   - Learning style (hints from background)

2. **Map to Role Requirements**
   - Extract JD requirements
   - Categorize: critical vs nice-to-have
   - Identify gaps vs candidate background
   - Spot growth opportunities
   - Flag potential skill mismatches

3. **Design Fair Assessment**
   - Create competency-based questions
   - Design scenarios tailored to background
   - Avoid biased/unfair questions
   - Mix assessment methods (coding, design, behavioral)
   - Set realistic time limits
   - Prepare evaluation rubric

4. **Generate Interview Guidance**
   - Expected duration
   - Key areas to probe
   - Potential follow-ups
   - Red flags to watch
   - Growth signal indicators

5. **Prepare Assessment Logistics**
   - Questions (3-5 questions)
   - Scenarios (real-world based)
   - Rubric (objective scoring)
   - Time limits (realistic)
   - Tools needed (IDE, whiteboard, etc)
   - Accessibility considerations

### Recruiter Will:

1. **Review Assessment Design**
   - Does it match the role?
   - Is it fair to all candidates?
   - Any biased language?
   - Realistic expectations?
   - Sufficient depth?

2. **Validate Fairness**
   - Would this disadvantage any group?
   - Does it test what matters?
   - Are questions clear?
   - Is scoring objective?

3. **Approve or Request Changes**
   - Approve → Move to assessment phase
   - Request changes → Agent redesigns
   - Reject → Design alternative

4. **Conduct Assessment**
   - Use agent's questions/scenarios
   - Follow agent's guidance
   - Judge quality of responses
   - Record results

5. **Interpret Results**
   - Apply human judgment
   - Assess confidence/growth potential
   - Weigh intangibles
   - Make advancement decision

---

## DATA MODEL ADDITIONS

### Assessment Design (New Table)

```
assessment_designs (new)
├── id (UUID, PK)
├── position_id (UUID, FK)
├── candidate_id (UUID, FK)
├── screening_result_id (UUID, FK)
├── agent_designed_at (timestamp)
├── agent_design (encrypted JSON)
│   ├── questions: [{question, type, expected_duration, rubric}]
│   ├── scenarios: [{scenario, context, questions}]
│   ├── interview_guidance: {duration, probe_areas, red_flags}
│   ├── accessibility_notes: str
│   └── rationale: str (why designed this way)
├── design_fairness_check (encrypted JSON)
│   ├── bias_indicators: [str]
│   ├── fairness_score: 0-100
│   └── recommendations: [str]
├── recruiter_review (enum)
│   ├── pending_review
│   ├── approved
│   ├── changes_requested
│   └── rejected
├── recruiter_id (UUID, FK, nullable)
├── recruiter_feedback (encrypted text, nullable)
├── recruiter_confidence (int 0-100, nullable)
├── created_at (timestamp)
└── updated_at (timestamp)
```

### Extend Assessment Model

```
assessments (extend)
├── assessment_design_id (UUID, FK, nullable) ← Link to design
├── design_approved_at (timestamp, nullable)
└── design_rationale (text, nullable) ← Why this assessment
```

---

## API ENDPOINTS (NEW)

```
POST /api/v1/assessments/design
  Request: {screening_result_id, position_id}
  Response: 202 Accepted with design_id
  Purpose: Initiate assessment design

GET /api/v1/assessments/designs/{design_id}
  Response: Full assessment design for recruiter review
  Purpose: Recruiter views design

GET /api/v1/assessments/designs/pending
  Response: Paginated pending designs for recruiter
  Purpose: Recruiter review queue

PATCH /api/v1/assessments/designs/{design_id}/approve
  Body: {recruiter_notes?, recruiter_confidence?}
  Response: Assessment created and ready
  Purpose: Recruiter approves design

PATCH /api/v1/assessments/designs/{design_id}/request-changes
  Body: {feedback, specific_issues}
  Response: Design queued for revision
  Purpose: Request design changes

GET /api/v1/assessments/designs/{design_id}/fairness-report
  Response: Fairness analysis and recommendations
  Purpose: Show fairness evaluation to recruiter
```

---

## ASSESSMENT DESIGNER AGENT IMPLEMENTATION

### File: `backend/app/agents/assessment_designer_agent.py`

**Main Class: AssessmentDesignerAgent**

**Key Methods:**

1. **design_assessment()**
   - Entry point
   - Orchestrates 6-phase pipeline

2. **_analyze_candidate_profile()**
   - Extract skills (technical, soft)
   - Experience fit analysis
   - Career progression analysis
   - Learning style inference
   - Strength identification
   - Gap analysis

3. **_analyze_role_requirements()**
   - Parse JD deeply
   - Extract competencies
   - Categorize criticality
   - Identify learning opportunities
   - Match to candidate gaps

4. **_design_assessment_questions()**
   - Generate 3-5 questions
   - Match to candidate background
   - Reflect role requirements
   - Vary question types (technical, design, behavioral)
   - Include real-world scenarios

5. **_create_evaluation_rubric()**
   - Define scoring criteria
   - Set performance levels (novice→expert)
   - Make scoring objective
   - Enable calibrated evaluation

6. **_generate_interview_guidance()**
   - Expected duration (time breakdown)
   - Key areas to probe
   - Follow-up questions
   - Red flags to notice
   - Growth signal indicators
   - Accessibility considerations

7. **_run_fairness_check()**
   - CRITICAL: Validate no bias
   - Check for demographic proxies
   - Check for cultural assumptions
   - Flag accessibility concerns
   - Recommend improvements

---

## RECRUITER REVIEW INTERFACE FLOW

```
1. PENDING ASSESSMENTS
   GET /assessments/designs/pending
   └─ Shows paginated queue of designs awaiting review
       Sorted by: recruiter, candidate, recency
       Cards show: candidate, role, agent confidence

2. REVIEW DESIGN
   GET /assessments/designs/{design_id}
   ├─ Full design details
   ├─ Questions (read-only)
   ├─ Evaluation rubric
   ├─ Interview guidance
   ├─ Fairness report
   └─ Accessibility notes

3. VALIDATE FAIRNESS
   - Read fairness analysis
   - Check: Demographic biases?
   - Check: Realistic expectations?
   - Check: Fair to all groups?
   - Check: Tests what matters?

4. DECISION
   - [APPROVE] → Assessment created, ready to use
   - [REQUEST CHANGES] → Specific feedback → Agent redesigns
   - [REJECT] → Design alternative manually

5. AGENT LEARNS
   - Approved: Learns what recruiter values
   - Changes requested: Learns specific issues
   - Rejected: Learns design doesn't fit
```

---

## CONSCIENCE IMPLEMENTATION (Phase 2)

### Fairness Validation Built-In:

1. **Bias Detection Gate**
   - Check for demographic proxies (age, background, origin)
   - Check for unfair assumptions (culture, socioeconomic)
   - Check for accessibility barriers
   - Flag potential disparate impact

2. **Cognitive Load Gate**
   - Check if assessment is realistic
   - Check time allocation vs difficulty
   - Check for knowledge prerequisites
   - Ensure fair to different learning styles

3. **Relevance Gate**
   - Check if assessment tests what matters
   - Check if assessment matches role
   - Check if assessment is calibrated to candidate
   - Ensure not over/under difficulty

4. **Equity Gate**
   - Check if similar candidates get similar assessments
   - Check if assessment disadvantages any group
   - Check if questions are clear (language, accessibility)
   - Ensure diverse representation in scenarios

---

## IMPLEMENTATION TIMELINE

### Week 5: Data Models & Agent Core

**Monday-Tuesday:**
- [ ] Create `assessment_designs` table (migration)
- [ ] Extend `assessments` model
- [ ] Create Pydantic schemas
- [ ] Database indexes

**Wednesday-Thursday:**
- [ ] Create `AssessmentDesignerAgent` class
- [ ] Implement `_analyze_candidate_profile()`
- [ ] Implement `_analyze_role_requirements()`
- [ ] Implement `_design_assessment_questions()`

**Friday:**
- [ ] Implement `_create_evaluation_rubric()`
- [ ] Implement `_generate_interview_guidance()`
- [ ] Unit tests (10+ tests)

### Week 6: Fairness & Service Layer

**Monday-Tuesday:**
- [ ] Implement `_run_fairness_check()` (4 gates)
- [ ] Create fairness reporting
- [ ] Fairness tests (5+ tests)

**Wednesday-Thursday:**
- [ ] Create `AssessmentDesignerService` class
- [ ] Service methods for all operations
- [ ] Integration with existing services

**Friday:**
- [ ] Integration tests (5+ tests)
- [ ] Error handling review

### Week 7: API & Worker Integration

**Monday-Tuesday:**
- [ ] Create `/api/v1/assessments/design.py`
- [ ] Implement all 5 endpoints
- [ ] Authentication & authorization

**Wednesday-Thursday:**
- [ ] Create Celery task: `design_assessment()`
- [ ] Worker integration
- [ ] Queue management

**Friday:**
- [ ] API tests (10+ tests)
- [ ] End-to-end tests

### Week 8: Frontend & Documentation

**Monday-Tuesday:**
- [ ] Assessment design UI (pending queue)
- [ ] Design detail view
- [ ] Fairness report display

**Wednesday-Thursday:**
- [ ] Approve/reject interface
- [ ] Changes request form
- [ ] Learning integration

**Friday:**
- [ ] Full documentation
- [ ] Performance validation
- [ ] Deployment checklist

---

## SUCCESS CRITERIA

### Performance Targets

| Metric | Target | Validation |
|--------|--------|-----------|
| Assessment design | 30 min (vs 4 hours) | Benchmark timing |
| Design latency | <5 sec | Response time test |
| Fairness check | <1 sec | Gate timing |
| Recruiter review | <10 min | Task timing |

### Quality Targets

| Metric | Target | How to Measure |
|--------|--------|---------------|
| Design appropriateness | >90% | Recruiter approval rate |
| Fairness validation | 100% | No rejected assessments |
| Bias detection | 100% | Catch flagged cases |
| Accessibility coverage | >95% | Universal design check |

### Recruiter Trust

| Metric | Target | How to Measure |
|--------|--------|---------------|
| Approval rate | >80% | Assessment designs approved |
| Changes rate | <15% | Requests for changes |
| Rejection rate | <5% | Manual redesigns needed |

---

## INTEGRATION POINTS

### With Phase 1:
- Input: `ScreeningResult` (candidate profile from screening)
- Input: `Position` (role requirements)
- Output: `Assessment` (assessment design ready to use)
- Link: `assessment_designs.screening_result_id`

### With Future Phases:
- Phase 3: Use designed assessment in evaluation
- Phase 4: Link assessment to matching
- Phase 5: Track assessment effectiveness

---

## RISK MITIGATION

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Assessment design too hard/easy | Medium | High | Recruiter validates difficulty |
| Biased questions generated | Low | Critical | 4 fairness gates + human review |
| Design not matched to role | Medium | High | Relevance gate validates |
| Accessibility barriers | Medium | Medium | Accessibility gate checks |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Recruiter overwhelmed by designs | Medium | Medium | Batch queue, sorting, filtering |
| Changes cycle delays | Medium | Medium | Quick redesign turnaround |
| Low approval rate | Low | Medium | Iterate based on feedback |

---

## DELIVERABLES (Week 8 End)

- ✅ 2 new model files (migrations + models)
- ✅ 1 schema file (5+ Pydantic models)
- ✅ 1 agent file (AssessmentDesignerAgent, 800+ lines)
- ✅ 1 service file (AssessmentDesignerService, 400+ lines)
- ✅ 1 API file (5 endpoints, 400+ lines)
- ✅ 1 worker file (Celery integration)
- ✅ 1 test file (25+ tests)
- ✅ Full documentation (design spec, API docs)

**Total**: ~3,000+ lines of new code
**Quality**: Enterprise-grade (100% type hints, error handling, tests)
**Tests**: 25+ unit tests (all passing)
**Conscience**: 4 fairness gates + recruiter approval

---

## NEXT PHASE (PHASE 3)

Phase 3 will:
- Run assessments (execute designed tests)
- Analyze results (score responses)
- Capture performance
- Link to learning

But Phase 2 alone is complete and valuable - recruiter can immediately start using agent-designed assessments.

---

**Status**: Ready to begin Week 5  
**Next Milestone**: Phase 2a (Data Models) completion by end of Week 5

