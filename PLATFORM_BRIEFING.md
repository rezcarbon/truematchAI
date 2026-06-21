# TrueMatch — Definitive Platform Briefing

**An AI-native, capability-first hiring platform**
_Last updated: 2026-06-14 · Backend + Web + iOS monorepo_

---

## 1. Executive summary

TrueMatch is an AI-embodied Applicant Tracking System (ATS) that **reasons about a candidate's demonstrated capability** rather than keyword-matching a résumé to a job description. Where a traditional ATS scores text overlap, TrueMatch produces a second, independent **capability score** — and surfaces the *delta* between them, with a counter-recommendation when a candidate is a "hidden gem" (high capability, low keyword match) or a "confirmed match."

The platform is **AI-native end to end**: a conversational agent drives the product through structured tool-use; an autonomous loop ingests and triages candidates; assessments run through a multi-signal reasoning pipeline; and a closed learning loop feeds hiring decisions back into future scoring. Every AI surface degrades gracefully to deterministic behavior when no model key is configured.

It ships as three coordinated layers:

| Layer | Stack | Scale |
|---|---|---|
| **Backend** | FastAPI · SQLAlchemy async · Celery · PostgreSQL 16 · Redis · Anthropic Claude | ~42k LOC · 185 routes · 34 models · 19 engines · 24 services · 54 worker/task modules |
| **Web** | Next.js 14 (App Router) · TypeScript · Tailwind · NextAuth · Recharts | ~25k LOC · 58 page routes · 70 components |
| **iOS** | SwiftUI · XcodeGen · async/await networking · Keychain | ~9k LOC · 78 files · 12 feature areas |

**Current production-readiness:** all three layers pass their CI gates — backend (ruff + `alembic check` + 317 tests), web (`next lint` + `next build`), iOS (`xcodebuild`). Migrations are clean on both the live DB and a fresh `alembic upgrade head`.

---

## 2. The thesis: capability-first hiring

A résumé is a lossy proxy for capability. Keyword ATS systems compound that loss — they reward candidates who write résumés the way the JD was written, and silently reject those who demonstrate the same capability through different evidence (open-source work, alternate credentials, adjacent experience).

TrueMatch scores every candidate on **three independent signals** and reasons over the gap between them:

1. **Traditional (keyword) score** — deterministic TF-weighted term overlap of the raw résumé vs. the raw JD, with IDF weighting learned from the accumulating JD corpus. Reproducible byte-for-byte.
2. **Semantic score** — deterministic concept overlap via static embeddings (model2vec, CPU, no GPU/torch) over raw text spans. Catches capability expressed in different words.
3. **Capability score** — LLM reasoning over the parsed résumé, verified external evidence, and credential substitutions, grounded by learned context from past decisions for the role.

The **score delta** (capability − traditional) and a governance-gated **counter-recommendation** are the platform's signature output: they tell a recruiter *"this candidate is stronger than their keywords suggest, and here's the evidence."*

---

## 3. System architecture

```
                         ┌──────────────────────────────────────────────┐
   Web (Next.js)  ─┐     │                  FastAPI (api/v1)            │
   iOS (SwiftUI)  ─┼────▶│  185 routes · JWT auth · role-gated deps      │
   (BFF / direct)  ┘     │  uniform ProblemDetail error contract         │
                         └───────────────┬──────────────────────────────┘
                                         │
              ┌──────────────────────────┼───────────────────────────────┐
              ▼                          ▼                               ▼
      ┌───────────────┐         ┌─────────────────┐            ┌──────────────────┐
      │ Engines (19)  │         │  Services (24)  │            │  Celery workers   │
      │ reasoning,    │         │ action handlers │            │  (54 modules)     │
      │ intake,       │◀───────▶│ decision-learn  │◀──────────▶│  assessment       │
      │ semantic,     │         │ role-taxonomy   │            │  pipeline, ingest │
      │ governance,   │         │ calendar, ATS   │            │  alerts, plans,   │
      │ enrichment …  │         │ connectors …    │            │  memory, taxonomy │
      └───────┬───────┘         └────────┬────────┘            └─────────┬────────┘
              │                          │                               │
              ▼                          ▼                               ▼
      ┌──────────────┐          ┌─────────────────┐            ┌──────────────────┐
      │ Anthropic    │          │  PostgreSQL 16  │            │      Redis        │
      │ Claude API   │          │ (encrypted PII) │            │ broker + cache    │
      └──────────────┘          └─────────────────┘            └──────────────────┘
```

