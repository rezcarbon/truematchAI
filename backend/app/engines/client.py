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
from app.core.resilience import CircuitBreaker
from app.engines.providers import minimax

logger = logging.getLogger("truematch.claude")

_PLACEHOLDER_KEYS = {"", "sk-ant-placeholder", "change-me", "placeholder"}

# Retry policy for transient API failures (network blips, rate limits, 5xx).
# Kept low so a genuine outage fails over to the backup quickly rather than
# burning N × timeout before the circuit opens.
_MAX_ATTEMPTS = 2
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


# Circuit breaker for Claude API resilience
_claude_breaker = CircuitBreaker(
    service_name="Claude API",
    failure_threshold=50,
    recovery_timeout=60,
    expected_exception=LLMError
)


def _create_with_retry(**kwargs: Any):
    """Create a Claude API message with retry logic and circuit breaker protection."""
    def _attempt_create():
        last_exc_inner: Exception | None = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                _started = time.monotonic()
                response = get_client().messages.create(**kwargs)
                # Record token usage + cost + latency centrally (all
                # non-streaming calls funnel through here).
                try:
                    from app.core.llm_usage import record_usage, record_latency
                    model = kwargs.get("model", "")
                    record_usage(model, getattr(response, "usage", None))
                    record_latency(model, time.monotonic() - _started)
                except Exception:  # noqa: BLE001 — accounting must never break a call
                    pass
                return response
            except (RateLimitError, APIConnectionError) as exc:
                last_exc_inner = exc
            except APIStatusError as exc:
                # Retry only server-side (5xx); client errors (4xx) are not transient.
                if exc.status_code < 500:
                    error_detail = str(exc)
                    if hasattr(exc, 'response') and hasattr(exc.response, 'json'):
                        try:
                            error_json = exc.response.json()
                            error_detail = f"{exc.status_code}: {error_json}"
                        except Exception:
                            pass
                    logger.error(f"Claude API 4xx error: {error_detail}")
                    raise LLMError(f"Claude API client error ({exc.status_code}): {error_detail}") from exc
                last_exc_inner = exc
            if attempt < _MAX_ATTEMPTS:
                # Deterministic backoff (no jitter — Math.random is unavailable and
                # repeatability aids debugging).
                time.sleep(_BASE_BACKOFF_SECONDS * attempt)
        raise LLMError("Claude API call failed after retries.") from last_exc_inner

    # Wrap with circuit breaker to prevent cascade failures
    try:
        return _claude_breaker.call(_attempt_create)
    except Exception as exc:
        error_msg = str(exc)
        if hasattr(exc, 'response'):
            error_msg += f" | Response: {exc.response}"
        logger.error(f"Claude API call failed (circuit: {_claude_breaker.state.value}): {error_msg}")
        # Normalise EVERY primary-path failure to LLMError — including the
        # circuit-breaker-OPEN rejection (a CircuitBreakerError) — so the
        # MiniMax failover, which catches LLMError, triggers uniformly. Without
        # this, an open circuit fails the call instead of failing over.
        if isinstance(exc, LLMError):
            raise
        raise LLMError(error_msg) from exc


def _build_system(system: str, cache_system: bool) -> list[dict[str, Any]]:
    if not system:
        return []

    blocks: list[dict[str, Any]] = [{"type": "text", "text": system}]
    # Only add cache control if system text is non-empty (Claude API requirement)
    if cache_system:
        blocks[0]["cache_control"] = {"type": "ephemeral"}
    return blocks


