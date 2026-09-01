"""Unit tests for Screening Agent - Phase 1.

Tests the core agent logic including conscience checks, scoring,
recommendations, and summary generation.
"""
import pytest
from uuid import uuid4

from app.agents.screening_agent import ScreeningAgent
from app.models.screening import ScreeningRecommendation
from app.models.resume import Resume
from app.models.position import Position


class TestScreeningAgentConscience:
    """Test conscience checks (bias detection)."""

    @pytest.mark.asyncio
    async def test_conscience_check_no_indicators(self, db_session):
        """Clean resume with no demographic indicators should pass conscience check."""
        agent = ScreeningAgent(db_session)

        result = await agent._run_conscience_check(
            "5 years Python developer. Strong in React and SQL.",
            batch_config=None
        )

        assert result["potential_disparate_impact"] is False
        assert result["should_be_reviewed"] is False
        assert isinstance(result["demographic_indicators"], list)

    @pytest.mark.asyncio
    async def test_conscience_check_detects_age_indicators(self, db_session):
        """Resume with age indicators should be flagged."""
        agent = ScreeningAgent(db_session)

        result = await agent._run_conscience_check(
            "Graduated from Harvard in 2005. 18 years experience in tech.",
            batch_config=None
        )

        assert result["potential_disparate_impact"] is True
        assert result["should_be_reviewed"] is True
        assert len(result["demographic_indicators"]) > 0

    @pytest.mark.asyncio
    async def test_conscience_check_detects_disability(self, db_session):
        """Resume mentioning disability should be flagged for fair review."""
        agent = ScreeningAgent(db_session)

        result = await agent._run_conscience_check(
            "Experienced developer. Accommodations: remote work.",
            batch_config=None
        )

        assert result["should_be_reviewed"] is True
        assert "disability" in str(result["fairness_notes"]).lower()

    @pytest.mark.asyncio
    async def test_conscience_check_never_returns_error_string(self, db_session):
        """Conscience check should handle errors gracefully."""
        agent = ScreeningAgent(db_session)

        # Even with invalid input, should not crash
        result = await agent._run_conscience_check(None, None)

        assert isinstance(result, dict)
        assert "fairness_notes" in result


class TestScreeningAgentSkillMatching:
    """Test skill matching logic."""

    @pytest.mark.asyncio
    async def test_skill_match_finds_required_skills(self, db_session):
        """Should match skills that appear in resume."""
        agent = ScreeningAgent(db_session)

        result = await agent._evaluate_skill_match(
            "Expert in Python, React, and PostgreSQL",
            "Required: Python, React, Docker",
            batch_config={
                "required_skills": ["Python", "React", "Docker"]
            }
        )

        assert len(result["matched"]) >= 2  # Python and React matched
        assert "Docker" in result["missing"]
        assert result["score"] > 50

    @pytest.mark.asyncio
    async def test_skill_match_detects_missing_skills(self, db_session):
        """Should identify missing required skills."""
        agent = ScreeningAgent(db_session)

        result = await agent._evaluate_skill_match(
            "5 years Python developer",
            "Required: Java, Kubernetes, AWS",
            batch_config={
                "required_skills": ["Java", "Kubernetes", "AWS"]
            }
        )

        assert len(result["missing"]) == 3
        assert result["score"] == 0

    @pytest.mark.asyncio
    async def test_skill_match_handles_empty_config(self, db_session):
        """Should work without batch config."""
        agent = ScreeningAgent(db_session)

        result = await agent._evaluate_skill_match(
            "Python developer with React experience",
            "Strong backend needed",
            batch_config=None
        )

        assert isinstance(result, dict)
        assert "score" in result


class TestScreeningAgentExperienceFit:
    """Test experience evaluation."""

    @pytest.mark.asyncio
    async def test_experience_fit_meets_minimum(self, db_session, sample_position):
        """Resume meeting minimum experience should score higher."""
        agent = ScreeningAgent(db_session)

        result = await agent._evaluate_experience(
            "10 years as Python engineer. Built distributed systems.",
            sample_position,
            {},
            batch_config={"min_experience_years": 5}
        )

        assert result["years"] >= 5
        assert result["score"] >= 50

    @pytest.mark.asyncio
    async def test_experience_fit_below_minimum(self, db_session, sample_position):
        """Resume below minimum should score lower."""
        agent = ScreeningAgent(db_session)

        result = await agent._evaluate_experience(
            "2 years as junior developer",
            sample_position,
            {},
            batch_config={"min_experience_years": 5}
        )

        assert result["years"] < 5
        assert result["score"] < 50

    @pytest.mark.asyncio
    async def test_experience_fit_detects_relevance(self, db_session, sample_position):
        """Should evaluate skill relevance."""
        agent = ScreeningAgent(db_session)

        result = await agent._evaluate_experience(
            "15 years leading Python teams at Google",
            sample_position,
            {"skills": ["Python", "SQL"]},
            batch_config=None
        )

        assert result["relevance"] in ["high", "medium", "low"]


