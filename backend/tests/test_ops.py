"""Ops/observability tests (A6): readiness, rate limiting, request id."""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import health, ratelimit
from app.core.ratelimit import RateLimitMiddleware


@pytest.mark.asyncio
async def test_readiness_reports_components(monkeypatch):
    async def _ok():
        return True

    async def _bad():
        return False

    monkeypatch.setattr(health, "check_db", _ok)
    monkeypatch.setattr(health, "check_redis", _bad)
    monkeypatch.setattr(health, "check_s3", _ok)
    monkeypatch.setattr(health, "check_llm", _ok)
    monkeypatch.setattr(health, "check_singpass", _ok)
    ready, components = await health.readiness()
    assert ready is False
    assert components == {
        "database": True,
        "redis": False,
        "s3": True,
        "llm": True,
        "singpass": True,
    }


@pytest.mark.asyncio
async def test_readiness_all_ok(monkeypatch):
    async def _ok():
        return True

    monkeypatch.setattr(health, "check_db", _ok)
    monkeypatch.setattr(health, "check_redis", _ok)
    monkeypatch.setattr(health, "check_s3", _ok)
    monkeypatch.setattr(health, "check_llm", _ok)
    monkeypatch.setattr(health, "check_singpass", _ok)
    ready, components = await health.readiness()
    assert ready is True


def _rate_limited_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/x")
    async def x():
        return {"ok": True}

    @app.get("/livez")
    async def livez():
        return {"ok": True}

    return app


def test_rate_limit_returns_429(monkeypatch):
    monkeypatch.setattr(ratelimit.settings, "rate_limit_enabled", True)
    monkeypatch.setattr(ratelimit.settings, "rate_limit_per_minute", 3)
    monkeypatch.setattr(ratelimit, "_redis", lambda: None)  # force in-memory path
    ratelimit._memory.clear()

    client = TestClient(_rate_limited_app())
    codes = [client.get("/x").status_code for _ in range(5)]
    assert codes.count(200) == 3
    assert codes[-1] == 429
    # 429 carries a Retry-After header
    assert "retry-after" in {k.lower() for k in client.get("/x").headers}


def test_rate_limit_exempts_probes(monkeypatch):
    monkeypatch.setattr(ratelimit.settings, "rate_limit_enabled", True)
    monkeypatch.setattr(ratelimit.settings, "rate_limit_per_minute", 1)
    monkeypatch.setattr(ratelimit, "_redis", lambda: None)
    ratelimit._memory.clear()

    client = TestClient(_rate_limited_app())
    # /livez is exempt: never rate limited
    assert all(client.get("/livez").status_code == 200 for _ in range(5))


def test_livez_and_request_id_header():
    from app.main import app

    client = TestClient(app)
    resp = client.get("/livez")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert resp.headers.get("X-Request-ID")