**Request paths.** The web app authenticates through NextAuth and reaches the backend either via a server-side BFF proxy (`/api/proxy/[...path]`, which injects the user's token) or — for streaming chat — directly. iOS uses a thin async/await REST layer with JWT bearer tokens. Both clients are role-aware: the same backend selects the right agent and gates tools by role.

**Sync vs. async.** Request handlers are async (asyncpg). Long-running work — the assessment pipeline, CV/JD analysis, ingestion, durable agent plans, memory merges, taxonomy rebuilds — runs in Celery (threads pool). Workers use a synchronous engine derived from the async URL; the few that must drive async engines (durable plans, ATS sync) open a fresh async session via `asyncio.run`.

---

## 4. Backend architecture

### 4.1 Layering

- **`api/v1/` (34 modules)** — thin HTTP routers. Auth, role-gated dependencies (`CurrentUser` / `CurrentRecruiter` / `CurrentAdmin`), request/response schemas. No business logic.
- **`engines/` (19 modules)** — pure, mostly side-effect-free reasoning/scoring functions. `is_live()` gates live-Claude vs. deterministic mock fixtures, so the whole pipeline is exercisable offline.
- **`services/` (24 modules)** — orchestration with side effects: action handlers, the decision-learning bridge, role taxonomy, calendar sync, ATS connectors, notifications, push, user memory.
- **`workers/` (54 modules)** — Celery tasks + Beat schedule for everything asynchronous and scheduled.
- **`core/`** — cross-cutting: crypto (AES-256-GCM field encryption), governance config loader, LLM usage/cost/latency accounting, logging + request IDs, health probes, rate limiting, observability (Sentry/Prometheus), the ProblemDetail exception framework.
- **`models/` (34)** — SQLAlchemy ORM; Alembic migrations are hand-authored where autogenerate produces noise.

### 4.2 The engines (the reasoning core)

| Engine | Role | Determinism |
|---|---|---|
| `intake` | parse résumé, traditional (keyword) ATS score | deterministic |
| `semantic_match` | concept-overlap score via static embeddings | deterministic |
| `reasoning` | capability assessment, trajectory, JD interrogation, counter-recommendation | LLM |
| `enrichment` | verify GitHub/DOI/ORCID/patent links into provenanced evidence | network, gated |
| `substitution` | score alternate credentials against JD proxies | LLM |
| `governance_engine` | coherence / consistency / fidelity / bias gates | deterministic checks |
| `decision_engine` | decision-type classification (approval / advisory / escalate) | deterministic |
| `jd_evolution` | longitudinal JD drift detection | deterministic + LLM recs |
| `cv_analysis_engine` / `jd_simulation_engine` | standalone CV analysis & JD candidate simulation | LLM |
| `interview_analysis` | transcript → competency-scored scorecard | LLM + mock fallback |
| `transcription` | audio résumé/interview → text (provider-gated) | external, gated |
| `corpus` / `text_utils` / `extract` | IDF corpus, tokenization, PDF/DOCX/text extraction | deterministic |
| `client` | Claude wrapper: forced-tool JSON, tool-use, vision, streaming, **budget-aware model routing**, usage accounting | — |
| `training_*` | training-data parsing, auto-learning, training chat | mixed |

### 4.3 The assessment pipeline (`workers/tasks.run_assessment`)

1. **Idempotency / reuse** — a SHA-256 of `(résumé text + JD text + prompt-registry version)` keys the result. An identical re-run replays a prior completed result with **zero LLM cost** (`pipeline.reused`).
2. **Parallel fan-out** — deterministic keyword + semantic matchers, trajectory + JD-interrogation, and the enrichment→substitution→capability chain run concurrently (thread pool over pure functions).
3. **Learned context** — the role's reinforced `SuccessPattern` *and* its self-learned role-family capabilities (taxonomy) are injected into the capability prompt.
4. **High-assurance mode (optional)** — 3 independent capability judgments → median + spread (uncertainty is itself a signal).
5. **Scoring + delta** — three scores persisted; delta computed; counter-recommendation generated when the governance-config delta gate is crossed.
6. **Governance gates** — coherence, consistency, fidelity, bias — logged immutably to `GovernanceLog`. A run is "governed" only when operational (real, numeric) gate values are present; otherwise it is honestly recorded as ungoverned, never falsely "passing."
7. **Decision typing** — approval → `completed`; advisory/escalate → `flagged_for_review`.
8. **Provenance** — a reproducibility manifest (input hashes, model, prompt-registry version, engine methods, live/mock) is written to the audit trail.
9. **Selective verification (optional)** — after the run, only the external links the reasoning actually cited are verified asynchronously.

### 4.4 The closed learning loop

Recording a hiring `Decision` (via REST or chat) **bridges to training**: it creates a `TrainingFeedback` row and reinforces the position's `SuccessPattern` (sample size, merged high-capability components, confidence). The next assessment for that role reads this back as injected context. A hire genuinely shapes future scoring for the role — deterministic, no model retraining.

### 4.5 Scheduled autonomy (Celery Beat)

`poll-cv-folder` / `poll-jd-folder` / `poll-cv-email` (autonomous ingestion) · `retention-daily-sweep` (PDPA/GDPR retention) · `check-stale-candidates` + `daily-digest` (proactive alerts) · `merge-user-memories` (durable agent memory) · `rebuild-role-taxonomy` (self-learned role families) · `resume-stalled-plans` (durable agent-plan recovery).

---

## 5. AI-native capabilities

These are the surfaces that make the platform *agentic*, not just an ATS with an LLM bolted on.

### 5.1 Conversational agent (chat)

- **Native tool-use, not regex.** The agent exposes role-scoped tools (`analyze`, `rank`, `schedule`, `approve`, `send`, `upload`, `plan`, `clarify`) as Anthropic tool schemas. The model emits *structured, validated* tool calls that map 1:1 onto the same action handlers the REST API uses.
- **Role-scoped + confirmation-gated.** Candidates get only `analyze`; recruiters/admins get the full set. Mutating tools require explicit user confirmation, and the role is **re-checked at execution time** (a stored action can't be confirmed by a user whose role no longer permits it).
- **Token streaming.** SSE endpoint streams live tokens (SDK stream bridged to an async queue) and captures tool calls in the final message.
- **Clarify-before-act.** When a request is ambiguous or missing a parameter, the agent calls `clarify` (asks a question with suggested options) instead of guessing or emitting a plan on assumptions.
- **Plan-then-execute, durably.** For multi-step goals the agent emits a `plan` (2–8 steps, with `{{step_N.path}}` references chaining one step's result into the next). Approved plans run in the **background** (`execute_agent_plan`), are **resumable across sessions and worker restarts** (progress committed per step; a Beat task re-enqueues stalled plans), and expose live status via `GET /chat/plans/{id}`.
- **Durable cross-session memory.** An hourly merge distills each user's chat history into a small, curated, encrypted memory (facts / preferences / active focus) that is injected into the agent's system prompt on every turn.
- **Graceful degradation.** If the model key is valid but out of credits, chat falls back to a context-aware mock reply rather than erroring.

### 5.2 Autonomous operation

- **Ingestion agents** watch folders and an IMAP inbox for CVs and JDs, extract text, auto-match to open positions, and queue for human review (approval-gated by config).
- **Autonomous loop** processes pending actions per user under **rate limiting and all-or-nothing budget enforcement** (never partially overspends a daily budget), with a dead-letter queue for permanent failures.
- **Proactive alerts** (not just reactive notifications): stale-candidate nudges and a per-recruiter daily digest, idempotent per day.

### 5.3 Self-learning & adaptation

- **IDF corpus learning** — the keyword matcher's IDF weights improve as more JDs are analyzed.
- **Success-pattern reinforcement** — the decision→assessment learning loop (§4.4).
- **Self-learned role taxonomy** — deterministic cosine clustering of position JDs (model2vec) into role *families*, each with aggregated recurring capabilities; rebuilt every 6h; injected as assessment context. The platform learns its own role taxonomy from the org's JDs rather than a hand-authored one.

### 5.4 Multimodal intake

- **Vision** — photograph a résumé; Claude vision transcribes it into a Resume (`intake="vision"`).
- **Audio** — record a spoken résumé or interview; a provider-gated speech-to-text engine transcribes it (`intake="audio"`).
- **Interview-content analysis** — a transcript (typed or transcribed) is reasoned into a structured scorecard: per-competency 1–5 ratings, evidence-cited strengths/concerns, red flags, and an overall recommendation. The transcript is encrypted at rest.

---

## 6. Feature catalog (by domain)

Availability: **W** = Web, **i** = iOS, **A** = API/automation.

| Domain | Capability | W | i | A |
|---|---|:--:|:--:|:--:|
| **Assessment** | Dual-score (traditional + semantic + capability) + delta + counter-rec | ✅ | ✅ | ✅ |
| | Instant progressive scores at create (deterministic immediate, capability streams) | ✅ | ✅ | ✅ |
| | Hash-based reuse / idempotency + high-assurance ensemble | — | — | ✅ |
| | On-demand "explain this score" (counter-rec reasoning, cached) | ✅ | ✅ | ✅ |
| | Auto-rescore candidates when a position's JD drifts | — | — | ✅ |
| **Candidate** | Self-assessment (own CV vs. pasted JD) | ✅ | ✅ | ✅ |
| | CV analysis (strengths / gaps / recommendations / job matches) | ✅ | ✅ | ✅ |
| | Résumé intake: file · photo (vision) · audio | ✅ | ✅ | ✅ |
| **Recruiter** | Position CRUD, JD versioning + drift/evolution view | ✅ | ✅ | ✅ |
| | JD simulation (quality, creep, wording, archetypes) | ✅ | ✅ | ✅ |
| | Candidate ranking / shortlisting (real semantic scores) | ✅ | ✅ | ✅ |
| | Pipeline (applications by stage), bulk stage/reject actions | ✅ | ✅ | ✅ |
| | Interview scheduling + **auto-schedule** (earliest common slot) + ICS export | ✅ | ✅ | ✅ |
| | Interview-content analysis → AI scorecard | ✅ | ✅ | ✅ |
| | Decisions (advance/reject/hold/hire) → drives the learning loop | ✅ | ✅ | ✅ |
| | Recruiter dashboard / metrics | ✅ | ✅ | ✅ |
| **Conversational** | Chat agent: tool-use, streaming, clarify, plan-then-execute, durable memory | ✅ | ✅ | ✅ |
| | Pending-action confirmation flow | ✅ | ✅ | ✅ |
| | Durable agent-plan status / cancel | ✅ | (API) | ✅ |
| **Autonomy** | Ingestion agents (folder + email), agent queue review | ✅ | ✅ | ✅ |
| | Autonomous decisions under governance + budget | ✅ | — | ✅ |
| | Proactive alerts (stale candidates, daily digest) | ✅ | ✅ | ✅ |
| **Governance** | Gate results + audit trail + reproducibility manifest (display-only) | ✅ | ✅ | ✅ |
| | Governance review queue (approve/escalate) | ✅ | ✅ | ✅ |
| **Admin** | Users, audit log, analytics, compliance status, governance config (display) | ✅ | ✅ | ✅ |
| | Role taxonomy view + rebuild | ✅ | (API) | ✅ |
| **Compliance** | DSAR export / right-to-erasure, encryption at rest, Singpass OIDC | ✅ | ✅ | ✅ |
| **Integrations** | External ATS connectors (Greenhouse, Lever) import — gated | ✅ | (API) | ✅ |
| | 2-way calendar push (Google / Microsoft) — gated | — | — | ✅ |
| **Notifications** | In-app + WebSocket; email + mobile push — gated | ✅ | ✅ | ✅ |

---

## 7. Web frontend (Next.js 14)

- **App Router** with three role areas — `/candidate`, `/recruiter`, `/admin` — gated by `middleware.ts` on the NextAuth session role. Auth lives in the `(auth)` route group.
- **Auth chain:** NextAuth credentials provider → backend `/auth/login` + `/auth/me`; JWT (with refresh) carried in an encrypted session; `accessToken`/`role` surfaced on the session for the BFF and direct calls.
- **Data access:** a server-side BFF proxy (`/api/proxy/[...path]`) forwards the logged-in user's token to the backend; the streaming chat page calls the backend directly for SSE.
- **Surfaces (58 routes):** dashboards, assessment + comparison views, CV analysis, JD quality/simulation, pipeline/kanban, decisions, the full chat UI (multi-session, streaming, action confirmation), admin analytics (DEI, pipeline, sources, recruiter performance, three-signal), training console, scrapers, governance dashboard, users/audit.
- **UI:** Tailwind + a small local `components/ui` kit (button, card, input, textarea, tabs, badge, gauge, progress, alert-dialog), Recharts for analytics, an SSR-safe theme provider, toast + notification center over WebSocket.
- **Quality gates:** `next build` (type-checked, 54 static pages) + `next lint` (`next/core-web-vitals`) both green.

---

## 8. iOS frontend (SwiftUI)

- **Role-aware shell.** `SessionManager` decodes the JWT `role` claim; `MainTabView` branches into Candidate / Recruiter / Admin tab sets, each with a "More" hub for overflow.
- **Ported foundation.** Core/Auth/Networking/Design layers were ported from a prior app and hardened: a JWT-tolerant token decoder, an in-memory token cache layered over Keychain (Keychain silently fails on unsigned simulator builds), and a corrected REST base URL.
- **Feature areas (12):** Assessment (dual-score detail + record decision), CV Analysis (+ photo/vision and audio intake), Chat (transcript, composer, suggestions, sessions drawer, **on-device voice dictation**), Positions (+ pipeline), Workspace (Reviews, JD Simulation, recruiter/admin dashboards, governance/compliance, decisions, admin console), Agent (live WS queue, approve/reject/reassign, JD draft review), Onboarding, Profile, Settings, History, Resume Upload.
- **Parity.** Everything available on the web platform is reachable through the iOS app; the few admin/automation surfaces that are API-only on iOS (taxonomy rebuild, plan management) are accessible via their endpoints.
- **Build:** unsigned simulator build via XcodeGen + `xcodebuild` — `BUILD SUCCEEDED`.

---

## 9. Cross-cutting concerns

### 9.1 Security & access control
- JWT bearer auth; role-gated dependencies; **execution-time role re-checks** on confirmed chat actions and per-step in agent plans.
- Field-level **AES-256-GCM encryption at rest** for all candidate-derived PII (parsed résumé data, raw narratives, supplementary/extracted text, assessment narratives & components, decision notes, interview transcripts, Singpass IDs via blind index).
- Privacy-preserving by default; no PII in URLs/query strings.

### 9.2 Uniform error contract
Every error — custom domain errors, validation errors, plain HTTP errors (auth/404/403/409), and unhandled exceptions — is rendered as a single `ProblemDetail` shape (`type`, `title`, `status`, `detail`, `instance`, `request_id`, `timestamp`). Backward-compatible: `detail` and the HTTP status are always preserved.

### 9.3 Compliance
- **DSAR**: data export (portability) + right-to-erasure (DB cascade + compliance tombstone), with retention sweeps.
- **Mappings** documented for EU AI Act, NYC LL144, PDPA/GDPR.
- **Governance is display-only on the client.** Operational gate threshold *values* live only in encrypted server-side config (`GOVERNANCE_CONFIG_PATH`); code references named constants, never literals. Clients render outcomes, never thresholds.

### 9.4 Observability & cost control
- JSON logs with request-ID propagation; `/livez` + `/readyz` probes (DB + Redis); optional Sentry; Prometheus `/metrics`.
- **Real LLM accounting:** token usage, USD cost, and latency are extracted from every Claude call and exported as Prometheus counters/histograms; per-turn cost is charged to the user's autonomous budget.
- **Budget-aware model routing:** secondary-class calls drop to a fast model under economy mode or once the day's spend crosses a soft ratio of the daily budget.

### 9.5 External integrations (all credential-gated)
Each follows the same convention: a real implementation that **no-ops or returns a clean 503 until credentials are configured**, never fabricated output.
- **Speech-to-text** (audio intake / interview analysis) — Whisper-compatible HTTP.
- **Calendar** — Microsoft Graph (Teams) / Google Calendar (Meet) event push + meeting-link provisioning.
- **ATS connectors** — Greenhouse (Harvest) + Lever: import jobs → positions and candidates → résumés+applications, idempotent via `external_ref`.
- **Email / push** — SMTP/SES/SendGrid + FCM.

---

## 10. Production-readiness status

| Layer | Gate | Status |
|---|---|---|
| Backend | `ruff check app tests` | ✅ clean |
| Backend | `alembic upgrade head && alembic check` (live + fresh) | ✅ no drift |
| Backend | `pytest` | ✅ 317 passed / 4 skipped / 0 failed |
| Backend | offline eval harness (scoring determinism + ranking) | ✅ pass |
| Web | `next lint` (`next/core-web-vitals`) | ✅ 0 errors |
| Web | `next build` (type-checked) | ✅ 54/54 pages |
| iOS | `xcodebuild` (unsigned simulator) | ✅ BUILD SUCCEEDED |
| Config | production guard | ✅ refuses placeholder model key in prod |

**CI** (`.github/workflows/ci.yml`): Postgres + Redis service containers; backend lint → migration drift gate → eval harness → pytest; web lint → typecheck → build; iOS build job (macos-14, XcodeGen + unsigned `xcodebuild`).

---

## 11. What it can and cannot do

**Can (in code, verified):** three-signal capability assessment + counter-recommendation; progressive + idempotent + ensemble scoring; auto-rescore on JD drift; self-learned role taxonomy; CV analysis; JD simulation + evolution; evidence enrichment + selective verification; credential substitution; governance gates + audit + provenance; conversational agent (tool-use, streaming, clarify, durable plans, durable memory); autonomous ingestion + decisions + proactive alerts; closed learning loop; multimodal intake (vision + audio); interview-content analysis; auto-scheduling over availability + ICS export; DSAR/erasure; encryption at rest; Singpass OIDC; full web + iOS role workspaces.

**Cannot (by design or pending credentials/decisions):**
- **Model fine-tuning** — learning is in-context (success patterns, taxonomy, memory), not weight retraining.
- **Bias / disparate-impact monitoring is dormant** — deliberately, because the platform does not collect the demographic data it would require (the task is left unregistered).
- **External-service features are no-ops until configured** — audio transcription, 2-way calendar push, ATS API import, email, mobile push all need their provider credentials.
- **2-way calendar is write-side today** — it pushes events and provisions meeting links; reading external free/busy would need per-user OAuth.
- **CV/JD analysis engines require live model credits** (no mock fallback, unlike chat and the assessment's deterministic signals).
- **Two stress tests are skipped (documented)** — they assert behaviors the autonomous loop intentionally does not implement (per-action batch capping; governance gating inside the action loop — governance runs in the assessment pipeline).

---

## 12. Operational runbook (local / staging)

- **Services:** PostgreSQL 16 + Redis via `brew services`; backend launched with `./run-local.sh` (applies migrations, starts the Celery worker [threads pool] + Beat + uvicorn on `127.0.0.1:8000`, docs at `/docs`).
- **Workers required** for async features (assessments, CV/JD analysis, ingestion, plans, memory, taxonomy). Restart the worker after engine code changes; restart uvicorn after live DDL (asyncpg prepared-statement cache).
- **Config:** `backend/.env.staging` (gitignored) holds generated encryption/JWT keys, governance thresholds, embeddings/enrichment toggles, and the model key. With a placeholder model key the reasoning runs on deterministic mocks (the two deterministic signals are always real).
- **Web:** `npm run dev` / `npm run build`; `.env.local` points the BFF at the backend.
- **iOS:** `cd ios && xcodegen generate && xcodebuild … CODE_SIGNING_ALLOWED=NO`.

---

## 13. Appendix — codebase map & scale

```
TrueMatch/
├── backend/                       ~42k LOC Python
│   ├── app/api/v1/      (34)      HTTP routers — 185 routes
│   ├── app/engines/     (19)      reasoning / scoring (is_live mock-gated)
│   ├── app/services/    (24)      orchestration with side effects
│   ├── app/workers/     (54)      Celery tasks + Beat schedule
│   ├── app/models/      (34)      SQLAlchemy ORM (encrypted PII)
│   ├── app/core/                  crypto, governance, llm_usage, errors, health, ratelimit
│   ├── alembic/versions/          hand-authored migrations (head: f3b8c61a72d9)
│   └── tests/                     317 passing
├── web/                           ~25k LOC TypeScript
│   ├── src/app/         (58)      App-Router pages (candidate/recruiter/admin)
│   ├── src/components/  (70)      UI + feature components
│   └── src/lib/                   api client, auth, BFF proxy, types
├── ios/                           ~9k LOC Swift
│   └── TrueMatch/Features/ (12)   role-aware SwiftUI workspaces
└── .github/workflows/ci.yml       backend + web + iOS gates
```

**Key data models (34):** `Assessment`, `Position` (+ `JDVersion`, `role_cluster_id`, `external_ref`), `Resume`, `Application`, `Interview` (+ `Scorecard`, `InterviewSlot`, calendar fields, AI-analysis fields), `Decision`, `Company`, `User`, `GovernanceLog` / `GovernanceReview`, `AuditTrail` (reproducibility), `AgentPlan`, `UserAgentMemory`, `RoleCluster`, `IngestQueueItem`, `AutonomousSettings`, `ChatSession`/`ChatMessage`, `Notification`, `DeviceToken`, `CVAnalysis*`, `JDSimulation*`, `Training*`, `DSARRequest`, `CapabilityMapping`/`CredentialMapping`/`SuccessPattern`, `CandidateArchetype`.

---

*This document is the single definitive briefing for TrueMatch. It reflects the codebase as of 2026-06-14, after the production-readiness pass across backend, web, and iOS. All AI surfaces are mock-gated for offline/credential-free operation; all external integrations are credential-gated no-ops until configured.*
