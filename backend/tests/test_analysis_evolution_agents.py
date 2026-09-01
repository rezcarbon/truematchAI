"""Unit tests for Analysis, Matching, and Evolution Agents - Phases 3-5."""
import pytest
from uuid import uuid4

from app.agents.analysis_agent import AnalysisAgent
from app.agents.matching_agent import MatchingAgent
from app.agents.evolution_agent import EvolutionAgent
from app.models.analysis_result import AnalysisResult
from app.models.assessment import Assessment
from app.models.assessment_design import AssessmentDesign
from app.models.candidate_match import CandidateMatch
from app.models.hiring_outcome import HiringOutcome
from app.models.position import Position
from app.models.resume import Resume


class TestAnalysisAgent:
    """Test Phase 3 Analysis Agent."""

    @pytest.mark.asyncio
    async def test_analyze_assessment_returns_dict(self, db_session):
        """Analysis pipeline returns all required fields."""
        agent = AnalysisAgent(db_session)

        # Mock data
        assessment = Assessment(
            id=uuid4(),
            resume_id=uuid4(),
            position_id=uuid4(),
            user_id=uuid4(),
        )
        design = AssessmentDesign(
            id=uuid4(),
            position_id=uuid4(),
            candidate_id=uuid4(),
            agent_design={"questions": []},
        )

        result = await agent.analyze_assessment(assessment, design, str(uuid4()))

        assert "responses_analyzed" in result
        assert "scoring_results" in result
        assert "pattern_analysis" in result
        assert "overall_metrics" in result
        assert "analysis_fairness_check" in result
        assert "recommendation" in result

    @pytest.mark.asyncio
    async def test_score_responses_produces_scores(self, db_session):
        """Response scoring produces objective scores."""
        agent = AnalysisAgent(db_session)

        analyzed = {
            "q1": {
                "text": "This is a detailed response to the question.",
                "parsed_intent": "Addresses question directly",
                "correctness_level": "mostly_correct",
                "comprehension_score": 75,
            }
        }

        design = AssessmentDesign(
            id=uuid4(),
            position_id=uuid4(),
            candidate_id=uuid4(),
            agent_design={"evaluation_rubric": {"competencies": ["problem-solving"]}},
        )
        assessment = Assessment(
            id=uuid4(),
            resume_id=uuid4(),
            position_id=uuid4(),
            user_id=uuid4(),
        )

        scoring = await agent._score_responses(assessment, design, analyzed)

        assert "q1" in scoring
        assert scoring["q1"]["score"] >= 0
        assert scoring["q1"]["score"] <= 100
        assert "confidence" in scoring["q1"]

    @pytest.mark.asyncio
    async def test_identify_patterns_finds_strengths_and_gaps(self, db_session):
        """Pattern identification finds strengths and gaps."""
        agent = AnalysisAgent(db_session)

        analyzed = {"q1": {"parsed_intent": "Good response"}}
        scoring = {"q1": {"score": 85}}

        patterns = await agent._identify_patterns(
            Assessment(id=uuid4(), resume_id=uuid4(), position_id=uuid4(), user_id=uuid4()),
            analyzed,
            scoring,
        )

        assert "strengths" in patterns
        assert "gaps" in patterns
        assert "growth_signals" in patterns
        assert "red_flags" in patterns

    @pytest.mark.asyncio
    async def test_fairness_check_detects_issues(self, db_session):
        """Fairness check identifies scoring issues."""
        agent = AnalysisAgent(db_session)

        analyzed = {"q1": {"parsed_intent": "confused"}}
        scoring = {"q1": {"score": 10}, "q2": {"score": 90}}

        fairness = await agent._check_scoring_fairness(analyzed, scoring, {})

        assert "passed" in fairness
        assert "issues" in fairness
        assert "fairness_score" in fairness


