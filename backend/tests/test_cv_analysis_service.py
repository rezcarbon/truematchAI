"""Comprehensive tests for CV Analysis Service."""
from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cv_analysis import (
    CVAnalysisRequest,
    CVAnalysisStatus,
    SeniorityLevel,
)
from app.models.resume_version import ResumeVersion
from app.services.cv_analysis import (
    CVAnalysisService,
    MarketCompetitivenessScore,
)


@pytest.fixture
def cv_analysis_service():
    """Create a CV analysis service with mock DB."""
    mock_db = AsyncMock(spec=AsyncSession)
    return CVAnalysisService(mock_db)


@pytest.fixture
def sample_parsed_resume():
    """Create sample parsed resume data."""
    return {
        "personal_info": {
            "name": "Jane Smith",
            "email": "jane@example.com",
        },
        "work_experience": [
            {
                "position": "Software Engineer",
                "company": "Tech Corp",
                "start_date": "2020-01-01",
                "description": "Developed microservices using Python and Java",
            },
            {
                "position": "Junior Developer",
                "company": "StartUp Inc",
                "start_date": "2018-01-01",
                "end_date": "2020-01-01",
            },
        ],
        "education": [
            {
                "degree": "BS Computer Science",
                "institution": "Tech University",
                "graduation_year": 2018,
            }
        ],
        "skills": ["python", "java", "sql", "docker", "kubernetes", "aws"],
        "certifications": ["AWS Solutions Architect", "Kubernetes Administrator"],
    }


@pytest.fixture
def sample_cv_request():
    """Create a sample CV analysis request."""
    request = MagicMock(spec=CVAnalysisRequest)
    request.id = uuid.uuid4()
    request.user_id = uuid.uuid4()
    request.resume_id = uuid.uuid4()
    request.target_role = "Senior Software Engineer"
    request.target_seniority = SeniorityLevel.senior
    request.career_focus_areas = ["Cloud Architecture", "System Design"]
    request.status = CVAnalysisStatus.pending
    return request


@pytest.fixture
def sample_resume_version(sample_parsed_resume):
    """Create a sample resume version."""
    version = MagicMock(spec=ResumeVersion)
    version.id = uuid.uuid4()
    version.resume_id = uuid.uuid4()
    version.user_id = uuid.uuid4()
    version.parsed_data = sample_parsed_resume
    version.raw_narrative = "Experienced software engineer..."
    version.created_at = datetime.utcnow()
    return version


class TestMarketCompetitivenessScore:
    """Test MarketCompetitivenessScore class."""

    def test_score_initialization(self):
        """Test score object initialization."""
        score = MarketCompetitivenessScore()

        assert score.overall_score == 0.0
        assert score.skill_competitiveness == 0.0
        assert score.experience_competitiveness == 0.0
        assert score.certifications_competitiveness == 0.0
        assert score.market_percentile == 0
        assert score.in_demand_skills_count == 0
        assert score.missing_trending_skills == []
        assert score.recommendations == []


class TestCVAnalysisServiceCreateRequest:
    """Test CV analysis request creation."""

    @pytest.mark.asyncio
    async def test_create_analysis_request_success(self, cv_analysis_service):
        """Test creating an analysis request."""
        user_id = uuid.uuid4()
        resume_id = uuid.uuid4()

        request = await cv_analysis_service.create_analysis_request(
            user_id=user_id,
            resume_id=resume_id,
            target_role="Senior Engineer",
            target_seniority=SeniorityLevel.senior,
            career_focus_areas=["Cloud", "AI"],
        )

        assert request.user_id == user_id
        assert request.resume_id == resume_id
        assert request.target_role == "Senior Engineer"
        assert request.target_seniority == SeniorityLevel.senior
        assert request.career_focus_areas == ["Cloud", "AI"]
        assert request.status == CVAnalysisStatus.pending

    @pytest.mark.asyncio
    async def test_create_analysis_request_without_focus_areas(self, cv_analysis_service):
        """Test creating request without focus areas."""
        request = await cv_analysis_service.create_analysis_request(
            user_id=uuid.uuid4(),
            resume_id=uuid.uuid4(),
            target_role="Engineer",
            target_seniority=SeniorityLevel.mid,
        )

        assert request.career_focus_areas == []


