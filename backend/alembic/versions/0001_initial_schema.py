"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-31 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role = postgresql.ENUM(
        "candidate", "recruiter", "admin", name="user_role", create_type=True
    )
    position_status = postgresql.ENUM(
        "draft", "open", "closed", "archived", name="position_status", create_type=True
    )
    assessment_status = postgresql.ENUM(
        "pending", "running", "completed", "failed", name="assessment_status", create_type=True
    )
    decision_outcome = postgresql.ENUM(
        "advance", "reject", "hold", "interview", "hire", name="decision_outcome",
        create_type=True,
    )
    profile_visibility = postgresql.ENUM(
        "private", "link", "public", name="profile_visibility", create_type=True
    )

    # --- companies ---------------------------------------------------------
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("plan", sa.String(64), nullable=False, server_default="free"),
        sa.Column("governance_config", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_companies_domain", "companies", ["domain"])

    # --- users -------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("singpass_id", sa.String(64), nullable=True),
        sa.Column("role", user_role, nullable=False, server_default="candidate"),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_company_id", "users", ["company_id"])
    op.create_index("ix_users_singpass_id", "users", ["singpass_id"])

    # --- resumes -----------------------------------------------------------
    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_id", sa.String(512), nullable=True),
        sa.Column("file_type", sa.String(64), nullable=True),
        sa.Column("parsed_data", postgresql.JSONB, nullable=True),
        sa.Column("raw_narrative", sa.Text, nullable=True),
        sa.Column("supplementary", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])

    # --- positions ---------------------------------------------------------
    op.create_table(
        "positions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("parsed_requirements", postgresql.JSONB, nullable=True),
        sa.Column("jd_quality_score", sa.Integer, nullable=True),
        sa.Column("jd_issues", postgresql.JSONB, nullable=True),
        sa.Column("status", position_status, nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_positions_company_id", "positions", ["company_id"])
    op.create_index("ix_positions_status", "positions", ["status"])

    # --- assessments -------------------------------------------------------
    op.create_table(
        "assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "resume_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "position_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("positions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", assessment_status, nullable=False, server_default="pending"),
        sa.Column("traditional_score", sa.Integer, nullable=True),
        sa.Column("traditional_detail", postgresql.JSONB, nullable=True),
        sa.Column("capability_score", sa.Integer, nullable=True),
        sa.Column("capability_components", postgresql.JSONB, nullable=True),
        sa.Column("capability_narrative", sa.Text, nullable=True),
        sa.Column("capability_evidence", postgresql.JSONB, nullable=True),
        sa.Column("trajectory_data", postgresql.JSONB, nullable=True),
        sa.Column("trajectory_narrative", sa.Text, nullable=True),
        sa.Column("counter_rec_triggered", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("counter_rec_reasoning", sa.Text, nullable=True),
        sa.Column("counter_rec_evidence", postgresql.JSONB, nullable=True),
        sa.Column("jd_quality_score", sa.Integer, nullable=True),
        sa.Column("jd_issues", postgresql.JSONB, nullable=True),
        sa.Column("governance_coherence", postgresql.JSONB, nullable=True),
        sa.Column("governance_consistency", postgresql.JSONB, nullable=True),
        sa.Column("governance_fidelity", postgresql.JSONB, nullable=True),
        sa.Column("governance_bias_flags", postgresql.JSONB, nullable=True),
        sa.Column("governance_audit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("score_delta", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_assessments_user_id", "assessments", ["user_id"])
    op.create_index("ix_assessments_position_id", "assessments", ["position_id"])
    op.create_index("ix_assessments_resume_id", "assessments", ["resume_id"])
    op.create_index("ix_assessments_status", "assessments", ["status"])

    # --- decisions ---------------------------------------------------------
    op.create_table(
        "decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "position_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("positions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "recruiter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("decision", decision_outcome, nullable=False),
        sa.Column("ai_recommendation_followed", sa.Boolean, nullable=True),
        sa.Column("override_reasoning", sa.Text, nullable=True),
        sa.Column("cultural_fit_notes", sa.Text, nullable=True),
        sa.Column("interview_notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_decisions_assessment_id", "decisions", ["assessment_id"])
    op.create_index("ix_decisions_position_id", "decisions", ["position_id"])

    # --- audit_trail -------------------------------------------------------
    op.create_table(
        "audit_trail",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("event_data", postgresql.JSONB, nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_type", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_trail_assessment_id", "audit_trail", ["assessment_id"])
    op.create_index("ix_audit_trail_event_type", "audit_trail", ["event_type"])
    op.create_index("ix_audit_trail_created_at", "audit_trail", ["created_at"])

    # --- capability_profiles ----------------------------------------------
    op.create_table(
        "capability_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("narrative", sa.Text, nullable=True),
        sa.Column("trajectory_summary", postgresql.JSONB, nullable=True),
        sa.Column("top_capabilities", postgresql.JSONB, nullable=True),
        sa.Column("assessment_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("share_token", sa.String(64), nullable=True, unique=True),
        sa.Column("visibility", profile_visibility, nullable=False, server_default="private"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_capability_profiles_user_id", "capability_profiles", ["user_id"], unique=True)
    op.create_index(
        "ix_capability_profiles_share_token", "capability_profiles", ["share_token"], unique=True
    )


def downgrade() -> None:
    op.drop_table("capability_profiles")
    op.drop_table("audit_trail")
    op.drop_table("decisions")
    op.drop_table("assessments")
    op.drop_table("positions")
    op.drop_table("resumes")
    op.drop_table("users")
    op.drop_table("companies")

    for enum_name in (
        "profile_visibility",
        "decision_outcome",
        "assessment_status",
        "position_status",
        "user_role",
    ):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
