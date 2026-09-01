# TrueMatch — AI-Embodied ATS Platform
## System Briefing Document
**Version 1.0 — May 2026 | MustafarAI / Digital Court — CONFIDENTIAL**

---

## 1. What TrueMatch Is

TrueMatch is an **AI-Embodied Applicant Tracking System** — a platform that REASONS about candidate capability rather than matching keywords against job descriptions. It operates autonomously, meaning CVs and JD drafts can be dropped or emailed into the system and processed without human intervention, while giving recruiters and hiring managers full oversight and control from any device including iOS on the move.

The platform is built on the principle that **the best candidates are often invisible to traditional ATS systems** — their capability lives in demonstrated work, patents, published research, and ecosystem-building rather than in the exact keywords a legacy system scans for. TrueMatch's signature feature is surfacing these candidates and explaining why, grounded in evidence.

**Owner:** Mohamed Reezan Mohd Fadzil / MustafarAI / Digital Court  
**Stack:** FastAPI (Python 3.12+) · PostgreSQL 16 · Redis · Celery · Anthropic Claude API · Next.js 14 · SwiftUI iOS 17 · model2vec embeddings  
**Monorepo:** `~/Desktop/TrueMatch/` — `backend/` · `web/` · `ios/`

---

## 2. Codebase Size & Maturity

| Layer | Files | Notes |
|---|---|---|
| **Backend** | 69 Python files | FastAPI app, 11 engines, 8 API routers, 11 models, 2 agents, 11 core modules |
| **Backend tests** | 18 test files, **87 pass** (1 skipped) | Ruff clean; Docker Postgres e2e skips w/o Docker |
| **Database migrations** | 9 (0001–0009) | Applied to live local Postgres |
| **API endpoints** | 48 | REST + WebSocket |
| **Web** | 24 pages · 31 components | Next.js 14 App Router, `next build` green |
| **iOS** | 61 Swift files | `xcodebuild BUILD SUCCEEDED` (Xcode 26, iOS 17 SDK) |

**Local staging is live** on this laptop: Postgres + Redis + API (`127.0.0.1:8000`) + Celery worker + Celery Beat (autonomous agents polling every 30 seconds). OpenClaw runs in parallel with zero port conflict (OpenClaw: 18789/18791; TrueMatch: 3000/5432/6379/8000).

---

## 3. What the System Can Do Today — Production-Ready Features

### 3.1 The Core Assessment Pipeline (Fully Live, Verified)

Every assessment runs a **9-stage pipeline** (parallel-fanned where independent):

| Stage | Engine | What it does |
|---|---|---|
| **1. Document extraction** | `extract.py` | Real PDF/DOCX/TXT → text extraction at upload; rejects image-only scans |
| **2. Resume parsing** | `intake.parse_resume` | LLM-powered structured extraction preserving the candidate's own narrative; captures non-traditional signals (patents, publications, shipped systems) |
| **3. JD analysis** | `intake.analyze_jd` | Decomposes JD into ESSENTIAL / PREFERRED / PROXY requirements; names the underlying capability each proxy is really testing for |
| **4. Traditional ATS baseline** | `intake.traditional_ats` | **Deterministic TF-IDF** (no LLM) — literal keyword overlap. Stable, reproducible, role-differentiated. M Moser = 13 / ALTEN = 15 / MDDI = 19 on the same CV. |
| **5. Semantic match** | `semantic_match.py` | **Static embeddings** (model2vec, 140 MB, no torch) — conceptual match on raw text spans. Catches "ecosystem brokering ↔ built innovation ecosystem" that keyword matching scores 0. |
| **6. Evidence enrichment** | `enrichment.py` | Fetches external links (GitHub/DOI/ORCID) over the network; verifies claims with primary sources; patent numbers flagged for IPOS manual confirmation |
| **7. Credential substitution** | `substitution.py` | For each JD proxy ("MSc CS"), explicitly scores the candidate's alternate evidence (HIGH/MEDIUM/WEAK). Unverified self-claims capped at MEDIUM. |
| **8. Capability reasoning** | `reasoning.py` | Full LLM capability assessment, trajectory, JD interrogation, counter-recommendation — role-specific, anchored to the JD's actual requirements |
| **9. Governance** | `governance_engine.py` | Mandatory coherence + consistency + fidelity + bias checks; gate failure routes to `flagged_for_review` — cannot be bypassed |

