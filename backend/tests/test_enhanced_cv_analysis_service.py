"""Comprehensive tests for Enhanced CV Analysis Service."""
from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cv_analysis import (
    CVAnalysisRequest,
    CVAnalysisStatus,
    SeniorityLevel,
)
from app.models.resume_version import ResumeVersion
from app.services.enhanced_cv_analysis_service import (
    EnhancedCVAnalysisService,
    SkillWithEvidence,
    SkillGapWithLearning,
    MarketCompetitiveness,
    ActionableRecommendation,
    EvidenceLink,
    EvidenceSource,
    EnhancedCVAnalysisResult,
)


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def enhanced_cv_service(mock_db):
    """Create enhanced CV analysis service with mock DB."""
    return EnhancedCVAnalysisService(mock_db)


@pytest.fixture
def sample_parsed_resume():
    """Create sample parsed resume data."""
    return {
        "personal_info": {
            "name": "Alice Engineer",
            "email": "alice@example.com",
            "github_profile": "https://github.com/alice",
            "linkedin_profile": "https://linkedin.com/in/alice",
        },
        "work_experience": [
            {
                "position": "Senior Software Engineer",
                "company": "Tech Corp",
                "start_date": "2021-01-01",
                "description": "Led Python and AWS cloud architecture for microservices platform",
            },
            {
                "position": "Software Engineer",
                "company": "StartUp Inc",
                "start_date": "2018-01-01",
                "end_date": "2021-01-01",
                "description": "Developed Python and JavaScript applications",
            },
        ],
        "education": [
            {
                "degree": "BS Computer Science",
                "institution": "Tech University",
                "graduation_year": 2018,
            }
        ],
        "skills": ["python", "java", "javascript", "aws", "docker", "kubernetes", "sql"],
        "certifications": ["AWS Solutions Architect", "Kubernetes Administrator"],
        "projects": [
            {
                "title": "Microservices Platform",
                "description": "Built scalable Python microservices using docker and kubernetes",
                "url": "https://github.com/alice/microservices",
            }
        ],
    }


@pytest.fixture
def sample_cv_request():
    """Create a sample CV analysis request."""
    request = MagicMock(spec=CVAnalysisRequest)
    request.id = uuid.uuid4()
    request.user_id = uuid.uuid4()
    request.resume_id = uuid.uuid4()
    request.target_role = "Staff Engineer"
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
    version.is_current = True
    version.created_at = datetime.utcnow()
    return version


class TestEvidenceLink:
    """Test EvidenceLink class."""

    def test_evidence_link_creation(self):
        """Test creating an evidence link."""
        evidence = EvidenceLink(
            source=EvidenceSource.GITHUB,
            url="https://github.com/alice/project",
            title="GitHub Repository",
            verified=True,
        )

        assert evidence.source == EvidenceSource.GITHUB
        assert evidence.url == "https://github.com/alice/project"
        assert evidence.title == "GitHub Repository"
        assert evidence.verified is True

    def test_evidence_link_to_dict(self):
        """Test converting evidence link to dictionary."""
        evidence = EvidenceLink(
            source=EvidenceSource.DOI_PAPER,
            url="https://doi.org/example",
            title="Research Paper",
            verified=False,
        )

        evidence_dict = evidence.to_dict()

        assert evidence_dict["source"] == "doi_paper"
        assert evidence_dict["url"] == "https://doi.org/example"
        assert evidence_dict["verified"] is False


class TestSkillWithEvidence:
    """Test SkillWithEvidence class."""

    def test_skill_creation(self):
        """Test creating a skill with evidence."""
        evidence = EvidenceLink(
            source=EvidenceSource.RESUME,
            url="internal",
            title="Work experience",
            verified=True,
        )

        skill = SkillWithEvidence(
            skill="Python",
            proficiency=8,
            evidence=[evidence],
            verified=True,
            categories=["programming"],
        )

        assert skill.skill == "Python"
        assert skill.proficiency == 8
        assert len(skill.evidence) == 1
        assert skill.verified is True

    def test_skill_to_dict(self):
        """Test converting skill to dictionary."""
        skill = SkillWithEvidence(
            skill="JavaScript",
            proficiency=7,
            evidence=[],
            verified=False,
        )

        skill_dict = skill.to_dict()

        assert skill_dict["skill"] == "JavaScript"
        assert skill_dict["proficiency"] == 7
        assert skill_dict["verified"] is False


