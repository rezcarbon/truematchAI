"""Application configuration via pydantic-settings.

All secrets and environment-specific values are loaded from the environment / .env.
NOTE: governance threshold VALUES are NOT defined here. They are loaded at runtime
from the external config referenced by GOVERNANCE_CONFIG_PATH (see core/governance.py).
"""
from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://truematch:password@localhost:5432/truematch"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"

    @property
    def celery_broker_url(self) -> str:
        return self.redis_url

    @property
    def celery_result_backend(self) -> str:
        return self.redis_url

    # Anthropic
    anthropic_api_key: str = "sk-ant-placeholder"
    anthropic_model: str = "claude-sonnet-4-20250514"
    llm_timeout_seconds: float = 60.0
    # Force deterministic mock fixtures even if a key is present (used by tests).
    llm_force_mock: bool = False

    # External-evidence enrichment (Pillar 5). When disabled, supplementary links
    # are recorded as UNVERIFIED rather than fetched — keeps the pipeline offline
    # and test-safe. Enable in environments with outbound network access.
    enrichment_enabled: bool = False
    enrichment_timeout_seconds: float = 12.0

    # Semantic matcher (Pillar 1). Static embeddings (deterministic) catch
    # conceptual matches the lexical floor misses; falls back to lexical when the
    # embedding model is unavailable (offline). Both are reproducible.
    semantic_use_embeddings: bool = True
    semantic_embedding_model: str = "minishlab/potion-base-8M"
    semantic_embedding_threshold: float = 0.40
    # Semantic score at/above which a surfaced candidate is a "strong match"
    # (concept-matching already endorses) vs a "hidden gem" (only deep capability
    # reasoning finds them). Used to classify the counter-recommendation.
    semantic_confirm_threshold: int = 60

    # Auth
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # S3 / AWS
    s3_bucket: str = "truematch-uploads"
    aws_region: str = "ap-southeast-1"
    aws_access_key_id: str = "placeholder"
    aws_secret_access_key: str = "placeholder"
    # Optional KMS key for S3 server-side encryption. When set, objects use
    # aws:kms; otherwise AES256 (SSE-S3). Uploads are always server-side encrypted.
    s3_kms_key_id: str = ""
    max_upload_bytes: int = 5_000_000  # 5 MB cap on resume uploads

    @property
    def s3_configured(self) -> bool:
        return self.aws_access_key_id not in ("", "placeholder") and self.aws_secret_access_key not in (
            "",
            "placeholder",
        )

    # Field-level encryption (PII at rest). Keys are base64-encoded and injected
    # from a secrets manager / KMS-wrapped at deploy time. NEVER committed.
    #   encryption_key       : 32-byte base64 AES-256 data-encryption key
    #   encryption_index_key : base64 HMAC key for searchable blind indexes
    # When unset, the app runs UNENCRYPTED (dev only) and logs a warning.
    encryption_key: str = ""
    encryption_index_key: str = ""

    # Governance — only the PATH lives in config, never the values.
    governance_config_path: str = "./governance/config.example.json"

    # Singpass (Singapore NDI) OIDC. When unconfigured, the auth flow runs in a
    # bounded DEV mode that returns a deterministic identity (no real NDI calls).
    singpass_issuer: str = ""  # OIDC discovery base, e.g. https://id.singpass.gov.sg
    singpass_client_id: str = ""
    singpass_redirect_uri: str = "https://api.truematch.ai/v1/auth/singpass/callback"
    singpass_scopes: str = "openid"
    # Paths to OUR private JWKs (JSON) used for token-endpoint client auth
    # (signing) and ID-token decryption. Provisioned via secrets manager; never
    # committed. Keys are loaded at runtime only.
    singpass_sig_jwk_path: str = ""
    singpass_enc_jwk_path: str = ""
    singpass_state_ttl_seconds: int = 600

    @property
    def singpass_configured(self) -> bool:
        return bool(
            self.singpass_issuer
            and self.singpass_client_id
            and self.singpass_sig_jwk_path
            and self.singpass_enc_jwk_path
        )

    # --- Autonomous ingestion agents ---
    # Drop-folder paths watched by the Celery Beat agents.
    ingest_cv_folder: str = "./inbox/cv"
    ingest_jd_folder: str = "./inbox/jd"
    ingest_folder_poll_seconds: float = 30.0
    # IMAP email ingestion (leave empty to disable).
    ingest_imap_host: str = ""
    ingest_imap_port: int = 993
    ingest_imap_user: str = ""
    ingest_imap_password: str = ""
    ingest_imap_folder: str = "INBOX"
    ingest_email_poll_seconds: float = 60.0
    # Max retries before marking an ingest item as failed.
    ingest_max_retries: int = 3
    # If True, CV agent requires human approval before running the pipeline.
    ingest_require_approval: bool = False

    # ─── PHASE A: AUTONOMY LAYER ───
    # File system monitoring
    assessment_inbox_path: str = "./inbox/assessments"

    # Email Ingestion (IMAP)
    email_ingestion_enabled: bool = False
    email_imap_host: str = "imap.gmail.com"
    email_imap_port: int = 993
    email_address: str = ""  # Email account to monitor
    email_password: str = ""  # Email password or app-specific password
    email_poll_interval: int = 300  # Poll every 5 minutes

    # Email Sending (SMTP)
    email_smtp_host: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_smtp_username: str = ""
    email_smtp_password: str = ""

    # Assessment Processing
    max_concurrent_assessments: int = 5  # Number of parallel assessment workers
    assessment_timeout_seconds: int = 60  # Max time per assessment

    # Notification Channels
    slack_webhook_url: str = ""  # Slack webhook for notifications
    slack_notifications_enabled: bool = False

    # ─── PHASE B: GOVERNANCE LAYER ───
    # Governance gates configuration
    governance_enable_coherence_gate: bool = True
    governance_enable_consistency_gate: bool = True
    governance_enable_fidelity_gate: bool = True
    governance_enable_bias_gate: bool = True

    # Decision thresholds
    decision_auto_approve_threshold: float = 0.85
    decision_review_threshold: float = 0.65
    decision_auto_reject_threshold: float = 0.65

    # ─── PHASE 1: AUTONOMY LAYER (Week 1) ───
    # Auto-approval/rejection thresholds
    # AUTO_APPROVE_THRESHOLD: Score >= this triggers automatic approval (if governance passes)
    # AUTO_REJECT_THRESHOLD: Score < this triggers automatic rejection
    # DECISION_REVIEW_THRESHOLD: Score between reject and approve requires manual review
    AUTO_APPROVE_THRESHOLD: float = 0.90
    AUTO_REJECT_THRESHOLD: float = 0.40
    DECISION_REVIEW_THRESHOLD: float = 0.65

    # Legacy email/SMTP config (kept for backward compatibility)
    # SMTP server for sending notification emails
    smtp_server: str = ""  # e.g., smtp.gmail.com
    smtp_port: int = 587  # TLS port (not 465 for SMTPS or 25 for plain)
    smtp_username: str = ""  # email account for sending
    smtp_password: str = ""  # SMTP password or app-specific password
    smtp_from_email: str = "noreply@truematch.ai"
    smtp_from_name: str = "TrueMatch"
    smtp_use_tls: bool = True
    # Email service provider (optional, for integrated APIs)
    sendgrid_api_key: str = ""  # SendGrid API key (alternative to SMTP)
    aws_ses_region: str = ""  # AWS SES region (alternative to SMTP)

    # App
    environment: str = "development"
    # NoDecode: don't JSON-parse this env var, so the validator below can accept
    # a comma-separated string (e.g. CORS_ORIGINS=http://a.com,http://b.com).
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # Observability / ops
    log_json: bool = True  # structured JSON logs (set false for human-readable dev logs)
    log_level: str = "INFO"
    sentry_dsn: str = ""  # error tracking; disabled when blank
    metrics_enabled: bool = True  # expose Prometheus /metrics
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 120  # per client IP; 0 disables

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, v: object) -> object:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
