//
//  GovernanceComplianceViews.swift
//  TrueMatch
//
//  Admin governance review queue (approve/reject/escalate) and compliance
//  system status, wired to the real endpoints.
//

import SwiftUI

// MARK: - Governance reviews

@MainActor
final class GovernanceReviewsViewModel: ObservableObject {
    @Published var response: GovernanceReviewListResponse?
    @Published var isLoading = false
    @Published var errorMessage: String?

    func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            response = try await APIClient.shared.request(endpoint: .governanceReviews(), type: GovernanceReviewListResponse.self)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func decide(_ item: GovernanceReviewItemDTO, decision: String) async {
        do {
            _ = try await APIClient.shared.requestVoid(
                endpoint: .approveGovernanceReview(id: item.id, ApproveReviewRequest(decision: decision, notes: nil))
            )
            await load()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct GovernanceReviewsView: View {
    @StateObject private var viewModel = GovernanceReviewsViewModel()

    var body: some View {
        NavigationStack {
            List {
                if let r = viewModel.response {
                    Section("Queue") {
                        MetricRow(label: "Pending", value: "\(r.pending)")
                        MetricRow(label: "Approved", value: "\(r.approved)")
                        MetricRow(label: "Rejected", value: "\(r.rejected)")
                        MetricRow(label: "Escalated", value: "\(r.escalated)")
                    }
                    if r.items.isEmpty {
                        Section {
                            Text("No reviews in the queue.").font(.subheadline).foregroundStyle(.secondary)
                        }
                    } else {
                        ForEach(r.items) { item in
                            Section(item.reviewType?.capitalized ?? "Review") {
                                if let reason = item.failureReason {
                                    Text(reason).font(.caption).foregroundStyle(.secondary)
                                }
                                HStack {
                                    Button("Approve") { Task { await viewModel.decide(item, decision: "approved") } }
                                        .buttonStyle(.borderedProminent).tint(.green)
                                    Button("Reject") { Task { await viewModel.decide(item, decision: "rejected") } }
                                        .buttonStyle(.bordered).tint(.red)
                                    Button("Escalate") { Task { await viewModel.decide(item, decision: "escalated") } }
                                        .buttonStyle(.bordered)
                                }
                                .font(.caption)
                            }
                        }
                    }
                } else if viewModel.isLoading {
                    ProgressView()
                }
            }
            .navigationTitle("Governance")
            .refreshable { await viewModel.load() }
            .task { await viewModel.load() }
        }
    }
}

// MARK: - Compliance status

@MainActor
final class ComplianceViewModel: ObservableObject {
    @Published var status: ComplianceStatusResponse?
    @Published var isLoading = false
    @Published var errorMessage: String?

    func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            status = try await APIClient.shared.request(endpoint: .complianceStatus, type: ComplianceStatusResponse.self)
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct ComplianceView: View {
    @StateObject private var viewModel = ComplianceViewModel()

    var body: some View {
        NavigationStack {
            List {
                if let s = viewModel.status {
                    Section("Status") {
                        MetricRow(label: "System", value: s.status.capitalized)
                    }
                    Section("Provenance") {
                        MetricRow(label: "Records created", value: "\(s.phaseCProvenance.recordsCreated)")
                    }
                    Section("Learning") {
                        MetricRow(label: "Weight updates", value: "\(s.phaseDLearning.weightUpdates)")
                        MetricRow(label: "Capabilities learned", value: "\(s.phaseDLearning.capabilitiesLearned)")
                        MetricRow(label: "Credential equivalencies", value: "\(s.phaseDLearning.credentialEquivalencies)")
                        MetricRow(label: "Updates applied", value: "\(s.phaseDLearning.totalUpdatesApplied)")
                    }
                } else if viewModel.isLoading {
                    ProgressView()
                }
            }
            .navigationTitle("Compliance")
            .refreshable { await viewModel.load() }
            .task { await viewModel.load() }
        }
    }
}
