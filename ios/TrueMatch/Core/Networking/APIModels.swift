//
//  APIModels.swift
//  TrueMatch
//
//  Codable wire models for the TrueMatch API. The shared decoder uses
//  `.convertFromSnakeCase`, so snake_case JSON keys map to camelCase here.
//

import Foundation

// MARK: - Auth Models

struct SignUpRequest: Codable {
    let email: String
    let password: String
    let displayName: String?
}

struct LoginRequest: Codable {
    let email: String
    let password: String
}

struct SingpassCallbackRequest: Codable {
    let code: String
    let state: String
}

/// Server response to `/auth/singpass/init`: the authorization URL to open and
/// the opaque state the client echoes back on callback.
struct SingpassInitResponse: Codable {
    let authURL: String
    let state: String
}

struct AuthTokenResponse: Codable {
    let accessToken: String
    let refreshToken: String
    let expiresIn: Int
    let userId: String

    private enum CodingKeys: String, CodingKey {
        case accessToken, refreshToken, expiresIn, userId
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        accessToken = try c.decode(String.self, forKey: .accessToken)
        refreshToken = try c.decode(String.self, forKey: .refreshToken)
        // The backend's login/refresh response only returns the tokens; user id
        // and expiry live inside the JWT. Fall back to the access-token claims
        // (`sub`, `exp`) when the fields aren't sent explicitly so decoding a
        // valid 200 response never fails.
        let claims = JWTClaims(accessToken)
        userId = (try? c.decode(String.self, forKey: .userId)) ?? claims.subject ?? ""
        if let explicit = try? c.decode(Int.self, forKey: .expiresIn) {
            expiresIn = explicit
        } else {
            expiresIn = claims.secondsUntilExpiry ?? 1800
        }
    }

    init(accessToken: String, refreshToken: String, expiresIn: Int, userId: String) {
        self.accessToken = accessToken
        self.refreshToken = refreshToken
        self.expiresIn = expiresIn
        self.userId = userId
    }
}

/// Minimal, dependency-free decoder for the unverified payload claims of a JWT.
/// Used only to read `sub`/`exp` for local session bookkeeping — never for trust
/// decisions (the server validates the signature).
private struct JWTClaims {
    let subject: String?
    let secondsUntilExpiry: Int?

    init(_ token: String) {
        let parts = token.split(separator: ".")
        guard parts.count >= 2,
              let payloadData = JWTClaims.base64URLDecode(String(parts[1])),
              let json = try? JSONSerialization.jsonObject(with: payloadData) as? [String: Any]
        else {
            subject = nil
            secondsUntilExpiry = nil
            return
        }
        subject = json["sub"] as? String
        if let exp = json["exp"] as? Double {
            secondsUntilExpiry = max(0, Int(exp - Date().timeIntervalSince1970))
        } else {
            secondsUntilExpiry = nil
        }
    }

    private static func base64URLDecode(_ s: String) -> Data? {
        var base64 = s.replacingOccurrences(of: "-", with: "+")
                      .replacingOccurrences(of: "_", with: "/")
        let pad = base64.count % 4
        if pad > 0 { base64 += String(repeating: "=", count: 4 - pad) }
        return Data(base64Encoded: base64)
    }
}

// MARK: - File Models

struct FileUploadResponse: Codable, Identifiable {
    let id: String
    let fileName: String
    let mimeType: String
    let sizeBytes: Int
    let createdAt: Date
}

// MARK: - Assessment Request

struct CreateAssessmentRequest: Codable {
    /// ID returned by POST /files/upload for the candidate resume.
    let fileId: String
    /// Optional free-text supplementary information supplied by the candidate.
    let supplementary: String?
    /// The job description (raw text) the candidate is being assessed against.
    let jobDescription: String?

    init(fileId: String, supplementary: String? = nil, jobDescription: String? = nil) {
        self.fileId = fileId
        self.supplementary = supplementary
        self.jobDescription = jobDescription
    }
}

// MARK: - Assessment Status

enum AssessmentStatus: String, Codable {
    case queued
    case processing
    case completed
    case failed
}

// MARK: - Assessment Response

