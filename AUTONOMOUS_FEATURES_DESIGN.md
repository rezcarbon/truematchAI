# Autonomous Features Design — Multi-Tier Roadmap

## Overview

This document outlines a comprehensive 3-month roadmap for autonomous features across the TrueMatch ATS platform. Each tier is designed for incremental shipping with measurable ROI, reducing recruiter toil while learning from every action.

**Vision**: Transform TrueMatch from a "match generator" into an "autonomous hiring partner" that learns from feedback and continuously improves decision quality.

---

## Tier 1: MVP+ — Quick Wins (1-2 weeks)

### Scope
Auto-decisions on high-confidence & low-confidence candidates, auto-notifications on status changes.

### 1.1 Auto-Approve High-Confidence Matches

**What gets automated:**
- CV assessments scoring > 0.90 (match_score) skip human review
- Automatically transition from `awaiting_review` → `processing` → assessment pipeline entry
- Only for positions with sufficient historical training data (>20 assessments)

**Design:**

```
CV Ingest → Scoring Engine
    ↓ (score > 0.90)
Check confidence threshold
    ↓ (yes)
Check position has training data
    ↓ (yes)
Auto-approve (assessment_auto_approved = true)
    ↓
Create Assessment record
    ↓
Emit event: "assessment_auto_initiated"
    ↓
Resume in candidate pipeline
```

**Data Flow:**
```
IngestQueueItem (status: awaiting_review)
  ├─ match_score: float (>0.90)
  ├─ assessment_id: UUID
  └─ auto_approved_by: "system_cv_agent"
  
Assessment (status: pending)
  ├─ source: "auto_approved"
  ├─ triggered_at: timestamp
  └─ auto_approved: true
```

**New Fields / Tables:**
- IngestQueueItem: add `auto_approved: bool`, `auto_approval_reason: str`
- Assessment: add `auto_triggered: bool`, `auto_approval_score: float`

**API / Endpoints Needed:**
- GET `/agents/auto-decisions/pending` — items queued for auto-approval (for audit)
- GET `/agents/auto-decisions/{id}/override` — override an auto-decision
- POST `/agents/config/auto-approval` — set confidence thresholds per position

**Database Schema Additions:**
```sql
ALTER TABLE ingest_queue
  ADD COLUMN auto_approved BOOLEAN DEFAULT false,
  ADD COLUMN auto_approval_reason VARCHAR(200),
  ADD COLUMN auto_approval_score FLOAT;

ALTER TABLE assessments
  ADD COLUMN auto_triggered BOOLEAN DEFAULT false,
  ADD COLUMN auto_trigger_score FLOAT;

CREATE TABLE auto_approval_config (
  id UUID PRIMARY KEY,
  position_id UUID NOT NULL UNIQUE,
  min_confidence_score FLOAT DEFAULT 0.90,
  enabled BOOLEAN DEFAULT true,
  min_training_samples INT DEFAULT 20,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**Success Metrics:**
- % of CVs approved automatically (target: 15-25% for mature positions)
- Time-to-interview reduction (target: 40% faster for auto-approved candidates)
- False positive rate (target: <5% — auto-approved candidates rejected in interviews)

**Effort Estimate:** 2-3 days
- 1 day: Schema + scoring integration
- 0.5 day: Endpoint + override logic
- 1 day: Testing + audit logs

---

### 1.2 Auto-Reject Low-Score Candidates

**What gets automated:**
- CV assessments scoring < 0.40 automatically rejected
- Prevents wasting recruiter time on poor matches
- Only for positions with historical data

**Design:**

```
CV Ingest → Scoring Engine
    ↓ (score < 0.40)
Check position has training data
    ↓ (yes)
Auto-reject + mark IngestQueueItem.status = rejected
    ↓
Emit event: "assessment_auto_rejected"
    ↓
Resume NOT added to pipeline
```

**Rejection Criteria:**
```python
AUTO_REJECT_THRESHOLD = 0.40
AUTO_REJECT_THRESHOLD_JUNIOR = 0.30  # More lenient for junior roles
AUTO_REJECT_REASON = "Automatically rejected: score below threshold"
```

**Data Flow:**
```
IngestQueueItem (status: awaiting_review)
  ├─ match_score: float (<0.40)
  └─ auto_rejected_by: "system_cv_agent"

# No Assessment record created
```

**New Fields / Tables:**
- IngestQueueItem: add `auto_rejected: bool`, `auto_rejection_reason: str`

**API / Endpoints Needed:**
- GET `/agents/auto-rejections` — list auto-rejected items (for audit/manual review)
- POST `/agents/auto-rejections/{id}/override` — override rejection, create assessment

**Database Schema Additions:**
```sql
ALTER TABLE ingest_queue
  ADD COLUMN auto_rejected BOOLEAN DEFAULT false,
  ADD COLUMN auto_rejection_reason VARCHAR(200),
  ADD COLUMN auto_rejection_score FLOAT;

