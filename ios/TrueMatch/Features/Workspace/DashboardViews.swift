//
//  DashboardViews.swift
//  TrueMatch
//
//  Recruiter and admin dashboards wired to the real metrics endpoints.
//

import SwiftUI

// MARK: - Recruiter dashboard

@MainActor
final class RecruiterDashboardViewModel: ObservableObject {
    @Published var entries: [RecruiterMetricEntry] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let resp = try await APIClient.shared.request(endpoint: .recruiterMetrics, type: RecruiterMetricsResponse.self)
            entries = resp.recruiters
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct RecruiterDashboardView: View {
    @StateObject private var viewModel = RecruiterDashboardViewModel()

    var body: some View {
        NavigationStack {
            List {
                if viewModel.entries.isEmpty && !viewModel.isLoading {
                    ContentUnavailableViewCompat(title: "No metrics yet",
                        systemImage: "chart.bar",
                        message: "Recruiter performance appears here as candidates move through the pipeline.")
                }
                ForEach(viewModel.entries) { e in
                    Section(e.recruiterName ?? "Recruiter") {
                        MetricRow(label: "Candidates reviewed", value: "\(e.metrics.candidatesReviewed)")
                        MetricRow(label: "Interviews scheduled", value: "\(e.metrics.interviewsScheduled)")
                        MetricRow(label: "Offers made", value: "\(e.metrics.offersMade)")
                        MetricRow(label: "Hire rate", value: String(format: "%.0f%%", e.metrics.hireRate * 100))
                        MetricRow(label: "Avg time to hire", value: "\(e.metrics.avgTimeToHire) days")
                    }
                }
            }
            .navigationTitle("Dashboard")
            .refreshable { await viewModel.load() }
            .task { await viewModel.load() }
        }
    }
}

// MARK: - Admin dashboard

@MainActor
final class AdminDashboardViewModel: ObservableObject {
    @Published var metrics: AdminMetricsResponse?
    @Published var isLoading = false
    @Published var errorMessage: String?

    func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            metrics = try await APIClient.shared.request(endpoint: .adminMetrics, type: AdminMetricsResponse.self)
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct AdminDashboardView: View {
    @StateObject private var viewModel = AdminDashboardViewModel()

    var body: some View {
        NavigationStack {
            List {
                if let h = viewModel.metrics?.data.systemHealth {
                    Section("System health") {
                        MetricRow(label: "Status", value: h.status.capitalized)
                        MetricRow(label: "Sessions (24h)", value: "\(h.last24Hours.totalSessions)")
                        MetricRow(label: "Sessions (7d)", value: "\(h.last7Days.totalSessions)")
                    }
                    Section("Governance") {
                        MetricRow(label: "Pending", value: "\(h.governance.pending)")
                        MetricRow(label: "Approved", value: "\(h.governance.approved)")
                        MetricRow(label: "Rejected", value: "\(h.governance.rejected)")
                        MetricRow(label: "Escalated", value: "\(h.governance.escalated)")
                    }
                } else if viewModel.isLoading {
                    ProgressView()
                }
            }
            .navigationTitle("Admin")
            .refreshable { await viewModel.load() }
            .task { await viewModel.load() }
        }
    }
}

struct MetricRow: View {
    let label: String
    let value: String
    var body: some View {
        HStack {
            Text(label).foregroundStyle(.secondary)
            Spacer()
            Text(value).font(.body.weight(.semibold))
        }
    }
}
