# TrueMatch Autonomous Features: 16-Week Roadmap

**Vision:** Build a fully autonomous recruitment platform that operates 24/7 with human oversight only for edge cases.

**Timeline:** 16 weeks to implement Tiers 1-3 (Quick wins → Full automation)

---

## Tier 1: MVP+ Quick Wins (Weeks 1-2)

### 1.1 Auto-Approve High-Confidence Matches

**What:** System automatically approves queue items with match confidence >0.90.

**When to Trigger:**
```
IF assessment_score >= 0.90
  AND governance_gates_passed == true
  AND job_open == true
THEN auto_approve()
```

**What Gets Sent:**
- Candidate notification: "Your assessment for [Position] has been auto-approved"
- Assessment enqueued for review
- Email notification to recruiter

**Data Flow:**
```
Queue Item (awaiting_review)
    ↓
Check confidence & gates
    ↓
Score >= 0.90? YES → Auto-approve
              NO  → Keep in queue
    ↓
Send notifications
Send assessment to pipeline
Log event
```

**Implementation:**
- Add `auto_approve_threshold` setting (default: 0.90)
- Modify approve_item() endpoint logic
- Create auto-approval decision event
- Add logging for audit trail

**Files to Modify:**
- `backend/app/api/v1/agents.py` - Add auto-approval logic
- `backend/app/config.py` - Add threshold setting
- `backend/app/workers/tasks.py` - Auto-approval task

**Database:**
- New field: `auto_approved: bool` on IngestQueueItem
- Track auto-approval timestamp

**Success Metrics:**
- 15-25% of assessments auto-approved (high-confidence matches)
- <5 minute delay from assessment complete to auto-approval
- Zero mis-approvals (false positives tracked)

**Estimated Effort:** 2-3 days

---

### 1.2 Auto-Reject Low-Score Candidates

**What:** System automatically rejects queue items with score <0.40.

**When to Trigger:**
```
IF assessment_score < 0.40
  AND assessment_complete == true
THEN auto_reject()
```

**What Gets Sent:**
- Candidate notification: "Your assessment for [Position] was not a strong match"
- Rejection logged
- Email to candidate with encouragement to apply for other roles

**Data Flow:**
```
Assessment Completes
    ↓
Score < 0.40? YES → Auto-reject
            NO  → Check approval threshold
    ↓
Send rejection email
Log audit event
Add to "candidates to reach out" (future opportunities)
```

**Implementation:**
- Add `auto_reject_threshold` setting (default: 0.40)
- Modify assessment completion logic
- Create auto-rejection event
- Send recruiter-configured rejection email

**Files to Modify:**
- `backend/app/workers/tasks.py` - Auto-rejection logic
- `backend/app/config.py` - Add threshold setting
- `backend/app/workers/notification_service.py` - Rejection emails

**Database:**
- New field: `auto_rejected: bool` on Assessment

**Success Metrics:**
- 20-30% of assessments auto-rejected (clear mismatches)
- 100% accuracy (no valid candidates rejected)
- Rejection emails sent within 1 minute

**Estimated Effort:** 1-2 days

**Note:** Track false rejects for continuous tuning

---

### 1.3 Auto-Notify Candidates on Status Changes

**What:** System sends automated notifications whenever assessment status changes.

**Status Changes:**
```
submission_received
  ↓
assessment_started (email: "We're reviewing your application")
  ↓
assessment_complete (email depends on outcome)
  ↓
approved (email: "Approved for next stage")
├─ rejected (email: "Not a match, but we've saved your profile")
└─ review (email: "Your application is under review")
```

**Notification Templates (Recruiter-Configurable):**