class TestScreeningAgentRecommendation:
    """Test recommendation generation (conscience checks)."""

    @pytest.mark.asyncio
    async def test_recommendation_never_returns_exclude(self, db_session):
        """Agent should NEVER recommend exclude or reject."""
        agent = ScreeningAgent(db_session)

        # Test with worst scores possible
        recommendation, _ = await agent._generate_recommendation(
            skill_match={"score": 0},
            experience_fit={"score": 0},
            trajectory={"score": 0},
            red_flags=[
                {"type": "test", "description": "Test flag", "severity": "critical"}
            ],
            bias_check={"should_be_reviewed": False}
        )

        # Even with 0 scores, should be "review" not "exclude"
        assert recommendation in [
            ScreeningRecommendation.advance,
            ScreeningRecommendation.hold,
            ScreeningRecommendation.review,
        ]
        assert str(recommendation.value) not in ["exclude", "reject"]

    @pytest.mark.asyncio
    async def test_recommendation_escalates_on_red_flags(self, db_session):
        """Should escalate to review if red flags exist."""
        agent = ScreeningAgent(db_session)

        recommendation, _ = await agent._generate_recommendation(
            skill_match={"score": 90},
            experience_fit={"score": 90},
            trajectory={"score": 90},
            red_flags=[{"type": "gap", "description": "Employment gap", "severity": "low"}],
            bias_check={"should_be_reviewed": False}
        )

        # Red flags should escalate to review
        assert recommendation == ScreeningRecommendation.review

    @pytest.mark.asyncio
    async def test_recommendation_escalates_on_bias_check(self, db_session):
        """Should escalate to review if conscience check triggered."""
        agent = ScreeningAgent(db_session)

        recommendation, _ = await agent._generate_recommendation(
            skill_match={"score": 90},
            experience_fit={"score": 90},
            trajectory={"score": 90},
            red_flags=[],
            bias_check={"should_be_reviewed": True}
        )

        # Bias checks should always escalate
        assert recommendation == ScreeningRecommendation.review

    @pytest.mark.asyncio
    async def test_recommendation_advance_on_strong_fit(self, db_session):
        """Strong fit with no concerns should recommend advance."""
        agent = ScreeningAgent(db_session)

        recommendation, confidence = await agent._generate_recommendation(
            skill_match={"score": 85},
            experience_fit={"score": 90},
            trajectory={"score": 85},
            red_flags=[],
            bias_check={"should_be_reviewed": False}
        )

        assert recommendation == ScreeningRecommendation.advance
        assert confidence >= 75

    @pytest.mark.asyncio
    async def test_recommendation_hold_on_medium_fit(self, db_session):
        """Medium fit should recommend hold."""
        agent = ScreeningAgent(db_session)

        recommendation, confidence = await agent._generate_recommendation(
            skill_match={"score": 60},
            experience_fit={"score": 65},
            trajectory={"score": 60},
            red_flags=[],
            bias_check={"should_be_reviewed": False}
        )

        assert recommendation == ScreeningRecommendation.hold
        assert 50 <= confidence <= 75


class TestScreeningAgentSummary:
    """Test summary generation for recruiter."""

    @pytest.mark.asyncio
    async def test_summary_includes_recommendation(self, db_session, sample_position, sample_resume):
        """Summary should clearly state recommendation at top."""
        agent = ScreeningAgent(db_session)

        summary = await agent._generate_summary(
            sample_resume,
            sample_position,
            ScreeningRecommendation.advance,
            85,
            skill_match={"matched": ["Python", "React"], "missing": ["Docker"]},
            experience_fit={"years": 8, "relevance": "high"},
            trajectory={"stability": "stable", "progression": "progressing"},
            red_flags=[],
            bias_check={"should_be_reviewed": False, "fairness_notes": "No concerns"}
        )

        assert "ADVANCE" in summary.upper()
        assert "85" in summary
        assert isinstance(summary, str)
        assert len(summary) > 200  # Should be substantial

    @pytest.mark.asyncio
    async def test_summary_includes_red_flags(self, db_session, sample_position, sample_resume):
        """Summary should include red flags as concerns."""
        agent = ScreeningAgent(db_session)

        red_flags = [
            {"type": "employment_gaps", "description": "6-month gap found", "severity": "low"}
        ]

        summary = await agent._generate_summary(
            sample_resume,
            sample_position,
            ScreeningRecommendation.hold,
            60,
            skill_match={"matched": [], "missing": []},
            experience_fit={"years": 3, "relevance": "medium"},
            trajectory={"stability": "moderate", "progression": "stable"},
            red_flags=red_flags,
            bias_check={"should_be_reviewed": False, "fairness_notes": ""}
        )

        assert "consideration" in summary.lower() or "concern" in summary.lower() or "gap" in summary.lower()

    @pytest.mark.asyncio
    async def test_summary_includes_fairness_notes(self, db_session, sample_position, sample_resume):
        """Summary should include fairness notes when present."""
        agent = ScreeningAgent(db_session)

        summary = await agent._generate_summary(
            sample_resume,
            sample_position,
            ScreeningRecommendation.review,
            50,
            skill_match={"matched": [], "missing": []},
            experience_fit={"years": 5, "relevance": "low"},
            trajectory={"stability": "stable", "progression": "stable"},
            red_flags=[],
            bias_check={
                "should_be_reviewed": True,
                "fairness_notes": "Candidate mentioned disability accommodation needs"
            }
        )

        assert "fairness" in summary.lower() or "note" in summary.lower()


