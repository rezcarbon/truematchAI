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

// MARK: - Generic Response

struct PaginatedResponse<T: Codable>: Codable {
    let data: [T]
    let cursor: String?
    let hasMore: Bool
}
