# TrueMatch — Web Platform

The web client for **TrueMatch**, an AI-embodied hiring-assessment platform. It serves three roles from a single Next.js app:

- **Candidate portal** — upload a resume, view capability-first assessments, browse roles.
- **Recruiter console** — capability-ranked pipelines, candidate comparison, JD quality, decisions.
- **Admin panel** — governance status, compliance, fairness analytics, audit trail, user management.

The signature insight throughout is the **delta** between a *Traditional ATS Score* and the *TrueMatch Capability Score* — the gap where strong candidates are routinely missed.

## Tech stack

- **Next.js 14** (App Router) + **TypeScript**
- **Tailwind CSS** with Shadcn/ui-style primitives (`button`, `card`, `badge`, `gauge`)
- **Recharts** for trajectory, comparison, fairness, and outcome charts
- **NextAuth.js** for authentication (credentials + a Singpass/OIDC placeholder)
- A **BFF (backend-for-frontend) proxy** — the browser never calls the backend directly

## Getting started

```bash
cp .env.example .env.local   # then fill in values
npm install
npm run dev                  # http://localhost:3000
```

Other scripts:

```bash
npm run build       # production build
npm run start       # serve the production build
npm run typecheck   # tsc --noEmit
npm run lint        # next lint
```

### Environment variables

| Variable | Scope | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | client | Base path the browser uses to reach the **BFF proxy** (defaults to `/api`). Not the backend. |
| `NEXTAUTH_SECRET` | server | NextAuth session signing secret. |
| `NEXTAUTH_URL` | server | Canonical app URL for NextAuth. |
| `BACKEND_API_URL` | **server only** | The real backend the proxy forwards to (`https://api.truematch.ai/v1`). |
| `BACKEND_API_TOKEN` | **server only** | Service token injected by the proxy. Never reaches the browser. |

## Architecture: thin client over a BFF proxy

The browser bundle is intentionally a **thin client**. It only ever calls the
server-side proxy at `src/app/api/[...proxy]/route.ts`. That route runs on the
server, forwards requests to `BACKEND_API_URL`, and injects the service token.

As a result:

- No backend secrets ship in the client bundle.
- No backend hostnames or tokens are exposed to the browser.
- Auth is attached server-side, not in client JavaScript.

## Mocked vs wired

This scaffold renders **standalone** without a live backend.

- `src/lib/api.ts` calls the BFF proxy first. If the proxy/backend is
  unreachable (502 or network error), it falls back to **clearly-typed mock
  data** in `src/lib/mock.ts` so every page renders.
- All mock values are illustrative fixtures (e.g. traditional `43`,
  capability `87`, delta `+44`).
- To go live, set `BACKEND_API_URL` / `BACKEND_API_TOKEN` and ensure the
  backend implements the routes the proxy forwards to (`/assessments/:id`,
  `/positions`, `/positions/:id/pipeline`, `/decisions`, `/audit`, `/users`).
  No client code changes are required.

### What is currently mocked

| Area | Source |
| --- | --- |
| Assessment (scores, narrative, gaps, counter-rec, JD quality, trajectory, governance) | `mockAssessment` |
| Recruiter pipeline | `mockPipeline` |
| Positions | `mockPositions` |
| Decisions / overrides | `mockDecisions` |
| Audit trail | `mockAudit` |
| Users | `mockUsers` |
| Admin analytics / fairness / outcomes | inline page fixtures |

## Project structure

```
src/
  app/
    layout.tsx, page.tsx              # marketing landing
    (auth)/                           # login, signup, singpass-callback
    (candidate)/                      # dashboard, upload, assessment/[id], jobs, profile, history
    (recruiter)/                      # dashboard, positions, candidates/[id], compare, jd-quality, decisions
    (admin)/                          # dashboard, configuration, compliance, analytics, audit, users
    api/[...proxy]/route.ts           # BFF proxy
    api/auth/[...nextauth]/route.ts   # NextAuth handler
  components/
    ui/         # button, card, badge, gauge
    assessment/ # DualScoreCard, CapabilityNarrative, TrajectoryChart, GapAnalysis,
                # CounterRecommendation, GovernanceBadges, DeltaVisualization
    recruiter/  # CandidatePipeline, CandidateCard, ComparisonView, DecisionPanel,
                # JDQualityCard, OverrideTracker
    admin/      # GovernanceConfig, ComplianceReport, AuditTrailViewer, BiasReport, OutcomeAnalytics
    shared/     # ScoreGauge, NarrativeBlock, StatusBadge, FileUpload, AppShell
  lib/          # api.ts, auth.ts, types.ts, utils.ts, mock.ts
  styles/       # globals.css
```

## Key UI behaviors

- **DualScoreCard** — Traditional ATS Score vs TrueMatch Capability Score side by side, with the delta highlighted as the headline.
- **CounterRecommendation** — appears when the traditional score is low but capability is high: *"This candidate does not match the JD as written. However…"*
- **GovernanceBadges** — coherence / consistency / fidelity status + score badges. **Display only**; values come from the backend.
- **TrajectoryChart** — Recharts career-arc of capability and scope over time.
- **CandidatePipeline** — sortable by capability score, traditional score, or delta.
- **JDQualityCard** — JD quality score plus proxy / impossible-requirement flags.

## Governance & data integrity

Governance signals (coherence, consistency, fidelity, bias flags) are **display
only**. The web client renders the scores and statuses provided by the
assessment service; it never computes them and never applies any threshold.
Governance policy is owned and enforced entirely server-side and is not exposed
to or editable from the web console.
