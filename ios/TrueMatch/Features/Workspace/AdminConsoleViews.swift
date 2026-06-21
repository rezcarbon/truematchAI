//
//  AdminConsoleViews.swift
//  TrueMatch
//
//  Admin console surfaces wired to the (newly resurrected) admin endpoints:
//  Users (/admin/users), Audit trail (/admin/audit), and Analytics
//  (/admin/analytics + /admin/compliance/report).
//

import SwiftUI

// MARK: - DTOs

struct AdminUserDTO: Codable, Identifiable {
    let id: String
    let email: String
    let role: String
    let displayName: String?
    let createdAt: String?
}

struct AdminUserListDTO: Codable {
    let items: [AdminUserDTO]
    let total: Int
}

struct AuditEventDTO: Codable, Identifiable {
    let id: String
    let assessmentId: String?
    let eventType: String
    let actorType: String?
    let createdAt: String?
}

struct AuditListDTO: Codable {
    let items: [AuditEventDTO]
    let total: Int
}

struct AdminAnalyticsDTO: Codable {
    let assessmentsTotal: Int
    let assessmentsByStatus: [String: Int]
    let avgScoreDelta: Double?
    let counterRecRate: Double?
    let decisionOverrideRate: Double?
}

struct ComplianceReportDTO: Codable {
    let totalAssessments: Int
    let governedAssessments: Int
    let counterRecommendations: Int
    let overrideCount: Int
    let biasFlagsRaised: Int
    let notes: String?
}

// MARK: - Users

@MainActor
final class AdminUsersViewModel: ObservableObject {
    @Published var users: [AdminUserDTO] = []
    @Published var total = 0
    @Published var errorMessage: String?

    func load() async {
        do {
            let resp = try await APIClient.shared.request(endpoint: .adminUsers, type: AdminUserListDTO.self)
            users = resp.items
            total = resp.total
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct AdminUsersView: View {
    @StateObject private var viewModel = AdminUsersViewModel()

    var body: some View {
        List {
            Section("Users (\(viewModel.total))") {
                ForEach(viewModel.users) { u in
                    VStack(alignment: .leading, spacing: 3) {
                        HStack {
                            Text(u.displayName ?? u.email).font(.subheadline.weight(.semibold))
                            Spacer()
                            TMBadge(text: u.role.capitalized,
                                    kind: u.role == "admin" ? .error : u.role == "recruiter" ? .info : .neutral)
                        }
                        Text(u.email).font(.caption).foregroundStyle(.secondary)
                    }
                }
            }
        }
        .navigationTitle("Users")
        .refreshable { await viewModel.load() }
        .task { await viewModel.load() }
    }
}

// MARK: - Audit trail

@MainActor
final class AdminAuditViewModel: ObservableObject {
    @Published var events: [AuditEventDTO] = []
    @Published var total = 0
    @Published var errorMessage: String?

    func load() async {
        do {
            let resp = try await APIClient.shared.request(endpoint: .adminAudit, type: AuditListDTO.self)
            events = resp.items
            total = resp.total
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct AdminAuditView: View {
    @StateObject private var viewModel = AdminAuditViewModel()

    var body: some View {
        List {
            Section("Audit events (\(viewModel.total))") {
                ForEach(viewModel.events) { e in
                    VStack(alignment: .leading, spacing: 3) {
                        Text(e.eventType).font(.subheadline.weight(.semibold))
                        HStack(spacing: 8) {
                            if let actor = e.actorType {
                                Label(actor, systemImage: actor == "system" ? "cpu" : "person")
                                    .font(.caption2).foregroundStyle(.secondary)
                            }
                            if let aid = e.assessmentId {
                                Text("assessment \(String(aid.prefix(8)))…")
                                    .font(.caption2).foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle("Audit Trail")
        .refreshable { await viewModel.load() }
        .task { await viewModel.load() }
    }
}

// MARK: - Analytics (assessment outcomes + compliance report)

@MainActor
final class AdminAnalyticsViewModel: ObservableObject {
    @Published var analytics: AdminAnalyticsDTO?
    @Published var compliance: ComplianceReportDTO?
    @Published var errorMessage: String?

    func load() async {
        do {
            analytics = try await APIClient.shared.request(endpoint: .adminAnalytics, type: AdminAnalyticsDTO.self)
            compliance = try await APIClient.shared.request(endpoint: .adminComplianceReport, type: ComplianceReportDTO.self)
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct AdminAnalyticsView: View {
    @StateObject private var viewModel = AdminAnalyticsViewModel()

    var body: some View {
        List {
            if let a = viewModel.analytics {
                Section("Assessments") {
                    MetricRow(label: "Total", value: "\(a.assessmentsTotal)")
                    ForEach(a.assessmentsByStatus.sorted(by: { $0.key < $1.key }), id: \.key) { k, v in
                        MetricRow(label: k.replacingOccurrences(of: "_", with: " ").capitalized, value: "\(v)")
                    }
                    if let d = a.avgScoreDelta {
                        MetricRow(label: "Avg score delta", value: String(format: "%.1f", d))
                    }
                    if let r = a.counterRecRate {
                        MetricRow(label: "Counter-rec rate", value: String(format: "%.0f%%", r * 100))
                    }
                    if let o = a.decisionOverrideRate {
                        MetricRow(label: "AI override rate", value: String(format: "%.0f%%", o * 100))
                    }
                }
            }
            if let c = viewModel.compliance {
                Section("Compliance") {
                    MetricRow(label: "Governed assessments", value: "\(c.governedAssessments)/\(c.totalAssessments)")
                    MetricRow(label: "Counter-recommendations", value: "\(c.counterRecommendations)")
                    MetricRow(label: "Overrides", value: "\(c.overrideCount)")
                    MetricRow(label: "Bias flags raised", value: "\(c.biasFlagsRaised)")
                }
                if let n = c.notes {
                    Section { Text(n).font(.caption).foregroundStyle(.secondary) }
                }
            }
        }
        .navigationTitle("Analytics")
        .refreshable { await viewModel.load() }
        .task { await viewModel.load() }
    }
}