class TestSkillGapWithLearning:
    """Test SkillGapWithLearning class."""

    def test_skill_gap_creation(self):
        """Test creating a skill gap with learning path."""
        gap = SkillGapWithLearning(
            skill="Kubernetes",
            importance="high",
            learning_path="Start with Docker, move to Kubernetes",
            estimated_weeks=12,
            priority=1,
        )

        assert gap.skill == "Kubernetes"
        assert gap.importance == "high"
        assert gap.estimated_weeks == 12
        assert gap.priority == 1

    def test_skill_gap_to_dict(self):
        """Test converting skill gap to dictionary."""
        gap = SkillGapWithLearning(
            skill="Machine Learning",
            importance="medium",
            learning_path="Follow Andrew Ng's course",
            estimated_weeks=16,
            resources=[{"platform": "Coursera", "url": "https://coursera.org"}],
        )

        gap_dict = gap.to_dict()

        assert gap_dict["skill"] == "Machine Learning"
        assert gap_dict["estimated_weeks"] == 16
        assert len(gap_dict["resources"]) == 1


class TestMarketCompetitiveness:
    """Test MarketCompetitiveness class."""

    def test_market_competitiveness_creation(self):
        """Test creating market competitiveness data."""
        from app.services.enhanced_cv_analysis_service import PeerComparison

        peer_comp = PeerComparison(
            percentile=75,
            peer_average=72.5,
            top_quartile_value=88.0,
            message="Top performer",
        )

        competitiveness = MarketCompetitiveness(
            score=85,
            percentile=75,
            peer_comparison=peer_comp,
            in_demand_skills_count=5,
            trending_skills=["python", "aws"],
        )

        assert competitiveness.score == 85
        assert competitiveness.percentile == 75
        assert competitiveness.in_demand_skills_count == 5


class TestActionableRecommendation:
    """Test ActionableRecommendation class."""

    def test_recommendation_creation(self):
        """Test creating an actionable recommendation."""
        recommendation = ActionableRecommendation(
            recommendation="Learn system design",
            impact_estimate="high",
            priority=1,
            timeframe_weeks=12,
            resources_needed=["Book", "Online course"],
            expected_outcome="Improved technical depth",
        )

        assert recommendation.recommendation == "Learn system design"
        assert recommendation.impact_estimate == "high"
        assert recommendation.priority == 1


