"""Retention Prediction Model - Post-hire outcome tracking and churn prevention.

Provides:
- Retention risk scoring
- Attrition early warning signals
- Manager coaching recommendations
- Team composition analysis
- Success factor analysis
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class RetentionRiskLevel(str, Enum):
    """Retention risk classification."""

    low = "low"  # <20% attrition risk
    medium = "medium"  # 20-50% attrition risk
    high = "high"  # 50-80% attrition risk
    critical = "critical"  # >80% attrition risk


class AttritionSignal(str, Enum):
    """Early warning signals for attrition."""

    performance_decline = "performance_decline"
    engagement_drop = "engagement_drop"
    communication_change = "communication_change"
    promotion_seeking = "promotion_seeking"
    role_mismatch = "role_mismatch"
    team_conflict = "team_conflict"
    compensation_concern = "compensation_concern"


@dataclass
class AttritionRisk:
    """Attrition risk assessment for new hire."""

    hire_id: str
    candidate_id: str
    hire_date: datetime

    # Risk scoring
    risk_score: float  # 0-1 (0=low, 1=high)
    risk_level: RetentionRiskLevel

    # Signals
    detected_signals: List[AttritionSignal]
    signal_strength: Dict[str, float]  # signal -> strength (0-1)

    # Timeline predictions
    days_to_potential_attrition: Optional[int] = None  # Days until predicted departure
    confidence: float = 0.7  # Prediction confidence (0-1)

    # Key factors
    primary_risk_factor: Optional[str] = None
    secondary_factors: List[str] = field(default_factory=list)

    # Assessment date
    assessed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self):
        """Serialize to dictionary."""
        return {
            "hire_id": self.hire_id,
            "candidate_id": self.candidate_id,
            "risk_score": round(self.risk_score, 2),
            "risk_level": self.risk_level.value,
            "detected_signals": [s.value for s in self.detected_signals],
            "signal_strength": {k: round(v, 2) for k, v in self.signal_strength.items()},
            "days_to_potential_attrition": self.days_to_potential_attrition,
            "confidence": round(self.confidence, 2),
            "primary_risk_factor": self.primary_risk_factor,
            "secondary_factors": self.secondary_factors,
            "assessed_at": self.assessed_at.isoformat(),
        }


@dataclass
class RetentionIntervention:
    """Recommended intervention to prevent attrition."""

    intervention_type: str  # manager_check_in, role_adjustment, mentoring, etc.
    priority: str  # high, medium, low
    target_audience: str  # manager, hr, candidate

    # Specific recommendations
    description: str
    action_steps: List[str]
    expected_impact: str  # e.g., "Reduce risk by 30%"

    # Timeline
    suggested_timeframe: str  # e.g., "within 7 days"

    # Success metrics
    success_indicators: List[str]
    follow_up_date: Optional[datetime] = None


@dataclass
class RetentionPrediction:
    """Complete retention prediction for new hire."""

    hire_id: str
    candidate_id: str
    position_id: str
    hire_date: datetime

    # Risk assessment
    attrition_risk: AttritionRisk

    # Interventions
    recommended_interventions: List[RetentionIntervention]

    # Success factors
    strengths: List[str]  # Why this hire is likely to succeed
    challenges: List[str]  # Challenges to monitor

    # Team context
    team_composition_impact: Dict  # How hire impacts team dynamics

    # Timeline
    assessment_period: str  # e.g., "first_90_days"
    next_check_date: Optional[datetime] = None

    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self):
        """Serialize to dictionary."""
        return {
            "hire_id": self.hire_id,
            "candidate_id": self.candidate_id,
            "position_id": self.position_id,
            "attrition_risk": self.attrition_risk.to_dict(),
            "recommended_interventions": [
                {
                    "intervention_type": i.intervention_type,
                    "priority": i.priority,
                    "description": i.description,
                    "action_steps": i.action_steps,
                    "expected_impact": i.expected_impact,
                }
                for i in self.recommended_interventions
            ],
            "strengths": self.strengths,
            "challenges": self.challenges,
            "assessment_period": self.assessment_period,
            "created_at": self.created_at.isoformat(),
        }


class RetentionPredictionModel:
    """ML model for retention prediction and churn prevention."""

    def __init__(self):
        # Feature thresholds (tunable)
        self.performance_decline_threshold = 0.3  # 30% decline triggers signal
        self.engagement_drop_threshold = 0.25
        self.signal_weights = {
            "performance_decline": 0.30,
            "engagement_drop": 0.25,
            "role_mismatch": 0.20,
            "compensation_concern": 0.15,
            "team_conflict": 0.10,
        }

    def predict_retention_risk(
        self,
        hire_id: str,
        candidate_id: str,
        hire_date: datetime,
        assessment_data: Dict,
    ) -> AttritionRisk:
        """
        Predict attrition risk for new hire.

        Args:
            hire_id: Hire ID
            candidate_id: Candidate ID
            hire_date: Hire date
            assessment_data: Assessment data (performance, engagement, etc.)

        Returns:
            AttritionRisk prediction
        """
        # Detect signals
        signals = self._detect_attrition_signals(assessment_data)
        signal_strength = {s.value: self._calculate_signal_strength(s, assessment_data) for s in signals}

        # Calculate overall risk score
        risk_score = self._calculate_risk_score(signals, signal_strength)

        # Map to risk level
        risk_level = self._score_to_level(risk_score)

        # Estimate days to attrition
        days_to_attrition = self._estimate_attrition_timeline(signals, risk_score) if signals else None

        # Identify primary risk factor
        primary_factor = max(signal_strength.items(), key=lambda x: x[1])[0] if signal_strength else None

        return AttritionRisk(
            hire_id=hire_id,
            candidate_id=candidate_id,
            hire_date=hire_date,
            risk_score=risk_score,
            risk_level=risk_level,
            detected_signals=signals,
            signal_strength=signal_strength,
            days_to_potential_attrition=days_to_attrition,
            confidence=0.75,  # Default confidence
            primary_risk_factor=primary_factor,
            secondary_factors=[s for s in signal_strength.keys() if s != primary_factor][:2],
        )

    def _detect_attrition_signals(self, assessment_data: Dict) -> List[AttritionSignal]:
        """Detect early warning signals for attrition."""
        signals = []

        # Check for performance decline
        if assessment_data.get("performance_rating") and assessment_data.get("previous_performance_rating"):
            decline = assessment_data["previous_performance_rating"] - assessment_data["performance_rating"]
            if decline > self.performance_decline_threshold:
                signals.append(AttritionSignal.performance_decline)

        # Check for engagement drop
        if assessment_data.get("engagement_score", 100) < 70:
            signals.append(AttritionSignal.engagement_drop)

        # Check for role mismatch
        if assessment_data.get("role_satisfaction_score", 100) < 60:
            signals.append(AttritionSignal.role_mismatch)

        # Check for compensation concern
        if assessment_data.get("compensation_satisfaction", 100) < 50:
            signals.append(AttritionSignal.compensation_concern)

        # Check for team conflict
        if assessment_data.get("team_dynamics_score", 100) < 55:
            signals.append(AttritionSignal.team_conflict)

        return signals

    def _calculate_signal_strength(self, signal: AttritionSignal, assessment_data: Dict) -> float:
        """Calculate strength of a signal (0-1)."""
        if signal == AttritionSignal.performance_decline:
            rating = assessment_data.get("performance_rating", 3)
            return min(1.0, max(0.0, 1.0 - (rating / 5)))

        elif signal == AttritionSignal.engagement_drop:
            engagement = assessment_data.get("engagement_score", 100)
            return 1.0 - (engagement / 100)

        elif signal == AttritionSignal.role_mismatch:
            satisfaction = assessment_data.get("role_satisfaction_score", 100)
            return 1.0 - (satisfaction / 100)

        elif signal == AttritionSignal.compensation_concern:
            satisfaction = assessment_data.get("compensation_satisfaction", 100)
            return 1.0 - (satisfaction / 100)

        elif signal == AttritionSignal.team_conflict:
            dynamics = assessment_data.get("team_dynamics_score", 100)
            return 1.0 - (dynamics / 100)

        return 0.0

    def _calculate_risk_score(self, signals: List[AttritionSignal], strengths: Dict) -> float:
        """Calculate overall attrition risk score (0-1)."""
        if not signals:
            return 0.0

        weighted_score = 0.0
        for signal in signals:
            weight = self.signal_weights.get(signal.value, 0.1)
            strength = strengths.get(signal.value, 0.5)
            weighted_score += weight * strength

        return min(1.0, weighted_score)

    def _score_to_level(self, score: float) -> RetentionRiskLevel:
        """Map risk score to risk level."""
        if score < 0.2:
            return RetentionRiskLevel.low
        elif score < 0.5:
            return RetentionRiskLevel.medium
        elif score < 0.8:
            return RetentionRiskLevel.high
        else:
            return RetentionRiskLevel.critical

    def _estimate_attrition_timeline(self, signals: List[AttritionSignal], risk_score: float) -> Optional[int]:
        """Estimate days until potential attrition."""
        if not signals:
            return None

        # Base timeline: higher risk = sooner departure
        base_days = 90  # Default 90-day window
        adjusted_days = max(14, int(base_days * (1 - risk_score)))  # Minimum 2 weeks

        return adjusted_days

    def generate_interventions(self, attrition_risk: AttritionRisk) -> List[RetentionIntervention]:
        """Generate manager coaching recommendations."""
        interventions = []

        for signal in attrition_risk.detected_signals:
            if signal == AttritionSignal.performance_decline:
                interventions.append(
                    RetentionIntervention(
                        intervention_type="performance_coaching",
                        priority="high",
                        target_audience="manager",
                        description="Candidate showing performance decline. Schedule check-in to understand challenges.",
                        action_steps=[
                            "Schedule 1:1 with candidate within 3 days",
                            "Discuss any blockers or challenges",
                            "Identify support needed (training, resources, mentoring)",
                        ],
                        expected_impact="Restore confidence and improve performance by 20-30%",
                        suggested_timeframe="within 7 days",
                        success_indicators=[
                            "Candidate reports feeling supported",
                            "Performance metrics improve",
                            "Regular check-ins scheduled",
                        ],
                    )
                )

            elif signal == AttritionSignal.role_mismatch:
                interventions.append(
                    RetentionIntervention(
                        intervention_type="role_discussion",
                        priority="high",
                        target_audience="manager",
                        description="Candidate may not be aligned with role expectations.",
                        action_steps=[
                            "Clarify role expectations",
                            "Discuss career path within company",
                            "Explore internal transfer opportunities if relevant",
                        ],
                        expected_impact="Increase role clarity and engagement by 25%",
                        suggested_timeframe="within 14 days",
                        success_indicators=[
                            "Candidate understands growth path",
                            "Role satisfaction improves",
                            "Engagement increases",
                        ],
                    )
                )

            elif signal == AttritionSignal.compensation_concern:
                interventions.append(
                    RetentionIntervention(
                        intervention_type="compensation_review",
                        priority="medium",
                        target_audience="hr",
                        description="Candidate has compensation concerns.",
                        action_steps=[
                            "Review market rates for role",
                            "Evaluate merit increase or bonus opportunity",
                            "Discuss benefits and total compensation",
                        ],
                        expected_impact="Increase compensation satisfaction by 30%",
                        suggested_timeframe="within 30 days",
                        success_indicators=[
                            "Compensation satisfaction increases",
                            "Candidate feels valued",
                            "Attrition risk decreases",
                        ],
                    )
                )

        return interventions if interventions else [
            RetentionIntervention(
                intervention_type="regular_check_in",
                priority="low",
                target_audience="manager",
                description="Maintain regular check-ins for new hire onboarding.",
                action_steps=[
                    "Weekly 1:1 meetings for first month",
                    "Bi-weekly for months 2-3",
                    "Monthly after first 90 days",
                ],
                expected_impact="Maintain engagement and support transition",
                suggested_timeframe="ongoing",
                success_indicators=[
                    "Hire feels supported",
                    "Performance meets expectations",
                    "Team integration smooth",
                ],
            )
        ]


__all__ = ["RetentionPredictionModel", "RetentionPrediction", "AttritionRisk"]
