"""WebSocket manager for real-time agent operator events.

Handles broadcasting of queue item state changes, agent metrics, and alerts
to connected operator dashboards.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, Set
from datetime import datetime

from fastapi import WebSocket

logger = logging.getLogger("truematch.agents_websocket")


class AgentOperatorManager:
    """
    Manages WebSocket connections for agent operators.

    Operators can subscribe to receive real-time events about:
    - Queue item approvals/rejections
    - Agent status changes
    - Processing errors and alerts
    """

    def __init__(self):
        """Initialize the operator connection manager."""
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self, websocket: WebSocket) -> None:
        """
        Subscribe a WebSocket connection to operator events.

        Args:
            websocket: The WebSocket connection to accept and track.

        Raises:
            RuntimeError: If the connection cannot be accepted.
        """
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.debug(f"Operator subscribed. Total: {len(self.active_connections)}")

    async def unsubscribe(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection from the operator feed.

        Args:
            websocket: The WebSocket connection to remove.
        """
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.debug(f"Operator unsubscribed. Total: {len(self.active_connections)}")

    async def broadcast_event(
        self,
        event_type: str,
        data: dict,
        exclude_websocket: WebSocket | None = None,
    ) -> None:
        """
        Broadcast an event to all connected operators.

        Args:
            event_type: Type of event (e.g., 'queue_item_action', 'agent_alert')
            data: Event payload
            exclude_websocket: Optional connection to exclude from broadcast

        Example:
            await manager.broadcast_event(
                event_type='queue_item_action',
                data={
                    'item_id': item.id,
                    'action': 'approved',
                    'by_user': user.id,
                }
            )
        """
        message = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }
        payload = json.dumps(message)

        dead_connections: Set[WebSocket] = set()

        async with self._lock:
            connections_copy = list(self.active_connections)

        for websocket in connections_copy:
            if websocket == exclude_websocket:
                continue

            try:
                await websocket.send_text(payload)
            except Exception as e:
                logger.warning(f"Failed to broadcast to operator: {e}")
                dead_connections.add(websocket)

        # Clean up dead connections
        if dead_connections:
            async with self._lock:
                self.active_connections.difference_update(dead_connections)
            logger.debug(f"Cleaned {len(dead_connections)} dead connections")

    async def broadcast_queue_item_action(
        self,
        item_id: str,
        action: str,
        user_id: str,
        status: str,
        notes: str | None = None,
        assessment_id: str | None = None,
    ) -> None:
        """
        Broadcast a queue item action event.

        Args:
            item_id: ID of the queue item
            action: Action performed ('approved', 'rejected', 'reassigned')
            user_id: ID of user performing the action
            status: New status of the item
            notes: Optional review notes
            assessment_id: Optional assessment ID created by approval
        """
        await self.broadcast_event(
            event_type="queue_item_action",
            data={
                "item_id": str(item_id),
                "action": action,
                "user_id": str(user_id),
                "status": status,
                "notes": notes,
                "assessment_id": str(assessment_id) if assessment_id else None,
            },
        )

    async def broadcast_agent_status_change(
        self,
        agent_type: str,
        running: bool,
        queue_size: int,
        last_error: str | None = None,
    ) -> None:
        """
        Broadcast an agent status change.

        Args:
            agent_type: Type of agent ('cv', 'jd', 'email')
            running: Whether agent is running
            queue_size: Current queue size
            last_error: Optional error message if status degraded
        """
        await self.broadcast_event(
            event_type="agent_status_change",
            data={
                "agent_type": agent_type,
                "running": running,
                "queue_size": queue_size,
                "last_error": last_error,
            },
        )

    async def broadcast_processing_alert(
        self,
        agent_type: str,
        alert_level: str,
        message: str,
        context: dict | None = None,
    ) -> None:
        """
        Broadcast a processing alert (error, warning, info).

        Args:
            agent_type: Type of agent where alert originated
            alert_level: Severity level ('error', 'warning', 'info')
            message: Alert message
            context: Optional additional context data
        """
        await self.broadcast_event(
            event_type="processing_alert",
            data={
                "agent_type": agent_type,
                "level": alert_level,
                "message": message,
                "context": context or {},
            },
        )

    def get_subscriber_count(self) -> int:
        """Get current number of connected operators."""
        return len(self.active_connections)


# Global singleton instance
_operator_manager: AgentOperatorManager | None = None


def get_operator_manager() -> AgentOperatorManager:
    """Get or create the global operator manager instance."""
    global _operator_manager
    if _operator_manager is None:
        _operator_manager = AgentOperatorManager()
    return _operator_manager