```
Status: assessment_started
Email Subject: "We're reviewing your application for {{position_title}}"
Email Body: "Hi {{candidate_name}}, we received your application and our AI is currently reviewing it. We'll update you within 24 hours."

Status: assessment_approved
Email Subject: "Great news about {{position_title}}"
Email Body: "Hi {{candidate_name}}, congratulations! Your assessment was approved. A recruiter will be in touch within 24 hours to discuss next steps."

Status: assessment_rejected
Email Subject: "Thank you for applying to {{position_title}}"
Email Body: "Hi {{candidate_name}}, while you're not a match for this specific role, we'd love to keep your profile in our system for future opportunities."
```

**Implementation:**
- Create NotificationTemplate model
- Add status_change event emitter to assessment pipeline
- Send notifications async via SNS/SES

**Files to Create:**
- `backend/app/models/notification_template.py`
- `backend/app/workers/candidate_notification.py`

**Database:**
- `notification_templates` table
- Track notification_sent timestamps on Assessment/IngestQueueItem

**Success Metrics:**
- 40% faster candidate communication (automtion vs manual)
- 100% delivery rate
- <1 second latency to send
- Personalization with candidate/position data

**Estimated Effort:** 3-4 days

**Total Tier 1: 6-9 days**

---

## Tier 2: Learning Signals (Weeks 2-3)

### 2.1 Recruiter Feedback Integration

**What:** Recruiters provide structured feedback on assessments → system learns.

**Feedback Types:**
```
1. "Good match" - candidate performs well
2. "Bad match" - candidate underperforms
3. "Different role" - candidate good for other position
4. "Contacted externally" - recruited elsewhere
5. "Accepted offer" - hired!
```

**Data Flow:**
```
Assessment Complete
    ↓
Recruiter Views Assessment
    ↓
Recruiter Clicks "Feedback"
    ↓
Selects Feedback Type + Notes
    ↓
Feedback Stored
    ↓
Learning System Processes
    ├─ Update capability weights
    ├─ Update domain mappings
    └─ Trigger recalibration if enough signals
```

**Implementation:**
- New API endpoint: `POST /assessments/{id}/feedback`
- Feedback form in recruiter dashboard
- Learning loop integration (exists from Phase D)

**Database:**
```sql
CREATE TABLE assessment_feedback (
  id UUID PRIMARY KEY,
  assessment_id UUID REFERENCES assessments(id),
  feedback_type VARCHAR(50),  -- good_match, bad_match, etc.
  notes TEXT,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP,
  resolved_by_learning BOOLEAN DEFAULT false
);
```

**Learning Signals:**
```
IF feedback_type == "good_match"
  THEN increase_capability_weights_from_assessment()
  
IF feedback_type == "bad_match"
  THEN flag_assessment_for_root_cause_analysis()
  
IF feedback_type == "different_role"
  THEN learn_position_substitution(from_pos, to_pos)
  
IF feedback_type == "hired"
  THEN mark_assessment_as_validated()
  THEN track_hire_outcome_for_accuracy_measurement()
```

**Dashboard Integration:**
```
Assessment Detail View
├─ Current Score: 0.87
├─ Governance Gates: ✓ All Passed
├─ Recruiter Feedback: [No feedback yet]
└─ [Add Feedback] button
    └─ Modal:
       ├─ Feedback Type Dropdown
       ├─ Notes Text Area
       └─ [Submit] button
```

**Success Metrics:**
- 80%+ of assessments have feedback within 2 weeks
- 5-10% accuracy improvement from learning
- Feedback → weight update within 1 hour
- Recruiter satisfaction with feedback UI

**Estimated Effort:** 5-7 days

---

### 2.2 Post-Hire Performance Tracking

**What:** Track performance of hired candidates to validate assessment accuracy.

**Data Collection:**
```
Hired Candidate
  ├─ Probation Period (90 days)
  │   ├─ Manager check-in: Week 2, 4, 8, 12
  │   └─ Rate: Exceeding / Meeting / Below expectations
  └─ After Probation
      ├─ Annual Review Rating
      ├─ Promotion Eligibility (6mo, 1yr, 2yr)
      └─ Retention (still employed?)
```

