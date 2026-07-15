"""Unit tests for Assessment Designer Agent - Phase 2."""
import pytest
from uuid import uuid4

from app.agents.assessment_designer_agent import AssessmentDesignerAgent
from app.models.resume import Resume
from app.models.position import Position


class TestAssessmentDesignerAgentAnalysis:
    """Test candidate profile and role analysis."""

    @pytest.mark.asyncio
    async def test_analyze_candidate_profile_with_skills(self, db_session):
        """Extract skills from resume."""
        agent = AssessmentDesignerAgent(db_session)

        result = await agent._analyze_candidate_profile(
            Resume(
                id=uuid4(),
                user_id=uuid4(),
                file_id="test",
                supplementary={
                    "extracted_text": "Python developer with 8 years experience in React and SQL databases."
                },
                raw_narrative="Senior engineer",
            )
        )

        assert result["skills"]["technical"] != []
        assert result["experience"]["years"] == 8
        assert result["experience"]["relevance"] in ["high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_analyze_candidate_profile_no_experience(self, db_session):
        """Handle resume with no experience info."""
        agent = AssessmentDesignerAgent(db_session)

        result = await agent._analyze_candidate_profile(
            Resume(
                id=uuid4(),
                user_id=uuid4(),
                file_id="test",
                supplementary={"extracted_text": ""},
                raw_narrative="",
            )
        )

        assert result["experience"]["years"] == 0
        assert isinstance(result["skills"]["technical"], list)

    @pytest.mark.asyncio
    async def test_analyze_role_requirements(self, db_session):
        """Extract requirements from JD."""
        agent = AssessmentDesignerAgent(db_session)

        position = Position(
            id=uuid4(),
            company_id=uuid4(),
            title="Senior Python Engineer",
            description="5+ years Python experience. Must know React, SQL, Docker.",
        )

        result = await agent._analyze_role_requirements(position)

        assert result["title"] == "Senior Python Engineer"
        assert isinstance(result["required_competencies"], list)
        assert isinstance(result["technical_requirements"], list)


class TestAssessmentDesignerAgentDesign:
    """Test assessment question design."""

    @pytest.mark.asyncio
    async def test_design_assessment_questions_generates_questions(self, db_session):
        """Design generates 3-5 questions."""
        agent = AssessmentDesignerAgent(db_session)

        candidate_profile = {
            "skills": {"technical": ["Python", "React"], "soft": ["Leadership"]},
            "experience": {"years": 8, "relevance": "high"},
            "trajectory": {"progression": "ascending"},
            "strengths": ["System design"],
            "gaps": [],
            "learning_style": {"hands_on": True},
        }

        role_requirements = {
            "title": "Senior Engineer",
            "required_competencies": ["Python", "System Design"],
            "technical_requirements": ["Python", "SQL"],
        }

        questions = await agent._design_assessment_questions(
            candidate_profile, role_requirements, Position(id=uuid4(), company_id=uuid4())
        )

        assert len(questions) >= 3
        assert all("question" in q for q in questions)
        assert all("type" in q for q in questions)
        assert all(q["type"] in ["coding", "design", "behavioral", "scenario"] for q in questions)

    @pytest.mark.asyncio
    async def test_design_assessment_questions_matches_candidate(self, db_session):
        """Questions are tailored to candidate profile."""
        agent = AssessmentDesignerAgent(db_session)

        candidate_profile = {
            "skills": {"technical": ["Python"], "soft": []},
            "experience": {"years": 8, "relevance": "high"},
            "trajectory": {"progression": "ascending"},
            "strengths": [],
            "gaps": [],
            "learning_style": {},
        }

        role_requirements = {
            "title": "Python Engineer",
            "required_competencies": ["Python"],
            "technical_requirements": ["Python"],
        }

        questions = await agent._design_assessment_questions(
            candidate_profile, role_requirements, Position(id=uuid4(), company_id=uuid4())
        )

        assert len(questions) > 0
        # Check that questions reference the role
        assert any("Python Engineer" in q.get("question", "") for q in questions)


class TestAssessmentDesignerAgentRubric:
    """Test evaluation rubric creation."""

    @pytest.mark.asyncio
    async def test_create_evaluation_rubric_has_competencies(self, db_session):
        """Rubric includes competencies and scoring."""
        agent = AssessmentDesignerAgent(db_session)

        questions = [
            {"question": "Design a system", "type": "design", "expected_duration_minutes": 30}
        ]
        role_requirements = {"title": "Engineer", "required_competencies": ["System Design"]}

        rubric = await agent._create_evaluation_rubric(questions, role_requirements)

        assert "competencies" in rubric
        assert len(rubric["competencies"]) > 0
        assert "scoring_levels" in rubric
        assert "passing_threshold" in rubric


class TestAssessmentDesignerAgentGuidance:
    """Test interview guidance generation."""

    @pytest.mark.asyncio
    async def test_generate_interview_guidance_includes_duration(self, db_session):
        """Guidance includes time estimates."""
        agent = AssessmentDesignerAgent(db_session)

        candidate_profile = {
            "skills": {"technical": ["Python"], "soft": ["Communication"]},
            "experience": {"years": 5},
            "trajectory": {},
            "strengths": [],
            "gaps": [],
            "learning_style": {},
        }

        role_requirements = {
            "title": "Engineer",
            "required_competencies": ["Python"],
        }

        questions = [
            {"question": "Design...", "type": "design", "expected_duration_minutes": 45},
            {"question": "Tell about...", "type": "behavioral", "expected_duration_minutes": 15},
        ]

        guidance = await agent._generate_interview_guidance(
            candidate_profile, role_requirements, questions
        )

        assert "estimated_duration_minutes" in guidance
        assert guidance["estimated_duration_minutes"] > 0
        assert "probe_areas" in guidance
        assert "red_flags" in guidance
        assert "growth_signals" in guidance


class TestAssessmentDesignerAgentFairness:
    """Test fairness validation gates."""

    @pytest.mark.asyncio
    async def test_bias_detection_gate_detects_age_bias(self, db_session):
        """Gate detects age-coded language."""
        agent = AssessmentDesignerAgent(db_session)

        questions = [
            {
                "question": "How many years old are you? This is a young person's role.",
                "type": "behavioral",
                "expected_duration_minutes": 15,
            }
        ]

        result = await agent._bias_detection_gate(questions)

        assert "passed" in result
        assert "issues" in result
        assert len(result["issues"]) > 0

    @pytest.mark.asyncio
    async def test_bias_detection_gate_passes_fair_questions(self, db_session):
        """Gate passes fair questions."""
        agent = AssessmentDesignerAgent(db_session)

        questions = [
            {
                "question": "Design a system for managing user data.",
                "type": "design",
                "expected_duration_minutes": 30,
            }
        ]

        result = await agent._bias_detection_gate(questions)

        assert "passed" in result
        assert result["passed"] is True

    @pytest.mark.asyncio
    async def test_cognitive_load_gate_checks_duration(self, db_session):
        """Gate validates assessment duration."""
        agent = AssessmentDesignerAgent(db_session)

        interview_guidance_short = {
            "estimated_duration_minutes": 20,
            "time_breakdown": {},
            "probe_areas": [],
            "red_flags": [],
            "growth_signals": [],
        }

        interview_guidance_long = {
            "estimated_duration_minutes": 300,  # 5 hours
            "time_breakdown": {},
            "probe_areas": [],
            "red_flags": [],
            "growth_signals": [],
        }

        result_long = await agent._cognitive_load_gate([], interview_guidance_long)
        assert result_long["passed"] is False

    @pytest.mark.asyncio
    async def test_fairness_check_runs_all_gates(self, db_session):
        """Fairness check runs all 4 gates."""
        agent = AssessmentDesignerAgent(db_session)

        candidate_profile = {"skills": {}, "experience": {}, "trajectory": {}}
        questions = [
            {"question": "Design a system", "type": "design", "expected_duration_minutes": 45}
        ]
        guidance = {
            "estimated_duration_minutes": 90,
            "time_breakdown": {},
            "probe_areas": [],
            "red_flags": [],
            "growth_signals": [],
        }

        result = await agent._run_fairness_check(candidate_profile, questions, guidance)

        assert "passed" in result
        assert "fairness_score" in result
        assert 0 <= result["fairness_score"] <= 100
        assert "gates_evaluated" in result
        assert len(result["gates_evaluated"]) == 4


class TestAssessmentDesignerAgentIntegration:
    """Integration tests for full design pipeline."""

    @pytest.mark.asyncio
    async def test_design_assessment_full_pipeline(self, db_session, sample_resume, sample_position):
        """Full assessment design pipeline works."""
        agent = AssessmentDesignerAgent(db_session)

        result = await agent.design_assessment(sample_resume, sample_position)

        assert "agent_design" in result
        assert "design_fairness_check" in result

        design = result["agent_design"]
        assert "questions" in design
        assert "interview_guidance" in design
        assert "evaluation_rubric" in design
        assert "design_rationale" in design

        fairness = result["design_fairness_check"]
        assert "passed" in fairness
        assert "fairness_score" in fairness
        assert "gates_evaluated" in fairness

    @pytest.mark.asyncio
    async def test_design_assessment_handles_missing_data(self, db_session):
        """Pipeline handles missing resume data gracefully."""
        agent = AssessmentDesignerAgent(db_session)

        resume = Resume(
            id=uuid4(),
            user_id=uuid4(),
            file_id="missing",
            supplementary={},
            raw_narrative="",
        )

        position = Position(
            id=uuid4(),
            company_id=uuid4(),
            title="Unknown Role",
            description="",
        )

        result = await agent.design_assessment(resume, position)

        assert "agent_design" in result
        assert "design_fairness_check" in result

    @pytest.mark.asyncio
    async def test_design_assessment_fairness_score_reasonable(self, db_session, sample_resume, sample_position):
        """Generated design has reasonable fairness score."""
        agent = AssessmentDesignerAgent(db_session)

        result = await agent.design_assessment(sample_resume, sample_position)

        fairness_score = result["design_fairness_check"]["fairness_score"]
        assert 0 <= fairness_score <= 100


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_resume():
    """Sample resume for testing."""
    return Resume(
        id=uuid4(),
        user_id=uuid4(),
        file_id="test-file",
        supplementary={
            "extracted_text": """
            Senior Software Engineer

            8 years experience building distributed systems.
            Expertise: Python, React, PostgreSQL, Docker, Kubernetes

            Experience:
            - Lead Engineer at Google (5 years)
            - Senior Developer at Uber (3 years)

            Stable career progression. Leadership background.
            """
        },
        raw_narrative="Senior engineer with 8 years experience",
    )


@pytest.fixture
def sample_position():
    """Sample position for testing."""
    return Position(
        id=uuid4(),
        company_id=uuid4(),
        title="Senior Backend Engineer",
        description="""
        We're looking for a Senior Backend Engineer with:
        - 5+ years Python experience
        - System design expertise
        - Leadership experience
        - Experience with distributed systems

        Nice to have: Docker, Kubernetes, SQL
        """,
    )


__all__ = [
    "TestAssessmentDesignerAgentAnalysis",
    "TestAssessmentDesignerAgentDesign",
    "TestAssessmentDesignerAgentRubric",
    "TestAssessmentDesignerAgentGuidance",
    "TestAssessmentDesignerAgentFairness",
    "TestAssessmentDesignerAgentIntegration",
]
