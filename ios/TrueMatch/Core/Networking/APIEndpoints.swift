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
}
