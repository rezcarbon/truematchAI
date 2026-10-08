"""Tests for pipeline forecasting module."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.forecasting.forecast_model import ForecastModel, PipelineForecast
from app.ml.forecasting.forecast_service import ForecastService


class TestForecastModel:
    """Test ForecastModel training and prediction."""

    def test_forecast_model_initialization(self):
        """Test model initialization."""
        model = ForecastModel()
        assert model.model is None
        assert model.scaler is None
        assert model.is_trained is False
        assert isinstance(model.feature_names, list)

    def test_feature_extraction(self):
        """Test feature extraction from position data."""
        model = ForecastModel()

        # Mock row object
        class MockRow:
            job_title = "Senior Software Engineer"
            required_skills = ["Python", "AWS", "Docker", "Kubernetes"]
            salary_min = 120000
            salary_max = 180000
            application_count = 25

        row = MockRow()
        features = model._extract_position_features(row)

        assert len(features) == 5
        assert features[0] == 3.0  # job_title_length (3 words)
        assert features[1] == 4.0  # skill_count
        assert features[2] == 60.0  # salary_range_k (180-120 = 60k)
        assert features[3] == 1.5   # salary_midpoint_norm (150k/100k)
        assert features[4] == 25.0  # application_count

    def test_forecast_prediction(self):
        """Test prediction on untrained model raises error."""
        model = ForecastModel()

        with pytest.raises(RuntimeError, match="Model not trained"):
            model.predict([3.0, 4.0, 60.0, 1.5, 25.0])

    def test_forecast_model_serialization(self, tmp_path):
        """Test model save/load."""
        model = ForecastModel()
        model.is_trained = True
        model.feature_names = ["feature1", "feature2"]

        # Save
        save_path = tmp_path / "model.pkl"
        model.save(str(save_path))
        assert save_path.exists()

        # Load
        new_model = ForecastModel()
        new_model.load(str(save_path))
        assert new_model.is_trained is True
        assert new_model.feature_names == ["feature1", "feature2"]

    def test_feature_importance_extraction(self):
        """Test feature importance calculation."""
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.preprocessing import StandardScaler

        model = ForecastModel()
        model.model = GradientBoostingRegressor(n_estimators=10)
        model.scaler = StandardScaler()
        model.feature_names = ["f1", "f2", "f3", "f4", "f5"]

        # Dummy training
        X = [[1, 2, 3, 4, 5], [2, 3, 4, 5, 6]]
        y = [30, 60]
        X_scaled = model.scaler.fit_transform(X)
        model.model.fit(X_scaled, y)

        importance = model._get_feature_importance()
        assert len(importance) == 5
        assert all(0 <= v <= 1 for v in importance.values())


class TestPipelineForecast:
    """Test PipelineForecast dataclass."""

    def test_forecast_creation(self):
        """Test creating a forecast."""
        position_id = str(uuid4())
        fill_date = datetime.utcnow() + timedelta(days=60)

        forecast = PipelineForecast(
            position_id=position_id,
            forecasted_fill_date=fill_date,
            estimated_days_to_fill=60,
            confidence=0.85,
            bottleneck_stage="interview_scheduled",
            recommendations=["Expedite interviews", "Parallel tracks"],
        )

        assert forecast.position_id == position_id
        assert forecast.estimated_days_to_fill == 60
        assert forecast.confidence == 0.85
        assert forecast.bottleneck_stage == "interview_scheduled"
        assert len(forecast.recommendations) == 2

    def test_forecast_to_dict(self):
        """Test forecast serialization to dict."""
        position_id = str(uuid4())
        fill_date = datetime.utcnow() + timedelta(days=60)

        forecast = PipelineForecast(
            position_id=position_id,
            forecasted_fill_date=fill_date,
            estimated_days_to_fill=60,
            confidence=0.849,
            bottleneck_stage="interview_scheduled",
            recommendations=["Expedite interviews"],
        )

        result = forecast.to_dict()

        assert result["position_id"] == position_id
        assert result["estimated_days_to_fill"] == 60
        assert result["confidence"] == 0.85  # Rounded to 2 decimals
        assert result["bottleneck_stage"] == "interview_scheduled"
        assert isinstance(result["created_at"], str)


class TestForecastService:
    """Test ForecastService."""

    def test_service_initialization(self):
        """Test service initialization."""
        from unittest.mock import AsyncMock

        mock_db = AsyncMock()
        service = ForecastService(mock_db)

        assert service.db == mock_db
        assert isinstance(service.model, ForecastModel)

    def test_fallback_prediction(self):
        """Test fallback prediction when model unavailable."""
        from unittest.mock import AsyncMock

        class MockPosition:
            title = "Senior Engineer"
            required_skills = ["Python", "AWS", "Docker", "Kubernetes", "GCP"]
            salary_min = 120000
            salary_max = 180000
            department = "Engineering"

        mock_db = AsyncMock()
        service = ForecastService(mock_db)

        position = MockPosition()
        prediction = service._fallback_prediction(position)

        assert "days_to_fill" in prediction
        assert "confidence" in prediction
        assert prediction["days_to_fill"] <= 120
        assert 0 <= prediction["confidence"] <= 1
        # Heuristic: base 30 days + 5 per skill (5 skills = 25)
        assert prediction["days_to_fill"] == 55

    def test_level_inference(self):
        """Test seniority level inference from title."""
        from unittest.mock import AsyncMock

        mock_db = AsyncMock()
        service = ForecastService(mock_db)

        class MockPosition:
            title: str
            required_skills = []
            salary_min = 100000
            salary_max = 150000
            department = "Engineering"

        # Test principal
        pos = MockPosition()
        pos.title = "Principal Engineer"
        assert service._infer_level_from_position(pos) == "principal"

        # Test senior
        pos.title = "Senior Software Engineer"
        assert service._infer_level_from_position(pos) == "senior"

        # Test mid
        pos.title = "Mid-Level Engineer"
        assert service._infer_level_from_position(pos) == "mid"

        # Test junior (default)
        pos.title = "Software Engineer"
        assert service._infer_level_from_position(pos) == "junior"

    def test_recommendation_generation(self):
        """Test recommendation generation based on bottleneck."""
        from unittest.mock import AsyncMock

        mock_db = AsyncMock()
        service = ForecastService(mock_db)

        # Test interview bottleneck
        from app.models.application_timeline import EventType
        recs = service._generate_recommendations(
            EventType.interview_scheduled, "Engineering"
        )
        assert len(recs) > 0
        assert any("interview" in rec.lower() for rec in recs)

        # Test offer bottleneck
        recs = service._generate_recommendations(
            EventType.offer_extended, "Engineering"
        )
        assert len(recs) > 0
        assert any("offer" in rec.lower() for rec in recs)

        # Test default recommendations
        recs = service._generate_recommendations(None, "Engineering")
        assert len(recs) > 0


# Integration tests (require database)
@pytest.mark.asyncio
class TestForecastingIntegration:
    """Integration tests with database."""

    async def test_forecast_service_with_mock_db(self):
        """Test forecast service with mock database."""
        from unittest.mock import AsyncMock, MagicMock

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)

        # Create service
        service = ForecastService(mock_db)

        # Verify service is initialized
        assert service.model is not None
        assert service.db == mock_db


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
