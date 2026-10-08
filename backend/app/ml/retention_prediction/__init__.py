"""Retention Prediction and Churn Prevention.

Provides:
- Post-hire outcome tracking
- Retention risk prediction
- Attrition early warning signals
- Manager coaching recommendations
- Team composition analysis
"""

from .retention_model import RetentionPrediction, AttritionRisk, RetentionIntervention
from .retention_service import RetentionPredictionService

__all__ = [
    "RetentionPrediction",
    "AttritionRisk",
    "RetentionIntervention",
    "RetentionPredictionService",
]
