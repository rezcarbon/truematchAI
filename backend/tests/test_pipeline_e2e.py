"""End-to-end orchestration test for the assessment pipeline.

Drives the REAL `run_assessment` task body (status transitions, governance
gating, counter-rec gating, audit trail) through a session-compatible harness so
the full orchestration is verified without Docker/Postgres. A separate
Docker-backed test (test_pipeline_e2e_postgres.py) covers the real driver/SQL.

Runs in mock LLM mode (conftest sets LLM_FORCE_MOCK=true): mock capability=81,
traditional=62, delta=19; mock governance measures coherence=0.88, consistency
deviation=0.05, fidelity=0.93.
"""
from __future__ import annotations

import uuid


from app.core.governance import (
    COHERENCE_THRESHOLD,
    CONSISTENCY_BOUND,
    COUNTER_REC_DELTA,
    FIDELITY_THRESHOLD,
    GovernanceConfig,
)
from app.models.assessment import Assessment, AssessmentStatus
from app.models.audit import AuditTrail
from app.models.position import Position
from app.models.resume import Resume
from app.workers import tasks


class FakeSession:
    """Minimal Session stand-in: supports the calls run_assessment makes."""

    def __init__(self, objects: dict[type, object], *, resume_missing: bool = False):
        self._objects = objects
        self._resume_missing = resume_missing
        self.added: list[object] = []

    # context manager
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get(self, model, ident):
        if model is Resume and self._resume_missing:
            return None
        return self._objects.get(model)

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        # Assign ids the way a real flush would, so governance_audit_id resolves.
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = uuid.uuid4()

    def commit(self):
        pass

    def rollback(self):
        pass

    # corpus IDF lookups (empty corpus → matcher uses plain TF)
    def scalar(self, stmt):
        return None

    def execute(self, stmt):
        class _R:
            def all(self_inner):
                return []

        return _R()

    # convenience
    def audit_events(self) -> list[str]:
        return [a.event_type for a in self.added if isinstance(a, AuditTrail)]


def _seed() -> tuple[Assessment, Resume, Position]:
    uid = uuid.uuid4()
    resume = Resume(
        user_id=uid,
        file_id="resumes/x/y.pdf",
        file_type="pdf",
        supplementary={"extracted_text": "Maya Okonkwo — shipped ML systems for 7 years."},
    )
    resume.id = uuid.uuid4()
    resume.parsed_data = None
    resume.raw_narrative = None
    position = Position(title="Senior ML Engineer", description="Requires MSc CS, 8+ years.")
    position.id = uuid.uuid4()
    position.parsed_requirements = None
    assessment = Assessment(
        resume_id=resume.id, position_id=position.id, user_id=uid
    )
    assessment.id = uuid.uuid4()
    assessment.counter_rec_triggered = False
    return assessment, resume, position


def _install(monkeypatch, session: FakeSession, cfg: GovernanceConfig | None):
    monkeypatch.setattr(tasks, "_session_factory", lambda: (lambda: session))
    monkeypatch.setattr(tasks, "get_governance_config", lambda: cfg)


def _governed_cfg(fidelity_threshold: float) -> GovernanceConfig:
    return GovernanceConfig(
        {
            COHERENCE_THRESHOLD: 0.70,
            CONSISTENCY_BOUND: 0.25,
            FIDELITY_THRESHOLD: fidelity_threshold,
            COUNTER_REC_DELTA: 25,
        }
    )


def _placeholder_cfg() -> GovernanceConfig:
    return GovernanceConfig(
        {k: "<x>" for k in (COHERENCE_THRESHOLD, CONSISTENCY_BOUND, FIDELITY_THRESHOLD, COUNTER_REC_DELTA)}
    )


def _run(aid: uuid.UUID) -> dict:
    # Execute the real task body locally (no broker/backend needed).
    return tasks.run_assessment.apply(args=[str(aid)]).get()


def test_governed_pass_completes(monkeypatch):
    assessment, resume, position = _seed()
    session = FakeSession({Assessment: assessment, Resume: resume, Position: position})
    # fidelity threshold 0.90 <= mock 0.93 -> all gates pass.
    _install(monkeypatch, session, _governed_cfg(0.90))

    result = _run(assessment.id)

    # Decision engine may flag for review based on other factors (e.g., article 14)
    assert result["status"] in ("completed", "flagged_for_review")
    assert result["governed"] is True
    assert assessment.status in (AssessmentStatus.completed, AssessmentStatus.flagged_for_review)
    # traditional is now a deterministic keyword score (not a fixed mock value)
    assert 0 <= assessment.traditional_score <= 100
    assert assessment.semantic_score is not None
    assert assessment.capability_score == 81
    assert assessment.score_delta == assessment.capability_score - assessment.traditional_score
    # Governance ran and fidelity gate should pass (threshold 0.90 <= mock 0.93).
    assert assessment.governance_fidelity["passed"] is True
    # IP-SAFETY: raw measure never persisted on the result object.
    assert "measure" not in assessment.governance_fidelity
    assert "governance_audit_id" and assessment.governance_audit_id is not None
    events = session.audit_events()
    assert "pipeline.started" in events
    assert "governance.completed" in events
    assert "pipeline.completed" in events


def test_governed_fidelity_failure_flags_for_review(monkeypatch):
    assessment, resume, position = _seed()
    session = FakeSession({Assessment: assessment, Resume: resume, Position: position})
    # fidelity threshold 0.95 > mock 0.93 -> fidelity gate FAILS -> review required.
    _install(monkeypatch, session, _governed_cfg(0.95))

    result = _run(assessment.id)

    assert result["status"] == "flagged_for_review"
    assert result["governance_review_required"] is True
    assert assessment.status is AssessmentStatus.flagged_for_review
    assert assessment.governance_fidelity["passed"] is False


def test_ungoverned_completes_and_counter_recommends(monkeypatch):
    assessment, resume, position = _seed()
    session = FakeSession({Assessment: assessment, Resume: resume, Position: position})
    # Placeholder config -> ungoverned: gates skipped, counter-rec directional.
    _install(monkeypatch, session, _placeholder_cfg())

    result = _run(assessment.id)

    # When ungoverned, decision engine may still flag for review based on other factors
    assert result["status"] in ("completed", "flagged_for_review")
    assert result["governed"] is False
    # Gates not evaluated when ungoverned.
    assert assessment.governance_coherence is None
    # Bias scan always runs.
    assert assessment.governance_bias_flags is not None
    # delta 19 > 0 -> directional counter-rec fires.
    assert assessment.counter_rec_triggered is True


def test_missing_resume_marks_failed(monkeypatch):
    assessment, resume, position = _seed()
    session = FakeSession(
        {Assessment: assessment, Resume: resume, Position: position}, resume_missing=True
    )
    _install(monkeypatch, session, _placeholder_cfg())

    # When resume is missing, the pipeline catches the error and returns a DLQ result
    # instead of raising (the task catches and retries on errors).
    result = _run(assessment.id)

    # Verify the assessment was marked as failed or moved to DLQ
    assert assessment.status is AssessmentStatus.failed
    assert result["status"] in ("dlq_triggered", "failed")
    # DLQ handler logs the failure event
    assert "pipeline.failed" in session.audit_events()
