//
//  APIEndpoints.swift
//  TrueMatch
//

import Foundation

// MARK: - HTTP Method

enum HTTPMethod: String {
    case GET
    case POST
    case PUT
    case DELETE
    case PATCH
}

// MARK: - API Endpoint

struct APIEndpoint {
    let path: String
    let method: HTTPMethod
    let queryItems: [URLQueryItem]?
    let body: (any Encodable)?

    var url: URL? {
        var components = URLComponents(
            url: AppConfiguration.API.baseURL,
            resolvingAgainstBaseURL: true
        )
        components?.path += "/\(AppConfiguration.API.apiVersion)/\(path)"
        components?.queryItems = queryItems
        return components?.url
    }

    init(
        path: String,
        method: HTTPMethod = .GET,
        queryItems: [URLQueryItem]? = nil,
        body: (any Encodable)? = nil
    ) {
        self.path = path
        self.method = method
        self.queryItems = queryItems
        self.body = body
    }
}

// MARK: - Endpoint Definitions

extension APIEndpoint {

    // MARK: Auth

    static func signup(_ request: SignUpRequest) -> APIEndpoint {
        APIEndpoint(path: "auth/signup", method: .POST, body: request)
    }

    static func login(_ request: LoginRequest) -> APIEndpoint {
        APIEndpoint(path: "auth/login", method: .POST, body: request)
    }

    /// Begin a Singpass OIDC flow. The server generates PKCE + state + nonce and
    /// returns the authorization URL; the client only opens it and relays the
    /// callback. Token exchange happens server-side.
    static var singpassInit: APIEndpoint {
        APIEndpoint(path: "auth/singpass/init", method: .GET)
    }

    static func singpassCallback(code: String, state: String) -> APIEndpoint {
        APIEndpoint(
            path: "auth/singpass/callback",
            method: .POST,
            body: SingpassCallbackRequest(code: code, state: state)
        )
    }

    static var refreshToken: APIEndpoint {
        APIEndpoint(path: "auth/refresh", method: .POST)
    }

    static var deleteSession: APIEndpoint {
        APIEndpoint(path: "auth/session", method: .DELETE)
    }

    // MARK: Assessments

    static func createAssessment(_ request: CreateAssessmentRequest) -> APIEndpoint {
        APIEndpoint(path: "assessments", method: .POST, body: request)
    }

    static func listAssessments(cursor: String? = nil) -> APIEndpoint {
        var items: [URLQueryItem] = []
        if let cursor = cursor {
            items.append(URLQueryItem(name: "cursor", value: cursor))
        }
        return APIEndpoint(path: "assessments", queryItems: items.isEmpty ? nil : items)
    }

    static func assessment(id: String) -> APIEndpoint {
        APIEndpoint(path: "assessments/\(id)")
    }

    static func assessmentNarrative(id: String) -> APIEndpoint {
        APIEndpoint(path: "assessments/\(id)/narrative")
    }

    static func assessmentTrajectory(id: String) -> APIEndpoint {
        APIEndpoint(path: "assessments/\(id)/trajectory")
    }

    static func assessmentGovernance(id: String) -> APIEndpoint {
        APIEndpoint(path: "assessments/\(id)/governance")
    }

    static func assessmentTraditional(id: String) -> APIEndpoint {
        APIEndpoint(path: "assessments/\(id)/traditional")
    }

    static func assessmentComparison(id: String) -> APIEndpoint {
        APIEndpoint(path: "assessments/\(id)/comparison")
    }

    static func deleteAssessment(id: String) -> APIEndpoint {
        APIEndpoint(path: "assessments/\(id)", method: .DELETE)
    }

    // MARK: Files

    static var uploadFile: APIEndpoint {
        APIEndpoint(path: "files/upload", method: .POST)
    }

    static func file(id: String) -> APIEndpoint {
        APIEndpoint(path: "files/\(id)")
    }

    static func deleteFile(id: String) -> APIEndpoint {
        APIEndpoint(path: "files/\(id)", method: .DELETE)
    }

    // MARK: Positions

    static var listPositions: APIEndpoint {
        APIEndpoint(path: "positions")
    }

    /// Candidates in a position's pipeline (recruiter view).
    static func positionPipeline(id: String) -> APIEndpoint {
        APIEndpoint(path: "ats/positions/\(id)/pipeline")
    }

    // MARK: Workspace (recruiter / admin)

