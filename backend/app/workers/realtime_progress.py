"""
Real-Time Progress Tracking - Phase E: WebSocket Integration

Provides real-time updates of assessment processing, governance gates,
and learning recalibration progress via WebSocket.

Enables:
- Live progress notifications (percentage complete)
- Gate validation status updates
- Decision reasoning in real-time
- Learning recalibration progress
- Queue statistics updates
"""
import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


class ProgressEventType(str, Enum):
    """Real-time progress event types."""

    ASSESSMENT_STARTED = "assessment_started"
    ASSESSMENT_PROCESSING = "assessment_processing"
    GATES_VALIDATING = "gates_validating"
    GATES_RESULT = "gates_result"
    DECISION_PENDING = "decision_pending"
    DECISION_MADE = "decision_made"
    NOTIFYING = "notifying"
    NOTIFIED = "notified"
    PROVENANCE_CREATING = "provenance_creating"
    PROVENANCE_CREATED = "provenance_created"
    LEARNING_PROCESSING = "learning_processing"
    LEARNING_PROCESSED = "learning_processed"
    ASSESSMENT_COMPLETED = "assessment_completed"
    ASSESSMENT_FAILED = "assessment_failed"
    RECALIBRATION_STARTED = "recalibration_started"
    RECALIBRATION_TESTING = "recalibration_testing"
    RECALIBRATION_COMPLETED = "recalibration_completed"
    QUEUE_UPDATE = "queue_update"


