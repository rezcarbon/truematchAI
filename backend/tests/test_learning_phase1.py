"""Comprehensive tests for Phase 1 learning system.

Tests:
- Metrics collection (TP/TN/FP/FN calculation)
- Learning pipeline orchestration
- Learning feedback API endpoints
- Celery task scheduling
- Learned context injection (via integration test)
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from typing import Any, AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.clock import utcnow
from app.database import Base
from app.models.assessment import Assessment, AssessmentStatus, DecisionType
from app.models.hiring_outcome import HiringDecision, HiringOutcome
from app.models.learning_metrics import AssessmentMetrics, CognitiveState, CognitiveEvolutionLog
from app.models.position import Position
from app.models.resume import Resume
from app.models.user import User, UserRole
from app.models.company import Company
from app.services.metrics_collector import MetricsCollector, HIRE_THRESHOLD
from app.services.learning_pipeline import LearningPipeline


# ─────────────────────────────────────────────────────────────────
# Fixtures: In-Memory Database
# ─────────────────────────────────────────────────────────────────


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create in-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def setup_test_data(test_db: AsyncSession) -> dict[str, Any]:
    """Create base test data: company, users, position, resume."""
    company = Company(
        id=uuid.uuid4(),
        name="Test Corp",
        domain="testcorp.com",
    )
    test_db.add(company)

    recruiter = User(
        id=uuid.uuid4(),
        email="recruiter@testcorp.com",
        role=UserRole.recruiter,
        company_id=company.id,
    )
    test_db.add(recruiter)

    candidate1 = User(
        id=uuid.uuid4(),
        email="candidate1@example.com",
        role=UserRole.candidate,
        company_id=company.id,
    )
    test_db.add(candidate1)

    candidate2 = User(
        id=uuid.uuid4(),
        email="candidate2@example.com",
        role=UserRole.candidate,
        company_id=company.id,
    )
    test_db.add(candidate2)

    position = Position(
        id=uuid.uuid4(),
        company_id=company.id,
        title="Software Engineer",
        description="Senior backend engineer",
    )
    test_db.add(position)

    resume1 = Resume(
        id=uuid.uuid4(),
        user_id=candidate1.id,
        raw_narrative="5 years Python, Django, FastAPI. Led team of 3.",
    )
    test_db.add(resume1)

    resume2 = Resume(
        id=uuid.uuid4(),
        user_id=candidate2.id,
        raw_narrative="2 years Python. Entry-level developer.",
    )
    test_db.add(resume2)

    await test_db.flush()

    return {
        "company": company,
        "recruiter": recruiter,
        "candidate1": candidate1,
        "candidate2": candidate2,
        "position": position,
        "resume1": resume1,
        "resume2": resume2,
    }


# ─────────────────────────────────────────────────────────────────
# Test: Metrics Collector
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_metrics_collector_calculates_tp_tn_fp_fn(
    test_db: AsyncSession, setup_test_data: dict
):
    """Test that metrics correctly identify TP, TN, FP, FN."""
    data = setup_test_data

    # Assessment 1: Predicted hire (score >= 60), actually hired → TP
    assessment1 = Assessment(
        id=uuid.uuid4(),
        resume_id=data["resume1"].id,
        position_id=data["position"].id,
        user_id=data["candidate1"].id,
        status=AssessmentStatus.completed,
        capability_score=75,  # > HIRE_THRESHOLD (60)
        decision_type=DecisionType.approval,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    test_db.add(assessment1)

    outcome1 = HiringOutcome(
        id=uuid.uuid4(),
        position_id=data["position"].id,
        candidate_id=data["candidate1"].id,
        candidate_match_id=uuid.uuid4(),
        hiring_decision=HiringDecision.hired,
        decision_made_at=utcnow(),
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    test_db.add(outcome1)

    # Assessment 2: Predicted reject (score < 60), actually rejected → TN
    assessment2 = Assessment(
        id=uuid.uuid4(),
        resume_id=data["resume2"].id,
        position_id=data["position"].id,
        user_id=data["candidate2"].id,
        status=AssessmentStatus.completed,
        capability_score=35,  # < HIRE_THRESHOLD (60)
        decision_type=DecisionType.escalate,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    test_db.add(assessment2)

    outcome2 = HiringOutcome(
        id=uuid.uuid4(),
        position_id=data["position"].id,
        candidate_id=data["candidate2"].id,
        candidate_match_id=uuid.uuid4(),
        hiring_decision=HiringDecision.not_hired,
        decision_made_at=utcnow(),
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    test_db.add(outcome2)

    await test_db.commit()

    # Collect metrics
    collector = MetricsCollector(test_db)
    metric_date = date.today()
    metrics = await collector.calculate_daily_metrics(metric_date)

    # Verify confusion matrix
    assert metrics.true_positives == 1, "Expected 1 TP (predicted hire, hired)"
    assert metrics.true_negatives == 1, "Expected 1 TN (predicted reject, rejected)"
    assert metrics.false_positives == 0, "Expected 0 FP"
    assert metrics.false_negatives == 0, "Expected 0 FN"

    # Verify computed metrics
    assert metrics.accuracy == 1.0, "Expected 100% accuracy (2/2 correct)"
    assert metrics.precision == 1.0, "Expected 100% precision"
    assert metrics.recall == 1.0, "Expected 100% recall"
    assert metrics.f1_score == 1.0, "Expected 100% F1 score"


@pytest.mark.asyncio
async def test_metrics_collector_handles_no_outcomes(
    test_db: AsyncSession, setup_test_data: dict
):
    """Test metrics calculation with no outcomes recorded."""
    data = setup_test_data

    assessment = Assessment(
        id=uuid.uuid4(),
        resume_id=data["resume1"].id,
        position_id=data["position"].id,
        user_id=data["candidate1"].id,
        status=AssessmentStatus.completed,
        capability_score=75,
        decision_type=DecisionType.approval,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    test_db.add(assessment)
    await test_db.commit()

    collector = MetricsCollector(test_db)
    metric_date = date.today()
    metrics = await collector.calculate_daily_metrics(metric_date)

    # No outcomes recorded
    assert metrics.assessments_with_outcome == 0
    assert metrics.accuracy is None
    assert metrics.f1_score is None


@pytest.mark.asyncio
async def test_metrics_collector_role_breakdown(
    test_db: AsyncSession, setup_test_data: dict
):
    """Test that metrics are computed per role."""
    data = setup_test_data

    assessment = Assessment(
        id=uuid.uuid4(),
        resume_id=data["resume1"].id,
        position_id=data["position"].id,
        user_id=data["candidate1"].id,
        status=AssessmentStatus.completed,
        capability_score=75,
        decision_type=DecisionType.approval,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    test_db.add(assessment)

    outcome = HiringOutcome(
        id=uuid.uuid4(),
        position_id=data["position"].id,
        candidate_id=data["candidate1"].id,
        candidate_match_id=uuid.uuid4(),
        hiring_decision=HiringDecision.hired,
        decision_made_at=utcnow(),
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    test_db.add(outcome)

    await test_db.commit()

    collector = MetricsCollector(test_db)
    metric_date = date.today()
    metrics = await collector.calculate_daily_metrics(metric_date)

    # Check role-specific metrics
    assert metrics.metrics_by_role, "Should have role metrics"
    role = data["position"].title
    assert role in metrics.metrics_by_role
    assert metrics.metrics_by_role[role]["accuracy"] == 1.0


# ─────────────────────────────────────────────────────────────────
# Test: Learning Pipeline
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_learning_pipeline_runs_all_steps(
    test_db: AsyncSession, setup_test_data: dict
):
    """Test that learning pipeline executes all 4 steps."""
    data = setup_test_data

    # Create enough assessments/outcomes for learning
    for i in range(15):
        candidate = User(
            id=uuid.uuid4(),
            email=f"candidate{i}@example.com",
            role=UserRole.candidate,
            company_id=data["company"].id,
        )
        test_db.add(candidate)

        resume = Resume(
            id=uuid.uuid4(),
            user_id=candidate.id,
            raw_narrative=f"Experience level {i}",
        )
        test_db.add(resume)

        score = 40 + (i * 3)  # Spread scores
        assessment = Assessment(
            id=uuid.uuid4(),
            resume_id=resume.id,
            position_id=data["position"].id,
            user_id=candidate.id,
            status=AssessmentStatus.completed,
            capability_score=score,
            decision_type=DecisionType.advisory,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        test_db.add(assessment)

        hired = score >= 60
        outcome = HiringOutcome(
            id=uuid.uuid4(),
            position_id=data["position"].id,
            candidate_id=candidate.id,
            candidate_match_id=uuid.uuid4(),
            hiring_decision=HiringDecision.hired if hired else HiringDecision.not_hired,
            decision_made_at=utcnow(),
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        test_db.add(outcome)

    await test_db.commit()

    # Run learning pipeline
    pipeline = LearningPipeline(test_db)
    metric_date = date.today()
    result = await pipeline.run_nightly_learning(metric_date)

    # Check that all steps completed
    assert "steps_completed" in result
    assert "compute_metrics" in result["steps_completed"]
    assert "collect_feedback" in result["steps_completed"]
    # With 15 outcomes, should reach 10+ threshold
    assert result["feedback_count"] >= 10

    # Metrics should be computed
    assert "metrics" in result
    assert result["metrics"]["total_assessments"] > 0


@pytest.mark.asyncio
async def test_learning_pipeline_skips_with_insufficient_feedback(
    test_db: AsyncSession, setup_test_data: dict
):
    """Test that pipeline skips pattern analysis with < 10 feedback items."""
    data = setup_test_data

    # Create only 5 assessments
    for i in range(5):
        candidate = User(
            id=uuid.uuid4(),
            email=f"candidate{i}@example.com",
            role=UserRole.candidate,
            company_id=data["company"].id,
        )
        test_db.add(candidate)

        resume = Resume(
            id=uuid.uuid4(),
            user_id=candidate.id,
            raw_narrative=f"Experience {i}",
        )
        test_db.add(resume)

        assessment = Assessment(
            id=uuid.uuid4(),
            resume_id=resume.id,
            position_id=data["position"].id,
            user_id=candidate.id,
            status=AssessmentStatus.completed,
            capability_score=50 + i,
            decision_type=DecisionType.escalate,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        test_db.add(assessment)

        outcome = HiringOutcome(
            id=uuid.uuid4(),
            position_id=data["position"].id,
            candidate_id=candidate.id,
            candidate_match_id=uuid.uuid4(),
            hiring_decision=HiringDecision.pending,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        test_db.add(outcome)

    await test_db.commit()

    pipeline = LearningPipeline(test_db)
    result = await pipeline.run_nightly_learning(date.today())

    # Should skip pattern analysis with insufficient data
    assert "skip_insufficient_data" in result["steps_completed"]


@pytest.mark.asyncio
async def test_learning_pipeline_updates_cognitive_state(
    test_db: AsyncSession, setup_test_data: dict
):
    """Test that learning pipeline updates cognitive state."""
    data = setup_test_data

    # Create initial cognitive state
    cognitive_state = CognitiveState(
        agent_type="system",
        gate_thresholds={"capability_hire": 60},
        reasoning_confidence=0.5,
    )
    test_db.add(cognitive_state)

    # Create assessments with outcomes
    for i in range(12):
        candidate = User(
            id=uuid.uuid4(),
            email=f"candidate{i}@example.com",
            role=UserRole.candidate,
            company_id=data["company"].id,
        )
        test_db.add(candidate)

        resume = Resume(
            id=uuid.uuid4(),
            user_id=candidate.id,
            raw_narrative=f"Exp {i}",
        )
        test_db.add(resume)

        score = 45 + (i * 2)
        assessment = Assessment(
            id=uuid.uuid4(),
            resume_id=resume.id,
            position_id=data["position"].id,
            user_id=candidate.id,
            status=AssessmentStatus.completed,
            capability_score=score,
            decision_type=DecisionType.advisory,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        test_db.add(assessment)

        outcome = HiringOutcome(
            id=uuid.uuid4(),
            position_id=data["position"].id,
            candidate_id=candidate.id,
            candidate_match_id=uuid.uuid4(),
            hiring_decision=HiringDecision.hired if score >= 60 else HiringDecision.not_hired,
            decision_made_at=utcnow(),
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        test_db.add(outcome)

    await test_db.commit()

    pipeline = LearningPipeline(test_db)
    result = await pipeline.run_nightly_learning(date.today())

    # Cognitive state should be updated
    from sqlalchemy import select
    stmt = select(CognitiveState).where(CognitiveState.agent_type == "system")
    db_result = await test_db.execute(stmt)
    updated_state = db_result.scalar_one()

    assert updated_state is not None
    assert updated_state.updated_at > cognitive_state.created_at


# ─────────────────────────────────────────────────────────────────
# Test: Celery Task
# ─────────────────────────────────────────────────────────────────


def test_learning_orchestrator_task_exists():
    """Test that Celery task is properly registered."""
    from app.workers.learning_orchestrator import run_nightly_learning_cycle

    assert run_nightly_learning_cycle is not None
    assert run_nightly_learning_cycle.name == (
        "app.workers.learning_orchestrator.run_nightly_learning_cycle"
    )


def test_learning_task_in_celery_beat_schedule():
    """Test that learning task is in Celery beat schedule."""
    from app.workers.celery_app import celery_app

    assert "nightly-learning-cycle" in celery_app.conf.beat_schedule
    schedule_entry = celery_app.conf.beat_schedule["nightly-learning-cycle"]
    assert schedule_entry["task"] == (
        "app.workers.learning_orchestrator.run_nightly_learning_cycle"
    )
    assert schedule_entry["schedule"] == 86400  # Once per day


# ─────────────────────────────────────────────────────────────────
# Test: API Endpoints (Mock Tests)
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_record_outcome_endpoint_requires_recruiter(
    test_db: AsyncSession, setup_test_data: dict
):
    """Test that only recruiters can record outcomes."""
    from app.api.v1.learning_feedback import record_hiring_outcome
    from app.core.exceptions import AuthorizationError

    data = setup_test_data

    assessment = Assessment(
        id=uuid.uuid4(),
        resume_id=data["resume1"].id,
        position_id=data["position"].id,
        user_id=data["candidate1"].id,
        status=AssessmentStatus.completed,
        capability_score=75,
        decision_type=DecisionType.approval,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    test_db.add(assessment)
    await test_db.flush()

    # Candidate user should be denied
    candidate = data["candidate1"]
    from app.api.v1.learning_feedback import RecordOutcomeRequest

    feedback = RecordOutcomeRequest(
        outcome="hired",
        outcome_reason="Test",
    )

    with pytest.raises(AuthorizationError):
        await record_hiring_outcome(assessment.id, feedback, candidate, test_db)


# ─────────────────────────────────────────────────────────────────
# Test: Integration
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_end_to_end_learning_cycle(
    test_db: AsyncSession, setup_test_data: dict
):
    """Test full cycle: assessment → outcome → metrics → learning."""
    data = setup_test_data

    # Create 20 assessments across a 30-day period
    base_date = date.today() - timedelta(days=30)
    for i in range(20):
        candidate = User(
            id=uuid.uuid4(),
            email=f"e2e_candidate{i}@example.com",
            role=UserRole.candidate,
            company_id=data["company"].id,
        )
        test_db.add(candidate)

        resume = Resume(
            id=uuid.uuid4(),
            user_id=candidate.id,
            raw_narrative=f"Experience {i}",
        )
        test_db.add(resume)

        # Score correlates with hire decision
        score = 40 + (i * 3)
        assessment = Assessment(
            id=uuid.uuid4(),
            resume_id=resume.id,
            position_id=data["position"].id,
            user_id=candidate.id,
            status=AssessmentStatus.completed,
            capability_score=score,
            decision_type=DecisionType.advisory,
            created_at=datetime.combine(base_date + timedelta(days=i), datetime.min.time()).replace(tzinfo=None),
            updated_at=datetime.combine(base_date + timedelta(days=i), datetime.min.time()).replace(tzinfo=None),
        )
        test_db.add(assessment)

        hired = score >= 60
        outcome = HiringOutcome(
            id=uuid.uuid4(),
            position_id=data["position"].id,
            candidate_id=candidate.id,
            candidate_match_id=uuid.uuid4(),
            hiring_decision=HiringDecision.hired if hired else HiringDecision.not_hired,
            decision_made_at=utcnow(),
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        test_db.add(outcome)

    await test_db.commit()

    # Run learning pipeline
    pipeline = LearningPipeline(test_db)
    target_date = date.today() - timedelta(days=1)
    result = await pipeline.run_nightly_learning(target_date)

    # Verify full cycle
    assert result["steps_completed"]
    assert "compute_metrics" in result["steps_completed"]
    assert result["feedback_count"] > 0
    assert "metrics" in result

    # Verify metrics make sense
    metrics = result["metrics"]
    assert metrics["total_assessments"] > 0
    assert 0 <= metrics["accuracy"] <= 1.0 if metrics["accuracy"] else True


__all__ = [
    "test_db",
    "setup_test_data",
    "test_metrics_collector_calculates_tp_tn_fp_fn",
    "test_metrics_collector_handles_no_outcomes",
    "test_metrics_collector_role_breakdown",
    "test_learning_pipeline_runs_all_steps",
    "test_learning_pipeline_skips_with_insufficient_feedback",
    "test_learning_pipeline_updates_cognitive_state",
    "test_learning_orchestrator_task_exists",
    "test_learning_task_in_celery_beat_schedule",
    "test_record_outcome_endpoint_requires_recruiter",
    "test_end_to_end_learning_cycle",
]
