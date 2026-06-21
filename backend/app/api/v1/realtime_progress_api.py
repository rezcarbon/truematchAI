"""
Real-Time Progress WebSocket API - Phase E

WebSocket endpoints for:
- Live assessment progress updates
- Queue statistics streaming
- Learning recalibration monitoring
- Assessment history retrieval
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.workers.realtime_progress import get_progress_tracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/realtime", tags=["realtime"])


@router.websocket("/ws/assessment/{assessment_id}")
async def websocket_assessment_progress(websocket: WebSocket, assessment_id: str):
    """
    WebSocket for real-time assessment progress.

    Client connects to this endpoint and receives live updates as assessment
    moves through stages: started → processing → gates → decision → notified → completed.

    Example (JavaScript):
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/realtime/ws/assessment/uuid');
    ws.onmessage = (event) => {
        const progressEvent = JSON.parse(event.data);
        console.log(`Progress: ${progressEvent.progress_percent}% - ${progressEvent.status}`);
    };
    ```
    """
    await websocket.accept()
    tracker = get_progress_tracker()

    # Define callback to send updates via WebSocket
    async def send_progress_update(event: Any):
        try:
            await websocket.send_json(event.to_dict())
        except Exception as e:
            logger.error(f"Error sending WebSocket update: {e}")

    # Subscribe to assessment progress
    tracker.subscribe_to_assessment(assessment_id, send_progress_update)

    # Send current progress if available
    current = tracker.get_assessment_progress(assessment_id)
    if current:
        await websocket.send_json(current)

    # Send event history
    events = tracker.get_assessment_events(assessment_id)
    for event in events:
        await websocket.send_json(event)

    try:
        # Keep connection open and receive heartbeat/disconnect
        while True:
            data = await websocket.receive_text()
            # Could handle client commands here (e.g., pause, cancel)
            logger.debug(f"Received from client: {data}")
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {assessment_id}")
        tracker.unsubscribe_from_assessment(
            assessment_id, send_progress_update
        )


@router.websocket("/ws/global")
async def websocket_global_progress(websocket: WebSocket):
    """
    WebSocket for global system progress.

    Streams all assessment progress + queue statistics to connected clients.
    Useful for dashboards showing system-wide status.

    Example (JavaScript):
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/realtime/ws/global');
    ws.onmessage = (event) => {
        const progressEvent = JSON.parse(event.data);
        if (progressEvent.event_type === 'queue_update') {
            console.log(`Queue: ${progressEvent.details.queue_size} pending`);
        }
    };
    ```
    """
    await websocket.accept()
    tracker = get_progress_tracker()

    # Define callback to send updates via WebSocket
    async def send_progress_update(event: Any):
        try:
            await websocket.send_json(event.to_dict())
        except Exception as e:
            logger.error(f"Error sending global WebSocket update: {e}")

    # Subscribe to all progress updates
    tracker.subscribe_global(send_progress_update)

    try:
        # Keep connection open
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received from client: {data}")
    except WebSocketDisconnect:
        logger.info("Global client disconnected")
        tracker.unsubscribe_global(send_progress_update)


@router.get("/assessment/{assessment_id}/progress")
async def get_assessment_progress(assessment_id: str) -> Dict[str, Any]:
    """
    Get current progress for assessment (REST fallback).

    Returns current stage and progress percentage.
    Useful if client prefers polling to WebSocket.
    """
    tracker = get_progress_tracker()
    progress = tracker.get_assessment_progress(assessment_id)

    if not progress:
        raise HTTPException(status_code=404, detail="Assessment not found")

    return progress


@router.get("/assessment/{assessment_id}/events")
async def get_assessment_events(assessment_id: str) -> Dict[str, Any]:
    """
    Get all progress events for assessment (REST fallback).

    Returns complete timeline of progress events.
    """
    tracker = get_progress_tracker()
    events = tracker.get_assessment_events(assessment_id)

    if not events:
        return {
            "assessment_id": assessment_id,
            "event_count": 0,
            "events": [],
        }

    return {
        "assessment_id": assessment_id,
        "event_count": len(events),
        "events": events,
    }


# WebSocket message format documentation
"""
# WebSocket Message Format (from server to client)

All WebSocket messages are JSON objects with this structure:

{
    "event_id": "uuid",
    "event_type": "assessment_started|assessment_processing|gates_validating|...",
    "assessment_id": "uuid or null",
    "timestamp": "2026-06-06T12:34:56.789Z",
    "progress_percent": 0-100,
    "status": "Human-readable status message",
    "details": { ... },  // Event-specific data
    "error": null or "Error message"
}

# Example Events:

1. Assessment Started
{
    "event_type": "assessment_started",
    "assessment_id": "abc-123",
    "progress_percent": 5,
    "status": "Assessment processing started",
    "details": {
        "cv_filename": "john_doe.pdf",
        "jd_title": "Senior Backend Engineer"
    }
}

2. Assessment Processing
{
    "event_type": "assessment_processing",
    "assessment_id": "abc-123",
    "progress_percent": 20,
    "status": "Running assessment: capability_analysis",
    "details": { "stage": "capability_analysis" }
}

3. Governance Gates Validating
{
    "event_type": "gates_validating",
    "assessment_id": "abc-123",
    "progress_percent": 40,
    "status": "Validating governance gates",
    "details": {
        "gates": ["coherence", "consistency", "fidelity", "bias"]
    }
}

4. Gates Result
{
    "event_type": "gates_result",
    "assessment_id": "abc-123",
    "progress_percent": 50,
    "status": "Governance gates validation complete",
    "details": {
        "passed": true,
        "results": {
            "coherence": "PASSED",
            "consistency": "PASSED",
            "fidelity": "PASSED",
            "bias": "PASSED"
        }
    }
}

5. Decision Made
{
    "event_type": "decision_made",
    "assessment_id": "abc-123",
    "progress_percent": 70,
    "status": "Decision: AUTO_APPROVE",
    "details": {
        "decision": "AUTO_APPROVE",
        "score": 0.89
    }
}

6. Assessment Completed
{
    "event_type": "assessment_completed",
    "assessment_id": "abc-123",
    "progress_percent": 100,
    "status": "Assessment completed",
    "details": {
        "final_decision": "AUTO_APPROVE"
    }
}

7. Assessment Failed
{
    "event_type": "assessment_failed",
    "assessment_id": "abc-123",
    "progress_percent": 0,
    "status": "Assessment failed",
    "error": "LLM timeout after 30 seconds"
}

8. Queue Update
{
    "event_type": "queue_update",
    "progress_percent": 0,
    "status": "Queue update",
    "details": {
        "queue_size": 5,
        "processing": 2,
        "completed": 142,
        "failed": 3
    }
}
"""
