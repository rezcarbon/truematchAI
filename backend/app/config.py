"""Application configuration via pydantic-settings.

All secrets and environment-specific values are loaded from the environment / .env.
NOTE: governance threshold VALUES are NOT defined here. They are loaded at runtime
from the external config referenced by GOVERNANCE_CONFIG_PATH (see core/governance.py).
"""
from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
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
    anthropic_model: str = "claude-sonnet-4-6"
    # Cheaper/faster model used for SECONDARY reasoning (trajectory, JD
    # interrogation) when economy mode or the soft budget kicks in.
    anthropic_fast_model: str = "claude-haiku-4-5-20251001"
    # Opus on a large structured (tool-use) call can legitimately take ~63s;
    # 60s caused spurious timeouts → retries → failover. 120s gives headroom.
    llm_timeout_seconds: float = 120.0
    # Force deterministic mock fixtures even if a key is present (used by tests).
    llm_force_mock: bool = False
    # Budget-aware model routing: 0 disables. When the day's global LLM spend
    # exceeds soft_ratio * budget, secondary reasoning downshifts to the fast
    # model; the strong model is reserved for capability verdicts and chat.
    llm_daily_budget_usd: float = 0.0
    llm_budget_soft_ratio: float = 0.7
    # Always route secondary reasoning to the fast model, regardless of budget.
    llm_economy_mode: bool = False

    # --- Backup LLM provider (MiniMax, OpenAI-compatible) ---------------------
    # Used as automatic failover when the primary (Anthropic) call fails after
    # retries — e.g. credit exhaustion, an outage, or the circuit opening. The
    # structured-output guarantee is preserved via OpenAI-style forced tool use.
    # Gated: with no key, failover is a no-op and Anthropic failures surface as
    # before. NOTE (PDPA): MiniMax is a PRC-based provider; enabling failover
    # routes candidate PII to it — confirm a region/DPA posture before go-live.
    minimax_api_key: str = ""
    minimax_base_url: str = "https://api.minimax.io/v1"
    minimax_model: str = "MiniMax-M2.5"
    # Vision-capable model for the image-transcription failover (photo intake).
    minimax_vision_model: str = "MiniMax-VL-01"
    # Master switch for failover (independent of key presence).
    llm_fallback_enabled: bool = True

    @property
    def minimax_configured(self) -> bool:
        return self.llm_fallback_enabled and bool(self.minimax_api_key.strip())

    # --- Google Cloud Vertex AI (Gemini 2.5, optional secondary routing) ----------
    # Enables cost-optimized secondary workloads (trajectory, summarization) via
    # Google's Gemini 2.5 model. When enabled + configured, "secondary" reasoning
    # routes to Gemini instead of Haiku (or MiniMax). Reduces cost ~60% vs Claude
    # while maintaining high quality for non-critical verdicts. Requires credentials:
    # 1. GCP service account JSON (base64-encoded in GOOGLE_APPLICATION_CREDENTIALS env)
    # 2. GCP project ID with Vertex AI enabled
    # 3. Region (default: us-central1; supports any region with Vertex AI)
    # Master switch: when false, Gemini is never used (all secondary → Haiku fallback).
    gemini_enabled: bool = False
    # GCP project ID where Vertex AI is enabled (e.g., "truematch-ai-prod")
    gemini_project_id: str = ""
    # GCP region hosting Vertex AI (e.g., "us-central1", "asia-southeast1")
    gemini_region: str = "us-central1"
    # Model selection for primary vs secondary work.
    # Primary: "gemini-2.5-pro" (reasoning-heavy, capability verdicts).
    # Secondary: "gemini-2.5-flash" (fast, cost-optimized, 60% cheaper than pro).
    gemini_primary_model: str = "gemini-2.5-pro"
    gemini_secondary_model: str = "gemini-2.5-flash"
    # Timeout for Gemini API calls (same budget as Claude to keep parity).
    gemini_timeout_seconds: float = 120.0
    # Fallback chain priority when Claude fails:
    # 1. Try primary (Claude Sonnet) → 2. Fallback to Gemini (if configured) →
    # 3. MiniMax (if configured) → 4. Deterministic mock.
    # When false, skips Gemini and goes straight to MiniMax/mock on Claude failure.
    gemini_fallback_enabled: bool = True
    # Route secondary reasoning to Gemini instead of Haiku (cost optimization).
    # When true, "secondary" calls skip Haiku and go → Gemini 2.5 Flash.
    # When false, secondary calls → Haiku as before (Gemini unused unless fallback).
    gemini_route_secondary: bool = False

    @property
    def gemini_configured(self) -> bool:
        """True when Gemini is enabled and GCP credentials are present."""
        return (
            self.gemini_enabled
            and bool(self.gemini_project_id.strip())
            and self.gemini_project_id != "placeholder"
        )

    # High-assurance assessments: run the capability judgment 3x in parallel and
    # report median + spread (uncertainty as a signal). Triples capability cost.
    assessment_high_assurance: bool = False
    # Reuse a prior completed assessment's results when (resume text + JD text +
    # prompt registry version) hash matches — effective determinism for repeats.
    assessment_reuse_identical: bool = True

    # Selective evidence verification: even when inline enrichment is disabled,
    # verify external links AFTER an assessment when the reasoning actually
    # relied on them (targeted, async, candidate-supplied public links only).
    enrichment_selective: bool = False

    # External-evidence enrichment (Pillar 5). When disabled, supplementary links
    # are recorded as UNVERIFIED rather than fetched — keeps the pipeline offline
    # and test-safe. Enable in environments with outbound network access.
    enrichment_enabled: bool = False
    enrichment_timeout_seconds: float = 12.0
    # Optional Lens.org patent API token. When set, filed patent numbers are
    # cross-checked against the public patent record and promoted to `verified`
    # once the application publishes (≈18 months post-filing). Without a token,
    # patents stay recorded-but-unverified with an honest "verifiable on
    # publication" reason — never silently treated as confirmed.
    lens_api_token: str = ""

    # Semantic matcher (Pillar 1). Static embeddings (deterministic) catch
    # conceptual matches the lexical floor misses; falls back to lexical when the
    # embedding model is unavailable (offline). Both are reproducible.
    semantic_use_embeddings: bool = True
    # Multilingual static embeddings (101 languages) — same model2vec loader as the
    # English model, so it is a drop-in. Enables non-English résumés/JDs to score
    # semantically (and cross-lingually: a Japanese CV vs an English JD share one
    # vector space). Falls back to the deterministic lexical signal when the model
    # is unavailable; under the English-pivot intake path that fallback is also
    # correct because the scored text has already been translated to English.
    semantic_embedding_model: str = "minishlab/potion-multilingual-128M"
    semantic_embedding_threshold: float = 0.40
    # Semantic score at/above which a surfaced candidate is a "strong match"
    # (concept-matching already endorses) vs a "hidden gem" (only deep capability
    # reasoning finds them). Used to classify the counter-recommendation.
    semantic_confirm_threshold: int = 60

    # Auth
    jwt_secret: str = Field(
        default="",
        description="JWT signing secret (32+ chars). Generate with: secrets.token_urlsafe(32)",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # S3 / AWS
    s3_bucket: str = "truematch-uploads"
    aws_region: str = "ap-southeast-1"
    aws_access_key_id: str = Field(
        default="",
        description="AWS access key ID. Never use 'placeholder' in production",
    )
    aws_secret_access_key: str = Field(
        default="",
        description="AWS secret access key",
    )
    # Optional KMS key for S3 server-side encryption. When set, objects use
    # aws:kms; otherwise AES256 (SSE-S3). Uploads are always server-side encrypted.
    s3_kms_key_id: str = ""
    max_upload_bytes: int = 5_000_000  # 5 MB cap on resume uploads

    @property
    def s3_enabled(self) -> bool:
        """Whether S3 file storage is enabled with valid credentials."""
        return (
            bool(self.aws_access_key_id)
            and bool(self.aws_secret_access_key)
            and self.aws_access_key_id != "placeholder"
            and self.aws_secret_access_key != "placeholder"
        )

    @property
    def s3_configured(self) -> bool:
        """Deprecated: use s3_enabled instead."""
        return self.s3_enabled

    # Field-level encryption (PII at rest). Keys are base64-encoded and injected
    # from a secrets manager / KMS-wrapped at deploy time. NEVER committed.
    #   encryption_key       : 32-byte base64 AES-256 data-encryption key
    #   encryption_index_key : base64 HMAC key for searchable blind indexes
    # When unset, the app runs UNENCRYPTED (dev only) and logs a warning.
    encryption_key: str = Field(
        default="",
        description="Base64-encoded AES-256 key (32 bytes). Generate: secrets.token_hex(32)",
    )
    encryption_index_key: str = Field(
        default="",
        description="Base64-encoded blind index key (32 bytes). Generate: secrets.token_hex(32)",
    )

    # Governance — only the PATH lives in config, never the values.
    governance_config_path: str = "./governance/config.example.json"

    # Singpass (Singapore NDI) OIDC. When unconfigured, the auth flow runs in a
    # bounded DEV mode that returns a deterministic identity (no real NDI calls).
    singpass_issuer: str = ""  # OIDC discovery base, e.g. https://id.singpass.gov.sg
    singpass_client_id: str = ""
    singpass_redirect_uri: str = "https://api.truematch.digital/v1/auth/singpass/callback"
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
    # Google Drive ingestion: poll a Drive folder where each candidate submission
    # is a subfolder containing one CV and one JD. Disabled unless a folder id +
    # access token are configured. The access token is an OAuth2 bearer (service
    # account or user) with read access to the folder.
    drive_ingest_enabled: bool = False
    drive_ingest_folder_id: str = ""
    drive_ingest_access_token: str = ""
    drive_ingest_poll_seconds: float = 120.0
    # Auto-report: when on, a completed assessment renders candidate + recruiter
    # PDFs to auto_report_output_dir (the concierge fulfilment hand-off). Off by
    # default; rendering never blocks or fails the assessment.
    auto_report_enabled: bool = False
    auto_report_output_dir: str = "./reports_out"
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

    # Autonomous Agent Loop Configuration
    autonomous_mode_enabled: bool = True

    # Email Service Configuration (Production-Ready)
    EMAIL_PROVIDER: str = Field(
        default="smtp",
        description="Email provider: 'smtp', 'sendgrid', or 'ses'"
    )
    EMAIL_FROM_ADDRESS: str = Field(
        default="noreply@truematch.digital",
        description="Sender email address for notifications"
    )

    # SMTP Configuration (if using SMTP provider)
    SMTP_SERVER: str = Field(
        default="smtp.gmail.com",
        description="SMTP server hostname"
    )
    SMTP_PORT: int = Field(
        default=587,
        description="SMTP port (587 for TLS, 465 for SMTPS)"
    )
    SMTP_USE_TLS: bool = Field(
        default=True,
        description="Use TLS encryption for SMTP"
    )
    SMTP_USERNAME: str = Field(
        default="",
        description="SMTP username for authentication"
    )
    SMTP_PASSWORD: str = Field(
        default="",
        description="SMTP password for authentication"
    )

    # SendGrid Configuration (if using SendGrid provider)
    SENDGRID_API_KEY: str = Field(
        default="",
        description="SendGrid API key for email delivery"
    )

    # AWS SES Configuration (if using SES provider)
    AWS_REGION: str = Field(
        default="us-east-1",
        description="AWS region for SES (if using SES provider)"
    )

    # Legacy email/SMTP config (kept for backward compatibility)
    # SMTP server for sending notification emails
    smtp_server: str = ""  # e.g., smtp.gmail.com
    smtp_port: int = 587  # TLS port (not 465 for SMTPS or 25 for plain)
    smtp_username: str = ""  # email account for sending
    smtp_password: str = ""  # SMTP password or app-specific password
    smtp_from_email: str = "noreply@truematch.digital"
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
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ]

    # Observability / ops
    log_json: bool = True  # structured JSON logs (set false for human-readable dev logs)
    log_level: str = "INFO"
    sentry_dsn: str = ""  # error tracking; disabled when blank
    metrics_enabled: bool = True  # expose Prometheus /metrics
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 120  # per client IP; 0 disables

    # Push notifications (FCM HTTP v1 / APNs). When unconfigured the dispatcher
    # is a no-op that logs intent — device registration still works, so the
    # client side is exercisable without provider credentials.
    push_enabled: bool = True
    fcm_project_id: str = ""           # Firebase project id (Android + iOS via FCM)
    fcm_credentials_json: str = ""     # path to service-account JSON, or inline JSON

    @property
    def push_configured(self) -> bool:
        """True when a real push provider credential is available."""
        return bool(self.fcm_project_id and self.fcm_credentials_json)

    # Audio resume intake (speech-to-text). Gated like push/email/S3: when no
    # provider credential is present the endpoint returns 503 rather than
    # pretending. Provider "openai" uses the Whisper transcription HTTP API.
    transcription_provider: str = ""  # "" (disabled) | "openai"
    transcription_api_key: str = ""
    transcription_model: str = "whisper-1"
    transcription_api_base: str = "https://api.openai.com/v1"
    transcription_max_bytes: int = 25_000_000  # provider hard limit is ~25 MB

    @property
    def transcription_configured(self) -> bool:
        """True when a real speech-to-text provider credential is available."""
        return bool(self.transcription_provider and self.transcription_api_key)

    # Auto-rescore: when a JD edit produces drift at/above this severity the
    # platform re-runs assessments for that position's active candidates.
    # Hash idempotency means unchanged inputs replay for free.
    auto_rescore_on_drift: bool = True
    auto_rescore_max_candidates: int = 200  # safety cap per drift event

    # Self-learned role taxonomy: deterministic cosine clustering of position
    # JDs into role families (model2vec embeddings). Rebuilt on a schedule.
    role_taxonomy_enabled: bool = True
    role_taxonomy_similarity: float = 0.62  # cosine threshold to join a cluster

    # Transition Intelligence: from an evidenced capability verdict, predict the
    # adjacent / higher-complexity roles a candidate could move into, the
    # upskilling gap, and an honest timeline. Candidate-facing, gated; reasons
    # over existing capability signals only (no physiological/biometric data,
    # no patented method encoded in product code).
    transition_intelligence_enabled: bool = True
    # Phase 3 longitudinal tracking: scheduled re-assessment of opted-in analyses
    # so a candidate's readiness/capability trajectory accumulates, plus outcome
    # recording for cohort "did they actually transition?" metrics.
    transition_tracking_enabled: bool = True
    transition_reassess_interval_days: int = 90

    # Training recommendations (Phase 2): map a candidate's upskilling gap to
    # concrete courses via pluggable providers. The curated catalog is built-in
    # and offline-safe; external partners are individually gated and are no-ops
    # until configured. To add a partner: implement the TrainingProvider
    # protocol, register it in app/services/training/__init__.py, add a flag here.
    training_recommendations_enabled: bool = True
    training_curated_enabled: bool = True
    skillsfuture_enabled: bool = True
    ntuc_learninghub_enabled: bool = False
    ntuc_learninghub_api_base: str = ""
    ntuc_learninghub_api_key: str = ""

    # Durable agent plans: a plan stuck "running" with no update for longer
    # than this is considered stalled and re-enqueued by the beat task.
    plan_stall_seconds: int = 600

    # Interview-content analysis: default duration when auto-scheduling.
    interview_default_minutes: int = 60

    # 2-way calendar sync. Gated like the other external integrations: when no
    # provider is configured the auto-scheduler still books locally (against
    # InterviewSlot availability), it just doesn't mirror to an external calendar.
    calendar_provider: str = ""  # "" | "google" | "microsoft"
    calendar_api_token: str = ""        # OAuth access token / service token
    calendar_api_base: str = ""         # override (e.g. Graph / Google base URL)
    calendar_organizer_email: str = ""  # calendar the events are written to

    @property
    def calendar_configured(self) -> bool:
        return bool(self.calendar_provider and self.calendar_api_token)

    # External ATS connectors. Each is gated on its own API key. Import maps the
    # provider's jobs -> Position and candidates -> Resume+Application.
    greenhouse_api_key: str = ""        # Harvest API key (Basic auth, key as username)
    greenhouse_api_base: str = "https://harvest.greenhouse.io/v1"
    lever_api_key: str = ""             # Lever API key (Basic auth)
    lever_api_base: str = "https://api.lever.co/v1"

    # Billing & payments (Stripe). Gated like every other external integration:
    # with no secret key, checkout returns 503 and enforcement is bypassed, so
    # the platform runs free/unmetered (current behavior) until configured.
    # We use Stripe-hosted Checkout only — card data never touches our servers.
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""     # whsec_... — verifies webhook signatures
    billing_currency: str = "usd"
    billing_success_url: str = "http://localhost:3000/billing/success?session_id={CHECKOUT_SESSION_ID}"
    billing_cancel_url: str = "http://localhost:3000/pricing?canceled=1"
    # Master switch for entitlement ENFORCEMENT at assessment-create. Default
    # off so the platform (and the test suite) behaves exactly as before until
    # billing is deliberately turned on. Checkout/webhook work regardless of
    # this flag — it only governs whether access is metered.
    billing_enforce: bool = False

    @property
    def stripe_configured(self) -> bool:
        """True when a real Stripe secret key is available."""
        return bool(self.stripe_secret_key)

    # Referrals: each completed assessment yields a shareable result + referral
    # code. A successful referral grants free credits to BOTH the referrer and
    # the new referee. A referee can only be referred once (anti-abuse).
    referral_enabled: bool = True
    referral_reward_credits: int = 1   # credits to referrer AND referee per referral
    share_base_url: str = "http://localhost:3000/share"  # public anonymised result page

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def encryption_enabled(self) -> bool:
        """Whether field-level encryption is enabled."""
        return bool(self.encryption_key and self.encryption_index_key)

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
