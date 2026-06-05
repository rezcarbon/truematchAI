# TrueMatch — UI/UX Screen Specification
## Web Platform + iOS Mobile
**Version 1.0 — May 2026 | MustafarAI / Digital Court — CONFIDENTIAL**

> Synthesised from: (1) live TrueMatch API + feature inventory, (2) 2024–2026 research across Greenhouse, Ashby, Lever, HireVue, Eightfold, X0PA, LinkedIn Recruiter, and modern queue dashboards. Every screen maps to a real, working backend endpoint.

---

## Design System Principles

1. **Three signals are first-class.** The Traditional ATS / Semantic / Capability score trio — each with delta chip — appears above the fold on every candidate view. Never collapsed by default.
2. **Agents are ambient, not hidden.** Agent status (CV Ingestion, JD Analysis) sits in a persistent strip on the command centre. Recruiters always know what's processing.
3. **Red = I must act. Amber = waiting. Green = done.** Consistent semantic colour across pipeline cards, governance badges, agent health, and SLA indicators.
4. **AI recommends. Human decides.** Every AI output carries an evidence link. Every human decision is explicitly recorded. Counter-recommendations are surfaced, never auto-applied.
5. **Mobile is for review and command, not authoring.** iOS screens are optimised for scorecards, approvals, agent control, and quick actions — not for building requisitions or analytics.
6. **Candidate transparency is mandatory.** Every candidate-facing screen shows the AI disclosure notice and data-rights controls.

---

## Web Platform — Complete Screen List

### 1. Authentication & Onboarding

| ID | Screen | Route | Connects to |
|---|---|---|---|
| W-AUTH-01 | Login | `/login` | Email/password + Singpass OAuth |
| W-AUTH-02 | Sign Up (candidate) | `/signup` | `POST /auth/signup` |
| W-AUTH-03 | Singpass callback | `/singpass-callback` | `POST /auth/singpass/callback` |

---

### 2. Recruiter — Command Centre Dashboard `R-01`

**Route:** `/recruiter/dashboard`  
**API:** `GET /agents/queue`, `GET /assessments`, `GET /positions`, `WS /api/v1/agents/ws`

The strategic home screen. Everything a recruiter needs the moment they log in.

**Layout: 4-zone grid (top strip → left → centre → right)**

```
┌─────────────────────────────────────────────────────────┐
│  DAILY TASK STRIP (horizontal — action-required items)   │
├──────────┬──────────────────────────┬────────────────────┤
│  ACTIVE  │    CANDIDATE WORK QUEUE  │  AGENT STATUS      │
│  JOBS    │    (today's review queue)│  + ACTIVITY FEED   │
│  (left)  │    (centre, largest)     │  (right panel)     │
└──────────┴──────────────────────────┴────────────────────┘
```

**Zone 1 — Daily Task Strip (horizontal scrollable chips):**
- `N scorecards due today` (red chip)
- `N interviews in the next 2 hours` (amber chip)
- `N approvals pending` (amber chip)
- `N offers awaiting response` (blue chip)
- `N CVs awaiting your review` (from `ingest_queue` where status=`awaiting_review`)

**Zone 2 — Active Jobs List (left panel):**
- Requisition title, department, days open
- Health dot: 🟢 on-track / 🟡 at-risk / 🔴 stalled / ⏸️ paused
- SLA indicator (days remaining before breach)
- Mini 3-stage funnel (applied → interviewed → offered) with counts
- `+ New Position` CTA

**Zone 3 — Candidate Work Queue (centre — main work surface):**
- Cards for candidates needing action today (sorted: red → amber → green)
- Card shows: name, role applied, current stage, days in stage, **3-signal score trio** (Traditional | Semantic | Capability each with Δ chip), action needed label
- Quick actions on card: `Advance` / `Schedule Interview` / `View Full Profile`
- Empty state: "All caught up — no candidates need action today."

**Zone 4 — Agent Status + Activity Feed (right panel):**

