"""Google Cloud Vertex AI (Gemini 2.5) client wrapper.

Provides a unified interface to Google's Gemini models via Vertex AI API.
Used as optional secondary routing for cost optimization (Gemini Flash ~60% cheaper
than Claude Sonnet) and as a fallback when Claude fails.

Structured output via forced tool use (OpenAI-compatible format).
Streaming via Server-Sent Events.
Graceful degradation when unconfigured or unavailable.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.config import settings

logger = logging.getLogger("truematch.gemini")

_PLACEHOLDER_KEYS = {"", "placeholder", "change-me"}


def is_configured() -> bool:
    """True when Gemini is enabled and GCP project is set."""
    return (
        settings.gemini_enabled
        and settings.gemini_configured
        and bool(settings.gemini_project_id.strip())
    )


def _get_client():
    """Lazy-load Vertex AI client (import only when needed)."""
    if not is_configured():
        return None
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel, Tool, ToolConfig

        vertexai.init(project=settings.gemini_project_id, location=settings.gemini_region)
        return GenerativeModel, Tool, ToolConfig
    except ImportError:
        logger.error("google-cloud-vertexai not installed. Install: pip install google-cloud-vertexai")
        return None


class GeminiError(RuntimeError):
    """Raised when a Gemini call cannot be completed or parsed."""


def complete_text(
    system: str,
    user_content: str,
    max_tokens: int = 2048,
    temperature: float = 0.2,
) -> str:
    """Invoke Gemini and return concatenated text response.

    Args:
        system: System prompt (instruction context)
        user_content: User message
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0.0-1.0)

    Returns:
        The text response (concatenated if multiple parts)

    Raises:
        GeminiError: On API failure or parsing error
    """
    if not is_configured():
        raise GeminiError("Gemini is not configured (gemini_enabled=False or project_id unset)")

    try:
        from vertexai.generative_models import GenerativeModel

        model = GenerativeModel(settings.gemini_secondary_model)

        messages = []
        if system:
            messages.append({"role": "user", "parts": [{"text": system}]})
            messages.append({"role": "model", "parts": [{"text": "Understood."}]})
        messages.append({"role": "user", "parts": [{"text": user_content}]})

        response = model.generate_content(
            messages,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            },
            safety_settings=[],  # Allow all content (governance handled upstream)
        )

        text_parts = []
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                text_parts.append(part.text)

        return "".join(text_parts).strip()
    except Exception as exc:
        logger.error(f"Gemini text completion failed: {exc}")
        raise GeminiError(f"Gemini text completion failed: {exc}") from exc


def complete_json(
    system: str,
    user_content: str,
    max_tokens: int = 2048,
    temperature: float = 0.0,
) -> dict[str, Any]:
    """Invoke Gemini and return structured JSON via forced tool use.

    Uses Gemini's function calling (equivalent to Claude's tool_use) to force
    a structured output. The model must call the emit_result tool with the JSON.

    Args:
        system: System prompt (instruction context)
        user_content: User message
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0.0-1.0)

    Returns:
        Parsed JSON dict (from the tool input)

    Raises:
        GeminiError: On API failure, parsing error, or no tool call
    """
    if not is_configured():
        raise GeminiError("Gemini is not configured")

    try:
        from vertexai.generative_models import GenerativeModel, Tool, ToolConfig

        # Define the emit_result function (schema matching Claude's forced tool)
        emit_result_tool = Tool.from_google_cloud_function({
            "type": "OBJECT",
            "properties": {
                "data": {
                    "type": "OBJECT",
                    "description": "The complete result object exactly as the instructions specify.",
                }
            },
            "required": ["data"],
        })

        model = GenerativeModel(
            settings.gemini_secondary_model,
            tools=[emit_result_tool],
            tool_config=ToolConfig(
                function_calling_config=ToolConfig.FunctionCallingConfig.AUTO
            ),
        )

        messages = []
        if system:
            messages.append({"role": "user", "parts": [{"text": system}]})
            messages.append({"role": "model", "parts": [{"text": "Understood."}]})
        messages.append({"role": "user", "parts": [{"text": user_content}]})

        response = model.generate_content(
            messages,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            },
            safety_settings=[],
        )

        # Extract tool call result
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'function_call'):
                tool_input = part.function_call.args
                data = tool_input.get("data", tool_input)
                if isinstance(data, dict) and data:
                    return data

        raise GeminiError("Gemini did not return a structured tool result (function call)")
    except GeminiError:
        raise
    except Exception as exc:
        logger.error(f"Gemini JSON completion failed: {exc}")
        raise GeminiError(f"Gemini JSON completion failed: {exc}") from exc


def stream_text(
    system: str,
    user_content: str,
    max_tokens: int = 1024,
    temperature: float = 0.2,
):
    """Yield assistant text deltas as they are generated (token streaming).

    A generator wrapper over Vertex AI streaming API. Yields plain text chunks;
    intended to be consumed and forwarded as SSE.

    Args:
        system: System prompt
        user_content: User message
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature

    Yields:
        Text chunks as they are generated

    Raises:
        GeminiError: On API failure (only after first token attempt)
    """
    if not is_configured():
        raise GeminiError("Gemini is not configured")

    try:
        from vertexai.generative_models import GenerativeModel

        model = GenerativeModel(settings.gemini_secondary_model)

        messages = []
        if system:
            messages.append({"role": "user", "parts": [{"text": system}]})
            messages.append({"role": "model", "parts": [{"text": "Understood."}]})
        messages.append({"role": "user", "parts": [{"text": user_content}]})

        response = model.generate_content(
            messages,
            stream=True,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            },
            safety_settings=[],
        )

        for chunk in response:
            for part in chunk.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    yield part.text
    except Exception as exc:
        logger.error(f"Gemini streaming failed: {exc}")
        raise GeminiError(f"Gemini streaming failed: {exc}") from exc


def transcribe_image(image_b64: str, media_type: str, max_tokens: int = 2048) -> str:
    """Transcribe text content of an image using Gemini vision.

    Used as vision fallback when Claude vision fails. Supports JPG, PNG, GIF, WebP.

    Args:
        image_b64: Base64-encoded image data
        media_type: MIME type (e.g., "image/jpeg")
        max_tokens: Maximum tokens in response

    Returns:
        Extracted text from the image

    Raises:
        GeminiError: On API failure or parsing error
    """
    if not is_configured():
        raise GeminiError("Gemini is not configured")

    try:
        from vertexai.generative_models import GenerativeModel, Part
        import base64

        model = GenerativeModel(settings.gemini_secondary_model)

        # Decode base64 and create inline data
        image_bytes = base64.b64decode(image_b64)

        # Map media type to Gemini format
        mime_to_gemini = {
            "image/jpeg": "image/jpeg",
            "image/png": "image/png",
            "image/gif": "image/gif",
            "image/webp": "image/webp",
        }
        gemini_mime = mime_to_gemini.get(media_type, "image/jpeg")

        response = model.generate_content(
            [
                Part.from_data(data=image_bytes, mime_type=gemini_mime),
                {
                    "text": (
                        "Transcribe ALL text visible in this document image "
                        "verbatim, preserving structure (headings, bullet "
                        "points, sections). Output only the transcribed text "
                        "with no commentary."
                    )
                },
            ],
            generation_config={"max_output_tokens": max_tokens, "temperature": 0.0},
            safety_settings=[],
        )

        text_parts = []
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                text_parts.append(part.text)

        return "".join(text_parts).strip()
    except Exception as exc:
        logger.error(f"Gemini vision transcription failed: {exc}")
        raise GeminiError(f"Gemini vision transcription failed: {exc}") from exc
