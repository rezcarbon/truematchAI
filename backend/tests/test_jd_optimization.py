"""Comprehensive tests for JD Optimization Service."""
from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.jd_version import JDVersion
from app.models.position import Position
from app.services.jd_optimization import JDDimension, JDOptimizationService


@pytest.fixture
def jd_service():
    """Create a JD optimization service with mock DB."""
    mock_db = AsyncMock(spec=AsyncSession)
    return JDOptimizationService(mock_db)


@pytest.fixture
def sample_position():
    """Create a sample position."""
    position = MagicMock(spec=Position)
    position.id = uuid.uuid4()
    position.user_id = uuid.uuid4()
    position.title = "Senior Software Engineer"
    return position


@pytest.fixture
def sample_jd_version():
    """Create a sample JD version."""
    version = MagicMock(spec=JDVersion)
    version.id = uuid.uuid4()
    version.position_id = uuid.uuid4()
    version.version = 1
    version.created_at = datetime.utcnow()
    version.parsed_requirements = {
        "clarity_score": 75,
        "completeness_score": 80,
        "specificity_score": 70,
        "fairness_score": 85,
        "accessibility_score": 60,
        "market_competitiveness_score": 78,
        "skill_alignment_score": 82,
        "growth_opportunity_score": 65,
        "compliance_score": 90,
        "engagement_appeal_score": 72,
        "required_skills": ["python", "java", "sql"],
        "complexity_score": 75,
        "seniority_level": "senior",
        "min_years_experience": 5,
    }
    version.jd_issues = {
        "clarity": [],
        "completeness": ["missing_reporting_structure"],
    }
    return version


class TestJDDimension:
    """Test JDDimension class."""

    def test_dimension_creation(self):
        """Test creating a dimension."""
        dimension = JDDimension(
            name="Clarity",
            weight=0.10,
            description="How clear the JD is",
        )

        assert dimension.name == "Clarity"
        assert dimension.weight == 0.10
        assert dimension.min_score == 0.0
        assert dimension.max_score == 100.0

    def test_dimension_custom_scores(self):
        """Test dimension with custom min/max scores."""
        dimension = JDDimension(
            name="Test",
            weight=0.5,
            description="Test",
            min_score=10.0,
            max_score=90.0,
        )

        assert dimension.min_score == 10.0
        assert dimension.max_score == 90.0


class TestJDOptimizationServiceAnalyzeJD:
    """Test JD analysis functionality."""

    @pytest.mark.asyncio
    async def test_analyze_jd_success(self, jd_service, sample_position, sample_jd_version):
        """Test successful JD analysis."""
        # Setup mocks
        jd_service._get_position = AsyncMock(return_value=sample_position)
        jd_service._get_latest_jd_version = AsyncMock(return_value=sample_jd_version)

        # Execute
        result = await jd_service.analyze_jd(sample_position.id, sample_position.user_id)

        # Verify
        assert result["position_id"] == str(sample_position.id)
        assert result["jd_version_id"] == str(sample_jd_version.id)
        assert "dimension_scores" in result
        assert "overall_score" in result
        assert "improvement_areas" in result
        assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_analyze_jd_position_not_found(self, jd_service):
        """Test analysis when position not found."""
        jd_service._get_position = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Position .* not found"):
            await jd_service.analyze_jd(uuid.uuid4(), uuid.uuid4())

    @pytest.mark.asyncio
    async def test_analyze_jd_no_version(self, jd_service, sample_position):
        """Test analysis when no JD version found."""
        jd_service._get_position = AsyncMock(return_value=sample_position)
        jd_service._get_latest_jd_version = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="No JD version found"):
            await jd_service.analyze_jd(sample_position.id, sample_position.user_id)

    @pytest.mark.asyncio
    async def test_analyze_jd_dimension_scores(self, jd_service, sample_position, sample_jd_version):
        """Test that all dimensions are scored."""
        jd_service._get_position = AsyncMock(return_value=sample_position)
        jd_service._get_latest_jd_version = AsyncMock(return_value=sample_jd_version)

        result = await jd_service.analyze_jd(sample_position.id, sample_position.user_id)

        # Verify all dimensions are present
        for dim_key in JDOptimizationService.DIMENSIONS:
            assert dim_key in result["dimension_scores"]
            assert "score" in result["dimension_scores"][dim_key]
            assert "weight" in result["dimension_scores"][dim_key]
            assert "name" in result["dimension_scores"][dim_key]

    def test_calculate_weighted_score(self, jd_service):
        """Test weighted score calculation."""
        dimension_scores = {
            "clarity": {"score": 80, "weight": 0.10},
            "completeness": {"score": 90, "weight": 0.12},
            "specificity": {"score": 70, "weight": 0.12},
            "fairness": {"score": 85, "weight": 0.10},
            "accessibility": {"score": 60, "weight": 0.08},
            "market_competitiveness": {"score": 75, "weight": 0.12},
            "skill_alignment": {"score": 80, "weight": 0.10},
            "growth_opportunity": {"score": 65, "weight": 0.08},
            "compliance": {"score": 90, "weight": 0.10},
            "engagement_appeal": {"score": 70, "weight": 0.08},
        }

        score = jd_service._calculate_weighted_score(dimension_scores)

        assert 0 <= score <= 100
        # Score should be weighted average
        expected = (
            80 * 0.10
            + 90 * 0.12
            + 70 * 0.12
            + 85 * 0.10
            + 60 * 0.08
            + 75 * 0.12
            + 80 * 0.10
            + 65 * 0.08
            + 90 * 0.10
            + 70 * 0.08
        )
        assert abs(score - expected) < 1.0

    def test_identify_improvements(self, jd_service):
        """Test improvement identification."""
        dimension_scores = {
            "clarity": {"name": "Clarity", "score": 50, "weight": 0.10, "max_score": 100},
            "completeness": {"name": "Completeness", "score": 95, "weight": 0.12, "max_score": 100},
        }

        improvements = jd_service._identify_improvements(dimension_scores)

        assert len(improvements) > 0
        # Clarity should be identified as improvement opportunity
        clarity_improvement = next(
            (i for i in improvements if i["dimension"] == "Clarity"), None
        )
        assert clarity_improvement is not None
        assert clarity_improvement["potential_gain"] == 50

    def test_generate_recommendations(self, jd_service, sample_jd_version):
        """Test recommendation generation."""
        dimension_scores = {
            "clarity": {"name": "Clarity", "score": 65, "weight": 0.10},
            "completeness": {"name": "Completeness", "score": 75, "weight": 0.12},
            "fairness": {"name": "Fairness", "score": 85, "weight": 0.10},
        }

        recommendations = jd_service._generate_recommendations(dimension_scores, sample_jd_version)

        assert len(recommendations) > 0
        assert any("language" in r.lower() for r in recommendations)


