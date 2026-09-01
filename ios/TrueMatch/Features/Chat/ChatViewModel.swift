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
        // An empty assistant bubble we stream tokens into.
        let assistantId = UUID().uuidString
        messages.append(ChatBubble(id: assistantId, role: .assistant, content: ""))
        isSending = true
        defer { isSending = false }

        do {
            let bytes = try await api.eventStream(
                endpoint: .streamChatMessage(sessionId: sessionId, StreamChatRequest(message: text))
            )

            let decoder = JSONDecoder()
            decoder.keyDecodingStrategy = .convertFromSnakeCase

            // SSE: lines accumulate into a frame until a blank line; each frame
            // carries an `event:` type and one or more `data:` lines.
            var eventType = "message"
            var dataBuffer = ""

            func dispatch() {
                defer { eventType = "message"; dataBuffer = "" }
                guard !dataBuffer.isEmpty, let data = dataBuffer.data(using: .utf8) else { return }
                switch eventType {
                case "token":
                    if let p = try? decoder.decode(StreamTokenPayload.self, from: data) {
                        appendToAssistant(p.text, id: assistantId)
                    }
                case "done":
                    if let p = try? decoder.decode(StreamDonePayload.self, from: data) {
                        finalizeAssistant(id: assistantId, actions: p.actions ?? [])
                        suggestions = p.suggestions ?? []
                    }
                case "error":
                    if let p = try? decoder.decode(StreamErrorPayload.self, from: data) {
                        appendToAssistant("\n\n⚠️ \(p.error)", id: assistantId)
                    }
                default:
                    break  // `connected` and any unknown events are ignored
                }
            }

            for try await line in bytes.lines {
                if line.isEmpty {
                    dispatch()
                } else if line.hasPrefix("event:") {
                    eventType = String(line.dropFirst(6)).trimmingCharacters(in: .whitespaces)
                } else if line.hasPrefix("data:") {
                    var chunk = String(line.dropFirst(5))
                    if chunk.first == " " { chunk.removeFirst() }  // strip one optional space
                    dataBuffer += dataBuffer.isEmpty ? chunk : "\n" + chunk
                }
            }
            dispatch()  // flush a trailing frame if the server closed without a blank line

            // Drop the placeholder if the stream produced nothing.
            if let idx = messages.firstIndex(where: { $0.id == assistantId }),
               messages[idx].content.isEmpty {
                messages.remove(at: idx)
            }
            await loadSessions()  // refresh ordering / counts
        } catch {
            // Streaming unavailable (older backend, proxy, or transport error):
            // fall back to the one-shot endpoint so chat still works.
            TrueMatchLogger.log(.error, "Chat: stream failed, falling back to one-shot: \(error)")
            await fallbackSend(text: text, sessionId: sessionId, assistantId: assistantId)
        }
    }

    /// One-shot send used when streaming isn't available; reuses the placeholder
    /// assistant bubble created by `send()`.
    private func fallbackSend(text: String, sessionId: String, assistantId: String) async {
        do {
            let resp = try await api.request(
                endpoint: .sendChatMessage(ChatSendRequest(sessionId: sessionId, message: text)),
                type: ChatSendResponse.self
            )
            replaceAssistant(id: assistantId, content: resp.response, actions: resp.actions)
            suggestions = resp.suggestions
            await loadSessions()
        } catch {
            TrueMatchLogger.log(.error, "Chat: send failed: \(error)")
            replaceAssistant(
                id: assistantId,
                content: "Sorry — I couldn't reach the assistant. \(error.localizedDescription)",
                actions: []
            )
        }
    }

    // MARK: - Streaming bubble mutation
    // ChatBubble is immutable, so we replace the element at its id to update it.

    private func appendToAssistant(_ text: String, id: String) {
        guard let idx = messages.firstIndex(where: { $0.id == id }) else { return }
        let current = messages[idx]
        messages[idx] = ChatBubble(id: id, role: .assistant,
                                   content: current.content + text, actions: current.actions)
    }

    private func finalizeAssistant(id: String, actions: [ChatActionDTO]) {
        guard let idx = messages.firstIndex(where: { $0.id == id }) else { return }
        let current = messages[idx]
        messages[idx] = ChatBubble(id: id, role: .assistant, content: current.content, actions: actions)
    }

    private func replaceAssistant(id: String, content: String, actions: [ChatActionDTO]) {
        if let idx = messages.firstIndex(where: { $0.id == id }) {
            messages[idx] = ChatBubble(id: id, role: .assistant, content: content, actions: actions)
        } else {
            messages.append(ChatBubble(role: .assistant, content: content, actions: actions))
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
