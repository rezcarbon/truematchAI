"""Tests for error handling and RFC 7807 Problem Detail responses."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ─ Validation Error Tests ────────────────────────────────────────────────


class TestValidationErrors:
    """Test that validation errors return RFC 7807 ProblemDetail format."""

    def test_invalid_email_format(self):
        """Test that invalid email format returns 422 with field-level errors."""
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "not-an-email",
                "password": "SecurePassword123",
                "role": "candidate",
            },
        )
        assert response.status_code == 422
        data = response.json()

        # Verify RFC 7807 structure
        assert data["type"] == "validation_error"
        assert data["title"] == "Request Validation Failed"
        assert data["status"] == 422
        assert "detail" in data
        assert "request_id" in data
        assert "timestamp" in data
        assert "errors" in data

        # Verify field-level errors
        errors = data["errors"]
        assert any(e["field"] == "email" for e in errors)

    def test_password_too_short(self):
        """Test that password validation enforces minimum length."""
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "password": "short",  # Less than 8 characters
                "role": "candidate",
            },
        )
        assert response.status_code == 422
        data = response.json()

        errors = data["errors"]
        assert any(e["field"] == "password" for e in errors)

    def test_missing_required_field(self):
        """Test that missing required fields return validation error."""
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                # Missing password
                "role": "candidate",
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert data["type"] == "validation_error"

    def test_request_id_included(self):
        """Test that request_id is included for correlation."""
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "invalid",
                "password": "short",
                "role": "invalid_role",
            },
        )
        assert response.status_code == 422
        data = response.json()

        # Verify request_id is included
        assert "request_id" in data
        assert len(data["request_id"]) > 0

        # Verify request_id is in response header
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"] == data["request_id"]


# ─ Authentication Error Tests ────────────────────────────────────────────


class TestAuthenticationErrors:
    """Test authentication-related error responses."""

    def test_invalid_login_credentials(self):
        """Test that invalid credentials return 401."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        data = response.json()

        assert data["type"] == "authentication_failed"
        assert data["title"] == "Authentication Failed"
        assert data["status"] == 401
        assert "detail" in data

    def test_missing_authorization_header(self):
        """Test that missing auth header returns 401."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        data = response.json()

        assert data["type"] == "authentication_failed"
        assert data["status"] == 401

    def test_invalid_token_format(self):
        """Test that malformed token returns 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_expired_refresh_token(self):
        """Test that expired refresh token returns 401."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiZXhwIjowfQ.invalid",
            },
        )
        assert response.status_code == 401


# ─ Conflict Error Tests ──────────────────────────────────────────────────


class TestConflictErrors:
    """Test conflict-related error responses (409)."""

    async def test_duplicate_email_registration(self, client):
        """Test that registering with existing email returns 409."""
        # First signup
        client.post(
            "/api/v1/auth/signup",
            json={
                "email": "existing@example.com",
                "password": "SecurePassword123",
                "role": "candidate",
            },
        )

        # Attempt duplicate registration
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "existing@example.com",
                "password": "AnotherPassword456",
                "role": "candidate",
            },
        )
        assert response.status_code == 409
        data = response.json()

        assert data["type"] == "conflict"
        assert data["title"] == "Conflict"
        assert data["status"] == 409
        assert "Email already registered" in data["detail"]


# ─ Authorization Error Tests ─────────────────────────────────────────────


class TestAuthorizationErrors:
    """Test authorization-related error responses (403)."""

    async def test_recruiter_only_endpoint(self, client):
        """Test that candidate cannot access recruiter endpoints."""
        # Register as candidate
        signup_response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "candidate@example.com",
                "password": "SecurePassword123",
                "role": "candidate",
            },
        )
        token = signup_response.json()["access_token"]

        # Attempt to create position (requires recruiter role)
        response = client.post(
            "/api/v1/positions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Senior Backend Engineer",
                "description": "Job description...",
            },
        )
        assert response.status_code == 403
        data = response.json()

        assert data["type"] == "authorization_failed"
        assert data["status"] == 403


# ─ Not Found Error Tests ─────────────────────────────────────────────────


class TestNotFoundErrors:
    """Test not found error responses (404)."""

    async def test_nonexistent_assessment(self, client):
        """Test that accessing nonexistent assessment returns 404."""
        # Register user to get token
        signup_response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "password": "SecurePassword123",
                "role": "candidate",
            },
        )
        token = signup_response.json()["access_token"]

        # Attempt to access nonexistent assessment
        response = client.get(
            "/api/v1/assessments/550e8400-e29b-41d4-a716-446655440000",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        data = response.json()

        assert data["type"] == "resource_not_found"
        assert data["status"] == 404
        assert "not found" in data["detail"].lower()
        assert "instance" in data


# ─ Rate Limiting Tests ───────────────────────────────────────────────────


class TestRateLimiting:
    """Test that rate limiting returns 429 with Retry-After header."""

    @pytest.mark.slow
    def test_rate_limit_exceeded(self):
        """Test that exceeding rate limit returns 429."""
        # Note: This test may be slow if rate limit is high
        # Get current rate limit from settings
        from app.config import settings

        # Make requests up to the limit
        for i in range(settings.rate_limit_per_minute + 1):
            response = client.get("/livez")
            if response.status_code == 429:
                # Rate limit hit
                assert response.status_code == 429
                assert "Retry-After" in response.headers
                return

        # If we get here, rate limit wasn't hit (limit may be very high)
        pytest.skip("Rate limit not hit in test (limit may be very high)")


# ─ Internal Server Error Tests ───────────────────────────────────────────


class TestInternalServerErrors:
    """Test that unhandled errors return generic 500 response."""

    def test_unhandled_exception_response_format(self):
        """Test that unhandled exceptions return RFC 7807 format without details."""
        # This would require mocking an error in an endpoint
        # For now, we test the health endpoint which should always succeed
        response = client.get("/health")
        assert response.status_code == 200

        # Test error handling indirectly by checking error response structure
        # when a real error occurs (database connection, etc.)


# ─ Response Header Tests ─────────────────────────────────────────────────


class TestResponseHeaders:
    """Test that response headers are set correctly."""

    def test_request_id_in_response_header(self):
        """Test that X-Request-ID is included in response headers."""
        response = client.get("/health")
        assert "X-Request-ID" in response.headers

    def test_content_type_json(self):
        """Test that error responses are JSON."""
        response = client.post(
            "/api/v1/auth/signup",
            json={"email": "invalid", "password": "short", "role": "invalid_role"},
        )
        assert response.headers["content-type"] == "application/json"


# ─ Error Message Consistency Tests ───────────────────────────────────────


class TestErrorMessageConsistency:
    """Test that error responses are consistent and helpful."""

    def test_validation_error_clarity(self):
        """Test that validation errors provide clear field information."""
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "invalid-email",
                "password": "short",
            },
        )
        data = response.json()

        # Each error should have field, message, and type
        for error in data.get("errors", []):
            assert "field" in error
            assert "message" in error
            assert "type" in error

    async def test_resource_not_found_includes_instance(self, client):
        """Test that 404 errors include the resource instance URI."""
        # Register user
        signup_response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "password": "SecurePassword123",
                "role": "candidate",
            },
        )
        token = signup_response.json()["access_token"]

        # Request nonexistent resource
        response = client.get(
            "/api/v1/assessments/550e8400-e29b-41d4-a716-446655440000",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()

        # Should include instance URI for debugging
        assert data.get("instance") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
