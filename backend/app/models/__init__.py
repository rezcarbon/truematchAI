"""SQLAlchemy ORM models for TrueMatch."""
from app.models.application import Application
from app.models.application_timeline import ApplicationTimeline, EventType
from app.models.assessment import Assessment
from app.models.audit import AuditTrail
from app.models.candidate_archetype import CandidateArchetype
from app.models.company import Company
from app.models.corpus import CorpusTermStat
from app.models.cv_analysis import CVAnalysisRequest, CVAnalysisResult
from app.models.decision import Decision
from app.models.disparate_impact import DisparateImpactAnalysis, DisparateImpactFlag
from app.models.dsar import DSARRequest, DSARStatus
from app.models.governance_log import GovernanceLog, GateName
from app.models.ingest_queue import IngestQueueItem
from app.models.interview import Interview, InterviewSlot, Scorecard
from app.models.jd_simulation import JDSimulationRequest, JDSimulationResult
from app.models.jd_version import JDVersion
from app.models.notification import Notification, NotificationPreference, NotificationType
from app.models.position import Position
from app.models.profile import CapabilityProfile
from app.models.resume import Resume
from app.models.resume_version import ResumeVersion
from app.models.saved_job import SavedJob, SavedJobsList
from app.models.user import User, UserRole
from app.models.training import (
    TrainingFeedback,
    FeedbackType,
    CapabilityMapping,
    CredentialMapping,
    SuccessPattern,
    TrainingProgress,
    TrainingInsight,
    VirtualBrainState,
)
# Previously missing from the package init — meaning these tables were absent
# from Base.metadata and alembic autogenerate wanted to DROP them. Import here
# so the metadata is complete and migrations stay accurate.
from app.models.autonomous_settings import AutonomousSettings
from app.models.chat import ChatSession, ChatMessage
from app.models.chat_memory import ChatSessionMemory
from app.models.governance_review import GovernanceReview, ReviewType, ReviewStatus
from app.models.job_scraping import (
    JobScrapingConfig,
    ScrapingRun,
    MassUploadBatch,
    JobDeduplication,
    UploadFieldMapping,
    JobSourceType,
    UploadType,
    BatchStatus,
)
from app.models.training_data import (
    TrainingDataUpload,
    TrainingDataItem,
    TrainingChatMessage,
    TrainingInsightBatch,
    TrainingLearningSession,
)
from app.models.device_token import DeviceToken
from app.models.agent_plan import AgentPlan
from app.models.user_memory import UserAgentMemory
from app.models.role_cluster import RoleCluster
from app.models.billing import Order, Entitlement, CreditLedger, Coupon, WebhookEvent
from app.models.referral import ReferralCode, ReferralRedemption, SharedResult
from app.models.capability_translation import CapabilityTranslation, TranslationStatus
from app.models.transition_analysis import (
    OutcomeStatus,
    TransitionAnalysis,
    TransitionOutcome,
    TransitionStatus,
)

__all__ = [
    "TransitionAnalysis",
    "TransitionOutcome",
    "TransitionStatus",
    "OutcomeStatus",
    "Application",
    "ApplicationTimeline",
    "EventType",
    "Assessment",
    "AuditTrail",
    "CandidateArchetype",
    "Company",
    "CorpusTermStat",
    "CapabilityTranslation",
    "TranslationStatus",
    "CVAnalysisRequest",
    "CVAnalysisResult",
    "Decision",
    "DisparateImpactAnalysis",
    "DisparateImpactFlag",
    "DSARRequest",
    "DSARStatus",
    "GateName",
    "GovernanceLog",
    "IngestQueueItem",
    "Interview",
    "InterviewSlot",
    "JDSimulationRequest",
    "JDSimulationResult",
    "JDVersion",
    "Notification",
    "NotificationPreference",
    "NotificationType",
    "Position",
    "CapabilityProfile",
    "Resume",
    "ResumeVersion",
    "SavedJob",
    "SavedJobsList",
    "Scorecard",
    "User",
    "UserRole",
    "TrainingFeedback",
    "FeedbackType",
    "CapabilityMapping",
    "CredentialMapping",
    "SuccessPattern",
    "TrainingProgress",
    "TrainingInsight",
    "VirtualBrainState",
    "AutonomousSettings",
    "ChatSession",
    "ChatMessage",
    "ChatSessionMemory",
    "GovernanceReview",
    "ReviewType",
    "ReviewStatus",
    "JobScrapingConfig",
    "ScrapingRun",
    "MassUploadBatch",
    "JobDeduplication",
    "UploadFieldMapping",
    "JobSourceType",
    "UploadType",
    "BatchStatus",
    "TrainingDataUpload",
    "TrainingDataItem",
    "TrainingChatMessage",
    "TrainingInsightBatch",
    "TrainingLearningSession",
    "DeviceToken",
    "AgentPlan",
    "UserAgentMemory",
    "RoleCluster",
    "Order",
    "Entitlement",
    "CreditLedger",
    "Coupon",
    "WebhookEvent",
    "ReferralCode",
    "ReferralRedemption",
    "SharedResult",
]
