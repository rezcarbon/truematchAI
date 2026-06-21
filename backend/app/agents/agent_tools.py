"""Tool schemas for the conversational agent.

These mirror the validated action handlers in `app.services.action_handlers`
(one tool per `ACTION_HANDLERS` entry). The agent exposes them to Claude via
native tool-use so the model emits *structured, validated* tool calls instead of
free-text `[ACTION: ...]` markers parsed by regex. Each emitted tool call maps
1:1 onto an action dict that `ActionExecutor` already knows how to run or queue
for confirmation.

Tools are scoped by role so a candidate can't, e.g., approve a hiring decision.
"""
from __future__ import annotations

from typing import Any



# ── Tool definitions (Anthropic tool-use schema) ─────────────────────────────

_ANALYZE_TOOL = {
    "name": "analyze",
    "description": (
        "Run a capability analysis on a resume — optionally against a specific "
        "position. Use when the user asks to assess, score, or analyse a "
        "candidate/CV, or to find capability gaps."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "resume_id": {"type": "string", "description": "Resume UUID to analyse"},
            "position_id": {
                "type": "string",
                "description": "Optional position UUID to assess the resume against",
            },
            "analysis_type": {
                "type": "string",
                "enum": ["cv_analysis", "jd_analysis"],
                "description": "cv_analysis for candidate capability; jd_analysis for fit to a JD",
            },
        },
        "required": ["resume_id"],
    },
}

_RANK_TOOL = {
    "name": "rank",
    "description": (
        "Rank/shortlist candidates for a position by a chosen criterion. Use when "
        "the user asks to compare, shortlist, or order candidates."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "position_id": {"type": "string", "description": "Position UUID"},
            "candidate_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "1-100 candidate UUIDs to rank",
            },
            "criteria": {
                "type": "string",
                "enum": ["skill_match", "experience", "availability", "overall"],
            },
        },
        "required": ["position_id", "candidate_ids"],
    },
}

_SCHEDULE_TOOL = {
    "name": "schedule",
    "description": (
        "Schedule an interview for an application. Use when the user asks to set "
        "up, book, or arrange an interview/phone screen."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "application_id": {"type": "string", "description": "Application UUID"},
            "interview_type": {
                "type": "string",
                "enum": ["phone_screen", "technical", "onsite", "panel"],
            },
            "scheduled_time": {"type": "string", "description": "ISO-8601 datetime"},
            "duration_minutes": {"type": "integer", "description": "15-480 minutes"},
            "location": {"type": "string", "description": "Location or video link"},
        },
        "required": ["application_id", "scheduled_time"],
    },
}

_APPROVE_TOOL = {
    "name": "approve",
    "description": (
        "Record a hiring decision on an assessment (advance/reject/hold/interview/"
        "hire). Use when the user makes or confirms a decision about a candidate."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "application_id": {"type": "string"},
            "assessment_id": {"type": "string"},
            "position_id": {"type": "string"},
            "decision": {
                "type": "string",
                "enum": ["advance", "reject", "hold", "interview", "hire"],
            },
            "reasoning": {"type": "string", "description": "Why this decision (optional)"},
        },
        "required": ["application_id", "assessment_id", "position_id", "decision"],
    },
}

_SEND_TOOL = {
    "name": "send",
    "description": (
        "Send a notification/email to a user (offer, rejection, update, schedule). "
        "Use when the user asks to notify, email, or message a candidate."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "recipient_id": {"type": "string", "description": "Recipient user UUID"},
            "message_type": {
                "type": "string",
                "enum": ["offer", "rejection", "update", "schedule"],
            },
            "context": {"type": "object", "description": "Message context (candidate, position, …)"},
        },
        "required": ["recipient_id", "message_type"],
    },
}

_UPLOAD_TOOL = {
    "name": "upload",
    "description": (
        "Register an already-uploaded file (resume/JD/candidate list) for "
        "processing. Only use when a file_id from a prior upload is available."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "file_id": {"type": "string"},
            "file_type": {"type": "string", "enum": ["resume", "jd", "candidates"]},
            "filename": {"type": "string"},
            "job_title": {"type": "string"},
            "jd_text": {"type": "string"},
        },
        "required": ["file_id", "filename"],
    },
}


