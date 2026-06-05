#!/usr/bin/env bash
# Local backend staging for TrueMatch — API + Celery worker, bound to localhost.
# Postgres (brew postgresql@16) and Redis (brew redis) must be running.
# Usage:  ./run-local.sh        (Ctrl-C stops both API and worker)
set -euo pipefail
cd "$(dirname "$0")"

source .venv/bin/activate
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
export PYTHONPATH="$PWD"

# Load staging env (env vars take precedence over the app's .env defaults).
set -a
# shellcheck disable=SC1091
source .env.staging
set +a

echo "==> Applying migrations"
alembic upgrade head

echo "==> Creating inbox folders for autonomous agents"
mkdir -p inbox/cv/processed inbox/jd/processed

echo "==> Starting Celery worker (threads pool, localhost Redis)"
celery -A app.workers.celery_app.celery_app worker \
    --loglevel=info --pool=threads --concurrency=4 &
WORKER_PID=$!

echo "==> Starting Celery Beat (autonomous agent scheduler)"
celery -A app.workers.celery_app.celery_app beat \
    --loglevel=info --schedule /tmp/tm_beat_schedule.db &
BEAT_PID=$!

trap 'echo "stopping worker+beat"; kill "$WORKER_PID" "$BEAT_PID" 2>/dev/null || true' EXIT

echo "==> Starting API on http://127.0.0.1:8000  (docs: /docs)"
echo "==> Agent inboxes: ./inbox/cv/ (CVs)  ./inbox/jd/ (JD drafts)"
exec uvicorn app.main:app --host 127.0.0.1 --port 8000