struct AssessmentResponse: Codable, Identifiable {
    let id: String
    let status: AssessmentStatus
    let traditionalScore: TraditionalScore?
    let capabilityScore: CapabilityScore?
    /// Difference between capability and traditional scores (capability - traditional).
    let delta: Double?
    let counterRecommendation: CounterRecommendation?
    let jdQuality: JDQuality?
    let trajectory: Trajectory?
    let governance: Governance?
    let createdAt: Date?
}

// MARK: - Traditional (keyword/ATS) Score

struct TraditionalScore: Codable {
    let score: Double
    let matchedKeywords: [String]
    let missingKeywords: [String]
    let explanation: String?
}

// MARK: - Capability Score

struct CapabilityScore: Codable {
    let score: Double
    let components: CapabilityComponents
    let narrative: String
    let evidence: [String]
}

struct CapabilityComponents: Codable {
    let demonstratedCapability: Double
    let domainDepth: Double
    let trajectoryStrength: Double
    let learningVelocity: Double
    let leadershipEvidence: Double
}

// MARK: - Counter Recommendation

struct CounterRecommendation: Codable {
    let triggered: Bool
    let reasoning: String?
    let evidencePoints: [String]
}

// MARK: - Job Description Quality

struct JDQuality: Codable {
    let score: Double
    let issues: [String]
    let recommendations: [String]
}

// MARK: - Trajectory

struct Trajectory: Codable {
    let direction: String
    let velocity: Double
    let domainCrossings: Int
    let narrative: String
    let invisibleCredentials: [String]
}

// MARK: - Governance (DISPLAY-ONLY)

/// Governance is provided by the backend and rendered as-is on the client.
/// The client never computes status or thresholds — it only displays the
/// `status` and `score`/`delta` values the backend returns.
struct Governance: Codable {
    let coherence: GovernanceMetric
    let consistency: GovernanceConsistency
    let fidelity: GovernanceMetric
    let biasFlags: [String]
    let auditId: String
}

struct GovernanceMetric: Codable {
    let status: String
    let score: Double
}

struct GovernanceConsistency: Codable {
    let status: String
    let delta: Double
}

// MARK: - Positions

struct PositionResponse: Codable, Identifiable {
    let id: String
    let title: String
    let department: String?
    let jobDescription: String
    let createdAt: Date
}

struct CreatePositionRequest: Codable {
    let title: String
    let department: String?
    let jobDescription: String
}

// MARK: - Decisions

struct DecisionResponse: Codable, Identifiable {
    let id: String
    let assessmentId: String
    let outcome: String
    let notes: String?
    let createdAt: Date
}

struct CreateDecisionRequest: Codable {
    let assessmentId: String
    let outcome: String
    let notes: String?
}

// MARK: - Profile

struct UserProfileResponse: Codable {
    let userId: String
    let displayName: String
    let email: String?
    let maskedNric: String?
}

struct UpdateProfileRequest: Codable {
    let displayName: String?
    let email: String?
}

// MARK: - Push Registration

struct PushTokenRegistration: Codable {
    let token: String
    let platform: String
}

// MARK: - Sync Models

struct SyncRequest: Codable {
    let actions: [OfflineActionPayload]
}

struct OfflineActionPayload: Codable {
    let localId: String
    let actionType: String
    let payload: String
    let createdAt: Date
}

struct SyncResponse: Codable {
    let processedCount: Int
    let failedIds: [String]
}

// MARK: - Agent Models

/// A single item in the autonomous ingest queue.
struct IngestQueueItem: Codable, Identifiable {
    let id: String
    let source: String           // "email" | "folder" | "api" | "webhook"
    let ingestType: String       // "cv" | "jd_draft"
    let status: String           // "pending"|"extracting"|"matching"|"processing"|
                                 // "completed"|"failed"|"rejected"|"awaiting_review"
    let resumeId: String?
    let assessmentId: String?
    let positionId: String?
    let retryCount: Int
    let createdAt: String
    // Detail fields (only present in GET /agents/queue/{id})
    let lastError: String?
    let jdAgentOutput: JDAgentOutput?
    let reviewNotes: String?

    var statusColor: String {
        switch status {
        case "completed": return "success"
        case "awaiting_review": return "warning"
        case "failed", "rejected": return "destructive"
        default: return "secondary"
        }
    }
}

