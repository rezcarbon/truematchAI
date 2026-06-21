"""Shared test configuration.

Force deterministic mock fixtures for all engine tests (no network), and ensure
governance env overrides from the host shell do not leak into tests.
"""
from __future__ import annotations

import os
import pytest
from uuid import uuid4

# Must be set before app.config is imported anywhere.
os.environ.setdefault("LLM_FORCE_MOCK", "true")
# Tests use the deterministic lexical matcher (no model download / network).
os.environ.setdefault("SEMANTIC_USE_EMBEDDINGS", "false")
for _k in (
    "GOVERNANCE_COHERENCE_THRESHOLD",
    "GOVERNANCE_CONSISTENCY_BOUND",
    "GOVERNANCE_FIDELITY_THRESHOLD",
    "GOVERNANCE_COUNTER_REC_DELTA",
):
    os.environ.pop(_k, None)


# Import after environment is set
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
import asyncio
from typing import AsyncGenerator, Generator

from app.main import app
from app.database import get_session, Base
from app.models.user import User
from app.models.company import Company
from app.core.security import create_access_token


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for session-scoped async fixtures."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def sync_db_session() -> Generator[Session, None, None]:
    """Create a synchronous test database session with clean tables for each test.

    Creates an ephemeral PostgreSQL database using psycopg (sync driver),
    initializes all tables from models' metadata, provides a clean session
    for synchronous tests (e.g., Celery task tests), and ensures proper
    cleanup/rollback after the test completes.

    Uses the local PostgreSQL instance (expected at localhost:5432).
    """
    import time
    import psycopg

    # Generate a unique test database name with timestamp and random suffix
    timestamp = str(int(time.time() * 1000000) % 1000000).zfill(6)
    test_db_name = f"test_sync_db_{timestamp}_{uuid4().hex[:8]}"

    # Default PostgreSQL connection parameters
    db_host = os.environ.get("TEST_DB_HOST", "localhost")
    db_port = int(os.environ.get("TEST_DB_PORT", "5432"))
    db_user = os.environ.get("TEST_DB_USER", os.environ.get("USER", "postgres"))
    db_password = os.environ.get("TEST_DB_PASSWORD", "")

    # Build connection string for psycopg
    if db_password:
        psycopg_conn_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/postgres"
    else:
        psycopg_conn_string = f"postgresql://{db_user}@{db_host}:{db_port}/postgres"

    # Create the test database
    try:
        with psycopg.connect(psycopg_conn_string) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE {test_db_name}")
    except Exception as e:
        raise RuntimeError(
            f"Failed to create test database {test_db_name}. "
            f"Ensure PostgreSQL is running at {db_host}:{db_port}. "
            f"Error: {e}"
        ) from e

    # Build the sync connection string for the test database
    sync_db_url = (
        f"postgresql+psycopg://{db_user}"
        f"{':' + db_password if db_password else ''}@{db_host}:{db_port}/{test_db_name}"
    )

    # Create sync engine for the test
    engine = create_engine(sync_db_url, echo=False, future=True)

    # Create all tables defined in Base.metadata
    with engine.begin() as conn:
        try:
            Base.metadata.drop_all(conn)
        except Exception:
            # Log but don't fail - might be first run
            pass

    # Ensure schema is fresh by recreating tables
    with engine.begin() as conn:
        try:
            Base.metadata.create_all(conn)
        except exc.ProgrammingError as e:
            # If the error is about duplicate objects, it means there's a schema issue
            if "already exists" in str(e):
                raise RuntimeError(
                    f"Tables/indices exist after drop_all! "
                    f"Error: {e}. Database={test_db_name}."
                ) from e
            raise

    # Create a session factory for the test
    TestingSessionLocal = sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
        autoflush=False,
    )

    # Create and yield a session for the test
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        # Rollback any uncommitted changes after test completes
        session.rollback()
        session.close()

    # Cleanup: drop all tables and dispose of engine
    try:
        with engine.begin() as conn:
            Base.metadata.drop_all(conn)
    except Exception:
        # Ignore errors during cleanup
        pass
    finally:
        engine.dispose()

    # Drop the test database
    try:
        with psycopg.connect(psycopg_conn_string) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                # Disconnect all sessions from the database before dropping it
                try:
                    cur.execute(
                        f"SELECT pg_terminate_backend(pg_stat_activity.pid) "
                        f"FROM pg_stat_activity "
                        f"WHERE pg_stat_activity.datname = '{test_db_name}' "
                        f"AND pid <> pg_backend_pid();"
                    )
                except Exception:
                    pass  # Ignore termination errors

                # Drop the database
                cur.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
    except Exception as e:
        # Log but don't fail - the next test might pass
        print(f"WARNING: Failed to drop test database {test_db_name}: {e}")


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with clean tables for each test.

    Creates an ephemeral async PostgreSQL database, initializes all tables from
    models' metadata, provides a clean async session for the test, and ensures
    proper cleanup/rollback after the test completes.

    Uses the local PostgreSQL instance (expected at localhost:5432), creating
    a unique test database for each test and cleaning it up afterward.
    """
    import uuid
    import asyncpg
    import time

    # Generate a unique test database name with timestamp and random suffix
    timestamp = str(int(time.time() * 1000000) % 1000000).zfill(6)
    test_db_name = f"test_db_{timestamp}_{uuid.uuid4().hex[:8]}"

    # Default PostgreSQL connection parameters
    db_host = os.environ.get("TEST_DB_HOST", "localhost")
    db_port = int(os.environ.get("TEST_DB_PORT", "5432"))
    db_user = os.environ.get("TEST_DB_USER", os.environ.get("USER", "postgres"))
    db_password = os.environ.get("TEST_DB_PASSWORD", "")

    # Build the asyncpg connection string (without scheme for asyncpg.connect)
    if db_password:
        asyncpg_conn_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/postgres"
    else:
        asyncpg_conn_string = f"postgresql://{db_user}@{db_host}:{db_port}/postgres"

    # Create the test database
    try:
        conn = await asyncpg.connect(asyncpg_conn_string)
        await conn.execute(f"CREATE DATABASE {test_db_name}")
        await conn.close()
    except Exception as e:
        raise RuntimeError(
            f"Failed to create test database {test_db_name}. "
            f"Ensure PostgreSQL is running at {db_host}:{db_port}. "
            f"Error: {e}"
        ) from e

    # Build the async connection string for the test database
    async_db_url = (
        f"postgresql+asyncpg://{db_user}"
        f"{':' + db_password if db_password else ''}@{db_host}:{db_port}/{test_db_name}"
    )

    # Create async engine for the test
    engine = create_async_engine(
        async_db_url,
        echo=False,
        future=True,
    )

    # Create all tables defined in Base.metadata
    async with engine.begin() as conn:
        # Drop all existing tables to ensure a clean slate
        try:
            await conn.run_sync(Base.metadata.drop_all)
        except Exception:
            # Log but don't fail - might be first run
            pass

    # Close the engine and reconnect to ensure schema is fresh
    await engine.dispose()

    # Reconnect and create tables
    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.create_all)
        except exc.ProgrammingError as e:
            # If the error is about duplicate objects, it means there's a schema issue
            if "already exists" in str(e):
                raise RuntimeError(
                    f"Tables/indices exist after drop_all! "
                    f"Error: {e}. Database={test_db_name}."
                ) from e
            raise

    # Create a session factory for the test
    AsyncTestingSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    # Create and yield a session for the test
    async with AsyncTestingSessionLocal() as session:
        yield session
        # Rollback any uncommitted changes after test completes
        await session.rollback()

    # Cleanup: drop all tables and dispose of engine
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    except Exception:
        # Ignore errors during cleanup
        pass
    finally:
        await engine.dispose()

    # Drop the test database
    try:
        conn = await asyncpg.connect(asyncpg_conn_string)
        # Disconnect all sessions from the database before dropping it
        try:
            await conn.execute(
                f"SELECT pg_terminate_backend(pg_stat_activity.pid) "
                f"FROM pg_stat_activity "
                f"WHERE pg_stat_activity.datname = '{test_db_name}' "
                f"AND pid <> pg_backend_pid();"
            )
        except Exception:
            pass  # Ignore termination errors

        # Drop the database
        await conn.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
        await conn.close()
    except Exception as e:
        # Log but don't fail - the next test might pass
        print(f"WARNING: Failed to drop test database {test_db_name}: {e}")


@pytest.fixture
async def test_async_db(db_session: AsyncSession):
    """Async session FACTORY bound to the same per-test database as db_session.

    Some tests open several short-lived sessions within one test, using
    ``async with test_async_db() as session: ...``. Returning the
    async_sessionmaker (callable -> AsyncSession, which is itself an async
    context manager) supports exactly that, on the same event loop and the same
    ephemeral DB that db_session created.
    """
    return async_sessionmaker(bind=db_session.bind, expire_on_commit=False)


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[TestClient, None]:
    """Create a FastAPI test client with database session override.

    The client uses the same db_session as tests, allowing API calls to
    interact with test data and assertions to verify database state.

    Note: This fixture is async because it depends on the async db_session
    fixture. Tests can use it as a regular fixture (pytest-asyncio handles it).
    """

    # The app (under TestClient) runs on its OWN event loop, separate from
    # pytest-asyncio's loop that owns `db_session`. Sharing the session object
    # across loops raises "Future attached to a different loop". Instead, point
    # the app at the SAME per-test database via a fresh engine created lazily
    # inside the app's loop (NullPool so no cross-loop connection reuse).
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    test_db_url = db_session.bind.url.render_as_string(hide_password=False)
    _state: dict = {}

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        """Yield a session on the app's loop, bound to the per-test database."""
        if "maker" not in _state:
            engine = create_async_engine(test_db_url, poolclass=NullPool)
            _state["maker"] = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with _state["maker"]() as session:
            yield session
            # Mirror app.database.get_session: persist successful work so the
            # test's own db_session (a different engine) can observe it.
            try:
                await session.commit()
            except Exception:
                await session.rollback()

    # Override BOTH session dependencies. Routes depend on app.deps.get_db,
    # which calls get_session() as a plain function — so overriding only
    # get_session never took effect and every client-fixture test silently hit
    # the REAL database (the root cause of the 401-user-not-found and
    # 409-email-exists failure classes).
    from app.deps import get_db as _deps_get_db

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[_deps_get_db] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    # Cleanup: remove all dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
async def company(db_session):
    """Create a test company in the test database."""
    company = Company(
        name="Test Company",
        domain="test.example.com",
        plan="enterprise",
    )
    db_session.add(company)
    await db_session.commit()
    return company