*Agent Status Strip (top of panel):*
```
CV Ingestion Agent    ● 3 processing  ✓ 47 done  ✗ 0 errors
JD Analysis Agent     ● 1 processing  ✓ 12 done  ✗ 0 errors
                      [View Queue →]          [+ Drop CV]  [+ JD Draft]
```

*Real-time Activity Feed (WebSocket `WS /api/v1/agents/ws`):*
- `14:32  CV ingested — Maya Okonkwo → matched to 'AI Leader' (Semantic 72%)`
- `14:31  JD draft analysed — 'Ecosystem Director' — quality 75/100 — awaiting review`
- `14:28  Assessment complete — Mohamed Reezan — δ+65 → counter-rec generated`
- `14:25  You advanced Sarah Chen → Interview stage`

---

### 3. Recruiter — Jobs & Positions

| ID | Screen | Route | Key APIs |
|---|---|---|---|
| W-R-02 | All Jobs / Requisition List | `/recruiter/positions` | `GET /positions` |
| W-R-03 | New Position (create + AI JD) | `/recruiter/positions/new` | `POST /positions`, `POST /agents/jd/draft` |
| W-R-04 | Approval Queue | `/recruiter/positions/approvals` | `GET /agents/queue?status=awaiting_review&type=jd_draft` |

**W-R-02 — All Jobs:**  
Sortable table: title, department, location, recruiter, # applicants, pipeline health mini-chart, JD quality score badge (from `position.jd_quality_score`), days open, status.
Filter: department / status / recruiter / SLA breach risk.
Bulk: pause, close, reassign, export.

**W-R-03 — New Position:**  
3-step wizard:
1. *Job details* — title, dept, location, type, salary band
2. *Job Description* — rich text editor + **"Analyse my JD" button** (calls `POST /agents/jd/draft`) → shows quality score, flagged issues + AI Fix: for each in a panel beside the editor as the recruiter types. The editor shows inline highlights (red underline = issue, hover for fix).
3. *Pipeline setup* — stages, interview plan, scorecard templates, approval chain

On create: `POST /positions` → JD interrogation runs synchronously → quality panel updates.

---

### 4. Recruiter — Candidate Pipeline

| ID | Screen | Route | Key APIs |
|---|---|---|---|
| W-R-05 | Pipeline (Kanban) | `/recruiter/positions/{id}` | `GET /positions/{id}/candidates`, `GET /positions/{id}/jd-versions` |
| W-R-06 | Pipeline (List) | `/recruiter/positions/{id}?view=list` | Same |
| W-R-07 | Candidate Search | `/recruiter/candidates` | `GET /assessments`, `GET /profile` |
| W-R-08 | Candidate Comparison | `/recruiter/compare` | `GET /assessments/{id}/comparison` |
| W-R-09 | Candidate Profile | `/recruiter/candidates/{id}` | `GET /assessments/{id}`, `/comparison`, `/narrative`, `/trajectory`, `/governance` |

**W-R-05 — Kanban Pipeline:**

