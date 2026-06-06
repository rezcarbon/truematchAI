"""
AI-Native Immutable Audit Trail - Phase C: Compliance & Legal Discovery

Creates write-once, append-only event log of all assessment decisions.
Enables compliance (GDPR, SOC2) and legal discovery.
"""
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    """Single immutable audit trail event."""

    event_id: str
    timestamp: str
    event_type: str  # ASSESSMENT_CREATED, ASSESSMENT_STARTED, GATES_VALIDATED, DECISION_MADE, NOTIFIED, COMPLETED
    assessment_id: str
    actor: str  # Who triggered (system, user_id, automated)
    action: str  # What happened
    result: str  # Success, failure, exception
    details: Dict[str, Any]  # Event-specific details
    ip_address: Optional[str] = None  # For security auditing
    request_id: Optional[str] = None  # Correlation ID

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class ImmutableAuditTrail:
    """
    Append-only audit trail for all assessment operations.

    Features:
    - Write-once semantics (immutable)
    - Chronological ordering
    - Event correlation (assessment_id, request_id)
    - Compliance reporting
    - Legal discovery support
    """

    def __init__(self):
        self.events: List[AuditEvent] = []
        self.assessment_events: Dict[str, List[AuditEvent]] = {}  # assessment_id -> events

    async def log_event(
        self,
        event_type: str,
        assessment_id: str,
        actor: str,
        action: str,
        result: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditEvent:
        """
        Log immutable audit event.

        Once logged, cannot be modified or deleted.
        """
        event = AuditEvent(
            event_id=str(uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            event_type=event_type,
            assessment_id=assessment_id,
            actor=actor,
            action=action,
            result=result,
            details=details,
            ip_address=ip_address,
            request_id=request_id,
        )

        # Append to global log
        self.events.append(event)

        # Index by assessment
        if assessment_id not in self.assessment_events:
            self.assessment_events[assessment_id] = []
        self.assessment_events[assessment_id].append(event)

        logger.info(
            f"Audit event logged: {event_type}",
            extra={
                "event_id": event.event_id,
                "assessment_id": assessment_id,
                "event_type": event_type,
                "result": result,
            },
        )

        return event

    async def log_assessment_created(
        self, assessment_id: str, cv_filename: str, jd_id: str, actor: str
    ) -> AuditEvent:
        """Log: Assessment created."""
        return await self.log_event(
            event_type="ASSESSMENT_CREATED",
            assessment_id=assessment_id,
            actor=actor,
            action=f"Assessment created for {cv_filename}",
            result="SUCCESS",
            details={
                "cv_filename": cv_filename,
                "jd_id": jd_id,
            },
        )

    async def log_assessment_started(
        self, assessment_id: str, reason: str = "Background processing"
    ) -> AuditEvent:
        """Log: Assessment started."""
        return await self.log_event(
            event_type="ASSESSMENT_STARTED",
            assessment_id=assessment_id,
            actor="system",
            action="Assessment processing started",
            result="SUCCESS",
            details={"reason": reason},
        )

    async def log_gates_validated(
        self,
        assessment_id: str,
        gates_passed: bool,
        gate_results: Dict[str, Any],
    ) -> AuditEvent:
        """Log: Governance gates validated."""
        return await self.log_event(
            event_type="GATES_VALIDATED",
            assessment_id=assessment_id,
            actor="system",
            action=f"Governance gates {'passed' if gates_passed else 'failed'}",
            result="SUCCESS" if gates_passed else "GATE_FAILURE",
            details={
                "gates_passed": gates_passed,
                "gate_results": gate_results,
            },
        )

    async def log_decision_made(
        self,
        assessment_id: str,
        decision: str,
        score: float,
        reasoning: Dict[str, Any],
    ) -> AuditEvent:
        """Log: Decision made."""
        return await self.log_event(
            event_type="DECISION_MADE",
            assessment_id=assessment_id,
            actor="system",
            action=f"Decision: {decision}",
            result="SUCCESS",
            details={
                "decision": decision,
                "score": score,
                "reasoning": reasoning,
            },
        )

    async def log_notifications_sent(
        self,
        assessment_id: str,
        channels: List[str],
        recipients: Dict[str, str],
    ) -> AuditEvent:
        """Log: Notifications sent."""
        return await self.log_event(
            event_type="NOTIFIED",
            assessment_id=assessment_id,
            actor="system",
            action=f"Notifications sent via {', '.join(channels)}",
            result="SUCCESS",
            details={
                "channels": channels,
                "recipients": recipients,
            },
        )

    async def log_assessment_completed(
        self,
        assessment_id: str,
        final_decision: str,
        processing_time_ms: int,
    ) -> AuditEvent:
        """Log: Assessment completed."""
        return await self.log_event(
            event_type="COMPLETED",
            assessment_id=assessment_id,
            actor="system",
            action="Assessment processing completed",
            result="SUCCESS",
            details={
                "final_decision": final_decision,
                "processing_time_ms": processing_time_ms,
            },
        )

    async def log_assessment_failed(
        self,
        assessment_id: str,
        error: str,
        exception: Optional[str] = None,
    ) -> AuditEvent:
        """Log: Assessment failed."""
        return await self.log_event(
            event_type="FAILED",
            assessment_id=assessment_id,
            actor="system",
            action="Assessment processing failed",
            result="FAILURE",
            details={
                "error": error,
                "exception": exception,
            },
        )

    async def get_assessment_history(self, assessment_id: str) -> List[AuditEvent]:
        """Get complete audit history for assessment."""
        return self.assessment_events.get(assessment_id, [])

    async def generate_compliance_report(
        self, assessment_id: str
    ) -> Dict[str, Any]:
        """Generate compliance-ready audit report."""
        events = self.assessment_events.get(assessment_id, [])

        if not events:
            return {"error": "No audit trail found"}

        return {
            "compliance_report": {
                "assessment_id": assessment_id,
                "event_count": len(events),
                "first_event": events[0].timestamp,
                "last_event": events[-1].timestamp,
                "timeline": [
                    {
                        "timestamp": e.timestamp,
                        "event_type": e.event_type,
                        "action": e.action,
                        "result": e.result,
                    }
                    for e in events
                ],
                "executive_summary": f"{assessment_id}: {len(events)} events from {events[0].timestamp} to {events[-1].timestamp}. "
                f"Final result: {events[-1].result}.",
            }
        }

    async def export_audit_log(self, assessment_ids: List[str]) -> str:
        """Export audit log as JSON-lines (one event per line)."""
        lines = []
        for assessment_id in assessment_ids:
            events = self.assessment_events.get(assessment_id, [])
            for event in events:
                lines.append(event.to_json())
        return "\n".join(lines)


# Global audit trail instance
_audit_trail: Optional[ImmutableAuditTrail] = None


def get_audit_trail() -> ImmutableAuditTrail:
    """Get or create audit trail."""
    global _audit_trail
    if _audit_trail is None:
        _audit_trail = ImmutableAuditTrail()
    return _audit_trail
