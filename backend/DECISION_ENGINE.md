# EU AI Act Article 14 Decision Engine

## Overview

The decision_engine implements the decision taxonomy required by the EU AI Act Article 14, which mandates human review for high-risk AI decisions. The engine classifies assessments into three decision types:

1. **approval**: Autonomous approval (confidence >= 90 + all governance passed)
2. **advisory**: Recommendation requiring human review (confidence 40-90 or governance failed)
3. **escalate**: Escalation to human decision-maker (confidence < 40)

## Core Functions

### determine_decision_type()

```python
def determine_decision_type(
    assessment: Assessment,
    capability_score: int,
    governance_passed: bool,
) -> tuple[DecisionType, bool]:
```

Classifies an assessment into a decision type based on:
- **Capability score**: Model confidence (0-100 scale)
- **Governance passed**: Boolean indicating ALL governance gates passed (coherence, consistency, fidelity)

Returns:
- `tuple[DecisionType, bool]`: (decision_type, requires_human_review)

#### Decision Priority

The function enforces a strict priority order:

1. **Escalation (capability < 40)**: Highest priority
   - If capability score is below 40, escalate immediately
   - Returns: (DecisionType.escalate, True)

2. **Governance Mandatory Gate**: Second priority
   - If governance did NOT fully pass, route to advisory
   - Returns: (DecisionType.advisory, True)

3. **Autonomous Approval (capability >= 90 + governance passed)**: Third priority
   - If capability >= 90 AND governance fully passed, approve autonomously
   - Returns: (DecisionType.approval, False)

4. **Advisory Default (40-90)**: Fourth priority
   - All other cases (capability 40-90) default to advisory
   - Returns: (DecisionType.advisory, True)

#### Governance Passed Logic

`governance_passed` is True when ALL three gates passed:
- Coherence: Assessment components are mutually supportive
- Consistency: Conclusion aligns with cited evidence
- Fidelity: All claims are grounded in source material

If any gate fails, `governance_passed` is False and decision routes to advisory.

### generate_decision_metadata()

```python
def generate_decision_metadata(
    assessment: Assessment,
    decision_type: DecisionType,
) -> dict:
```

Generates compliance-grade metadata for audit trail and human review.

Returns a dict with:
- `type` (str): The decision_type value ("approval", "advisory", or "escalate")
- `requires_human_review` (bool): True for advisory/escalate, False for approval
- `article_14_compliant` (bool): Always True (all paths are compliant)
- `reasoning` (str): Why this decision type was selected (includes score, governance status)
- `recommendation` (str): Actionable next step for human reviewers

#### Reasoning Examples

**Approval:**
```
Autonomous approval granted. Capability assessment demonstrates high confidence 
(score=95), and all governance gates passed: coherence=True, consistency=True, 
fidelity=True. Article 14 autonomy threshold met.
```

**Advisory (mid-confidence):**
```
Advisory recommendation issued. Decision routed to human review due to: capability 
score (60) below autonomy threshold (90). Article 14 requires human oversight for 
this confidence/governance profile.
```

**Advisory (governance failed):**
```
Advisory recommendation issued. Decision routed to human review due to: coherence 
governance gate failed. Article 14 requires human oversight for this confidence/governance profile.
```

**Escalate:**
```
Escalation required. Capability assessment confidence (35) is below escalation 
threshold (40). High-risk decisions require human review before any autonomous action. 
Article 14 escalation protocol triggered.
```

### apply_decision_to_assessment()

```python
def apply_decision_to_assessment(
    assessment: Assessment,
    decision_type: DecisionType,
    governance_passed: bool,
) -> None:
```

Convenience function that applies decision classification directly to Assessment model.

Updates fields:
- `decision_type` (DecisionType): The classified decision type
- `human_review_required` (bool): Whether human review is required
- `article_14_compliant` (bool): Always True
- `review_reason` (str): Full reasoning from generate_decision_metadata()

Does NOT commit to database—caller manages session.

## Integration with Assessment Pipeline

### In run_assessment() Task

The decision engine is integrated into the Celery task at the end of the pipeline, after governance gates have been evaluated:

```python
# Calculate decision type from capability score + governance status
capability_score = cap or 0
decision_type, requires_review = decision_engine.determine_decision_type(
    assessment, capability_score, governance_fully_passed
)

# Apply to assessment instance
decision_engine.apply_decision_to_assessment(
    assessment, decision_type, governance_fully_passed
)

# Set status based on decision type
if decision_type == "approval":
    assessment.status = AssessmentStatus.completed
else:
    assessment.status = AssessmentStatus.flagged_for_review
```

