"""EU AI Act Article 14 decision taxonomy tests.

Tests for the decision_engine module covering:
- Decision type classification (approval, advisory, escalate)
- Human review requirement logic
- Decision metadata generation and reasoning
- Integration with Assessment model
"""
from __future__ import annotations

import uuid


from app.engines.decision_engine import (
    apply_decision_to_assessment,
    determine_decision_type,
    generate_decision_metadata,
)
from app.models.assessment import AssessmentStatus, DecisionType


class MockAssessment:
    """Minimal Assessment mock for testing decision_engine functions."""

    def __init__(
        self,
        capability_score: int | None = None,
        governance_coherence: dict | None = None,
        governance_consistency: dict | None = None,
        governance_fidelity: dict | None = None,
    ):
        self.id = uuid.uuid4()
        self.resume_id = uuid.uuid4()
        self.position_id = uuid.uuid4()
        self.user_id = uuid.uuid4()
        self.status = AssessmentStatus.running
        self.capability_score = capability_score
        self.governance_coherence = governance_coherence
        self.governance_consistency = governance_consistency
        self.governance_fidelity = governance_fidelity
        self.decision_type = None
        self.human_review_required = False
        self.article_14_compliant = True
        self.review_reason = None


class TestDetermineDecisionType:
    """Test determine_decision_type function."""

    def test_escalate_when_capability_below_40(self):
        """Low capability (< 40) always escalates."""
        assessment = MockAssessment(capability_score=35)
        decision_type, requires_review = determine_decision_type(
            assessment, capability_score=35, governance_passed=True
        )
        assert decision_type == DecisionType.escalate
        assert requires_review is True

    def test_escalate_at_boundary_39(self):
        """Capability at 39 is below escalation threshold (40)."""
        assessment = MockAssessment(capability_score=39)
        decision_type, requires_review = determine_decision_type(
            assessment, capability_score=39, governance_passed=True
        )
        assert decision_type == DecisionType.escalate
        assert requires_review is True

    def test_advisory_when_governance_failed(self):
        """Failed governance routes to advisory regardless of capability."""
        assessment = MockAssessment(capability_score=95)
        decision_type, requires_review = determine_decision_type(
            assessment, capability_score=95, governance_passed=False
        )
        assert decision_type == DecisionType.advisory
        assert requires_review is True

    def test_advisory_when_capability_40_to_90(self):
        """Mid-range capability (40-90) defaults to advisory."""
        test_scores = [40, 50, 75, 89]
        for score in test_scores:
            assessment = MockAssessment(capability_score=score)
            decision_type, requires_review = determine_decision_type(
                assessment, capability_score=score, governance_passed=True
            )
            assert decision_type == DecisionType.advisory
            assert requires_review is True

    def test_approval_when_capability_90_and_governance_passed(self):
        """Capability >= 90 + governance passed = autonomous approval."""
        assessment = MockAssessment(capability_score=90)
        decision_type, requires_review = determine_decision_type(
            assessment, capability_score=90, governance_passed=True
        )
        assert decision_type == DecisionType.approval
        assert requires_review is False

    def test_approval_at_high_capability(self):
        """High capability scores (95, 100) with governance passed = approval."""
        test_scores = [90, 95, 100]
        for score in test_scores:
            assessment = MockAssessment(capability_score=score)
            decision_type, requires_review = determine_decision_type(
                assessment, capability_score=score, governance_passed=True
            )
            assert decision_type == DecisionType.approval
            assert requires_review is False

    def test_priority_order_low_score_wins_over_governance(self):
        """Escalation threshold (score < 40) takes priority over governance."""
        # Even if governance passed, low score forces escalate
        assessment = MockAssessment(capability_score=30)
        decision_type, _ = determine_decision_type(
            assessment, capability_score=30, governance_passed=True
        )
        assert decision_type == DecisionType.escalate


