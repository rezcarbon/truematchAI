"""
WebSocket connection manager for real-time updates
Handles: pipeline updates, interview notifications, scorecard notifications, presence
"""

from typing import Dict, Set
import json
from datetime import datetime
from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}  # position_id -> set of websockets
        self.user_positions: Dict[WebSocket, str] = {}  # websocket -> position_id
        self.websocket_users: Dict[WebSocket, str] = {}  # websocket -> user_id (for proper routing)
        self.user_presence: Dict[str, Set[str]] = {}  # position_id -> set of user_ids

    async def connect(self, websocket: WebSocket, position_id: str, user_id: str):
        """Register a new WebSocket connection"""
        await websocket.accept()

        if position_id not in self.active_connections:
            self.active_connections[position_id] = set()

        self.active_connections[position_id].add(websocket)
        self.user_positions[websocket] = position_id
        self.websocket_users[websocket] = str(user_id)  # Store actual user_id for routing

        # Track user presence
        if position_id not in self.user_presence:
            self.user_presence[position_id] = set()
        self.user_presence[position_id].add(str(user_id))

        # Broadcast presence update
        await self._broadcast_to_position(
            position_id,
            {
                "type": "presence_update",
                "active_users": list(self.user_presence.get(position_id, set())),
                "timestamp": datetime.utcnow().isoformat(),
            },
            exclude_websocket=None,
        )

    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection"""
        position_id = self.user_positions.get(websocket)

        if position_id:
            self.active_connections[position_id].discard(websocket)
            self.user_presence[position_id].discard(str(user_id))

            # Broadcast presence update
            if self.active_connections[position_id]:
                await self._broadcast_to_position(
                    position_id,
                    {
                        "type": "presence_update",
                        "active_users": list(self.user_presence.get(position_id, set())),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

        # Clean up connection tracking
        if websocket in self.user_positions:
            del self.user_positions[websocket]
        if websocket in self.websocket_users:
            del self.websocket_users[websocket]

    async def broadcast_pipeline_update(self, position_id: str, application_id: str, new_stage: str):
        """Broadcast when a candidate moves to a new stage"""
        await self._broadcast_to_position(
            position_id,
            {
                "type": "pipeline_update",
                "application_id": application_id,
                "new_stage": new_stage,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def broadcast_interview_scheduled(self, position_id: str, application_id: str, scheduled_at: str):
        """Broadcast when an interview is scheduled"""
        await self._broadcast_to_position(
            position_id,
            {
                "type": "interview_scheduled",
                "application_id": application_id,
                "scheduled_at": scheduled_at,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def send_interview_reminder(self, position_id: str, user_id: str, interview_id: str, minutes_until: int):
        """Send an interview reminder to a specific user"""
        message = {
            "type": "interview_reminder",
            "interview_id": interview_id,
            "minutes_until": minutes_until,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if position_id in self.active_connections:
            for websocket in self.active_connections[position_id]:
                try:
                    await websocket.send_json(message)
                except:
                    pass

    async def broadcast_scorecard_submitted(self, position_id: str, interview_id: str, score: float):
        """Broadcast when a scorecard is submitted"""
        await self._broadcast_to_position(
            position_id,
            {
                "type": "scorecard_submitted",
                "interview_id": interview_id,
                "score": score,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def send_notification_to_user(self, user_id: str, notification: dict):
        """Send a notification to a specific user via WebSocket if connected.

        Routes notification to all WebSocket connections for the target user_id.
        """
        user_id_str = str(user_id)
        delivered = False

        # Find all websockets connected by this user (across different positions)
        for position_id, websockets in self.active_connections.items():
            for ws in list(websockets):  # Use list() to avoid mutation issues
                # Get the actual user_id from our tracking dictionary
                ws_user_id = self.websocket_users.get(ws)

                # Only send if this websocket belongs to the target user
                if ws_user_id == user_id_str:
                    try:
                        await ws.send_json(notification)
                        delivered = True
                    except Exception as e:
                        # Log but don't fail - remove dead connection
                        logger.warning(
                            f"Failed to send notification to user {user_id_str}",
                            extra={"user_id": user_id_str, "error": str(e)},
                        )
                        try:
                            websockets.discard(ws)
                        except Exception:
                            pass

        if not delivered:
            logger.debug(
                f"User {user_id_str} not connected for real-time notification delivery",
                extra={"user_id": user_id_str},
            )

    async def _broadcast_to_position(
        self,
        position_id: str,
        message: dict,
        exclude_websocket: WebSocket = None
    ):
        """Broadcast a message to all connected clients for a position"""
        if position_id not in self.active_connections:
            return

        dead_connections = []
        for websocket in self.active_connections[position_id]:
            if websocket == exclude_websocket:
                continue

            try:
                await websocket.send_json(message)
            except Exception:
                dead_connections.append(websocket)

        # Clean up dead connections
        for websocket in dead_connections:
            await self.disconnect(websocket, "system")


# Global connection manager instance
manager = ConnectionManager()
