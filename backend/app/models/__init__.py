"""SQLAlchemy ORM models for TrueMatch."""
from app.models.application import Application
from app.models.assessment import Assessment
from app.models.audit import AuditTrail
from app.models.candidate_archetype import CandidateArchetype
from app.models.company import Company
from app.models.corpus import CorpusTermStat
from app.models.cv_analysis import CVAnalysisRequest, CVAnalysisResult
from app.models.decision import Decision
from app.models.ingest_queue import IngestQueueItem
from app.models.interview import Interview, InterviewSlot, Scorecard
from app.models.jd_simulation import JDSimulationRequest, JDSimulationResult
from app.models.jd_version import JDVersion
from app.models.notification import Notification, NotificationPreference, NotificationType
from app.models.position import Position
from app.models.profile import CapabilityProfile
from app.models.resume import Resume
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

__all__ = [
    "Application",
    "Assessment",
    "AuditTrail",
    "CandidateArchetype",
    "Company",
    "CorpusTermStat",
    "CVAnalysisRequest",
    "CVAnalysisResult",
    "Decision",
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
]
