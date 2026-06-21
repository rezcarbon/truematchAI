"""GDPR data minimization — field whitelisting before external API calls.

This module implements strict field whitelisting to ensure that only necessary
data is sent to external services (Claude API, etc) in compliance with GDPR
principles of data minimization and purpose limitation.

Each redaction function:
  1. Accepts a data structure (resume dict or Assessment model instance)
  2. Extracts only whitelisted fields
  3. Logs redaction details with context (assessment_id, redacted_fields)
  4. Returns a clean dict safe for external API transmission

Logging includes the names of fields that were removed so data loss can be
audited and governance gates can verify coverage.
"""
from __future__ import annotations

import logging
from typing import Any

from app.models.assessment import Assessment

logger = logging.getLogger("truematch.gdpr")

# Whitelist of resume fields allowed to be sent to Claude API.
# These fields contain job-relevant competency signals without sensitive PII.
RESUME_FIELDS_ALLOWED_TO_CLAUDE: dict[str, str] = {
    "skills": "Technical and professional competencies",
    "experience": "Work history and role responsibilities",
    "education": "Academic background and credentials",
    "certifications": "Professional certifications and licenses",
}

# Whitelist of assessment fields allowed to be sent to Claude API.
# Limited to numeric scores that were already computed locally.
ASSESSMENT_FIELDS_ALLOWED_TO_CLAUDE: dict[str, str] = {
    "traditional_score": "Keyword-based ATS simulation score",
    "semantic_score": "Semantic/concept-level match score",
    "capability_score": "Capability assessment reasoning score",
}


def redact_resume_for_claude(parsed_resume: dict) -> dict:
    """Extract only whitelisted fields from a parsed resume.

    Args:
        parsed_resume: A dictionary containing parsed resume data, typically
                      produced by a resume parser (e.g. Lever, Ashby, internal parser).

    Returns:
        A new dict containing only whitelisted resume fields. Fields not in the
        whitelist are silently discarded.

    Logs:
        INFO-level log with the names of all fields that were redacted (removed),
        so auditors can verify that no sensitive data was transmitted.
    """
    if not isinstance(parsed_resume, dict):
        logger.warning(
            "redact_resume_for_claude received non-dict input; returning empty dict",
            extra={"input_type": type(parsed_resume).__name__},
        )
        return {}

    # Extract only whitelisted fields.
    redacted_resume: dict[str, Any] = {}
    for field_name in RESUME_FIELDS_ALLOWED_TO_CLAUDE:
        if field_name in parsed_resume:
            redacted_resume[field_name] = parsed_resume[field_name]

    # Identify and log all fields that were removed.
    all_fields = set(parsed_resume.keys())
    allowed_fields = set(RESUME_FIELDS_ALLOWED_TO_CLAUDE.keys())
    removed_fields = sorted(all_fields - allowed_fields)

    logger.info(
        "Resume redacted for Claude API transmission",
        extra={
            "allowed_field_count": len(redacted_resume),
            "redacted_field_count": len(removed_fields),
            "redacted_fields": removed_fields,
        },
    )

    return redacted_resume


def redact_assessment_for_claude(assessment: Assessment) -> dict:
    """Extract only whitelisted fields from an Assessment model instance.

    The Assessment model contains sensitive encrypted data (narrative, evidence,
    governance results). This function extracts only the three numeric scores
    that were already computed locally, which are safe to send externally.

    Args:
        assessment: An Assessment ORM instance (SQLAlchemy model).

    Returns:
        A dict containing only whitelisted assessment fields. Fields not in the
        whitelist are silently discarded.

    Logs:
        INFO-level log with assessment_id, the count of fields redacted, and the
        explicit list of field names removed, so auditors can verify correct
        minimization.

    Raises:
        AttributeError: If assessment is not an Assessment instance or does not
                       have the required attributes (defensive).
    """
    if not isinstance(assessment, Assessment):
        logger.error(
            "redact_assessment_for_claude received non-Assessment input",
            extra={
                "input_type": type(assessment).__name__,
                "assessment_id": getattr(assessment, "id", "unknown"),
            },
        )
        raise TypeError(
            f"redact_assessment_for_claude requires Assessment instance, got {type(assessment).__name__}"
        )

    # Build whitelist dict from Assessment attributes.
    redacted_assessment: dict[str, Any] = {}
    for field_name in ASSESSMENT_FIELDS_ALLOWED_TO_CLAUDE:
        if hasattr(assessment, field_name):
            value = getattr(assessment, field_name)
            # Only include the field if it has a value (not None).
            if value is not None:
                redacted_assessment[field_name] = value

    # Identify all Assessment attributes (public, non-dunder) that could have been sent.
    # Exclude internal SQLAlchemy attributes and callable methods.
    all_attributes = {
        attr
        for attr in dir(assessment)
        if not attr.startswith("_")
        and hasattr(Assessment, attr)
        and not callable(getattr(assessment, attr, None))
    }

    # Attributes actually present and non-None on this instance.
    accessible_attributes = {
        attr
        for attr in all_attributes
        if hasattr(assessment, attr) and getattr(assessment, attr, None) is not None
    }

    allowed_fields = set(ASSESSMENT_FIELDS_ALLOWED_TO_CLAUDE.keys())
    removed_fields = sorted(accessible_attributes - allowed_fields)

    logger.info(
        "Assessment redacted for Claude API transmission",
        extra={
            "assessment_id": str(assessment.id),
            "allowed_field_count": len(redacted_assessment),
            "redacted_field_count": len(removed_fields),
            "redacted_fields": removed_fields,
        },
    )

    return redacted_assessment
