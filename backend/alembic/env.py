"""Alembic environment.

Runs migrations against the configured DATABASE_URL. Uses a synchronous driver
(stripping +asyncpg) for the migration connection.
"""
from __future__ import annotations

from logging.config import fileConfig
from sqlalchemy import inspect, text

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
# Strip +asyncpg and all SSL params, keep the base connection clean
_base_url = (settings.database_url
    .replace("postgresql+asyncpg://", "postgresql+psycopg://")
    .split("?")[0]  # Remove all query params (SSL, sslmode, etc.)
)
config.set_main_option("sqlalchemy.url", _base_url)


def run_migrations_offline() -> None:
    context.configure(
        url=_base_url,
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
    with connectable.begin() as connection:
        # Check if alembic_version table exists
        inspector = inspect(connection)
        if "alembic_version" not in inspector.get_table_names():
            # Create the table if it doesn't exist
            connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)"))

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