struct JDAgentOutput: Codable {
    let qualityScore: Int?
    let issues: [JDIssue]?
    let titleHint: String?
}

struct JDIssue: Codable {
    let type: String
    let severity: String?
    let detail: String?
    let recommendation: String?
}

struct JDSuggestionsResponse: Codable {
    let positionId: String
    let status: String
    let jdImprovedDraft: String?
    let jdAgentOutput: JDAgentOutput?
    let createdAt: String?
}

struct AgentTriggerRequest: Codable {
    let resumeId: String
    let positionId: String?
    let jdText: String?
}

struct AgentTriggerResponse: Codable {
    let assessmentId: String
    let status: String
}

struct JDDraftRequest: Codable {
    let jdText: String
    let positionId: String?
    let title: String?
}

struct QueueActionRequest: Codable {
    let notes: String?
}

struct ReassignRequest: Codable {
    let positionId: String
    let notes: String?
}

// MARK: - Agent WebSocket Events

enum AgentEvent: Decodable {
    case itemApproved(id: String, status: String)
    case itemRejected(id: String)
    case itemCompleted(id: String, assessmentId: String?)
    case pong
    case unknown

    private enum CodingKeys: String, CodingKey { case event, id, status, assessmentId }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        let event = (try? c.decode(String.self, forKey: .event)) ?? ""
        let id = (try? c.decode(String.self, forKey: .id)) ?? ""
        switch event {
        case "item_approved":
            let status = (try? c.decode(String.self, forKey: .status)) ?? ""
            self = .itemApproved(id: id, status: status)
        case "item_rejected": self = .itemRejected(id: id)
        case "item_completed":
            let aid = try? c.decode(String.self, forKey: .assessmentId)
            self = .itemCompleted(id: id, assessmentId: aid)
        default: self = .unknown
        }
    }
}

// MARK: - Learning & Feedback (Phase 1)

struct RecordOutcomeRequest: Codable {
    let outcome: String  // "hired" | "rejected" | "counter"
    let outcomeReason: String?
    let performanceData: PerformanceDataRequest?
    let hiringManagerRating: Int?
    let counterRecDetails: CounterRecDetails?

    init(
        outcome: String,
        outcomeReason: String? = nil,
        performanceData: PerformanceDataRequest? = nil,
        hiringManagerRating: Int? = nil,
        counterRecDetails: CounterRecDetails? = nil
    ) {
        self.outcome = outcome
        self.outcomeReason = outcomeReason
        self.performanceData = performanceData
        self.hiringManagerRating = hiringManagerRating
        self.counterRecDetails = counterRecDetails
    }
}

struct PerformanceDataRequest: Codable {
    let timeToHire: Int?           // days
    let timeToProductivity: Int?   // days
    let retentionMonths: Int?
    let performanceRating: Double?
    let notes: String?
}

struct CounterRecDetails: Codable {
    let hired: Bool
    let reason: String?
}

struct FeedbackStatusResponse: Codable {
    let assessmentId: String
    let hasOutcome: Bool
    let lastOutcomeAt: String?
}

struct LearningMetricsResponse: Codable {
    let metricDate: String
    let modelVersion: String
    let totalAssessments: Int
    let totalOutcomes: Int
    let accuracy: Double?
    let precision: Double?
    let recall: Double?
    let f1Score: Double?
    let expectedCalibrationError: Double?
    let avgConfidence: Double?
    let falsePositiveRate: Double?
    let falseNegativeRate: Double?
    let metricsByRole: [String: RoleMetrics]?
}

struct RoleMetrics: Codable {
    let accuracy: Double?
    let precision: Double?
    let recall: Double?
    let f1Score: Double?
    let totalAssessments: Int
    let totalOutcomes: Int
}

// MARK: - Generic Response

struct PaginatedResponse<T: Codable>: Codable {
    let data: [T]
    let cursor: String?
    let hasMore: Bool
}

// MARK: - Match Notifications (Transparency Feature)

enum NotificationStatus: String, Codable {
    case profileSent = "profile_sent"
    case profileViewed = "profile_viewed"
    case interviewScheduled = "interview_scheduled"
    case interviewCompleted = "interview_completed"
    case offerReceived = "offer_received"
    case rejected = "rejected"
}

