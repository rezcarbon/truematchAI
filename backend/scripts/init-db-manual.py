#!/usr/bin/env python3
"""
Emergency Database Initialization Script
Bypasses Alembic migrations and directly creates all necessary tables from SQLAlchemy models.
Use only when migrations have failed and database is empty.

Usage:
  python scripts/init-db-manual.py

Set DATABASE_URL environment variable before running.
"""
import sys
import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.pool import NullPool

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import Base, engine as default_engine

def init_database():
    """Initialize database by creating all tables from SQLAlchemy models."""

    # Create engine with explicit URL from settings
    db_url = settings.database_url

    # Convert async URL to sync for initialization
    sync_url = db_url.replace("+asyncpg", "").replace("?ssl=require", "").replace("&ssl=require", "")
    sync_url = sync_url.replace("postgresql://", "postgresql+psycopg://")
    if "sslmode" not in sync_url:
        if "?" in sync_url:
            sync_url += "&sslmode=require"
        else:
            sync_url += "?sslmode=require"

    print(f"📦 Initializing database...")
    print(f"   Database URL: {sync_url[:50]}...")

    try:
        init_engine = create_engine(sync_url, poolclass=NullPool, echo=False)

        # Test connection
        with init_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")

        # Check what tables already exist
        inspector = inspect(init_engine)
        existing_tables = set(inspector.get_table_names())

        if existing_tables:
            print(f"⚠️  Database has {len(existing_tables)} existing tables")
            print(f"   Tables: {', '.join(sorted(existing_tables)[:10])}")
            print("   Skipping table creation (database already initialized)")
            return True

        print("🔨 Creating tables from SQLAlchemy models...")
        Base.metadata.create_all(init_engine)

        # Verify tables were created
        inspector = inspect(init_engine)
        new_tables = set(inspector.get_table_names())

        print(f"✅ Created {len(new_tables)} tables:")
        for table in sorted(new_tables):
            col_count = len(inspector.get_columns(table))
            print(f"   - {table} ({col_count} columns)")

        # Verify critical columns exist
        critical_checks = [
            ("users", "singpass_id_bidx"),
            ("users", "email"),
            ("resumes", "id"),
            ("audit_trail", "id"),
        ]

        print("\n🔍 Verifying critical schema elements...")
        all_good = True
        for table, column in critical_checks:
            try:
                columns = {c['name'] for c in inspector.get_columns(table)}
                if column in columns:
                    print(f"   ✅ {table}.{column} exists")
                else:
                    print(f"   ❌ {table}.{column} MISSING")
                    all_good = False
            except Exception as e:
                print(f"   ❌ Error checking {table}.{column}: {e}")
                all_good = False

        if all_good:
            print("\n🎉 Database initialization complete!")
            return True
        else:
            print("\n⚠️  Some critical columns are missing. Check the output above.")
            return False

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