class TestScreeningAgentLearning:
    """Test learning signal capture."""

    @pytest.mark.asyncio
    async def test_learning_signals_captured(self, db_session, sample_position, sample_resume):
        """Agent should capture learning signals for improvement."""
        agent = ScreeningAgent(db_session)

        signals = await agent._capture_learning_signals(
            sample_resume,
            sample_position,
            ScreeningRecommendation.advance,
            85
        )

        assert signals["position_id"] == str(sample_position.id)
        assert signals["recommendation"] == "advance"
        assert signals["confidence"] == 85
        assert "timestamp" in signals


class TestScreeningAgentIntegration:
    """Integration tests for full screening pipeline."""

    @pytest.mark.asyncio
    async def test_full_screening_pipeline(self, db_session, sample_position, sample_resume):
        """Full screening should produce valid ScreeningResult."""
        agent = ScreeningAgent(db_session)

        result = await agent.screen_resume(
            sample_resume,
            sample_position,
            batch_config={
                "min_experience_years": 3,
                "required_skills": ["Python"]
            }
        )

        assert result["agent_recommendation"] in [
            ScreeningRecommendation.advance,
            ScreeningRecommendation.hold,
            ScreeningRecommendation.review,
        ]
        assert 0 <= result["confidence_score"] <= 100
        assert len(result["screening_summary"]) > 100
        assert isinstance(result["screening_details"], dict)
        assert isinstance(result["bias_flags"], dict)

    @pytest.mark.asyncio
    async def test_screening_handles_missing_data(self, db_session, sample_position):
        """Screening should handle missing resume data gracefully."""
        agent = ScreeningAgent(db_session)

        # Create minimal resume with no text
        from app.models.resume import Resume
        resume = Resume(
            id=uuid4(),
            user_id=uuid4(),
            file_id="missing",
            supplementary={},  # No extracted_text
            raw_narrative=""
        )

        result = await agent.screen_resume(resume, sample_position)

        assert result["agent_recommendation"] == ScreeningRecommendation.review
        assert isinstance(result["screening_summary"], str)

    @pytest.mark.asyncio
    async def test_screening_handles_missing_position(self, db_session, sample_resume):
        """Screening should handle missing position data gracefully."""
        agent = ScreeningAgent(db_session)

        # Create minimal position
        from app.models.position import Position
        position = Position(
            id=uuid4(),
            company_id=uuid4(),
            title="Unknown Role",
            description=""
        )

        result = await agent.screen_resume(sample_resume, position)

        assert result["agent_recommendation"] in [
            ScreeningRecommendation.advance,
            ScreeningRecommendation.hold,
            ScreeningRecommendation.review,
        ]
        assert result["confidence_score"] >= 0


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_resume():
    """Sample resume for testing."""
    from app.models.resume import Resume

    return Resume(
        id=uuid4(),
        user_id=uuid4(),
        file_id="test-file",
        supplementary={
            "extracted_text": """
            Senior Python Developer

            10 years experience building distributed systems.
            Expertise: Python, React, PostgreSQL, Docker, AWS

            Experience:
            - Lead Engineer at Google (5 years)
            - Senior Developer at Uber (3 years)
            - Developer at Airbnb (2 years)

            Stable career progression. Currently seeking new challenges.
            """
        },
        raw_narrative="Senior Python engineer with 10 years experience"
    )


@pytest.fixture
def sample_position():
    """Sample position for testing."""
    from app.models.position import Position

    return Position(
        id=uuid4(),
        company_id=uuid4(),
        title="Senior Python Engineer",
        description="We're looking for an experienced Python engineer to lead our backend team.",
        metadata={
            "requirements": ["Python", "SQL", "System Design"],
            "skills": ["Python", "React", "SQL"]
        }
    )


__all__ = [
    "TestScreeningAgentConscience",
    "TestScreeningAgentSkillMatching",
    "TestScreeningAgentExperienceFit",
    "TestScreeningAgentRecommendation",
    "TestScreeningAgentSummary",
    "TestScreeningAgentLearning",
    "TestScreeningAgentIntegration",
]
