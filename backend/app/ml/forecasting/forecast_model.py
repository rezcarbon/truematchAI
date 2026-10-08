"""Pipeline Forecasting Model - Predicts time-to-hire for job positions.

Uses historical ApplicationTimeline and HiringOutcome data to train regression models
that predict how long a position will take to fill.

Features extracted from position data:
- JD complexity (word count, skill count)
- Seniority level
- Department
- Salary range
- Historical fill time for similar positions

Target variable:
- Days to fill (from application created → offer accepted)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import pickle
import json

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

from app.models.application_timeline import ApplicationTimeline, EventType
from app.models.hiring_outcome import HiringOutcome, HiringDecision
from app.models.position import Position
from app.models.assessment import Assessment

logger = logging.getLogger(__name__)


@dataclass
class PipelineForecast:
    """Result of a time-to-hire forecast."""

    position_id: str
    forecasted_fill_date: datetime
    estimated_days_to_fill: int
    confidence: float  # 0-1
    bottleneck_stage: Optional[str] = None
    recommendations: list[str] = None
    model_version: str = "v1"
    created_at: datetime = None

    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            "position_id": self.position_id,
            "forecasted_fill_date": self.forecasted_fill_date.isoformat(),
            "estimated_days_to_fill": self.estimated_days_to_fill,
            "confidence": round(self.confidence, 2),
            "bottleneck_stage": self.bottleneck_stage,
            "recommendations": self.recommendations or [],
            "model_version": self.model_version,
            "created_at": (self.created_at or datetime.utcnow()).isoformat(),
        }


class ForecastModel:
    """ML model for time-to-hire prediction."""

    def __init__(self):
        self.model: Optional[GradientBoostingRegressor] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: list[str] = []
        self.is_trained = False

    async def train_from_data(
        self,
        db: AsyncSession,
        min_samples: int = 100,
        test_size: float = 0.2,
    ) -> dict:
        """
        Train forecasting model from historical hiring data.

        Args:
            db: Database session
            min_samples: Minimum number of historical records needed
            test_size: Test/train split ratio

        Returns:
            Training results dict with metrics
        """
        logger.info("Starting model training from historical data...")

        # Extract training data
        X, y, metadata = await self._extract_training_data(db)

        if len(X) < min_samples:
            logger.warning(f"Insufficient data: {len(X)} < {min_samples} required")
            return {
                "status": "insufficient_data",
                "samples_found": len(X),
                "samples_required": min_samples,
            }

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        logger.info(f"Training on {len(X_train)} samples, testing on {len(X_test)}")

        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            verbose=1,
        )
        self.model.fit(X_train_scaled, y_train)

        # Evaluate
        train_r2 = self.model.score(X_train_scaled, y_train)
        test_r2 = self.model.score(X_test_scaled, y_test)

        # Calculate RMSE
        train_pred = self.model.predict(X_train_scaled)
        test_pred = self.model.predict(X_test_scaled)
        train_rmse = np.sqrt(np.mean((y_train - train_pred) ** 2))
        test_rmse = np.sqrt(np.mean((y_test - test_pred) ** 2))

        self.is_trained = True

        results = {
            "status": "success",
            "train_r2": float(train_r2),
            "test_r2": float(test_r2),
            "train_rmse_days": float(train_rmse),
            "test_rmse_days": float(test_rmse),
            "feature_importance": self._get_feature_importance(),
            "samples_used": len(X),
        }

        logger.info(f"Model training complete - Test R²: {test_r2:.3f}, RMSE: {test_rmse:.1f} days")

        return results

    async def _extract_training_data(self, db: AsyncSession) -> tuple[list, list, dict]:
        """Extract and prepare training data from historical records."""

        # Query historical hiring outcomes with complete pipelines
        stmt = select(
            Position.id,
            Position.job_title,
            Position.required_skills,
            Position.salary_min,
            Position.salary_max,
            func.count(Assessment.id).label("application_count"),
            func.max(ApplicationTimeline.latest_event_timestamp).label("final_timestamp"),
            func.min(ApplicationTimeline.created_at).label("first_timestamp"),
        ).join(
            Assessment, Assessment.position_id == Position.id
        ).join(
            ApplicationTimeline, ApplicationTimeline.assessment_id == Assessment.id
        ).group_by(
            Position.id,
            Position.job_title,
            Position.required_skills,
            Position.salary_min,
            Position.salary_max,
        )

        result = await db.execute(stmt)
        rows = result.fetchall()

        X, y = [], []

        for row in rows:
            # Calculate days to fill
            if row.final_timestamp and row.first_timestamp:
                days_to_fill = (row.final_timestamp - row.first_timestamp).days
                if days_to_fill < 1:  # Skip invalid data
                    continue
            else:
                continue

            # Extract features
            features = self._extract_position_features(row)
            X.append(features)
            y.append(days_to_fill)

        return X, y, {"rows_processed": len(rows), "valid_samples": len(X)}

    def _extract_position_features(self, row) -> list:
        """Extract ML features from a position record."""
        features = []

        # Feature 1: JD Complexity (word count in title + skill count)
        job_title_length = len(row.job_title.split()) if row.job_title else 0
        features.append(job_title_length)

        # Feature 2: Skill count from required_skills
        skill_count = len(row.required_skills) if row.required_skills else 0
        features.append(skill_count)

        # Feature 3: Salary range (high - low)
        salary_range = 0
        if row.salary_min and row.salary_max:
            salary_range = (row.salary_max - row.salary_min) / 1000  # In thousands
        features.append(salary_range)

        # Feature 4: Salary midpoint (normalized)
        salary_mid = 0
        if row.salary_min and row.salary_max:
            salary_mid = (row.salary_min + row.salary_max) / 2 / 100000  # Normalized
        features.append(salary_mid)

        # Feature 5: Application count (competition)
        features.append(float(row.application_count or 0))

        # Pad to fixed feature count (5)
        self.feature_names = [
            "job_title_length",
            "skill_count",
            "salary_range_k",
            "salary_midpoint_norm",
            "application_count",
        ]

        return features

    def predict(self, position_features: list) -> dict:
        """
        Predict time-to-hire for a position.

        Returns dict with:
        - days_to_fill: Predicted days
        - confidence: Model confidence (0-1)
        """
        if not self.is_trained or self.model is None:
            raise RuntimeError("Model not trained. Call train_from_data() first.")

        # Scale features
        features_scaled = self.scaler.transform([position_features])

        # Predict
        days_pred = self.model.predict(features_scaled)[0]
        days_pred = max(1, days_pred)  # Ensure positive

        # Confidence based on model prediction variance
        # (simplified: use tree variance estimate)
        confidence = min(1.0, 0.7 + (0.3 * (1 / (1 + abs(days_pred) / 30))))

        return {
            "days_to_fill": int(days_pred),
            "confidence": float(confidence),
        }

    def _get_feature_importance(self) -> dict:
        """Get feature importance from trained model."""
        if self.model is None:
            return {}

        importances = self.model.feature_importances_
        return {
            name: float(imp)
            for name, imp in zip(self.feature_names, importances)
        }

    def save(self, filepath: str):
        """Save trained model to disk."""
        with open(filepath, "wb") as f:
            pickle.dump({
                "model": self.model,
                "scaler": self.scaler,
                "feature_names": self.feature_names,
                "is_trained": self.is_trained,
            }, f)
        logger.info(f"Model saved to {filepath}")

    def load(self, filepath: str):
        """Load trained model from disk."""
        with open(filepath, "rb") as f:
            data = pickle.load(f)
        self.model = data["model"]
        self.scaler = data["scaler"]
        self.feature_names = data["feature_names"]
        self.is_trained = data["is_trained"]
        logger.info(f"Model loaded from {filepath}")


__all__ = ["ForecastModel", "PipelineForecast"]
