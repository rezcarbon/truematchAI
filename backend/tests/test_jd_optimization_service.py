"""Comprehensive integration tests for JD Optimization Service."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from app.engines.client import LLMError
from app.services.jd_optimization_service import JDDimension, JDOptimizationService


@pytest.fixture
def jd_service():
    """Create JD optimization service."""
    return JDOptimizationService()


@pytest.fixture
def sample_jd_text():
    """Sample job description for testing."""
    return """
    Senior Software Engineer

    Location: San Francisco, CA
    Salary: $150,000 - $220,000

    About the Role:
    We are seeking an experienced Senior Software Engineer to join our platform team.
    You will be responsible for designing and implementing scalable systems.

    Requirements:
    - 5+ years of software development experience
    - Strong proficiency in Python, Java, or Go
    - Experience with distributed systems
    - BS in Computer Science or equivalent

    Nice to Have:
    - Experience with Kubernetes
    - Prior startup experience
    - Open source contributions

    Benefits:
    - Health insurance
    - 401k matching
    - Remote work flexibility
    - Professional development budget
    - Generous PTO (25+ days)

    We are committed to building a diverse and inclusive team.
    """


@pytest.fixture
def sample_claude_response():
    """Sample Claude analysis response."""
    return {
        "dimensions": {
            "clarity": {"score": 85, "feedback": "Well-written and clear expectations"},
            "realism": {"score": 75, "feedback": "Some requirements may be challenging"},
            "inclusivity": {"score": 80, "feedback": "Good use of inclusive language"},
            "competitiveness": {"score": 88, "feedback": "Competitive salary and benefits"},
            "specificity": {"score": 82, "feedback": "Good specification of requirements"},
            "skill_accuracy": {"score": 80, "feedback": "Skills well-aligned with role"},
            "bias_indicators": {"score": 90, "feedback": "No obvious bias detected"},
            "growth_potential": {"score": 78, "feedback": "Good development opportunities mentioned"},
            "remote_friendliness": {"score": 85, "feedback": "Clear remote work policy"},
            "diversity_focus": {"score": 82, "feedback": "Explicit diversity commitment"},
        },
        "issues": [
            {
                "type": "vagueness",
                "dimension": "specificity",
                "text": "scalable systems",
                "severity": "low",
            }
        ],
        "suggestions": [
            {
                "dimension": "clarity",
                "action": "Add specific metrics for success",
                "rationale": "Help candidates understand role impact",
            }
        ],
    }


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
        assert dimension.description == "How clear the JD is"

    def test_all_dimensions_created(self, jd_service):
        """Test that all 10 dimensions are properly configured."""
        expected_dimensions = {
            "clarity",
            "realism",
            "inclusivity",
            "competitiveness",
            "specificity",
            "skill_accuracy",
            "bias_indicators",
            "growth_potential",
            "remote_friendliness",
            "diversity_focus",
        }

        assert set(jd_service.DIMENSIONS.keys()) == expected_dimensions

    def test_dimension_weights_sum_to_one(self, jd_service):
        """Test that dimension weights sum to 1.0."""
        total_weight = sum(dim.weight for dim in jd_service.DIMENSIONS.values())
        assert abs(total_weight - 1.0) < 0.001


class TestJDOptimizationServiceAnalyzeJD:
    """Test JD analysis functionality."""

    @pytest.mark.asyncio
    async def test_analyze_jd_detailed_success(
        self, jd_service, sample_jd_text, sample_claude_response
    ):
        """Test successful JD analysis."""
        with patch(
            "app.services.jd_optimization_service._create_with_retry"
        ) as mock_api:
            # Mock Claude response
            mock_response = MagicMock()
            mock_response.content = [
                MagicMock(
                    type="text",
                    text=json.dumps(sample_claude_response),
                )
            ]
            mock_api.return_value = mock_response

            result = await jd_service.analyze_jd_detailed(
                sample_jd_text, "Senior Software Engineer"
            )

            assert "score" in result
            assert "dimensions" in result
            assert "issues" in result
            assert "suggestions" in result
            assert 0 <= result["score"] <= 100
            assert len(result["dimensions"]) == 10

    @pytest.mark.asyncio
    async def test_analyze_jd_dimension_scores(
        self, jd_service, sample_jd_text, sample_claude_response
    ):
        """Test that all dimensions are scored."""
        with patch(
            "app.services.jd_optimization_service._create_with_retry"
        ) as mock_api:
            mock_response = MagicMock()
            mock_response.content = [
                MagicMock(
                    type="text",
                    text=json.dumps(sample_claude_response),
                )
            ]
            mock_api.return_value = mock_response

            result = await jd_service.analyze_jd_detailed(sample_jd_text, "Test Role")

            dimension_names = {d["name"] for d in result["dimensions"]}
            expected_names = {dim.name for dim in jd_service.DIMENSIONS.values()}
            assert dimension_names == expected_names

    @pytest.mark.asyncio
    async def test_analyze_jd_llm_error_handling(self, jd_service, sample_jd_text):
        """Test handling of LLM errors."""
        with patch(
            "app.services.jd_optimization_service._create_with_retry"
        ) as mock_api:
            mock_api.side_effect = LLMError("API call failed")

            with pytest.raises(LLMError):
                await jd_service.analyze_jd_detailed(sample_jd_text, "Test Role")

    @pytest.mark.asyncio
    async def test_analyze_jd_invalid_response_handling(
        self, jd_service, sample_jd_text
    ):
        """Test handling of invalid JSON response."""
        with patch(
            "app.services.jd_optimization_service._create_with_retry"
        ) as mock_api:
            mock_response = MagicMock()
            mock_response.content = [
                MagicMock(
                    type="text",
                    text="Invalid JSON response",
                )
            ]
            mock_api.return_value = mock_response

            result = await jd_service.analyze_jd_detailed(sample_jd_text, "Test Role")

            # Should return default structure
            assert result["score"] >= 0
            assert len(result["dimensions"]) == 10


class TestJDOptimizationServiceComputeQualityScore:
    """Test quality score computation."""

    def test_compute_quality_score_perfect(self, jd_service):
        """Test quality score with all dimensions at 100."""
        dimensions = {
            key: {"score": 100} for key in jd_service.DIMENSIONS.keys()
        }

        score = jd_service.compute_quality_score(dimensions)

        assert score == 100

    def test_compute_quality_score_poor(self, jd_service):
        """Test quality score with all dimensions at 0."""
        dimensions = {key: {"score": 0} for key in jd_service.DIMENSIONS.keys()}

        score = jd_service.compute_quality_score(dimensions)

        assert score == 0

    def test_compute_quality_score_weighted(self, jd_service):
        """Test weighted calculation respects dimension weights."""
        dimensions = {
            "clarity": {"score": 50},  # weight 0.10
            "competitiveness": {"score": 100},  # weight 0.12
        }

        score = jd_service.compute_quality_score(dimensions)

        # Should be between 0 and 100
        assert 0 <= score <= 100

    def test_compute_quality_score_empty(self, jd_service):
        """Test quality score with empty dimensions."""
        score = jd_service.compute_quality_score({})

        assert score == 0

    def test_compute_quality_score_partial_dimensions(self, jd_service):
        """Test quality score with partial dimensions."""
        dimensions = {
            "clarity": {"score": 75},
            "realism": {"score": 80},
        }

        score = jd_service.compute_quality_score(dimensions)

        assert 0 <= score <= 100


class TestJDOptimizationServiceGenerateFixes:
    """Test fix generation for issues."""

    def test_generate_fixes_for_bias_issue(self, jd_service):
        """Test generating fixes for bias issues."""
        issue = {
            "type": "bias",
            "text": "native speaker required",
            "dimension": "bias_indicators",
        }

        fixes = jd_service.generate_fixes_for_issue(issue)

        assert len(fixes) > 0
        assert fixes[0]["priority"] == "high"
        assert "bias" in fixes[0]["action"].lower()

    def test_generate_fixes_for_vagueness(self, jd_service):
        """Test generating fixes for vague requirements."""
        issue = {
            "type": "vagueness",
            "text": "strong programming skills",
            "dimension": "specificity",
        }

        fixes = jd_service.generate_fixes_for_issue(issue)

        assert len(fixes) > 0
        assert "metric" in fixes[0]["action"].lower() or "specific" in fixes[0]["action"].lower()

    def test_generate_fixes_for_unrealistic(self, jd_service):
        """Test generating fixes for unrealistic requirements."""
        issue = {
            "type": "unrealistic",
            "text": "10+ years in Python",
            "dimension": "realism",
        }

        fixes = jd_service.generate_fixes_for_issue(issue)

        assert len(fixes) > 0
        assert fixes[0]["priority"] == "high"

    def test_generate_fixes_for_unclear(self, jd_service):
        """Test generating fixes for unclear requirements."""
        issue = {
            "type": "unclear",
            "text": "various technologies",
            "dimension": "clarity",
        }

        fixes = jd_service.generate_fixes_for_issue(issue)

        assert len(fixes) > 0
        assert fixes[0]["priority"] == "medium"

    def test_generate_fixes_for_missing_context(self, jd_service):
        """Test generating fixes for missing context."""
        issue = {
            "type": "missing_context",
            "text": "reporting structure",
            "dimension": "clarity",
        }

        fixes = jd_service.generate_fixes_for_issue(issue)

        assert len(fixes) > 0
        assert "Add" in fixes[0]["action"] or "add" in fixes[0]["action"]

    def test_generate_fixes_for_unknown_type(self, jd_service):
        """Test generating fixes for unknown issue type."""
        issue = {
            "type": "unknown_type",
            "text": "some issue",
            "dimension": "clarity",
        }

        fixes = jd_service.generate_fixes_for_issue(issue)

        assert len(fixes) > 0
        assert "Address" in fixes[0]["action"]


class TestJDOptimizationServiceComputeMarketCompetitiveness:
    """Test market competitiveness scoring."""

    def test_compute_market_competitiveness_with_salary(self, jd_service):
        """Test competitiveness score with salary info."""
        jd = "Senior Engineer, Salary: $150,000 - $200,000"

        score = jd_service.compute_market_competitiveness(jd)

        assert score > 50  # Should be boosted by salary mention

    def test_compute_market_competitiveness_with_benefits(self, jd_service):
        """Test competitiveness score with benefits."""
        jd = "Health insurance, 401k, remote work, PTO"

        score = jd_service.compute_market_competitiveness(jd)

        assert score > 50

    def test_compute_market_competitiveness_complete_package(self, jd_service):
        """Test competitiveness score with complete compensation package."""
        jd = """
        Salary: $180,000
        Benefits: Health insurance, 401k
        Remote: Fully remote or hybrid
        Growth: Training budget and mentorship
        Diversity: Committed to diverse hiring
        """

        score = jd_service.compute_market_competitiveness(jd)

        assert score >= 70

    def test_compute_market_competitiveness_minimal(self, jd_service):
        """Test competitiveness score with minimal info."""
        jd = "Software Engineer position available"

        score = jd_service.compute_market_competitiveness(jd)

        assert 0 <= score <= 100

    def test_compute_market_competitiveness_with_market_data(self, jd_service):
        """Test competitiveness score with market data provided."""
        jd = "Salary: $150,000"
        market_data = {"avg_salary_min": 120000, "avg_salary_max": 200000}

        score = jd_service.compute_market_competitiveness(jd, market_data)

        assert 0 <= score <= 100


class TestJDOptimizationServicePromptBuilding:
    """Test prompt construction for Claude."""

    def test_build_analysis_prompt(self, jd_service):
        """Test prompt building."""
        jd_text = "Senior Engineer role"
        position_title = "Senior Software Engineer"

        prompt = jd_service._build_analysis_prompt(jd_text, position_title)

        assert "Senior Software Engineer" in prompt
        assert "Senior Engineer role" in prompt
        assert all(dim.name in prompt for dim in jd_service.DIMENSIONS.values())

    def test_build_analysis_prompt_includes_dimensions(self, jd_service):
        """Test that prompt includes all dimensions."""
        prompt = jd_service._build_analysis_prompt("Test JD", "Test Role")

        for dimension in jd_service.DIMENSIONS.values():
            assert dimension.name in prompt


class TestJDOptimizationServiceParseResponse:
    """Test response parsing."""

    def test_parse_analysis_response_valid_json(self, jd_service, sample_claude_response):
        """Test parsing valid JSON response."""
        response_text = json.dumps(sample_claude_response)

        result = jd_service._parse_analysis_response(response_text)

        assert "dimensions" in result
        assert "issues" in result
        assert "suggestions" in result

    def test_parse_analysis_response_with_surrounding_text(
        self, jd_service, sample_claude_response
    ):
        """Test parsing JSON response with surrounding text."""
        response_text = (
            "Here's my analysis:\n"
            + json.dumps(sample_claude_response)
            + "\nThat's my analysis."
        )

        result = jd_service._parse_analysis_response(response_text)

        assert "dimensions" in result

    def test_parse_analysis_response_invalid_json(self, jd_service):
        """Test parsing invalid JSON response."""
        response_text = "This is not JSON"

        result = jd_service._parse_analysis_response(response_text)

        # Should return default structure
        assert "dimensions" in result
        assert len(result["dimensions"]) == 10

    def test_parse_analysis_response_empty_json(self, jd_service):
        """Test parsing empty JSON."""
        response_text = "{}"

        result = jd_service._parse_analysis_response(response_text)

        # Should handle gracefully
        assert isinstance(result, dict)


class TestJDOptimizationServiceIntegration:
    """Integration tests for the service."""

    @pytest.mark.asyncio
    async def test_full_analysis_workflow(
        self, jd_service, sample_jd_text, sample_claude_response
    ):
        """Test complete analysis workflow."""
        with patch(
            "app.services.jd_optimization_service._create_with_retry"
        ) as mock_api:
            mock_response = MagicMock()
            mock_response.content = [
                MagicMock(
                    type="text",
                    text=json.dumps(sample_claude_response),
                )
            ]
            mock_api.return_value = mock_response

            # Analyze JD
            analysis = await jd_service.analyze_jd_detailed(
                sample_jd_text, "Senior Software Engineer"
            )

            # Verify results
            assert analysis["score"] > 0
            assert len(analysis["dimensions"]) == 10

            # Check for specific issues
            if analysis["issues"]:
                for issue in analysis["issues"]:
                    fixes = jd_service.generate_fixes_for_issue(issue)
                    assert len(fixes) > 0

    @pytest.mark.asyncio
    async def test_analysis_with_score_computation(
        self, jd_service, sample_jd_text, sample_claude_response
    ):
        """Test that analysis score computation works correctly."""
        with patch(
            "app.services.jd_optimization_service._create_with_retry"
        ) as mock_api:
            mock_response = MagicMock()
            mock_response.content = [
                MagicMock(
                    type="text",
                    text=json.dumps(sample_claude_response),
                )
            ]
            mock_api.return_value = mock_response

            result = await jd_service.analyze_jd_detailed(sample_jd_text, "Test Role")

            # Compute score from dimensions
            dimension_dict = {}
            for dim in result["dimensions"]:
                dimension_dict[dim["name"].lower().replace(" ", "_")] = {
                    "score": dim["score"]
                }

            computed_score = jd_service.compute_quality_score(dimension_dict)
            assert computed_score == result["score"]