**Live-verified results on owner's CV (Mohamed Reezan Mohd Fadzil):**
- vs M Moser AI Leader: **Traditional 13 → Semantic 68 → Capability 78 · Δ65 · counter-rec FIRED** (hidden gem)
- vs MDDI Ecosystem Director: **Traditional 19 → Semantic 72 → Capability 78 · Δ59 · counter-rec FIRED**
- vs ALTEN AI Asia Manager: **Traditional 15 → Semantic 71 → Capability 72 · Δ57 · counter-rec FIRED**

Same candidate scores **differently per role** (both deterministic signals differentiate correctly), and the system correctly identifies him as a `surfaced_strong_match` for all three — his capability far exceeds what a keyword ATS would surface.

---

### 3.2 JD Intelligence (Pillar 2 + 3)

**One-shot JD quality (live):**
- Scores the JD 0–100 for quality
- Classifies every requirement as ESSENTIAL / PREFERRED / PROXY
- For proxies: names the underlying capability the credential is really testing
- Flags: vague requirements, inflated seniority, impossible constraints ("8 years of a 3-year-old tool"), exclusionary phrasing, purple-squirrel specs
- Produces a concrete, actionable **Fix:** for every issue
- Runs synchronously at position creation — immediate quality feedback

**JD evolution (live, Pillar 3):**
- Every position change snapshots an immutable version (JD version history table)
- `jd_evolution.py` detects longitudinal drift across versions: `experience_creep`, `scope_expansion`, `quality_decline`
- Produces recommendations + an AI-rewritten evolved requirements draft
- Live-tested: inflating ALTEN from "7–12 yrs" to "12–18 yrs" immediately detected as `experience_creep` + `degrading` trend

---

### 3.3 Autonomous Agentic Operation (Fully Live)

**The system runs 24/7 without human intervention:**

| Capability | How |
|---|---|
| **CV drop-folder ingestion** | Copy any PDF/DOCX to `backend/inbox/cv/` — Celery Beat picks it up within 30 seconds |
| **Email CV ingestion** | Configure IMAP credentials in `.env.staging` — the agent polls unread messages every 60 seconds, extracts CV attachments + email body as cover letter |
| **Cover letter extraction** | Email body or second attachment is automatically associated as `additional_context` in the assessment |
| **Auto-matching** | Incoming CV is matched to the best open position by TF-IDF similarity |
| **JD draft drop-folder** | Copy a `.txt` JD draft to `backend/inbox/jd/` — agent picks it up, scores it, improves it, holds for human review |
| **API-triggered from iOS** | `POST /agents/trigger` — run an assessment on any resume from anywhere |
| **JD draft via API** | `POST /agents/jd/draft` — submit JD text for autonomous analysis from iOS |
| **Approval workflow** | `INGEST_REQUIRE_APPROVAL=true` routes all autonomous CVs through human review before pipeline runs |
| **Live-verified** | Beat dispatched JD folder task, processed 1 file, moved to `processed/` — all confirmed in logs |

---

### 3.4 iOS App — On-the-Move Control (Builds, Not Yet Device-Signed)

**Agent command screens:**
- `AgentDashboardView` — live WebSocket-connected feed; queue counts; quick-action buttons to trigger assessments or submit JD drafts
- `IngestQueueView` — filterable list of everything the agents picked up; approve/reject/reassign with notes
- `JDDraftReviewView` — quality score, per-issue Fix: recommendations, AI-improved draft with inline editor, one-tap accept

**Assessment screens:**
- Resume upload (PDF/DOCX/text paste + supplementary links, patents, DOIs)
- 3-signal progression (Keyword → Semantic → Capability bar chart + match-type badge)
- Dual-score card (Traditional vs Capability + delta)
- Capability narrative, trajectory, gap analysis, governance badges, substitution panel
- Job matching, assessment history, profile

