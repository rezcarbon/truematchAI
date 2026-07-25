"""Alembic environment.

Runs migrations against the configured DATABASE_URL. Uses a synchronous driver
(stripping +asyncpg) for the migration connection.
"""
from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.database import Base

# Import models so their metadata is registered on Base.
from app import models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Use a synchronous driver for migrations (psycopg v3, matching the worker).
# Strip +asyncpg and incompatible SSL params, then set psycopg dialect
_url = settings.database_url.replace("+asyncpg", "").replace("?ssl=require", "").replace("&ssl=require", "")
_sync_url = _url.replace("postgresql://", "postgresql+psycopg://")
if "?" not in _sync_url and ("ssl" not in _url):
    _sync_url += "?sslmode=require"
elif "?" in _sync_url and "sslmode" not in _sync_url:
    _sync_url += "&sslmode=require"
config.set_main_option("sqlalchemy.url", _sync_url)


def run_migrations_offline() -> None:
    context.configure(
        url=_sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
