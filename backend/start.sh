#!/bin/bash

echo "======================================"
echo "TrueMatch API Startup"
echo "======================================"
echo "Environment: ${ENVIRONMENT:-staging}"
echo "Port: ${PORT:-8000}"
echo "Database: ${DATABASE_URL:0:20}..."
echo "Redis: ${REDIS_URL:0:20}..."
echo ""

# Run migrations if DATABASE_URL is set, but don't fail if they fail
if [ -n "$DATABASE_URL" ]; then
  echo "Running database migrations..."
  alembic upgrade head || echo "⚠️  Migration warning (continuing anyway)"
  echo ""
fi

echo "Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
