"""Durable user-memory merge tasks.

A beat task finds users whose chat activity is newer than their memory and
enqueues a per-user LLM summarize-merge. The merge uses the SECONDARY model
class (budget-aware routing) — memory curation never needs the frontier model.
"""
from __future__ import annotations

import json
import logging
import uuid

from sqlalchemy import select

from app.engines.client import call_claude_json, is_live, select_model
from app.models.chat import ChatMessage, ChatSession
from app.models.user_memory import UserAgentMemory
from app.services.user_memory import MAX_ITEMS_PER_SECTION, MERGE_PROMPT
from app.workers.celery_app import celery_app
from app.workers.tasks import _session_factory

logger = logging.getLogger("truematch.user_memory")

# How many recent messages feed one merge (bounded prompt size).
_TRANSCRIPT_LIMIT = 40
_EMPTY = {"facts": [], "preferences": [], "active_focus": []}


@celery_app.task(name="app.workers.user_memory.merge_stale_user_memories")
def merge_stale_user_memories() -> dict:
    """Beat entry point: enqueue a merge for every user with fresh chat activity."""
    with _session_factory()() as db:
        rows = db.execute(
            select(ChatSession.user_id, UserAgentMemory.updated_at)
            .outerjoin(UserAgentMemory, UserAgentMemory.user_id == ChatSession.user_id)
            .where(ChatSession.last_message_at.is_not(None))
            .distinct()
        ).all()
        stale = [
            str(user_id)
            for user_id, mem_updated in rows
            if mem_updated is None
            or db.execute(
                select(ChatSession.id)
                .where(
                    ChatSession.user_id == user_id,
                    ChatSession.last_message_at > mem_updated,
                )
                .limit(1)
            ).first()
            is not None
        ]
    for uid in stale:
        merge_user_memory.delay(uid)
    return {"enqueued": len(stale)}


@celery_app.task(name="app.workers.user_memory.merge_user_memory", max_retries=1)
def merge_user_memory(user_id: str) -> dict:
    """LLM summarize-merge of recent chat into the user's durable memory."""
    if not is_live():
        return {"status": "skipped", "reason": "no API key (mock mode)"}

    uid = uuid.UUID(user_id)
    with _session_factory()() as db:
        row = db.execute(
            select(UserAgentMemory).where(UserAgentMemory.user_id == uid)
        ).scalar_one_or_none()
        existing = (row.memory if row else None) or _EMPTY

        since = row.updated_at if row else None
        q = (
            select(ChatMessage.role, ChatMessage.content)
            .join(ChatSession, ChatSession.id == ChatMessage.session_id)
            .where(ChatSession.user_id == uid)
            .order_by(ChatMessage.created_at.desc())
            .limit(_TRANSCRIPT_LIMIT)
        )
        if since is not None:
            q = q.where(ChatMessage.created_at > since)
        messages = list(reversed(db.execute(q).all()))
        if not messages:
            return {"status": "skipped", "reason": "no new messages"}

        transcript = "\n".join(f"{role}: {content[:500]}" for role, content in messages)
        merged = call_claude_json(
            system="You curate durable user memory. Be terse and conservative.",
            user_content=MERGE_PROMPT.format(
                existing=json.dumps(existing),
                transcript=transcript,
                max_items=MAX_ITEMS_PER_SECTION,
            ),
            max_tokens=1024,
            model=select_model("secondary"),
        )
        memory = {
            k: [str(i) for i in (merged.get(k) or [])][:MAX_ITEMS_PER_SECTION]
            for k in _EMPTY
        }

        if row is None:
            row = UserAgentMemory(user_id=uid, memory=memory, merge_count=1)
            db.add(row)
        else:
            row.memory = memory
            row.merge_count = (row.merge_count or 0) + 1
        db.commit()
        logger.info("Merged user memory for %s (merge #%s)", user_id, row.merge_count)
        return {"status": "completed", "user_id": user_id, "merge_count": row.merge_count}