### Assessment Status Mapping

| Decision Type | Assessment Status | Human Review | Usage |
|---|---|---|---|
| approval | completed | No | Autonomous decision approved, no review needed |
| advisory | flagged_for_review | Yes | Recommendation, requires human validation |
| escalate | flagged_for_review | Yes | Low confidence, requires human decision |

## Decision Logic Examples

### Example 1: High Confidence + Governance Passed → Approval

```
capability_score: 95
governance_coherence: passed
governance_consistency: passed
governance_fidelity: passed

Result: DecisionType.approval, human_review_required=False
Status: Assessment.completed
→ Autonomous decision, no human review needed
```

### Example 2: Mid Confidence + Governance Passed → Advisory

```
capability_score: 65
governance_coherence: passed
governance_consistency: passed
governance_fidelity: passed

Result: DecisionType.advisory, human_review_required=True
Status: Assessment.flagged_for_review
→ Recommendation, human review required
```

### Example 3: High Confidence + Governance Failed → Advisory

```
capability_score: 95
governance_coherence: FAILED
governance_consistency: passed
governance_fidelity: passed

Result: DecisionType.advisory, human_review_required=True
Status: Assessment.flagged_for_review
→ Even high confidence cannot bypass failed governance
```

### Example 4: Low Confidence → Escalate

```
capability_score: 35
governance_coherence: passed
governance_consistency: passed
governance_fidelity: passed

Result: DecisionType.escalate, human_review_required=True
Status: Assessment.flagged_for_review
→ Escalate to senior reviewer or hiring manager
```

## Compliance Features

### Article 14 Requirements

The decision engine ensures compliance with EU AI Act Article 14:

1. **High-risk Decision Identification**
   - All decisions except autonomous approvals are flagged for human review
   - Low-confidence assessments are escalated immediately

2. **Human Oversight**
   - Decisions marked "advisory" or "escalate" require human review
   - Audit trail includes decision type and reasoning

3. **Transparency**
   - Each decision includes detailed reasoning visible to human reviewers
   - Governance gate status is recorded (coherence, consistency, fidelity)

4. **Auditability**
   - Decision metadata logged to assessment.review_reason
   - Governance audit trail includes decision classification
   - Status transitions tracked: running → completed/flagged_for_review

### Audit Trail

Each assessment run generates audit entries:

```python
_audit(
    db, aid, "decision.classified",
    {
        "decision_type": "approval",
        "capability_score": 95,
        "governance_passed": True,
        "requires_human_review": False,
        "article_14_compliant": True,
    }
)
```

## Threshold Configuration

The decision engine uses two hard thresholds (NOT governance-configurable):

1. **Autonomous Approval Threshold**: >= 90
   - Capability score must be >= 90 for autonomous approval
   - Hard threshold, not configurable via governance config

2. **Escalation Threshold**: < 40
   - Capability score below 40 triggers escalation
   - Hard threshold, not configurable via governance config

Governance gates (coherence, consistency, fidelity) are configurable via `settings.governance_config_path` but the score thresholds are fixed.

## Testing

Comprehensive test suite in `tests/test_decision_engine.py`:

- **TestDetermineDecisionType**: Decision classification logic
- **TestGenerateDecisionMetadata**: Metadata generation and reasoning
- **TestApplyDecisionToAssessment**: Integration with Assessment model
- **TestDecisionTypeIntegration**: Full workflow scenarios
- **TestEdgeCases**: Boundary conditions and edge cases

Run tests:
```bash
pytest tests/test_decision_engine.py -v
```

## Future Extensions

Potential enhancements:

1. **Confidence Percentile Adjustment**: Adjust thresholds (90, 40) based on domain or position type
2. **Explainability**: Generate LIME/SHAP explanations for high-risk decisions
3. **Appeals Process**: Track human overrides of model decisions
4. **Benchmarking**: Compare model decisions to human outcomes over time
5. **Regulatory Updates**: Support EU AI Act amendments and sector-specific regulations

## References

- EU AI Act, Article 14: Human Oversight
- TrueMatch Assessment Pipeline: `/app/workers/tasks.py`
- Governance Configuration: `/app/core/governance.py`
- Assessment Model: `/app/models/assessment.py`