    /// Record a hiring decision (drives the learning loop server-side).
    static func recordDecision(_ request: DecisionRequest) -> APIEndpoint {
        APIEndpoint(path: "decisions", method: .POST, body: request)
    }

    /// Start a JD simulation.
    static func startJDSimulation(_ request: JDSimRequest) -> APIEndpoint {
        APIEndpoint(path: "recruiters/jd-simulation", method: .POST, body: request)
    }

    /// Poll a JD simulation result.
    static func jdSimulation(id: String) -> APIEndpoint {
        APIEndpoint(path: "recruiters/jd-simulation/\(id)")
    }

    /// Recruiter performance metrics.
    static var recruiterMetrics: APIEndpoint {
        APIEndpoint(path: "ats/recruiter-metrics/")
    }

    /// Admin system metrics.
    static var adminMetrics: APIEndpoint {
        APIEndpoint(path: "admin/metrics")
    }

    /// Governance review queue.
    static func governanceReviews(status: String? = nil) -> APIEndpoint {
        let qi = status.map { [URLQueryItem(name: "status", value: $0)] }
        return APIEndpoint(path: "governance-reviews", queryItems: qi)
    }

    /// Approve / reject / escalate a governance review.
    static func approveGovernanceReview(id: String, _ request: ApproveReviewRequest) -> APIEndpoint {
        APIEndpoint(path: "governance-reviews/\(id)/approve", method: .POST, body: request)
    }

    /// Compliance system status (provenance + learning).
    static var complianceStatus: APIEndpoint {
        APIEndpoint(path: "compliance/system-status")
    }

    // MARK: CV Analysis (candidate) + resumes

    /// List the current user's resumes.
    static var listResumes: APIEndpoint {
        APIEndpoint(path: "files/resumes")
    }

    /// Multimodal intake: upload a resume PHOTO; the backend transcribes it
    /// with vision and creates a Resume.
    static var uploadResumeImage: APIEndpoint {
        APIEndpoint(path: "files/resume/image", method: .POST)
    }

    /// Start a CV gap analysis.
    static func startCVAnalysis(_ request: CVAnalysisStartRequest) -> APIEndpoint {
        APIEndpoint(path: "candidates/cv-analysis", method: .POST, body: request)
    }

    /// Poll a CV analysis result.
    static func cvAnalysis(id: String) -> APIEndpoint {
        APIEndpoint(path: "candidates/cv-analysis/\(id)")
    }

    /// Start a Capability Translation (ATS-legible rewrite + measured lift).
    static func startCapabilityTranslation(_ request: CapabilityTranslationStartRequest) -> APIEndpoint {
        APIEndpoint(path: "candidates/capability-translation", method: .POST, body: request)
    }

    /// Poll a capability translation result.
    static func capabilityTranslation(id: String) -> APIEndpoint {
        APIEndpoint(path: "candidates/capability-translation/\(id)")
    }

    /// Start a Transition Intelligence analysis (adjacent/higher roles + upskilling).
    static func startTransition(_ request: TransitionStartRequest) -> APIEndpoint {
        APIEndpoint(path: "candidates/transition-intelligence", method: .POST, body: request)
    }

    /// Poll a transition-intelligence result.
    static func transition(id: String) -> APIEndpoint {
        APIEndpoint(path: "candidates/transition-intelligence/\(id)")
    }

    /// Enable/disable quarterly re-assessment for an analysis (Phase 3).
    static func setTransitionTracking(id: String, _ request: TransitionTrackRequest) -> APIEndpoint {
        APIEndpoint(path: "candidates/transition-intelligence/\(id)/track", method: .POST, body: request)
    }

    /// Capability/readiness trajectory for a résumé (Phase 3 longitudinal view).
    static func transitionTrajectory(resumeId: String) -> APIEndpoint {
        APIEndpoint(path: "candidates/transition-intelligence/trajectory/by-resume/\(resumeId)")
    }

    // MARK: Decisions audit (recruiter)

    static var listDecisions: APIEndpoint {
        APIEndpoint(path: "decisions")
    }

    // MARK: Admin console

    static var adminUsers: APIEndpoint {
        APIEndpoint(path: "admin/users")
    }

    static var adminAudit: APIEndpoint {
        APIEndpoint(path: "admin/audit")
    }

    static var adminAnalytics: APIEndpoint {
        APIEndpoint(path: "admin/analytics")
    }