class TestJDOptimizationServiceVersionComparison:
    """Test JD version comparison functionality."""

    @pytest.mark.asyncio
    async def test_compare_jd_versions(self, jd_service):
        """Test comparing two JD versions."""
        v1 = MagicMock(spec=JDVersion)
        v1.id = uuid.uuid4()
        v1.position_id = uuid.uuid4()
        v1.version = 1
        v1.created_at = datetime(2026, 1, 1)
        v1.parsed_requirements = {
            "required_skills": ["python", "java"],
            "min_years_experience": 3,
        }
        v1.jd_issues = {}

        v2 = MagicMock(spec=JDVersion)
        v2.id = uuid.uuid4()
        v2.position_id = v1.position_id
        v2.version = 2
        v2.created_at = datetime(2026, 6, 1)
        v2.parsed_requirements = {
            "required_skills": ["python", "java", "sql"],
            "min_years_experience": 5,
        }
        v2.jd_issues = {}

        jd_service._get_jd_version = AsyncMock(side_effect=lambda vid: v1 if vid == v1.id else v2)

        result = await jd_service.compare_jd_versions(v1.position_id, v1.id, v2.id)

        assert result["position_id"] == str(v1.position_id)
        assert "requirement_changes" in result
        assert "requirement_additions" in result
        assert "requirement_removals" in result

    @pytest.mark.asyncio
    async def test_compare_versions_mismatch(self, jd_service):
        """Test comparison with mismatched positions."""
        v1 = MagicMock(spec=JDVersion)
        v1.id = uuid.uuid4()
        v1.position_id = uuid.uuid4()

        v2 = MagicMock(spec=JDVersion)
        v2.id = uuid.uuid4()
        v2.position_id = uuid.uuid4()

        jd_service._get_jd_version = AsyncMock(side_effect=lambda vid: v1 if vid == v1.id else v2)

        with pytest.raises(ValueError, match="Version positions do not match"):
            await jd_service.compare_jd_versions(uuid.uuid4(), v1.id, v2.id)


class TestJDOptimizationServiceDriftDetection:
    """Test requirement drift detection."""

    @pytest.mark.asyncio
    async def test_detect_requirement_drift_insufficient_versions(self, jd_service):
        """Test drift detection with insufficient versions."""
        jd_service._get_all_jd_versions = AsyncMock(return_value=[])

        result = await jd_service.detect_requirement_drift(uuid.uuid4())

        assert result["drift_detected"] is False

    @pytest.mark.asyncio
    async def test_detect_requirement_drift_complexity_creep(self, jd_service):
        """Test detection of complexity creep."""
        v1 = MagicMock()
        v1.version = 1
        v1.created_at = datetime(2026, 1, 1)
        v1.parsed_requirements = {"complexity_score": 50, "required_skills": ["python"]}

        v2 = MagicMock()
        v2.version = 2
        v2.created_at = datetime(2026, 6, 1)
        v2.parsed_requirements = {"complexity_score": 75, "required_skills": ["python", "java"]}

        position_id = uuid.uuid4()
        jd_service._get_all_jd_versions = AsyncMock(return_value=[v1, v2])

        result = await jd_service.detect_requirement_drift(position_id)

        assert result["total_versions"] == 2
        assert "complexity_trend" in result
        assert len(result["complexity_trend"]) == 2

    @pytest.mark.asyncio
    async def test_detect_requirement_drift_skill_growth(self, jd_service):
        """Test detection of skill requirement growth."""
        v1 = MagicMock()
        v1.version = 1
        v1.created_at = datetime(2026, 1, 1)
        v1.parsed_requirements = {"required_skills": ["python"]}

        v2 = MagicMock()
        v2.version = 2
        v2.created_at = datetime(2026, 6, 1)
        v2.parsed_requirements = {"required_skills": ["python", "java", "sql"]}

        jd_service._get_all_jd_versions = AsyncMock(return_value=[v1, v2])

        result = await jd_service.detect_requirement_drift(uuid.uuid4())

        assert "skill_count_trend" in result
        assert len(result["skill_count_trend"]) == 2


