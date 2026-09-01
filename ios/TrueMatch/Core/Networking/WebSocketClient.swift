//
//  WebSocketClient.swift
//  TrueMatch
//
//  Streams live assessment progress (stage updates, partial scores, completion)
//  from the backend while an assessment is being computed.
//

import Foundation
import Combine

// MARK: - WebSocket Event

enum WebSocketEvent: Sendable {
    case connected
    case disconnected(Error?)
    case messageReceived(Data)
    case progress(AssessmentProgress)
    case stageUpdate(AssessmentStage)
    case completed(AssessmentResponse)
    case error(String)
}

// MARK: - Assessment Stage

enum AssessmentStage: String, Codable, Sendable {
    case parsingResume = "parsing_resume"
    case keywordMatch = "keyword_match"
    case capabilityAnalysis = "capability_analysis"
    case trajectoryAnalysis = "trajectory_analysis"
    case governanceReview = "governance_review"

    var displayText: String {
        switch self {
        case .parsingResume: return "Parsing resume..."
        case .keywordMatch: return "Matching keywords..."
        case .capabilityAnalysis: return "Analyzing capability..."
        case .trajectoryAnalysis: return "Mapping trajectory..."
        case .governanceReview: return "Governance review..."
        }
    }
}

// MARK: - Assessment Progress

struct AssessmentProgress: Codable, Sendable {
    let assessmentId: String
    let percent: Double
    let stage: AssessmentStage?
    let message: String?
}

// MARK: - Connection State

enum ConnectionState: Equatable, Sendable {
    case connected
    case connecting
    case disconnected
}

// MARK: - WebSocket Wire Message

private struct WSIncoming: Codable {
    let type: String
    let progress: AssessmentProgress?
    let stage: String?
    let assessment: AssessmentResponse?
    let error: String?
}

// MARK: - WebSocket Client

@MainActor
final class WebSocketClient: ObservableObject {
    @Published var connectionState: ConnectionState = .disconnected

    var isConnected: Bool { connectionState == .connected }

    private var webSocketTask: URLSessionWebSocketTask?
    private let session: URLSession
    private let eventSubject = PassthroughSubject<WebSocketEvent, Never>()

    private var reconnectAttempts: Int = 0
    private let maxReconnectDelay: TimeInterval = 30
    private var reconnectTask: Task<Void, Never>?
    private var pingTask: Task<Void, Never>?
    private var currentAssessmentId: String?
    private var isIntentionalDisconnect = false

    var events: AnyPublisher<WebSocketEvent, Never> {
        eventSubject.eraseToAnyPublisher()
    }

    init() {
        let config = URLSessionConfiguration.default
        config.waitsForConnectivity = true
        self.session = URLSession(configuration: config)
    }

    // MARK: - Connect

    func connect(assessmentId: String) {
        currentAssessmentId = assessmentId
        isIntentionalDisconnect = false
        reconnectAttempts = 0
        performConnect(assessmentId: assessmentId)
    }

    private func performConnect(assessmentId: String) {
        guard connectionState != .connected else { return }
        connectionState = .connecting

        let url = AppConfiguration.API.webSocketURL
            .appendingPathComponent("assessments")
            .appendingPathComponent(assessmentId)
            .appendingPathComponent("stream")

        var request = URLRequest(url: url)
        if let token = SessionManager.shared.accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = session.webSocketTask(with: request)
        webSocketTask?.resume()

        connectionState = .connected
        reconnectAttempts = 0
        eventSubject.send(.connected)

        receiveMessage()
        startPingPong()

        TrueMatchLogger.log(.info, "WebSocket connected to assessment: \(assessmentId)")
    }

    // MARK: - Disconnect

    func disconnect() {
        isIntentionalDisconnect = true
        reconnectTask?.cancel()
        reconnectTask = nil
        pingTask?.cancel()
        pingTask = nil

        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
        connectionState = .disconnected
        eventSubject.send(.disconnected(nil))

        TrueMatchLogger.log(.info, "WebSocket disconnected intentionally")
    }

    // MARK: - Send

    func send(_ message: String) async throws {
        guard let task = webSocketTask, connectionState == .connected else {
            throw WebSocketError.notConnected
        }
        try await task.send(.string(message))
    }