    static var adminComplianceReport: APIEndpoint {
        APIEndpoint(path: "admin/compliance/report")
    }

    static func position(id: String) -> APIEndpoint {
        APIEndpoint(path: "positions/\(id)")
    }

    static func createPosition(_ request: CreatePositionRequest) -> APIEndpoint {
        APIEndpoint(path: "positions", method: .POST, body: request)
    }

    // MARK: Decisions

    static func decision(id: String) -> APIEndpoint {
        APIEndpoint(path: "decisions/\(id)")
    }

    static func createDecision(_ request: CreateDecisionRequest) -> APIEndpoint {
        APIEndpoint(path: "decisions", method: .POST, body: request)
    }

    // MARK: Profile

    static var profile: APIEndpoint {
        APIEndpoint(path: "profile")
    }

    static func updateProfile(_ request: UpdateProfileRequest) -> APIEndpoint {
        APIEndpoint(path: "profile", method: .PUT, body: request)
    }

    // MARK: Push Notifications

    static func registerPushToken(token: String, platform: String = "ios") -> APIEndpoint {
        APIEndpoint(
            path: "profile/push/register",
            method: .POST,
            body: PushTokenRegistration(token: token, platform: platform)
        )
    }

    // MARK: Sync

    static func syncOfflineActions(request: SyncRequest) -> APIEndpoint {
        APIEndpoint(path: "sync/actions", method: .POST, body: request)
    }

    // MARK: Agent Control

    /// Fetch the current ingest queue (optionally filtered by status).
    static func agentQueue(status: String? = nil) -> APIEndpoint {
        let qi = status.map { [URLQueryItem(name: "status", value: $0)] }
        return APIEndpoint(path: "agents/queue", method: .GET, queryItems: qi)
    }

    static func agentQueueItem(id: String) -> APIEndpoint {
        APIEndpoint(path: "agents/queue/\(id)", method: .GET)
    }

    static func approveQueueItem(id: String, notes: String? = nil) -> APIEndpoint {
        APIEndpoint(path: "agents/queue/\(id)/approve", method: .POST,
                    body: QueueActionRequest(notes: notes))
    }

    static func rejectQueueItem(id: String, notes: String? = nil) -> APIEndpoint {
        APIEndpoint(path: "agents/queue/\(id)/reject", method: .POST,
                    body: QueueActionRequest(notes: notes))
    }

    static func reassignQueueItem(id: String, positionId: String, notes: String? = nil) -> APIEndpoint {
        APIEndpoint(path: "agents/queue/\(id)/reassign", method: .POST,
                    body: ReassignRequest(positionId: positionId, notes: notes))
    }

    /// Manually trigger an assessment from iOS.
    static func agentTrigger(_ request: AgentTriggerRequest) -> APIEndpoint {
        APIEndpoint(path: "agents/trigger", method: .POST, body: request)
    }

    /// Submit a JD draft for autonomous analysis.
    static func submitJDDraft(_ request: JDDraftRequest) -> APIEndpoint {
        APIEndpoint(path: "agents/jd/draft", method: .POST, body: request)
    }

    /// Fetch AI-improved JD suggestions for a position.
    static func jdSuggestions(positionId: String) -> APIEndpoint {
        APIEndpoint(path: "agents/jd/\(positionId)/suggestions", method: .GET)
    }

    // MARK: Chat (conversational AI)

    /// Create a new chat session.
    static func createChatSession(_ request: CreateChatSessionRequest) -> APIEndpoint {
        APIEndpoint(path: "chat/sessions", method: .POST, body: request)
    }

    /// List the current user's chat sessions.
    static var listChatSessions: APIEndpoint {
        APIEndpoint(path: "chat/sessions", method: .GET)
    }

    /// Fetch a single session with its full message history.
    static func chatSession(id: String) -> APIEndpoint {
        APIEndpoint(path: "chat/sessions/\(id)", method: .GET)
    }

    /// Delete a chat session.
    static func deleteChatSession(id: String) -> APIEndpoint {
        APIEndpoint(path: "chat/sessions/\(id)", method: .DELETE)
    }

    /// Send a message to the role-aware agent (trailing slash matches the
    /// backend route to avoid a 307 redirect).
    static func sendChatMessage(_ request: ChatSendRequest) -> APIEndpoint {
        APIEndpoint(path: "chat/", method: .POST, body: request)
    }
}
