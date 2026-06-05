"""Anthropic Claude client wrapper.

Centralizes construction of the Anthropic client and thin helpers that apply
prompt caching to the (large, stable) system prompt, perform bounded retries on
transient errors, and parse strict-JSON responses robustly. Engine modules call
into these helpers rather than instantiating the SDK directly.
"""
from __future__ import annotations

import json
import logging
import re
import time
from functools import lru_cache
from typing import Any

from anthropic import Anthropic, APIConnectionError, APIStatusError, RateLimitError

from app.config import settings

logger = logging.getLogger("truematch.claude")

_PLACEHOLDER_KEYS = {"", "sk-ant-placeholder", "change-me", "placeholder"}

# Retry policy for transient API failures (network blips, rate limits, 5xx).
_MAX_ATTEMPTS = 3
_BASE_BACKOFF_SECONDS = 1.5


class LLMError(RuntimeError):
    """Raised when a live Claude call cannot be completed or parsed."""


def is_live() -> bool:
    """True when a real Anthropic API key is configured.

    When False, engines fall back to deterministic mock fixtures so the pipeline
    remains runnable in local/offline/test environments without a key. Production
    deployments MUST set a real ANTHROPIC_API_KEY.
    """
    if settings.llm_force_mock:
        return False
    return settings.anthropic_api_key.strip() not in _PLACEHOLDER_KEYS


@lru_cache
def get_client() -> Anthropic:
    return Anthropic(api_key=settings.anthropic_api_key, timeout=settings.llm_timeout_seconds)


def _create_with_retry(**kwargs: Any):
    last_exc: Exception | None = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            return get_client().messages.create(**kwargs)
        except (RateLimitError, APIConnectionError) as exc:
            last_exc = exc
        except APIStatusError as exc:
            # Retry only server-side (5xx); client errors (4xx) are not transient.
            if exc.status_code < 500:
                raise LLMError(f"Claude API client error ({exc.status_code}).") from exc
            last_exc = exc
        if attempt < _MAX_ATTEMPTS:
            # Deterministic backoff (no jitter — Math.random is unavailable and
            # repeatability aids debugging).
            time.sleep(_BASE_BACKOFF_SECONDS * attempt)
    raise LLMError("Claude API call failed after retries.") from last_exc


def _build_system(system: str, cache_system: bool) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = [{"type": "text", "text": system}]
    if cache_system:
        blocks[0]["cache_control"] = {"type": "ephemeral"}
    return blocks


def call_claude(
    *,
    system: str,
    user_content: str,
    max_tokens: int = 2048,
    temperature: float = 0.2,
    cache_system: bool = True,
) -> str:
    """Invoke Claude with an optionally cached system prompt.

    The system prompt is marked with `cache_control` so the stable, proprietary
    instruction block is cached across calls in the pipeline. Returns the
    concatenated text of the response content blocks.
    """
    response = _create_with_retry(
        model=settings.anthropic_model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=_build_system(system, cache_system),
        messages=[{"role": "user", "content": user_content}],
    )
    return "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )


_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _extract_json(text: str) -> dict[str, Any]:
    """Parse a JSON object from a model response, tolerating prose/code fences."""
    candidate = text.strip()
    # strict=False allows control characters (e.g. literal newlines/tabs) inside
    # string values — LLMs routinely emit multi-line narrative fields that strict
    # JSON rejects, so tolerate them rather than fail the whole assessment.
    # 1) Direct parse.
    try:
        return json.loads(candidate, strict=False)
    except json.JSONDecodeError:
        pass
    # 2) Fenced ```json ... ``` block.
    fence = _FENCE_RE.search(candidate)
    if fence:
        try:
            return json.loads(fence.group(1), strict=False)
        except json.JSONDecodeError:
            pass
    # 3) First balanced { ... } span.
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(candidate[start : end + 1], strict=False)
        except json.JSONDecodeError:
            pass
    raise LLMError("Claude response could not be parsed as JSON.")


_RESULT_TOOL = {
    "name": "emit_result",
    "description": "Return the structured assessment result for this step.",
    # The result is wrapped in a named `data` object. A bare `{"type":"object"}`
    # schema gets echoed back by the model; a named property makes it populate
    # the real structure (defined by the per-step system prompt) instead.
    # Forcing tool use makes the SDK return already-parsed JSON, eliminating
    # brace/quote/control-char/markdown parse failures entirely.
    "input_schema": {
        "type": "object",
        "properties": {
            "data": {
                "type": "object",
                "description": "The complete result object exactly as the instructions specify.",
            }
        },
        "required": ["data"],
    },
}


def call_claude_json(
    *,
    system: str,
    user_content: str,
    max_tokens: int = 2048,
    temperature: float = 0.0,
    cache_system: bool = True,
) -> dict[str, Any]:
    """Invoke Claude and return a structured JSON object via FORCED TOOL USE.

    The model is required to call `emit_result`; the SDK parses its input into a
    dict, so there is no fragile string-parsing of model prose. Truncated output
    (`stop_reason == "max_tokens"`) is retried with a larger token budget so
    content-rich inputs still produce a complete object.
    """
    system_blocks = _build_system(system, cache_system)
    messages = [{"role": "user", "content": user_content}]
    tokens = max_tokens
    last_error: Exception | None = None
    for _ in range(3):
        response = _create_with_retry(
            model=settings.anthropic_model,
            max_tokens=tokens,
            temperature=temperature,
            system=system_blocks,
            tools=[_RESULT_TOOL],
            tool_choice={"type": "tool", "name": "emit_result"},
            messages=messages,
        )
        for block in response.content:
            if getattr(block, "type", None) == "tool_use" and isinstance(block.input, dict):
                data = block.input.get("data")
                return data if isinstance(data, dict) else block.input
        # No usable tool_use block. If the output was truncated, give it more room.
        last_error = LLMError("Claude did not return a structured tool result.")
        if getattr(response, "stop_reason", None) != "max_tokens" or tokens >= 8192:
            break
        tokens = min(tokens * 2, 8192)
    raise LLMError("Claude did not return a structured tool result.") from last_error


class ClaudeClient:
    """Wrapper around Claude API for use in engine modules.

    Provides a simple interface for engines to call Claude for text and JSON generation.
    """

    def __init__(self, api_key: str | None = None):
        """Initialize with optional API key override (usually uses settings.anthropic_api_key)."""
        if api_key:
            # Temporarily override for this instance (rarely needed)
            self.api_key = api_key
        else:
            self.api_key = settings.anthropic_api_key

    def analyze(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.2,
        return_json: bool = False,
    ) -> str | dict[str, Any]:
        """Invoke Claude with the given prompt.

        Args:
            prompt: The user message/prompt to send to Claude
            system: System prompt (if empty, uses engine defaults)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)
            return_json: If True, parse response as JSON; otherwise return text

        Returns:
            Either a string (text response) or dict (if return_json=True)
        """
        try:
            if return_json:
                return call_claude_json(
                    system=system,
                    user_content=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            else:
                return call_claude(
                    system=system,
                    user_content=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
        except LLMError as e:
            logger.error("Claude API call failed: %s", e)
            raise
