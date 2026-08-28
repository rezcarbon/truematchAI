#!/usr/bin/env python3
"""Migration wrapper that handles DATABASE_URL conversion for Alembic."""
import os
import subprocess
import sys

# Get the async database URL from environment
db_url = os.environ.get('DATABASE_URL', '')

# Convert postgresql+asyncpg://... to postgresql://...
if 'postgresql+asyncpg://' in db_url:
    sync_db_url = db_url.replace('postgresql+asyncpg://', 'postgresql+psycopg://')
    # Remove sslmode=disable from URL as psycopg handles it differently
    sync_db_url = sync_db_url.replace('?sslmode=disable', '').replace('&sslmode=disable', '')
    os.environ['SQLALCHEMY_URL'] = sync_db_url

# Run alembic upgrade head
result = subprocess.run(['alembic', 'upgrade', 'head'], cwd='/app')
sys.exit(result.returncode)