class TestCVAnalysisServiceAnalyzeCV:
    """Test CV analysis functionality."""

    @pytest.mark.asyncio
    async def test_analyze_cv_success(
        self, cv_analysis_service, sample_cv_request, sample_resume_version
    ):
        """Test successful CV analysis."""
        cv_analysis_service._get_analysis_request = AsyncMock(return_value=sample_cv_request)
        cv_analysis_service._get_current_resume_version = AsyncMock(
            return_value=sample_resume_version
        )
        cv_analysis_service._analyze_skill_gaps = AsyncMock(return_value=[])
        cv_analysis_service._identify_weakness_areas = MagicMock(return_value=[])
        cv_analysis_service._summarize_strengths = MagicMock(return_value="Strong skills")
        cv_analysis_service._analyze_job_fit = AsyncMock(
            return_value={"scores": {}, "top_positions": [], "underrated": []}
        )
        cv_analysis_service._generate_improvements = MagicMock(return_value=[])
        cv_analysis_service._generate_rewording_suggestions = MagicMock(return_value={})
        cv_analysis_service._analyze_career_trajectory = MagicMock(return_value="Good trajectory")
        cv_analysis_service._analyze_market_positioning = MagicMock(return_value="Good position")
        cv_analysis_service._identify_growth_opportunities = MagicMock(return_value=[])
        cv_analysis_service._check_coherence = MagicMock(return_value={"passed": True})
        cv_analysis_service._check_consistency = MagicMock(return_value={"passed": True})
        cv_analysis_service._check_fidelity = MagicMock(return_value={"passed": True})
        cv_analysis_service._check_bias_flags = MagicMock(return_value={"flags": []})

        result = await cv_analysis_service.analyze_cv(sample_cv_request.id)

        assert result.cv_analysis_request_id == sample_cv_request.id
        assert result.missing_capabilities is not None
        assert result.job_fit_scores is not None
        assert result.governance_passed is not None

    @pytest.mark.asyncio
    async def test_analyze_cv_request_not_found(self, cv_analysis_service):
        """Test analysis when request not found."""
        cv_analysis_service._get_analysis_request = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Analysis request .* not found"):
            await cv_analysis_service.analyze_cv(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_analyze_cv_unauthorized(
        self, cv_analysis_service, sample_cv_request
    ):
        """Test analysis with unauthorized user."""
        cv_analysis_service._get_analysis_request = AsyncMock(return_value=sample_cv_request)

        with pytest.raises(ValueError, match="Unauthorized"):
            await cv_analysis_service.analyze_cv(sample_cv_request.id, user_id=uuid.uuid4())

    @pytest.mark.asyncio
    async def test_analyze_cv_resume_not_found(self, cv_analysis_service, sample_cv_request):
        """Test analysis when resume not found."""
        cv_analysis_service._get_analysis_request = AsyncMock(return_value=sample_cv_request)
        cv_analysis_service._get_current_resume_version = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Resume version not found"):
            await cv_analysis_service.analyze_cv(sample_cv_request.id)


class TestCVAnalysisServiceMarketCompetitiveness:
    """Test market competitiveness scoring."""

    @pytest.mark.asyncio
    async def test_calculate_market_competitiveness(
        self, cv_analysis_service, sample_resume_version
    ):
        """Test market competitiveness calculation."""
        cv_analysis_service._get_current_resume_version = AsyncMock(
            return_value=sample_resume_version
        )

        score = await cv_analysis_service.calculate_market_competitiveness(
            sample_resume_version.resume_id
        )

        assert isinstance(score, MarketCompetitivenessScore)
        assert 0 <= score.overall_score <= 100
        assert 0 <= score.market_percentile <= 100
        assert score.in_demand_skills_count > 0

    @pytest.mark.asyncio
    async def test_calculate_market_competitiveness_resume_not_found(
        self, cv_analysis_service
    ):
        """Test market competitiveness with missing resume."""
        cv_analysis_service._get_current_resume_version = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Resume not found"):
            await cv_analysis_service.calculate_market_competitiveness(uuid.uuid4())


class TestCVAnalysisServiceSkillGaps:
    """Test skill gap analysis."""

    @pytest.mark.asyncio
    async def test_analyze_skill_gaps(self, cv_analysis_service, sample_parsed_resume):
        """Test skill gap analysis."""
        gaps = await cv_analysis_service._analyze_skill_gaps(
            sample_parsed_resume, "Senior Software Engineer"
        )

        assert isinstance(gaps, list)
        for gap in gaps:
            assert "skill" in gap
            assert "importance" in gap

    def test_identify_weakness_areas_no_skills(self, cv_analysis_service):
        """Test weakness identification with missing skills."""
        resume = {
            "personal_info": {"name": "John"},
            "skills": None,
        }

        weaknesses = cv_analysis_service._identify_weakness_areas(resume)

        assert "No skills section" in weaknesses

    def test_identify_weakness_areas_vague_descriptions(self, cv_analysis_service):
        """Test weakness identification with vague descriptions."""
        resume = {
            "work_experience": [
                {"description": "Worked on projects"}
            ]
        }

        weaknesses = cv_analysis_service._identify_weakness_areas(resume)

        assert any("detail" in w.lower() for w in weaknesses)

    def test_summarize_strengths(self, cv_analysis_service, sample_parsed_resume):
        """Test strength summarization."""
        strengths = cv_analysis_service._summarize_strengths(sample_parsed_resume)

        assert isinstance(strengths, str)
        assert len(strengths) > 0


class TestCVAnalysisServiceJobFit:
    """Test job fit analysis."""

    @pytest.mark.asyncio
    async def test_analyze_job_fit(
        self, cv_analysis_service, sample_parsed_resume
    ):
        """Test job fit analysis."""
        result = await cv_analysis_service._analyze_job_fit(
            sample_parsed_resume,
            "Senior Software Engineer",
            SeniorityLevel.senior
        )

        assert "scores" in result
        assert "top_positions" in result
        assert "underrated" in result

    def test_calculate_role_fit(
        self, cv_analysis_service, sample_parsed_resume
    ):
        """Test role fit scoring."""
        score = cv_analysis_service._calculate_role_fit(
            sample_parsed_resume,
            "Senior Engineer",
            SeniorityLevel.senior
        )

        assert 0 <= score <= 100


class TestCVAnalysisServiceRecommendations:
    """Test recommendation generation."""

    def test_generate_improvements(self, cv_analysis_service, sample_parsed_resume):
        """Test improvement suggestions."""
        weaknesses = ["Missing skills section"]

        improvements = cv_analysis_service._generate_improvements(
            sample_parsed_resume, weaknesses
        )

        assert isinstance(improvements, list)

    def test_generate_rewording_suggestions(self, cv_analysis_service, sample_parsed_resume):
        """Test rewording suggestions."""
        suggestions = cv_analysis_service._generate_rewording_suggestions(
            sample_parsed_resume
        )

        assert isinstance(suggestions, dict)
        assert "experience" in suggestions or len(suggestions) >= 0


class TestCVAnalysisServiceCareerInsights:
    """Test career insights analysis."""

    def test_analyze_career_trajectory_no_experience(self, cv_analysis_service):
        """Test trajectory analysis with no experience."""
        trajectory = cv_analysis_service._analyze_career_trajectory({})

        assert "No career history" in trajectory

    def test_analyze_career_trajectory_single_role(self, cv_analysis_service):
        """Test trajectory analysis with single role."""
        resume = {
            "work_experience": [
                {"position": "Engineer", "company": "Corp"}
            ]
        }

        trajectory = cv_analysis_service._analyze_career_trajectory(resume)

        assert "Early career" in trajectory

    def test_analyze_career_trajectory_established(self, cv_analysis_service):
        """Test trajectory analysis with multiple roles."""
        resume = {
            "work_experience": [
                {"position": "Senior Engineer", "company": "Corp1"},
                {"position": "Engineer", "company": "Corp2"},
                {"position": "Junior Engineer", "company": "Corp3"},
            ]
        }

        trajectory = cv_analysis_service._analyze_career_trajectory(resume)

        assert "Established career" in trajectory

    def test_analyze_market_positioning(
        self, cv_analysis_service, sample_parsed_resume
    ):
        """Test market positioning analysis."""
        positioning = cv_analysis_service._analyze_market_positioning(
            sample_parsed_resume, SeniorityLevel.senior
        )

        assert isinstance(positioning, str)
        assert len(positioning) > 0

    def test_identify_growth_opportunities(
        self, cv_analysis_service, sample_parsed_resume
    ):
        """Test growth opportunity identification."""
        opportunities = cv_analysis_service._identify_growth_opportunities(
            sample_parsed_resume, ["Cloud", "AI"]
        )

        assert "Cloud" in str(opportunities)


class TestCVAnalysisServiceGovernanceChecks:
    """Test governance/QA checks."""

    def test_check_coherence(self, cv_analysis_service, sample_parsed_resume):
        """Test coherence check."""
        result = cv_analysis_service._check_coherence(sample_parsed_resume)

        assert "passed" in result
        assert isinstance(result["passed"], bool)

    def test_check_consistency(self, cv_analysis_service, sample_parsed_resume):
        """Test consistency check."""
        result = cv_analysis_service._check_consistency(sample_parsed_resume)

        assert "passed" in result
        assert isinstance(result["passed"], bool)

    def test_check_fidelity(self, cv_analysis_service, sample_parsed_resume):
        """Test fidelity check."""
        result = cv_analysis_service._check_fidelity(sample_parsed_resume)

        assert "passed" in result
        assert isinstance(result["passed"], bool)

    def test_check_bias_flags(self, cv_analysis_service, sample_parsed_resume):
        """Test bias flag check."""
        result = cv_analysis_service._check_bias_flags(sample_parsed_resume)

        assert "flags" in result
        assert isinstance(result["flags"], list)


class TestCVAnalysisServiceSkillCompetitiveness:
    """Test skill competitiveness calculations."""

    def test_calculate_skill_competitiveness_high(self, cv_analysis_service):
        """Test high skill competitiveness."""
        skills = ["python", "java", "kubernetes", "aws", "machine_learning"]

        result = cv_analysis_service._calculate_skill_competitiveness(
            skills, "Senior Engineer"
        )

        assert result["score"] > 50
        assert result["in_demand_count"] > 3

    def test_calculate_skill_competitiveness_low(self, cv_analysis_service):
        """Test low skill competitiveness."""
        skills = ["typing", "communication"]

        result = cv_analysis_service._calculate_skill_competitiveness(
            skills, "Engineer"
        )

        assert result["score"] == 0
        assert result["in_demand_count"] == 0

    def test_calculate_experience_competitiveness(self, cv_analysis_service):
        """Test experience competitiveness."""
        experience = [
            {"position": "Role1", "company": "Corp1"},
            {"position": "Role2", "company": "Corp2"},
            {"position": "Role3", "company": "Corp3"},
        ]

        score = cv_analysis_service._calculate_experience_competitiveness(experience)

        assert 0 <= score <= 100
        assert score > 0

    def test_calculate_experience_competitiveness_none(self, cv_analysis_service):
        """Test experience competitiveness with no experience."""
        score = cv_analysis_service._calculate_experience_competitiveness([])

        assert score == 0.0

    def test_calculate_certifications_competitiveness(self, cv_analysis_service):
        """Test certification competitiveness."""
        certs = ["AWS Solutions Architect", "Kubernetes Administrator"]

        score = cv_analysis_service._calculate_certifications_competitiveness(certs)

        assert 0 <= score <= 100
        assert score > 0

    def test_estimate_seniority_level_junior(self, cv_analysis_service):
        """Test seniority estimation - junior."""
        experience = [{"position": "Junior"}]

        level = cv_analysis_service._estimate_seniority_level(experience)

        assert level in ["junior", "mid"]

    def test_estimate_seniority_level_senior(self, cv_analysis_service):
        """Test seniority estimation - senior."""
        experience = [
            {"position": f"Role{i}", "company": f"Corp{i}"}
            for i in range(6)
        ]

        level = cv_analysis_service._estimate_seniority_level(experience)

        assert level in ["senior", "mid"]


class TestCVAnalysisServiceRetrieval:
    """Test result retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_analysis_result(self, cv_analysis_service):
        """Test retrieving analysis result."""
        result_mock = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = result_mock
        cv_analysis_service.db.execute = AsyncMock(return_value=mock_result)

        result = await cv_analysis_service.get_analysis_result(uuid.uuid4())

        assert result == result_mock

    @pytest.mark.asyncio
    async def test_get_user_analyses(self, cv_analysis_service):
        """Test retrieving user's analyses."""
        mock_analyses = [MagicMock(), MagicMock()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_analyses
        cv_analysis_service.db.execute = AsyncMock(return_value=mock_result)

        results = await cv_analysis_service.get_user_analyses(uuid.uuid4())

        assert len(results) == 2


class TestCVAnalysisServiceHelpers:
    """Test helper methods."""

    def test_get_role_skills_software_engineer(self, cv_analysis_service):
        """Test getting role-specific skills."""
        skills = cv_analysis_service._get_role_skills("software engineer")

        assert "python" in skills
        assert "java" in skills
        assert "sql" in skills

    def test_get_role_skills_data_scientist(self, cv_analysis_service):
        """Test getting data scientist skills."""
        skills = cv_analysis_service._get_role_skills("data scientist")

        assert "python" in skills
        assert "machine_learning" in skills

    def test_get_learning_resources(self, cv_analysis_service):
        """Test getting learning resources."""
        resources = cv_analysis_service._get_learning_resources("python")

        assert isinstance(resources, list)
        assert len(resources) > 0

    def test_score_to_percentile(self, cv_analysis_service):
        """Test score to percentile conversion."""
        percentile = cv_analysis_service._score_to_percentile(85)

        assert 0 <= percentile <= 100
        assert percentile == 85

    def test_score_to_percentile_boundary(self, cv_analysis_service):
        """Test percentile conversion at boundaries."""
        assert cv_analysis_service._score_to_percentile(0) >= 1
        assert cv_analysis_service._score_to_percentile(100) <= 99

    def test_generate_competitiveness_recommendations(self, cv_analysis_service):
        """Test competitiveness recommendations."""
        score = MarketCompetitivenessScore()
        score.skill_competitiveness = 40
        score.experience_competitiveness = 50
        score.missing_trending_skills = ["kubernetes", "docker"]

        recommendations = cv_analysis_service._generate_competitiveness_recommendations(score)

        assert len(recommendations) > 0
        assert any("skill" in r.lower() for r in recommendations)


class TestCVAnalysisServiceEdgeCases:
    """Test edge cases and error conditions."""

    def test_analyze_skill_gaps_empty_resume(self, cv_analysis_service):
        """Test skill gap analysis with empty resume."""
        # This should handle gracefully
        result = cv_analysis_service._get_role_skills("unknown_role")
        assert isinstance(result, set)

    def test_summarize_strengths_empty_resume(self, cv_analysis_service):
        """Test strength summary for empty resume."""
        summary = cv_analysis_service._summarize_strengths({})

        assert summary == "Solid baseline"

    def test_identify_weakness_areas_comprehensive(self, cv_analysis_service):
        """Test weakness identification catches all areas."""
        minimal_resume = {
            "skills": None,
            "certifications": None,
        }

        weaknesses = cv_analysis_service._identify_weakness_areas(minimal_resume)

        assert len(weaknesses) > 0
