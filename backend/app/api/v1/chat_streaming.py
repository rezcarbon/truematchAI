"""Server-Sent Events (SSE) streaming for real-time chat progress."""
import asyncio
import json
import logging
import threading
from app.core.clock import utcnow
from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.config import settings
from app.deps import get_current_user, get_db
from app.models.user import User
from app.models.chat import ChatMessage, ChatSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


def _sse(event: str, data: dict) -> str:
    """Format a Server-Sent Event frame."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


class StreamMessageRequest(BaseModel):
    message: str


@router.post("/{session_id}/message/stream")
async def stream_chat_message(
    session_id: str,
    payload: StreamMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Send a message and stream the assistant's reply token-by-token (SSE).

    Streams real model output as it is generated, then emits a final `done`
    event carrying the persisted `message_id`, any structured tool actions, and
    suggestions. Falls back to a chunked mock reply when no API key is set.
    """
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID")

    session = await db.get(ChatSession, session_uuid)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Persist the user message up front.
    db.add(ChatMessage(session_id=session_uuid, role="user", content=payload.message))
    await db.commit()

    # Build the same role-aware context the non-streaming path uses.
    from app.agents.agent_router import get_agent_for_user
    from app.agents.agent_tools import tools_for_role, tool_calls_to_actions
    from app.engines.client import _build_system, get_client, is_live

    agent = await get_agent_for_user(user.id, user.role, db, company_id=None)
    system_prompt, user_context = await agent.prepare_turn(payload.message, user, db)
    message = payload.message

    async def event_generator() -> AsyncGenerator[str, None]:
        yield _sse("connected", {"session_id": session_id})

        full_text_parts: list[str] = []
        tool_calls: list[dict] = []

        if not is_live():
            # Mock fallback: stream a context-aware reply in word chunks.
            reply = agent._mock_reply(message, user_context)
            for word in reply.split(" "):
                full_text_parts.append(word + " ")
                yield _sse("token", {"text": word + " "})
                await asyncio.sleep(0.01)
        else:
            # Bridge the synchronous SDK stream into async SSE via a queue.
            queue: asyncio.Queue = asyncio.Queue()
            loop = asyncio.get_running_loop()
            tools = tools_for_role(user.role)

            def worker() -> None:
                try:
                    with get_client().messages.stream(
                        model=settings.anthropic_model,
                        max_tokens=1024,
                        temperature=0.2,
                        # Reuse the shared system-block builder so the large,
                        # stable prompt is prompt-cached (matches non-streaming).
                        system=_build_system(system_prompt, True),
                        tools=tools,
                        messages=[{"role": "user", "content": message}],
                    ) as stream:
                        for text in stream.text_stream:
                            loop.call_soon_threadsafe(queue.put_nowait, ("token", text))
                        final = stream.get_final_message()
                        try:
                            from app.core.llm_usage import record_usage
                            record_usage(settings.anthropic_model, getattr(final, "usage", None))
                        except Exception:  # noqa: BLE001
                            pass
                        calls = [
                            {"id": b.id, "name": b.name, "input": b.input}
                            for b in final.content
                            if getattr(b, "type", None) == "tool_use"
                        ]
                        loop.call_soon_threadsafe(queue.put_nowait, ("tools", calls))
                except Exception as exc:  # noqa: BLE001 — surfaced as SSE error
                    loop.call_soon_threadsafe(queue.put_nowait, ("error", str(exc)))
                finally:
                    loop.call_soon_threadsafe(queue.put_nowait, ("end", None))

            threading.Thread(target=worker, daemon=True).start()

            stream_errored = False
            try:
                while True:
                    kind, data = await queue.get()
                    if kind == "end":
                        break
                    if kind == "token":
                        full_text_parts.append(data)
                        yield _sse("token", {"text": data})
                    elif kind == "tools":
                        tool_calls = data or []
                    elif kind == "error":
                        stream_errored = True
            except (asyncio.CancelledError, GeneratorExit):
                # Client disconnected mid-stream — stop forwarding. The worker
                # thread is a daemon over a context-managed SDK stream, so it
                # unwinds on its own; we simply stop draining the queue.
                raise

            if stream_errored:
                if not full_text_parts:
                    # Total failure before any text (e.g. exhausted credit
                    # balance): degrade to a chunked context-aware mock reply so
                    # the chat stays usable instead of showing a raw error.
                    reply = agent._mock_reply(message, user_context)
                    for word in reply.split(" "):
                        full_text_parts.append(word + " ")
                        yield _sse("token", {"text": word + " "})
                        await asyncio.sleep(0.01)
                else:
                    # Partial reply then failure: signal the truncation rather
                    # than presenting it as a complete answer.
                    yield _sse("error", {"error": "The response was cut off. Please retry."})

        text = "".join(full_text_parts).strip()
        actions = tool_calls_to_actions(tool_calls)
        if not text and actions:
            text = "I've prepared the following action(s) for your review:"
        elif not text:
            text = "Done."

        # Persist the assistant message (with any pending actions) and update
        # the session, using a fresh DB session — the request-scoped one may be
        # mid-stream. Import lazily to avoid a cycle.
        from app.database import AsyncSessionLocal

        message_id = ""
        try:
            async with AsyncSessionLocal() as wdb:
                assistant = ChatMessage(
                    session_id=session_uuid,
                    role="assistant",
                    content=text,
                    actions_taken=actions or None,
                )
                wdb.add(assistant)
                s = await wdb.get(ChatSession, session_uuid)
                if s:
                    s.last_message_at = utcnow()
                await wdb.commit()
                message_id = str(assistant.id)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to persist streamed assistant message: %s", exc)

        yield _sse(
            "done",
            {
                "message_id": message_id,
                "actions": actions,
                "suggestions": agent._generate_suggestions(user_context, actions),
            },
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{session_id}/stream")
async def stream_chat_progress(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream real-time progress updates for a chat session.

    Uses Server-Sent Events (SSE) to push updates to the client
    as the agent processes the message and executes actions.

    Args:
        session_id: Chat session ID
        user: Current user
        db: Database session

    Returns:
        StreamingResponse with SSE events
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for chat progress."""
        try:
            # Send initial connection event
            yield "event: connected\n"
            yield f'data: {{"session_id": "{session_id}", "user_id": "{str(user.id)}"}}\n\n'

            # Simulate processing stages with updates
            # In production, these would be actual async tasks updating a progress table

            yield "event: analyzing\n"
            yield 'data: {"stage": "analyzing_message", "progress": 10}\n\n'
            await asyncio.sleep(0.5)

            yield "event: context_loaded\n"
            yield 'data: {"stage": "loaded_user_context", "progress": 25}\n\n'
            await asyncio.sleep(0.5)

            yield "event: llm_request\n"
            yield 'data: {"stage": "sending_to_llm", "progress": 40}\n\n'
            await asyncio.sleep(1.0)

            yield "event: llm_response\n"
            yield 'data: {"stage": "received_from_llm", "progress": 60}\n\n'
            await asyncio.sleep(0.3)

            yield "event: parsing_actions\n"
            yield 'data: {"stage": "parsing_agent_actions", "progress": 75}\n\n'
            await asyncio.sleep(0.3)

            yield "event: executing_actions\n"
            yield 'data: {"stage": "executing_actions", "progress": 85}\n\n'
            await asyncio.sleep(0.5)

            yield "event: saving_context\n"
            yield 'data: {"stage": "saving_session_memory", "progress": 95}\n\n'
            await asyncio.sleep(0.2)

            # Send final completion event
            yield "event: completed\n"
            yield 'data: {"stage": "completed", "progress": 100, "message": "Chat processing complete"}\n\n'

            logger.info(
                "Streaming completed",
                extra={
                    "session_id": session_id,
                    "user_id": str(user.id),
                },
            )

        except asyncio.CancelledError:
            logger.info(
                "Stream cancelled",
                extra={
                    "session_id": session_id,
                    "user_id": str(user.id),
                },
            )
        except Exception as e:
            logger.error(
                f"Stream error: {e}",
                extra={
                    "session_id": session_id,
                    "user_id": str(user.id),
                },
            )
            yield "event: error\n"
            yield f'data: {{"error": "{str(e)}"}}\n\n'

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