_PLAN_TOOL = {
    "name": "plan",
    "description": (
        "Propose a MULTI-STEP plan when the user's goal requires more than one "
        "action (e.g. 'rank these candidates, then schedule the top two'). Each "
        "step uses one of the other tools. Later steps may reference earlier "
        "results with the placeholder syntax {{step_N.PATH}} — e.g. "
        "{{step_1.rankings[0].candidate_id}}. The user approves the whole plan "
        "once; steps then execute in order. Use the individual tools directly "
        "for single-action requests."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Short name for the plan"},
            "steps": {
                "type": "array",
                "minItems": 2,
                "maxItems": 8,
                "items": {
                    "type": "object",
                    "properties": {
                        "tool": {
                            "type": "string",
                            "enum": ["analyze", "rank", "schedule", "approve", "send"],
                        },
                        "parameters": {
                            "type": "object",
                            "description": (
                                "Tool parameters; string values may embed "
                                "{{step_N.PATH}} references to earlier results"
                            ),
                        },
                        "description": {"type": "string"},
                    },
                    "required": ["tool", "parameters"],
                },
            },
        },
        "required": ["title", "steps"],
    },
}


_CLARIFY_TOOL = {
    "name": "clarify",
    "description": (
        "Ask the user a clarifying question BEFORE acting when the request is "
        "ambiguous or missing a parameter you need (e.g. which position, which "
        "candidates, what time, who to notify). ALWAYS prefer this over guessing "
        "or over emitting a multi-step `plan` with assumed values. Provide "
        "suggested answers in `options` when you can. This changes nothing — it "
        "only asks."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The single, specific question to ask"},
            "options": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional suggested answers the user can pick from",
            },
            "missing": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Which parameters are missing/ambiguous (for context)",
            },
        },
        "required": ["question"],
    },
}


_ALL_TOOLS = {
    "analyze": _ANALYZE_TOOL,
    "rank": _RANK_TOOL,
    "schedule": _SCHEDULE_TOOL,
    "approve": _APPROVE_TOOL,
    "send": _SEND_TOOL,
    "upload": _UPLOAD_TOOL,
    "plan": _PLAN_TOOL,
    "clarify": _CLARIFY_TOOL,
}

# Which tools each role may use. Candidates can only analyse their own resume.
# Every role may `clarify` — asking a question is never privileged.
_ROLE_TOOLS: dict[str, list[str]] = {
    "candidate": ["analyze", "clarify"],
    "recruiter": ["analyze", "rank", "schedule", "approve", "send", "upload", "plan", "clarify"],
    "admin": ["analyze", "rank", "schedule", "approve", "send", "upload", "plan", "clarify"],
}

# Tools that change state and should ALWAYS be confirmed by the user before
# executing, even in autonomous mode is off (handled by the manual-mode default).
MUTATING_TOOLS = {"schedule", "approve", "send", "upload", "plan"}


def tools_for_role(role: Any) -> list[dict]:
    """Return the tool schemas available to a user role."""
    key = getattr(role, "value", str(role)).lower()
    names = _ROLE_TOOLS.get(key, ["analyze"])
    return [_ALL_TOOLS[n] for n in names if n in _ALL_TOOLS]


def describe_tool_call(name: str, params: dict) -> str:
    """Human-readable one-line description of a tool call for the UI/audit."""
    if name == "analyze":
        return f"Analyse resume {str(params.get('resume_id', ''))[:8]}…"
    if name == "rank":
        n = len(params.get("candidate_ids", []) or [])
        return f"Rank {n} candidate(s) for position {str(params.get('position_id', ''))[:8]}…"
    if name == "schedule":
        return f"Schedule {params.get('interview_type', 'interview')} for application {str(params.get('application_id', ''))[:8]}…"
    if name == "approve":
        return f"Record decision '{params.get('decision', 'advance')}' on assessment {str(params.get('assessment_id', ''))[:8]}…"
    if name == "send":
        return f"Send {params.get('message_type', 'update')} to {str(params.get('recipient_id', ''))[:8]}…"
    if name == "upload":
        return f"Process uploaded {params.get('file_type', 'file')} '{params.get('filename', '')}'"
    if name == "plan":
        steps = params.get("steps", []) or []
        seq = " → ".join(s.get("tool", "?") for s in steps)
        return f"Plan: {params.get('title', 'multi-step')} ({len(steps)} steps: {seq})"
    if name == "clarify":
        return f"Clarifying question: {str(params.get('question', ''))[:80]}"
    return f"{name} action"


def tool_calls_to_actions(tool_calls: list[dict]) -> list[dict]:
    """Map raw Anthropic tool_use blocks to ActionExecutor action dicts."""
    actions: list[dict] = []
    for i, call in enumerate(tool_calls):
        name = call.get("name", "")
        params = call.get("input") if isinstance(call.get("input"), dict) else {}
        actions.append(
            {
                "id": call.get("id") or f"action_{i}",
                "type": name,
                "description": describe_tool_call(name, params),
                "parameters": params,
                "status": "pending",
                "requires_confirmation": name in MUTATING_TOOLS,
            }
        )
    return actions
