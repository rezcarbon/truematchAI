"""Tests for salary benchmarking module."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.salary_benchmarking.salary_model import (
    SalaryBenchmarkingModel,
    SalaryData,
    OfferRecommendation,
    SalaryBenchmark,
)
from app.ml.salary_benchmarking.salary_service import SalaryBenchmarkingService


class TestSalaryData:
    """Test SalaryData dataclass."""

    def test_salary_data_creation(self):
        """Test creating salary data."""
        data = SalaryData(
            role_title="Software Engineer",
            level="mid",
            location="San Francisco, CA",
            min_salary=120000,
            max_salary=210000,
            median_salary=160000,
            percentile_25=140000,
            percentile_75=185000,
            data_points=2341,
            data_source="levels.fyi",
        )

        assert data.role_title == "Software Engineer"
        assert data.level == "mid"
        assert data.median_salary == 160000
        assert data.data_points == 2341

    def test_salary_data_to_dict(self):
        """Test salary data serialization."""
        data = SalaryData(
            role_title="Software Engineer",
            level="mid",
            location="San Francisco, CA",
            min_salary=120000,
            max_salary=210000,
            median_salary=160000,
            percentile_25=140000,
            percentile_75=185000,
            data_points=2341,
            data_source="levels.fyi",
        )

        result = data.to_dict()

        assert result["role_title"] == "Software Engineer"
        assert result["min_salary"] == 120000
        assert isinstance(result["updated_at"], str)


class TestOfferRecommendation:
    """Test OfferRecommendation dataclass."""

    def test_offer_recommendation_creation(self):
        """Test creating offer recommendation."""
        rec = OfferRecommendation(
            suggested_offer=165000,
            competitive_range=(150000, 185000),
            negotiation_buffer=20000,
            win_likelihood=0.85,
            rationale="Based on 80% skills match",
            comparison_to_market="At market",
        )

        assert rec.suggested_offer == 165000
        assert rec.win_likelihood == 0.85
        assert rec.comparison_to_market == "At market"

    def test_offer_recommendation_to_dict(self):
        """Test offer recommendation serialization."""
        rec = OfferRecommendation(
            suggested_offer=165000,
            competitive_range=(150000, 185000),
            negotiation_buffer=20000,
            win_likelihood=0.85,
            rationale="Based on 80% skills match",
            comparison_to_market="At market",
        )

        result = rec.to_dict()

        assert result["suggested_offer"] == 165000
        assert result["win_likelihood"] == 0.85
        assert result["competitive_range"] == (150000, 185000)


class TestSalaryBenchmarkingModel:
    """Test SalaryBenchmarkingModel."""

    def test_model_initialization(self):
        """Test model initialization."""
        model = SalaryBenchmarkingModel()
        assert model.levels_api_key is None
        assert model.glassdoor_api_key is None

    def test_model_with_api_keys(self):
        """Test model with API keys."""
        model = SalaryBenchmarkingModel(
            levels_api_key="test-key-1",
            glassdoor_api_key="test-key-2",
        )
        assert model.levels_api_key == "test-key-1"
        assert model.glassdoor_api_key == "test-key-2"

    def test_role_title_normalization(self):
        """Test role title normalization."""
        model = SalaryBenchmarkingModel()

        assert model._normalize_role_title("software engineer") == "Software Engineer"
        assert model._normalize_role_title("Senior Developer") == "Software Engineer"
        assert model._normalize_role_title("Data Scientist") == "Data Scientist"
        assert model._normalize_role_title("product manager") == "Product Manager"

    def test_fallback_data_retrieval(self):
        """Test fallback data retrieval."""
        model = SalaryBenchmarkingModel()

        data = model._get_fallback_data(
            "Software Engineer", "mid", "San Francisco, CA"
        )

        assert data is not None
        assert data.role_title == "Software Engineer"
        assert data.level == "mid"
        assert data.median_salary == 160000
        assert data.min_salary == 120000
        assert data.max_salary == 210000

    def test_fallback_data_missing_role(self):
        """Test fallback when role not found."""
        model = SalaryBenchmarkingModel()

        data = model._get_fallback_data(
            "Underwater Basket Weaver", "senior", "San Francisco, CA"
        )

        assert data is None

    def test_offer_recommendation_above_market(self):
        """Test offer recommendation when above market."""
        model = SalaryBenchmarkingModel()

        # Get fallback market data
        market_data = model._get_fallback_data(
            "Software Engineer", "senior", "San Francisco, CA"
        )

        # Perfect skills match, high criticality
        rec = model.recommend_offer(
            market_data=market_data,
            candidate_level="senior",
            candidate_skills_match=1.0,  # Perfect match
            role_criticality=1.2,  # 20% more critical
        )

        assert rec.suggested_offer > market_data.percentile_75
        assert rec.comparison_to_market == "Above market"
        assert rec.win_likelihood > 0.8

    def test_offer_recommendation_at_market(self):
        """Test offer recommendation at market."""
        model = SalaryBenchmarkingModel()

        market_data = model._get_fallback_data(
            "Software Engineer", "mid", "San Francisco, CA"
        )

        # 75% skills match, standard criticality
        rec = model.recommend_offer(
            market_data=market_data,
            candidate_level="mid",
            candidate_skills_match=0.75,
            role_criticality=1.0,
        )

        assert market_data.percentile_25 <= rec.suggested_offer <= market_data.percentile_75
        assert rec.comparison_to_market == "At market"
        assert 0.7 <= rec.win_likelihood <= 0.8

    def test_offer_recommendation_below_market(self):
        """Test offer recommendation below market."""
        model = SalaryBenchmarkingModel()

        market_data = model._get_fallback_data(
            "Software Engineer", "junior", "San Francisco, CA"
        )

        # Poor skills match, low criticality
        rec = model.recommend_offer(
            market_data=market_data,
            candidate_level="junior",
            candidate_skills_match=0.4,  # Poor match
            role_criticality=0.8,  # Less critical
        )

        assert rec.suggested_offer < market_data.median_salary
        assert rec.comparison_to_market == "Below market"
        assert rec.win_likelihood < 0.7

    @pytest.mark.asyncio
    async def test_get_market_data_fallback(self):
        """Test getting market data with fallback."""
        model = SalaryBenchmarkingModel()

        data = await model.get_market_data(
            "Software Engineer", "mid", "San Francisco, CA"
        )

        assert data is not None
        assert data.role_title == "Software Engineer"
        assert data.level == "mid"
        assert 100000 <= data.min_salary <= 200000
        assert data.data_source == "truematch_fallback"

    @pytest.mark.asyncio
    async def test_get_market_data_missing(self):
        """Test getting market data for unknown role."""
        model = SalaryBenchmarkingModel()

        data = await model.get_market_data(
            "Unicorn Trainer", "senior", "Mars"
        )

        assert data is None


class TestSalaryBenchmark:
    """Test SalaryBenchmark dataclass."""

    def test_salary_benchmark_creation(self):
        """Test creating salary benchmark."""
        market_data = SalaryData(
            role_title="Software Engineer",
            level="mid",
            location="San Francisco, CA",
            min_salary=120000,
            max_salary=210000,
            median_salary=160000,
            percentile_25=140000,
            percentile_75=185000,
            data_points=2341,
            data_source="levels.fyi",
        )

        rec = OfferRecommendation(
            suggested_offer=165000,
            competitive_range=(150000, 185000),
            negotiation_buffer=20000,
            win_likelihood=0.85,
            rationale="Test",
            comparison_to_market="At market",
        )

        benchmark = SalaryBenchmark(
            role="Software Engineer",
            location="San Francisco, CA",
            market_data=market_data,
            recommendation=rec,
        )

        assert benchmark.role == "Software Engineer"
        assert benchmark.market_data.median_salary == 160000
        assert benchmark.recommendation.win_likelihood == 0.85

    def test_salary_benchmark_to_dict(self):
        """Test salary benchmark serialization."""
        market_data = SalaryData(
            role_title="Software Engineer",
            level="mid",
            location="San Francisco, CA",
            min_salary=120000,
            max_salary=210000,
            median_salary=160000,
            percentile_25=140000,
            percentile_75=185000,
            data_points=2341,
            data_source="levels.fyi",
        )

        rec = OfferRecommendation(
            suggested_offer=165000,
            competitive_range=(150000, 185000),
            negotiation_buffer=20000,
            win_likelihood=0.85,
            rationale="Test",
            comparison_to_market="At market",
        )

        benchmark = SalaryBenchmark(
            role="Software Engineer",
            location="San Francisco, CA",
            market_data=market_data,
            recommendation=rec,
        )

        result = benchmark.to_dict()

        assert result["role"] == "Software Engineer"
        assert result["market_data"]["median_salary"] == 160000
        assert result["recommendation"]["suggested_offer"] == 165000


class TestSalaryBenchmarkingService:
    """Test SalaryBenchmarkingService."""

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test service initialization."""
        mock_db = AsyncMock(spec=AsyncSession)
        service = SalaryBenchmarkingService(mock_db)

        assert service.db == mock_db
        assert isinstance(service.model, SalaryBenchmarkingModel)

    @pytest.mark.asyncio
    async def test_get_benchmark(self):
        """Test getting benchmark."""
        mock_db = AsyncMock(spec=AsyncSession)
        service = SalaryBenchmarkingService(mock_db)

        benchmark = await service.get_benchmark(
            role_title="Software Engineer",
            level="mid",
            location="San Francisco, CA",
        )

        assert benchmark is not None
        assert benchmark.role == "Software Engineer"
        assert benchmark.market_data.median_salary == 160000
        assert benchmark.recommendation.suggested_offer > 0

    @pytest.mark.asyncio
    async def test_extract_salary_from_resume(self):
        """Test salary extraction from resume."""
        mock_db = AsyncMock(spec=AsyncSession)
        service = SalaryBenchmarkingService(mock_db)

        # Test with numeric salary
        mock_resume = MagicMock()
        mock_resume.parsed_data = {"salary_expectation": 150000}

        salary = service._extract_salary_from_resume(mock_resume)
        assert salary == 150000.0

        # Test with string salary
        mock_resume.parsed_data = {"salary_expectation": "$160000"}
        salary = service._extract_salary_from_resume(mock_resume)
        assert salary == 160000.0

        # Test with no salary
        mock_resume.parsed_data = {}
        salary = service._extract_salary_from_resume(mock_resume)
        assert salary is None

    @pytest.mark.asyncio
    async def test_infer_level_from_position(self):
        """Test level inference from position."""
        mock_db = AsyncMock(spec=AsyncSession)
        service = SalaryBenchmarkingService(mock_db)

        # Test senior
        mock_pos = MagicMock()
        mock_pos.title = "Senior Software Engineer"
        level = service._infer_level_from_position(mock_pos)
        assert level == "senior"

        # Test junior
        mock_pos.title = "Software Engineer"
        level = service._infer_level_from_position(mock_pos)
        assert level == "junior"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
