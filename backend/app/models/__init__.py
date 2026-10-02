"""SQLAlchemy ORM models for TrueMatch."""
from app.models.agent_config import (
    AgentConfig,
    AgentConfigAudit,
    AgentConfigAuditAction,
    AgentConfigStatus,
    AgentConfigVersion,
)
from app.models.agent_plan import AgentPlan
from app.models.analysis_result import AnalysisResult, AnalysisStatus
from app.models.application import Application
from app.models.application_timeline import ApplicationTimeline, EventType
from app.models.assessment import Assessment
from app.models.assessment_design import AssessmentDesign
from app.models.audit import AuditTrail

# Previously missing from the package init — meaning these tables were absent
# so the metadata is complete and migrations stay accurate.
from app.models.autonomous_settings import AutonomousSettings
from app.models.billing import Coupon, CreditLedger, Entitlement, Order, WebhookEvent
from app.models.candidate_archetype import CandidateArchetype
from app.models.candidate_match import PERSONA_ICONS, CandidateMatch, FitLevel, MatchStatus
from app.models.capability_translation import CapabilityTranslation, TranslationStatus
from app.models.career_coach import (
    CareerCoaching,
    CareerGoal,
    CoachingProgressReport,
    CoachingSession,
    CoachQuestion,
    InterviewPrepSession,
    PersonalizedCareerPlan,
    SkillAssessment,
)
from app.models.chat import (
    ChatMessage,
    ChatSession,
    Conversation,
    ConversationStatus,
    Message,
    MessageRole,
)
from app.models.chat_memory import ChatSessionMemory
from app.models.company import Company
from app.models.corpus import CorpusTermStat
from app.models.cv_analysis import CVAnalysisRequest, CVAnalysisResult
from app.models.decision import Decision
from app.models.device_token import DeviceToken
from app.models.disparate_impact import DisparateImpactAnalysis, DisparateImpactFlag
from app.models.dsar import DSARRequest, DSARStatus
from app.models.governance_log import GateName, GovernanceLog
from app.models.governance_review import GovernanceReview, ReviewStatus, ReviewType
from app.models.ingest_queue import IngestQueueItem
from app.models.interview import Interview, InterviewSlot, Scorecard
from app.models.jd_simulation import JDSimulationRequest, JDSimulationResult
from app.models.jd_version import JDVersion
from app.models.job_application import (
    ApplicationEventType as JobApplicationEventType,
)
from app.models.job_application import (
    ApplicationStatus,
    JobApplication,
)
from app.models.job_scraping import (
    BatchStatus,
    JobDeduplication,
    JobScrapingConfig,
    JobSourceType,
    MassUploadBatch,
    ScrapingRun,
    UploadFieldMapping,
    UploadType,
)
from app.models.match_notification import MatchNotification, NotificationStatus
from app.models.notification import Notification, NotificationPreference, NotificationType
from app.models.position import Position
from app.models.profile import CapabilityProfile
from app.models.referral import ReferralCode, ReferralRedemption, SharedResult
from app.models.resume import Resume
from app.models.resume_version import ResumeVersion
from app.models.role_cluster import RoleCluster
from app.models.saved_job import SavedJob, SavedJobsList
from app.models.screening import (
    RecruiterDecision,
    ScreeningBatch,
    ScreeningBatchStatus,
    ScreeningRecommendation,
    ScreeningResult,
)
from app.models.training import (
    CapabilityMapping,
    CredentialMapping,
    FeedbackType,
    SuccessPattern,
    TrainingFeedback,
    TrainingInsight,
    TrainingProgress,
    VirtualBrainState,
)
from app.models.training_data import (
    TrainingChatMessage,
    TrainingDataItem,
    TrainingDataUpload,
    TrainingInsightBatch,
    TrainingLearningSession,
)
from app.models.transition_analysis import (
    OutcomeStatus,
    TransitionAnalysis,
    TransitionOutcome,
    TransitionStatus,
)
from app.models.user import User, UserRole
from app.models.user_memory import UserAgentMemory

__all__ = [
    "TransitionAnalysis",
    "TransitionOutcome",
    "TransitionStatus",
    "OutcomeStatus",
    "Application",
    "ApplicationTimeline",
    "EventType",
    "JobApplication",
    "ApplicationStatus",
    "JobApplicationEventType",
    "Assessment",
    "AnalysisResult",
    "AnalysisStatus",
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
    "Conversation",
    "Message",
    "ConversationStatus",
    "MessageRole",
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
    "AgentConfig",
    "AgentConfigVersion",
    "AgentConfigAudit",
    "AgentConfigStatus",
    "AgentConfigAuditAction",
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
    "ScreeningBatch",
    "ScreeningResult",
    "ScreeningRecommendation",
    "ScreeningBatchStatus",
    "RecruiterDecision",
    "CareerCoaching",
    "CareerGoal",
    "PersonalizedCareerPlan",
    "SkillAssessment",
    "InterviewPrepSession",
    "CoachingSession",
    "CoachQuestion",
    "CoachingProgressReport",
    "CandidateMatch",
    "MatchStatus",
    "FitLevel",
    "PERSONA_ICONS",
    "MatchNotification",
    "NotificationStatus",
    "AssessmentDesign",
]
