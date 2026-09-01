"""MiniMax backup provider (OpenAI-compatible Chat Completions).

Used only as failover when the primary Anthropic call fails. Preserves the
structured-output guarantee via OpenAI-style forced tool use: the model is
required to call ``emit_result`` and we read its parsed ``data`` argument. If a
given MiniMax model declines forced tool choice, we fall back to a tolerant
JSON parse of the message content — still far better than a hard failure on the
backup path.

Kept dependency-light (httpx only) and self-contained (no import of the
Anthropic client) to avoid coupling/circular imports.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger("truematch.minimax")


class MiniMaxError(RuntimeError):
    """Raised when the MiniMax backup call cannot be completed or parsed."""


def is_configured() -> bool:
    return settings.minimax_configured


_RESULT_FUNCTION = {
    "type": "function",
    "function": {
        "name": "emit_result",
        "description": "Return the structured result for this step.",
        "parameters": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": "The complete result object exactly as the instructions specify.",
                }
            },
            "required": ["data"],
        },
    },
}

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
# MiniMax-M2.x are REASONING models: they emit a <think>…</think> chain before
# the answer/tool call, which (a) must be stripped before parsing content and
# (b) consumes tokens — so structured calls need generous headroom or they get
# truncated mid-thought before ever reaching the tool call.
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_THINKING_FLOOR = 4096
_THINKING_CEIL = 8192


def _strip_think(text: str) -> str:
    return _THINK_RE.sub("", text or "").strip()


def _post(payload: dict) -> dict:
    url = settings.minimax_base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.minimax_api_key}",
        "Content-Type": "application/json",
    }
    try:
        with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
            resp = client.post(url, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        raise MiniMaxError(f"MiniMax request failed: {exc}") from exc
    if resp.status_code >= 400:
        raise MiniMaxError(f"MiniMax HTTP {resp.status_code}: {resp.text[:300]}")
    try:
        return resp.json()
    except ValueError as exc:
        raise MiniMaxError("MiniMax returned non-JSON body.") from exc


def _messages(system: str, user_content: str) -> list[dict]:
    msgs: list[dict] = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": user_content})
    return msgs


def _extract_json(text: str) -> dict[str, Any]:
    candidate = (text or "").strip()
    for attempt in (candidate, _fenced(candidate), _braced(candidate)):
        if not attempt:
            continue
        try:
            obj = json.loads(attempt, strict=False)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    raise MiniMaxError("MiniMax response could not be parsed as JSON.")


def _fenced(text: str) -> str | None:
    m = _FENCE_RE.search(text)
    return m.group(1) if m else None


def _braced(text: str) -> str | None:
    start, end = text.find("{"), text.rfind("}")
    return text[start : end + 1] if start != -1 and end > start else None


def complete_json(
    *, system: str, user_content: str, max_tokens: int = 2048, temperature: float = 0.0
) -> dict[str, Any]:
    """Structured JSON via forced tool use, with a tolerant text fallback.

    Reasoning-aware: gives the model headroom for its <think> chain and retries
    once with a larger budget if the first attempt is truncated mid-thought.
    """
    tokens = max(max_tokens, _THINKING_FLOOR)
    for _ in range(2):
        payload = {
            "model": settings.minimax_model,
            "messages": _messages(system, user_content),
            "max_tokens": tokens,
            "temperature": temperature,
            "tools": [_RESULT_FUNCTION],
            "tool_choice": {"type": "function", "function": {"name": "emit_result"}},
        }
        body = _post(payload)
        choice = (body.get("choices") or [{}])[0]
        message = choice.get("message") or {}

        # Preferred path: parse the forced tool call's arguments.
        for call in message.get("tool_calls") or []:
            fn = call.get("function") or {}
            if fn.get("name") == "emit_result" and fn.get("arguments"):
                try:
                    args = json.loads(fn["arguments"], strict=False)
                except json.JSONDecodeError:
                    continue
                data = args.get("data") if isinstance(args, dict) else None
                result = data if isinstance(data, dict) else (args if isinstance(args, dict) else {})
                if result:  # non-empty only; else fall through to retry-on-truncation
                    return result

        # Fallback: some replies put JSON in content (after a <think> block).
        content = message.get("content")
        if isinstance(content, str):
            cleaned = _strip_think(content)
            if cleaned:
                try:
                    return _extract_json(cleaned)
                except MiniMaxError:
                    pass

        # Truncated mid-thought before producing a result → retry with more room.
        if choice.get("finish_reason") == "length" and tokens < _THINKING_CEIL:
            tokens = min(tokens * 2, _THINKING_CEIL)
            continue
        break
    raise MiniMaxError("MiniMax did not return a usable structured result.")


def complete_text(
    *, system: str, user_content: str, max_tokens: int = 2048, temperature: float = 0.2
) -> str:
    """Plain-text completion (backup for non-structured calls)."""
    payload = {
        "model": settings.minimax_model,
        "messages": _messages(system, user_content),
        "max_tokens": max(max_tokens, _THINKING_FLOOR),
        "temperature": temperature,
    }
    body = _post(payload)
    choice = (body.get("choices") or [{}])[0]
    content = (choice.get("message") or {}).get("content")
    return _strip_think(content) if isinstance(content, str) else ""


def transcribe_image(image_b64: str, media_type: str, max_tokens: int = 2048) -> str:
    """Vision backup: transcribe document image text via a MiniMax VL model.

    Uses the OpenAI-compatible image_url content block with a base64 data URI.
    """
    payload = {
        "model": settings.minimax_vision_model,
        "max_tokens": max_tokens,
        "temperature": 0.0,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{image_b64}"},
                    },
                    {
                        "type": "text",
                        "text": (
                            "Transcribe ALL text visible in this document image "
                            "verbatim, preserving structure (headings, bullet points, "
                            "sections). Output only the transcribed text, no commentary."
                        ),
                    },
                ],
            }
        ],
    }
    body = _post(payload)
    choice = (body.get("choices") or [{}])[0]
    content = (choice.get("message") or {}).get("content")
    if isinstance(content, list):  # some VL responses return content blocks
        content = "".join(
            b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
        )
    return _strip_think(content) if isinstance(content, str) else ""


def stream_text(
    *, system: str, user_content: str, max_tokens: int = 1024, temperature: float = 0.2
):
    """Stream text deltas (backup for chat SSE). Yields plain text chunks.

    Parses the OpenAI-compatible SSE stream (`data: {...}` lines → delta.content).
    """
    url = settings.minimax_base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.minimax_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.minimax_model,
        "messages": _messages(system, user_content),
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
    }
    try:
        with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
            with client.stream("POST", url, headers=headers, json=payload) as resp:
                if resp.status_code >= 400:
                    resp.read()
                    raise MiniMaxError(f"MiniMax stream HTTP {resp.status_code}: {resp.text[:300]}")
                for line in resp.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = (chunk.get("choices") or [{}])[0].get("delta") or {}
                    piece = delta.get("content")
                    if isinstance(piece, str) and piece:
                        yield piece
    except httpx.HTTPError as exc:
        raise MiniMaxError(f"MiniMax stream failed: {exc}") from exc