```
[Applied (12)]        [Screening (8)]      [Interview (4)]      [Offer (1)]
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Maya Okonkwo │     │ Sarah Chen   │     │ John Tan     │     │ Priya Nair   │
│ 🔴 Scorecard │     │ 🟡 Awaiting  │     │ ✅ On track  │     │ Offer sent   │
│ ATS 19       │     │ ATS 42       │     │ ATS 13       │     │ ATS 72       │
│ Sem 72  ↑+5  │     │ Sem 68       │     │ Sem 72  ↑+12 │     │ Sem 83       │
│ Cap 78  ↑+3  │     │ Cap 81       │     │ Cap 78       │     │ Cap 87       │
│ ⚡ counter-rec│     │ 4d in stage  │     │ 2d in stage  │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

- Card shows: name, priority colour (red/amber/green), **3-signal score trio** (each with delta since last assessment), stage badge, days-in-stage counter, counter-rec badge (⚡) if triggered, source badge, automation trigger indicator (⚙️ on stages with rules)
- Drag-and-drop between stages (records decision in audit trail)
- Click card → W-R-09
- Above board: **JD Quality banner** — "Quality 75/100 · 3 issues · [View suggestions →]"

**W-R-06 — List Pipeline:**  
Columns: name, stage, days in stage, ATS score (with Δ), Semantic score (with Δ), Capability score (with Δ), match type badge, last activity, actions.
Sortable by any score. Multi-select → bulk advance / reject / message / export.

**W-R-08 — Candidate Comparison:**  
Side-by-side for 2–4 candidates (max per Greenhouse/Ashby research).
Per candidate column:
- 3-signal scores with delta chips
- Radar chart (domain_depth / problem_solving / collaboration / delivery / adaptability — all from `capability_components`)
- Credential substitutions (from `substitutions` — HIGH/MED/WEAK per proxy)
- Verified evidence count (from `verified_evidence`)
- Governance status (coherence ✅ / fidelity ✅ / bias flags)
- Match type label

Overlay radar charts for direct comparison (toggle).

**W-R-09 — Candidate Profile (Recruiter) — The most important screen:**

```
HEADER: [Name]  [Role applied]  [Stage Badge 🔴]  [Source]  [Applied: 3d ago]
─────────────────────────────────────────────────────────────────────────────
SIGNAL PROGRESSION (full width, above fold):
[Traditional ATS ██░░░░░ 19]  →  [Semantic ████████ 72]  →  [Capability ████████ 78]
     "Keyword literal"                "Concept match"          "Demonstrated ability"
     Δ+0 (baseline)                  Δ+12 ↑                   Δ+3 ↑
                    DELTA: +59   ⚡ COUNTER-RECOMMENDATION GENERATED
                    match_type: surfaced_strong_match

CREDENTIAL SUBSTITUTIONS:
  MSc Computer Science → technical depth    ████ HIGH   [evidence →]
  8+ yrs FAANG          → scale experience  ███░ MED    [evidence →]

VERIFIED EVIDENCE: ✅ ORCID (8 publications)  ✅ mustafarai.com  ⚠️ 6 patents (manual IPOS)

─────────────────────────────────────────────────────────────────────────────
TABS: [Assessment] [JD Comparison] [Scorecards] [Timeline] [Notes] [Audit]
─────────────────────────────────────────────────────────────────────────────

