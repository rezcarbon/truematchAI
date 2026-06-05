//
//  AgentDashboardViewModel.swift
//  TrueMatch
//

import Foundation
import SwiftUI
import Combine

// MARK: - Live event model

struct LiveEvent: Identifiable {
    let id = UUID()
    let title: String
    let subtitle: String
    let icon: String
    let color: Color
}

// MARK: - ViewModel

@MainActor
final class AgentDashboardViewModel: ObservableObject {
    @Published var wsConnected = false
    @Published var pendingCount = 0
    @Published var reviewCount = 0
    @Published var recentEvents: [LiveEvent] = []
    @Published var showTrigger = false
    @Published var showJDDraft = false
    @Published var errorMessage: String?

    private var wsTask: Task<Void, Never>?
    private var wsSocketTask: URLSessionWebSocketTask?

    func connect() {
        refreshQueue()
        wsTask = Task { await openAgentWebSocket() }
    }

    private func openAgentWebSocket() async {
        guard let url = AppConfiguration.API.wsBase?.appendingPathComponent("agents/ws") else { return }
        var request = URLRequest(url: url)
        if let token = SessionManager.shared.accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        let task = URLSession.shared.webSocketTask(with: request)
        wsSocketTask = task
        task.resume()
        wsConnected = true
        while !Task.isCancelled {
            do {
                let msg = try await task.receive()
                if case .string(let text) = msg { handleWSEvent(text) }
            } catch {
                break
            }
        }
        wsConnected = false
    }

    func disconnect() {
        wsTask?.cancel()
        wsTask = nil
        wsSocketTask?.cancel(with: .normalClosure, reason: nil)
        wsSocketTask = nil
        wsConnected = false
    }

    func refreshQueue() {
        Task {
            do {
                let items = try await APIClient.shared.request(
                    endpoint: .agentQueue(),
                    type: [IngestQueueItem].self
                )
                pendingCount = items.filter { $0.status == "pending" || $0.status == "processing" }.count
                reviewCount = items.filter { $0.status == "awaiting_review" }.count
            } catch {
                TrueMatchLogger.log(.error, "Queue refresh failed: \(error)")
            }
        }
    }

    func triggerAssessment(resumeId: String, jdText: String?) {
        Task {
            do {
                let req = AgentTriggerRequest(resumeId: resumeId, positionId: nil, jdText: jdText)
                let resp = try await APIClient.shared.request(
                    endpoint: .agentTrigger(req),
                    type: AgentTriggerResponse.self
                )
                appendEvent(LiveEvent(
                    title: "Assessment triggered",
                    subtitle: "ID: \(resp.assessmentId.prefix(8))…",
                    icon: "play.circle.fill", color: .green
                ))
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }

    func submitJDDraft(jdText: String, title: String?) {
        Task {
            do {
                let req = JDDraftRequest(jdText: jdText, positionId: nil, title: title)
                _ = try await APIClient.shared.request(
                    endpoint: .submitJDDraft(req),
                    type: [String: String].self
                )
                appendEvent(LiveEvent(
                    title: "JD draft submitted",
                    subtitle: title ?? "Analysing…",
                    icon: "doc.badge.plus", color: .blue
                ))
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }

    // MARK: - WebSocket event handling

    @MainActor
    private func handleWSEvent(_ raw: String) {
        guard let data = raw.data(using: .utf8),
              let event = try? JSONDecoder().decode(AgentEvent.self, from: data) else { return }
        switch event {
        case .itemApproved(let id, _):
            appendEvent(LiveEvent(title: "Item approved", subtitle: "ID: \(id.prefix(8))…",
                                  icon: "checkmark.circle.fill", color: .green))
            refreshQueue()
        case .itemRejected(let id):
            appendEvent(LiveEvent(title: "Item rejected", subtitle: "ID: \(id.prefix(8))…",
                                  icon: "xmark.circle.fill", color: .red))
            refreshQueue()
        case .itemCompleted(let id, _):
            appendEvent(LiveEvent(title: "Assessment complete", subtitle: "ID: \(id.prefix(8))…",
                                  icon: "checkmark.seal.fill", color: .green))
            refreshQueue()
        case .pong, .unknown:
            break
        }
    }

    private func appendEvent(_ event: LiveEvent) {
        recentEvents.insert(event, at: 0)
        if recentEvents.count > 20 { recentEvents.removeLast() }
    }
}