**Foundation:**
- Real JWT auth + Singpass OAuth (server-owned PKCE)
- WebSocket streaming for live assessment progress
- SwiftData offline caching + background sync
- Push notifications (assessment-ready, agent events, JD draft ready)
- Deep-link routing to agent/assessment/position screens
- EN / ZH-Hans / MS / TA localisation (scaffolded)

---

### 3.5 Web Console (Builds, Reads Mock Until Live Backend Connected)

- **24 pages** across 3 role areas: `/candidate`, `/recruiter`, `/admin`
- Real NextAuth (validates against backend `/auth/login` + `/me`; tokens in encrypted JWT; auto-refresh)
- Role-based middleware (`middleware.ts` — admin / recruiter / candidate gated)
- BFF proxy (`/api/proxy/[...path]`) forwards **logged-in user's token** server-side
- Real write operations: `FileUpload → POST /files/resume`, `DecisionPanel → POST /decisions`, JD quality live from backend
- 3-signal `SignalProgression` component, `SubstitutionPanel`, `JDQualityCard` with per-issue Fix:
- Candidate upload page: 2-step resume upload → paste JD → trigger self-assessment
- Read pages fall back to mock data when backend unreachable (by design for offline dev)

---

### 3.6 Security, Compliance & Auditability

**Field-level encryption (all PII at rest):**
- AES-256-GCM, `enc:v1:` prefix (versioned for key rotation)
- Every candidate-PII column encrypted: resume text/parsed data, narratives, decision notes, audit events, JD agent output, substitutions, evidence, `singpass_id`
- Keyed blind index for `singpass_id` equality lookups without exposing ciphertext
- Encryption-at-rest proven through a real SQLite engine test

**Regulatory compliance (`COMPLIANCE.md`):**
| Framework | Key controls implemented |
|---|---|
| **EU AI Act** | Governance gates (Art.9), immutable logging (Art.12), transparency (Art.13), human oversight (Art.14), reproducibility (Art.15) |
| **NYC Local Law 144** | Bias check on every assessment (not sampled), exportable bias analytics, proxy→substitution to reduce adverse impact |
| **PDPA / GDPR** | `POST /profile/export` (portability), `DELETE /profile` (erasure + cascade + tombstone), data minimisation (NDI UUID not NRIC) |

**Provenance & reproducibility:**
- Every assessment records a `pipeline.provenance` manifest: input SHA-256 hashes (resume + JD), model name, `PROMPT_REGISTRY_VERSION`, deterministic engine method versions (`keyword-tfidf-v1`, `lexical-span-v2`, `jd-evolution-v1`), reasoning mode (live/mock)
- The same CV + JD **always produces the same deterministic scores** (traditional + semantic)
- Full immutable audit trail: 7+ audit events per assessment

**IP safety (absolute):**
- Governance threshold values live ONLY in encrypted server-side config — never in source, logs, API responses, or client code
- Named constants only in source (`COHERENCE_THRESHOLD`, `CONSISTENCY_BOUND`, `FIDELITY_THRESHOLD`, `COUNTER_REC_DELTA`)
- Forbidden terms (`Kuramoto`, `Lipschitz`, `TFNP`, MustafarAI patent numbers) grep-verified absent from all code
- Client governance is display-only; no threshold computation on any client

---

### 3.7 Infrastructure & Operations

- **Infra**: Dockerfile + `docker-compose.yml` (postgres/redis/migrate/api/worker services)
- **CI/CD**: `.github/workflows/ci.yml` (ruff + pytest + web build; Docker Postgres e2e test)
- **Probes**: `/livez` (liveness), `/readyz` (Postgres + Redis checks, 503 when down), `/health`
- **Observability**: structured JSON logs + `X-Request-ID` correlation (verified in responses); optional Sentry + Prometheus (`/metrics`)
- **Rate limiting**: fixed-window per-IP (Redis-backed, in-memory fallback), probes exempt
- **Celery hardening**: soft/hard time limits (10/11 min), `acks_late`, prefetch 1, result TTL 24h
- **Local staging**: runs entirely on laptop (no cloud, no GPU, ~0.5 GB RAM overhead, zero OpenClaw conflict)

---

## 4. The Three-Signal Scoring Architecture (Unique)

