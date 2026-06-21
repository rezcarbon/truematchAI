//
//  ChatViewModel.swift
//  TrueMatch
//
//  Drives the conversational AI assistant. The backend routes each message to
//  the right role agent (candidate / recruiter / admin) based on the JWT, so the
//  client stays role-agnostic — it just manages sessions, sends messages, and
//  renders the streamed reply plus any agent actions/suggestions.
//

import Foundation
import SwiftUI

@MainActor
final class ChatViewModel: ObservableObject {
    @Published var sessions: [ChatSessionSummary] = []
    @Published var messages: [ChatBubble] = []
    @Published var suggestions: [String] = []
    @Published var inputText: String = ""
    @Published var currentSessionId: String?
    @Published var isSending = false
    @Published var isLoadingSession = false
    @Published var errorMessage: String?

    private let api = APIClient.shared

    var canSend: Bool {
        !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && currentSessionId != nil
            && !isSending
    }

    // MARK: - Session lifecycle

    func loadSessions() async {
        do {
            sessions = try await api.request(endpoint: .listChatSessions, type: [ChatSessionSummary].self)
        } catch {
            TrueMatchLogger.log(.error, "Chat: load sessions failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }

    /// Ensure there is an active session to talk to, creating one if needed.
    func startIfNeeded() async {
        await loadSessions()
        if let first = sessions.first {
            await selectSession(id: first.id)
        } else {
            await newSession()
        }
    }

    func newSession() async {
        do {
            let title = "Chat \(Self.shortDate())"
            let created = try await api.request(
                endpoint: .createChatSession(CreateChatSessionRequest(title: title)),
                type: ChatSessionResponse.self
            )
            currentSessionId = created.id
            messages = []
            suggestions = []
            await loadSessions()
        } catch {
            TrueMatchLogger.log(.error, "Chat: new session failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }

    func selectSession(id: String) async {
        isLoadingSession = true
        defer { isLoadingSession = false }
        currentSessionId = id
        suggestions = []
        do {
            let detail = try await api.request(endpoint: .chatSession(id: id), type: ChatSessionDetailResponse.self)
            messages = detail.messages.map { dto in
                ChatBubble(
                    id: dto.id,
                    role: dto.role == "assistant" ? .assistant : .user,
                    content: dto.content,
                    actions: dto.actionsTaken ?? []
                )
            }
        } catch {
            TrueMatchLogger.log(.error, "Chat: load session failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }

    func deleteSession(id: String) async {
        do {
            try await api.requestVoid(endpoint: .deleteChatSession(id: id))
            if currentSessionId == id {
                currentSessionId = nil
                messages = []
                suggestions = []
            }
            await loadSessions()
            if currentSessionId == nil { await startIfNeeded() }
        } catch {
            TrueMatchLogger.log(.error, "Chat: delete session failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Messaging

    func send() async {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, let sessionId = currentSessionId else { return }

        inputText = ""
        suggestions = []
        messages.append(ChatBubble(role: .user, content: text))
        isSending = true
        defer { isSending = false }

        do {
            let resp = try await api.request(
                endpoint: .sendChatMessage(ChatSendRequest(sessionId: sessionId, message: text)),
                type: ChatSendResponse.self
            )
            messages.append(ChatBubble(role: .assistant, content: resp.response, actions: resp.actions))
            suggestions = resp.suggestions
            await loadSessions() // refresh ordering / counts
        } catch {
            TrueMatchLogger.log(.error, "Chat: send failed: \(error)")
            messages.append(ChatBubble(
                role: .assistant,
                content: "Sorry — I couldn't reach the assistant. \(error.localizedDescription)"
            ))
        }
    }

    func useSuggestion(_ s: String) {
        inputText = s
    }

    private static func shortDate() -> String {
        let f = DateFormatter()
        f.dateFormat = "MMM d, HH:mm"
        return f.string(from: Date())
    }
}
