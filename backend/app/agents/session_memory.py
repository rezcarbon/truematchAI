"""Session memory management for maintaining conversation context."""
import json
from app.core.clock import utcnow


class SessionMemory:
    """Tracks conversation context across messages within a session."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.context = {
            "current_focus": None,  # What user is currently working on
            "active_resources": {},  # User's CVs, jobs, candidates
            "last_action": None,  # Last action taken
            "conversation_state": "idle",  # idle, processing, awaiting_confirmation
            "metadata": {
                "started_at": utcnow().isoformat(),
                "message_count": 0,
                "focus_changes": [],
            },
        }

    def update_focus(self, focus: str):
        """Update what user is currently focused on."""
        old_focus = self.context["current_focus"]
        self.context["current_focus"] = focus
        if old_focus != focus:
            self.context["metadata"]["focus_changes"].append({
                "from": old_focus,
                "to": focus,
                "timestamp": utcnow().isoformat(),
            })

    def add_resource(self, resource_type: str, resource_id: str, name: str):
        """Track a resource the user is working with."""
        if resource_type not in self.context["active_resources"]:
            self.context["active_resources"][resource_type] = []

        self.context["active_resources"][resource_type].append({
            "id": resource_id,
            "name": name,
            "added_at": utcnow().isoformat(),
        })

    def set_state(self, state: str):
        """Update conversation state."""
        self.context["conversation_state"] = state

    def record_action(self, action_id: str, description: str, status: str):
        """Record last action taken."""
        self.context["last_action"] = {
            "id": action_id,
            "description": description,
            "status": status,
            "timestamp": utcnow().isoformat(),
        }

    def increment_message_count(self):
        """Track number of messages in this session."""
        self.context["metadata"]["message_count"] += 1

    def get_context(self) -> dict:
        """Get current session context."""
        return self.context

    def to_json(self) -> str:
        """Serialize context to JSON."""
        return json.dumps(self.context, default=str)

    @classmethod
    def from_json(cls, session_id: str, json_str: str) -> "SessionMemory":
        """Deserialize context from JSON."""
        memory = cls(session_id)
        memory.context = json.loads(json_str)
        return memory