Traditional ATS gives you **one** signal: keyword match. TrueMatch gives you **three independent signals** that tell different stories:

```
Traditional (keyword-tfidf-v1)  →  Semantic (embedding:potion-base-8M)  →  Capability (LLM reasoning)
     DETERMINISTIC                       DETERMINISTIC                         LLM-BASED
     Role-differentiated                 Role-differentiated                   Role-anchored
     No LLM                              No torch, 3.6ms encode               Real Claude
     Reproducible / auditable            Reproducible / auditable              Governed + audited
```

**What each signal tells you:**
- **Traditional (low)**: A keyword ATS would reject this candidate
- **Semantic (moderate–high)**: At the conceptual level, their experience matches what the role needs — even if the vocabulary differs
- **Capability (high)**: The reasoning engine, with evidence, says they can perform this role
- **Large delta** (capability − traditional): A candidate hidden from conventional screening
- **`match_type` classification**: `hidden_gem` (all three signals diverge — rescue this person) vs `surfaced_strong_match` (signals agree — confirm this person) vs `keyword_aligned` (no counter-rec needed)

**The IDF learning loop**: every analysed JD contributes term frequencies to the `corpus_term_stats` table. As the corpus grows, the keyword matcher automatically down-weights common terms and up-weights role-distinctive terms — the system sharpens with every analysis.

---

## 5. What the System CANNOT Do Yet

| Gap | Severity | What's needed |
|---|---|---|
| **Capability score is "sticky"** (~78–81 for most candidates) | Medium | The LLM capability prompt needs stricter role-anchoring; it rates general competence rather than role-fit strongly enough |
| **Traditional ATS is flat across JDs** (often ~13–19) | Medium | Acceptable for generating delta; could benefit from embedding-aware term weighting beyond TF-IDF |
| **Singpass OIDC is unverified against live NDI** | Medium | Code-complete; needs NDI onboarding credentials (client_id, signing/encryption JWKs, registered redirect URI) |
| **S3 object storage uses stub credentials** | Medium | Raw resume binary not stored (extracted text is); needs real AWS credentials for file durability |
| **iOS needs a signing Team to run on device** | Medium | Compiles and runs on simulator; App Store / device run needs Apple Developer account |
| **iOS skeleton screens** (JobMatching/Profile/Settings detail) | Low–Medium | Compile but show minimal content; need full screens before App Store submission |
| **iOS unit tests = zero** | Low | `TrueMatchTests/` exists but is empty; xcodebuild coverage not enabled |
| **Web reads are mock-fallback** | Resolved once backend deployed | All reads fall back to realistic mock data when backend unreachable; by design for offline dev |
| **No app icon art** | Low | AppIcon slot exists in Assets.xcassets; needs 1024² PNG design |
| **KMS key-wrap + rotation runbook** | Operational | Encryption keys come from env; production should wrap DEK with AWS KMS |
| **NYC LL144 formal bias-audit export endpoint** | Low | Bias checks run on every assessment; a PDF/CSV export for the independent auditor isn't built |
| **Pillar 3 JD evolution web surface** | Low | `/agents/jd/{id}/suggestions` API exists; the web recruiter UI for reviewing evolved JDs is the iOS `JDDraftReviewView` — no Next.js equivalent yet |
| **Multi-tenant isolation** | Phase 3 | Row-level security by `company_id` is in the schema; not enforced at RLS/policy level |
| **ATS integration connectors** | Phase 3 | No Workday/Greenhouse/iCIMS connectors |
| **Android app** | Phase 3 | iOS only |

---

## 6. Unique Strengths & Differentiators

### 6.1 The fundamental idea
Every other ATS is a **keyword filter that got smarter**. TrueMatch is an **AI reasoner that can also filter by keywords** (the traditional baseline). The delta between the two IS the product — it is literally a measurement of what conventional screening misses.

### 6.2 The alternate-credentials engine (Pillar 6)
No other ATS explicitly asks: *"The JD requires an MSc CS — but is there alternate evidence that demonstrates the same underlying capability?"* TrueMatch names the proxy, hunts the CV for substitutes, and scores HIGH/MEDIUM/WEAK. A candidate with 6 lead-inventor patents, 8 peer-reviewed publications, and a shipped production AI system scores HIGH substitution for "deep technical depth" — even with an Economics degree. A traditional ATS scores them zero.