CREATE TABLE auto_rejection_config (
  id UUID PRIMARY KEY,
  position_id UUID NOT NULL UNIQUE,
  max_rejection_score FLOAT DEFAULT 0.40,
  enabled BOOLEAN DEFAULT true,
  min_training_samples INT DEFAULT 20,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**Success Metrics:**
- % of CVs rejected automatically (target: 20-30%)
- Recruiter time saved per rejected candidate (estimated: 5-10 min)
- False negative rate (target: <2% — auto-rejected candidates who would have been good)

**Effort Estimate:** 1-2 days
- 0.5 day: Schema + logic
- 0.5 day: Endpoints
- 0.5 day: Testing + audit trail

---

### 1.3 Auto-Notify Candidates on Status Changes

**What gets automated:**
- Send email/SMS when candidate moves between pipeline stages
- Status changes: Screened → Interviewed → Offered → Rejected
- Template-based notifications with candidate name, position, next steps

**Design:**

```
Assessment Status Change
    ↓
Check candidate contact preference (email/sms/both)
    ↓
Select template based on status + position
    ↓
Render template with candidate data
    ↓
Send via email or SMS
    ↓
Log notification in audit table
```

**Data Flow:**
```
Assessment (status: interview_scheduled)
    ↓
CandidateNotification record created
  ├─ assessment_id: UUID
  ├─ recipient_email: str
  ├─ template_name: str (e.g., "interview_scheduled")
  ├─ status: "pending" | "sent" | "failed"
  └─ sent_at: timestamp

CandidatePreference (per Resume)
  ├─ allow_email_notifications: bool
  ├─ allow_sms_notifications: bool
  └─ preferred_contact_method: "email" | "sms" | "both"
```

**Notification Templates:**

```
--- interview_scheduled ---
Subject: Your {{position_title}} Interview

Hello {{candidate_name}},

We'd love to move forward with your application for {{position_title}} at {{company_name}}.

Your interview is scheduled for: {{interview_date}} at {{interview_time}}
Interview type: {{interview_type}} (video/phone/in-person)
Interviewer: {{interviewer_name}}

Next steps:
- Confirm your availability by clicking the link below
- Review the job description: {{jd_link}}
- Prepare 2-3 examples showcasing relevant skills

[CONFIRM] [RESCHEDULE] [DECLINE]

Questions? Reply to this email.

---

--- application_rejected ---
Subject: Your {{position_title}} Application

Hello {{candidate_name}},

Thank you for your interest in {{position_title}} at {{company_name}}.

We've reviewed your application and decided to move forward with other candidates at this time.

We were impressed by:
- {{highlight_1}}
- {{highlight_2}}

Consider applying for: {{similar_positions_link}}

Best of luck in your search!
```

**API / Endpoints Needed:**
- POST `/agents/notifications/configure` — set candidate preferences
- GET `/agents/notifications` — list sent/pending notifications
- POST `/agents/notifications/{id}/resend` — manually resend a notification

**Database Schema Additions:**
```sql
CREATE TABLE candidate_notification_preferences (
  id UUID PRIMARY KEY,
  resume_id UUID NOT NULL UNIQUE REFERENCES resumes(id),
  allow_email_notifications BOOLEAN DEFAULT true,
  allow_sms_notifications BOOLEAN DEFAULT false,
  preferred_contact_method VARCHAR(20) DEFAULT 'email',
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE candidate_notifications (
  id UUID PRIMARY KEY,
  assessment_id UUID NOT NULL REFERENCES assessments(id),
  resume_id UUID NOT NULL REFERENCES resumes(id),
  recipient_email VARCHAR(255),
  recipient_phone VARCHAR(20),
  template_name VARCHAR(100),
  template_version INT,
  rendered_body TEXT,
  status VARCHAR(20) DEFAULT 'pending',  -- pending, sent, failed, bounced
  sent_at TIMESTAMP,
  failed_reason TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE notification_templates (
  id UUID PRIMARY KEY,
  name VARCHAR(100) UNIQUE,  -- e.g., "interview_scheduled"
  subject_template TEXT,
  body_template TEXT,
  variables JSON,  -- ["candidate_name", "position_title", ...]
  enabled BOOLEAN DEFAULT true,
  version INT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**Worker Task:**
- `send_candidate_notification.delay(assessment_id, trigger_status)` — enqueue notification send

**Success Metrics:**
- Email open rate (target: >40%)
- Interview confirmation rate (target: >85%)
- Candidate satisfaction (survey: "Kept me informed")

**Effort Estimate:** 3-4 days
- 1 day: Template system + schema
- 1 day: Email/SMS integration (SendGrid or Twilio)
- 1 day: Worker task + error handling
- 0.5 day: Endpoints + preference UI

---

## Tier 2: Phase 2 — Learning Signals (2-3 weeks)

### Scope
Integrate recruiter feedback into the scoring model, validate prediction accuracy with hire outcomes, learn career path patterns.

### 2.1 Recruiter Feedback Integration

**What gets automated:**
- Collect structured feedback when recruiters approve/reject assessments
- Use feedback to fine-tune match scoring for future candidates
- Track which feedback improves hiring outcomes

**Design:**

```
Recruiter Action
    ├─ Approves assessment (implicit signal: "good fit")
    ├─ Rejects assessment (implicit signal: "poor fit")
    └─ Leaves notes (explicit feedback)
    
    ↓
Parse assessment data + feedback
    ↓
Extract features & feedback labels
    ↓
Log to FeedbackSignal table
    ↓
Batch feedback daily → Training job
    ↓
Fine-tune scoring model weights
```

**Feedback Signal Schema:**

```
FeedbackSignal
  ├─ assessment_id: UUID
  ├─ feedback_type: "approved" | "rejected" | "explicit_note"
  ├─ recruiter_id: UUID
  ├─ feedback_text: str (for explicit notes)
  ├─ feedback_category: str (skill_mismatch, culture_fit, experience_level, etc.)
  ├─ confidence: float (0-1, how confident is recruiter in this feedback)
  ├─ created_at: timestamp
  └─ used_for_training: bool (whether this signal improved model accuracy)
```

**Feedback Categories:**

```python
FEEDBACK_CATEGORIES = {
    "skill_match": "Technical skills don't match requirements",
    "experience_level": "Too junior/senior for the role",
    "culture_fit": "Personality/values misalignment",
    "communication": "Communication skills mismatch",
    "certifications": "Missing required certifications",
    "availability": "Can't start when needed",
    "salary_expectation": "Salary expectation mismatch",
    "location": "Location/relocation concerns",
    "positive_surprise": "Better than expected",
    "red_flag": "Background check, reference issues",
}
```

**API / Endpoints Needed:**
- POST `/agents/feedback` — submit feedback with structured category
- GET `/agents/feedback/summary` — metrics on which feedback categories improve hiring
- GET `/agents/model/performance` — accuracy of scoring model over time

**Database Schema Additions:**
```sql
CREATE TABLE feedback_signals (
  id UUID PRIMARY KEY,
  assessment_id UUID NOT NULL REFERENCES assessments(id),
  resume_id UUID NOT NULL REFERENCES resumes(id),
  position_id UUID NOT NULL REFERENCES positions(id),
  feedback_type VARCHAR(50),  -- approved, rejected, explicit_note
  recruiter_id UUID REFERENCES users(id),
  feedback_text TEXT,
  feedback_category VARCHAR(100),
  confidence FLOAT DEFAULT 1.0,
  was_hire_decision BOOLEAN,  -- later filled when outcome known
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE model_training_batches (
  id UUID PRIMARY KEY,
  agent_type VARCHAR(20),  -- "cv_scoring"
  training_data_count INT,
  training_date TIMESTAMP,
  model_version VARCHAR(50),
  accuracy FLOAT,
  precision FLOAT,
  recall FLOAT,
  notes TEXT,
  created_at TIMESTAMP
);
```

**Success Metrics:**
- % feedback signals collected (target: 70%+ of decisions logged)
- Model accuracy improvement from baseline (target: +5-10% after 2 weeks of feedback)
- Agreement rate between model and recruiter (target: >85%)

**Effort Estimate:** 5-7 days
- 1.5 days: Feedback schema + endpoints
- 2 days: Integration with approval/rejection flow
- 1.5 days: ML pipeline to retrain scorer
- 1 day: Testing + metrics dashboard

---

### 2.2 Post-Hire Performance Tracking

**What gets automated:**
- Track which candidates hired actually succeed in their roles
- Validate assessment accuracy against real job performance
- Identify patterns in successful hires vs. poor performers
- Use performance data to improve future assessments

**Design:**

```
Candidate Hired
    ↓
Collect baseline: assessment_score, feedback_category, role requirements
    ↓
--- 30 days later ---
Collect performance data:
  - Manager satisfaction rating (1-5)
  - 30-day checklist completion
  - Quality of work outputs
  - Team feedback
  ↓
60/90 days: Repeat performance check
    ↓
Correlate assessment_score → performance_rating
    ↓
Calculate "hire quality" = actual performance / predicted performance
    ↓
Update model feedback: "Assessment was accurate/inaccurate"
```

**Data Flow:**

```
Hire (when Assessment → Offer → Acceptance)
  ├─ assessment_id: UUID
  ├─ resume_id: UUID
  ├─ hire_date: timestamp
  └─ original_assessment_score: float

HirePerformance (30-day checkpoint)
  ├─ hire_id: UUID
  ├─ checkpoint_days: 30
  ├─ manager_satisfaction: int (1-5)
  ├─ checklist_completion: float (0-1)
  ├─ quality_rating: int (1-5)
  ├─ team_feedback_score: float (0-1)
  ├─ overall_performance: int (1-5)
  └─ created_at: timestamp

PerformanceValidation
  ├─ assessment_id: UUID
  ├─ predicted_success_probability: float
  ├─ actual_performance_rating: float
  ├─ validation_accuracy: bool (pred ≈ actual)
  └─ created_at: timestamp
```

**API / Endpoints Needed:**
- POST `/agents/hires` — mark candidate as hired
- POST `/agents/hires/{id}/performance-check` — submit 30/60/90 day feedback
- GET `/agents/hires/performance-summary` — accuracy of hiring predictions
- GET `/agents/assessment/{id}/hire-outcome` — what happened to this assessment

**Database Schema Additions:**
```sql
CREATE TABLE hires (
  id UUID PRIMARY KEY,
  assessment_id UUID NOT NULL UNIQUE REFERENCES assessments(id),
  resume_id UUID NOT NULL REFERENCES resumes(id),
  position_id UUID NOT NULL REFERENCES positions(id),
  offer_accepted_date DATE,
  hire_date DATE,
  original_assessment_score FLOAT,
  created_at TIMESTAMP
);

CREATE TABLE hire_performance_checks (
  id UUID PRIMARY KEY,
  hire_id UUID NOT NULL REFERENCES hires(id),
  checkpoint_days INT,  -- 30, 60, 90
  manager_satisfaction INT,  -- 1-5
  checklist_completion FLOAT,
  quality_rating INT,  -- 1-5
  team_feedback_score FLOAT,
  overall_performance INT,  -- 1-5
  notes TEXT,
  created_at TIMESTAMP
);

CREATE TABLE performance_validations (
  id UUID PRIMARY KEY,
  assessment_id UUID NOT NULL UNIQUE REFERENCES assessments(id),
  predicted_success_probability FLOAT,
  actual_performance_rating FLOAT,
  validation_accuracy_delta FLOAT,  -- |pred - actual|
  assessment_was_accurate BOOLEAN,
  created_at TIMESTAMP
);

CREATE INDEX idx_hires_hire_date ON hires(hire_date);
CREATE INDEX idx_perf_checks_checkpoint ON hire_performance_checks(checkpoint_days);
```

**Success Metrics:**
- % of hires tracked with performance data (target: 60%+)
- Correlation between assessment score and 30-day performance (target: >0.7)
- % of assessments validated as "accurate" (target: >80%)

**Effort Estimate:** 5-6 days
- 1 day: Hire tracking schema
- 1.5 days: Performance check UI + endpoints
- 1.5 days: Correlation analysis + reporting
- 1 day: Integration with model feedback loop

---

### 2.3 Career Path Learning

**What gets automated:**
- Identify patterns: Which assessments lead to promotions/success in IC vs. management roles?
- Learn candidate trajectories: entry-level → senior → staff → manager
- Use trajectory patterns to improve future assessments
- Recommend career progression opportunities to candidates

**Design:**

```
Track Assessment → Role → Performance → Promotion
    ↓
Aggregate patterns across all hires
    ↓
Build trajectory models:
  - IC skill trajectory (IC1 → IC2 → IC3 → IC4 → IC5)
  - Manager trajectory (IC → Manager → Senior Manager)
  ↓
Use patterns to:
  1. Predict if candidate is IC or manager-track
  2. Recommend training/development gaps
  3. Identify high-potential candidates for accelerated growth
```

**Career Path Data:**

```
CareerTrajectory
  ├─ resume_id: UUID
  ├─ trajectory_type: "ic" | "manager" | "specialist"
  ├─ level_progression: [
  │     {level: "IC2", date: "2021-01-01", company: "Company A"},
  │     {level: "IC3", date: "2022-06-15", company: "Company A"},
  │     {level: "IC4", date: "2024-01-01", company: "Company B"},
  │   ]
  ├─ time_in_role_avg_months: int
  ├─ promotion_frequency: "fast" | "normal" | "slow"
  ├─ skill_growth_areas: ["system_design", "mentoring", "project_leadership"]
  └─ predicted_next_level: str

TrajectoryPattern
  ├─ pattern_id: UUID
  ├─ skill_combination: ["java", "leadership", "communication"]
  ├─ successful_trajectory_type: "manager"
  ├─ success_rate: float (% who get promoted in this track)
  ├─ avg_time_to_promotion: int (months)
  ├─ market_demand: float (0-1)
  └─ created_at: timestamp
```

**API / Endpoints Needed:**
- GET `/agents/careers/trajectory/{resume_id}` — detected career trajectory
- GET `/agents/careers/patterns` — identify career path patterns from historical hires
- POST `/agents/careers/trajectory-predict` — predict candidate's likely trajectory

**Database Schema Additions:**
```sql
CREATE TABLE career_trajectories (
  id UUID PRIMARY KEY,
  resume_id UUID NOT NULL UNIQUE REFERENCES resumes(id),
  trajectory_type VARCHAR(50),  -- ic, manager, specialist
  level_progression JSONB,
  time_in_role_avg_months INT,
  promotion_frequency VARCHAR(20),
  skill_growth_areas JSONB,
  predicted_next_level VARCHAR(50),
  confidence FLOAT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE trajectory_patterns (
  id UUID PRIMARY KEY,
  skill_combination JSONB,
  trajectory_type VARCHAR(50),
  success_rate FLOAT,
  avg_time_to_promotion INT,
  market_demand FLOAT,
  total_samples INT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE career_recommendations (
  id UUID PRIMARY KEY,
  resume_id UUID NOT NULL REFERENCES resumes(id),
  recommendation_type VARCHAR(100),  -- "skill_gap", "growth_opportunity", "role_match"
  recommendation_text TEXT,
  confidence FLOAT,
  created_at TIMESTAMP
);
```

**Success Metrics:**
- Accuracy of trajectory detection (target: >75%)
- % of candidates matched to right track (IC vs. manager) based on assessment (target: >85%)
- Time-to-promotion correlation (trajectory pattern predictions vs. actual)

**Effort Estimate:** 4-5 days
- 1 day: Career trajectory extraction from CV
- 1.5 days: Pattern mining from historical hire data
- 1 day: Endpoints + recommendations
- 0.5 day: Testing

---

## Tier 3: Phase 3 — Integration Automation (3-4 weeks)

### Scope
Interview scheduling, offer generation, candidate preference learning.

### 3.1 Interview Scheduling Automation

**What gets automated:**
- Auto-schedule interviews with candidates based on availability
- Calendar API integration (Google Calendar, Outlook)
- Find optimal meeting time for candidate + interviewer(s)
- Send meeting invitations with video conferencing link
- Handle reschedules and cancellations

**Design:**

```
Assessment Approved for Interview
    ↓
Fetch candidate's available time slots (survey/calendar)
    ↓
Fetch interviewer's calendar
    ↓
Find mutually available slots
    ├─ Prefer morning (9-11am) or early afternoon (1-3pm)
    ├─ Avoid Friday if possible
    └─ Allow 1-hour buffer between interviews
    ↓
Rank slots by preference:
  1. Both parties available
  2. In timezone of candidate/company
  3. Within 2-5 business days
    ↓
Select top 3 options
    ↓
Send candidate link: "Pick your preferred time"
    ↓
Candidate selects → Create calendar events
    ↓
Send confirmation emails with Zoom link
```

**Data Flow:**

```
InterviewSchedule
  ├─ assessment_id: UUID
  ├─ interview_type: "phone" | "video" | "in_person"
  ├─ interviewer_ids: [UUID, ...]
  ├─ proposed_slots: [
  │     {start: datetime, end: datetime, timezone: "UTC"},
  │     ...
  │   ]
  ├─ candidate_selected_slot: datetime
  ├─ scheduled_at: datetime
  ├─ video_conference_link: str
  ├─ status: "draft" | "proposed" | "scheduled" | "completed"
  └─ created_at: timestamp

InterviewerAvailability
  ├─ user_id: UUID
  ├─ calendar_provider: "google" | "outlook"
  ├─ calendar_access_token: encrypted str
  ├─ last_synced: timestamp
  └─ busy_slots: JSONB (cached from calendar API)
```

**API / Endpoints Needed:**
- POST `/agents/interviews/schedule` — initiate interview scheduling
- POST `/agents/interviews/{id}/propose-slots` — send candidate 3 time options
- POST `/agents/interviews/{id}/confirm` — candidate selects time, create events
- POST `/agents/interviews/{id}/reschedule` — handle reschedule requests
- GET `/agents/interviews/upcoming` — recruiter view of upcoming interviews

**Integrations Needed:**
- Google Calendar API / Outlook Calendar API
- Zoom API (or Calendly embedding)
- Email service (SendGrid, etc.)

**Database Schema Additions:**
```sql
CREATE TABLE interview_schedules (
  id UUID PRIMARY KEY,
  assessment_id UUID NOT NULL UNIQUE REFERENCES assessments(id),
  interview_type VARCHAR(30),  -- phone, video, in_person
  interviewer_ids UUID[],
  proposed_slots JSONB,
  candidate_selected_slot TIMESTAMP WITH TIME ZONE,
  scheduled_at TIMESTAMP WITH TIME ZONE,
  video_conference_link VARCHAR(500),
  video_conference_provider VARCHAR(50),  -- zoom, google_meet, etc
  status VARCHAR(30) DEFAULT 'draft',
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE interviewer_availability (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL UNIQUE REFERENCES users(id),
  calendar_provider VARCHAR(50),  -- google, outlook
  calendar_provider_email VARCHAR(255),
  last_synced_at TIMESTAMP,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE calendar_access_tokens (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL UNIQUE REFERENCES users(id),
  provider VARCHAR(50),
  access_token TEXT ENCRYPTED,
  refresh_token TEXT ENCRYPTED,
  expires_at TIMESTAMP,
  scopes TEXT[],
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**Worker Tasks:**
- `sync_interviewer_calendars.delay()` — periodic task to refresh calendar data
- `propose_interview_slots.delay(assessment_id)` — send candidate time options
- `create_interview_events.delay(schedule_id)` — create calendar events on confirmation

**Success Metrics:**
- % of interviews auto-scheduled (target: 70%+)
- Time to schedule interview reduction (target: from 2 days → 4 hours)
- Candidate satisfaction with scheduling process (target: >85%)

**Effort Estimate:** 10-14 days
- 2 days: Calendar API integration (Google/Outlook)
- 2 days: Slot proposal + candidate selection UI
- 2 days: Zoom/video conference integration
- 2 days: Worker tasks + error handling
- 1.5 days: Reschedule logic
- 1.5 days: Testing + edge cases

---

### 3.2 Offer Generation Automation

**What gets automated:**
- Auto-generate offer letters based on position, candidate, market data
- Template system with salary benchmarking
- Allow manual adjustments before sending
- Track offer acceptance/rejection

**Design:**

```
Interview Process Complete → Hire Decision Made
    ↓
Trigger offer generation
    ↓
Fetch market data (salary, equity, benefits)
    ├─ Position level + location
    ├─ Candidate's expected salary (from profile)
    └─ Market benchmarks (Glassdoor, Levels.fyi)
    ↓
Retrieve offer template (position-specific)
    ├─ Base salary range
    ├─ Equity (if applicable)
    ├─ Benefits template
    └─ Start date
    ↓
Fill template with computed values
    ├─ Suggested salary: median(market, candidate expectation)
    ├─ Equity: standard for level
    ├─ Benefits: package for compensation band
    ↓
Generate PDF offer
    ↓
Send to recruiter for review & approval
    ├─ Can adjust salary (with approval alert if >10% from benchmark)
    ├─ Can customize terms
    ↓
Send to candidate with acceptance deadline
    ↓
Track acceptance/rejection
```

**Offer Data:**

```
OfferTemplate
  ├─ id: UUID
  ├─ position_id: UUID (optional, for position-specific templates)
  ├─ title: str (e.g., "Software Engineer L3")
  ├─ base_salary_range: {min: float, max: float}
  ├─ equity_vesting_schedule: str
  ├─ benefits_package: {health_insurance, pto, ...}
  ├─ start_date_offset_days: int (days from acceptance)
  ├─ template_version: int
  └─ created_at: timestamp

Offer
  ├─ id: UUID
  ├─ assessment_id: UUID
  ├─ resume_id: UUID
  ├─ offer_template_id: UUID
  ├─ salary_offered: float
  ├─ equity_offered: str (e.g., "0.02%")
  ├─ start_date: date
  ├─ benefits_customizations: JSON
  ├─ market_salary_benchmark: float
  ├─ candidate_expectation_salary: float
  ├─ status: "draft" | "pending_approval" | "sent" | "accepted" | "rejected"
  ├─ acceptance_deadline: date
  ├─ sent_at: timestamp
  ├─ accepted_at: timestamp
  └─ created_at: timestamp

SalaryBenchmark
  ├─ id: UUID
  ├─ title: str
  ├─ location: str
  ├─ level: int (1-10)
  ├─ median_salary: float
  ├─ p25_salary: float
  ├─ p75_salary: float
  ├─ data_source: str (e.g., "glassdoor", "levels.fyi")
  └─ updated_at: timestamp
```

**API / Endpoints Needed:**
- POST `/agents/offers/generate` — generate draft offer
- GET `/agents/offers/{id}` — view draft offer
- POST `/agents/offers/{id}/approve` — approve and send to candidate
- POST `/agents/offers/{id}/update` — adjust salary/terms
- GET `/agents/offers/{id}/market-check` — show market benchmarks
- POST `/agents/offers/{id}/send` — send offer to candidate
- POST `/agents/offers/acceptance/{offer_id}` — candidate accepts/rejects

**Integrations Needed:**
- Salary benchmark API (Levels.fyi, Glassdoor, Payscale)
- PDF generation (reportlab, weasyprint)
- E-signature service (DocuSign, Hellosign) — optional for MVP

**Database Schema Additions:**
```sql
CREATE TABLE offer_templates (
  id UUID PRIMARY KEY,
  position_id UUID REFERENCES positions(id),
  title VARCHAR(255),
  base_salary_min FLOAT,
  base_salary_max FLOAT,
  equity_vesting_schedule TEXT,
  benefits_package JSONB,
  start_date_offset_days INT DEFAULT 14,
  template_body TEXT,  -- Template string with {{placeholders}}
  version INT DEFAULT 1,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE offers (
  id UUID PRIMARY KEY,
  assessment_id UUID NOT NULL UNIQUE REFERENCES assessments(id),
  resume_id UUID NOT NULL REFERENCES resumes(id),
  offer_template_id UUID REFERENCES offer_templates(id),
  salary_offered FLOAT NOT NULL,
  equity_offered VARCHAR(50),
  start_date DATE,
  benefits_customizations JSONB,
  market_salary_benchmark FLOAT,
  candidate_expectation_salary FLOAT,
  status VARCHAR(30) DEFAULT 'draft',
  acceptance_deadline DATE,
  sent_at TIMESTAMP,
  accepted_at TIMESTAMP,
  rejected_at TIMESTAMP,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE salary_benchmarks (
  id UUID PRIMARY KEY,
  title VARCHAR(255),
  location VARCHAR(100),
  level INT,
  median_salary FLOAT,
  p25_salary FLOAT,
  p75_salary FLOAT,
  sample_count INT,
  data_source VARCHAR(100),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE UNIQUE INDEX idx_salary_benchmarks_title_location_level 
ON salary_benchmarks(title, location, level);
```

**Worker Tasks:**
- `sync_salary_benchmarks.delay()` — daily job to update market data
- `generate_offer.delay(assessment_id)` — create PDF offer

**Success Metrics:**
- % of offers generated automatically (target: 90%+)
- Time to deliver offer to candidate (target: <2 hours from approval)
- Offer acceptance rate (typical: 75-85%)
- Salary accuracy (within recruiter approval 95%+ of time)

**Effort Estimate:** 8-10 days
- 1.5 days: Salary benchmark API integration
- 2 days: Template system + offer generation
- 1.5 days: PDF generation + email
- 1 day: Market data validation + approval flow
- 1 day: Offer acceptance tracking
- 1 day: Testing

---

### 3.3 Candidate Preference Learning

**What gets automated:**
- Learn candidate preferences from CV/profile: salary, location, work style, industry
- Automatically surface matching opportunities from new job openings
- Recommend positions to candidates that fit their career goals
- Track preference accuracy against actual acceptances

**Design:**

```
CV Ingest → Parse:
  ├─ Salary: Extract from CV where stated (e.g., "Looking for $120-150k")
  ├─ Location: Extract "Open to relocation", preferred cities
  ├─ Work style: "Remote only", "Hybrid", "On-site"
  ├─ Industries: Tech, Finance, Healthcare (from job titles)
  ├─ Company size: "Prefer startups", "Want large stable company"
  └─ Career goals: "Seeking IC3 role", "Ready for management"
    ↓
Store in CandidateProfile
    ↓
New position opens
    ↓
Score all candidates:
  - Skill match (existing scoring)
  - Preference match (new)
    ├─ Salary range overlap
    ├─ Location match
    ├─ Industry fit
    └─ Work style compatibility
    ↓
Recommend top candidates to position
    ↓
Auto-message: "We found a role matching your preferences: {{position}}"
    ↓
Track if candidate:
  - Views the position
  - Applies
  - Accepts interview
  - Gets hired
    ↓
Use outcomes to refine preference model
```

**Candidate Preference Data:**

```
CandidatePreferences
  ├─ resume_id: UUID
  ├─ salary_min: float | null
  ├─ salary_max: float | null
  ├─ location_preferred: [str, ...]  -- ["SF", "NYC", "Austin"]
  ├─ location_willing_to_relocate: bool
  ├─ work_style: "remote" | "hybrid" | "on_site" | "any"
  ├─ industries_preferred: [str, ...]  -- ["tech", "finance"]
  ├─ company_size_preference: "startup" | "growth" | "enterprise" | "any"
  ├─ career_goals: str  -- "IC4 role", "Team lead", "Staff engineer"
  ├─ extracted_from: "cv_parsing" | "candidate_survey" | "application"
  ├─ confidence: float (0-1, how confident in this preference)
  └─ updated_at: timestamp

PositionMatch (for each position/candidate pair)
  ├─ position_id: UUID
  ├─ resume_id: UUID
  ├─ skill_match_score: float
  ├─ preference_match_score: float
  │   ├─ salary_match: float (0-1, overlap of ranges)
  │   ├─ location_match: float
  │   ├─ work_style_match: float
  │   └─ industry_match: float
  ├─ combined_match_score: float
  ├─ recommended: bool
  ├─ candidate_view_email_sent: bool
  └─ created_at: timestamp
```

**API / Endpoints Needed:**
- POST `/agents/preferences/update/{resume_id}` — extract and update preferences
- GET `/agents/preferences/{resume_id}` — view detected preferences
- GET `/agents/positions/{position_id}/top-candidates` — ranked by skill + preference match
- POST `/agents/recommendations/send` — send candidate "matching opportunity" emails
- GET `/agents/candidates/{resume_id}/recommendations` — positions recommended to candidate

**Database Schema Additions:**
```sql
CREATE TABLE candidate_preferences (
  id UUID PRIMARY KEY,
  resume_id UUID NOT NULL UNIQUE REFERENCES resumes(id),
  salary_min FLOAT,
  salary_max FLOAT,
  location_preferred VARCHAR(255)[],
  location_willing_to_relocate BOOLEAN DEFAULT false,
  work_style VARCHAR(50),  -- remote, hybrid, on_site, any
  industries_preferred VARCHAR(100)[],
  company_size_preference VARCHAR(50),
  career_goals TEXT,
  extracted_from VARCHAR(100),
  confidence FLOAT DEFAULT 0.5,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE position_matches (
  id UUID PRIMARY KEY,
  position_id UUID NOT NULL REFERENCES positions(id),
  resume_id UUID NOT NULL REFERENCES resumes(id),
  skill_match_score FLOAT,
  salary_match_score FLOAT,
  location_match_score FLOAT,
  work_style_match_score FLOAT,
  industry_match_score FLOAT,
  combined_match_score FLOAT,
  recommended BOOLEAN DEFAULT false,
  candidate_recommendation_sent_at TIMESTAMP,
  candidate_clicked_at TIMESTAMP,
  candidate_applied_at TIMESTAMP,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  UNIQUE(position_id, resume_id)
);

CREATE INDEX idx_position_matches_combined_score 
ON position_matches(position_id, combined_match_score DESC);
```

**Worker Tasks:**
- `extract_candidate_preferences.delay(resume_id)` — CV parsing → preference extraction
- `recommend_matching_positions.delay(resume_id)` — find + send position recommendations

**Success Metrics:**
- Preference extraction accuracy (target: >80% for salary/location)
- % of recommended positions candidate engages with (target: 15-25% click rate)
- Hiring accuracy when preference + skill match is high (target: >85%)

**Effort Estimate:** 6-8 days
- 1.5 days: Preference extraction from CV (NLP)
- 1.5 days: Preference + skill match scoring
- 1 day: Endpoints + recommendation logic
- 1 day: Auto-messaging to candidates
- 1 day: Outcome tracking + accuracy metrics
- 0.5 day: Testing

---

## Tier 4: Future — Advanced Intelligence (4-6 weeks, post-launch)

These features require more data and are planned for later releases but worth documenting.

### 4.1 Diversity & Bias Detection

**Design:**
- Analyze assessments for demographic bias in scoring
- Alert on patterns (e.g., "Non-native speakers scored 10% lower on average")
- Suggest corrections to scoring models
- Track diversity metrics per position/team

**Effort:** 4-5 weeks
**Success Metric:** Reduce scoring bias by 50%

### 4.2 Market Intelligence

**Design:**
- Aggregated salary trends (anonymized candidate expectations vs. offers)
- Skill demand trends (which skills becoming scarce?)
- Competitor hiring patterns (what companies are hiring similar roles)
- Churn prediction (which hires are likely to leave in 1 year)

**Effort:** 3-4 weeks
**Success Metric:** Salary competitive positioning (<5% deviation from market)

### 4.3 Team Compatibility Scoring

**Design:**
- Learn which candidate profiles integrate best with existing teams
- Factor in personality/communication style, experience overlap, skill gaps
- Predict on-team performance vs. interview performance

**Effort:** 4-5 weeks
**Success Metric:** Improved team cohesion & retention metrics

---

## Implementation Roadmap & Timeline

```
Week 1-2  (Tier 1.1 + 1.2)
├─ Auto-approve/reject logic
├─ Decision audit trail
└─ Override mechanism

Week 2-3  (Tier 1.3)
├─ Notification templates
├─ Email/SMS integration
└─ Preference collection

Week 3-4  (Tier 2.1)
├─ Feedback signal schema
├─ Feedback endpoints
└─ Model retraining job

Week 4-5  (Tier 2.2)
├─ Hire tracking
├─ Performance checks
└─ Accuracy validation

Week 5-6  (Tier 2.3)
├─ Career path extraction
├─ Pattern mining
└─ Trajectory predictions

Week 6-10 (Tier 3.1)
├─ Calendar API integration
├─ Interview scheduling UI
└─ Zoom integration

Week 10-13 (Tier 3.2)
├─ Offer template system
├─ Salary benchmarking API
└─ Offer generation + signing

Week 13-16 (Tier 3.3)
├─ Preference extraction
├─ Position recommendation
└─ Engagement tracking
```

---

## Success Metrics Dashboard

### By Tier

**Tier 1 (MVP+):**
- Time saved per candidate: 15-20 min
- Manual review burden reduction: 25-30%
- Conversion rate lift: +5-10%

**Tier 2 (Learning):**
- Model accuracy improvement: +5-15%
- Hiring success rate: +10-15%
- Time-to-hire reduction: 20-30%

**Tier 3 (Integration):**
- End-to-end time reduction: 40-50%
- Interview confirmation rate: >85%
- Offer-to-acceptance rate: 75-85%
- Offer turnaround: <2 hours

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Model overfits to company hiring bias | Regular audit + feedback diversity tracking |
| Automation eliminates human judgment too aggressively | Override mechanism + confidence thresholds |
| Candidate experience suffers (too robotic) | Personalization in notifications; human touch on offers |
| Privacy concerns with preference tracking | Transparent opt-in; encrypted storage; GDPR compliance |
| Integration complexity (calendar, signature APIs) | Phase 3 is last; solid foundation in Tier 1-2 |

---

## Conclusion

This roadmap prioritizes:
1. **Quick wins** (Tier 1): Deployable in 2 weeks, immediate ROI
2. **Learning foundations** (Tier 2): Build feedback loops for continuous improvement
3. **Full automation** (Tier 3): End-to-end hiring acceleration
4. **Advanced intelligence** (Tier 4): Long-term competitive advantage

Each tier is independently valuable and can be shipped separately.
