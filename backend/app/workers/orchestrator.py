"""
TrueMatch AI-Native Orchestrator - Phase A+B+C+D Integration

Orchestrates all autonomy, governance, provenance, and learning components:
- File system monitoring (Phase A)
- Email ingestion (Phase A)
- Assessment queueing (Phase A)
- Decision engine (Phase A)
- Governance gates (Phase B)
- Notifications (Phase A)
- Provenance tracking (Phase C)
- Learning loop integration (Phase D)

This is the central hub that runs on application startup.
"""
import asyncio
import logging
from typing import Any, Callable, Optional

from app.config import settings
from app.workers.assessment_queue import AssessmentProcessor, AssessmentQueue, get_assessment_queue, get_assessment_processor
from app.workers.decision_engine import DecisionThresholds, configure_decision_thresholds, get_decision_engine
from app.workers.email_ingestion import get_email_ingestor, start_email_ingestion, stop_email_ingestion
from app.workers.file_ingestion import get_file_monitor, start_file_monitoring, stop_file_monitoring
from app.workers.governance_gates import get_governance_validator
from app.workers.notification_service import get_notification_dispatcher
from app.workers.provenance_learning_orchestrator import (
    get_provenance_learning_orchestrator,
)

logger = logging.getLogger(__name__)


class TrueMatchOrchestrator:
    """
    Central orchestrator for AI-native autonomous operations.

    Manages lifecycle of all Phase A+B+C+D components:
    1. File system monitor (folder drop) [Phase A]
    2. Email ingestor (IMAP polling) [Phase A]
    3. Assessment queue (priority job queue) [Phase A]
    4. Assessment processor (worker pool) [Phase A]
    5. Governance gates (mandatory validation) [Phase B]
    6. Decision engine (auto-approve/reject logic) [Phase A]
    7. Notification dispatcher (Slack/email/in-app) [Phase A]
    8. Provenance tracker (SHA-256 hashing, audit trail) [Phase C]
    9. Learning loop (feedback processing, weight updates) [Phase D]

    Flow:
    CV/JD arrives → File/Email ingestion → Assessment queue → Processor
                                                                  ↓
                                                        Assessment execution
                                                                  ↓
                                                        Governance gates ← [CANNOT BYPASS]
                                                                  ↓
                                                        Decision engine
                                                                  ↓
                                                        Notifications (Slack/email)
                                                                  ↓
                                                  Create Provenance Record (C)
                                                                  ↓
                                                  Process Training Feedback (D)
    """

    def __init__(
        self,
        assessment_executor: Optional[Callable] = None,
        governance_validator: Optional[Callable] = None,
        decision_engine_executor: Optional[Callable] = None,
        notification_dispatcher: Optional[Callable] = None,
    ):
        self.is_running = False

        # Initialize Phase A+B components
        self.file_monitor = get_file_monitor()
        self.email_ingestor = get_email_ingestor()
        self.assessment_queue = get_assessment_queue()
        self.assessment_processor = get_assessment_processor()
        self.governance_validator = get_governance_validator()
        self.notification_dispatcher = get_notification_dispatcher()
        self.decision_engine = get_decision_engine()

        # Initialize Phase C+D components
        self.provenance_learning_orchestrator = get_provenance_learning_orchestrator()

        # Configure assessment processor with business logic
        if assessment_executor:
            self.assessment_processor.assessment_executor = assessment_executor
        if governance_validator:
            self.assessment_processor.governance_validator = governance_validator
        if decision_engine_executor:
            self.assessment_processor.decision_engine = decision_engine_executor
        if notification_dispatcher:
            self.assessment_processor.notification_dispatcher = notification_dispatcher

        # Wire provenance+learning orchestrator to assessment processor
        self.assessment_processor.provenance_learning = self.provenance_learning_orchestrator

        logger.info("TrueMatch Orchestrator initialized (Phase A+B+C+D)")

    def configure_thresholds(self):
        """Configure decision thresholds from settings."""
        thresholds = DecisionThresholds(
            auto_approve_score=settings.decision_auto_approve_threshold,
            review_score_min=settings.decision_review_threshold,
            auto_reject_score=settings.decision_auto_reject_threshold,
        )
        configure_decision_thresholds(thresholds)
        logger.info(f"Decision thresholds configured: approve={thresholds.auto_approve_score}")

    async def start(self):
        """Start all autonomous components (Phase A+B+C+D)."""
        if self.is_running:
            logger.warning("Orchestrator already running")
            return

        self.is_running = True
        logger.info("═" * 80)
        logger.info("TRUEMATCH AI-NATIVE ORCHESTRATOR STARTING")
        logger.info("═" * 80)

        # Configure thresholds
        self.configure_thresholds()

        # Start file system monitor
        logger.info("Starting file system monitor...")
        self.file_monitor.start()
        logger.info(f"  ✓ File monitor active: {self.file_monitor.inbox_path}")

        # Start email ingestor (if enabled)
        if settings.email_ingestion_enabled:
            logger.info("Starting email ingestor...")
            try:
                await start_email_ingestion()
                logger.info(f"  ✓ Email ingestor active: {settings.email_imap_host}")
            except Exception as e:
                logger.error(f"  ✗ Email ingestor failed to start: {e}")

        # Start assessment processor (worker pool)
        logger.info(f"Starting assessment processor ({settings.max_concurrent_assessments} workers)...")
        try:
            asyncio.create_task(self.assessment_processor.start())
            logger.info(f"  ✓ Assessment processor active")
        except Exception as e:
            logger.error(f"  ✗ Assessment processor failed to start: {e}")

        # Schedule learning recalibration (Phase D)
        if getattr(settings, "learning_enable", True):
            logger.info("Scheduling learning recalibration...")
            try:
                recalibration_interval = getattr(settings, "recalibration_interval_hours", 24)
                await self.provenance_learning_orchestrator.schedule_learning_recalibration(
                    interval_hours=recalibration_interval
                )
                logger.info(f"  ✓ Learning recalibration scheduled (every {recalibration_interval}h)")
            except Exception as e:
                logger.error(f"  ✗ Learning recalibration scheduling failed: {e}")

        logger.info("═" * 80)
        logger.info("TRUEMATCH AI-NATIVE ORCHESTRATOR READY")
        logger.info("═" * 80)
        logger.info("")
        logger.info("Phase A: Autonomy Layer")
        logger.info("  ✓ File system monitoring (folder drop)")
        logger.info("  ✓ Email ingestion (IMAP polling)" if settings.email_ingestion_enabled else "  ○ Email ingestion (disabled)")
        logger.info("  ✓ Assessment queue (priority-based)")
        logger.info("  ✓ Assessment processor (concurrent workers)")
        logger.info("  ✓ Notifications (Slack/email/in-app)")
        logger.info("")
        logger.info("Phase B: Governance Layer")
        logger.info(f"  ✓ Coherence gate (mandatory)")
        logger.info(f"  ✓ Consistency gate (mandatory)")
        logger.info(f"  ✓ Fidelity gate (mandatory)")
        logger.info(f"  ✓ Bias detection gate (mandatory)")
        logger.info("")
        logger.info("Phase C: Provenance & Reproducibility")
        logger.info("  ✓ SHA-256 input hashing")
        logger.info("  ✓ Model version tracking")
        logger.info("  ✓ Immutable audit trail")
        logger.info("  ✓ Reproducibility verification")
        logger.info("")
        logger.info("Phase D: Learning Loop Integration")
        logger.info("  ✓ Capability weight updates")
        logger.info("  ✓ Credential equivalency learning")
        logger.info("  ✓ Automatic recalibration")
        logger.info("  ✓ Batch re-scoring")
        logger.info("")
        logger.info(f"Decision Thresholds:")
        logger.info(f"  • Auto-Approve: {settings.decision_auto_approve_threshold}")
        logger.info(f"  • Review: {settings.decision_review_threshold}")
        logger.info(f"  • Auto-Reject: {settings.decision_auto_reject_threshold}")
        logger.info("")

    def stop(self):
        """Stop all autonomous components."""
        if not self.is_running:
            return

        self.is_running = False

        logger.info("═" * 80)
        logger.info("TRUEMATCH AI-NATIVE ORCHESTRATOR STOPPING")
        logger.info("═" * 80)

        # Stop file monitor
        logger.info("Stopping file system monitor...")
        self.file_monitor.stop()
        logger.info("  ✓ File monitor stopped")

        # Stop email ingestor
        if settings.email_ingestion_enabled:
            logger.info("Stopping email ingestor...")
            stop_email_ingestion()
            logger.info("  ✓ Email ingestor stopped")

        # Stop assessment processor
        logger.info("Stopping assessment processor...")
        self.assessment_processor.stop()
        logger.info("  ✓ Assessment processor stopped")

        logger.info("═" * 80)
        logger.info("TRUEMATCH AI-NATIVE ORCHESTRATOR STOPPED")
        logger.info("═" * 80)

    def get_status(self) -> dict[str, Any]:
        """Get current system status (Phase A+B+C+D)."""
        queue_stats = self.assessment_queue.get_queue_stats()
        provenance_learning_status = self.provenance_learning_orchestrator.get_system_state()

        return {
            "orchestrator_running": self.is_running,
            "phase_a": {
                "file_monitor": {
                    "running": self.file_monitor.is_running,
                    "inbox_path": str(self.file_monitor.inbox_path),
                },
                "email_ingestor": {
                    "enabled": settings.email_ingestion_enabled,
                    "running": getattr(self.email_ingestor, "is_running", False),
                },
                "assessment_queue": queue_stats,
            },
            "phase_b": {
                "governance_gates": {
                    "coherence": settings.governance_enable_coherence_gate,
                    "consistency": settings.governance_enable_consistency_gate,
                    "fidelity": settings.governance_enable_fidelity_gate,
                    "bias": settings.governance_enable_bias_gate,
                },
                "decision_thresholds": {
                    "auto_approve": settings.decision_auto_approve_threshold,
                    "review": settings.decision_review_threshold,
                    "auto_reject": settings.decision_auto_reject_threshold,
                },
            },
            "phase_c": {
                "provenance": provenance_learning_status.get("provenance", {}),
                "audit": provenance_learning_status.get("audit", {}),
            },
            "phase_d": {
                "learning": provenance_learning_status.get("learning", {}),
            },
        }