### 6.3 External evidence verification (Pillar 5)
Supplementary links (ORCID, GitHub, DOIs) are **fetched and verified** — not just trusted as text. A publication listed on a CV either resolves to a real Zenodo/Crossref record or it's marked unverified. This changes the counter-recommendation from "the LLM thinks so" to "here is primary-source proof, scored."

### 6.4 The JD interrogation that pushes back
The system doesn't just analyse the JD — it **interrogates it**. "This JD requires 8 years with a tool that has existed for 3 years." "MSc CS is a proxy for technical depth — not the actual need." "This spec describes a candidate who effectively does not exist." Recruiters get the JD quality score AND a concrete Fix: for every issue, before a single candidate is ever assessed.

### 6.5 Autonomous, agentic operation
CVs arrive by email, drop-folder, or API. JD drafts arrive the same way. The system processes everything without human initiation, holds items for review when required, and the recruiter approves/rejects/reassigns from their phone. This is architecturally different from an ATS where humans always initiate.

### 6.6 Every decision is reproducible and auditable
The two deterministic signals (keyword-tfidf-v1, embedding:potion-base-8M) produce **bit-identical results** for the same CV + JD every run. The provenance manifest records input hashes, model version, prompt registry version, and engine method versions. Any assessment can be reconstructed and independently verified. This is a regulatory requirement (EU AI Act Art.15) that most ATS products cannot satisfy.

### 6.7 Governance that cannot be bypassed
The platform is not "AI-assisted" in the sense of a helpful suggestion. The governance engine is a **mandatory gate**: coherence, consistency, fidelity, and bias checks run on every assessment before any output reaches a user. If fidelity fails, the assessment is routed to `flagged_for_review` — automatically, without any code path that bypasses it. The threshold values are trade secrets stored in encrypted server-side config; they have never appeared in source code, logs, or API responses.

### 6.8 The IDF learning loop
Every JD the system analyses makes the keyword matcher smarter. Common recruitment boilerplate ("experience", "strong", "team") gets progressively down-weighted. Role-distinctive terms ("kubernetes", "ecosystem brokering", "cognitive AI") get up-weighted. The system compounds value with use.

---

## 7. Architecture Principles

1. **Reason, don't match.** Assess what the candidate CAN DO, not how their resume LOOKS.
2. **Three signals, not one.** Keyword baseline → semantic concept match → capability reasoning. The delta between them is the insight.
3. **All reasoning is server-side.** Clients are thin. Both iOS and web are presentation layers consuming the same API. Governance cannot be bypassed by client modification.
4. **Deterministic where possible.** The two non-LLM signals are reproducible/auditable pure functions of raw text. No variance.
5. **Agents are independent functions.** Every engine can execute in isolation. The pipeline fans them out in parallel. Adding a new signal means adding a function — not rewriting the pipeline.
6. **Counter-recommend.** When a great candidate would be rejected by traditional screening, say so and explain why with evidence.
7. **Interrogate the JD.** The specification is not sacred. If it's flawed, say so.
8. **Govern everything.** Every assessment is coherence-checked, consistency-bounded, and fidelity-verified before any human sees it.
9. **Human decides.** AI reasons. Human judges. The AI surfaces what the human would miss. The human applies what the AI cannot know.
10. **Audit always.** Every assessment, every decision, every override, every autonomous action — recorded, timestamped, exportable.

---

## 8. Current Stack Reference

### Backend
| Component | Technology |
|---|---|
| API framework | FastAPI 0.111+ with async SQLAlchemy 2.x |
| Database | PostgreSQL 16 (9 migrations applied) |
| Message broker / cache | Redis 8 |
| Async task queue | Celery 5.4 (worker + Beat scheduler) |
| LLM reasoning | Anthropic Claude (claude-sonnet-4-20250514) via forced tool-use JSON |
| Embeddings | model2vec `potion-base-8M` (59 MB, no torch, 3.6ms encode) |
| Authentication | JWT (python-jose) + bcrypt 4.1+ + Singpass OIDC |
| Encryption | AES-256-GCM (cryptography library) + HMAC blind index |
| External enrichment | httpx (Crossref/DataCite DOI, ORCID, GitHub APIs) |
| Object storage | boto3/S3 (stub credentials in staging; SSE on) |

