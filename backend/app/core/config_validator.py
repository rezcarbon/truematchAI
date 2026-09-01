"""Configuration validator for critical secrets at startup.

Validates all critical secrets are properly configured before the application
starts. Separates errors (must-have) from warnings (should-have) and provides
helpful remediation guidance.

Different validation rules apply per environment:
- development: warnings OK, errors fail
- staging: all critical secrets required, some warnings permitted
- production: strict - all secrets required, zero tolerance for weak keys
"""
from __future__ import annotations

import base64
import logging
import secrets
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class SecretValidator:
    """Validate all critical secrets at startup, fail fast if misconfigured."""

    def __init__(self, app_settings: Any) -> None:
        """Initialize validator with application settings.

        Args:
            app_settings: Pydantic Settings instance
        """
        self.settings = app_settings
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate_all(self) -> None:
        """Run all validations, raise if any critical errors found.

        Raises:
            ValueError: If any critical configuration errors detected
        """
        logger.info("Starting configuration validation...")

        self.validate_encryption_keys()
        self.validate_s3_credentials()
        self.validate_jwt_secret()
        self.validate_singpass_keys()
        self.validate_database_url()
        self.validate_redis_url()
        self.validate_anthropic_key()

        self._log_results()

        if self.errors:
            error_msg = "\n".join([f"  - {e}" for e in self.errors])
            raise ValueError(f"Configuration validation failed:\n{error_msg}")

    def validate_anthropic_key(self) -> None:
        """In production, refuse to boot on a placeholder Anthropic key — otherwise
        the entire AI pipeline silently runs on mock fixtures."""
        from app.engines.client import _PLACEHOLDER_KEYS

        key = (self.settings.anthropic_api_key or "").strip()
        if self.settings.is_production and key in _PLACEHOLDER_KEYS:
            self.errors.append(
                "ANTHROPIC_API_KEY must be set in production "
                "(placeholder key would serve mock AI results)."
            )
        elif key in _PLACEHOLDER_KEYS:
            self.warnings.append(
                "ANTHROPIC_API_KEY is a placeholder — AI features run on mock fixtures."
            )

    def validate_encryption_keys(self) -> None:
        """Validate field-level encryption keys.

        Checks:
        - Keys are set and non-empty
        - Keys decode properly from base64
        - Keys are minimum length (32 bytes = 256 bits)
        - Warns if encryption is disabled in production
        """
        encryption_key = self.settings.encryption_key.strip()
        encryption_index_key = self.settings.encryption_index_key.strip()

        # Check if encryption is configured
        encryption_configured = bool(encryption_key and encryption_index_key)

        if not encryption_configured:
            if self.settings.is_production:
                self.errors.append(
                    "ENCRYPTION_KEY and ENCRYPTION_INDEX_KEY are required in production. "
                    "Generate with: python -c \"import secrets; "
                    "print(secrets.token_hex(32))\""
                )
            else:
                self.warnings.append(
                    "Field-level encryption is not configured. "
                    "PII will be stored unencrypted. "
                    "For production, generate keys with: python -c \"import secrets; "
                    "print(secrets.token_hex(32))\""
                )
            return

        # Validate ENCRYPTION_KEY
        try:
            decoded_key = base64.b64decode(encryption_key)
            if len(decoded_key) < 32:
                self.errors.append(
                    f"ENCRYPTION_KEY is too short ({len(decoded_key)} bytes). "
                    "Minimum 32 bytes (256 bits) required. "
                    "Generate with: python -c \"import secrets; "
                    "print(base64.b64encode(secrets.token_bytes(32)).decode())\""
                )
        except Exception as e:
            # Try hex format
            try:
                decoded_key = bytes.fromhex(encryption_key)
                if len(decoded_key) < 32:
                    self.errors.append(
                        f"ENCRYPTION_KEY is too short ({len(decoded_key)} bytes). "
                        "Minimum 32 bytes required."
                    )
            except Exception:
                self.errors.append(
                    f"ENCRYPTION_KEY is not valid base64 or hex: {e}"
                )

        # Validate ENCRYPTION_INDEX_KEY
        try:
            decoded_index_key = base64.b64decode(encryption_index_key)
            if len(decoded_index_key) < 32:
                self.errors.append(
                    f"ENCRYPTION_INDEX_KEY is too short ({len(decoded_index_key)} bytes). "
                    "Minimum 32 bytes (256 bits) required."
                )
        except Exception as e:
            try:
                decoded_index_key = bytes.fromhex(encryption_index_key)
                if len(decoded_index_key) < 32:
                    self.errors.append(
                        f"ENCRYPTION_INDEX_KEY is too short ({len(decoded_index_key)} bytes). "
                        "Minimum 32 bytes required."
                    )
            except Exception:
                self.errors.append(
                    f"ENCRYPTION_INDEX_KEY is not valid base64 or hex: {e}"
                )

    def validate_s3_credentials(self) -> None:
        """Validate AWS S3 credentials.

        Checks:
        - AWS_ACCESS_KEY_ID is not placeholder
        - AWS_SECRET_ACCESS_KEY is not placeholder
        - S3_BUCKET is set
        - Warns if using moto (mock) vs real S3
        """
        access_key = self.settings.aws_access_key_id.strip()
        secret_key = self.settings.aws_secret_access_key.strip()
        bucket = self.settings.s3_bucket.strip()

        # Check for placeholder values
        if access_key == "placeholder" or secret_key == "placeholder":
            if self.settings.is_production:
                self.errors.append(
                    "AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY contain 'placeholder'. "
                    "These must be set to real AWS credentials in production."
                )
            else:
                self.warnings.append(
                    "AWS S3 credentials are using placeholder values. "
                    "Set real AWS credentials for file uploads to work."
                )
            return

        if not bucket:
            if self.settings.is_production:
                self.errors.append("S3_BUCKET must be set in production")
            else:
                self.warnings.append(
                    "S3_BUCKET is not set. File uploads will fail."
                )
            return

        # Check credentials are non-empty if not using placeholder
        if not access_key or not secret_key:
            if self.settings.is_production:
                self.errors.append(
                    "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are required in production"
                )
            else:
                self.warnings.append(
                    "AWS S3 credentials are incomplete. File uploads will fail."
                )

    def validate_jwt_secret(self) -> None:
        """Validate JWT signing secret.

        Checks:
        - JWT_SECRET is not default 'change-me'
        - Minimum length (32 characters)
        - Warns if not using cryptographically strong random
        """
        jwt_secret = self.settings.jwt_secret.strip()

        if not jwt_secret or jwt_secret == "change-me":
            self.errors.append(
                "JWT_SECRET is not set or is 'change-me'. "
                "Generate a strong secret with: "
                "python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
            return

        if len(jwt_secret) < 32:
            if self.settings.is_production:
                self.errors.append(
                    f"JWT_SECRET is too short ({len(jwt_secret)} chars). "
                    "Minimum 32 characters required. "
                    "Generate with: python -c \"import secrets; "
                    "print(secrets.token_urlsafe(32))\""
                )
            else:
                self.warnings.append(
                    f"JWT_SECRET is short ({len(jwt_secret)} chars). "
                    "Consider using 32+ characters for better security."
                )

    def validate_singpass_keys(self) -> None:
        """Validate Singpass OIDC configuration.

        Checks:
        - JWK files exist if Singpass is configured
        - Warns (not errors) if development mode
        """
        sig_path = self.settings.singpass_sig_jwk_path.strip()
        enc_path = self.settings.singpass_enc_jwk_path.strip()

        # If neither is configured, Singpass is disabled (dev mode)
        if not sig_path and not enc_path:
            logger.info("Singpass OIDC not configured - running in development mode")
            return

        # If one is configured, both must be
        if sig_path and not enc_path:
            self.errors.append(
                "SINGPASS_SIG_JWK_PATH is set but SINGPASS_ENC_JWK_PATH is missing. "
                "Both must be configured for Singpass OIDC."
            )
            return

        if enc_path and not sig_path:
            self.errors.append(
                "SINGPASS_ENC_JWK_PATH is set but SINGPASS_SIG_JWK_PATH is missing. "
                "Both must be configured for Singpass OIDC."
            )
            return

        # Check files exist
        sig_file = Path(sig_path)
        enc_file = Path(enc_path)

        if not sig_file.exists():
            self.errors.append(
                f"SINGPASS_SIG_JWK_PATH points to non-existent file: {sig_path}"
            )
        if not enc_file.exists():
            self.errors.append(
                f"SINGPASS_ENC_JWK_PATH points to non-existent file: {enc_path}"
            )

    def validate_database_url(self) -> None:
        """Validate database connection URL.

        Checks:
        - DATABASE_URL is set and valid postgres:// URL
        - Warns if using localhost in production
        """
        db_url = self.settings.database_url.strip()

        if not db_url:
            self.errors.append("DATABASE_URL is not set")
            return

        if not db_url.startswith(("postgresql://", "postgresql+asyncpg://")):
            self.errors.append(
                f"DATABASE_URL must be a PostgreSQL URL (postgresql://...), got: {db_url[:30]}..."
            )
            return

        if self.settings.is_production and "localhost" in db_url:
            self.warnings.append(
                "DATABASE_URL contains 'localhost'. "
                "In production, use a remote database host."
            )

    def validate_redis_url(self) -> None:
        """Validate Redis connection URL.

        Checks:
        - REDIS_URL is set and valid redis:// URL
        - Warns if using localhost in production
        """
        redis_url = self.settings.redis_url.strip()

        if not redis_url:
            self.errors.append(
                "REDIS_URL is not set. Required for rate limiting and token denylist."
            )
            return

        if not redis_url.startswith("redis://"):
            self.errors.append(
                f"REDIS_URL must be a Redis URL (redis://...), got: {redis_url[:30]}..."
            )
            return

        if self.settings.is_production and "localhost" in redis_url:
            self.warnings.append(
                "REDIS_URL contains 'localhost'. "
                "In production, use a remote Redis host."
            )

    def _log_results(self) -> None:
        """Log validation results with structured format."""
        if self.errors:
            logger.critical(
                f"Configuration validation failed with {len(self.errors)} error(s)",
                extra={"error_count": len(self.errors), "errors": self.errors},
            )

        if self.warnings:
            logger.warning(
                f"Configuration validation passed with {len(self.warnings)} warning(s)",
                extra={"warning_count": len(self.warnings), "warnings": self.warnings},
            )

        if not self.errors and not self.warnings:
            logger.info(
                "Configuration validation passed",
                extra={
                    "encryption_enabled": bool(
                        self.settings.encryption_key and self.settings.encryption_index_key
                    ),
                    "s3_enabled": self.settings.s3_configured,
                    "singpass_configured": self.settings.singpass_configured,
                    "environment": self.settings.environment,
                },
            )


class SecretGenerator:
    """Generate cryptographically secure secrets for configuration."""

    @staticmethod
    def generate_encryption_key(length: int = 32) -> str:
        """Generate a base64-encoded AES-256 encryption key.

        Args:
            length: Length in bytes (default 32 for AES-256)

        Returns:
            Base64-encoded key suitable for ENCRYPTION_KEY
        """
        return secrets.token_hex(length)

    @staticmethod
    def generate_encryption_index_key(length: int = 32) -> str:
        """Generate a base64-encoded blind index key.

        Args:
            length: Length in bytes (default 32)

        Returns:
            Base64-encoded key suitable for ENCRYPTION_INDEX_KEY
        """
        return secrets.token_hex(length)

    @staticmethod
    def generate_jwt_secret(length: int = 32) -> str:
        """Generate a JWT signing secret.

        Args:
            length: Length in characters (default 32)

        Returns:
            URL-safe random string suitable for JWT_SECRET
        """
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_all_secrets() -> dict[str, str]:
        """Generate all required secrets at once.

        Returns:
            Dictionary with ENCRYPTION_KEY, ENCRYPTION_INDEX_KEY, JWT_SECRET
        """
        return {
            "ENCRYPTION_KEY": SecretGenerator.generate_encryption_key(),
            "ENCRYPTION_INDEX_KEY": SecretGenerator.generate_encryption_index_key(),
            "JWT_SECRET": SecretGenerator.generate_jwt_secret(),
        }


__all__ = ["SecretValidator", "SecretGenerator"]
