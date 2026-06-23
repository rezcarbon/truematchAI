"""Tests for the Google Drive ingestion agent (app.workers.agents.ingest_drive).

Drive REST access is isolated in DriveClient, so the pipeline is exercised with a
fake client + patched extraction/parse/enqueue — no network, no Google SDK.
"""
from __future__ import annotations

from unittest.mock import MagicMock


from app.workers.agents import ingest_drive
from app.models.ingest_queue import IngestSource, IngestStatus
from app.models.assessment import Assessment
from app.models.position import Position
from app.models.resume import Resume

FOLDER = "application/vnd.google-apps.folder"


def _patch_pipeline(monkeypatch):
    """Patch the lazily-imported extract/parse/enqueue so no real work runs."""
    import app.engines.extract as extract_mod
    import app.engines.intake as intake_mod
    import app.workers.tasks as tasks_mod

    monkeypatch.setattr(extract_mod, "extract_text",
                        lambda b, t: ("CV text" if t != "txt" else b.decode()) if b else "")
    monkeypatch.setattr(intake_mod, "parse_resume", lambda *a, **k: {"narrative": "n"})
    enqueue = MagicMock()
    monkeypatch.setattr(tasks_mod.run_assessment, "delay", enqueue)
    return enqueue


# ---------------- pure helpers ----------------

def test_classify_uses_name_hints():
    files = [
        {"id": "1", "name": "John_CV.pdf", "mimeType": "application/pdf"},
        {"id": "2", "name": "Target_JD.txt", "mimeType": "text/plain"},
    ]
    cv, jd = ingest_drive._classify(files)
    assert cv["id"] == "1" and jd["id"] == "2"


def test_classify_falls_back_when_one_hint_missing():
    # Only the JD is named; the other doc becomes the CV.
    files = [
        {"id": "1", "name": "document.pdf", "mimeType": "application/pdf"},
        {"id": "2", "name": "role-jd.pdf", "mimeType": "application/pdf"},
    ]
    cv, jd = ingest_drive._classify(files)
    assert jd["id"] == "2" and cv["id"] == "1"


def test_classify_ignores_subfolders():
    files = [{"id": "f", "name": "extra", "mimeType": FOLDER},
             {"id": "1", "name": "cv.pdf", "mimeType": "application/pdf"}]
    cv, jd = ingest_drive._classify(files)
    assert cv["id"] == "1" and jd is None


def test_ext_for():
    assert ingest_drive._ext_for("a.PDF", "") == "pdf"
    assert ingest_drive._ext_for("a", "application/pdf") == "pdf"
    assert ingest_drive._ext_for("a.docx", "") == "docx"
    assert ingest_drive._ext_for("a", "text/plain") == "txt"


# ---------------- pipeline ----------------

def test_process_submission_creates_paired_assessment(sync_db_session, monkeypatch):
    enqueue = _patch_pipeline(monkeypatch)
    monkeypatch.setattr(ingest_drive.settings, "ingest_require_approval", False)

    item = ingest_drive.process_submission(
        sync_db_session,
        submission_ref="gdrive:sub1",
        cv_bytes=b"resume bytes", cv_type="pdf",
        jd_bytes=b"Senior ML Engineer JD", jd_type="txt",
        submitter_name="Jane Doe",
    )

    assert item.source is IngestSource.cloud_drive
    assert item.status is IngestStatus.processing
    assert item.resume_id and item.position_id and item.assessment_id
    # explicit pairing: the JD that arrived with the CV is the position description
    pos = sync_db_session.get(Position, item.position_id)
    assert pos.description == "Senior ML Engineer JD"
    assert sync_db_session.get(Resume, item.resume_id) is not None
    assert sync_db_session.get(Assessment, item.assessment_id) is not None
    enqueue.assert_called_once_with(str(item.assessment_id))


def test_process_submission_respects_approval_gate(sync_db_session, monkeypatch):
    enqueue = _patch_pipeline(monkeypatch)
    monkeypatch.setattr(ingest_drive.settings, "ingest_require_approval", True)

    item = ingest_drive.process_submission(
        sync_db_session, submission_ref="gdrive:sub2",
        cv_bytes=b"x", cv_type="pdf", jd_bytes=b"jd", jd_type="txt",
    )
    assert item.status is IngestStatus.awaiting_review
    enqueue.assert_not_called()  # held for human approval, not enqueued


class _FakeDrive:
    def __init__(self, subfolders, files_by_folder, blobs):
        self._subs = subfolders
        self._files = files_by_folder
        self._blobs = blobs

    def list_children(self, folder_id, *, folders_only=False):
        if folders_only:
            return self._subs
        return self._files.get(folder_id, [])

    def download(self, file_id):
        return self._blobs[file_id]


def test_poll_processes_then_is_idempotent(sync_db_session, monkeypatch):
    enqueue = _patch_pipeline(monkeypatch)
    monkeypatch.setattr(ingest_drive.settings, "ingest_require_approval", False)

    client = _FakeDrive(
        subfolders=[{"id": "subA", "name": "Candidate A", "mimeType": FOLDER}],
        files_by_folder={"subA": [
            {"id": "cvA", "name": "cv.pdf", "mimeType": "application/pdf"},
            {"id": "jdA", "name": "jd.txt", "mimeType": "text/plain"},
        ]},
        blobs={"cvA": b"resume", "jdA": b"the job description"},
    )

    n1 = ingest_drive._poll(sync_db_session, client, "root")
    assert n1 == 1
    assert sync_db_session.query(Position).filter_by(external_ref="gdrive:subA").count() == 1
    enqueue.assert_called_once()

    # Re-poll: the submission is already ingested → skipped (no duplicate).
    n2 = ingest_drive._poll(sync_db_session, client, "root")
    assert n2 == 0
    assert sync_db_session.query(Position).filter_by(external_ref="gdrive:subA").count() == 1


def test_poll_skips_submission_missing_cv_or_jd(sync_db_session, monkeypatch):
    _patch_pipeline(monkeypatch)
    client = _FakeDrive(
        subfolders=[{"id": "subB", "name": "Incomplete", "mimeType": FOLDER}],
        files_by_folder={"subB": [{"id": "only", "name": "cv.pdf", "mimeType": "application/pdf"}]},
        blobs={"only": b"x"},
    )
    assert ingest_drive._poll(sync_db_session, client, "root") == 0


def test_poll_drive_disabled_is_noop(monkeypatch):
    monkeypatch.setattr(ingest_drive.settings, "drive_ingest_enabled", False)
    assert ingest_drive.poll_drive() == {"status": "disabled"}


def test_poll_drive_unconfigured(monkeypatch):
    monkeypatch.setattr(ingest_drive.settings, "drive_ingest_enabled", True)
    monkeypatch.setattr(ingest_drive.settings, "drive_ingest_folder_id", "")
    monkeypatch.setattr(ingest_drive.settings, "drive_ingest_access_token", "")
    assert ingest_drive.poll_drive()["status"] == "unconfigured"


def test_beat_schedule_includes_drive_poll():
    from app.workers.celery_app import celery_app
    assert "poll-drive" in celery_app.conf.beat_schedule
