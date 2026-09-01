# TrueMatch Backend

AI-embodied ATS / hiring-assessment platform backend (FastAPI).

TrueMatch evaluates candidates by **demonstrated capability** rather than keyword
matching: it runs a traditional ATS simulation as a baseline, then performs a
capability assessment, trajectory analysis, job-description interrogation, and —
where the capability view materially diverges from the baseline — produces an
evidence-backed counter-recommendation. Every result passes through a governance
layer (coherence, consistency, fidelity, and bias checks) and is recorded in an
append-only audit trail.

## Tech stack

- Python 3.12+, FastAPI, Uvicorn
- PostgreSQL 16 via SQLAlchemy 2.x (async, asyncpg) + Alembic migrations
- Redis (cache + Celery broker/result backend)
- Celery for the asynchronous assessment pipeline
- Anthropic Claude (`claude-sonnet-4-20250514`) for reasoning
- Pydantic v2 / pydantic-settings, JWT auth (python-jose), passlib (bcrypt)
- boto3 for S3 uploads

## Project layout

```
app/
  main.py            FastAPI app, CORS, routers, health
  config.py          Settings (pydantic-settings)
  database.py        Async engine + session
  deps.py            get_db, get_current_user, role guards
  models/            SQLAlchemy models
  schemas/           Pydantic request/response models
  api/v1/            Routers: auth, assessments, positions, decisions, profile, files, admin
  core/              security.py (hash/JWT), governance.py (named-constant gate registry)
  engines/           intake, reasoning, governance_engine, client (Claude), prompts/ (server-side)
  workers/           celery_app.py, tasks.py (assessment pipeline)
governance/          config.example.json (PLACEHOLDER values only)
alembic/             migrations
```

## Setup

```bash
# 1. Create a virtualenv and install
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. Configure environment
cp .env.example .env
# edit .env: DATABASE_URL, REDIS_URL, ANTHROPIC_API_KEY, JWT_SECRET, S3_BUCKET, GOVERNANCE_CONFIG_PATH

# 3. Run database migrations
alembic upgrade head
```

## Run

```bash
# API
uvicorn app.main:app --reload --port 8000
# OpenAPI docs at http://localhost:8000/docs

# Redis (broker) — e.g. via Docker
docker run -p 6379:6379 redis:7

# Celery worker (assessment pipeline)
celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

## Assessment pipeline

Creating an assessment (`POST /api/v1/assessments`) enqueues a Celery task
(`app.workers.tasks.run_assessment`) that runs:

1. **Intake** — parse resume, analyze job description, simulate a traditional ATS baseline.
2. **Reasoning** — capability assessment, trajectory analysis, JD interrogation, and a
   counter-recommendation when capability materially exceeds the baseline.
3. **Governance** — coherence, consistency, fidelity, and bias checks.
4. **Compile + audit** — persist results and write audit-trail events.

### Live Claude calls vs mock data

The engine modules call Claude live whenever a real `ANTHROPIC_API_KEY` is
configured (`app/engines/client.is_live()`); with the placeholder key they return
deterministic **MOCK** fixtures so the pipeline runs offline and in tests. Set
`LLM_FORCE_MOCK=true` to force mocks even with a key. The client
(`app/engines/client.py`) applies **prompt caching** to the stable system block,
parses strict JSON robustly, and retries transient errors. Resume text is
extracted from PDF/DOCX/TXT at upload time (`app/engines/extract.py`).

## Observability & ops

- **Probes:** `/livez` (liveness), `/readyz` (checks Postgres + Redis, 503 when
  not ready), `/health` (basic). Docker `HEALTHCHECK` targets `/livez`.
- **Logging:** structured JSON to stdout with a per-request correlation id
  (`X-Request-ID`, echoed in responses). Set `LOG_JSON=false` for dev-readable logs.
- **Metrics:** Prometheus at `/metrics` (request count + latency) when
  `METRICS_ENABLED` and `prometheus-client` is installed.
- **Error tracking:** set `SENTRY_DSN` to enable Sentry (`send_default_pii=False`).
- **Rate limiting:** fixed-window per-IP (`RATE_LIMIT_PER_MINUTE`, Redis-backed
  with in-memory fallback); probes/metrics are exempt.
- **Celery:** `task_acks_late`, prefetch 1, soft/hard time limits (10/11 min).

## Docker

```bash
cp .env.example .env
docker compose up --build       # postgres + redis + migrate + api + worker
# api on :8000, applies `alembic upgrade head` via the one-shot `migrate` service
```

CI (`.github/workflows/ci.yml`) runs ruff + the full pytest suite (including the
Dockerized Postgres end-to-end test) and a web typecheck/build.

## PII encryption & data rights

- **Encryption at rest:** sensitive columns (resume text/parsed data, assessment
  narratives + derived JSONB, decision notes, audit events, profile, `singpass_id`)
  are AES-256-GCM encrypted transparently at the ORM layer
  (`app/core/crypto.py`, `app/models/_types.py`). Keys come from `ENCRYPTION_KEY` /
  `ENCRYPTION_INDEX_KEY` (base64, secrets-manager injected). Blank → unencrypted
  dev mode (warns). Searchable `singpass_id` uses a keyed blind index.
- **S3:** uploads are server-side encrypted (KMS or AES256), size-capped, and fail
  hard in production if storage is misconfigured.
- **PDPA/GDPR:** `POST /profile/export` (portability) and `DELETE /profile`
  (right to erasure, DB-cascade + compliance tombstone).

## Governance & IP safety

Governance threshold **values** never appear in source. Code references **named
constants only** (`COHERENCE_THRESHOLD`, `CONSISTENCY_BOUND`, `FIDELITY_THRESHOLD`)
and loads the actual values at runtime from the external/encrypted configuration
referenced by `GOVERNANCE_CONFIG_PATH`. `governance/config.example.json` contains
**placeholder** values only. Governance API responses expose pass/fail booleans and
qualitative notes — never thresholds. The committed `.gitignore` excludes `.env`,
real governance config files, and `*.secret`.

Prompt templates under `app/engines/prompts/` are **proprietary**, kept
server-side, and are never exposed through the API. They are placeholder scaffolds
to be hardened before production (see that directory's README).