@pytest.fixture
async def admin_user(db_session, company):
    """Create an admin user in the test database."""
    user = User(
        email=f"admin_test_{uuid4()}@test.com",
        password_hash="hash",
        role="admin",
        company_id=company.id,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def recruiter_user(db_session, company):
    """Create a recruiter user in the test database."""
    user = User(
        email=f"recruiter_test_{uuid4()}@test.com",
        password_hash="hash",
        role="recruiter",
        company_id=company.id,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def admin_token(admin_user):
    """Create an admin JWT token."""
    return create_access_token(subject=str(admin_user.id), role="admin")


@pytest.fixture
async def recruiter_token(recruiter_user):
    """Create a recruiter JWT token."""
    return create_access_token(subject=str(recruiter_user.id), role="recruiter")


# Session-level fixture to mock health checks by default for tests
# that don't explicitly monkeypatch them
@pytest.fixture(scope="session", autouse=True)
def _setup_default_health_mocks():
    """Set up default health check mocks that can be overridden by tests."""
    from app.core import health

    # Create async mock functions that return True by default
    async def mock_check_db():
        return True

    async def mock_check_redis():
        return True

    async def mock_check_s3():
        return True

    async def mock_check_llm():
        return True

    async def mock_check_singpass():
        return True

    # Store original functions so tests can restore them if needed
    originals = {
        'check_db': health.check_db,
        'check_redis': health.check_redis,
        'check_s3': health.check_s3,
        'check_llm': health.check_llm,
        'check_singpass': health.check_singpass,
    }

    # Apply default mocks
    health.check_db = mock_check_db
    health.check_redis = mock_check_redis
    health.check_s3 = mock_check_s3
    health.check_llm = mock_check_llm
    health.check_singpass = mock_check_singpass

    yield originals

    # Restore originals after all tests
    for name, original in originals.items():
        setattr(health, name, original)
