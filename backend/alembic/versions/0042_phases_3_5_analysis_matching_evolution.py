"""Phases 3-5: Analysis Agent, Matching Agent, Evolution Agent.

Revision ID: 0042
Revises: 0041_assessment_designer_phase_2
Create Date: 2026-07-15 22:00:00.000000

Phase 3: Analysis Agent - Score assessment responses
Phase 4: Matching Agent - Calculate job fit scores
Phase 5: Evolution Agent - Track outcomes and learn
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0042"
down_revision = "0041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create analysis_results, candidate_matches, and hiring_outcomes tables."""

    # Phase 3: AnalysisResult table
    op.create_table(
        "analysis_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_design_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending_analysis",
                "analyzing",
                "analysis_complete",
                "scoring_complete",
                "error",
                name="analysis_status",
            ),
            nullable=False,
            server_default="pending_analysis",
        ),
        sa.Column(
            "responses_analyzed",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="Individual response analysis",
        ),
        sa.Column(
            "scoring_results",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="Objective scores",
        ),
        sa.Column(
            "pattern_analysis",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="Pattern analysis",
        ),
        sa.Column(
            "overall_metrics",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="Overall metrics",
        ),
        sa.Column(
            "analysis_fairness_check",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="Bias detection in scoring",
        ),
        sa.Column(
            "recommendation",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="Recommendation",
        ),
        sa.Column(
            "overall_confidence",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="0-100 confidence",
        ),
        sa.Column(
            "analysis_note",
            sa.Text(),
            nullable=True,
            comment="Recruiter-visible summary",
        ),
        sa.Column("analysis_completed_at", sa.DateTime(), nullable=True),
        sa.Column(
            "recruiter_reviewed",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("recruiter_review_at", sa.DateTime(), nullable=True),
        sa.Column("recruiter_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["assessment_design_id"], ["assessment_designs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["candidate_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_analysis_results_assessment_id", "analysis_results", ["assessment_id"])
    op.create_index("ix_analysis_results_candidate_id", "analysis_results", ["candidate_id"])
    op.create_index("ix_analysis_results_position_id", "analysis_results", ["position_id"])
    op.create_index("ix_analysis_results_status", "analysis_results", ["status"])
    op.create_index("ix_analysis_results_created_at", "analysis_results", ["created_at"])

    # Phase 4: CandidateMatch table
    op.create_table(
        "candidate_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_result_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending_match",
                "matching",
                "match_complete",
                "ranked",
                "error",
                name="match_status",
            ),
            nullable=False,
            server_default="pending_match",
        ),
        sa.Column(
            "skill_match",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="Skill alignment",
        ),
        sa.Column(
            "experience_match",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="Experience fit",
        ),
        sa.Column(
            "team_fit",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="Team compatibility",
        ),
        sa.Column(
            "compensation_fit",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="Salary expectations",
        ),
        sa.Column(
            "overall_match",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="Overall score and fit level",
        ),
        sa.Column(
            "match_validation",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="Validation gates",
        ),
        sa.Column("rank_in_batch", sa.Integer(), nullable=True),
        sa.Column("percentile", sa.Integer(), nullable=True),
        sa.Column(
            "fit_level",
            sa.Enum(
                "strong_fit",
                "good_fit",
                "moderate_fit",
                "weak_fit",
                "poor_fit",
                name="fit_level",
            ),
            nullable=False,
            server_default="moderate_fit",
        ),
        sa.Column(
            "overall_score",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="0-100 match score",
        ),
        sa.Column(
            "match_confidence",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="0-100 confidence",
        ),
        sa.Column(
            "concerns",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="Concerns and risks",
        ),
        sa.Column(
            "opportunities",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="Opportunities",
        ),
        sa.Column("match_completed_at", sa.DateTime(), nullable=True),
        sa.Column("recruiter_reviewed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("recruiter_review_at", sa.DateTime(), nullable=True),
        sa.Column("recruiter_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_result_id"], ["analysis_results.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["candidate_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_candidate_matches_analysis_result_id", "candidate_matches", ["analysis_result_id"])
    op.create_index("ix_candidate_matches_position_id", "candidate_matches", ["position_id"])
    op.create_index("ix_candidate_matches_candidate_id", "candidate_matches", ["candidate_id"])
    op.create_index("ix_candidate_matches_fit_level", "candidate_matches", ["fit_level"])
    op.create_index("ix_candidate_matches_overall_score", "candidate_matches", ["overall_score"])
    op.create_index("ix_candidate_matches_rank_in_batch", "candidate_matches", ["rank_in_batch"])

    # Phase 5: HiringOutcome table
    op.create_table(
        "hiring_outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "hiring_decision",
            sa.Enum(
                "hired",
                "not_hired",
                "offer_declined",
                "withdrawn",
                "pending",
                name="hiring_decision",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("decision_made_at", sa.DateTime(), nullable=True),
        sa.Column("decision_rationale", sa.Text(), nullable=True),
        sa.Column("hired", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("hire_date", sa.DateTime(), nullable=True),
        sa.Column("tenure_days", sa.Integer(), nullable=True),
        sa.Column(
            "performance_rating",
            sa.Enum(
                "exceeding",
                "meeting",
                "developing",
                "underperforming",
                name="performance_rating",
            ),
            nullable=True,
        ),
        sa.Column("performance_evaluated_at", sa.DateTime(), nullable=True),
        sa.Column(
            "performance_details",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="Performance context",
        ),
        sa.Column("retained", sa.Boolean(), nullable=True),
        sa.Column("last_active_at", sa.DateTime(), nullable=True),
        sa.Column(
            "screening_recommendation",
            sa.String(50),
            nullable=True,
            comment="Screening agent recommendation",
        ),
        sa.Column(
            "assessment_recommendation",
            sa.String(50),
            nullable=True,
            comment="Assessment agent recommendation",
        ),
        sa.Column(
            "match_score_at_time",
            sa.Integer(),
            nullable=True,
            comment="Match score (0-100)",
        ),
        sa.Column(
            "actual_performance_vs_prediction",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="Accuracy tracking",
        ),
        sa.Column(
            "learning_feedback",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="Feedback for evolution agent",
        ),
        sa.Column(
            "bias_signals",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="Bias detection feedback",
        ),
        sa.Column("improvement_notes", sa.Text(), nullable=True),
        sa.Column("recruiter_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["candidate_match_id"], ["candidate_matches.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["candidate_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_hiring_outcomes_candidate_match_id", "hiring_outcomes", ["candidate_match_id"])
    op.create_index("ix_hiring_outcomes_position_id", "hiring_outcomes", ["position_id"])
    op.create_index("ix_hiring_outcomes_candidate_id", "hiring_outcomes", ["candidate_id"])
    op.create_index("ix_hiring_outcomes_hiring_decision", "hiring_outcomes", ["hiring_decision"])
    op.create_index("ix_hiring_outcomes_performance_rating", "hiring_outcomes", ["performance_rating"])
    op.create_index("ix_hiring_outcomes_hire_date", "hiring_outcomes", ["hire_date"])


def downgrade() -> None:
    """Drop analysis_results, candidate_matches, and hiring_outcomes tables."""

    op.drop_index("ix_hiring_outcomes_hire_date")
    op.drop_index("ix_hiring_outcomes_performance_rating")
    op.drop_index("ix_hiring_outcomes_hiring_decision")
    op.drop_index("ix_hiring_outcomes_candidate_id")
    op.drop_index("ix_hiring_outcomes_position_id")
    op.drop_index("ix_hiring_outcomes_candidate_match_id")
    op.drop_table("hiring_outcomes")

    op.drop_index("ix_candidate_matches_rank_in_batch")
    op.drop_index("ix_candidate_matches_overall_score")
    op.drop_index("ix_candidate_matches_fit_level")
    op.drop_index("ix_candidate_matches_candidate_id")
    op.drop_index("ix_candidate_matches_position_id")
    op.drop_index("ix_candidate_matches_analysis_result_id")
    op.drop_table("candidate_matches")

    op.drop_index("ix_analysis_results_created_at")
    op.drop_index("ix_analysis_results_status")
    op.drop_index("ix_analysis_results_position_id")
    op.drop_index("ix_analysis_results_candidate_id")
    op.drop_index("ix_analysis_results_assessment_id")
    op.drop_table("analysis_results")
