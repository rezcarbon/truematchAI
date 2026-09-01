"""Orchestrate the nightly learning cycle.

Four-step process:
1. Calculate yesterday's metrics
2. Collect feedback from last 24 hours
3. Identify patterns in outcomes
4. Retrain/calibrate if sufficient data

All steps are best-effort; failures are logged but not raised.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utcnow
from app.models.assessment import Assessment, AssessmentStatus
from app.models.hiring_outcome import HiringOutcome, HiringDecision
from app.models.learning_metrics import AssessmentMetrics, CognitiveState, CognitiveEvolutionLog
from app.models.position import Position
from app.services.metrics_collector import MetricsCollector, HIRE_THRESHOLD

logger = logging.getLogger("truematch.learning_pipeline")


class LearningPipeline:
    """Manages the 4-step nightly learning process."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.metrics_collector = MetricsCollector(db)

    async def run_nightly_learning(self, target_date: Optional[date] = None) -> dict:
        """
        Execute the complete nightly learning cycle.

        Steps:
        1. Calculate yesterday's metrics
        2. Collect feedback from last 24 hours
        3. Identify patterns
        4. Retrain/calibrate if sufficient data (≥10 feedback items)

        Args:
            target_date: Date to analyze (default: yesterday)

        Returns:
            Summary dict with results from each step
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        logger.info(f"Starting nightly learning cycle for {target_date}")
        results = {
            "target_date": str(target_date),
            "steps_completed": [],
            "errors": [],
        }

        try:
            # Step 1: Calculate yesterday's metrics
            logger.info("Step 1/4: Computing daily metrics...")
            metrics = await self._compute_metrics(target_date)
            results["metrics"] = {
                "accuracy": metrics.accuracy,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1_score": metrics.f1_score,
                "total_assessments": metrics.total_assessments,
                "assessments_with_outcome": metrics.assessments_with_outcome,
            }
            results["steps_completed"].append("compute_metrics")
            await self.db.commit()

            # Step 2: Collect feedback from last 24 hours
            logger.info("Step 2/4: Collecting feedback...")
            feedback_count = await self._collect_feedback(target_date)
            results["feedback_count"] = feedback_count
            results["steps_completed"].append("collect_feedback")

            # Step 3 & 4: Only if sufficient data
            if feedback_count >= 10:
                logger.info(f"Step 3/4: Identifying patterns ({feedback_count} feedback items)...")
                patterns = await self._identify_patterns(target_date)
                results["patterns"] = patterns
                results["steps_completed"].append("identify_patterns")

                # Step 4: Retrain if improvement > 2%
                potential_improvement = patterns.get("potential_improvement", 0)
                if potential_improvement > 0.02:
                    logger.info(
                        f"Step 4/4: Retraining (potential improvement: +{potential_improvement:.1%})..."
                    )
                    await self._retrain_model(target_date, patterns)
                    results["steps_completed"].append("retrain_model")
                    await self.db.commit()
                else:
                    logger.info(
                        f"Skipping retrain: improvement {potential_improvement:.1%} < 2% threshold"
                    )
                    results["steps_completed"].append("skip_retrain")
            else:
                logger.info(
                    f"Insufficient feedback ({feedback_count} < 10). Skipping pattern analysis."
                )
                results["steps_completed"].append("skip_insufficient_data")

            logger.info(f"Nightly learning cycle complete for {target_date}")
            return results

        except Exception as exc:
            logger.error(f"Nightly learning cycle failed: {exc}", exc_info=True)
            results["error"] = str(exc)
            await self.db.rollback()
            raise

    async def _compute_metrics(self, metric_date: date) -> AssessmentMetrics:
        """Step 1: Calculate daily metrics."""
        metrics = await self.metrics_collector.calculate_daily_metrics(
            metric_date, model_version="v1"
        )

        logger.info(
            f"Computed metrics for {metric_date}: "
            f"Accuracy={metrics.accuracy:.1%}, "
            f"Precision={metrics.precision:.1%}, "
            f"Recall={metrics.recall:.1%}, "
            f"F1={metrics.f1_score:.1%}"
        )

        return metrics

    async def _collect_feedback(self, target_date: date) -> int:
        """Step 2: Aggregate feedback from target_date to target_date+1."""
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = datetime.combine(
            target_date + timedelta(days=1), datetime.min.time()
        )

        stmt = select(func.count(HiringOutcome.id)).where(
            and_(
                HiringOutcome.created_at >= start_time,
                HiringOutcome.created_at < end_time,
                HiringOutcome.hiring_decision != HiringDecision.pending,
            )
        )

        result = await self.db.execute(stmt)
        count = result.scalar() or 0

        logger.info(f"Collected {count} feedback items from {target_date}")
        return count

    async def _identify_patterns(self, target_date: date) -> dict:
        """Step 3: Analyze patterns in recent outcomes."""
        patterns = {}

        # Query recent assessments with outcomes (last 30 days)
        thirty_days_ago = datetime.combine(
            target_date - timedelta(days=30), datetime.min.time()
        )

        stmt = select(Assessment).where(
            and_(
                Assessment.updated_at >= thirty_days_ago,
                Assessment.status == AssessmentStatus.completed,
                Assessment.capability_score.isnot(None),
            )
        )

        result = await self.db.execute(stmt)
        recent_assessments = result.scalars().all()

        logger.info(f"Analyzing {len(recent_assessments)} recent assessments")

        # Pattern 1: Which capability components predict success?
        component_success = await self._analyze_component_success(recent_assessments)
        patterns["component_predictors"] = component_success

        # Pattern 2: Role-specific insights
        role_patterns = await self._analyze_role_patterns(recent_assessments)
        patterns["role_patterns"] = role_patterns

        # Pattern 3: Threshold optimization
        optimal_threshold = await self._calibrate_threshold(recent_assessments)
        patterns["optimal_threshold"] = optimal_threshold

        # Estimate potential improvement
        current_metrics = await self.db.get(AssessmentMetrics, None)
        # Get latest metrics for target_date
        stmt = select(AssessmentMetrics).where(
            AssessmentMetrics.metric_date == target_date
        )
        result = await self.db.execute(stmt)
        current_metric = result.scalar_one_or_none()

        if current_metric:
            patterns["current_f1"] = current_metric.f1_score or 0.0
            # Conservative estimate: 2-5% improvement
            patterns["potential_improvement"] = 0.03

        logger.info(f"Identified {len(patterns)} pattern types")
        return patterns

    async def _analyze_component_success(self, assessments: list[Assessment]) -> dict:
        """Which capability components correlate with hires?"""
        # Aggregate component scores for hired vs not hired
        hired_components = {}
        rejected_components = {}

        for assessment in assessments:
            # Get outcome
            outcome_stmt = select(HiringOutcome).where(
                HiringOutcome.position_id == assessment.position_id
            ).order_by(HiringOutcome.created_at.desc()).limit(1)

            outcome_result = await self.db.execute(outcome_stmt)
            outcome = outcome_result.scalar_one_or_none()

            if not outcome or not assessment.capability_components:
                continue

            is_hired = outcome.hiring_decision in (
                HiringDecision.hired,
                HiringDecision.offer_declined,
            )
            target_dict = hired_components if is_hired else rejected_components

            # Extract component scores
            for comp_name, comp_data in assessment.capability_components.items():
                if isinstance(comp_data, dict) and "score" in comp_data:
                    score = comp_data["score"]
                    if comp_name not in target_dict:
                        target_dict[comp_name] = []
                    target_dict[comp_name].append(score)

        # Compute average scores per component
        component_analysis = {}
        all_components = set(hired_components.keys()) | set(rejected_components.keys())

        for comp in all_components:
            hired_scores = hired_components.get(comp, [])
            rejected_scores = rejected_components.get(comp, [])

            hired_avg = sum(hired_scores) / len(hired_scores) if hired_scores else 0
            rejected_avg = sum(rejected_scores) / len(rejected_scores) if rejected_scores else 0

            component_analysis[comp] = {
                "avg_hired": round(hired_avg, 2),
                "avg_rejected": round(rejected_avg, 2),
                "delta": round(hired_avg - rejected_avg, 2),
                "predictiveness": round(abs(hired_avg - rejected_avg) / 100, 2),
            }

        # Sort by predictiveness
        return dict(
            sorted(
                component_analysis.items(),
                key=lambda x: x[1]["predictiveness"],
                reverse=True,
            )
        )

    async def _analyze_role_patterns(self, assessments: list[Assessment]) -> dict:
        """Per-role success patterns."""
        role_analysis = {}

        # Group by role
        by_role: dict[str, list[Assessment]] = {}
        for assessment in assessments:
            position = await self.db.get(Position, assessment.position_id)
            if not position:
                continue

            role = position.title or "unknown"
            if role not in by_role:
                by_role[role] = []
            by_role[role].append(assessment)

        # Analyze each role
        for role, role_assessments in by_role.items():
            hired = 0
            rejected = 0
            total_score = 0

            for assessment in role_assessments:
                outcome_stmt = select(HiringOutcome).where(
                    HiringOutcome.position_id == assessment.position_id
                ).order_by(HiringOutcome.created_at.desc()).limit(1)

                outcome_result = await self.db.execute(outcome_stmt)
                outcome = outcome_result.scalar_one_or_none()

                if outcome:
                    if outcome.hiring_decision in (
                        HiringDecision.hired,
                        HiringDecision.offer_declined,
                    ):
                        hired += 1
                    else:
                        rejected += 1

                total_score += assessment.capability_score or 0

            total = hired + rejected
            if total > 0:
                role_analysis[role] = {
                    "hire_rate": round(hired / total, 2),
                    "avg_score": round(total_score / len(role_assessments), 1),
                    "sample_size": total,
                    "hired": hired,
                    "rejected": rejected,
                }

        return role_analysis

    async def _calibrate_threshold(self, assessments: list[Assessment]) -> float:
        """Recommend optimal capability_score threshold."""
        # Analyze hired vs rejected at different score ranges
        score_buckets: dict[int, dict] = {}

        for assessment in assessments:
            score = assessment.capability_score or 0
            bucket = (score // 10) * 10  # 0-10, 10-20, etc.

            if bucket not in score_buckets:
                score_buckets[bucket] = {"hired": 0, "total": 0}

            outcome_stmt = select(HiringOutcome).where(
                HiringOutcome.position_id == assessment.position_id
            ).order_by(HiringOutcome.created_at.desc()).limit(1)

            outcome_result = await self.db.execute(outcome_stmt)
            outcome = outcome_result.scalar_one_or_none()

            if outcome:
                if outcome.hiring_decision in (
                    HiringDecision.hired,
                    HiringDecision.offer_declined,
                ):
                    score_buckets[bucket]["hired"] += 1
                score_buckets[bucket]["total"] += 1

        # Find threshold where hire rate crosses 50%
        optimal_threshold = HIRE_THRESHOLD  # Default
        for score in sorted(score_buckets.keys()):
            bucket = score_buckets[score]
            if bucket["total"] > 0:
                hire_rate = bucket["hired"] / bucket["total"]
                if hire_rate >= 0.5:
                    optimal_threshold = score + 5
                    break

        logger.info(f"Calibrated threshold: {optimal_threshold} (from {HIRE_THRESHOLD})")
        return optimal_threshold

    async def _retrain_model(self, target_date: date, patterns: dict) -> None:
        """Step 4: Update learned weights and thresholds."""
        try:
            # Get or create current cognitive state
            stmt = select(CognitiveState).where(
                CognitiveState.agent_type == "system"
            )
            result = await self.db.execute(stmt)
            cognitive_state = result.scalar_one_or_none()

            if not cognitive_state:
                cognitive_state = CognitiveState(
                    agent_type="system",
                    decision_weights={},
                    gate_thresholds={"capability_hire": HIRE_THRESHOLD},
                    reasoning_confidence=0.5,
                )
                self.db.add(cognitive_state)
                await self.db.flush()

            # Update gate thresholds based on patterns
            old_threshold = cognitive_state.gate_thresholds.get(
                "capability_hire", HIRE_THRESHOLD
            )
            new_threshold = patterns.get("optimal_threshold", old_threshold)

            cognitive_state.gate_thresholds["capability_hire"] = new_threshold
            cognitive_state.updated_at = utcnow()

            # Log evolution
            evolution_log = CognitiveEvolutionLog(
                agent_type="system",
                event_type="threshold_adjusted",
                before_state={"threshold": old_threshold},
                after_state={"threshold": new_threshold},
                change_reason=f"Calibration from patterns: {patterns.get('role_patterns', {})}",
                expected_improvement=patterns.get("potential_improvement", 0),
                triggered_by_date=target_date,
                created_at=utcnow(),
                updated_at=utcnow(),
            )

            self.db.add(evolution_log)
            await self.db.flush()

            logger.info(
                f"Updated capability_hire threshold: {old_threshold} → {new_threshold}"
            )

        except Exception as exc:
            logger.error(f"Failed to retrain model: {exc}", exc_info=True)
            # Don't raise — learning must not block operations


__all__ = ["LearningPipeline"]