# Global orchestrator instance
_orchestrator: Optional[TrueMatchOrchestrator] = None


def get_orchestrator(
    assessment_executor: Optional[Callable] = None,
    governance_validator: Optional[Callable] = None,
    decision_engine_executor: Optional[Callable] = None,
    notification_dispatcher: Optional[Callable] = None,
) -> TrueMatchOrchestrator:
    """Get or create orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TrueMatchOrchestrator(
            assessment_executor=assessment_executor,
            governance_validator=governance_validator,
            decision_engine_executor=decision_engine_executor,
            notification_dispatcher=notification_dispatcher,
        )
    return _orchestrator


async def start_orchestrator(
    assessment_executor: Optional[Callable] = None,
    governance_validator: Optional[Callable] = None,
    decision_engine_executor: Optional[Callable] = None,
    notification_dispatcher: Optional[Callable] = None,
):
    """Start orchestrator on application startup."""
    orchestrator = get_orchestrator(
        assessment_executor=assessment_executor,
        governance_validator=governance_validator,
        decision_engine_executor=decision_engine_executor,
        notification_dispatcher=notification_dispatcher,
    )
    await orchestrator.start()


def stop_orchestrator():
    """Stop orchestrator on application shutdown."""
    orchestrator = get_orchestrator()
    orchestrator.stop()