**Validation Logic:**
```
Hired assessment_score: 0.87
 ↓
6 months later: Manager rating = "Exceeding"
 ↓
Validation: CORRECT HIRE ✓
 ↓
Learn: Increase "Team Leadership" weight (candidate strong there)
 ↓
Update learning signals
```

**Implementation:**
- Integration with HR system (or manual entry UI)
- Map hired candidates to original assessment
- Periodic validation job

**Database:**
```sql
CREATE TABLE hire_validation (
  id UUID PRIMARY KEY,
  assessment_id UUID REFERENCES assessments(id),
  hire_date DATE,
  probation_rating VARCHAR(50),  -- exceeding, meeting, below
  six_month_rating VARCHAR(50),
  one_year_rating VARCHAR(50),
  still_employed BOOLEAN,
  promotion_eligible BOOLEAN,
  created_at TIMESTAMP
);
```

**Success Metrics:**
- 90%+ accuracy of predicted vs actual performance
- 85%+ retention rate (staying employed)
- 20%+ promotion rate (good hires grow)
- Feedback loop closes assessment quality loop

**Estimated Effort:** 5-6 days

---

### 2.3 Career Path Learning

**What:** Learn which candidates succeed in IC vs Manager tracks.

**Pattern Discovery:**
```
Candidate A:
  - Assessment: High "Team Leadership"
  - Hired as: Senior Engineer (IC)
  - 6mo: Manager rating: "Exceeding"
  - 1yr: Promoted to: Engineering Manager
  - Learning: "Team Leadership" + "People Skills" → good for Manager track

Candidate B:
  - Assessment: High "Technical Depth"
  - Hired as: Senior Engineer (IC)
  - 6mo: Manager rating: "Exceeding"
  - 2yr: Still IC, declined management offer
  - Learning: "Technical Depth" → strong IC indicator
```

**Implementation:**
- Track career path (IC → Senior IC → Staff Engineer vs IC → Manager → Director)
- Correlate with assessment results
- Auto-categorize candidates for future positions

**Success Metrics:**
- 75%+ accuracy identifying IC vs Manager track potential
- Manager candidates stay in roles longer when correctly matched
- IC specialists perform better when not pushed to management

**Estimated Effort:** 4-5 days

**Total Tier 2: 14-18 days**

---

## Tier 3: Integration Automation (Weeks 3-4)

### 3.1 Interview Scheduling

**What:** Automatically schedule interviews for approved candidates.

**Integration:**
```
Candidate Approved
  ├─ Candidate Status: "Ready for Interview"
  ├─ Calendar Integrations:
  │   ├─ Google Calendar (recruiter's)
  │   ├─ Zoom (auto-create meeting)
  │   └─ Candidate calendar (optional)
  └─ Scheduling Logic:
      ├─ Find 3 available slots (next 3 days)
      ├─ Send candidate link: "Pick your interview time"
      ├─ Candidate picks slot
      └─ Confirmation emails + Zoom links sent automatically
```

**Implementation:**
- Google Calendar API integration
- Zoom API for auto-meeting creation
- Candidate self-scheduling (no recruiter needed)

**Database:**
```sql
CREATE TABLE interview_slots (
  id UUID PRIMARY KEY,
  assessment_id UUID REFERENCES assessments(id),
  recruiter_id UUID REFERENCES users(id),
  proposed_times JSON,  -- [{start, end, recruiter_tz}, ...]
  candidate_selected_time TIMESTAMP,
  zoom_link VARCHAR(500),
  calendar_event_id VARCHAR(500),  -- Google Calendar ID
  created_at TIMESTAMP
);
```

**Success Metrics:**
- 50% faster interviews scheduled
- <1 minute from approval to candidate receiving interview offer
- 80%+ candidate acceptance rate (easy self-scheduling)
- 100% zoom link generation

**Estimated Effort:** 10-14 days (API integration complexity)

---

### 3.2 Offer Generation

**What:** Automatically generate personalized offer letters from templates.