### Web
| Component | Technology |
|---|---|
| Framework | Next.js 14 App Router, TypeScript |
| Auth | NextAuth.js 4.24 (credentials → backend validate + me) |
| Styling | Tailwind CSS + Shadcn/ui |
| Visualization | Recharts (trajectory, analytics) |
| BFF proxy | `/api/proxy/[...path]` — forwards user JWT server-side |

### iOS
| Component | Technology |
|---|---|
| Framework | SwiftUI, iOS 17+, SwiftData |
| Networking | URLSession actor (APIClient) + URLSessionWebSocketTask |
| Auth | Keychain (SessionManager) + Singpass ASWebAuthenticationSession |
| Offline | SwiftData models + OfflineQueue + BGTask sync |
| Push | APNs (PushNotificationManager + NotificationHandler) |
| Localization | Localizable.xcstrings (EN/ZH-Hans/MS/TA) |

---

## 9. Production Readiness Checklist

| Item | Status |
|---|---|
| Core reasoning pipeline (all 8 pillars) | ✅ Production-ready, live-verified |
| Deterministic signals (traditional + semantic) | ✅ Stable, role-differentiated, reproducible |
| Governance (4 gates + mandatory routing) | ✅ Live — caught real fidelity failures |
| Field-level PII encryption (AES-256-GCM) | ✅ All columns encrypted, at-rest proven |
| PDPA/GDPR export + erasure | ✅ Endpoints built and tested |
| Immutable audit trail + provenance | ✅ Full chain, regulator-exportable |
| Autonomous CV ingestion (folder + email) | ✅ Live on staging |
| Autonomous JD analysis (folder + API) | ✅ Live on staging |
| Agent control API + WebSocket | ✅ All endpoints, real-time feed |
| iOS agent screens (Dashboard/Queue/JDReview) | ✅ Compiles, builds succeeded |
| Web console (role-gated, write ops) | ✅ Builds, all writes wired |
| Auth (email/password JWT + bcrypt) | ✅ Live on staging |
| Auth (Singpass OIDC) | ⚠️ Code-complete, needs NDI credentials |
| S3 file storage | ⚠️ Wired, stub credentials in staging |
| iOS on-device run | ⚠️ Needs Apple Developer signing team |
| Real governance thresholds | ⚠️ Staging uses test values; trade-secret values must be provisioned |
| Anthropic API key | ⚠️ Needs rotation; staging runs mock without one |
| Docker/cloud deployment | ⚠️ Dockerfile + compose ready; not yet deployed |

---

## 10. Operating the System Today

**Start local staging:**
```bash
cd ~/Desktop/TrueMatch/backend
./run-local.sh
# API: http://127.0.0.1:8000  |  Docs: /docs
# Inbox folders: ./inbox/cv/  and  ./inbox/jd/
```

**Drop a CV:**
```bash
cp /path/to/candidate.pdf ~/Desktop/TrueMatch/backend/inbox/cv/
# Agent picks it up within 30 seconds
```

**Drop a JD draft:**
```bash
echo "We are looking for a Senior AI Engineer…" > ~/Desktop/TrueMatch/backend/inbox/jd/role.txt
# Agent analyses it, improves it, holds for review
```

**Enable real reasoning:**
```
# Edit backend/.env.staging
ANTHROPIC_API_KEY=sk-ant-<your-rotated-key>
# Then: ./run-local.sh
```

**Enable email ingestion:**
```
# Edit backend/.env.staging
INGEST_IMAP_HOST=imap.gmail.com
INGEST_IMAP_USER=hiring@yourdomain.com
INGEST_IMAP_PASSWORD=<app-password>
```

---

*This document is CONFIDENTIAL. The governance engine implements proprietary mechanisms that are patent-pending under MustafarAI / Digital Court. All governance parameters are trade secrets.*

*© 2026 Mohamed Reezan Mohd Fadzil / MustafarAI / Digital Court. All Rights Reserved.*
