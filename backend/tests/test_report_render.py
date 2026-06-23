"""Tests for auto-report rendering (app.services.report_render + render_reports task).

render_reports is duck-typed over the Assessment attributes, so it's exercised with
a lightweight namespace (no DB), and the deposit/guards are tested directly.
"""
from __future__ import annotations

import datetime
from types import SimpleNamespace
from uuid import uuid4

from app.services.report_render import render_reports
from app.workers import render_reports as task_mod


def _fake_assessment(**over):
    base = dict(
        id=uuid4(),
        created_at=datetime.datetime(2026, 6, 23, 12, 0, 0),
        traditional_score=25,
        semantic_score=95,
        capability_score=62,
        score_delta=37,
        capability_narrative="Strong evidenced capability across the role's core dimensions.",
        capability_components={
            "domain_depth": {"score": 68, "reasoning": "Deep, demonstrated domain expertise."},
            "problem_solving": {"score": 80, "reasoning": "Clear decomposition of hard problems."},
        },
        counter_rec_triggered=True,
        counter_rec_reasoning="ATS ranks 25 but evidenced capability is 62 — hidden gem.",
        jd_quality_score=72,
    )
    base.update(over)
    return SimpleNamespace(**base)


def test_render_reports_produces_two_pdfs():
    pdfs = render_reports(_fake_assessment(), candidate_name="Jane Doe",
                          target_title="Venture Partner")
    assert set(pdfs) == {"candidate", "recruiter"}
    for kind, data in pdfs.items():
        assert data.startswith(b"%PDF"), kind
        assert len(data) > 2000, f"{kind} too small ({len(data)} bytes)"


def test_render_reports_handles_multilingual_and_missing_fields():
    # non-English source + missing narrative/components must still render cleanly
    a = _fake_assessment(capability_narrative=None, capability_components=None,
                         counter_rec_triggered=False, counter_rec_reasoning=None,
                         jd_quality_score=None)
    pdfs = render_reports(a, candidate_name="Mohamed Reezan",
                          target_title="AI Deployment Strategist", source_language="ta")
    assert pdfs["candidate"].startswith(b"%PDF")
    assert pdfs["recruiter"].startswith(b"%PDF")


def test_render_reports_red_band_for_low_capability():
    # low capability should not raise and should still produce both reports
    pdfs = render_reports(_fake_assessment(capability_score=30, score_delta=5,
                          counter_rec_triggered=False),
                          candidate_name="X", target_title="Role")
    assert pdfs["recruiter"].startswith(b"%PDF")


def test_deposit_writes_local_files(tmp_path, monkeypatch):
    monkeypatch.setattr(task_mod.settings, "auto_report_output_dir", str(tmp_path))
    # s3_enabled is a computed property → false without creds in tests, so local path is used
    locations = task_mod._deposit("abc123", {"candidate": b"%PDF-1\n", "recruiter": b"%PDF-2\n"})
    assert (tmp_path / "abc123_candidate.pdf").exists()
    assert (tmp_path / "abc123_recruiter.pdf").exists()
    assert len(locations) == 2


def test_render_task_disabled_is_noop(monkeypatch):
    monkeypatch.setattr(task_mod.settings, "auto_report_enabled", False)
    assert task_mod.render_assessment_reports("any-id") == {"status": "disabled"}


def test_candidate_name_falls_back():
    assert task_mod._candidate_name(None) == "Candidate"
    r = SimpleNamespace(parsed_data={"name": "Ada Lovelace"}, supplementary={})
    assert task_mod._candidate_name(r) == "Ada Lovelace"
    r2 = SimpleNamespace(parsed_data={}, supplementary={"sender_name": "Grace H"})
    assert task_mod._candidate_name(r2) == "Grace H"
