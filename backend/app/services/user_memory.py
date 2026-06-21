"""Durable per-user agent memory: read-side helpers + LLM merge prompt.

The agent injects a small, curated memory block into its system prompt every
turn (async read). A Celery task periodically merges recent chat transcripts
into that memory with an LLM summarize-merge (sync write). Memory is stored
encrypted (EncryptedJSON) and is user-erasable.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_memory import UserAgentMemory

# Hard caps keep the injected block small and the merge convergent.
MAX_ITEMS_PER_SECTION = 10
_SECTIONS = ("facts", "preferences", "active_focus")


async def fetch_memory_block(db: AsyncSession, user_id: uuid.UUID) -> str:
    """Return the formatted DURABLE MEMORY prompt block for a user ('' if none)."""
    row = (
        await db.execute(
            select(UserAgentMemory).where(UserAgentMemory.user_id == user_id)
        )
    ).scalar_one_or_none()
    if row is None or not row.memory:
        return ""
    return format_memory_block(row.memory)


def format_memory_block(memory: dict) -> str:
    """Format the memory dict as prompt text (shared by async + sync paths)."""
    lines: list[str] = []
    titles = {
        "facts": "Known facts",
        "preferences": "Preferences",
        "active_focus": "Active focus",
    }
    for key in _SECTIONS:
        items = (memory.get(key) or [])[:MAX_ITEMS_PER_SECTION]
        if items:
            lines.append(f"{titles[key]}:")
            lines.extend(f"- {item}" for item in items)
    return "\n".join(lines)


MERGE_PROMPT = """You maintain a small durable memory about how one user works \
with a hiring platform's AI assistant. Merge the new conversation into the \
existing memory.

EXISTING MEMORY (JSON):
{existing}

NEW CONVERSATION (most recent messages, oldest first):
{transcript}

Rules:
- Keep only DURABLE information: stable facts about the user's role/work, \
expressed preferences about how the assistant should behave, and what the \
user is currently working on (active_focus).
- Drop anything transient, sensitive, or speculative. No message quotes.
- Update or remove items the new conversation contradicts or completes.
- Each item is one short sentence. At most {max_items} items per list.

Return JSON: {{"facts": [...], "preferences": [...], "active_focus": [...]}}
"""
