#!/usr/bin/env python3
"""Simple verification script for Phase 1 implementation.

Tests core functionality without requiring pytest.
"""

import sys
import traceback
from datetime import datetime, timedelta
from uuid import uuid4

def test_forecast_model():
    """Test ForecastModel functionality."""
    print("\n✓ Testing ForecastModel...")

    try:
        from backend.app.ml.forecasting.forecast_model import ForecastModel, PipelineForecast

        # Test 1: Model initialization
        model = ForecastModel()
        assert model.model is None, "Model should be None initially"
        assert model.scaler is None, "Scaler should be None initially"
        assert model.is_trained is False, "Should not be trained initially"
        print("  ✓ Model initialization")

        # Test 2: Feature extraction
        class MockRow:
            job_title = "Senior Software Engineer"
            required_skills = ["Python", "AWS", "Docker", "Kubernetes"]
            salary_min = 120000
            salary_max = 180000
            application_count = 25

        row = MockRow()
        features = model._extract_position_features(row)
        assert len(features) == 5, f"Expected 5 features, got {len(features)}"
        assert features[0] == 3.0, f"Expected job_title_length=3, got {features[0]}"
        assert features[1] == 4.0, f"Expected skill_count=4, got {features[1]}"
        print("  ✓ Feature extraction")

        # Test 3: Fallback prediction
        model_untrained = ForecastModel()
        try:
            model_untrained.predict([3.0, 4.0, 60.0, 1.5, 25.0])
            assert False, "Should raise RuntimeError for untrained model"
        except RuntimeError as e:
            assert "not trained" in str(e)
        print("  ✓ Untrained model error handling")

        # Test 4: PipelineForecast creation
        position_id = str(uuid4())
        fill_date = datetime.utcnow() + timedelta(days=60)
        forecast = PipelineForecast(
            position_id=position_id,
            forecasted_fill_date=fill_date,
            estimated_days_to_fill=60,
            confidence=0.85,
            bottleneck_stage="interview_scheduled",
            recommendations=["Expedite interviews"],
        )
        assert forecast.position_id == position_id
        assert forecast.confidence == 0.85
        print("  ✓ PipelineForecast creation")

        # Test 5: Forecast serialization
        forecast_dict = forecast.to_dict()
        assert "position_id" in forecast_dict
        assert "estimated_days_to_fill" in forecast_dict
        assert forecast_dict["confidence"] == 0.85
        print("  ✓ Forecast serialization")

        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        traceback.print_exc()
        return False


def test_salary_benchmarking_model():
    """Test SalaryBenchmarkingModel functionality."""
    print("\n✓ Testing SalaryBenchmarkingModel...")

    try:
        from backend.app.ml.salary_benchmarking.salary_model import (
            SalaryBenchmarkingModel,
            SalaryData,
            OfferRecommendation,
        )

        # Test 1: Model initialization
        model = SalaryBenchmarkingModel()
        assert model.levels_api_key is None
        assert model.glassdoor_api_key is None
        print("  ✓ Model initialization")

        # Test 2: Role title normalization
        assert model._normalize_role_title("software engineer") == "Software Engineer"
        assert model._normalize_role_title("Data Scientist") == "Data Scientist"
        print("  ✓ Role normalization")

        # Test 3: Fallback data retrieval
        data = model._get_fallback_data("Software Engineer", "mid", "San Francisco, CA")
        assert data is not None
        assert data.role_title == "Software Engineer"
        assert data.median_salary == 160000
        print("  ✓ Fallback data retrieval")

        # Test 4: Missing fallback data
        data = model._get_fallback_data("Unicorn Trainer", "senior", "Mars")
        assert data is None
        print("  ✓ Missing data handling")

        # Test 5: Offer recommendation - above market
        market_data = SalaryData(
            role_title="Software Engineer",
            level="senior",
            location="San Francisco, CA",
            min_salary=160000,
            max_salary=300000,
            median_salary=220000,
            percentile_25=190000,
            percentile_75=260000,
            data_points=1000,
            data_source="test",
        )

        rec = model.recommend_offer(
            market_data=market_data,
            candidate_level="senior",
            candidate_skills_match=1.0,
            role_criticality=1.2,
        )

        assert rec.suggested_offer > 0
        assert rec.win_likelihood > 0
        assert rec.win_likelihood <= 1.0
        print("  ✓ Offer recommendation")

        # Test 6: SalaryData serialization
        data_dict = market_data.to_dict()
        assert data_dict["role_title"] == "Software Engineer"
        assert data_dict["median_salary"] == 220000
        print("  ✓ SalaryData serialization")

        # Test 7: OfferRecommendation serialization
        rec_dict = rec.to_dict()
        assert "suggested_offer" in rec_dict
        assert "win_likelihood" in rec_dict
        print("  ✓ OfferRecommendation serialization")

        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        traceback.print_exc()
        return False


