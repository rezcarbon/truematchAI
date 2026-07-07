//
//  CareerCoachViewModel.swift
//  TrueMatch
//
//  Manages career coaching chat interface with WebSocket connection,
//  structured response handling, and message history.
//

import Foundation
import SwiftUI
import Combine

@MainActor
final class CareerCoachViewModel: ObservableObject {
    @Published var messages: [CareerCoachMessage] = []
    @Published var inputText: String = ""
    @Published var suggestedFollowUps: [String] = []
    @Published var isLoading = false
    @Published var isSending = false
    @Published var errorMessage: String?
    @Published var connectionStatus: ConnectionStatus = .disconnected

    enum ConnectionStatus {
        case connecting
        case connected
        case disconnected
        case failed
    }

    private let api = APIClient.shared
    private let candidateId: String
    private var webSocket: URLSessionWebSocketTask?
    private var receiveTask: Task<Void, Never>?

    var canSend: Bool {
        !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !isSending
            && connectionStatus == .connected
    }

    init(candidateId: String) {
        self.candidateId = candidateId
    }

    // MARK: - Connection

    func connectWebSocket() async {
        guard connectionStatus != .connected else { return }

        connectionStatus = .connecting

        let sessionId = "coach_\(candidateId)_\(UUID().uuidString)"
        guard let url = URL(string: "\(AppConfiguration.API.wsBaseURL)/candidate/coach/\(sessionId)") else {
            connectionStatus = .failed
            errorMessage = "Invalid WebSocket URL"
            return
        }

        let request = URLRequest(url: url)
        let webSocket = URLSession.shared.webSocketTask(with: request)
        self.webSocket = webSocket
        webSocket.resume()

        connectionStatus = .connected
        receiveMessages()
    }

    func disconnect() {
        webSocket?.cancel(with: .goingAway, reason: nil)
        webSocket = nil
        receiveTask?.cancel()
        connectionStatus = .disconnected
    }

    // MARK: - Messaging

    func send() async {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, canSend else { return }

        inputText = ""
        suggestedFollowUps = []

        // Add user message to history
        let userMessage = CareerCoachMessage(
            id: UUID().uuidString,
            role: "user",
            content: text,
            structuredContent: nil,
            timestamp: ISO8601DateFormatter().string(from: Date())
        )
        messages.append(userMessage)

        isSending = true
        defer { isSending = false }

        do {
            // Create assistant message placeholder
            let assistantId = UUID().uuidString
            let assistantMessage = CareerCoachMessage(
                id: assistantId,
                role: "assistant",
                content: "",
                structuredContent: nil,
                timestamp: ISO8601DateFormatter().string(from: Date())
            )
            messages.append(assistantMessage)

            // Send message via WebSocket
            let sendData = try JSONEncoder().encode([
                "type": "message",
                "content": text
            ] as [String: Any])

            if let jsonString = String(data: sendData, encoding: .utf8) {
                try await webSocket?.send(.string(jsonString))
            }
        } catch {
            TrueMatchLogger.log(.error, "CareerCoach: send failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }

    private func receiveMessages() {
        receiveTask = Task {
            while !Task.isCancelled {
                do {
                    let message = try await webSocket?.receive()

                    switch message {
                    case .string(let text):
                        await handleReceivedMessage(text)
                    case .data(let data):
                        await handleReceivedData(data)
                    default:
                        break
                    }
                } catch {
                    TrueMatchLogger.log(.error, "CareerCoach: receive failed: \(error)")
                    connectionStatus = .failed
                    break
                }
            }
        }
    }

    @MainActor
    private func handleReceivedMessage(_ text: String) async {
        guard let data = text.data(using: .utf8) else { return }

        do {
            let decoder = JSONDecoder()
            decoder.keyDecodingStrategy = .convertFromSnakeCase

            if let message = try? decoder.decode(CareerCoachMessage.self, from: data) {
                if let index = messages.lastIndex(where: { $0.role == "assistant" && $0.content.isEmpty }) {
                    messages[index] = message
                    suggestedFollowUps = message.structuredContent?.nextSteps ?? []
                } else {
                    messages.append(message)
                }
            }
        } catch {
            TrueMatchLogger.log(.error, "CareerCoach: decode failed: \(error)")
        }
    }

    @MainActor
    private func handleReceivedData(_ data: Data) async {
        await handleReceivedMessage(String(data: data, encoding: .utf8) ?? "")
    }

    func useSuggestion(_ suggestion: String) {
        inputText = suggestion
    }

    // MARK: - Message History

    func clearHistory() {
        messages = []
        suggestedFollowUps = []
    }
}

// MARK: - JSON Helpers

extension CareerCoachMessage {
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        role = try container.decode(String.self, forKey: .role)
        content = try container.decode(String.self, forKey: .content)
        structuredContent = try container.decodeIfPresent(StructuredResponse.self, forKey: .structuredContent)
        timestamp = try container.decode(String.self, forKey: .timestamp)
    }

    enum CodingKeys: String, CodingKey {
        case id
        case role
        case content
        case structuredContent
        case timestamp
    }
}