struct MatchNotification: Codable, Identifiable {
    let id: String
    let matchId: String
    let status: NotificationStatus
    let message: String?
    let timestamp: Date
    let emailSent: Bool

    enum CodingKeys: String, CodingKey {
        case id, status, message, emailSent
        case matchId = "matchId"
        case timestamp = "statusTimestamp"
    }
}

struct MatchNotificationResponse: Codable {
    let matchId: String
    let events: [MatchNotification]
}

// MARK: - Candidate Match with Persona Info

struct CandidateMatch: Codable, Identifiable {
    let id: String
    let positionId: String
    let overallScore: Int
    let fitLevel: String
    let matchedByPersona: String?
    let personaConfidence: Int
    let personaReasoning: String?
    let concerns: [String]?
    let opportunities: [String]?

    enum CodingKeys: String, CodingKey {
        case id, concerns, opportunities
        case positionId = "positionId"
        case overallScore = "overallScore"
        case fitLevel = "fitLevel"
        case matchedByPersona = "matchedByPersona"
        case personaConfidence = "personaConfidence"
        case personaReasoning = "personaReasoning"
    }
}

// MARK: - Privacy Preferences

enum PrivacyLevel: String, Codable {
    case hidden = "hidden"
    case passive = "passive"
    case active = "active"
}

struct PrivacyPreferences: Codable {
    let privacyLevel: PrivacyLevel
    let currentEmployer: String?
    let blockedCompanies: [String]?

    enum CodingKeys: String, CodingKey {
        case privacyLevel = "privacyLevel"
        case currentEmployer = "currentEmployer"
        case blockedCompanies = "blockedCompanies"
    }
}

struct UpdatePrivacyPreferencesRequest: Codable {
    let privacyLevel: PrivacyLevel
    let blockedCompanies: [String]?
}

// MARK: - Job Filtering with Quality Thresholds

struct JobFilterRequest: Codable {
    let locations: [String]?
    let jobTypes: [String]?
    let matchScoreMin: Int?
    let workTypes: [String]?  // "full-time", "fractional", "advisory"
    let salaryMin: Int?
    let salaryMax: Int?
    let industries: [String]?
    let sortBy: String?  // "match", "salary", "recency"
    let sortOrder: String?  // "asc", "desc"

    init(
        locations: [String]? = nil,
        jobTypes: [String]? = nil,
        matchScoreMin: Int? = nil,
        workTypes: [String]? = nil,
        salaryMin: Int? = nil,
        salaryMax: Int? = nil,
        industries: [String]? = nil,
        sortBy: String? = "match",
        sortOrder: String? = "desc"
    ) {
        self.locations = locations
        self.jobTypes = jobTypes
        self.matchScoreMin = matchScoreMin
        self.workTypes = workTypes
        self.salaryMin = salaryMin
        self.salaryMax = salaryMax
        self.industries = industries
        self.sortBy = sortBy
        self.sortOrder = sortOrder
    }
}

struct JobWithPersona: Codable, Identifiable {
    let id: String
    let title: String
    let company: String
    let location: String
    let matchScore: Double
    let jobType: String
    let remote: String  // "fully", "hybrid", "onsite"
    let salaryMin: Int?
    let salaryMax: Int?
    let salary_currency: String?
    let level: String
    let matchedByPersona: String?
    let personaIcon: String?
    let isHiddenGem: Bool?
}

// MARK: - Recruiter Search & Decision Models

struct SearchCandidatesRequest: Codable {
    let query: String?
    let skills: [String]?
    let experience: String?
    let location: String?
    let availabilityMin: String?
}

struct RecordDecisionRequest: Codable {
    let decision: String  // "interested", "rejected", "hold"
    let notes: String?
}

// MARK: - Candidate Job Recommendations Models

struct GetJobRecommendationsRequest: Codable {
    let qualityThreshold: String?  // "80%+", "60%+", "40%+"
    let limit: Int?
    let offset: Int?
}

struct SaveJobRequest: Codable {
    let jobId: String
    let personalization: String?
}

struct RejectJobRequest: Codable {
    let jobId: String
    let reason: String?
}

struct GetApplicationsRequest: Codable {
    let status: String?  // "draft", "submitted", "reviewed", "accepted", "rejected"
    let limit: Int?
    let offset: Int?
}
