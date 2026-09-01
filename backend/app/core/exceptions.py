"""
Custom exception hierarchy and RFC 7807 Problem Detail response models.

This module defines all domain-specific exceptions and the standardized
error response format for the TrueMatch API.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


# ─ Custom Exception Hierarchy ────────────────────────────────────────────


class TrueMatchError(Exception):
    """Base exception for all TrueMatch domain errors."""

    def __init__(
        self,
        message: str,
        error_type: str = "internal_error",
        status_code: int = 500,
        instance: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize a TrueMatchError.

        Args:
            message: Human-readable error message
            error_type: Machine-readable error code (e.g., "validation_error")
            status_code: HTTP status code (default: 500)
            instance: URI identifying the problem instance (e.g., "/api/v1/assessments/uuid")
            details: Additional error context (e.g., validation errors)
        """
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.instance = instance
        self.details = details or {}
        super().__init__(message)


class ValidationError(TrueMatchError):
    """Raised when request validation fails (HTTP 400/422)."""

    def __init__(
        self,
        message: str = "Request validation failed",
        details: Optional[dict[str, Any]] = None,
        instance: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_type="validation_error",
            status_code=422,
            instance=instance,
            details=details,
        )


class AuthenticationError(TrueMatchError):
    """Raised when authentication fails (HTTP 401)."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_type="authentication_failed",
            status_code=401,
        )


class AuthorizationError(TrueMatchError):
    """Raised when user lacks required permissions (HTTP 403)."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            error_type="authorization_failed",
            status_code=403,
        )


class NotFoundError(TrueMatchError):
    """Raised when a resource is not found (HTTP 404)."""

    def __init__(
        self,
        message: str = "Resource not found",
        instance: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_type="resource_not_found",
            status_code=404,
            instance=instance,
        )


class ConflictError(TrueMatchError):
    """Raised when there is a resource conflict (HTTP 409)."""

    def __init__(
        self,
        message: str = "Conflict",
        instance: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_type="conflict",
            status_code=409,
            instance=instance,
        )


class StorageError(TrueMatchError):
    """Raised when file storage operations fail (HTTP 503)."""

    def __init__(self, message: str = "Storage service unavailable"):
        super().__init__(
            message=message,
            error_type="storage_error",
            status_code=503,
        )


class DatabaseError(TrueMatchError):
    """Raised when database operations fail (HTTP 503)."""

    def __init__(self, message: str = "Database service unavailable"):
        super().__init__(
            message=message,
            error_type="database_error",
            status_code=503,
        )


class ExternalServiceError(TrueMatchError):
    """Raised when external service calls fail (HTTP 503)."""

    def __init__(
        self,
        service_name: str = "External service",
        message: Optional[str] = None,
    ):
        msg = message or f"{service_name} is temporarily unavailable"
        super().__init__(
            message=msg,
            error_type="external_service_error",
            status_code=503,
        )


class LLMError(ExternalServiceError):
    """Raised when LLM API calls fail."""

    def __init__(self, message: Optional[str] = None):
        super().__init__(service_name="LLM", message=message)


# ─ RFC 7807 Problem Detail Response Model ────────────────────────────────


class ProblemDetail(BaseModel):
    """
    RFC 7807 Problem Details for HTTP APIs.

    This standardized response format provides machine-readable details
    about HTTP error responses, enabling better error handling in clients.

    Reference: https://www.rfc-editor.org/rfc/rfc7807
    """

    type: str = Field(
        ...,
        description="Machine-readable error type (e.g., 'validation_error', 'resource_not_found')",
        examples=["validation_error", "authentication_failed", "resource_not_found"],
    )

    title: str = Field(
        ...,
        description="Short human-readable title of the error",
        examples=["Validation Error", "Authentication Failed", "Resource Not Found"],
    )

    status: int = Field(
        ...,
        description="HTTP status code",
        examples=[400, 401, 404, 422, 500],
        ge=400,
        le=599,
    )

    detail: str = Field(
        ...,
        description="Detailed human-readable explanation",
        examples=[
            "The 'email' field must be a valid email address",
            "Invalid credentials provided",
            "Assessment with ID 'abc123' not found",
        ],
    )

    request_id: str = Field(
        ...,
        description="Unique request identifier for correlation and debugging",
        examples=["req-550e8400-e29b-41d4-a716-446655440000"],
    )

    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp when the error occurred",
        examples=["2026-06-03T10:30:00Z"],
    )

    instance: Optional[str] = Field(
        None,
        description="URI identifying the specific problem instance (e.g., the resource URI)",
        examples=["/api/v1/assessments/550e8400-e29b-41d4-a716-446655440000"],
    )

    errors: Optional[list[dict[str, Any]]] = Field(
        None,
        description="Field-level validation errors (for 422 responses)",
        examples=[
            [
                {"field": "email", "message": "invalid email format", "type": "value_error.email"},
                {"field": "password", "message": "ensure this value has at least 8 characters", "type": "value_error.string.too_short"},
            ]
        ],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "validation_error",
                "title": "Request Validation Failed",
                "status": 422,
                "detail": "The request body contains validation errors",
                "request_id": "req-550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2026-06-03T10:30:00Z",
                "instance": "/api/v1/auth/signup",
                "errors": [
                    {
                        "field": "email",
                        "message": "invalid email format",
                        "type": "value_error.email",
                    }
                ],
            }
        }


def problem_detail_from_exception(
    exc: TrueMatchError,
    request_id: str,
    timestamp: Optional[str] = None,
) -> ProblemDetail:
    """
    Convert a TrueMatchError to a ProblemDetail response.

    Args:
        exc: The exception to convert
        request_id: Unique request identifier
        timestamp: ISO 8601 timestamp (defaults to now)

    Returns:
        ProblemDetail instance ready for JSON serialization
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    # Map error type to title
    title_map = {
        "validation_error": "Validation Error",
        "authentication_failed": "Authentication Failed",
        "authorization_failed": "Authorization Failed",
        "resource_not_found": "Resource Not Found",
        "conflict": "Conflict",
        "storage_error": "Storage Error",
        "database_error": "Database Error",
        "external_service_error": "External Service Error",
        "llm_error": "LLM Error",
    }

    title = title_map.get(exc.error_type, "Internal Server Error")

    # Validation errors may include field-level errors
    errors = None
    if exc.error_type == "validation_error" and "errors" in exc.details:
        errors = exc.details["errors"]

    return ProblemDetail(
        type=exc.error_type,
        title=title,
        status=exc.status_code,
        detail=exc.message,
        request_id=request_id,
        timestamp=timestamp,
        instance=exc.instance,
        errors=errors,
    )
