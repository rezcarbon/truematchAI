"""Speech-to-text for audio resume intake.

Claude does not accept audio input, so transcription uses an external provider
(the de-facto-standard Whisper HTTP API). Gated exactly like enrichment / push
/ email / S3: when no provider credential is configured the call raises so the
endpoint can return a clean 503 — never a fabricated transcript.
"""
from __future__ import annotations

import logging

from app.config import settings

logger = logging.getLogger("truematch.transcription")


class TranscriptionError(RuntimeError):
    """Raised when transcription is unavailable or the provider call fails."""


def is_configured() -> bool:
    return settings.transcription_configured


def transcribe_audio(audio_bytes: bytes, filename: str, content_type: str) -> str:
    """Return the transcript of a spoken-resume audio file.

    Raises TranscriptionError when no provider is configured or the provider
    request fails. The caller maps this to a 503/502 rather than guessing.
    """
    if not settings.transcription_configured:
        raise TranscriptionError("No speech-to-text provider is configured.")

    provider = settings.transcription_provider.lower()
    if provider == "openai":
        return _transcribe_openai(audio_bytes, filename, content_type)
    raise TranscriptionError(f"Unsupported transcription provider: {provider!r}")


def _transcribe_openai(audio_bytes: bytes, filename: str, content_type: str) -> str:
    """Whisper transcription via the OpenAI-compatible HTTP API.

    Uses multipart/form-data exactly as the provider expects; no SDK dependency
    so this works on the same lean runtime as the rest of the engines.
    """
    import httpx

    url = f"{settings.transcription_api_base.rstrip('/')}/audio/transcriptions"
    files = {"file": (filename or "audio", audio_bytes, content_type or "application/octet-stream")}
    data = {"model": settings.transcription_model, "response_format": "text"}
    headers = {"Authorization": f"Bearer {settings.transcription_api_key}"}
    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, headers=headers, files=files, data=data)
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.warning("Transcription provider returned %s", exc.response.status_code)
        raise TranscriptionError(
            f"Transcription provider error ({exc.response.status_code})."
        ) from exc
    except httpx.HTTPError as exc:  # network/timeout
        raise TranscriptionError(f"Transcription request failed: {exc}") from exc

    # response_format=text yields a bare transcript; tolerate JSON too.
    body = resp.text.strip()
    if body.startswith("{"):
        try:
            return (resp.json().get("text") or "").strip()
        except Exception:  # noqa: BLE001
            return body
    return body
