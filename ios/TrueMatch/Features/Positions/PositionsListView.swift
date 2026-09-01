//
//  PositionsListView.swift
//  TrueMatch
//
//  Recruiter Positions list → tap a position to see its candidate pipeline,
//  grouped by stage. Replaces the placeholder JobMatching tab.
//

import SwiftUI

struct PositionsListView: View {
    @StateObject private var viewModel = PositionsViewModel()

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.isLoading && viewModel.positions.isEmpty {
                    ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if viewModel.positions.isEmpty {
                    emptyState
                } else {
                    List(viewModel.positions) { position in
                        NavigationLink(destination: PositionPipelineView(position: position)) {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(position.title).font(.subheadline.weight(.semibold))
                                HStack(spacing: 8) {
                                    if let status = position.status {
                                        TMBadge(text: status.capitalized, kind: .neutral)
                                    }
                                    if let q = position.jdQualityScore {
                                        Text("JD quality \(q)")
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                            }
                            .padding(.vertical, 2)
                        }
                    }
                }
            }
            .navigationTitle("Positions")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button { Task { await viewModel.load() } } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
            .refreshable { await viewModel.load() }
            .task { await viewModel.load() }
            .alert("Couldn't load positions",
                   isPresented: Binding(get: { viewModel.errorMessage != nil },
                                        set: { if !$0 { viewModel.errorMessage = nil } })) {
                Button("OK", role: .cancel) { viewModel.errorMessage = nil }
            } message: { Text(viewModel.errorMessage ?? "") }
        }
    }

    private var emptyState: some View {
        VStack(spacing: 10) {
            Image(systemName: "briefcase")
                .font(.system(size: 40))
                .foregroundStyle(TrueMatchTheme.accentColor)
            Text("No open positions").font(.headline)
            Text("Positions you create will appear here with their candidate pipeline.")
                .font(.subheadline).foregroundStyle(.secondary).multilineTextAlignment(.center)
        }
        .padding(40)
    }
}

struct PositionPipelineView: View {
    let position: PositionDTO
    @StateObject private var viewModel = PipelineViewModel()

    var body: some View {
        List {
            // JD quality (mirrors the web /recruiter/jd-quality view).
            if let d = viewModel.detail, let score = d.jdQualityScore {
                Section("JD quality") {
                    HStack {
                        Text("Quality score").foregroundStyle(.secondary)
                        Spacer()
                        Text("\(score)")
                            .font(.body.weight(.bold))
                            .foregroundStyle(score >= 70 ? .green : score >= 50 ? .orange : .red)
                    }
                    if let issues = d.jdIssues?.issues, !issues.isEmpty {
                        ForEach(issues) { issue in
                            VStack(alignment: .leading, spacing: 3) {
                                HStack {
                                    Text(issue.type.replacingOccurrences(of: "_", with: " ").capitalized)
                                        .font(.subheadline.weight(.semibold))
                                    Spacer()
                                    if let sev = issue.severity {
                                        TMBadge(text: sev.capitalized,
                                                kind: sev == "high" ? .error : sev == "medium" ? .warning : .neutral)
                                    }
                                }
                                if let rec = issue.recommendation {
                                    Text("Fix: \(rec)").font(.caption).foregroundStyle(.secondary)
                                }
                            }
                        }
                    }
                }
            }
            if viewModel.candidates.isEmpty && !viewModel.isLoading {
                Text("No candidates in this pipeline yet.")
                    .font(.subheadline).foregroundStyle(.secondary)
            }
            ForEach(viewModel.byStage, id: \.stage) { group in
                Section(stageLabel(group.stage) + " (\(group.items.count))") {
                    ForEach(group.items) { c in
                        HStack(spacing: 10) {
                            Image(systemName: "person.crop.circle")
                                .foregroundStyle(TrueMatchTheme.accentColor)
                            VStack(alignment: .leading, spacing: 2) {
                                Text("Candidate \(String(c.userId?.prefix(8) ?? "—"))")
                                    .font(.subheadline)
                                if let src = c.source {
                                    Text("Source: \(src)").font(.caption).foregroundStyle(.secondary)
                                }
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle(position.title)
        .navigationBarTitleDisplayMode(.inline)
        .refreshable { await viewModel.load(positionId: position.id) }
        .task { await viewModel.load(positionId: position.id) }
    }

    private func stageLabel(_ stage: String) -> String {
        stage.replacingOccurrences(of: "_", with: " ").capitalized
    }
}