[Assessment tab]:
  Capability Narrative (3-5 paragraphs)
  Radar chart (5 components with evidence)
  Gap Analysis (what the role needs that isn't evidenced)
  Trajectory (direction: ascending, velocity: high, invisible credentials)

[JD Comparison tab]:
  Side-by-side: JD requirements vs. candidate evidence
  Per-requirement: matched / substituted / gap
  JD Quality score + issues + AI Fix: per issue

[Governance tab]:
  ✅ Coherence  ✅ Consistency  ✅ Fidelity  ⚠️ 1 bias flag
  Counter-recommendation full text
  Audit trail: pipeline.provenance → intake → enrichment → reasoning → governance

─────────────────────────────────────────────────────────────────────────────
ACTIONS (sticky bottom bar):
[Advance to Interview →]  [Hold]  [Reject]  [Schedule Interview]  [Message]
```

---

### 5. Recruiter — JD Quality & Evolution

| ID | Screen | Route | Key APIs |
|---|---|---|---|
| W-R-10 | JD Quality Dashboard | `/recruiter/jd-quality` | `GET /positions`, `GET /positions/{id}` |
| W-R-11 | JD Draft Review | `/recruiter/positions/{id}/jd-review` | `GET /agents/jd/{id}/suggestions`, `GET /positions/{id}/jd-versions`, `GET /positions/{id}/evolution` |

**W-R-10 — JD Quality Dashboard:**  
For each active position: quality score gauge (0–100), issue count, issue type breakdown (proxy / impossible / exclusionary / ambiguous). Per-issue: type badge, detail text, **Fix: AI recommendation in full**. Link to JD Draft Review.

**W-R-11 — JD Draft Review:**  
Split-pane view:
- Left: Original JD with inline highlights (each issue underlined in severity colour)
- Right: AI-improved draft (editable rich text)
- Between: issue list with severity and Fix: for each, linked to highlight on left
- Below: JD version history timeline (from `jd_versions`) — versions as dots on a line, click any dot → see that version + quality score
- Bottom: quality trend sparkline (quality across versions → shows improvement or degradation)
- Actions: `Accept improved draft` / `Edit improved draft` / `Keep original`

---

### 6. Recruiter — Decisions & Offers

| ID | Screen | Route | Key APIs |
|---|---|---|---|
| W-R-12 | Decision Tracking | `/recruiter/decisions` | `GET /decisions?position={id}` |
| W-R-13 | Interview Scheduling | `/recruiter/schedule/{id}` | `PATCH /decisions/{id}` |

**W-R-12 — Decision Tracking:**  
Audit table of all decisions: candidate, position, decision outcome, AI recommendation, whether AI was followed, override reasoning (if any), recruiter, timestamp. Filter by position / outcome / AI-followed.
This is the compliance export screen — download as CSV/PDF for audit.

---

### 7. Recruiter — Communications

| ID | Screen | Route | Key APIs |
|---|---|---|---|
| W-R-13 | Inbox | `/recruiter/inbox` | (future: messaging API) |

Threaded messaging unified with candidate context panel (stage, scores, next steps).

---

### 8. Agent Monitoring & Control

| ID | Screen | Route | Key APIs |
|---|---|---|---|
| W-AG-01 | Agent Command Centre | `/recruiter/agents` | `GET /agents/queue`, `WS /api/v1/agents/ws` |
| W-AG-02 | Ingest Queue | `/recruiter/agents/queue` | `GET /agents/queue`, `POST /agents/queue/{id}/approve|reject|reassign` |
| W-AG-03 | JD Draft Submissions | `/recruiter/agents/jd-drafts` | `GET /agents/queue?type=jd_draft` |

**W-AG-01 — Agent Command Centre:**

```
┌─────────────────────────────────────────────────────────────────┐
│ SYSTEM HEALTH STRIP                                              │
│  Processing rate: 23 jobs/hr  │  Queue depth: 14  │  Errors: 0  │
│  Latency: 2.1s avg            │  Dead-letter: 0   │  ● Healthy  │
├───────────────────────┬─────────────────────────────────────────┤
│ CV INGESTION AGENT    │  REAL-TIME EVENT LOG                    │
│ ● Running             │  14:32  CV: Maya Okonkwo → matched AI  │
│ Processing: 3 jobs    │  14:31  JD: Ecosystem Director – done  │
│ Done today: 47        │  14:28  Assessment: M.Reezan complete  │
│ Errors: 0             │  14:25  Beat: poll-cv-folder (0.3s)    │
│ Last beat: 8s ago     │  14:25  Beat: poll-jd-folder (0.0s)    │
│ [View jobs →]         │  ...                                    │
├───────────────────────┤  [Retry failed]  [Pause agent]          │
│ JD ANALYSIS AGENT     │                                         │
│ ● Idle                │  QUEUE SUMMARY                          │
│ Done today: 12        │  Pending:         3                     │
│ Errors: 0             │  Processing:      1                     │
│ [View jobs →]         │  Awaiting review: 2                     │
├───────────────────────┤  Completed today: 58                    │
│ [+ Drop CV file]      │  Failed:          0                     │
│ [+ Submit JD draft]   │  [View full queue →]                    │
└───────────────────────┴─────────────────────────────────────────┘
```

**W-AG-02 — Ingest Queue:**  
Table: item type (CV/JD), status badge (colour-coded), source (email/folder/api), sender, auto-matched position, created, retry count, last error.
Status filters: all / awaiting_review / processing / completed / failed.

Per-item actions:
- CV `awaiting_review`: **[Approve → pipeline]** / **[Reassign position]** / **[Reject]** (with notes)
- JD `awaiting_review`: **[View suggestions →]** (opens W-R-11) / **[Reject]**

---

### 9. Analytics Dashboards

| ID | Screen | Route | Key APIs |
|---|---|---|---|
| W-A-01 | Executive KPI Dashboard | `/admin/analytics` | `GET /admin/analytics/outcomes` |
| W-A-02 | Pipeline Funnel Analytics | `/admin/analytics/funnel` | `GET /admin/analytics/outcomes` |
| W-A-03 | Score Distribution & AI Analytics | `/admin/analytics/scores` | `GET /assessments` |
| W-A-04 | Diversity & Equity Dashboard | `/admin/analytics/bias` | `GET /admin/analytics/bias` |
| W-A-05 | Source Attribution | `/admin/analytics/sources` | `GET /admin/analytics/outcomes` |
| W-A-06 | JD Quality Trends | `/admin/analytics/jd-quality` | `GET /admin/analytics/jd-quality` |

**W-A-01 — Executive KPI Dashboard:**

```
┌────────┐  ┌────────┐  ┌──────────┐  ┌────────────┐  ┌──────────────┐
│  Open  │  │ Hires  │  │  Offer   │  │ Avg Time   │  │  Counter-rec │
│  Roles │  │ vs Plan│  │Acceptance│  │  to Hire   │  │  Accept Rate │
│   12   │  │  8/10  │  │  84%↑    │  │  28d↓      │  │   73%        │
└────────┘  └────────┘  └──────────┘  └────────────┘  └──────────────┘

[30d trend lines for each KPI]

SIGNAL EFFECTIVENESS:
Traditional ATS avg: 38  │  Semantic avg: 68  │  Capability avg: 77
Avg delta: +39           │  Counter-recs fired: 23 (61%)  │  Accepted: 17 (74%)
"74% of counter-recommendations accepted by recruiters — validating AI reasoning"
```

**W-A-03 — Score Distribution & AI Analytics:**
- 3-panel histogram: distribution of traditional / semantic / capability across all candidates
- Delta distribution (what percentage of candidates have delta > governance threshold)
- Match-type breakdown: `hidden_gem` / `surfaced_strong_match` / `keyword_aligned` counts with acceptance rates
- Correlation scatter: semantic vs. capability (do they agree?)
- Governance: coherence/consistency/fidelity pass rates, `flagged_for_review` count
- Bias flag frequency by type

**W-A-04 — Diversity Dashboard:**
- Pass-through rate by demographic group at each stage
- Adverse impact ratio per stage (flag when < 0.8)
- Counter-recommendation demographics: are we surfacing diverse candidates the keyword ATS missed?
- Substitution acceptance: HIGH-rated substitutions accepted vs. rejected

---

### 10. Compliance & Audit

| ID | Screen | Route | Key APIs |
|---|---|---|---|
| W-AD-01 | Compliance Dashboard | `/admin/compliance` | `GET /admin/compliance/report` |
| W-AD-02 | Audit Trail Viewer | `/admin/audit` | `GET /admin/audit?from=&to=` |
| W-AD-03 | Bias Monitoring | `/admin/analytics/bias` | `GET /admin/analytics/bias` |
| W-AD-04 | Governance Config | `/admin/configuration` | `GET/PATCH /admin/governance/config` |

**W-AD-01 — Compliance Dashboard:**
- Governance pass rates (coherence / consistency / fidelity / bias) as KPI tiles
- `flagged_for_review` rate and resolution times
- NYC LL144: bias audit summary (assessments with flags, demographic pass-through rates, remediation log)
- PDPA/GDPR: erasure requests received/fulfilled, export requests, data retention status
- Regulatory export buttons: EU AI Act report / NYC LL144 annual audit / PDPA compliance

**W-AD-02 — Audit Trail:**
- Timestamped log of every AI action: `pipeline.provenance`, `intake.completed`, `enrichment.completed`, `reasoning.completed`, `governance.completed`, `classification.completed`, `pipeline.completed`
- Model version + prompt registry version displayed per assessment
- Human override log: when recruiters diverged from AI recommendation + reason
- Filter by assessment ID, date range, event type
- Export as PDF/CSV for regulator submission

---

### 11. Admin Screens

| ID | Screen | Route |
|---|---|---|
| W-AD-05 | User Management | `/admin/users` |
| W-AD-06 | Integration Hub | `/admin/integrations` |
| W-AD-07 | Assessment Configuration | `/admin/configuration` |

**W-AD-07 — Assessment Configuration:**
- Signal weight sliders (Traditional / Semantic / Capability — sum to 100%)
- Counter-rec delta threshold (governance-controlled, named constant only — value not shown in UI)
- `INGEST_REQUIRE_APPROVAL` toggle (require human approval before autonomous CV processing runs pipeline)
- `ENRICHMENT_ENABLED` toggle
- Prompt registry version display (read-only: `2026.05.31c`)
- Governance gate status: `COHERENCE_THRESHOLD`, `CONSISTENCY_BOUND`, `FIDELITY_THRESHOLD`, `COUNTER_REC_DELTA` — operational / placeholder status (values never shown, only operational status)

---

### 12. Candidate Portal Screens

| ID | Screen | Route | Key APIs |
|---|---|---|---|
| W-C-01 | Candidate Dashboard | `/candidate/dashboard` | `GET /assessments` |
| W-C-02 | Upload Resume & Assess | `/candidate/upload` | `POST /files/resume`, `POST /assessments/self` |
| W-C-03 | My Assessment | `/candidate/assessment/{id}` | `GET /assessments/{id}`, `/comparison`, `/narrative`, `/trajectory`, `/governance` |
| W-C-04 | Job Browse | `/candidate/jobs` | `GET /positions` |
| W-C-05 | My Profile | `/candidate/profile` | `GET/PATCH /profile/me` |
| W-C-06 | History | `/candidate/history` | `GET /assessments` |
| W-C-07 | Data Rights | `/candidate/privacy` | `POST /profile/export`, `DELETE /profile` |

**W-C-01 — Candidate Dashboard:**
- Most recent assessment score trio (Traditional / Semantic / Capability with deltas)
- "Your profile at a glance" — top capabilities, trajectory direction, invisible credentials count
- Active applications + status
- Recommended jobs (positions where semantic score would be high)
- "Improve your profile" suggestions (gap analysis from latest assessment)

**W-C-03 — My Assessment:**  
*Important: candidate sees their OWN assessment — transparency-first design.*
- **Score trio** (same as recruiter view — candidates can see all three scores)
- "What a traditional system sees vs. what TrueMatch sees" — plain-language framing of the delta
- Capability narrative (what you CAN do, evidenced)
- Gap analysis (what the role needs that isn't evidenced yet — actionable)
- Trajectory (ascending / stable / declining — career arc summary)
- Governance status: "This assessment passed all quality checks." / "This assessment is under review."
- **AI disclosure notice**: "Anthropic Claude (version X) was used to assess your resume. Your data is not used for AI training." [Data rights →]
- Improvement suggestions: specific, actionable ("Quantify the impact of the HLX ecosystem project — outcomes rather than activities would strengthen your delivery score")

**W-C-07 — Data Rights:**
- PDPA/GDPR rights centre
- `Download all my data` → calls `POST /profile/export` → JSON download
- `Request account deletion` → confirmation modal → `DELETE /profile` → cascade + tombstone
- `Consent history` — what consents were given and when
- `AI transparency` — which model, which prompt registry version, what was assessed

---

## iOS App — Complete Screen List

### Navigation Structure

```
Bottom Tab Bar:
  🏠 Home (Agent Dashboard + Today's tasks)
  📋 Pipeline (Job list → Kanban)
  👤 Candidates (Search + Profile)
  💬 Messages
  📊 Analytics (read-only snapshot)
```

---

### Recruiter iOS Screens

| ID | Screen | Connects to |
|---|---|---|
| iOS-R-01 | Home / Agent Command Centre | WebSocket + `/agents/queue` + `/assessments` |
| iOS-R-02 | Job List | `GET /positions` |
| iOS-R-03 | Pipeline (horizontal Kanban) | `GET /positions/{id}/candidates` |
| iOS-R-04 | Candidate Profile (mobile) | `GET /assessments/{id}`, `/comparison`, `/narrative` |
| iOS-R-05 | Scorecard Submission | `POST /decisions` |
| iOS-R-06 | Candidate Search | `GET /assessments` |
| iOS-R-07 | Candidate Comparison (2-up) | `GET /assessments/{id}/comparison` |
| iOS-R-08 | Approval Queue | `GET /agents/queue?status=awaiting_review` |
| iOS-R-09 | Analytics Snapshot | `GET /admin/analytics/outcomes` |

**iOS-R-01 — Home / Agent Command Centre (THE most-used iOS screen):**

```
┌─────────────────────────────────┐
│ 🟢 Agents active · 47 processed │  ← persistent status bar
│ CV Agent ● 3 running  ⚡ 0 err  │
│ JD Agent  ● 1 running  ✓ 12    │
├─────────────────────────────────┤
│ TODAY'S TASKS                   │
│ ┌─────────────────────────────┐ │
│ │ 🔴 3 scorecards due         │ │  ← swipe to complete
│ │ 🟡 2 approvals pending      │ │
│ │ 📋 5 CVs awaiting review    │ │
│ └─────────────────────────────┘ │
├─────────────────────────────────┤
│ LIVE EVENTS (WebSocket feed)    │
│ 14:32 Maya O. → AI Leader match │
│ 14:28 Assessment: M.Reezan δ+65 │
│ 14:25 JD 'Eco Director' analysed│
├─────────────────────────────────┤
│ QUICK ACTIONS                   │
│ [⚡ Trigger Assessment]          │
│ [📄 Submit JD Draft]            │
│ [📥 View Ingest Queue]          │
└─────────────────────────────────┘
```

**iOS-R-03 — Pipeline (horizontal scroll Kanban):**
- One stage visible at a time; adjacent stages partially visible (peek pattern)
- Swipe-to-action: swipe right on card → advance; swipe left → defer/schedule
- Score trio on each card (compact: `ATS 19 · Sem 72 · Cap 78 · ⚡`)
- Haptic feedback on stage advance
- Pull-to-refresh

**iOS-R-04 — Candidate Profile (stacked card layout):**

Card 1 (header): name, role, stage, applied date  
Card 2 (SCORES — most important): 3-signal score trio with delta chips + match type badge  
Card 3 (SUBSTITUTIONS): proxy → alternate evidence rows with HIGH/MED/WEAK badges  
Card 4 (NARRATIVE): capability summary (tap to expand)  
Card 5 (GOVERNANCE): badge strip (✅ coherence, ✅ fidelity, ⚠️ 1 bias flag)  
Card 6 (COUNTER-REC): if triggered, full text  

Sticky bottom action bar: `Advance` | `Schedule` | `Reject` | `Message`

**iOS-R-05 — Scorecard (swipe-per-competency):**
- One competency per screen (domain_depth → problem_solving → collaboration → delivery → adaptability)
- Large segmented control for 1–5 rating
- Evidence text field below rating
- Bottom progress: ●●○○○ competency 2 of 5
- AI transcript summary (collapsible card above rating)
- Final screen: overall recommendation (Strong Yes/Yes/No/Strong No) + mandatory comment for No

---

### iOS Agent Screens (built and shipped)

| ID | Screen | Connects to |
|---|---|---|
| iOS-AG-01 | Agent Dashboard | `GET /agents/queue`, WS |
| iOS-AG-02 | Ingest Queue | `GET /agents/queue`, approve/reject/reassign |
| iOS-AG-03 | JD Draft Review | `GET /agents/jd/{id}/suggestions` |

*(These three screens are already built — `AgentDashboardView`, `IngestQueueView`, `JDDraftReviewView`)*

---

### Candidate iOS Screens

| ID | Screen | Connects to |
|---|---|---|
| iOS-C-01 | Application Status | `GET /assessments` |
| iOS-C-02 | Upload Resume | `POST /files/resume` → `POST /assessments/self` |
| iOS-C-03 | My Assessment | `GET /assessments/{id}`, `/comparison`, `/narrative` |
| iOS-C-04 | Job Browse & Apply | `GET /positions` |
| iOS-C-05 | Profile | `GET/PATCH /profile/me` |
| iOS-C-06 | Data Rights | `POST /profile/export`, `DELETE /profile` |

**iOS-C-03 — My Assessment (candidate):**
- Score trio (same as recruiter — full transparency)
- Plain-language delta explanation: "Traditional systems see 19% match. TrueMatch sees 72% concept match and 78% demonstrated capability."
- Capability narrative
- Improvement suggestions (actionable, specific)
- AI disclosure chip: "Assessed by Anthropic Claude · v2026.05.31c · [Data rights →]"

---

## Priority Build Order

### Phase 1 — Launch Critical (web-first)
1. `W-R-01` Recruiter Command Centre Dashboard ← the product's first impression
2. `W-R-05` Pipeline Kanban ← core daily workflow
3. `W-R-09` Candidate Profile ← most feature-rich, most impactful
4. `W-C-03` Candidate Assessment ← transparency + NPS driver
5. `W-AG-01` Agent Command Centre ← differentiator, real-time agents

### Phase 2 — Core Functionality
6. `W-R-02/03` Job List + Creation with JD AI analysis
7. `W-R-08` Candidate Comparison
8. `W-R-11` JD Draft Review
9. `W-AD-01/02` Compliance Dashboard + Audit Trail
10. `W-A-01` Executive Analytics Dashboard

### Phase 3 — Full Analytics + Candidate Portal
11. `W-A-02–06` Analytics suite
12. `W-C-01–07` Full candidate portal
13. `W-AG-02` Ingest Queue (web)
14. `W-AD-03–07` Full admin suite

### iOS
15. `iOS-R-01` Home / Agent Command Centre ← most used
16. `iOS-R-03/04` Pipeline + Candidate Profile ← daily workflow
17. `iOS-R-05` Scorecard submission
18. `iOS-C-01–03` Candidate status + assessment ← candidate-facing
19. *(iOS-AG-01/02/03 already built)*

---

## Key Design Decisions for TrueMatch-Specific UI

### The Delta Bar (TrueMatch signature component)
Every candidate card and profile shows this horizontal 3-signal bar as the **primary** information element — not buried in a tab:

```
[ATS 19 ░░░░░░░░░░░] → [Sem 72 ████████░░] → [Cap 78 ████████░░]
         ↑ Keyword filter saw this        ↑ Full capability
                    Δ+59  ⚡ counter-rec
```

### Governance Badges (always visible)
Unlike competitor platforms, governance is a **visible trust signal** — not hidden in audit:
- `✅ Governed · All gates passed` green chip
- `⚠️ Under review · Fidelity gate` amber chip — routes to human review explanation
- `🔴 Ungoverned · Config not provisioned` red chip (dev/mock mode)

### Counter-Recommendation Card
When fired (delta > threshold), this card appears as a **highlighted, prominent block** — not a subtle footnote:
```
┌─ ⚡ COUNTER-RECOMMENDATION ─────────────────────────────────────────┐
│  This candidate does NOT match the JD as written. However,          │
│  [specific evidence] suggests they may exceed what the role          │
│  actually needs because [specific reasoning].                        │
│                                                                      │
│  VERIFY: [3 specific claims to check]                               │
│  [Advance for review →]                           [Dismiss]         │
└──────────────────────────────────────────────────────────────────────┘
```

### Match Type Badge
Displayed prominently on every candidate card in pipeline and profile:
- `🟣 hidden_gem` — keyword AND concept missed them; only capability found them
- `🟢 surfaced_strong_match` — all three signals agree
- `⬜ keyword_aligned` — no counter-rec needed; conventional screen found them

---

*This specification is derived from the live TrueMatch codebase (May 2026) and informed by 2024–2026 UI/UX research across Greenhouse (March 2026 pipeline update), Ashby, Lever, HireVue, Eightfold AI, X0PA, LinkedIn Recruiter iOS, and modern queue dashboard patterns.*

*© 2026 Mohamed Reezan Mohd Fadzil / MustafarAI / Digital Court. All Rights Reserved.*
