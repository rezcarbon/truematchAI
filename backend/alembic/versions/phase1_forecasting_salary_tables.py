"""Add Phase 1 tables for forecasting and salary benchmarking.

Migration for:
- forecast_results: Pipeline forecasting predictions
- salary_benchmarks: Market salary data
- compensation_offers: Offer records linked to salary benchmarks
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = "phase1_001_forecasting_salary"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create Phase 1 tables."""

    # Forecast results table
    op.create_table(
        "forecast_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("forecasted_fill_date", sa.DateTime(), nullable=False),
        sa.Column("estimated_days_to_fill", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("bottleneck_stage", sa.String(50), nullable=True),
        sa.Column("recommendations", postgresql.JSON(), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=False, server_default="v1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_forecast_results_position_id", "forecast_results", ["position_id"]
    )
    op.create_index(
        "ix_forecast_results_created_at", "forecast_results", ["created_at"]
    )

    # Salary benchmarks table
    op.create_table(
        "salary_benchmarks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_title", sa.String(255), nullable=False),
        sa.Column("level", sa.String(50), nullable=False),
        sa.Column("location", sa.String(255), nullable=False),
        sa.Column("min_salary", sa.Integer(), nullable=False),
        sa.Column("max_salary", sa.Integer(), nullable=False),
        sa.Column("median_salary", sa.Integer(), nullable=False),
        sa.Column("percentile_25", sa.Integer(), nullable=False),
        sa.Column("percentile_75", sa.Integer(), nullable=False),
        sa.Column("data_points", sa.Integer(), nullable=False),
        sa.Column("data_source", sa.String(50), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "role_title", "level", "location", name="uq_salary_benchmarks_role_level_location"
        ),
    )
    op.create_index(
        "ix_salary_benchmarks_role_title", "salary_benchmarks", ["role_title"]
    )
    op.create_index(
        "ix_salary_benchmarks_level", "salary_benchmarks", ["level"]
    )
    op.create_index(
        "ix_salary_benchmarks_location", "salary_benchmarks", ["location"]
    )
    op.create_index(
        "ix_salary_benchmarks_updated_at", "salary_benchmarks", ["updated_at"]
    )

    # Compensation offers table
    op.create_table(
        "compensation_offers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("salary_benchmark_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("offered_salary", sa.Integer(), nullable=False),
        sa.Column("market_median", sa.Integer(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("recommendation_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["candidate_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["salary_benchmark_id"], ["salary_benchmarks.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_compensation_offers_candidate_id", "compensation_offers", ["candidate_id"]
    )
    op.create_index(
        "ix_compensation_offers_position_id", "compensation_offers", ["position_id"]
    )
    op.create_index(
        "ix_compensation_offers_created_at", "compensation_offers", ["created_at"]
    )


def downgrade():
    """Drop Phase 1 tables."""
    op.drop_table("compensation_offers")
    op.drop_table("salary_benchmarks")
    op.drop_table("forecast_results")
