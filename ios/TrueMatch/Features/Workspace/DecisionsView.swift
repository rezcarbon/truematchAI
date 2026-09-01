//
//  DecisionsView.swift
//  TrueMatch
//
//  Recruiter decision audit log — every recorded hiring decision with its
//  outcome and whether the AI recommendation was followed. Mirrors the web
//  /recruiter/decisions page (GET /decisions).
//

import SwiftUI

struct DecisionRecordDTO: Codable, Identifiable {
    let id: String
    let assessmentId: String
    let positionId: String
    let recruiterId: String
    let decision: String
    let aiRecommendationFollowed: Bool?
    let overrideReasoning: String?
    let createdAt: String?
}

@MainActor
final class DecisionsViewModel: ObservableObject {
    @Published var decisions: [DecisionRecordDTO] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            decisions = try await APIClient.shared.request(endpoint: .listDecisions, type: [DecisionRecordDTO].self)
        } catch {
            TrueMatchLogger.log(.error, "Decisions load failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }
}

struct DecisionsView: View {
    @StateObject private var viewModel = DecisionsViewModel()

    var body: some View {
        List {
            if viewModel.decisions.isEmpty && !viewModel.isLoading {
                ContentUnavailableViewCompat(
                    title: "No decisions yet",
                    systemImage: "checkmark.seal",
                    message: "Hiring decisions you record appear here with a full audit trail."
                )
            }
            ForEach(viewModel.decisions) { d in
                VStack(alignment: .leading, spacing: 5) {
                    HStack {
                        TMBadge(text: d.decision.capitalized, kind: badgeKind(d.decision))
                        Spacer()
                        if d.aiRecommendationFollowed == true {
                            Label("AI followed", systemImage: "sparkles")
                                .font(.caption2).foregroundStyle(.green)
                        } else if d.aiRecommendationFollowed == false {
                            Label("Override", systemImage: "person.fill.questionmark")
                                .font(.caption2).foregroundStyle(.orange)
                        }
                    }
                    Text("Assessment \(String(d.assessmentId.prefix(8)))…")
                        .font(.caption).foregroundStyle(.secondary)
                    if let r = d.overrideReasoning, !r.isEmpty {
                        Text(r).font(.caption).foregroundStyle(.secondary).lineLimit(2)
                    }
                }
                .padding(.vertical, 2)
            }
        }
        .navigationTitle("Decisions")
        .refreshable { await viewModel.load() }
        .task { await viewModel.load() }
    }

    private func badgeKind(_ d: String) -> TMBadgeKind {
        switch d {
        case "hire", "advance": return .success
        case "reject": return .error
        case "hold": return .warning
        default: return .info
        }
    }
}