class TestJDOptimizationServiceOptimizeRecommendations:
    """Test JD optimization recommendations."""

    @pytest.mark.asyncio
    async def test_optimize_jd_recommendations_success(
        self, jd_service, sample_position, sample_jd_version
    ):
        """Test generating optimization recommendations."""
        jd_service._get_position = AsyncMock(return_value=sample_position)
        jd_service._get_latest_jd_version = AsyncMock(return_value=sample_jd_version)
        jd_service.analyze_jd = AsyncMock(
            return_value={
                "dimension_scores": {
                    "clarity": {"score": 65, "name": "Clarity"},
                    "completeness": {"score": 95, "name": "Completeness"},
                }
            }
        )

        result = await jd_service.optimize_jd_recommendations(sample_position.id)

        assert "immediate_actions" in result
        assert "high_priority" in result
        assert "medium_priority" in result
        assert "low_priority" in result
        assert result["position_id"] == str(sample_position.id)

    @pytest.mark.asyncio
    async def test_optimize_jd_position_not_found(self, jd_service):
        """Test recommendation generation with missing position."""
        jd_service._get_position = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Position .* not found"):
            await jd_service.optimize_jd_recommendations(uuid.uuid4())


class TestJDOptimizationServiceExtractMethods:
    """Test helper methods for requirement extraction."""

    def test_extract_requirement_changes_skills(self, jd_service):
        """Test extracting changed skill requirements."""
        v1 = MagicMock()
        v1.parsed_requirements = {
            "required_skills": ["python", "java"],
            "skill_experience": {"python": 3, "java": 5},
        }

        v2 = MagicMock()
        v2.parsed_requirements = {
            "required_skills": ["python", "java"],
            "skill_experience": {"python": 5, "java": 5},
        }

        changes = jd_service._extract_requirement_changes(v1, v2)

        assert len(changes) > 0
        python_change = next((c for c in changes if c["skill"] == "python"), None)
        assert python_change is not None
        assert python_change["from"] == 3
        assert python_change["to"] == 5

    def test_extract_additions(self, jd_service):
        """Test extracting added requirements."""
        v1 = MagicMock()
        v1.parsed_requirements = {"required_skills": ["python", "java"]}

        v2 = MagicMock()
        v2.parsed_requirements = {
            "required_skills": ["python", "java", "sql"],
            "skill_experience": {"sql": 3},
        }

        additions = jd_service._extract_additions(v1, v2)

        assert len(additions) == 1
        assert additions[0]["skill"] == "sql"
        assert additions[0]["type"] == "new_requirement"

    def test_extract_removals(self, jd_service):
        """Test extracting removed requirements."""
        v1 = MagicMock()
        v1.parsed_requirements = {
            "required_skills": ["python", "java", "sql"],
            "skill_experience": {"sql": 3},
        }

        v2 = MagicMock()
        v2.parsed_requirements = {"required_skills": ["python", "java"]}

        removals = jd_service._extract_removals(v1, v2)

        assert len(removals) == 1
        assert removals[0]["skill"] == "sql"
        assert removals[0]["type"] == "removed_requirement"

    def test_analyze_scope_change(self, jd_service):
        """Test scope change analysis."""
        v1 = MagicMock()
        v1.parsed_requirements = {
            "complexity_score": 60,
            "seniority_level": "mid",
            "min_years_experience": 3,
        }

        v2 = MagicMock()
        v2.parsed_requirements = {
            "complexity_score": 80,
            "seniority_level": "senior",
            "min_years_experience": 5,
        }

        scope_change = jd_service._analyze_scope_change(v1, v2)

        assert scope_change["complexity_change"] == 20
        assert scope_change["seniority_change"] is True
        assert scope_change["min_years_experience_change"] == 2


class TestJDOptimizationServiceDimensionActions:
    """Test dimension-specific action generation."""

    def test_get_dimension_action(self, jd_service):
        """Test getting specific dimension actions."""
        action = jd_service._get_dimension_action("clarity", 45)
        assert "Rewrite" in action or "unclear" in action

        action = jd_service._get_dimension_action("fairness", 60)
        assert "bias" in action.lower() or "discriminatory" in action.lower()

        action = jd_service._get_dimension_action("unknown", 50)
        assert action is not None