@dataclass
class ProgressEvent:
    """Single real-time progress event."""

    event_id: str
    event_type: ProgressEventType
    assessment_id: Optional[str] = None
    timestamp: str = None
    progress_percent: int = 0  # 0-100
    status: str = ""  # Description of current status
    details: Dict[str, Any] = None  # Event-specific details
    error: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
        if self.details is None:
            self.details = {}

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["event_type"] = self.event_type.value
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class ProgressTracker:
    """
    Tracks real-time progress of assessments and learning.

    Broadcasts events to connected WebSocket clients.
    """

    def __init__(self):
        self.subscribers: Dict[str, Set[Callable]] = {}  # assessment_id -> callbacks
        self.global_subscribers: Set[Callable] = set()  # All assessments
        self.event_history: Dict[str, List[ProgressEvent]] = {}  # assessment_id -> events
        self.current_progress: Dict[str, Dict[str, Any]] = {}  # assessment_id -> progress

    def subscribe_to_assessment(
        self, assessment_id: str, callback: Callable
    ) -> str:
        """
        Subscribe to progress updates for specific assessment.

        Callback will be called with ProgressEvent whenever progress updates.
        Returns subscription_id.
        """
        if assessment_id not in self.subscribers:
            self.subscribers[assessment_id] = set()
            self.event_history[assessment_id] = []
            self.current_progress[assessment_id] = {
                "assessment_id": assessment_id,
                "started_at": datetime.utcnow().isoformat(),
                "progress_percent": 0,
                "current_stage": "pending",
            }

        self.subscribers[assessment_id].add(callback)
        logger.info(f"Subscribed to assessment progress: {assessment_id}")
        return f"sub_{assessment_id}_{len(self.subscribers[assessment_id])}"

    def subscribe_global(self, callback: Callable) -> str:
        """Subscribe to all progress updates."""
        self.global_subscribers.add(callback)
        logger.info(f"Subscribed to global progress updates")
        return f"sub_global_{len(self.global_subscribers)}"

    def unsubscribe_from_assessment(self, assessment_id: str, callback: Callable):
        """Unsubscribe from assessment progress updates."""
        if assessment_id in self.subscribers:
            self.subscribers[assessment_id].discard(callback)
            logger.info(f"Unsubscribed from assessment progress: {assessment_id}")

    def unsubscribe_global(self, callback: Callable):
        """Unsubscribe from global updates."""
        self.global_subscribers.discard(callback)

    async def emit_event(self, event: ProgressEvent):
        """
        Emit progress event to subscribers.

        Broadcasts to both assessment-specific and global subscribers.
        """
        # Add to history
        if event.assessment_id:
            if event.assessment_id not in self.event_history:
                self.event_history[event.assessment_id] = []
            self.event_history[event.assessment_id].append(event)

            # Update current progress
            if event.assessment_id in self.current_progress:
                self.current_progress[event.assessment_id]["progress_percent"] = (
                    event.progress_percent
                )
                self.current_progress[event.assessment_id]["current_stage"] = (
                    event.status
                )
                self.current_progress[event.assessment_id]["last_event"] = event.timestamp

        logger.info(
            f"Progress event: {event.event_type}",
            extra={
                "assessment_id": event.assessment_id,
                "progress": event.progress_percent,
                "status": event.status,
            },
        )

        # Notify assessment-specific subscribers
        if event.assessment_id and event.assessment_id in self.subscribers:
            for callback in self.subscribers[event.assessment_id]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error calling subscriber callback: {e}")

        # Notify global subscribers
        for callback in self.global_subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error calling global subscriber callback: {e}")

    async def log_assessment_started(
        self, assessment_id: str, cv_filename: str, jd_title: str
    ):
        """Log: Assessment started."""
        event = ProgressEvent(
            event_id=str(uuid4()),
            event_type=ProgressEventType.ASSESSMENT_STARTED,
            assessment_id=assessment_id,
            progress_percent=5,
            status="Assessment processing started",
            details={
                "cv_filename": cv_filename,
                "jd_title": jd_title,
            },
        )
        await self.emit_event(event)

    async def log_assessment_processing(self, assessment_id: str, stage: str):
        """Log: Assessment processing in progress."""
        event = ProgressEvent(
            event_id=str(uuid4()),
            event_type=ProgressEventType.ASSESSMENT_PROCESSING,
            assessment_id=assessment_id,
            progress_percent=20,
            status=f"Running assessment: {stage}",
            details={"stage": stage},
        )
        await self.emit_event(event)

    async def log_gates_validating(
        self, assessment_id: str, gates: List[str]
    ):
        """Log: Governance gates being validated."""
        event = ProgressEvent(
            event_id=str(uuid4()),
            event_type=ProgressEventType.GATES_VALIDATING,
            assessment_id=assessment_id,
            progress_percent=40,
            status="Validating governance gates",
            details={"gates": gates},
        )
        await self.emit_event(event)

    async def log_gates_result(
        self,
        assessment_id: str,
        passed: bool,
        gate_results: Dict[str, Any],
    ):
        """Log: Governance gates validation result."""
        event = ProgressEvent(
            event_id=str(uuid4()),
            event_type=ProgressEventType.GATES_RESULT,
            assessment_id=assessment_id,
            progress_percent=50,
            status="Governance gates validation complete",
            details={
                "passed": passed,
                "results": gate_results,
            },
        )
        await self.emit_event(event)

    async def log_decision_pending(self, assessment_id: str):
        """Log: Decision pending."""
        event = ProgressEvent(
            event_id=str(uuid4()),
            event_type=ProgressEventType.DECISION_PENDING,
            assessment_id=assessment_id,
            progress_percent=60,
            status="Making decision",
        )
        await self.emit_event(event)

    async def log_decision_made(
        self, assessment_id: str, decision: str, score: float
    ):
        """Log: Decision made."""
        event = ProgressEvent(
            event_id=str(uuid4()),
            event_type=ProgressEventType.DECISION_MADE,
            assessment_id=assessment_id,
            progress_percent=70,
            status=f"Decision: {decision}",
            details={
                "decision": decision,
                "score": score,
            },
        )
        await self.emit_event(event)

    async def log_notifying(self, assessment_id: str, channels: List[str]):
        """Log: Sending notifications."""
        event = ProgressEvent(
            event_id=str(uuid4()),
            event_type=ProgressEventType.NOTIFYING,
            assessment_id=assessment_id,
            progress_percent=80,
            status=f"Sending notifications via {', '.join(channels)}",
            details={"channels": channels},
        )
        await self.emit_event(event)

    async def log_notified(self, assessment_id: str):
        """Log: Notifications sent."""
        event = ProgressEvent(
            event_id=str(uuid4()),
            event_type=ProgressEventType.NOTIFIED,
            assessment_id=assessment_id,
            progress_percent=90,
            status="Notifications sent",
        )
        await self.emit_event(event)

    async def log_provenance_creating(self, assessment_id: str):
        """Log: Creating provenance record."""
        event = ProgressEvent(
            event_id=str(uuid4()),
            event_type=ProgressEventType.PROVENANCE_CREATING,
            assessment_id=assessment_id,
            progress_percent=92,
            status="Creating provenance record",
        )
        await self.emit_event(event)

    async def log_provenance_created(self, assessment_id: str):
        """Log: Provenance record created."""
        event = ProgressEvent(
            event_id=str(uuid4()),
            event_type=ProgressEventType.PROVENANCE_CREATED,
            assessment_id=assessment_id,
            progress_percent=95,
            status="Provenance record created",
        )
        await self.emit_event(event)

    async def log_learning_processing(self, assessment_id: str):
        """Log: Processing training feedback."""
        event = ProgressEvent(
            event_id=str(uuid4()),
            event_type=ProgressEventType.LEARNING_PROCESSING,
            assessment_id=assessment_id,
            progress_percent=97,
            status="Processing training feedback",
        )
        await self.emit_event(event)

    async def log_learning_processed(self, assessment_id: str):
        """Log: Training feedback processed."""
        event = ProgressEvent(
            event_id=str(uuid4()),
            event_type=ProgressEventType.LEARNING_PROCESSED,
            assessment_id=assessment_id,
            progress_percent=99,
            status="Training feedback processed",
        )
        await self.emit_event(event)

    async def log_assessment_completed(
        self, assessment_id: str, decision: str
    ):
        """Log: Assessment completed."""
        event = ProgressEvent(
            event_id=str(uuid4()),
            event_type=ProgressEventType.ASSESSMENT_COMPLETED,
            assessment_id=assessment_id,
            progress_percent=100,
            status="Assessment completed",
            details={"final_decision": decision},
        )
        await self.emit_event(event)

    async def log_assessment_failed(self, assessment_id: str, error: str):
        """Log: Assessment failed."""
        event = ProgressEvent(
            event_id=str(uuid4()),
            event_type=ProgressEventType.ASSESSMENT_FAILED,
            assessment_id=assessment_id,
            progress_percent=0,
            status="Assessment failed",
            error=error,
        )
        await self.emit_event(event)

    async def log_queue_update(
        self, queue_size: int, processing: int, completed: int, failed: int
    ):
        """Log: Queue statistics update."""
        event = ProgressEvent(
            event_id=str(uuid4()),
            event_type=ProgressEventType.QUEUE_UPDATE,
            progress_percent=0,
            status="Queue update",
            details={
                "queue_size": queue_size,
                "processing": processing,
                "completed": completed,
                "failed": failed,
            },
        )
        await self.emit_event(event)

    async def log_recalibration_started(self):
        """Log: Learning recalibration started."""
        event = ProgressEvent(
            event_id=str(uuid4()),
            event_type=ProgressEventType.RECALIBRATION_STARTED,
            progress_percent=10,
            status="Learning recalibration started",
        )
        await self.emit_event(event)

    async def log_recalibration_testing(
        self, assessments_tested: int, total_assessments: int
    ):
        """Log: Recalibration testing progress."""
        progress = int((assessments_tested / max(total_assessments, 1)) * 80) + 10
        event = ProgressEvent(
            event_id=str(uuid4()),
            event_type=ProgressEventType.RECALIBRATION_TESTING,
            progress_percent=progress,
            status=f"Testing new weights: {assessments_tested}/{total_assessments}",
            details={
                "assessments_tested": assessments_tested,
                "total_assessments": total_assessments,
            },
        )
        await self.emit_event(event)

    async def log_recalibration_completed(
        self, improvement: float, accuracy_before: float, accuracy_after: float
    ):
        """Log: Recalibration completed."""
        event = ProgressEvent(
            event_id=str(uuid4()),
            event_type=ProgressEventType.RECALIBRATION_COMPLETED,
            progress_percent=100,
            status=f"Recalibration complete: {improvement*100:.1f}% improvement",
            details={
                "improvement": improvement,
                "accuracy_before": accuracy_before,
                "accuracy_after": accuracy_after,
            },
        )
        await self.emit_event(event)

    def get_assessment_progress(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """Get current progress for assessment."""
        return self.current_progress.get(assessment_id)

    def get_assessment_events(self, assessment_id: str) -> List[Dict[str, Any]]:
        """Get all events for assessment."""
        if assessment_id not in self.event_history:
            return []
        return [event.to_dict() for event in self.event_history[assessment_id]]


# Global progress tracker instance
_tracker: Optional[ProgressTracker] = None


def get_progress_tracker() -> ProgressTracker:
    """Get or create progress tracker."""
    global _tracker
    if _tracker is None:
        _tracker = ProgressTracker()
    return _tracker
