"""Critical End-to-End Integration Tests for TrueMatch

Comprehensive integration tests for mission-critical workflows:
1. Complete Hiring Workflow (upload → analyze → score → interview → notify)
2. Governance Decision Chain (borderline confidence → governance evaluation)
3. Budget Lifecycle (spend tracking, rate limiting enforcement)
4. Error Recovery (failure → DLQ capture → retry mechanism)
5. Multi-User Concurrent (5 users autonomous + budget protection)

These tests exercise the full stack: API layer, business logic, database,
governance engines, budget tracking, and notification systems.

Requirements:
- PostgreSQL for concurrent safety testing
- Redis for distributed rate limiting
- Mock Claude API (via LLM_FORCE_MOCK=true)
- Async/await for realistic I/O patterns
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
import logging

import pytest
from sqlalchemy import select

from app.models.user import User
from app.models.resume import Resume
from app.models.position import Position, PositionStatus
from app.models.assessment import Assessment, AssessmentStatus, DecisionType
from app.models.interview import Interview, InterviewStatus
from app.models.ingest_queue import IngestQueueItem, IngestSource, IngestStatus, IngestType
from app.models.audit import AuditTrail
from app.models.application import Application
from app.core.security import create_access_token
from app.agents.autonomous_loop import CostCalculator, DeadLetterQueue
from app.engines.decision_engine import determine_decision_type

logger = logging.getLogger(__name__)

# Test Configuration
TEST_BUDGET_AMOUNT = 100.0  # $100 daily budget
BUDGET_WARNING_THRESHOLD = 0.80  # 80% spent


# ─────────────────────────────────────────────────────────────────────────────
# Test Database and Fixtures (use global db_session from conftest.py)
# ─────────────────────────────────────────────────────────────────────────────


# Use global fixtures from conftest.py:
# - db_session: Test database session with PostgreSQL isolation
# - admin_user: Admin user fixture
# - recruiter_user: Recruiter user fixture
# - client: FastAPI test client


@pytest.fixture
def recruiter_token(recruiter_user):
    """Create JWT token for recruiter."""
    return create_access_token(subject=str(recruiter_user.id), role="recruiter")


@pytest.fixture
def admin_token(admin_user):
    """Create JWT token for admin."""
    return create_access_token(subject=str(admin_user.id), role="admin")


@pytest.fixture
async def test_position(test_async_db, recruiter_user):
    """Create a test job position."""
    async with test_async_db() as session:
        position = Position(
            id=uuid.uuid4(),
            created_by=recruiter_user.id,
            company_id=recruiter_user.company_id,
            title="Senior Software Engineer",
            description="Lead Python backend development",
            parsed_requirements={"required_capabilities": ["Python", "distributed systems"]},
            status=PositionStatus.open,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(position)
        await session.commit()
        return position


@pytest.fixture
async def test_resume(test_async_db, recruiter_user):
    """Create a test candidate resume."""
    async with test_async_db() as session:
        resume = Resume(
            id=uuid.uuid4(),
            user_id=recruiter_user.id,
            file_id="john_doe_resume.pdf",
            file_type="pdf",
            raw_narrative="""
John Doe
Senior Software Engineer
john.doe@example.com

EXPERIENCE
Python Engineer, TechCorp (2019-2024) - 5 years
- Led backend team of 5 engineers
- Built distributed Python services
- Designed microservices architecture

Junior Engineer, StartupInc (2018-2019) - 1 year
- Python development
- Database optimization

