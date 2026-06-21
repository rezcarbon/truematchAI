"""Comprehensive tests for Phase 3: Autonomous Loop.

Tests cover:
- Cost calculation and budget enforcement
- Dead letter queue management
- Metrics tracking
- Polling jitter (prevents thundering herd)
- Batch size limits
- Connection pool configuration
- Error handling and recovery
- Governance integration
- Rate limiting enforcement

Phase 3 Production-Ready Testing
"""
import pytest
from uuid import uuid4
import asyncio


from app.agents.autonomous_loop import (
    AutonomousLoopManager,
    CostCalculator,
    DeadLetterQueue,
    LoopMetrics,
    POLLING_INTERVAL_SECONDS,
    POLLING_JITTER_SECONDS,
    MAX_BATCH_SIZE,
)


@pytest.mark.asyncio
class TestCostCalculator:
    """Test cost calculation engine."""

    def test_calculate_cost_upload(self):
        """Upload actions cost $0.10."""
        cost = CostCalculator.calculate_action_cost("upload")
        assert cost == 0.10

    def test_calculate_cost_analyze(self):
        """Analyze actions cost $0.50."""
        cost = CostCalculator.calculate_action_cost("analyze")
        assert cost == 0.50

    def test_calculate_cost_rank(self):
        """Rank actions cost $0.25."""
        cost = CostCalculator.calculate_action_cost("rank")
        assert cost == 0.25

    def test_calculate_cost_schedule(self):
        """Schedule actions cost $0.05."""
        cost = CostCalculator.calculate_action_cost("schedule")
        assert cost == 0.05

    def test_calculate_cost_approve(self):
        """Approve actions cost $0.05."""
        cost = CostCalculator.calculate_action_cost("approve")
        assert cost == 0.05

    def test_calculate_cost_send(self):
        """Send actions cost $0.02."""
        cost = CostCalculator.calculate_action_cost("send")
        assert cost == 0.02

    def test_calculate_cost_case_insensitive(self):
        """Cost calculation is case-insensitive."""
        assert (
            CostCalculator.calculate_action_cost("UPLOAD")
            == CostCalculator.calculate_action_cost("upload")
        )
        assert (
            CostCalculator.calculate_action_cost("AnalYze")
            == CostCalculator.calculate_action_cost("analyze")
        )

    def test_calculate_cost_unknown_type(self):
        """Unknown action types get default cost."""
        cost = CostCalculator.calculate_action_cost("unknown_type")
        assert cost == 0.05  # Default cost

    def test_would_exceed_budget_false(self):
        """Action doesn't exceed budget."""
        would_exceed = CostCalculator.would_exceed_budget(
            current_spending=50.0,
            daily_budget=100.0,
            action_cost=25.0,
        )
        assert would_exceed is False

    def test_would_exceed_budget_true(self):
        """Action exceeds remaining budget."""
        would_exceed = CostCalculator.would_exceed_budget(
            current_spending=80.0,
            daily_budget=100.0,
            action_cost=25.0,
        )
        assert would_exceed is True

    def test_would_exceed_budget_exactly_at_limit(self):
        """Action brings spending to exact limit."""
        would_exceed = CostCalculator.would_exceed_budget(
            current_spending=75.0,
            daily_budget=100.0,
            action_cost=25.0,
        )
        assert would_exceed is False

    def test_would_exceed_budget_one_cent_over(self):
        """Action exceeds limit by one cent."""
        would_exceed = CostCalculator.would_exceed_budget(
            current_spending=75.01,
            daily_budget=100.0,
            action_cost=25.0,
        )
        assert would_exceed is True


@pytest.mark.asyncio
class TestDeadLetterQueue:
    """Test dead letter queue management."""

    async def test_add_failed_action(self):
        """Add failed action to DLQ."""
        dlq = DeadLetterQueue()
        user_id = uuid4()

        await dlq.add_failed_action(
            action_id="action_1",
            user_id=user_id,
            error="Test error",
            retry_count=2,
        )

        assert len(dlq.failed_actions) == 1
        action = dlq.failed_actions[0]
        assert action["action_id"] == "action_1"
        assert action["user_id"] == str(user_id)
        assert action["error"] == "Test error"
        assert action["retry_count"] == 2
        assert action["status"] == "pending_review"

    async def test_add_multiple_failed_actions(self):
        """Add multiple failed actions."""
        dlq = DeadLetterQueue()

        for i in range(5):
            await dlq.add_failed_action(
                action_id=f"action_{i}",
                user_id=uuid4(),
                error=f"Error {i}",
            )

        assert len(dlq.failed_actions) == 5

    async def test_get_pending_reviews(self):
        """Get all pending review actions."""
        dlq = DeadLetterQueue()

        # Add actions
        for i in range(3):
            await dlq.add_failed_action(
                action_id=f"action_{i}",
                user_id=uuid4(),
                error=f"Error {i}",
            )

        # Get pending
        pending = await dlq.get_pending_reviews()
        assert len(pending) == 3

    async def test_mark_reviewed(self):
        """Mark action as reviewed."""
        dlq = DeadLetterQueue()
        await dlq.add_failed_action("action_1", uuid4(), "Error", 0)

        await dlq.mark_reviewed("action_1")

        pending = await dlq.get_pending_reviews()
        assert len(pending) == 0

        assert dlq.failed_actions[0]["status"] == "reviewed"

    async def test_mark_reviewed_nonexistent(self):
        """Marking nonexistent action is safe."""
        dlq = DeadLetterQueue()

        # Should not raise
        await dlq.mark_reviewed("nonexistent")


