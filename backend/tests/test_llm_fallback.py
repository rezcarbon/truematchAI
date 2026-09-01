"""LLM failover: when Anthropic fails, route to the MiniMax backup (if configured)."""
from __future__ import annotations

import pytest

from app.engines import client
from app.engines.client import (
    LLMError,
    call_claude,
    call_claude_json,
    extract_text_from_image,
    stream_claude,
)
from app.engines.providers import minimax


def test_json_fails_over_to_minimax(monkeypatch):
    # Primary (Anthropic) hard-fails after retries.
    def _boom(*a, **k):
        raise LLMError("credit balance too low")

    monkeypatch.setattr(client, "_anthropic_json", _boom)
    monkeypatch.setattr(minimax, "is_configured", lambda: True)
    monkeypatch.setattr(
        minimax, "complete_json",
        lambda **k: {"score": 77, "served_by": "minimax"},
    )
    out = call_claude_json(system="s", user_content="u")
    assert out["served_by"] == "minimax" and out["score"] == 77


def test_json_no_fallback_when_unconfigured(monkeypatch):
    monkeypatch.setattr(client, "_anthropic_json", lambda *a, **k: (_ for _ in ()).throw(LLMError("down")))
    monkeypatch.setattr(minimax, "is_configured", lambda: False)
    with pytest.raises(LLMError):
        call_claude_json(system="s", user_content="u")


def test_json_raises_when_both_rails_fail(monkeypatch):
    monkeypatch.setattr(client, "_anthropic_json", lambda *a, **k: (_ for _ in ()).throw(LLMError("down")))
    monkeypatch.setattr(minimax, "is_configured", lambda: True)

    def _backup_boom(**k):
        raise minimax.MiniMaxError("backup down too")

    monkeypatch.setattr(minimax, "complete_json", _backup_boom)
    with pytest.raises(LLMError, match="both failed"):
        call_claude_json(system="s", user_content="u")


def test_open_circuit_fails_over_to_minimax(monkeypatch):
    """An OPEN circuit raises CircuitBreakerError (not LLMError); _create_with_retry
    must normalise it to LLMError so failover still triggers."""
    from app.core.resilience import CircuitBreakerError

    def _open(*a, **k):
        raise CircuitBreakerError("Claude API")

    monkeypatch.setattr(client._claude_breaker, "call", _open)
    monkeypatch.setattr(minimax, "is_configured", lambda: True)
    monkeypatch.setattr(minimax, "complete_json", lambda **k: {"served_by": "minimax_after_open_circuit"})
    out = call_claude_json(system="s", user_content="u")
    assert out["served_by"] == "minimax_after_open_circuit"


def test_text_fails_over_to_minimax(monkeypatch):
    def _boom(*a, **k):
        raise LLMError("outage")

    monkeypatch.setattr(client, "_create_with_retry", _boom)
    monkeypatch.setattr(minimax, "is_configured", lambda: True)
    monkeypatch.setattr(minimax, "complete_text", lambda **k: "backup text")
    assert call_claude(system="s", user_content="u") == "backup text"


class _Blk:
    def __init__(self, inp):
        self.type = "tool_use"
        self.input = inp


class _Resp:
    def __init__(self, inp, stop):
        self.content = [_Blk(inp)]
        self.stop_reason = stop


def test_truncated_empty_tooluse_retries_with_more_tokens(monkeypatch):
    """A max_tokens-truncated empty {} tool result must NOT be returned — it must
    fall through to the larger-budget retry (the parse_resume empty bug)."""
    calls = {"n": 0}

    def fake(**k):
        calls["n"] += 1
        if calls["n"] == 1:
            return _Resp({}, "max_tokens")            # truncated → empty args
        return _Resp({"data": {"skills": ["python"]}}, "end_turn")  # full result

    monkeypatch.setattr(client, "_create_with_retry", fake)
    monkeypatch.setattr(minimax, "is_configured", lambda: False)
    out = call_claude_json(system="s", user_content="u", max_tokens=100)
    assert out == {"skills": ["python"]}
    assert calls["n"] == 2  # proved it retried instead of returning {}


def test_minimax_parses_forced_tool_call(monkeypatch):
    """The backup must read the forced emit_result tool call's `data`."""
    fake = {
        "choices": [
            {
                "message": {
                    "tool_calls": [
                        {"function": {"name": "emit_result", "arguments": '{"data": {"ok": true}}'}}
                    ]
                }
            }
        ]
    }
    monkeypatch.setattr(minimax, "_post", lambda payload: fake)
    out = minimax.complete_json(system="s", user_content="u")
    assert out == {"ok": True}


def test_minimax_falls_back_to_content_json(monkeypatch):
    """If the model answers in content despite tool_choice, tolerate it."""
    fake = {"choices": [{"message": {"content": '```json\n{"data": 1, "x": 2}\n```'}}]}
    monkeypatch.setattr(minimax, "_post", lambda payload: fake)
    out = minimax.complete_json(system="s", user_content="u")
    assert out["x"] == 2


# --- vision + streaming failover -------------------------------------------


def test_vision_fails_over_to_minimax(monkeypatch):
    def _boom(*a, **k):
        raise LLMError("vision credit error")

    monkeypatch.setattr(client, "_create_with_retry", _boom)
    monkeypatch.setattr(minimax, "is_configured", lambda: True)
    monkeypatch.setattr(minimax, "transcribe_image", lambda b64, mt, mx=2048: "BACKUP TRANSCRIPT")
    assert extract_text_from_image("b64", "image/png") == "BACKUP TRANSCRIPT"


def test_stream_fails_over_before_first_token(monkeypatch):
    # Primary stream raises immediately (no tokens yielded yet).
    from anthropic import APIConnectionError

    def _raise_stream(*a, **k):
        raise APIConnectionError(request=None)

    monkeypatch.setattr(client, "get_client", lambda: type("C", (), {"messages": type("M", (), {"stream": staticmethod(_raise_stream)})()})())
    monkeypatch.setattr(minimax, "is_configured", lambda: True)
    monkeypatch.setattr(minimax, "stream_text", lambda **k: iter(["he", "llo"]))
    out = "".join(stream_claude(system="s", user_content="u"))
    assert out == "hello"


def test_stream_does_not_failover_after_tokens(monkeypatch):
    """If the primary already streamed text, we must NOT fail over (would
    duplicate output) — it re-raises instead."""
    from anthropic import APIConnectionError

    class _Stream:
        text_stream = property(lambda self: self._gen())

        def _gen(self):
            yield "partial "
            raise APIConnectionError(request=None)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(
        client, "get_client",
        lambda: type("C", (), {"messages": type("M", (), {"stream": staticmethod(lambda **k: _Stream())})()})(),
    )
    backup_called = {"n": 0}
    monkeypatch.setattr(minimax, "is_configured", lambda: True)
    monkeypatch.setattr(minimax, "stream_text", lambda **k: backup_called.__setitem__("n", 1) or iter(["X"]))

    got = []
    with pytest.raises(LLMError):
        for piece in stream_claude(system="s", user_content="u"):
            got.append(piece)
    assert got == ["partial "]        # primary tokens delivered
    assert backup_called["n"] == 0     # backup NOT invoked mid-stream