class TestGenerateDecisionMetadata:
    """Test generate_decision_metadata function."""

    def test_approval_metadata(self):
        """Approval metadata includes autonomy statement."""
        assessment = MockAssessment(
            capability_score=95,
            governance_coherence={"passed": True},
            governance_consistency={"passed": True},
            governance_fidelity={"passed": True},
        )
        metadata = generate_decision_metadata(assessment, DecisionType.approval)

        assert metadata["type"] == "approval"
        assert metadata["requires_human_review"] is False
        assert metadata["article_14_compliant"] is True
        assert "high confidence" in metadata["reasoning"]
        assert "Proceed with autonomous" in metadata["recommendation"]

    def test_advisory_metadata(self):
        """Advisory metadata includes review statement."""
        assessment = MockAssessment(
            capability_score=60,
            governance_coherence={"passed": True},
            governance_consistency={"passed": True},
            governance_fidelity={"passed": True},
        )
        metadata = generate_decision_metadata(assessment, DecisionType.advisory)

        assert metadata["type"] == "advisory"
        assert metadata["requires_human_review"] is True
        assert metadata["article_14_compliant"] is True
        assert "human review" in metadata["reasoning"]
        assert "Review assessment with candidate" in metadata["recommendation"]

    def test_escalate_metadata(self):
        """Escalate metadata includes escalation statement."""
        assessment = MockAssessment(
            capability_score=35,
            governance_coherence={"passed": True},
            governance_consistency={"passed": True},
            governance_fidelity={"passed": True},
        )
        metadata = generate_decision_metadata(assessment, DecisionType.escalate)

        assert metadata["type"] == "escalate"
        assert metadata["requires_human_review"] is True
        assert metadata["article_14_compliant"] is True
        assert "Escalation required" in metadata["reasoning"]
        assert "Escalate to senior reviewer" in metadata["recommendation"]

    def test_advisory_metadata_with_failed_coherence(self):
        """Advisory metadata captures specific governance failure reasons."""
        assessment = MockAssessment(
            capability_score=85,
            governance_coherence={"passed": False},
            governance_consistency={"passed": True},
            governance_fidelity={"passed": True},
        )
        metadata = generate_decision_metadata(assessment, DecisionType.advisory)

        assert "coherence governance gate failed" in metadata["reasoning"]

    def test_advisory_metadata_with_multiple_gate_failures(self):
        """Advisory metadata lists all failed governance gates."""
        assessment = MockAssessment(
            capability_score=85,
            governance_coherence={"passed": False},
            governance_consistency={"passed": False},
            governance_fidelity={"passed": True},
        )
        metadata = generate_decision_metadata(assessment, DecisionType.advisory)

        assert "coherence governance gate failed" in metadata["reasoning"]
        assert "consistency governance gate failed" in metadata["reasoning"]

    def test_metadata_structure(self):
        """Metadata dict has all required keys."""
        assessment = MockAssessment(capability_score=85)
        metadata = generate_decision_metadata(assessment, DecisionType.advisory)

        required_keys = {"type", "requires_human_review", "article_14_compliant", "reasoning", "recommendation"}
        assert required_keys.issubset(metadata.keys())

    def test_metadata_compliance_flag_always_true(self):
        """Article 14 compliance flag is always True (all paths compliant)."""
        for decision_type in [DecisionType.approval, DecisionType.advisory, DecisionType.escalate]:
            assessment = MockAssessment(capability_score=50)
            metadata = generate_decision_metadata(assessment, decision_type)
            assert metadata["article_14_compliant"] is True


class TestApplyDecisionToAssessment:
    """Test apply_decision_to_assessment integration function."""

    def test_apply_approval_decision(self):
        """Approval decision sets all fields correctly."""
        assessment = MockAssessment(capability_score=95)
        apply_decision_to_assessment(assessment, DecisionType.approval, governance_passed=True)

        assert assessment.decision_type == DecisionType.approval
        assert assessment.human_review_required is False
        assert assessment.article_14_compliant is True
        assert assessment.review_reason is not None
        assert "autonomous approval" in assessment.review_reason.lower()

    def test_apply_advisory_decision(self):
        """Advisory decision sets human review flag."""
        assessment = MockAssessment(capability_score=60)
        apply_decision_to_assessment(assessment, DecisionType.advisory, governance_passed=True)

        assert assessment.decision_type == DecisionType.advisory
        assert assessment.human_review_required is True
        assert assessment.article_14_compliant is True
        assert assessment.review_reason is not None

    def test_apply_escalate_decision(self):
        """Escalate decision sets escalation flag."""
        assessment = MockAssessment(capability_score=30)
        apply_decision_to_assessment(assessment, DecisionType.escalate, governance_passed=True)

        assert assessment.decision_type == DecisionType.escalate
        assert assessment.human_review_required is True
        assert assessment.article_14_compliant is True

    def test_decision_metadata_in_review_reason(self):
        """Applied review_reason includes full metadata reasoning."""
        assessment = MockAssessment(capability_score=95)
        apply_decision_to_assessment(assessment, DecisionType.approval, governance_passed=True)

        assert "Article 14 autonomy threshold met" in assessment.review_reason