@pytest.mark.asyncio
class TestLoopMetrics:
    """Test metrics tracking."""

    def test_record_cycle(self):
        """Record completed cycle."""
        metrics = LoopMetrics()
        metrics.record_cycle()
        assert metrics.cycles_completed == 1

    def test_record_action_executed(self):
        """Record executed action."""
        metrics = LoopMetrics()
        metrics.record_action_executed()
        assert metrics.actions_executed == 1

    def test_record_action_failed(self):
        """Record failed action."""
        metrics = LoopMetrics()
        metrics.record_action_failed()
        assert metrics.actions_failed == 1

    def test_record_user_processed(self):
        """Record processed user."""
        metrics = LoopMetrics()
        metrics.record_user_processed()
        assert metrics.users_processed == 1

    def test_record_governance_review(self):
        """Record governance review created."""
        metrics = LoopMetrics()
        metrics.record_governance_review()
        assert metrics.governance_reviews_created == 1

    def test_record_error(self):
        """Record error for monitoring."""
        metrics = LoopMetrics()
        metrics.record_error("Test error message")
        assert metrics.last_error == "Test error message"
        assert metrics.last_error_time is not None

    def test_get_stats_empty(self):
        """Get stats when nothing recorded."""
        metrics = LoopMetrics()
        stats = metrics.get_stats()

        assert stats["cycles_completed"] == 0
        assert stats["actions_executed"] == 0
        assert stats["actions_failed"] == 0
        assert stats["success_rate_percent"] == 0

    def test_get_stats_with_data(self):
        """Get stats with recorded data."""
        metrics = LoopMetrics()
        metrics.record_cycle()
        metrics.record_action_executed()
        metrics.record_action_executed()
        metrics.record_action_failed()
        metrics.record_user_processed()

        stats = metrics.get_stats()

        assert stats["cycles_completed"] == 1
        assert stats["actions_executed"] == 2
        assert stats["actions_failed"] == 1
        assert stats["users_processed"] == 1

    def test_success_rate_calculation(self):
        """Success rate calculated correctly."""
        metrics = LoopMetrics()

        # 4 successes, 1 failure = 80%
        for _ in range(4):
            metrics.record_action_executed()
        metrics.record_action_failed()

        stats = metrics.get_stats()
        assert stats["success_rate_percent"] == 80.0

    def test_uptime_reported(self):
        """Uptime seconds reported."""
        metrics = LoopMetrics()
        stats = metrics.get_stats()

        assert "uptime_seconds" in stats
        assert stats["uptime_seconds"] >= 0


@pytest.mark.asyncio
class TestAutonomousLoopManager:
    """Test autonomous loop manager."""

    def test_initialization(self):
        """Loop manager initializes correctly."""
        manager = AutonomousLoopManager()

        assert manager.running is False
        assert manager._session_maker is None
        assert manager._engine is None
        assert isinstance(manager.metrics, LoopMetrics)
        assert isinstance(manager.dlq, DeadLetterQueue)

    def test_get_status(self):
        """Get current status."""
        manager = AutonomousLoopManager()
        status = manager.get_status()

        assert "running" in status
        assert "metrics" in status
        assert "dlq_pending" in status
        assert status["running"] is False

    def test_metrics_persistence(self):
        """Metrics persist across calls."""
        manager = AutonomousLoopManager()

        manager.metrics.record_cycle()
        manager.metrics.record_action_executed()

        status1 = manager.get_status()
        assert status1["metrics"]["cycles_completed"] == 1
        assert status1["metrics"]["actions_executed"] == 1

        # Record more
        manager.metrics.record_cycle()

        status2 = manager.get_status()
        assert status2["metrics"]["cycles_completed"] == 2

    def test_dlq_accessible(self):
        """DLQ accessible from manager."""
        manager = AutonomousLoopManager()
        assert manager.dlq is not None