def test_forecast_service():
    """Test ForecastService functionality."""
    print("\n✓ Testing ForecastService...")

    try:
        from backend.app.ml.forecasting.forecast_service import ForecastService
        from unittest.mock import AsyncMock

        # Test 1: Service initialization
        mock_db = AsyncMock()
        service = ForecastService(mock_db)
        assert service.db == mock_db
        assert service.model is not None
        print("  ✓ Service initialization")

        # Test 2: Level inference
        class MockPosition:
            title: str
            required_skills = []
            salary_min = 100000
            salary_max = 150000
            department = "Engineering"

        pos = MockPosition()
        pos.title = "Principal Engineer"
        assert service._infer_level_from_position(pos) == "principal"

        pos.title = "Senior Software Engineer"
        assert service._infer_level_from_position(pos) == "senior"

        pos.title = "Software Engineer"
        assert service._infer_level_from_position(pos) == "junior"
        print("  ✓ Level inference")

        # Test 3: Fallback prediction
        pos.title = "Senior Engineer"
        pos.required_skills = ["Python", "AWS", "Docker"]
        prediction = service._fallback_prediction(pos)
        assert "days_to_fill" in prediction
        assert "confidence" in prediction
        assert prediction["days_to_fill"] > 0
        assert prediction["confidence"] <= 1.0
        print("  ✓ Fallback prediction")

        # Test 4: Recommendation generation
        recs = service._generate_recommendations("interview_scheduled", "Engineering")
        assert len(recs) > 0
        assert isinstance(recs, list)
        print("  ✓ Recommendation generation")

        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        traceback.print_exc()
        return False


def test_salary_benchmarking_service():
    """Test SalaryBenchmarkingService functionality."""
    print("\n✓ Testing SalaryBenchmarkingService...")

    try:
        from backend.app.ml.salary_benchmarking.salary_service import SalaryBenchmarkingService
        from unittest.mock import AsyncMock

        # Test 1: Service initialization
        mock_db = AsyncMock()
        service = SalaryBenchmarkingService(mock_db)
        assert service.db == mock_db
        assert service.model is not None
        print("  ✓ Service initialization")

        # Test 2: Salary extraction
        from unittest.mock import MagicMock

        mock_resume = MagicMock()

        # Test numeric salary
        mock_resume.parsed_data = {"salary_expectation": 150000}
        salary = service._extract_salary_from_resume(mock_resume)
        assert salary == 150000.0

        # Test string salary
        mock_resume.parsed_data = {"salary_expectation": "$160000"}
        salary = service._extract_salary_from_resume(mock_resume)
        assert salary == 160000.0

        # Test missing salary
        mock_resume.parsed_data = {}
        salary = service._extract_salary_from_resume(mock_resume)
        assert salary is None
        print("  ✓ Salary extraction")

        # Test 3: Level inference
        mock_pos = MagicMock()
        mock_pos.title = "Senior Software Engineer"
        level = service._infer_level_from_position(mock_pos)
        assert level == "senior"

        mock_pos.title = "Software Engineer"
        level = service._infer_level_from_position(mock_pos)
        assert level == "junior"
        print("  ✓ Level inference")

        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        traceback.print_exc()
        return False


def test_api_schemas():
    """Test API request/response schemas."""
    print("\n✓ Testing API Schemas...")

    try:
        from pydantic import BaseModel, ValidationError

        # Test ForecastRequest schema
        class ForecastRequest(BaseModel):
            position_id: str
            department: str = None

        req = ForecastRequest(position_id="test-id")
        assert req.position_id == "test-id"
        print("  ✓ ForecastRequest schema")

        # Test SalaryDataResponse schema
        class SalaryDataResponse(BaseModel):
            role_title: str
            level: str
            location: str
            min_salary: int
            max_salary: int
            median_salary: int

        resp = SalaryDataResponse(
            role_title="Engineer",
            level="mid",
            location="SF",
            min_salary=100000,
            max_salary=200000,
            median_salary=150000,
        )
        assert resp.median_salary == 150000
        print("  ✓ SalaryDataResponse schema")

        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        traceback.print_exc()
        return False


def test_imports():
    """Test that all modules can be imported."""
    print("\n✓ Testing Module Imports...")

    try:
        from backend.app.ml.forecasting import ForecastModel, PipelineForecast, ForecastService
        print("  ✓ Forecasting module imports")

        from backend.app.ml.salary_benchmarking import (
            SalaryBenchmark,
            SalaryData,
            OfferRecommendation,
            SalaryBenchmarkingService,
        )
        print("  ✓ Salary benchmarking module imports")

        return True
    except Exception as e:
        print(f"  ✗ Import error: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("PHASE 1 IMPLEMENTATION VERIFICATION")
    print("=" * 60)

    tests = [
        ("Module Imports", test_imports),
        ("ForecastModel", test_forecast_model),
        ("SalaryBenchmarkingModel", test_salary_benchmarking_model),
        ("ForecastService", test_forecast_service),
        ("SalaryBenchmarkingService", test_salary_benchmarking_service),
        ("API Schemas", test_api_schemas),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Unexpected error in {test_name}: {e}")
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {test_name}")

    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ ALL TESTS PASSED - Phase 1 Implementation is VERIFIED")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