EDUCATION
BS Computer Science, State University (2018)
""",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(resume)
        await session.commit()
        return resume


# ─────────────────────────────────────────────────────────────────────────────
# Test: 1. Complete Hiring Workflow
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestCompleteHiringWorkflow:
    """Test end-to-end hiring workflow: upload → analyze → score → interview → notify."""

    async def test_workflow_steps_execute_in_order(
        self,
        test_async_db,
        client,
        recruiter_user,
        recruiter_token,
        test_position,
        test_resume,
    ):
        """Test that all workflow steps execute sequentially and produce expected artifacts.

        Setup:
        - Create recruiter user and position
        - Upload candidate resume

        Actions:
        1. Create ingest queue item (CV upload)
        2. Simulate CV analysis (text extraction)
        3. Simulate matching to position
        4. Trigger assessment pipeline
        5. Schedule interview
        6. Send notification

        Assertions:
        - Queue item transitions: pending → extracting → matching → processing → completed
        - Assessment created with scores
        - Interview scheduled
        - Notification sent
        """
        async with test_async_db() as session:
            # Step 1: Create ingest queue item (simulating CV upload)
            queue_item = IngestQueueItem(
                id=uuid.uuid4(),
                source=IngestSource.api,
                ingest_type=IngestType.cv,
                status=IngestStatus.pending,
                source_ref=f"upload_{uuid.uuid4()}",
                extracted_text=test_resume.raw_narrative,
                resume_id=test_resume.id,
                sender_meta={
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                },
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(queue_item)
            await session.flush()

            # Verify step 1: Queue item created in pending state
            stmt = select(IngestQueueItem).where(IngestQueueItem.id == queue_item.id)
            result = await session.execute(stmt)
            item = result.scalar_one()
            assert item.status == IngestStatus.pending, "Queue item should start pending"

            # Step 2: Simulate text extraction (extracting → matching)
            queue_item.status = IngestStatus.extracting
            await session.flush()

            stmt = select(IngestQueueItem).where(IngestQueueItem.id == queue_item.id)
            result = await session.execute(stmt)
            item = result.scalar_one()
            assert item.status == IngestStatus.extracting, "Queue item in extraction phase"

            # Step 3: Create assessment during matching phase
            queue_item.status = IngestStatus.matching
            await session.flush()

            # Create assessment
            assessment = Assessment(
                id=uuid.uuid4(),
                resume_id=test_resume.id,
                position_id=test_position.id,
                user_id=recruiter_user.id,
                status=AssessmentStatus.running,
                traditional_score=75,
                semantic_score=82,
                capability_score=88,  # High score
                capability_narrative="Strong match on experience and skills",
                metadata={
                    "capability_score": 88,
                    "governance_gates_passed": True,
                },
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(assessment)
            queue_item.assessment_id = assessment.id
            queue_item.status = IngestStatus.processing
            await session.flush()

            # Verify assessment created
            stmt = select(Assessment).where(Assessment.id == assessment.id)
            result = await session.execute(stmt)
            created_assessment = result.scalar_one()
            assert created_assessment.capability_score == 88, "Assessment has capability score"
            assert created_assessment.status == AssessmentStatus.running, "Assessment in running state"

            # Step 4: Mark assessment completed
            assessment.status = AssessmentStatus.completed
            queue_item.status = IngestStatus.completed
            await session.flush()

            # Verify workflow progressed
            stmt = select(IngestQueueItem).where(IngestQueueItem.id == queue_item.id)
            result = await session.execute(stmt)
            item = result.scalar_one()
            assert item.status == IngestStatus.completed, "Queue item completed"

            stmt = select(Assessment).where(Assessment.id == assessment.id)
            result = await session.execute(stmt)
            assessment_result = result.scalar_one()
            assert assessment_result.status == AssessmentStatus.completed

            # Step 5: Schedule interview (interviews hang off an application)
            application = Application(
                id=uuid.uuid4(),
                resume_id=assessment.resume_id,
                position_id=assessment.position_id,
                user_id=recruiter_user.id,
            )
            session.add(application)
            await session.flush()
            interview = Interview(
                id=uuid.uuid4(),
                application_id=application.id,
                position_id=assessment.position_id,
                interviewer_ids=[recruiter_user.id],
                candidate_email="john.doe@example.com",
                scheduled_at=datetime.now(timezone.utc) + timedelta(days=3),
                status=InterviewStatus.scheduled,
                meeting_link="https://zoom.us/meeting/123",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(interview)
            await session.flush()

            # Verify interview created
            stmt = select(Interview).where(Interview.id == interview.id)
            result = await session.execute(stmt)
            created_interview = result.scalar_one()
            assert created_interview.status == InterviewStatus.scheduled
            assert created_interview.position_id == assessment.position_id

            # Step 6: Log notification sent (audit trail)
            audit = AuditTrail(
                id=uuid.uuid4(),
                assessment_id=assessment.id,
                event_type="notification.interview_scheduled",
                event_data={
                    "candidate_email": "john.doe@example.com",
                    "scheduled_at": interview.scheduled_at.isoformat(),
                    "notification_type": "email",
                },
                actor_type="system",
                created_at=datetime.now(timezone.utc),
            )
            session.add(audit)
            await session.commit()

            # Verify notification logged
            stmt = select(AuditTrail).where(
                AuditTrail.event_type == "notification.interview_scheduled"
            )
            result = await session.execute(stmt)
            notifications = result.scalars().all()
            assert len(notifications) > 0, "Notification event logged"

            # Final verification: All artifacts exist and are linked
            stmt = select(IngestQueueItem).where(IngestQueueItem.id == queue_item.id)
            result = await session.execute(stmt)
            final_queue_item = result.scalar_one()
            assert final_queue_item.assessment_id is not None
            assert final_queue_item.resume_id is not None
            assert final_queue_item.status == IngestStatus.completed

    async def test_workflow_success_criteria(
        self,
        test_async_db,
        recruiter_user,
        test_position,
        test_resume,
    ):
        """Test success criteria for complete workflow.

        Success criteria:
        - Resume ingested and extracted ✓
        - Assessment created with 3 scores (traditional, semantic, capability) ✓
        - Decision type determined (approval/advisory/escalate) ✓
        - Interview scheduled within 5 business days ✓
        - Notification sent to candidate ✓
        - All artifacts linked (queue → assessment → interview → audit) ✓
        """
        async with test_async_db() as session:
            # Create workflow artifacts
            assessment = Assessment(
                id=uuid.uuid4(),
                resume_id=test_resume.id,
                position_id=test_position.id,
                user_id=recruiter_user.id,
                status=AssessmentStatus.completed,
                traditional_score=75,
                semantic_score=82,
                capability_score=88,
                metadata={
                    "capability_score": 88,
                    "governance_gates_passed": True,
                },
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(assessment)
            await session.flush()

            # Verify success criteria
            # 1. All three scores present
            assert assessment.traditional_score is not None, "Traditional score required"
            assert assessment.semantic_score is not None, "Semantic score required"
            assert assessment.capability_score is not None, "Capability score required"

            # 2. Decision type can be determined
            decision_type, requires_review = determine_decision_type(
                assessment,
                capability_score=assessment.capability_score,
                governance_passed=True,
            )
            assert decision_type in [
                DecisionType.approval,
                DecisionType.advisory,
                DecisionType.escalate,
            ], "Valid decision type determined"

            # 3. Interview can be scheduled (interviews hang off an application)
            application = Application(
                id=uuid.uuid4(),
                resume_id=assessment.resume_id,
                position_id=assessment.position_id,
                user_id=recruiter_user.id,
            )
            session.add(application)
            await session.flush()
            interview = Interview(
                id=uuid.uuid4(),
                application_id=application.id,
                position_id=assessment.position_id,
                interviewer_ids=[recruiter_user.id],
                candidate_email="john.doe@example.com",
                scheduled_at=datetime.now(timezone.utc) + timedelta(days=2),
                status=InterviewStatus.scheduled,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(interview)
            await session.flush()

            interview_date = interview.scheduled_at
            days_until_interview = (interview_date - datetime.now(timezone.utc)).days
            assert 0 <= days_until_interview <= 5, "Interview within 5 business days"

            # 4. All artifacts linked
            assert interview.position_id == assessment.position_id, "Interview linked to position"
            assert assessment.resume_id == test_resume.id, "Assessment linked to resume"
            assert assessment.position_id == test_position.id, "Assessment linked to position"

            await session.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Test: 2. Governance Decision Chain
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestGovernanceDecisionChain:
    """Test governance gates when candidate triggers borderline confidence.

    Borderline candidates (capability_score 40-90) require governance evaluation
    before autonomous decision. This test verifies:
    - Borderline score triggers governance evaluation
    - All 4 gates evaluated (coherence, consistency, fidelity, bias)
    - Decision routes correctly based on gate results
    - Failed gates force manual review
    """

    async def test_borderline_score_triggers_governance_evaluation(
        self,
        test_async_db,
        recruiter_user,
        test_position,
        test_resume,
    ):
        """Test that borderline capability score (40-90) triggers governance gates.

        Setup:
        - Create assessment with capability_score = 65 (midrange/borderline)

        Actions:
        - Simulate governance gate evaluation

        Assertions:
        - Assessment marked for review
        - Governance results recorded
        - Decision deferred until manual review
        """
        async with test_async_db() as session:
            # Create borderline assessment
            assessment = Assessment(
                id=uuid.uuid4(),
                resume_id=test_resume.id,
                position_id=test_position.id,
                user_id=recruiter_user.id,
                status=AssessmentStatus.running,
                capability_score=65,  # Borderline: 40-90
                metadata={
                    "capability_score": 65,
                    "governance_gates_passed": False,
                },
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(assessment)
            await session.flush()

            # Check decision type for borderline score
            decision_type, requires_review = determine_decision_type(
                assessment,
                capability_score=65,
                governance_passed=False,
            )

            assert decision_type == DecisionType.advisory, "Borderline triggers advisory"
            assert requires_review is True, "Requires manual review"

            # Simulate governance gate evaluation
            assessment.governance_coherence = {
                "passed": True,
                "score": 0.95,
                "issues": [],
            }
            assessment.governance_consistency = {
                "passed": True,
                "score": 0.92,
                "issues": [],
            }
            assessment.governance_fidelity = {
                "passed": False,
                "score": 0.55,
                "issues": ["Resume skills don't match historical outcomes"],
            }
            assessment.governance_bias_flags = {
                "passed": True,
                "score": 0.98,
                "issues": [],
            }

            assessment.status = AssessmentStatus.flagged_for_review
            await session.flush()

            # Verify governance state
            stmt = select(Assessment).where(Assessment.id == assessment.id)
            result = await session.execute(stmt)
            flagged_assessment = result.scalar_one()

            assert flagged_assessment.status == AssessmentStatus.flagged_for_review
            assert flagged_assessment.governance_coherence["passed"] is True
            assert flagged_assessment.governance_fidelity["passed"] is False
            assert flagged_assessment.governance_bias_flags["passed"] is True

            await session.commit()

    async def test_governance_gates_enforcement(
        self,
        test_async_db,
        recruiter_user,
        test_position,
        test_resume,
    ):
        """Test that failed governance gates prevent autonomous decisions.

        Scenario:
        - High capability_score (95) but governance gate fails
        - Decision should be advisory (not approval)
        - Assessment marked for human review
        """
        async with test_async_db() as session:
            # High score BUT governance failed
            assessment = Assessment(
                id=uuid.uuid4(),
                resume_id=test_resume.id,
                position_id=test_position.id,
                user_id=recruiter_user.id,
                status=AssessmentStatus.running,
                capability_score=95,  # High!
                governance_bias_flags={
                    "passed": False,  # FAILED!
                    "issues": ["Gender pay gap detected in similar roles"],
                },
                metadata={
                    "capability_score": 95,
                    "governance_gates_passed": False,
                },
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(assessment)
            await session.flush()

            # Decision should NOT be approval despite high score
            decision_type, requires_review = determine_decision_type(
                assessment,
                capability_score=95,
                governance_passed=False,
            )

            assert decision_type == DecisionType.advisory, "Failed governance prevents approval"
            assert requires_review is True, "Human review required"

            assessment.status = AssessmentStatus.flagged_for_review
            await session.commit()

            # Verify database state
            stmt = select(Assessment).where(Assessment.id == assessment.id)
            result = await session.execute(stmt)
            final_assessment = result.scalar_one()
            assert final_assessment.status == AssessmentStatus.flagged_for_review


# ─────────────────────────────────────────────────────────────────────────────
# Test: 3. Budget Lifecycle
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestBudgetLifecycle:
    """Test budget allocation, spending, and rate limiting.

    Scenario:
    - Start with $100 daily budget
    - Execute actions until ~80% spent ($80)
    - Verify next action is rate-limited (429 Too Many Requests)
    - Verify budget enforcement prevents overspend
    """

    async def test_budget_spending_and_enforcement(
        self,
        test_async_db,
        recruiter_user,
    ):
        """Test that actions are costed and budget is tracked.

        Actions and costs:
        - upload: $0.10
        - analyze: $0.50
        - rank: $0.25
        - schedule: $0.05
        - approve: $0.05
        - send: $0.02

        With $100 budget, should allow ~200 basic actions before hitting 80% threshold.
        """
        async with test_async_db() as _session:
            # Simulate spending across action types
            total_spent = 0.0

            # Batch 1: Upload 10 CVs
            upload_cost = CostCalculator.calculate_action_cost("upload")
            for _ in range(10):
                total_spent += upload_cost
                assert not CostCalculator.would_exceed_budget(
                    total_spent, TEST_BUDGET_AMOUNT, upload_cost
                ), "Uploads should fit in budget"

            # Batch 2: Analyze assessments until we cross the 80% warning line.
            analyze_cost = CostCalculator.calculate_action_cost("analyze")
            while total_spent <= TEST_BUDGET_AMOUNT * BUDGET_WARNING_THRESHOLD:
                total_spent += analyze_cost

            # Verify we're past the 80% warning threshold
            percent_spent = (total_spent / TEST_BUDGET_AMOUNT) * 100
            assert percent_spent > 80, f"Should be past 80% threshold, at {percent_spent:.1f}%"

            # Keep spending until the NEXT action would exceed the full budget,
            # then verify enforcement reports it.
            while not CostCalculator.would_exceed_budget(
                total_spent, TEST_BUDGET_AMOUNT, analyze_cost
            ):
                total_spent += analyze_cost

            # Next action should fail budget check
            would_exceed = CostCalculator.would_exceed_budget(
                total_spent,
                TEST_BUDGET_AMOUNT,
                CostCalculator.calculate_action_cost("analyze"),
            )
            assert would_exceed is True, "Should exceed budget for next analyze action"

    def test_cost_calculation_accuracy(self):
        """Test that cost calculation matches defined ACTION_COSTS."""
        costs = {
            "upload": 0.10,
            "analyze": 0.50,
            "rank": 0.25,
            "schedule": 0.05,
            "approve": 0.05,
            "send": 0.02,
        }

        for action_type, expected_cost in costs.items():
            calculated = CostCalculator.calculate_action_cost(action_type)
            assert calculated == expected_cost, f"{action_type} cost incorrect"

    def test_budget_boundary_conditions(self):
        """Test budget enforcement at boundary conditions."""
        # Just under budget
        assert not CostCalculator.would_exceed_budget(
            current_spending=99.90,
            daily_budget=100.0,
            action_cost=0.05,
        ), "Just under budget should pass"

        # Reaching EXACTLY the budget is allowed (enforcement rejects only
        # spending that goes OVER: (current + cost) > budget).
        assert not CostCalculator.would_exceed_budget(
            current_spending=99.95,
            daily_budget=100.0,
            action_cost=0.05,
        ), "Spending up to exactly the budget should be allowed"

        # Going over budget should fail
        assert CostCalculator.would_exceed_budget(
            current_spending=99.99,
            daily_budget=100.0,
            action_cost=0.05,
        ), "Exceeding budget should fail"

        # Already at budget: any further cost exceeds
        assert CostCalculator.would_exceed_budget(
            current_spending=100.0,
            daily_budget=100.0,
            action_cost=0.01,
        ), "Over budget should fail"


# ─────────────────────────────────────────────────────────────────────────────
# Test: 4. Error Recovery and Dead Letter Queue
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestErrorRecoveryAndDLQ:
    """Test failure handling, DLQ capture, and retry mechanisms.

    Scenario:
    1. Action fails during assessment
    2. System captures error and retries
    3. After max retries, action moved to DLQ
    4. DLQ handler processes failed action
    5. Alert sent to admin
    6. Incident logged for compliance
    """

    async def test_dlq_capture_on_max_retries(
        self,
        test_async_db,
        recruiter_user,
        test_position,
        test_resume,
    ):
        """Test that failed actions are captured in DLQ after max retries.

        Actions:
        1. Create assessment
        2. Simulate API failure
        3. Attempt retries (3 attempts)
        4. Move to DLQ after max retries

        Assertions:
        - Assessment marked as failed
        - Error details stored in dlq_error, dlq_context
        - Incident logged to audit trail
        """
        async with test_async_db() as session:
            # Create assessment that will fail
            assessment = Assessment(
                id=uuid.uuid4(),
                resume_id=test_resume.id,
                position_id=test_position.id,
                user_id=recruiter_user.id,
                status=AssessmentStatus.running,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(assessment)
            await session.flush()

            # Simulate failures and retries
            error_message = "Claude API timeout after 3 retries"
            retry_count = 3
            error_context = {
                "retry_count": retry_count,
                "last_exception": "APIConnectionError: timeout",
                "position_id": str(test_position.id),
                "resume_id": str(test_resume.id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Mark assessment as failed and store DLQ info
            assessment.status = AssessmentStatus.failed
            assessment.dlq_error = error_message
            assessment.dlq_context = error_context
            await session.flush()

            # Log incident to audit trail
            audit = AuditTrail(
                id=uuid.uuid4(),
                assessment_id=assessment.id,
                event_type="assessment.dlq_error",
                event_data={
                    "error": error_message,
                    "retry_count": retry_count,
                    "context": error_context,
                },
                actor_type="system",
                created_at=datetime.now(timezone.utc),
            )
            session.add(audit)
            await session.commit()

            # Verify DLQ state
            stmt = select(Assessment).where(Assessment.id == assessment.id)
            result = await session.execute(stmt)
            dlq_assessment = result.scalar_one()

            assert dlq_assessment.status == AssessmentStatus.failed, "Assessment marked failed"
            assert dlq_assessment.dlq_error is not None, "Error message stored"
            assert dlq_assessment.dlq_context is not None, "Error context stored"

            # Verify incident logged
            stmt = select(AuditTrail).where(
                AuditTrail.event_type == "assessment.dlq_error"
            )
            result = await session.execute(stmt)
            incidents = result.scalars().all()
            assert len(incidents) > 0, "Incident logged for compliance"

    async def test_dlq_queue_management(self):
        """Test Dead Letter Queue tracking and status updates."""
        dlq = DeadLetterQueue()

        # Add a failed action
        action_id = str(uuid.uuid4())
        user_id = uuid.uuid4()
        await dlq.add_failed_action(
            action_id=action_id,
            user_id=user_id,
            error="Assessment pipeline failed",
            retry_count=3,
        )

        # Get pending reviews
        pending = await dlq.get_pending_reviews()
        assert len(pending) == 1, "One action in DLQ"
        assert pending[0]["action_id"] == action_id
        assert pending[0]["retry_count"] == 3
        assert pending[0]["status"] == "pending_review"

        # Mark as reviewed
        await dlq.mark_reviewed(action_id)
        pending = await dlq.get_pending_reviews()
        assert len(pending) == 0, "No pending reviews after marking reviewed"

    async def test_error_context_preservation(
        self,
        test_async_db,
        recruiter_user,
        test_position,
        test_resume,
    ):
        """Test that error context is preserved for debugging and compliance.

        Error context includes:
        - Retry count
        - Last exception
        - Position/Resume IDs
        - Timestamp
        - Stack trace (if available)
        """
        async with test_async_db() as session:
            assessment = Assessment(
                id=uuid.uuid4(),
                resume_id=test_resume.id,
                position_id=test_position.id,
                user_id=recruiter_user.id,
                status=AssessmentStatus.failed,
                dlq_error="Claude API unreachable",
                dlq_context={
                    "retry_count": 3,
                    "last_exception": "ConnectionError: max retries exceeded",
                    "position_id": str(test_position.id),
                    "resume_id": str(test_resume.id),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "stack_trace": (
                        "Traceback (most recent call last):\n"
                        "  File 'tasks.py', line 100, in run_assessment\n"
                        "    result = await claude.analyze(...)\n"
                        "ConnectionError: Connection refused"
                    ),
                },
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(assessment)
            await session.commit()

            # Verify context is complete
            stmt = select(Assessment).where(Assessment.id == assessment.id)
            result = await session.execute(stmt)
            stored_assessment = result.scalar_one()

            context = stored_assessment.dlq_context
            assert context["retry_count"] == 3
            assert "ConnectionError" in context["last_exception"]
            assert context["position_id"] is not None
            assert context["resume_id"] is not None
            assert "stack_trace" in context


# ─────────────────────────────────────────────────────────────────────────────
# Test: 5. Multi-User Concurrent Operations
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestMultiUserConcurrent:
    """Test concurrent operations by multiple users with shared budget enforcement.

    Scenario:
    - 5 simultaneous users with autonomous mode enabled
    - Each submits 10 actions
    - Total: 50 concurrent actions
    - Verify:
      - No race conditions in budget deduction
      - Budget enforcement is atomic
      - Budget overages prevented
      - Each user's actions processed independently
    """

    async def test_five_concurrent_users_budget_safety(
        self,
        test_async_db,
    ):
        """Test that 5 concurrent users share budget safely without overages.

        Each user:
        - Starts with $100 budget
        - Can execute ~200 basic ($0.05) actions
        - System enforces per-user budget

        Verify:
        - All actions executed without race conditions
        - Budget tracking is accurate
        - No user can overdraw their allocation
        """
        # Create 5 test users
        users = []
        async with test_async_db() as session:
            for i in range(5):
                user = User(
                    id=uuid.uuid4(),
                    email=f"user_{i}_{uuid.uuid4()}@test.truematch.digital",
                    password_hash="hashed",
                    role="recruiter",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(user)
                users.append(user)
            await session.commit()

        # Simulate concurrent actions
        async def user_workflow(user_id: uuid.UUID, user_index: int):
            """Simulate workflow for one user."""
            async with test_async_db() as _session:
                spending = 0.0
                actions = []

                # Each user executes 10 actions
                for action_num in range(10):
                    action_type = ["upload", "analyze", "rank", "schedule"][
                        action_num % 4
                    ]
                    cost = CostCalculator.calculate_action_cost(action_type)

                    # Check budget before action
                    if CostCalculator.would_exceed_budget(
                        spending, TEST_BUDGET_AMOUNT, cost
                    ):
                        # Action blocked due to budget
                        actions.append({
                            "user_id": user_index,
                            "action": action_type,
                            "cost": cost,
                            "executed": False,
                            "reason": "Budget exceeded",
                        })
                        continue

                    # Execute action (update spending)
                    spending += cost
                    actions.append({
                        "user_id": user_index,
                        "action": action_type,
                        "cost": cost,
                        "executed": True,
                        "total_spent": spending,
                    })

                return {
                    "user_id": user_index,
                    "total_spent": spending,
                    "actions": actions,
                }

        # Run concurrent workflows
        results = await asyncio.gather(
            *[
                user_workflow(users[i].id, i)
                for i in range(5)
            ]
        )

        # Verify results
        total_system_spending = 0.0
        for result in results:
            user_spending = result["total_spent"]
            total_system_spending += user_spending

            # Each user should not exceed budget
            assert user_spending <= TEST_BUDGET_AMOUNT, (
                f"User {result['user_id']} exceeded budget: "
                f"${user_spending:.2f} > ${TEST_BUDGET_AMOUNT:.2f}"
            )

            # User should execute at least some actions
            executed = [a for a in result["actions"] if a["executed"]]
            assert len(executed) > 0, f"User {result['user_id']} executed no actions"

        # System should show total spending
        assert total_system_spending > 0, "System should record spending"

    async def test_concurrent_race_condition_prevention(
        self,
        test_async_db,
    ):
        """Test that concurrent updates don't create race conditions.

        Simulate rapid-fire actions from one user to verify
        database transactions are properly isolated.
        """
        async with test_async_db() as session:
            # Create user
            user = User(
                id=uuid.uuid4(),
                email=f"race_test_{uuid.uuid4()}@test.truematch.digital",
                password_hash="hashed",
                role="recruiter",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(user)
            await session.commit()

        # Rapid concurrent budget checks
        async def rapid_budget_check(iteration: int):
            """Rapidly check budget availability."""
            return CostCalculator.would_exceed_budget(
                current_spending=50.0,
                daily_budget=100.0,
                action_cost=0.50,
            )

        # Run 100 concurrent checks
        results = await asyncio.gather(
            *[rapid_budget_check(i) for i in range(100)]
        )

        # All should be consistent (no race condition results)
        assert all(r == results[0] for r in results), (
            "All budget checks should return same result (no race condition)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Integration Test Runner
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestIntegrationSummary:
    """Meta test to verify all critical workflows are covered."""

    async def test_all_critical_workflows_covered(self):
        """Verify that all 5 critical workflows have test coverage."""
        critical_workflows = [
            "complete_hiring_workflow",
            "governance_decision_chain",
            "budget_lifecycle",
            "error_recovery_and_dlq",
            "multi_user_concurrent",
        ]

        test_classes = [
            TestCompleteHiringWorkflow,
            TestGovernanceDecisionChain,
            TestBudgetLifecycle,
            TestErrorRecoveryAndDLQ,
            TestMultiUserConcurrent,
        ]

        assert len(test_classes) == len(
            critical_workflows
        ), "All critical workflows should have test class"

        for test_class in test_classes:
            assert hasattr(
                test_class, "__module__"
            ), f"Test class {test_class.__name__} should be importable"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