**Components:**
```
Offer Template
  ├─ Role: [Senior Backend Engineer]
  ├─ Salary: BASE_SALARY[role][level][location]
  ├─ Equity: EQUITY_POOL[company_stage][role]
  ├─ Benefits: [standard benefits list]
  ├─ Start Date: 2 weeks from accepted
  └─ Personalization:
      ├─ Candidate name, background
      ├─ Role-specific responsibilities
      └─ Market-appropriate compensation

Offer Generation Flow:
Assessment Approved
  ├─ Extract: Role, Seniority, Location
  ├─ Calculate: Salary band (market data + company scale)
  ├─ Generate: Offer letter (PDF)
  ├─ Get Approval: Manager/Finance review
  └─ Send: to Candidate + DocuSign for signature
```

**Implementation:**
- Template system with variable substitution
- Salary benchmarking API integration
- DocuSign integration for e-signatures

**Database:**
```sql
CREATE TABLE offer_generated (
  id UUID PRIMARY KEY,
  assessment_id UUID REFERENCES assessments(id),
  offer_pdf_url VARCHAR(500),
  base_salary NUMERIC(10,2),
  equity_percent NUMERIC(10,4),
  start_date DATE,
  accepted BOOLEAN,
  docusign_status VARCHAR(50),  -- sent, opened, signed, declined
  created_at TIMESTAMP
);
```

**Success Metrics:**
- <2 hour time from approval to offer in candidate's inbox
- 90%+ acceptance rate
- 100% offer accuracy (no manual review needed)
- Salary consistency across candidates

**Estimated Effort:** 8-10 days (PDF generation + DocuSign)

---

### 3.3 Candidate Preference Learning

**What:** Learn candidate preferences for future matching.

**Signals Collected:**
```
During Application:
  ├─ Location preferences
  ├─ Salary expectations
  ├─ Remote/hybrid preference
  └─ Domain preferences (AI/ML, Web, Mobile, etc)

During Assessment:
  ├─ Questions answered about preferences
  └─ Optional feedback form

Post-Hire:
  ├─ Salary accepted: Actual compensation preferences
  ├─ Location: Where they actually chose
  └─ Team: Which team/domain they joined
```

**Learning Logic:**
```
IF candidate prefers "AI/ML" in application
  AND hired into "AI/ML" team
  AND happy (high performance rating)
THEN increase match score for AI/ML roles

IF candidate expected 150-200K
  AND offered 180K + accepted
  AND happy after 1 year
THEN learn: This candidate is good match for 150-200K roles
```

**Implementation:**
- Preferences form in application
- Explicit question set during assessment
- Correlation analysis post-hire

**Success Metrics:**
- 75%+ of candidates match preferred domain
- 80%+ satisfied with compensation (no regrets)
- 20%+ improvement in candidate acceptance rates
- Better domain-specific candidate sourcing

**Estimated Effort:** 6-8 days

**Total Tier 3: 24-32 days**

---

## Tier 4: Future (Advanced Intelligence)

### 4.1 Diversity & Inclusion Scoring

Detect and correct bias in matching:
- Background diversity scoring
- Underrepresented group optimization
- Fair representation metrics

**Estimated Effort:** 10-14 days

### 4.2 Team Compatibility Scoring

Analyze team composition for optimal fit:
- Personality compatibility
- Skill diversity requirements
- Team growth needs

**Estimated Effort:** 12-16 days

### 4.3 Market Intelligence

Benchmarking & competitive intelligence:
- Salary benchmarking
- Location cost-of-living adjustment
- Skill demand in market

**Estimated Effort:** 8-10 days

### 4.4 Retention Prediction

Predictive models for candidate longevity:
- Early churn indicators
- Retention optimization
- Career growth prediction

**Estimated Effort:** 10-14 days

---

## Summary: Timeline & Impact

### 16-Week Roadmap