class TestDecisionTypeIntegration:
    """Integration tests for complete decision workflow."""

    def test_full_workflow_approval(self):
        """Complete workflow: score 95 + governance passed -> approval."""
        assessment = MockAssessment(
            capability_score=95,
            governance_coherence={"passed": True},
            governance_consistency={"passed": True},
            governance_fidelity={"passed": True},
        )

        # Step 1: Determine type
        decision_type, requires_review = determine_decision_type(
            assessment, capability_score=95, governance_passed=True
        )
        assert decision_type == DecisionType.approval
        assert requires_review is False

        # Step 2: Generate metadata
        metadata = generate_decision_metadata(assessment, decision_type)
        assert metadata["requires_human_review"] is False

        # Step 3: Apply to assessment
        apply_decision_to_assessment(assessment, decision_type, governance_passed=True)
        assert assessment.decision_type == DecisionType.approval

    def test_full_workflow_advisory_mid_confidence(self):
        """Complete workflow: score 60 + governance passed -> advisory."""
        assessment = MockAssessment(
            capability_score=60,
            governance_coherence={"passed": True},
            governance_consistency={"passed": True},
            governance_fidelity={"passed": True},
        )

        decision_type, requires_review = determine_decision_type(
            assessment, capability_score=60, governance_passed=True
        )
        assert decision_type == DecisionType.advisory
        assert requires_review is True

        metadata = generate_decision_metadata(assessment, decision_type)
        assert metadata["requires_human_review"] is True

        apply_decision_to_assessment(assessment, decision_type, governance_passed=True)
        assert assessment.human_review_required is True

    def test_full_workflow_advisory_governance_failed(self):
        """Complete workflow: governance failed -> advisory (even high score)."""
        assessment = MockAssessment(
            capability_score=95,
            governance_coherence={"passed": False},
            governance_consistency={"passed": True},
            governance_fidelity={"passed": True},
        )

        decision_type, requires_review = determine_decision_type(
            assessment, capability_score=95, governance_passed=False
        )
        assert decision_type == DecisionType.advisory
        assert requires_review is True

    def test_full_workflow_escalate(self):
        """Complete workflow: score < 40 -> escalate."""
        assessment = MockAssessment(capability_score=35)

        decision_type, requires_review = determine_decision_type(
            assessment, capability_score=35, governance_passed=True
        )
        assert decision_type == DecisionType.escalate
        assert requires_review is True

        metadata = generate_decision_metadata(assessment, decision_type)
        assert "escalation" in metadata["reasoning"].lower()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_capability_score_of_zero(self):
        """Zero capability always escalates."""
        assessment = MockAssessment(capability_score=0)
        decision_type, _ = determine_decision_type(
            assessment, capability_score=0, governance_passed=True
        )
        assert decision_type == DecisionType.escalate

    def test_capability_score_of_100(self):
        """Max capability with governance passed = approval."""
        assessment = MockAssessment(capability_score=100)
        decision_type, requires_review = determine_decision_type(
            assessment, capability_score=100, governance_passed=True
        )
        assert decision_type == DecisionType.approval
        assert requires_review is False

    def test_governance_passed_false_with_score_90(self):
        """Score 90 + governance failed = advisory (not approval)."""
        assessment = MockAssessment(capability_score=90)
        decision_type, _ = determine_decision_type(
            assessment, capability_score=90, governance_passed=False
        )
        assert decision_type == DecisionType.advisory

    def test_none_governance_fields_handled(self):
        """None governance fields don't crash metadata generation."""
        assessment = MockAssessment(
            capability_score=50,
            governance_coherence=None,
            governance_consistency=None,
            governance_fidelity=None,
        )
        metadata = generate_decision_metadata(assessment, DecisionType.advisory)
        assert metadata is not None
        assert "reasoning" in metadata
