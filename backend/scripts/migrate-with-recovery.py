#!/usr/bin/env python3
"""
Robust Migration Runner with Error Recovery
Attempts to run Alembic migrations with detailed error handling and recovery options.

Usage:
  python scripts/migrate-with-recovery.py [--init-empty] [--skip-0024]

Options:
  --init-empty      Initialize empty database from SQLAlchemy models before running migrations
  --skip-0024       Skip migration 0024 (known problematic for fresh installs)
"""
import sys
import os
import subprocess
import json
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.pool import NullPool
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import Base

def get_sync_url():
    """Convert async database URL to sync URL for migrations."""
    db_url = settings.database_url
    sync_url = db_url.replace("+asyncpg", "").replace("?ssl=require", "").replace("&ssl=require", "")
    sync_url = sync_url.replace("postgresql://", "postgresql+psycopg://")
    if "sslmode" not in sync_url:
        if "?" in sync_url:
            sync_url += "&sslmode=require"
        else:
            sync_url += "?sslmode=require"
    return sync_url

def check_database_connection():
    """Verify database connection."""
    print("🔍 Checking database connection...")
    sync_url = get_sync_url()

    try:
        engine = create_engine(sync_url, poolclass=NullPool, echo=False)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def get_current_revision():
    """Get current Alembic revision from database."""
    print("📍 Checking current migration state...")
    sync_url = get_sync_url()

    try:
        engine = create_engine(sync_url, poolclass=NullPool, echo=False)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1"))
            row = result.fetchone()
            if row:
                current = row[0]
                print(f"   Current revision: {current}")
                return current
            else:
                print("   No migrations applied yet")
                return None
    except Exception as e:
        print(f"   alembic_version table not found (first run): {e}")
        return None

def init_empty_database():
    """Initialize empty database from SQLAlchemy models."""
    print("🔨 Initializing empty database from SQLAlchemy models...")
    sync_url = get_sync_url()

    try:
        engine = create_engine(sync_url, poolclass=NullPool, echo=False)
        Base.metadata.create_all(engine)
        print("✅ Database tables created from models")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False

def run_migrations(skip_0024=False):
    """Run Alembic migrations."""
    print("🚀 Running Alembic migrations...")

    if skip_0024:
        print("   ⚠️  Skipping migration 0024 as requested")
        # Mark 0024 as already applied without running it
        try:
            sync_url = get_sync_url()
            engine = create_engine(sync_url, poolclass=NullPool, echo=False)

            with engine.connect() as conn:
                conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('0024') ON CONFLICT DO NOTHING"))
                conn.commit()
            print("   ✅ Migration 0024 marked as applied")
        except Exception as e:
            print(f"   ⚠️  Could not mark 0024 as applied: {e}")

    # Run alembic upgrade head
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            print("✅ Migrations completed successfully")
            if result.stdout:
                print(f"   Output: {result.stdout[:200]}")
            return True
        else:
            print(f"❌ Migrations failed with return code {result.returncode}")
            if result.stdout:
                print(f"   STDOUT:\n{result.stdout}")
            if result.stderr:
                print(f"   STDERR:\n{result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Migrations timed out after 300 seconds")
        return False
    except Exception as e:
        print(f"❌ Failed to run migrations: {e}")
        return False

def verify_critical_schema():
    """Verify critical schema elements exist."""
    print("🔍 Verifying critical schema elements...")
    sync_url = get_sync_url()

    try:
        engine = create_engine(sync_url, poolclass=NullPool, echo=False)
        inspector = inspect(engine)

        critical_checks = [
            ("users", "singpass_id_bidx"),
            ("users", "email"),
            ("resumes", "id"),
            ("audit_trail", "id"),
        ]

        all_good = True
        for table, column in critical_checks:
            try:
                columns = {c['name'] for c in inspector.get_columns(table)}
                if column in columns:
                    print(f"   ✅ {table}.{column}")
                else:
                    print(f"   ❌ {table}.{column} MISSING")
                    all_good = False
            except Exception as e:
                print(f"   ❌ {table}.{column}: {e}")
                all_good = False

        return all_good
    except Exception as e:
        print(f"❌ Failed to verify schema: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Robust migration runner with recovery options")
    parser.add_argument("--init-empty", action="store_true", help="Initialize empty database from models")
    parser.add_argument("--skip-0024", action="store_true", help="Skip migration 0024")
    args = parser.parse_args()

    print("=" * 70)
    print("🔧 TRUEMATCH DATABASE MIGRATION RECOVERY")
    print("=" * 70)

    # Step 1: Check connection
    if not check_database_connection():
        print("\n❌ Cannot proceed without database connection")
        return False

    # Step 2: Check current state
    current_revision = get_current_revision()

    # Step 3: Initialize if requested and empty
    if args.init_empty or current_revision is None:
        if current_revision is None:
            print("\n💡 Database appears empty, initializing from models...")
            if not init_empty_database():
                print("\n❌ Failed to initialize database")
                return False

    # Step 4: Run migrations
    print()
    if not run_migrations(skip_0024=args.skip_0024):
        print("\n⚠️  Migrations had issues. Check the output above.")

    # Step 5: Verify critical schema
    print()
    schema_ok = verify_critical_schema()

    # Summary
    print("\n" + "=" * 70)
    if schema_ok:
        print("✅ DATABASE MIGRATION COMPLETE - All critical elements verified")
        print("=" * 70)
        return True
    else:
        print("❌ DATABASE MIGRATION INCOMPLETE - Some critical elements missing")
        print("=" * 70)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
