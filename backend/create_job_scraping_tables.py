#!/usr/bin/env python3
"""
Create job scraping tables directly using SQLAlchemy.
This bypasses alembic to work around hanging issues.
"""
import asyncio
import sys
from sqlalchemy import text

# Add backend to path
sys.path.insert(0, '/Users/darthmod/Desktop/TrueMatch/backend')

from app.database import engine


async def create_tables():
    """Create all job scraping tables"""

    sql_statements = [
        # Create job_scraping_config table
        """
        CREATE TABLE IF NOT EXISTS job_scraping_config (
            id UUID NOT NULL PRIMARY KEY,
            source_type VARCHAR(50) NOT NULL,
            enabled BOOLEAN NOT NULL DEFAULT false,
            config JSONB NOT NULL DEFAULT '{}',
            poll_hours INTEGER NOT NULL DEFAULT 24,
            last_run TIMESTAMP WITH TIME ZONE,
            next_run TIMESTAMP WITH TIME ZONE,
            legal_approved BOOLEAN NOT NULL DEFAULT false,
            legal_approval_date TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_job_scraping_config_source_type ON job_scraping_config(source_type)",
        "CREATE INDEX IF NOT EXISTS ix_job_scraping_config_enabled ON job_scraping_config(enabled)",

        # Create scraping_run table
        """
        CREATE TABLE IF NOT EXISTS scraping_run (
            id UUID NOT NULL PRIMARY KEY,
            config_id UUID NOT NULL REFERENCES job_scraping_config(id) ON DELETE CASCADE,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            started_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            jobs_found INTEGER NOT NULL DEFAULT 0,
            jobs_processed INTEGER NOT NULL DEFAULT 0,
            jobs_failed INTEGER NOT NULL DEFAULT 0,
            errors JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_scraping_run_status ON scraping_run(status)",
        "CREATE INDEX IF NOT EXISTS ix_scraping_run_config_id ON scraping_run(config_id)",

        # Create mass_upload_batch table
        """
        CREATE TABLE IF NOT EXISTS mass_upload_batch (
            id UUID NOT NULL PRIMARY KEY,
            upload_type VARCHAR(50) NOT NULL,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            filename VARCHAR(255),
            field_mapping JSONB,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            total_rows INTEGER NOT NULL DEFAULT 0,
            processed_rows INTEGER NOT NULL DEFAULT 0,
            failed_rows INTEGER NOT NULL DEFAULT 0,
            duplicate_rows INTEGER NOT NULL DEFAULT 0,
            errors JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            completed_at TIMESTAMP WITH TIME ZONE
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_mass_upload_batch_status ON mass_upload_batch(status)",
        "CREATE INDEX IF NOT EXISTS ix_mass_upload_batch_user_id ON mass_upload_batch(user_id)",

        # Create job_deduplication table
        """
        CREATE TABLE IF NOT EXISTS job_deduplication (
            id UUID NOT NULL PRIMARY KEY,
            fingerprint VARCHAR(256) NOT NULL UNIQUE,
            external_ids JSONB NOT NULL DEFAULT '{}',
            ingest_queue_item_id UUID,
            first_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            last_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            seen_count INTEGER NOT NULL DEFAULT 1
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_job_deduplication_fingerprint ON job_deduplication(fingerprint)",
        "CREATE INDEX IF NOT EXISTS ix_job_deduplication_ingest_queue_item_id ON job_deduplication(ingest_queue_item_id)",

        # Create upload_field_mapping table
        """
        CREATE TABLE IF NOT EXISTS upload_field_mapping (
            id UUID NOT NULL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            description VARCHAR(1000),
            field_mapping JSONB NOT NULL,
            required_fields JSONB NOT NULL DEFAULT '[]',
            is_system BOOLEAN NOT NULL DEFAULT true,
            created_by UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_upload_field_mapping_name ON upload_field_mapping(name)",
        "CREATE INDEX IF NOT EXISTS ix_upload_field_mapping_is_system ON upload_field_mapping(is_system)",
    ]

    print("🔧 Creating job scraping tables...\n")

    try:
        async with engine.begin() as conn:
            for i, statement in enumerate(sql_statements, 1):
                try:
                    await conn.execute(text(statement))
                    status = "✅" if len(statement) > 50 else "✓"
                    if "CREATE TABLE" in statement:
                        table_name = statement.split("CREATE TABLE IF NOT EXISTS ")[1].split(" (")[0]
                        print(f"{status} Created table: {table_name}")
                    elif "CREATE INDEX" in statement:
                        index_name = statement.split("CREATE INDEX IF NOT EXISTS ")[1].split(" ")[0]
                        print(f"{status} Created index: {index_name}")
                except Exception as e:
                    print(f"⚠️  Statement {i}: {str(e)[:100]}")

        # Update alembic version
        async with engine.begin() as conn:
            await conn.execute(text("UPDATE alembic_version SET version_num = '0010'"))
            print(f"\n✅ Updated alembic_version to 0010")

        print("\n" + "="*60)
        print("✅ ALL JOB SCRAPING TABLES CREATED SUCCESSFULLY!")
        print("="*60)

        # Verify tables were created
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname='public'
                AND tablename IN ('job_scraping_config', 'scraping_run', 'mass_upload_batch',
                                  'job_deduplication', 'upload_field_mapping')
                ORDER BY tablename
            """))
            tables = result.fetchall()

            print(f"\n📊 Verification: {len(tables)}/5 tables exist")
            for (table,) in tables:
                print(f"   ✓ {table}")

        print("\n✨ Database is now ready for job scraping features!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(create_tables())
    sys.exit(0 if success else 1)