```
Week 1-2:  Tier 1 (MVP+ Quick Wins)         → 15-25% auto-decisions
Week 3:    Tier 2 (Learning Signals)        → +5-15% accuracy
Week 4:    Tier 3 (Integration Automation)  → 40-50% time reduction
Weeks 5+:  Tier 4 (Advanced Intelligence)   → Competitive advantage
```

### Expected Business Impact

**Tier 1 Impact (Weeks 1-2):**
- 25-30% of decisions automated
- 15-20 minutes saved per candidate (manual approval)
- Faster candidate experience (instant approvals)

**Tier 2 Impact (Weeks 3):**
- +5-15% improvement in hiring accuracy
- 20-30% reduction in time-to-hire
- Better data for continuous learning

**Tier 3 Impact (Weeks 4):**
- 40-50% end-to-end time reduction (submit → offer → signed)
- 80%+ offer acceptance rate
- Interviews self-scheduled (no recruiter overhead)

**Cumulative Impact:**
- 60-70% autonomous operation (limited human intervention)
- 3-5x faster hiring (weeks → days)
- 85%+ hiring accuracy (validated by post-hire performance)
- 24/7 availability (no human bottlenecks)

---

## Architecture: Integration Points

### Queue System → Auto-Decisions

```
IngestQueue (await_review)
    ↓ [approve endpoint]
    ├─ Check: score >= 0.90? → Auto-approve
    ├─ Check: score < 0.40?  → Auto-reject
    └─ Otherwise: Queue for recruiter review
        ↓
Assessment enqueued
```

### Learning Loops

```
Assessment Complete
    ↓
Recruiter provides feedback
    ↓
Learning System processes
    ├─ Update capability weights
    ├─ Learn preference patterns
    └─ Schedule recalibration
        ↓
Next assessment benefits from learning
```

### Interview Scheduling

```
Candidate Approved
    ├─ Generate interview slots
    ├─ Send self-service link
    ├─ Candidate books
    └─ Calendar + Zoom auto-created
```

### Offer Generation

```
Candidate Approved
    ├─ Extract role + level
    ├─ Calculate salary
    ├─ Generate PDF
    ├─ Get approval
    └─ Send DocuSign link
```

---

## Dependencies & Blockers

**Tier 1:**
- ✅ No external dependencies
- ✅ Can start immediately

**Tier 2:**
- ✅ Requires Tier 1 (auto-decisions for feedback context)
- ⚠️ Requires HR data access (hire tracking)

**Tier 3:**
- ✅ Requires Tier 2 (performance validation)
- ❌ Requires external API integrations (Google Calendar, Zoom, DocuSign)
- ❌ Requires legal review (offer letter templates)

**Tier 4:**
- ✅ Requires all prior tiers (data source)
- ❌ Requires ML/data science team
- ❌ Requires legal/compliance review (DEI scoring)

---

## Success Criteria by Tier

| Metric | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|--------|--------|--------|--------|--------|
| Auto-Decision Rate | 25-30% | 30-40% | 50-60% | 70-80% |
| Hiring Accuracy | Base | +5-15% | +10-20% | +15-25% |
| Time-to-Hire (days) | 14 | 10 | 3-5 | 2-3 |
| Candidate Experience | Good | Better | Excellent | Outstanding |
| Recruiter Efficiency | Baseline | +20% | +60% | +80% |

---

## Recommendation

**Start with Tier 1 this week** (6-9 days)
- Quick wins with immediate ROI
- Foundation for future tiers
- Low risk, high visibility

**Follow with Tier 2** (next 2 weeks)
- Learning loops pay compounding dividend
- Validates assessment accuracy
- Enables Tier 3

**Plan Tier 3** (weeks 3-4)
- Schedule external API integrations NOW
- Get legal review on offer templates
- Expect 2-3 week implementation

**Defer Tier 4** (month 2)
- Requires robust data from Tiers 1-3
- May need ML/DS resources
- Competitive advantage vs necessity

---

**Total 16-Week Investment:** ~80-100 person-days  
**ROI:** 3-5x faster hiring, 60-70% autonomous operation, 85%+ accuracy
