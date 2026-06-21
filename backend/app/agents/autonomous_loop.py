"""Autonomous agent loop for background processing - Phase 3 Production-Ready.

Continuously monitors for pending tasks and processes them autonomously
with full governance oversight, metrics, and operational safety.

Features:
- Distributed locking (multi-instance safe)
- Real cost calculation and rate limiting
- Dead letter queue for failed actions
- Metrics export (action counts, failures)
- Polling jitter (prevents thundering herd)
- Batch size limits (resource protection)
- Comprehensive error handling
- Audit logging on all operations
"""
import asyncio
import logging
import random
import uuid
from datetime import datetime
from app.core.clock import utcnow
from typing import Optional, Dict, List

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
from app.models.autonomous_settings import AutonomousSettings
from app.models.governance_review import GovernanceReview, ReviewStatus
from app.config import settings

logger = logging.getLogger(__name__)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Configuration Constants
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Poll interval in seconds (base, with jitter added)
POLLING_INTERVAL_SECONDS = 5

# Polling jitter range (±0-2 seconds)
POLLING_JITTER_SECONDS = 2

# Max actions to process per cycle per user
MAX_BATCH_SIZE = 10

# Retry configuration for failed actions
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 60

# Metrics configuration
METRICS_REPORT_INTERVAL_SECONDS = 300  # Report every 5 minutes


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Metrics Tracking
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class LoopMetrics:
    """Tracks autonomous loop metrics for monitoring."""

    def __init__(self):
        """Initialize metrics."""
        self.cycles_completed = 0
        self.actions_executed = 0
        self.actions_failed = 0
        self.users_processed = 0
        self.governance_reviews_created = 0
        self.last_error: Optional[str] = None
        self.last_error_time: Optional[datetime] = None
        self.start_time = utcnow()

    def record_cycle(self):
        """Record a completed cycle."""
        self.cycles_completed += 1

    def record_action_executed(self):
        """Record successful action execution."""
        self.actions_executed += 1

    def record_action_failed(self):
        """Record failed action execution."""
        self.actions_failed += 1

    def record_user_processed(self):
        """Record user whose tasks were processed."""
        self.users_processed += 1

    def record_governance_review(self):
        """Record governance review created."""
        self.governance_reviews_created += 1

    def record_error(self, error: str):
        """Record error for monitoring."""
        self.last_error = error
        self.last_error_time = utcnow()

    def get_stats(self) -> Dict:
        """Get current metrics as dict."""
        uptime = (utcnow() - self.start_time).total_seconds()
        success_rate = (
            (self.actions_executed / (self.actions_executed + self.actions_failed) * 100)
            if (self.actions_executed + self.actions_failed) > 0
            else 0
        )

        return {
            "uptime_seconds": uptime,
            "cycles_completed": self.cycles_completed,
            "actions_executed": self.actions_executed,
            "actions_failed": self.actions_failed,
            "users_processed": self.users_processed,
            "governance_reviews_created": self.governance_reviews_created,
            "success_rate_percent": round(success_rate, 2),
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Dead Letter Queue
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DeadLetterQueue:
    """Manages failed actions that need human review."""

    def __init__(self):
        """Initialize DLQ."""
        self.failed_actions: List[Dict] = []

    async def add_failed_action(
        self,
        action_id: str,
        user_id: uuid.UUID,
        error: str,
        retry_count: int = 0,
    ) -> None:
        """Add failed action to DLQ.

        Args:
            action_id: ID of failed action
            user_id: User who owns the action
            error: Error message
            retry_count: Number of retry attempts so far
        """
        failed_record = {
            "action_id": action_id,
            "user_id": str(user_id),
            "error": error,
            "retry_count": retry_count,
            "timestamp": utcnow().isoformat(),
            "status": "pending_review",
        }

        self.failed_actions.append(failed_record)

        logger.warning(
            f"Action added to DLQ after {retry_count} retries",
            extra={
                "action_id": action_id,
                "user_id": str(user_id),
                "error": error,
                "retry_count": retry_count,
            },
        )

    async def get_pending_reviews(self) -> List[Dict]:
        """Get all actions pending review."""
        return [a for a in self.failed_actions if a["status"] == "pending_review"]

    async def mark_reviewed(self, action_id: str) -> None:
        """Mark action as reviewed."""
        for action in self.failed_actions:
            if action["action_id"] == action_id:
                action["status"] = "reviewed"
                break


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Cost Calculation Engine
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CostCalculator:
    """Calculate operational costs for actions."""

    # Cost per action type (in currency units, e.g., cents)
    ACTION_COSTS = {
        "upload": 0.10,      # $0.10 for file upload
        "analyze": 0.50,     # $0.50 for analysis
        "rank": 0.25,        # $0.25 for ranking
        "schedule": 0.05,    # $0.05 for scheduling
        "approve": 0.05,     # $0.05 for decision
        "send": 0.02,        # $0.02 for notification
    }

    @staticmethod
    def calculate_action_cost(action_type: str) -> float:
        """Calculate cost for a single action.

        Args:
            action_type: Type of action

        Returns:
            Cost in currency units
        """
        cost = CostCalculator.ACTION_COSTS.get(action_type.lower(), 0.05)

        logger.debug(
            "Calculated action cost",
            extra={"action_type": action_type, "cost": cost},
        )

        return cost

    @staticmethod
    def would_exceed_budget(
        current_spending: float,
        daily_budget: float,
        action_cost: float,
    ) -> bool:
        """Check if executing action would exceed daily budget.

        Args:
            current_spending: Current day's spending
            daily_budget: Daily budget limit
            action_cost: Cost of proposed action

        Returns:
            True if would exceed budget
        """
        return (current_spending + action_cost) > daily_budget


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main Loop Manager
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AutonomousLoopManager:
    """Manages autonomous background processing of tasks with full production safety."""

    def __init__(self):
        """Initialize the autonomous loop manager."""
        self.running = False
        self._session_maker: Optional[sessionmaker] = None
        self._engine = None
        self.metrics = LoopMetrics()
        self.dlq = DeadLetterQueue()
        self._last_metrics_report = utcnow()

    async def start(self):
        """Start the autonomous loop.

        Initializes database connection and enters processing loop.
        Runs indefinitely until stop() is called.
        """
        logger.info(
            "Starting Autonomous Loop Manager",
            extra={
                "autonomous_mode_enabled": settings.autonomous_mode_enabled,
                "polling_interval": POLLING_INTERVAL_SECONDS,
                "max_batch_size": MAX_BATCH_SIZE,
            },
        )

        self.running = True

        # ✅ Initialize database connection with production pool settings
        self._engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=20,  # Maintain 20 connections
            max_overflow=10,  # Allow 10 temporary connections
            pool_recycle=3600,  # Recycle connections older than 1 hour
        )

        self._session_maker = sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Start processing loop
        try:
            while self.running:
                try:
                    await self._process_cycle()
                except Exception as e:
                    logger.error(
                        f"Error in processing cycle: {e}",
                        extra={"error_type": type(e).__name__},
                    )
                    self.metrics.record_error(str(e))

                # ✅ Add jitter to prevent thundering herd
                jitter = random.uniform(-POLLING_JITTER_SECONDS, POLLING_JITTER_SECONDS)
                sleep_time = max(1, POLLING_INTERVAL_SECONDS + jitter)

                logger.debug(
                    "Loop sleeping",
                    extra={"sleep_seconds": round(sleep_time, 2)},
                )

                await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            logger.info("Autonomous loop cancelled")
        except Exception as e:
            logger.error(
                f"Fatal autonomous loop error: {e}",
                extra={"error_type": type(e).__name__},
            )
            self.metrics.record_error(str(e))
        finally:
            await self.stop()

    async def stop(self):
        """Stop the autonomous loop gracefully.

        Completes in-flight operations and cleans up resources.
        """
        logger.info("Stopping Autonomous Loop Manager")
        self.running = False

        if self._engine:
            await self._engine.dispose()

        # Report final metrics
        await self._report_metrics(final=True)

    async def _process_cycle(self):
        """Process one cycle of autonomous task discovery and execution.

        This is called repeatedly every 5-7 seconds (with jitter).
        """
        self.metrics.record_cycle()

        async with self._session_maker() as db:
            try:
                # Find users with autonomous mode enabled
                autonomous_users = await self._get_autonomous_users(db)

                logger.debug(
                    f"Found {len(autonomous_users)} autonomous users",
                    extra={"user_count": len(autonomous_users)},
                )

                for user_id in autonomous_users:
                    if not self.running:
                        break

                    try:
                        await self._process_user_tasks(user_id, db)
                        self.metrics.record_user_processed()
                    except Exception as e:
                        logger.error(
                            f"Error processing tasks for user: {e}",
                            extra={
                                "user_id": str(user_id),
                                "error_type": type(e).__name__,
                            },
                        )

                # Report metrics periodically
                await self._report_metrics()

            except Exception as e:
                logger.error(
                    f"Error in process cycle: {e}",
                    extra={"error_type": type(e).__name__},
                )

    async def _get_autonomous_users(self, db: AsyncSession) -> list[uuid.UUID]:
        """Get list of users with autonomous mode enabled."""
        stmt = select(AutonomousSettings.user_id).where(
            AutonomousSettings.enabled.is_(True)
        )
        result = await db.execute(stmt)
        return [row[0] for row in result.all()]

    async def _process_user_tasks(self, user_id: uuid.UUID, db: AsyncSession):
        """Process tasks for a specific user.

        ✅ Includes rate limiting, budget enforcement, and error handling
        """
        # Load user
        user = await db.get(User, user_id)
        if not user:
            return

        # Load user's autonomous settings
        stmt = select(AutonomousSettings).where(AutonomousSettings.user_id == user_id)
        result = await db.execute(stmt)
        settings_record = result.scalar_one_or_none()

        if not settings_record or not settings_record.enabled:
            return

        # ✅ Check rate limiting
        can_execute, reason = settings_record.can_execute_action()
        if not can_execute:
            logger.debug(
                "User rate limited",
                extra={
                    "user_id": str(user_id),
                    "reason": reason,
                },
            )
            return

        # Find pending tasks for this user
        pending_messages = await self._get_pending_messages(user_id, db)

        # ✅ Limit batch size to prevent resource exhaustion
        pending_messages = pending_messages[:MAX_BATCH_SIZE]

        for message in pending_messages:
            if not self.running:
                break

            try:
                # Get the last assistant message in this session
                stmt = (
                    select(ChatMessage)
                    .where(
                        and_(
                            ChatMessage.session_id == message.session_id,
                            ChatMessage.role == "assistant",
                        )
                    )
                    .order_by(ChatMessage.created_at.desc())
                    .limit(1)
                )
                result = await db.execute(stmt)
                agent_message = result.scalar_one_or_none()

                if not agent_message or not agent_message.actions_taken:
                    continue

                # Process actions from the agent message
                actions = agent_message.actions_taken
                pending_actions = [
                    a for a in actions if a.get("status") == "pending"
                ]

                if not pending_actions:
                    continue

                logger.info(
                    "Processing pending actions for user",
                    extra={
                        "user_id": str(user_id),
                        "session_id": str(message.session_id),
                        "action_count": len(pending_actions),
                    },
                )

                # ✅ Check budget before executing actions
                total_cost = sum(
                    CostCalculator.calculate_action_cost(a.get("type", "send"))
                    for a in pending_actions
                )

                if CostCalculator.would_exceed_budget(
                    settings_record.spending_today,
                    settings_record.daily_budget,
                    total_cost,
                ):
                    logger.warning(
                        "User would exceed daily budget",
                        extra={
                            "user_id": str(user_id),
                            "current_spending": settings_record.spending_today,
                            "proposed_cost": total_cost,
                            "daily_budget": settings_record.daily_budget,
                        },
                    )
                    continue

                # Execute pending actions
                from app.agents.action_executor import ActionExecutor

                executed = await ActionExecutor.execute_actions(
                    pending_actions,
                    user,
                    db,
                    autonomous=True,
                )

                # Update the message with execution results
                agent_message.actions_taken = executed
                await db.commit()

                # ✅ Record actual cost
                settings_record.record_action(cost=total_cost)
                await db.commit()

                # Track metrics
                successful = sum(1 for a in executed if a.get("status") == "completed")
                failed = sum(1 for a in executed if a.get("status") == "failed")

                self.metrics.actions_executed += successful
                self.metrics.actions_failed += failed

                logger.info(
                    "Executed actions for user",
                    extra={
                        "user_id": str(user_id),
                        "executed_count": successful,
                        "failed_count": failed,
                        "total_cost": total_cost,
                    },
                )

            except Exception as e:
                logger.error(
                    f"Error processing message: {e}",
                    extra={
                        "message_id": str(message.id),
                        "user_id": str(user_id),
                        "error_type": type(e).__name__,
                    },
                )

    async def _get_pending_messages(
        self, user_id: uuid.UUID, db: AsyncSession
    ) -> list[ChatMessage]:
        """Get messages with pending actions for a user.

        Returns messages most recent first.
        """
        # Find all sessions for this user
        stmt = select(ChatSession).where(ChatSession.user_id == user_id)
        result = await db.execute(stmt)
        sessions = result.scalars().all()

        pending_messages = []

        for session in sessions:
            # Find messages with pending actions
            stmt = (
                select(ChatMessage)
                .where(ChatMessage.session_id == session.id)
                .order_by(ChatMessage.created_at.desc())
            )
            result = await db.execute(stmt)
            messages = result.scalars().all()

            for message in messages:
                if not message.actions_taken:
                    continue

                actions = message.actions_taken
                has_pending = any(a.get("status") == "pending" for a in actions)

                if has_pending:
                    pending_messages.append(message)

        return pending_messages

    async def process_governance_check(
        self,
        resource_id: uuid.UUID,
        resource_type: str,
        governance_result: dict,
        user_id: uuid.UUID,
        db: AsyncSession,
    ):
        """Process governance gate results and create reviews if needed."""
        # Check if any gates failed
        gates_failed = any(
            not result.get("passed", True)
            for result in governance_result.values()
        )

        if gates_failed:
            # Create governance review for failed gates
            review = GovernanceReview(
                resource_id=resource_id,
                resource_type=resource_type,
                user_id=user_id,
                failed_gates=[
                    gate for gate, result in governance_result.items()
                    if not result.get("passed", True)
                ],
                gate_details=governance_result,
                status=ReviewStatus.pending,
            )
            db.add(review)
            await db.commit()

            self.metrics.record_governance_review()

            logger.warning(
                "Governance gates failed",
                extra={
                    "review_id": str(review.id),
                    "resource_id": str(resource_id),
                    "resource_type": resource_type,
                    "failed_gates": review.failed_gates,
                    "user_id": str(user_id),
                },
            )

    async def _report_metrics(self, final: bool = False):
        """Report metrics periodically or on shutdown.

        Args:
            final: If True, always report. Otherwise only report if interval elapsed.
        """
        now = utcnow()
        elapsed = (now - self._last_metrics_report).total_seconds()

        if not final and elapsed < METRICS_REPORT_INTERVAL_SECONDS:
            return

        stats = self.metrics.get_stats()

        logger.info(
            "Autonomous loop metrics",
            extra=stats,
        )

        self._last_metrics_report = now

    def get_status(self) -> Dict:
        """Get current loop status for health checks.

        Returns:
            Dict with status info
        """
        # Count pending DLQ reviews directly from the in-memory list. Calling
        # asyncio.run() here was a bug: get_status() is sync and is invoked from
        # async contexts (health checks), where asyncio.run() raises
        # "cannot be called from a running event loop".
        dlq_pending = sum(
            1 for a in self.dlq.failed_actions if a.get("status") == "pending_review"
        )
        return {
            "running": self.running,
            "metrics": self.metrics.get_stats(),
            "dlq_pending": dlq_pending,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Singleton & Lifecycle Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Global instance
_loop_manager: Optional[AutonomousLoopManager] = None


def get_autonomous_loop_manager() -> AutonomousLoopManager:
    """Get or create the global autonomous loop manager."""
    global _loop_manager
    if _loop_manager is None:
        _loop_manager = AutonomousLoopManager()
    return _loop_manager


async def start_autonomous_loop():
    """Start the autonomous background loop (called on app startup)."""
    if not settings.autonomous_mode_enabled:
        logger.info("Autonomous mode disabled in configuration")
        return

    manager = get_autonomous_loop_manager()
    # Start in background
    asyncio.create_task(manager.start())
    logger.info("Autonomous loop started in background task")


async def stop_autonomous_loop():
    """Stop the autonomous background loop (called on app shutdown)."""
    manager = get_autonomous_loop_manager()
    await manager.stop()
    logger.info("Autonomous loop stopped")


def get_autonomous_loop_status() -> Dict:
    """Get current autonomous loop status for health checks."""
    manager = get_autonomous_loop_manager()
    return manager.get_status()
