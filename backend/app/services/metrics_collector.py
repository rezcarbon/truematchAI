"""Compute daily learning metrics from assessments and outcomes.

Calculates precision, recall, F1-score, and confidence calibration
by comparing predicted outcomes (capability_score >= threshold) against
actual hiring decisions (HiringOutcome.hiring_decision).
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utcnow
from app.models.assessment import Assessment, AssessmentStatus, DecisionType
from app.models.hiring_outcome import HiringOutcome, HiringDecision
from app.models.learning_metrics import AssessmentMetrics
from app.models.position import Position

logger = logging.getLogger("truematch.metrics_collector")

HIRE_THRESHOLD = 60  # capability_score >= this means "hire prediction"


class MetricsCollector:
    """Calculates daily precision, recall, F1 from assessment predictions vs actual outcomes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_daily_metrics(
        self, metric_date: date, model_version: str = "v1"
    ) -> AssessmentMetrics:
        """
        Compute metrics for all assessments completed on metric_date.

        Comparison logic:
        - Predicted "hire" if capability_score >= HIRE_THRESHOLD (60)
        - Actual "hire" if HiringOutcome.hiring_decision == hired

        Args:
            metric_date: Date to calculate metrics for
            model_version: Model version tag (v1, v2, etc.)

        Returns:
            AssessmentMetrics object with computed values

        Raises:
            Exception: Database errors are logged but not raised
                      (metrics must never block operations)
        """
        try:
            logger.info(f"Computing metrics for {metric_date} (model {model_version})")

            # Get all assessments completed on metric_date
            stmt = select(Assessment).where(
                and_(
                    func.date(Assessment.updated_at) == metric_date,
                    Assessment.status == AssessmentStatus.completed,
                    Assessment.capability_score.isnot(None),
                )
            )
            result = await self.db.execute(stmt)
            assessments = result.scalars().all()

            tp, tn, fp, fn = 0, 0, 0, 0
            confidences: list[float] = []

            # For each assessment, check if outcome was recorded
            for assessment in assessments:
                # Get hiring outcome for this assessment
                outcome_stmt = select(HiringOutcome).where(
                    and_(
                        HiringOutcome.position_id == assessment.position_id,
                        # Rough match: candidate was in this assessment
                        # (In production, assessment should have direct foreign key to HiringOutcome)
                    )
                ).order_by(HiringOutcome.created_at.desc()).limit(1)

                outcome_result = await self.db.execute(outcome_stmt)
                outcome = outcome_result.scalar_one_or_none()

                if outcome:
                    # Prediction: score >= HIRE_THRESHOLD means "hire recommendation"
                    predicted_hire = (assessment.capability_score or 0) >= HIRE_THRESHOLD
                    # Actual: hired if decision is hired or offer_declined is also positive
                    actual_hire = outcome.hiring_decision in (
                        HiringDecision.hired,
                        HiringDecision.offer_declined,  # they got the job
                    )

                    # Update confusion matrix
                    if predicted_hire and actual_hire:
                        tp += 1
                    elif not predicted_hire and not actual_hire:
                        tn += 1
                    elif predicted_hire and not actual_hire:
                        fp += 1
                    else:  # not predicted_hire and actual_hire
                        fn += 1

                    # Extract confidence from decision_type
                    confidence = self._decision_type_to_confidence(
                        assessment.decision_type or DecisionType.escalate
                    )
                    confidences.append(confidence)

            # Compute metrics
            total = tp + tn + fp + fn
            accuracy = (tp + tn) / total if total > 0 else 0.0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

            # F1 score
            if precision + recall > 0:
                f1 = 2 * precision * recall / (precision + recall)
            else:
                f1 = 0.0

            # Error rates
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

            # Confidence calibration: Expected Calibration Error
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
            ece = abs(avg_confidence - accuracy)

            # Create metrics record
            metrics = AssessmentMetrics(
                metric_date=metric_date,
                model_version=model_version,
                total_assessments=len(assessments),
                assessments_with_outcome=total,
                true_positives=tp,
                true_negatives=tn,
                false_positives=fp,
                false_negatives=fn,
                accuracy=round(accuracy, 4),
                precision=round(precision, 4),
                recall=round(recall, 4),
                f1_score=round(f1, 4),
                false_positive_rate=round(fpr, 4),
                false_negative_rate=round(fnr, 4),
                avg_confidence=round(avg_confidence, 4),
                expected_calibration_error=round(ece, 4),
                metrics_by_role={},  # Populated below
                thresholds_tested={},  # Populated below
                created_at=utcnow(),
                updated_at=utcnow(),
            )

            # Compute per-role metrics
            metrics.metrics_by_role = await self._compute_role_metrics(
                assessments, metric_date
            )

            self.db.add(metrics)
            await self.db.flush()

            logger.info(
                f"Metrics for {metric_date}: Accuracy={accuracy:.1%}, "
                f"Precision={precision:.1%}, Recall={recall:.1%}, "
                f"F1={f1:.1%}, ECE={ece:.4f}, Total={len(assessments)}"
            )

            return metrics

        except Exception as exc:
            logger.error(f"Failed to compute metrics for {metric_date}: {exc}", exc_info=True)
            # Don't raise — metrics must not block operations
            # Return empty metrics record
            return AssessmentMetrics(
                metric_date=metric_date,
                model_version=model_version,
                total_assessments=0,
                assessments_with_outcome=0,
                true_positives=0,
                true_negatives=0,
                false_positives=0,
                false_negatives=0,
                accuracy=None,
                precision=None,
                recall=None,
                f1_score=None,
                false_positive_rate=None,
                false_negative_rate=None,
                avg_confidence=None,
                expected_calibration_error=None,
                created_at=utcnow(),
                updated_at=utcnow(),
            )

    async def _compute_role_metrics(
        self, assessments: list[Assessment], metric_date: date
    ) -> dict:
        """Compute metrics per role."""
        by_role: dict[str, dict] = {}

        for assessment in assessments:
            # Get position to extract role
            position = await self.db.get(Position, assessment.position_id)
            if not position:
                continue

            role = position.title or "unknown"
            if role not in by_role:
                by_role[role] = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}

            # Get outcome
            outcome_stmt = select(HiringOutcome).where(
                HiringOutcome.position_id == assessment.position_id
            ).order_by(HiringOutcome.created_at.desc()).limit(1)

            outcome_result = await self.db.execute(outcome_stmt)
            outcome = outcome_result.scalar_one_or_none()

            if outcome:
                predicted_hire = (assessment.capability_score or 0) >= HIRE_THRESHOLD
                actual_hire = outcome.hiring_decision in (
                    HiringDecision.hired,
                    HiringDecision.offer_declined,
                )

                if predicted_hire and actual_hire:
                    by_role[role]["tp"] += 1
                elif not predicted_hire and not actual_hire:
                    by_role[role]["tn"] += 1
                elif predicted_hire and not actual_hire:
                    by_role[role]["fp"] += 1
                else:
                    by_role[role]["fn"] += 1

        # Compute metrics per role
        role_metrics = {}
        for role, cm in by_role.items():
            tp, tn, fp, fn = cm["tp"], cm["tn"], cm["fp"], cm["fn"]
            total = tp + tn + fp + fn

            if total > 0:
                accuracy = (tp + tn) / total
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                f1 = (
                    2 * precision * recall / (precision + recall)
                    if (precision + recall) > 0
                    else 0.0
                )

                role_metrics[role] = {
                    "accuracy": round(accuracy, 4),
                    "precision": round(precision, 4),
                    "recall": round(recall, 4),
                    "f1": round(f1, 4),
                    "sample_size": total,
                    "tp": tp,
                    "tn": tn,
                    "fp": fp,
                    "fn": fn,
                }

        return role_metrics

    def _decision_type_to_confidence(self, decision_type: DecisionType) -> float:
        """Map decision_type to confidence score (0.0-1.0)."""
        mapping = {
            DecisionType.approval: 0.9,  # Very confident
            DecisionType.advisory: 0.7,  # Moderately confident
            DecisionType.escalate: 0.4,  # Uncertain
        }
        return mapping.get(decision_type, 0.5)


__all__ = ["MetricsCollector", "HIRE_THRESHOLD"]
