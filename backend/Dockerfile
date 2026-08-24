# TrueMatch backend image — runs both the API and the Celery worker
# (the command is overridden per service in docker-compose / orchestration).
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Build deps for psycopg/cryptography wheels (kept minimal).
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy source code
COPY app ./app
COPY pyproject.toml ./

# Install dependencies from requirements, not package installation
RUN pip install --upgrade pip && \
    pip install \
    'fastapi>=0.111' \
    'uvicorn[standard]>=0.30' \
    'sqlalchemy[asyncio]>=2.0.30' \
    'asyncpg>=0.29' \
    'alembic>=1.13' \
    'redis>=5.0' \
    'celery>=5.4' \
    'anthropic>=0.34' \
    'pydantic[email]>=2.7' \
    'pydantic-settings>=2.3' \
    'python-jose[cryptography]>=3.3' \
    'bcrypt>=4.1' \
    'python-multipart>=0.0.9' \
    'boto3>=1.34' \
    'aioboto3>=1.14' \
    'google-cloud-aiplatform>=1.0' \
    'pypdf>=4.2' \
    'python-docx>=1.1' \
    'psycopg[binary]>=3.1' \
    'httpx>=0.27' \
    'cryptography>=42.0' \
    'sentry-sdk[fastapi]>=2.0' \
    'prometheus-client>=0.20' \
    'model2vec>=0.3' \
    'stripe>=9,<13' \
    'aioimaplib>=1.1' \
    'aiosmtplib>=5.0' \
    'aiofiles>=23.0' \
    'watchdog>=4.0' \
    'reportlab>=4.0' && \
    # Remove any installed app/truematch packages to avoid conflicts
    pip uninstall -y truematch-backend app 2>/dev/null || true

# Ensure Python imports from the source directory (prepend to path)
ENV PYTHONPATH=/app:${PYTHONPATH}

COPY alembic.ini ./
COPY alembic ./alembic
COPY governance ./governance

# Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/livez || exit 1

# Default: API server. The worker service overrides this command.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