class TestEnhancedCVAnalysisService:
    """Test EnhancedCVAnalysisService."""

    @pytest.mark.asyncio
    async def test_service_initialization(self, enhanced_cv_service):
        """Test service initialization."""
        assert enhanced_cv_service.db is not None
        assert enhanced_cv_service.anthropic_client is not None

    @pytest.mark.asyncio
    async def test_get_analysis_request(self, enhanced_cv_service, sample_cv_request):
        """Test getting analysis request."""
        enhanced_cv_service.db.execute = AsyncMock()
        enhanced_cv_service.db.execute.return_value.scalars.return_value.first = MagicMock(
            return_value=sample_cv_request
        )

        result = await enhanced_cv_service._get_analysis_request(sample_cv_request.id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_estimate_proficiency(self, enhanced_cv_service, sample_parsed_resume):
        """Test proficiency estimation."""
        proficiency = enhanced_cv_service._estimate_proficiency("Python", sample_parsed_resume)

        assert 1 <= proficiency <= 10

    @pytest.mark.asyncio
    async def test_get_role_required_skills(self, enhanced_cv_service):
        """Test getting required skills for a role."""
        skills = enhanced_cv_service._get_role_required_skills("Software Engineer")

        assert "python" in skills
        assert "javascript" in skills

    @pytest.mark.asyncio
    async def test_calculate_skill_competitiveness(self, enhanced_cv_service):
        """Test skill competitiveness calculation."""
        skills = ["python", "java", "javascript", "sql"]
        score = enhanced_cv_service._calculate_skill_competitiveness(skills)

        assert 0 <= score <= 100
        assert score > 0  # Should have some score with these in-demand skills

    @pytest.mark.asyncio
    async def test_calculate_experience_competitiveness(self, enhanced_cv_service):
        """Test experience competitiveness calculation."""
        experience = [
            {"position": "Role 1"},
            {"position": "Role 2"},
            {"position": "Role 3"},
        ]
        score = enhanced_cv_service._calculate_experience_competitiveness(experience)

        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_score_to_percentile(self, enhanced_cv_service):
        """Test score to percentile conversion."""
        percentile = enhanced_cv_service._score_to_percentile(85.0)

        assert 0 <= percentile <= 100

    @pytest.mark.asyncio
    async def test_calculate_salary_boost(self, enhanced_cv_service):
        """Test salary boost calculation."""
        skills = ["python", "aws", "kubernetes"]
        boost = enhanced_cv_service._calculate_salary_boost(skills)

        assert boost >= 0
        assert boost <= 100

    @pytest.mark.asyncio
    async def test_extract_strengths_with_evidence(
        self, enhanced_cv_service, sample_parsed_resume
    ):
        """Test extracting strengths with evidence."""
        with patch.object(
            enhanced_cv_service, "_extract_evidence_from_github", return_value=[]
        ):
            with patch.object(
                enhanced_cv_service, "_extract_evidence_from_linkedin", return_value=[]
            ):
                strengths = await enhanced_cv_service._extract_strengths_with_evidence(
                    sample_parsed_resume
                )

        assert len(strengths) > 0
        assert all(isinstance(s, SkillWithEvidence) for s in strengths)

    @pytest.mark.asyncio
    async def test_extract_evidence_from_resume(
        self, enhanced_cv_service, sample_parsed_resume
    ):
        """Test extracting evidence from resume."""
        evidence = await enhanced_cv_service._extract_evidence_from_resume(
            "Python", sample_parsed_resume
        )

        assert isinstance(evidence, list)
        if evidence:
            assert all(isinstance(e, EvidenceLink) for e in evidence)

    @pytest.mark.asyncio
    async def test_analyze_skill_gaps_with_learning(
        self, enhanced_cv_service, sample_parsed_resume
    ):
        """Test analyzing skill gaps with learning paths."""
        with patch.object(
            enhanced_cv_service, "_generate_learning_path", return_value="Learning path"
        ):
            gaps = await enhanced_cv_service._analyze_skill_gaps_with_learning(
                sample_parsed_resume, "Staff Engineer"
            )

        assert isinstance(gaps, list)
        assert all(isinstance(g, SkillGapWithLearning) for g in gaps)

    @pytest.mark.asyncio
    async def test_calculate_market_competitiveness(
        self, enhanced_cv_service, sample_parsed_resume
    ):
        """Test market competitiveness calculation."""
        competitiveness = await enhanced_cv_service._calculate_market_competitiveness(
            sample_parsed_resume, "Senior Software Engineer"
        )

        assert competitiveness is not None
        assert 0 <= competitiveness.score <= 100
        assert 0 <= competitiveness.percentile <= 100

    @pytest.mark.asyncio
    async def test_generate_actionable_recommendations(
        self, enhanced_cv_service, sample_parsed_resume
    ):
        """Test generating actionable recommendations."""
        with patch.object(
            enhanced_cv_service,
            "_call_claude_api",
            return_value='[{"recommendation": "Learn system design", "impact_estimate": "high"}]',
        ):
            recommendations = await enhanced_cv_service._generate_actionable_recommendations(
                sample_parsed_resume, "Staff Engineer", SeniorityLevel.senior
            )

        assert isinstance(recommendations, list)

    @pytest.mark.asyncio
    async def test_parse_recommendations(self, enhanced_cv_service):
        """Test parsing recommendations from Claude."""
        response = '''
        [
            {
                "recommendation": "Learn system design",
                "impact_estimate": "high",
                "priority": 1,
                "timeframe_weeks": 12
            }
        ]
        '''

        recommendations = await enhanced_cv_service._parse_recommendations(response)

        assert len(recommendations) > 0
        assert isinstance(recommendations[0], ActionableRecommendation)

    @pytest.mark.asyncio
    async def test_get_default_recommendations(
        self, enhanced_cv_service, sample_parsed_resume
    ):
        """Test getting default recommendations."""
        recommendations = enhanced_cv_service._get_default_recommendations(
            sample_parsed_resume, "Senior Engineer"
        )

        assert len(recommendations) > 0
        assert all(isinstance(r, ActionableRecommendation) for r in recommendations)

    @pytest.mark.asyncio
    async def test_calculate_confidence_scores(self, enhanced_cv_service):
        """Test calculating confidence scores."""
        result = EnhancedCVAnalysisResult(
            analysis_request_id=uuid.uuid4(),
            strengths_with_evidence=[
                SkillWithEvidence(skill="Python", proficiency=8, verified=True)
            ],
            gaps_with_learning=[
                SkillGapWithLearning(
                    skill="Kubernetes", importance="high", learning_path="", estimated_weeks=12
                )
            ],
        )

        confidence_scores = await enhanced_cv_service._calculate_confidence_scores(result)

        assert isinstance(confidence_scores, dict)
        assert "strengths_confidence" in confidence_scores
        assert "gaps_confidence" in confidence_scores

    @pytest.mark.asyncio
    async def test_analyze_cv_enhanced_not_found(self, enhanced_cv_service):
        """Test analyze_cv_enhanced with non-existent request."""
        enhanced_cv_service.db.execute = AsyncMock()
        enhanced_cv_service.db.execute.return_value.scalars.return_value.first = MagicMock(
            return_value=None
        )

        with pytest.raises(ValueError):
            await enhanced_cv_service.analyze_cv_enhanced(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_analyze_cv_enhanced_unauthorized(self, enhanced_cv_service, sample_cv_request):
        """Test analyze_cv_enhanced with unauthorized user."""
        enhanced_cv_service.db.execute = AsyncMock()
        enhanced_cv_service.db.execute.return_value.scalars.return_value.first = MagicMock(
            return_value=sample_cv_request
        )

        with pytest.raises(ValueError, match="Unauthorized"):
            await enhanced_cv_service.analyze_cv_enhanced(
                sample_cv_request.id, user_id=uuid.uuid4()
            )


class TestEnhancedCVAnalysisIntegration:
    """Integration tests for enhanced CV analysis."""

    @pytest.mark.asyncio
    async def test_extract_strengths_with_multiple_skills(self, enhanced_cv_service):
        """Test extracting strengths from diverse skill set."""
        resume = {
            "skills": ["Python", "JavaScript", "AWS", "Docker", "SQL"],
            "work_experience": [
                {
                    "description": "Developed Python microservices using Docker and AWS",
                }
            ],
            "projects": [
                {
                    "description": "Built JavaScript frontend with React",
                }
            ],
        }

        with patch.object(
            enhanced_cv_service, "_extract_evidence_from_github", return_value=[]
        ):
            with patch.object(
                enhanced_cv_service, "_extract_evidence_from_linkedin", return_value=[]
            ):
                strengths = await enhanced_cv_service._extract_strengths_with_evidence(resume)

        assert len(strengths) == 5
        python_skill = next((s for s in strengths if s.skill == "Python"), None)
        assert python_skill is not None
        assert python_skill.proficiency > 5

    @pytest.mark.asyncio
    async def test_skill_gap_analysis_completeness(self, enhanced_cv_service):
        """Test that skill gap analysis covers key areas."""
        resume = {
            "skills": ["Python"],  # Only one skill
            "work_experience": [],
            "projects": [],
        }

        gaps = await enhanced_cv_service._analyze_skill_gaps_with_learning(
            resume, "Software Engineer"
        )

        # Should identify gaps for most required skills
        gap_skills = [g.skill for g in gaps]
        assert len(gap_skills) > 0
        assert any("java" in s.lower() for s in gap_skills)

    @pytest.mark.asyncio
    async def test_market_competitiveness_scoring(self, enhanced_cv_service):
        """Test market competitiveness scoring logic."""
        strong_resume = {
            "skills": ["python", "java", "javascript", "aws", "kubernetes"],
            "work_experience": [{"position": "Role"} for _ in range(4)],
        }

        weak_resume = {
            "skills": [],
            "work_experience": [],
        }

        strong_comp = await enhanced_cv_service._calculate_market_competitiveness(
            strong_resume, "Senior Engineer"
        )
        weak_comp = await enhanced_cv_service._calculate_market_competitiveness(
            weak_resume, "Senior Engineer"
        )

        assert strong_comp.score > weak_comp.score


class TestErrorHandling:
    """Test error handling in enhanced CV analysis service."""

    @pytest.mark.asyncio
    async def test_extract_strengths_with_invalid_data(self, enhanced_cv_service):
        """Test extracting strengths with invalid resume data."""
        invalid_resume = {
            "skills": "not a list",  # Invalid
            "work_experience": None,
        }

        strengths = await enhanced_cv_service._extract_strengths_with_evidence(invalid_resume)

        assert isinstance(strengths, list)

    @pytest.mark.asyncio
    async def test_skill_gap_analysis_with_invalid_role(self, enhanced_cv_service):
        """Test skill gap analysis with non-existent role."""
        resume = {"skills": ["Python"]}

        gaps = await enhanced_cv_service._analyze_skill_gaps_with_learning(
            resume, "NonExistentRole123"
        )

        assert isinstance(gaps, list)

    @pytest.mark.asyncio
    async def test_confidence_scores_with_empty_result(self, enhanced_cv_service):
        """Test confidence scores with empty analysis result."""
        result = EnhancedCVAnalysisResult(
            analysis_request_id=uuid.uuid4(),
        )

        scores = await enhanced_cv_service._calculate_confidence_scores(result)

        assert isinstance(scores, dict)
        assert all(0 <= v <= 1 for v in scores.values())
