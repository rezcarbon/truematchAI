# TrueMatch Engine — Production Deploy (host-agnostic)

The engine deploys as one unit via `Dockerfile` + `docker-compose.yml`:
`migrate` (alembic upgrade head) → `api` (uvicorn) → `worker` (Celery) → `beat`.
This runs as-is on a VPS, or maps cleanly onto Fly.io / Render / ECS (one
service per compose service; managed Postgres + Redis + an S3 bucket).

## Required environment

Set these on the host (secrets via the platform's secret store — never commit
real values):

| Var | Purpose |
|-----|---------|
| `DATABASE_URL` | `postgresql+asyncpg://USER:PASS@HOST:5432/truematch` |
| `REDIS_URL` | Celery broker/result backend |
| `JWT_SECRET` | `python -c "import secrets;print(secrets.token_urlsafe(48))"` |
| `ENCRYPTION_KEY` | base64 32 bytes — **required**; rotating needs a re-encrypt plan |
| `ANTHROPIC_API_KEY` | LLM access |
| `ANTHROPIC_MODEL` | capability verdict — `claude-sonnet-4-6` |
| `ANTHROPIC_FAST_MODEL` | extraction/secondary — `claude-haiku-4-5-20251001` |
| `CORS_ORIGINS` | `https://truematch.digital,https://www.truematch.digital` |
| `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` | billing → entitlement |

## File storage (needed for volume)

Local disk doesn't work across multiple workers. Set S3 and uploads move to
object storage automatically (already coded, server-side encrypted):

```
S3_BUCKET=truematch-uploads
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-southeast-1
# S3_KMS_KEY_ID=         # optional SSE-KMS
TRUEMATCH_COST_LEDGER=/var/lib/truematch/llm_cost.jsonl   # optional per-call cost log
```

## Google Drive auto-ingestion

Each candidate submission is a **Drive subfolder containing one CV and one JD**
(explicit pairing). The `poll-drive` beat task pulls new subfolders, pairs the
files, and runs the standard assessment pipeline. Disabled until configured:

```
DRIVE_INGEST_ENABLED=true
DRIVE_INGEST_FOLDER_ID=<root folder id whose subfolders are submissions>
DRIVE_INGEST_ACCESS_TOKEN=<OAuth2 bearer (service account/user) with read access>
DRIVE_INGEST_POLL_SECONDS=120
```

Idempotent (dedups on `Position.external_ref`), so re-polls never duplicate.

## Handling volume

- **Workers**: `worker` runs `celery … --pool=threads --concurrency=N`. The
  threads pool suits IO-bound LLM calls — scale `N` and add worker replicas to
  your **Anthropic rate limit**, not CPU (the LLM is the ceiling, not the box).
- **Cost**: ~13 LLM calls per assessment (~$0.15 Haiku / ~$0.58 Sonnet). The
  circuit breaker + cost ledger guard spend; set per-day budget envs if needed.
- **Idempotency**: identical CV+JD reuse the prior result (input-hash cache).
- **Routing**: large-delta / advisory assessments auto-route to human review.