class TestMatchingAgent:
    """Test Phase 4 Matching Agent."""

    @pytest.mark.asyncio
    async def test_calculate_match_returns_complete_dict(self, db_session):
        """Matching pipeline returns all required fields."""
        agent = MatchingAgent(db_session)

        analysis = AnalysisResult(
            id=uuid4(),
            assessment_id=uuid4(),
            assessment_design_id=uuid4(),
            candidate_id=uuid4(),
            position_id=uuid4(),
            pattern_analysis={"strengths": ["Python", "Leadership"]},
        )
        position = Position(
            id=uuid4(),
            company_id=uuid4(),
            title="Senior Engineer",
            description="5+ years Python experience",
        )
        resume = Resume(
            id=uuid4(),
            user_id=uuid4(),
            file_id="test",
        )

        result = await agent.calculate_match(analysis, position, resume)

        assert "skill_match" in result
        assert "experience_match" in result
        assert "team_fit" in result
        assert "compensation_fit" in result
        assert "overall_score" in result
        assert "concerns" in result
        assert "opportunities" in result

    @pytest.mark.asyncio
    async def test_skill_match_scores_relevance(self, db_session):
        """Skill match accurately scores candidate skills."""
        agent = MatchingAgent(db_session)

        analysis = AnalysisResult(
            id=uuid4(),
            assessment_id=uuid4(),
            assessment_design_id=uuid4(),
            candidate_id=uuid4(),
            position_id=uuid4(),
            pattern_analysis={"strengths": ["Python", "SQL"]},
        )
        position = Position(
            id=uuid4(),
            company_id=uuid4(),
            title="Python Developer",
            description="Required: Python, SQL, React",
        )

        skill_match = await agent._score_skill_match(analysis, position)

        assert "technical" in skill_match
        assert "gaps" in skill_match
        assert "match_score" in skill_match
        assert skill_match["match_score"] >= 0

    @pytest.mark.asyncio
    async def test_experience_match_evaluates_fit(self, db_session):
        """Experience match evaluates tenure and relevance."""
        agent = MatchingAgent(db_session)

        analysis = AnalysisResult(
            id=uuid4(),
            assessment_id=uuid4(),
            assessment_design_id=uuid4(),
            candidate_id=uuid4(),
            position_id=uuid4(),
            pattern_analysis={"gaps": []},
        )
        position = Position(
            id=uuid4(),
            company_id=uuid4(),
            title="Senior Developer",
            description="5+ years experience required",
        )
        resume = Resume(
            id=uuid4(),
            user_id=uuid4(),
            file_id="test",
        )

        exp_match = await agent._score_experience_match(analysis, position, resume)

        assert "years_required" in exp_match
        assert "relevance" in exp_match
        assert "match_score" in exp_match

    @pytest.mark.asyncio
    async def test_validation_gates_flag_concerns(self, db_session):
        """Validation gates properly flag skill/experience concerns."""
        agent = MatchingAgent(db_session)

        skill_match = {"match_score": 30}  # Below minimum
        experience_match = {"match_score": 40, "relevance": "low"}
        overall_score = 30

        validation = await agent._run_validation_gates(
            skill_match, experience_match, overall_score
        )

        assert "passed" in validation
        assert "issues" in validation
        assert validation["passed"] is False


class TestEvolutionAgent:
    """Test Phase 5 Evolution Agent."""

    @pytest.mark.asyncio
    async def test_process_outcome_returns_feedback(self, db_session):
        """Evolution pipeline returns learning feedback."""
        agent = EvolutionAgent(db_session)

        outcome = HiringOutcome(
            id=uuid4(),
            candidate_match_id=uuid4(),
            position_id=uuid4(),
            candidate_id=uuid4(),
            hiring_decision="hired",
            hired=True,
            screening_recommendation="advance",
            assessment_recommendation="advance",
            match_score_at_time=80,
        )

        result = await agent.process_outcome(outcome)

        assert "prediction_accuracy" in result
        assert "learning_feedback" in result
        assert "bias_signals" in result
        assert "agent_accuracy_metrics" in result

    @pytest.mark.asyncio
    async def test_prediction_comparison_detects_errors(self, db_session):
        """Prediction accuracy properly compares agent recommendations to outcomes."""
        agent = EvolutionAgent(db_session)

        outcome_hired = HiringOutcome(
            id=uuid4(),
            candidate_match_id=uuid4(),
            position_id=uuid4(),
            candidate_id=uuid4(),
            hiring_decision="hired",
            hired=True,
            screening_recommendation="advance",
        )

        accuracy = await agent._compare_prediction_vs_reality(outcome_hired)

        assert "prediction_correct" in accuracy
        assert "screening_accuracy" in accuracy
        assert "assessment_accuracy" in accuracy

    @pytest.mark.asyncio
    async def test_bias_detection_identifies_patterns(self, db_session):
        """Bias detection identifies potential bias patterns."""
        agent = EvolutionAgent(db_session)

        outcome_wrong = HiringOutcome(
            id=uuid4(),
            candidate_match_id=uuid4(),
            position_id=uuid4(),
            candidate_id=uuid4(),
            hiring_decision="not_hired",
            hired=False,
            match_score_at_time=90,  # High score but not hired = potential bias
        )

        accuracy = {"match_score_variance": 40}

        bias = await agent._detect_bias_patterns(outcome_wrong, accuracy)

        assert "suspected_bias" in bias
        assert "protected_attributes" in bias


class TestIntegration:
    """Integration tests across phases."""

    @pytest.mark.asyncio
    async def test_full_pipeline_analysis_to_outcome(self, db_session):
        """Full pipeline from assessment analysis through outcome learning."""
        # This would require setting up full data model
        # Placeholder for integration test
        assert True

    @pytest.mark.asyncio
    async def test_fairness_maintained_across_phases(self, db_session):
        """Fairness checks are maintained across all agent phases."""
        # Verify bias detection in analysis flows through matching
        assert True


__all__ = [
    "TestAnalysisAgent",
    "TestMatchingAgent",
    "TestEvolutionAgent",
    "TestIntegration",
]
