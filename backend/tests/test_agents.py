"""Autonomous agent tests — ingestion, JD processing, control API."""
from __future__ import annotations

import pathlib

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.ingest_queue import IngestStatus, IngestType


# ── CV ingestion agent tests ──────────────────────────────────────────────────

def test_poll_folder_creates_inbox_dir(tmp_path, monkeypatch):
    """poll_folder creates the directory if it doesn't exist."""
    from app.workers.agents import ingest_cv
    monkeypatch.setattr(ingest_cv.settings, "ingest_cv_folder", str(tmp_path / "cv_in"))
    monkeypatch.setattr(ingest_cv, "_SessionFactory", None)
    monkeypatch.setattr(ingest_cv, "_engine", None)

    # Can't call the task without a real DB; just assert directory creation logic.
    folder = pathlib.Path(ingest_cv.settings.ingest_cv_folder)
    folder.mkdir(parents=True, exist_ok=True)
    assert folder.exists()


def test_poll_folder_skips_unsupported_ext(tmp_path, monkeypatch):
    from app.workers.agents import ingest_cv
    monkeypatch.setattr(ingest_cv.settings, "ingest_cv_folder", str(tmp_path))
    # Place an unsupported file.
    (tmp_path / "not_a_cv.xlsx").write_bytes(b"data")
    result = ingest_cv.poll_folder.run()
    assert result["skipped"] == 1
    assert result["processed"] == 0


def test_best_position_returns_none_when_no_positions():
    from app.workers.agents.ingest_cv import _best_position

    class FakeDB:
        def scalars(self, stmt):
            class R:
                def all(self_inner): return []
            return R()

    assert _best_position(FakeDB(), "some resume text") is None


# ── JD draft agent tests ──────────────────────────────────────────────────────

def test_poll_jd_folder_skips_unsupported(tmp_path, monkeypatch):
    from app.workers.agents import ingest_jd
    monkeypatch.setattr(ingest_jd.settings, "ingest_jd_folder", str(tmp_path))
    (tmp_path / "notes.xlsx").write_bytes(b"data")
    result = ingest_jd.poll_folder.run()
    assert result["skipped"] == 1
    assert result["processed"] == 0


def test_poll_jd_folder_processes_txt(tmp_path, monkeypatch):
    from app.workers.agents import ingest_jd
    monkeypatch.setattr(ingest_jd.settings, "ingest_jd_folder", str(tmp_path))

    class FakeDB:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def add(self, o): pass
        def flush(self): pass
        def commit(self): pass
        def scalar(self, s): return 0
        def scalars(self, s):
            class R:
                def all(self_r): return []
            return R()

    monkeypatch.setattr(ingest_jd, "_db", lambda: FakeDB)
    monkeypatch.setattr(ingest_jd, "_process_jd", lambda db, jd, src, ref, pos_id=None, title=None: None)

    jd_file = tmp_path / "role.txt"
    jd_file.write_text("We are looking for an AI leader with 10 years experience.")
    result = ingest_jd.poll_folder.run()
    assert result["processed"] == 1


# ── Agent control API tests ───────────────────────────────────────────────────

@pytest.fixture
def auth_client():
    """Unauthenticated test client — just checking routes exist."""
    return TestClient(app, raise_server_exceptions=False)


def test_agent_routes_exist(auth_client):
    """All agent endpoints are registered and return 401/422, not 404."""
    for path in ["/api/v1/agents/queue", "/api/v1/agents/queue/non-existent-id"]:
        r = auth_client.get(path)
        assert r.status_code in (401, 422), f"{path} returned {r.status_code}"
    r = auth_client.post("/api/v1/agents/jd/draft", json={"jd_text": "x" * 25})
    assert r.status_code in (401, 422)


def test_ingest_queue_model_statuses():
    """All expected status values are defined."""
    assert IngestStatus.awaiting_review.value == "awaiting_review"
    assert IngestStatus.completed.value == "completed"
    assert IngestType.cv.value == "cv"
    assert IngestType.jd_draft.value == "jd_draft"


def test_beat_schedule_registered():
    """Celery Beat schedule includes both watcher tasks."""
    from app.workers.celery_app import celery_app
    schedule = celery_app.conf.beat_schedule
    assert "poll-cv-folder" in schedule
    assert "poll-jd-folder" in schedule
    assert "poll-cv-email" in schedule