def extract_text_from_image(image_b64: str, media_type: str, max_tokens: int = 2048) -> str:
    """Transcribe the text content of an image (photo/scan of a resume or JD)
    using Claude vision. Returns the extracted plain text.

    Multimodal intake: lets a user snap a photo of a printed CV/JD instead of
    uploading a file. Raises LLMError on failure so callers can fall back.
    """
    try:
        response = _create_with_retry(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            temperature=0.0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "Transcribe ALL text visible in this document image "
                                "verbatim, preserving structure (headings, bullet "
                                "points, sections). Output only the transcribed text "
                                "with no commentary."
                            ),
                        },
                    ],
                }
            ],
        )
        return "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip()
    except LLMError as primary_exc:
        if not minimax.is_configured():
            raise
        logger.warning("Primary vision failed (%s) — failing over to MiniMax (vision).", primary_exc)
        try:
            return minimax.transcribe_image(image_b64, media_type, max_tokens)
        except Exception as backup_exc:  # noqa: BLE001
            raise LLMError(
                f"Primary and MiniMax backup both failed (vision): {primary_exc} | {backup_exc}"
            ) from backup_exc


def call_claude_with_tools(
    *,
    system: str,
    user_content: str,
    tools: list[dict[str, Any]],
    history: list[dict[str, Any]] | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.2,
    cache_system: bool = True,
) -> tuple[str, list[dict[str, Any]]]:
    """Invoke Claude with tool-use enabled (the model decides whether to call).

    Returns ``(text, tool_calls)`` where ``text`` is the assistant's natural
    language reply (possibly empty when it only emits tool calls) and
    ``tool_calls`` is a list of ``{"id", "name", "input"}`` dicts — one per
    tool_use block the model produced. The caller is responsible for executing
    or queueing those calls; this function never executes them.
    """
    messages: list[dict[str, Any]] = []
    for turn in (history or []):
        role = turn.get("role", "user")
        content = turn.get("content", "")
        if content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_content})

    response = _create_with_retry(
        model=settings.anthropic_model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=_build_system(system, cache_system),
        tools=tools,
        messages=messages,
    )

    text_parts: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    for block in response.content:
        btype = getattr(block, "type", None)
        if btype == "text":
            text_parts.append(block.text)
        elif btype == "tool_use":
            tool_calls.append(
                {"id": block.id, "name": block.name, "input": block.input}
            )
    return "".join(text_parts).strip(), tool_calls


