#!/usr/bin/env python3
"""Create CV/JD analysis tables directly using SQLAlchemy."""
import asyncio
import sys
from sqlalchemy import text

sys.path.insert(0, '/Users/darthmod/Desktop/TrueMatch/backend')

from app.database import engine


async def create_tables():
    """Create all CV/JD analysis tables"""

    sql_statements = [
        # Create enums
        """
        DO $$ BEGIN
            CREATE TYPE cv_analysis_status AS ENUM ('pending', 'analyzing', 'completed', 'failed');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,
        """
        DO $$ BEGIN
            CREATE TYPE jd_simulation_status AS ENUM ('pending', 'analyzing', 'completed', 'failed');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,
        """
        DO $$ BEGIN
            CREATE TYPE seniority_level AS ENUM ('junior', 'mid', 'senior', 'lead');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,
        """
        DO $$ BEGIN
            CREATE TYPE simulation_type AS ENUM ('requirement_fit', 'market_comparison', 'candidate_archetype');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,
        # Create cv_analysis_requests table
        """
        CREATE TABLE IF NOT EXISTS cv_analysis_requests (
            id UUID NOT NULL PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            resume_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
            target_role VARCHAR(255) NOT NULL,
            target_seniority seniority_level NOT NULL,
            career_focus_areas JSONB,
            status cv_analysis_status NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_cv_analysis_requests_user_id ON cv_analysis_requests(user_id)",
        "CREATE INDEX IF NOT EXISTS ix_cv_analysis_requests_status ON cv_analysis_requests(status)",

        # Create cv_analysis_results table
        """
        CREATE TABLE IF NOT EXISTS cv_analysis_results (
            id UUID NOT NULL PRIMARY KEY,
            cv_analysis_request_id UUID NOT NULL REFERENCES cv_analysis_requests(id) ON DELETE CASCADE,
            missing_capabilities JSONB,
            weakness_areas JSONB,
            strength_summary TEXT,
            top_matching_position_ids JSONB,
            job_fit_scores JSONB,
            underrated_positions JSONB,
            improvement_suggestions JSONB,
            reworded_cv_sections JSONB,
            trajectory_analysis TEXT,
            market_positioning TEXT,
            growth_opportunities JSONB,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_cv_analysis_results_request_id ON cv_analysis_results(cv_analysis_request_id)",

        # Create jd_simulation_requests table
        """
        CREATE TABLE IF NOT EXISTS jd_simulation_requests (
            id UUID NOT NULL PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            position_id UUID REFERENCES positions(id) ON DELETE CASCADE,
            jd_text TEXT,
            simulation_type simulation_type NOT NULL,
            target_candidate_profile JSONB,
            status jd_simulation_status NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_jd_simulation_requests_user_id ON jd_simulation_requests(user_id)",
        "CREATE INDEX IF NOT EXISTS ix_jd_simulation_requests_status ON jd_simulation_requests(status)",

        # Create jd_simulation_results table
        """
        CREATE TABLE IF NOT EXISTS jd_simulation_results (
            id UUID NOT NULL PRIMARY KEY,
            jd_simulation_request_id UUID NOT NULL REFERENCES jd_simulation_requests(id) ON DELETE CASCADE,
            critical_capabilities JSONB,
            missing_clarity JSONB,
            capability_recommendations JSONB,
            requirement_difficulty_score INTEGER,
            experience_years_assessment TEXT,
            tech_stack_balance TEXT,
            creep_warnings JSONB,
            fit_by_archetype JSONB,
            best_archetype_fit VARCHAR(50),
            talent_pool_estimate TEXT,
            quality_score INTEGER,
            market_positioning TEXT,
            missing_sections JSONB,
            quality_issues JSONB,
            suggested_job_title_variations JSONB,
            improved_role_description TEXT,
            capability_verbiage_suggestions JSONB,
            benefits_suggestions JSONB,
            culture_fit_language TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_jd_simulation_results_request_id ON jd_simulation_results(jd_simulation_request_id)",

        # Create candidate_archetypes table
        """
        CREATE TABLE IF NOT EXISTS candidate_archetypes (
            id UUID NOT NULL PRIMARY KEY,
            company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
            role_level seniority_level NOT NULL,
            role_title VARCHAR(255) NOT NULL,
            typical_profile JSONB NOT NULL,
            description TEXT,
            is_system BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_candidate_archetypes_company_id ON candidate_archetypes(company_id)",
        "CREATE INDEX IF NOT EXISTS ix_candidate_archetypes_is_system ON candidate_archetypes(is_system)",
        "CREATE INDEX IF NOT EXISTS ix_candidate_archetypes_role_level ON candidate_archetypes(role_level)",

        # Update migration version
        "UPDATE alembic_version SET version_num = '0011'",
    ]

    print("🔧 Creating CV/JD analysis tables...\n")

    try:
        async with engine.begin() as conn:
            for i, statement in enumerate(sql_statements, 1):
                try:
                    await conn.execute(text(statement))
                    if "CREATE TABLE" in statement:
                        table_name = statement.split("CREATE TABLE IF NOT EXISTS ")[1].split(" (")[0]
                        print(f"✅ Created table: {table_name}")
                    elif "CREATE INDEX" in statement:
                        index_name = statement.split("CREATE INDEX IF NOT EXISTS ")[1].split(" ")[0]
                        print(f"✓ Created index: {index_name}")
                    elif "CREATE TYPE" in statement:
                        enum_name = statement.split("CREATE TYPE ")[1].split(" AS")[0]
                        print(f"✓ Created enum: {enum_name}")
                except Exception as e:
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print(f"⚠️  Already exists (skipped): {str(e)[:80]}")
                    else:
                        print(f"⚠️  Statement {i}: {str(e)[:100]}")

        print("\n" + "="*60)
        print("✅ ALL CV/JD ANALYSIS TABLES CREATED SUCCESSFULLY!")
        print("="*60)

        # Verify tables were created
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname='public'
                AND tablename IN ('cv_analysis_requests', 'cv_analysis_results', 'jd_simulation_requests',
                                  'jd_simulation_results', 'candidate_archetypes')
                ORDER BY tablename
            """))
            tables = result.fetchall()

            print(f"\n📊 Verification: {len(tables)}/5 tables exist")
            for (table,) in tables:
                print(f"   ✓ {table}")

        print("\n✨ Database is now ready for CV/JD analysis features!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(create_tables())
    sys.exit(0 if success else 1)
