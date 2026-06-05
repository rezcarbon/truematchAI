"""Add CV analysis and JD simulation tables

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-03 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    seniority_level = postgresql.ENUM("junior", "mid", "senior", "lead", name="seniority_level")
    seniority_level.create(op.get_bind(), checkfirst=True)

    cv_analysis_status = postgresql.ENUM("pending", "analyzing", "completed", "failed", name="cv_analysis_status")
    cv_analysis_status.create(op.get_bind(), checkfirst=True)

    jd_simulation_status = postgresql.ENUM("pending", "analyzing", "completed", "failed", name="jd_simulation_status")
    jd_simulation_status.create(op.get_bind(), checkfirst=True)

    simulation_type = postgresql.ENUM("requirement_fit", "market_comparison", "candidate_archetype", name="simulation_type")
    simulation_type.create(op.get_bind(), checkfirst=True)

    # Create cv_analysis_requests table
    op.create_table(
        "cv_analysis_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_role", sa.String(255), nullable=False),
        sa.Column("target_seniority", postgresql.ENUM("junior", "mid", "senior", "lead", name="seniority_level", create_type=False), nullable=False),
        sa.Column("career_focus_areas", postgresql.JSONB(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("pending", "analyzing", "completed", "failed", name="cv_analysis_status", create_type=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["resume_id"],
            ["resumes.id"],
            ondelete="CASCADE",
        ),
        sa.Index("ix_cv_analysis_requests_user_id", "user_id"),
        sa.Index("ix_cv_analysis_requests_status", "status"),
    )

    # Create cv_analysis_results table
    op.create_table(
        "cv_analysis_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cv_analysis_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("missing_capabilities", postgresql.JSONB(), nullable=True),
        sa.Column("weakness_areas", postgresql.JSONB(), nullable=True),
        sa.Column("strength_summary", sa.Text(), nullable=True),
        sa.Column("top_matching_position_ids", postgresql.JSONB(), nullable=True),
        sa.Column("job_fit_scores", postgresql.JSONB(), nullable=True),
        sa.Column("underrated_positions", postgresql.JSONB(), nullable=True),
        sa.Column("improvement_suggestions", postgresql.JSONB(), nullable=True),
        sa.Column("reworded_cv_sections", postgresql.JSONB(), nullable=True),
        sa.Column("trajectory_analysis", sa.Text(), nullable=True),
        sa.Column("market_positioning", sa.Text(), nullable=True),
        sa.Column("growth_opportunities", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["cv_analysis_request_id"],
            ["cv_analysis_requests.id"],
            ondelete="CASCADE",
        ),
        sa.Index("ix_cv_analysis_results_request_id", "cv_analysis_request_id"),
    )

    # Create jd_simulation_requests table
    op.create_table(
        "jd_simulation_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("jd_text", sa.Text(), nullable=True),
        sa.Column("simulation_type", postgresql.ENUM("requirement_fit", "market_comparison", "candidate_archetype", name="simulation_type", create_type=False ), nullable=False),
        sa.Column("target_candidate_profile", postgresql.JSONB(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("pending", "analyzing", "completed", "failed", name="jd_simulation_status", create_type=False ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["position_id"],
            ["positions.id"],
            ondelete="CASCADE",
        ),
        sa.Index("ix_jd_simulation_requests_user_id", "user_id"),
        sa.Index("ix_jd_simulation_requests_status", "status"),
    )

    # Create jd_simulation_results table
    op.create_table(
        "jd_simulation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("jd_simulation_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("critical_capabilities", postgresql.JSONB(), nullable=True),
        sa.Column("missing_clarity", postgresql.JSONB(), nullable=True),
        sa.Column("capability_recommendations", postgresql.JSONB(), nullable=True),
        sa.Column("requirement_difficulty_score", sa.Integer(), nullable=True),
        sa.Column("experience_years_assessment", sa.Text(), nullable=True),
        sa.Column("tech_stack_balance", sa.Text(), nullable=True),
        sa.Column("creep_warnings", postgresql.JSONB(), nullable=True),
        sa.Column("fit_by_archetype", postgresql.JSONB(), nullable=True),
        sa.Column("best_archetype_fit", sa.String(50), nullable=True),
        sa.Column("talent_pool_estimate", sa.Text(), nullable=True),
        sa.Column("quality_score", sa.Integer(), nullable=True),
        sa.Column("market_positioning", sa.Text(), nullable=True),
        sa.Column("missing_sections", postgresql.JSONB(), nullable=True),
        sa.Column("quality_issues", postgresql.JSONB(), nullable=True),
        sa.Column("suggested_job_title_variations", postgresql.JSONB(), nullable=True),
        sa.Column("improved_role_description", sa.Text(), nullable=True),
        sa.Column("capability_verbiage_suggestions", postgresql.JSONB(), nullable=True),
        sa.Column("benefits_suggestions", postgresql.JSONB(), nullable=True),
        sa.Column("culture_fit_language", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["jd_simulation_request_id"],
            ["jd_simulation_requests.id"],
            ondelete="CASCADE",
        ),
        sa.Index("ix_jd_simulation_results_request_id", "jd_simulation_request_id"),
    )

    # Create candidate_archetypes table
    op.create_table(
        "candidate_archetypes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("role_level", postgresql.ENUM("junior", "mid", "senior", "lead", name="seniority_level", create_type=False ), nullable=False),
        sa.Column("role_title", sa.String(255), nullable=False),
        sa.Column("typical_profile", postgresql.JSONB(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            ondelete="CASCADE",
        ),
        sa.Index("ix_candidate_archetypes_company_id", "company_id"),
        sa.Index("ix_candidate_archetypes_is_system", "is_system"),
        sa.Index("ix_candidate_archetypes_role_level", "role_level"),
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("candidate_archetypes")
    op.drop_table("jd_simulation_results")
    op.drop_table("jd_simulation_requests")
    op.drop_table("cv_analysis_results")
    op.drop_table("cv_analysis_requests")

    # Note: Don't drop enums as they may be used by other tables/migrations
    # and are managed separately in earlier migrations