def stream_claude(
    *,
    system: str,
    user_content: str,
    history: list[dict[str, Any]] | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.2,
    cache_system: bool = True,
):
    """Yield assistant text deltas as they are generated (token streaming).

    A thin generator wrapper over the SDK streaming API. Yields plain text
    chunks; intended to be consumed and forwarded as SSE. Raises LLMError on a
    terminal failure so callers can emit an error event.
    """
    messages: list[dict[str, Any]] = []
    for turn in (history or []):
        role = turn.get("role", "user")
        content = turn.get("content", "")
        if content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_content})

    yielded = False
    primary_exc: Exception | None = None
    try:
        with get_client().messages.stream(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=_build_system(system, cache_system),
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yielded = True
                yield text
            try:
                from app.core.llm_usage import record_usage
                record_usage(settings.anthropic_model, getattr(stream.get_final_message(), "usage", None))
            except Exception:  # noqa: BLE001
                pass
        return
    except (RateLimitError, APIConnectionError, APIStatusError) as exc:
        primary_exc = exc

    # Only safe to fail over if NOTHING was streamed yet — otherwise switching
    # providers mid-stream would duplicate already-sent text to the client.
    if yielded or not minimax.is_configured():
        raise LLMError(f"Claude streaming failed: {primary_exc}") from primary_exc
    logger.warning(
        "Primary stream failed before first token (%s) — failing over to MiniMax (stream).",
        primary_exc,
    )
    try:
        for piece in minimax.stream_text(
            system=system, user_content=user_content,
            max_tokens=max_tokens, temperature=temperature,
        ):
            yield piece
    except Exception as backup_exc:  # noqa: BLE001
        raise LLMError(
            f"Primary and MiniMax backup both failed (stream): {primary_exc} | {backup_exc}"
        ) from backup_exc


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
    try:
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
    except LLMError as primary_exc:
        if not minimax.is_configured():
            raise
        logger.warning("Primary LLM failed (%s) — failing over to MiniMax (text).", primary_exc)
        try:
            text = minimax.complete_text(
                system=system, user_content=user_content,
                max_tokens=max_tokens, temperature=temperature,
            )
            logger.info("MiniMax backup served a text call.")
            return text
        except Exception as backup_exc:  # noqa: BLE001
            raise LLMError(
                f"Primary and MiniMax backup both failed: {primary_exc} | {backup_exc}"
            ) from backup_exc


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


def select_model(call_class: str = "primary") -> str:
    """Budget-aware model routing.

    - "primary" (capability verdicts, counter-rec, chat) → always the full model.
    - "secondary" (trajectory, JD interrogation, summaries) → the fast model when
      economy mode is on OR the day's spend has crossed the soft budget line.

    The system degrades along a cost gradient instead of falling off a cliff:
    full model → fast model for secondary work → (at key/credit failure) the
    existing tagged-mock floor.
    """
    if call_class != "secondary":
        return settings.anthropic_model
    if settings.llm_economy_mode:
        return settings.anthropic_fast_model
    budget = settings.llm_daily_budget_usd
    if budget > 0:
        from app.core.llm_usage import day_spend_usd

        if day_spend_usd() >= budget * settings.llm_budget_soft_ratio:
            logger.info(
                "Budget routing: secondary reasoning downshifted to fast model",
                extra={"day_spend_usd": round(day_spend_usd(), 4), "budget_usd": budget},
            )
            return settings.anthropic_fast_model
    return settings.anthropic_model


def _anthropic_json(
    system: str, user_content: str, max_tokens: int, temperature: float,
    cache_system: bool, model: str | None,
) -> dict[str, Any]:
    system_blocks = _build_system(system, cache_system)
    messages = [{"role": "user", "content": user_content}]
    tokens = max_tokens
    last_error: Exception | None = None
    for _ in range(3):
        response = _create_with_retry(
            model=model or settings.anthropic_model,
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
                result = data if isinstance(data, dict) else block.input
                # Only accept a NON-EMPTY result. An empty {} with
                # stop_reason=="max_tokens" means the model was truncated before
                # it finished writing the tool arguments — fall through to retry
                # with a larger budget rather than returning nothing.
                if result:
                    return result
        # No usable (non-empty) tool_use block. If truncated, give it more room.
        last_error = LLMError("Claude did not return a structured tool result.")
        if getattr(response, "stop_reason", None) != "max_tokens" or tokens >= 8192:
            break
        tokens = min(tokens * 2, 8192)
    raise LLMError("Claude did not return a structured tool result.") from last_error


def call_claude_json(
    *,
    system: str,
    user_content: str,
    max_tokens: int = 2048,
    temperature: float = 0.0,
    cache_system: bool = True,
    model: str | None = None,
) -> dict[str, Any]:
    """Invoke the LLM and return a structured JSON object via FORCED TOOL USE.

    Primary: Anthropic (the model must call `emit_result`; the SDK returns
    parsed JSON, so there is no fragile string-parsing). Truncated output is
    retried with a larger token budget.

    Failover: if the Anthropic call fails after retries (credit exhaustion,
    outage, open circuit) AND MiniMax is configured, the same request is retried
    against MiniMax with OpenAI-style forced tool use — preserving the structured
    guarantee. The backup is a no-op when unconfigured (Anthropic errors surface
    as before).
    """
    try:
        return _anthropic_json(system, user_content, max_tokens, temperature, cache_system, model)
    except LLMError as primary_exc:
        if not minimax.is_configured():
            raise
        logger.warning("Primary LLM failed (%s) — failing over to MiniMax (structured).", primary_exc)
        try:
            result = minimax.complete_json(
                system=system, user_content=user_content,
                max_tokens=max_tokens, temperature=temperature,
            )
            logger.info("MiniMax backup served a structured call.")
            return result
        except Exception as backup_exc:  # noqa: BLE001 — both rails down
            raise LLMError(
                f"Primary and MiniMax backup both failed: {primary_exc} | {backup_exc}"
            ) from backup_exc


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