    func sendJSON<T: Encodable>(_ value: T) async throws {
        let data = try JSONEncoder().encode(value)
        guard let jsonString = String(data: data, encoding: .utf8) else {
            throw WebSocketError.encodingFailed
        }
        try await send(jsonString)
    }

    // MARK: - Receive Loop

    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            Task { @MainActor in
                guard let self = self else { return }
                switch result {
                case .success(let message):
                    self.handleReceivedMessage(message)
                    self.receiveMessage()
                case .failure(let error):
                    TrueMatchLogger.log(.error, "WebSocket receive error: \(error.localizedDescription)")
                    self.handleDisconnection(error: error)
                }
            }
        }
    }

    private func handleReceivedMessage(_ message: URLSessionWebSocketTask.Message) {
        switch message {
        case .data(let data):
            parseIncomingData(data)
        case .string(let text):
            if let data = text.data(using: .utf8) {
                parseIncomingData(data)
            }
        @unknown default:
            break
        }
    }

    private func parseIncomingData(_ data: Data) {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        decoder.keyDecodingStrategy = .convertFromSnakeCase

        guard let incoming = try? decoder.decode(WSIncoming.self, from: data) else {
            eventSubject.send(.messageReceived(data))
            return
        }

        switch incoming.type {
        case "progress":
            if let progress = incoming.progress {
                eventSubject.send(.progress(progress))
            }

        case "stage":
            if let stageStr = incoming.stage,
               let stage = AssessmentStage(rawValue: stageStr) {
                eventSubject.send(.stageUpdate(stage))
            }

        case "completed":
            if let assessment = incoming.assessment {
                eventSubject.send(.completed(assessment))
            }

        case "error":
            eventSubject.send(.error(incoming.error ?? "Unknown server error"))

        default:
            eventSubject.send(.messageReceived(data))
        }
    }

    // MARK: - Ping/Pong Keepalive

    private func startPingPong() {
        pingTask?.cancel()
        pingTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(30))
                guard !Task.isCancelled else { break }
                self?.webSocketTask?.sendPing { error in
                    if let error = error {
                        TrueMatchLogger.log(.warning, "Ping failed: \(error.localizedDescription)")
                        Task { @MainActor in
                            self?.handleDisconnection(error: error)
                        }
                    }
                }
            }
        }
    }

    // MARK: - Auto-Reconnect

    private func handleDisconnection(error: Error?) {
        guard !isIntentionalDisconnect else { return }
        guard connectionState != .connecting else { return }

        pingTask?.cancel()
        connectionState = .disconnected
        eventSubject.send(.disconnected(error))

        scheduleReconnect()
    }

    private func scheduleReconnect() {
        guard let assessmentId = currentAssessmentId, !isIntentionalDisconnect else { return }

        reconnectTask?.cancel()
        reconnectTask = Task { [weak self] in
            guard let self = self else { return }
            let delay = self.reconnectDelay()
            TrueMatchLogger.log(.info, "WebSocket reconnecting in \(delay)s (attempt \(self.reconnectAttempts + 1))")

            try? await Task.sleep(for: .seconds(delay))
            guard !Task.isCancelled else { return }

            self.reconnectAttempts += 1
            self.performConnect(assessmentId: assessmentId)
        }
    }

    private func reconnectDelay() -> TimeInterval {
        let base: TimeInterval = 1.0
        let exponential = base * pow(2.0, Double(reconnectAttempts))
        return min(exponential, maxReconnectDelay)
    }

    // MARK: - App Lifecycle

    func handleAppDidEnterBackground() {
        disconnect()
    }

    func handleAppWillEnterForeground() {
        guard let assessmentId = currentAssessmentId else { return }
        isIntentionalDisconnect = false
        connect(assessmentId: assessmentId)
    }
}

// MARK: - WebSocket Errors

enum WebSocketError: LocalizedError {
    case notConnected
    case encodingFailed

    var errorDescription: String? {
        switch self {
        case .notConnected: return "WebSocket is not connected"
        case .encodingFailed: return "Failed to encode message"
        }
    }
}