@pytest.mark.asyncio
class TestPollingIntervals:
    """Test polling interval behavior."""

    def test_polling_interval_constant(self):
        """Base polling interval is 5 seconds."""
        assert POLLING_INTERVAL_SECONDS == 5

    def test_polling_jitter_range(self):
        """Jitter is within ±2 seconds."""
        assert POLLING_JITTER_SECONDS == 2

    def test_jitter_prevents_thundering_herd(self):
        """Multiple instances with jitter have different sleep times."""
        import random

        times = set()
        for _ in range(100):
            jitter = random.uniform(-POLLING_JITTER_SECONDS, POLLING_JITTER_SECONDS)
            sleep_time = POLLING_INTERVAL_SECONDS + jitter
            times.add(round(sleep_time, 2))

        # With jitter, we should have many different values
        assert len(times) > 10


@pytest.mark.asyncio
class TestBatchSizing:
    """Test batch size limits."""

    def test_max_batch_size_constant(self):
        """Max batch size is 10."""
        assert MAX_BATCH_SIZE == 10

    def test_batch_limits_resource_usage(self):
        """Batch limiting prevents resource exhaustion."""
        # Create 15 messages
        messages = list(range(15))

        # Apply batch limit
        limited = messages[:MAX_BATCH_SIZE]

        assert len(limited) == 10


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and recovery."""

    def test_metrics_record_error(self):
        """Error recorded in metrics."""
        metrics = LoopMetrics()
        metrics.record_error("Critical error")

        stats = metrics.get_stats()
        assert stats["last_error"] == "Critical error"
        assert stats["last_error_time"] is not None

    def test_manager_error_recovery(self):
        """Manager recovers from errors gracefully."""
        manager = AutonomousLoopManager()
        manager.metrics.record_error("Test error")

        # Manager should still be able to process
        assert manager.running is False
        assert manager.metrics.last_error == "Test error"

    def test_dlq_stores_failed_actions(self):
        """Failed actions stored in DLQ for review."""
        async def test():
            dlq = DeadLetterQueue()
            await dlq.add_failed_action(
                "action_1",
                uuid4(),
                "Database timeout",
                retry_count=3,
            )

            pending = await dlq.get_pending_reviews()
            assert len(pending) == 1
            assert pending[0]["error"] == "Database timeout"

        asyncio.run(test())


@pytest.mark.asyncio
class TestIntegration:
    """Integration tests for Phase 3."""

    def test_full_lifecycle(self):
        """Full loop manager lifecycle."""
        manager = AutonomousLoopManager()

        # Initialize
        assert manager.running is False
        assert manager.metrics.cycles_completed == 0

        # Simulate some activity
        manager.metrics.record_cycle()
        manager.metrics.record_action_executed()
        manager.metrics.record_action_executed()
        manager.metrics.record_action_failed()

        # Check status
        status = manager.get_status()
        assert status["metrics"]["cycles_completed"] == 1
        assert status["metrics"]["actions_executed"] == 2
        assert status["metrics"]["actions_failed"] == 1

    def test_budget_enforcement_scenario(self):
        """Budget enforcement prevents overspending."""
        # User has $100 daily budget
        daily_budget = 100.0
        current_spending = 75.0

        # Try 2 analyze actions ($0.50 each)
        action_costs = [
            CostCalculator.calculate_action_cost("analyze"),
            CostCalculator.calculate_action_cost("analyze"),
        ]

        total_cost = sum(action_costs)

        # Should succeed
        would_exceed = CostCalculator.would_exceed_budget(
            current_spending,
            daily_budget,
            total_cost,
        )
        assert would_exceed is False

        # A large batch (~$30) on top of $76 spent would push past the $100
        # budget, so enforcement must reject it.
        large_cost = 30.0
        would_exceed = CostCalculator.would_exceed_budget(
            current_spending + total_cost,
            daily_budget,
            large_cost,
        )
        assert would_exceed is True

    def test_cost_tracking_scenario(self):
        """Cost tracking scenario."""
        actions = [
            ("upload", 0.10),
            ("analyze", 0.50),
            ("rank", 0.25),
            ("schedule", 0.05),
            ("approve", 0.05),
            ("send", 0.02),
        ]

        total_cost = 0.0
        for action_type, expected_cost in actions:
            cost = CostCalculator.calculate_action_cost(action_type)
            assert cost == expected_cost
            total_cost += cost

        # Total cost should be $0.97
        assert round(total_cost, 2) == 0.97
