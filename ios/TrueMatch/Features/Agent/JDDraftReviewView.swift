//
//  JDDraftReviewView.swift
//  TrueMatch
//
//  Side-by-side review of the original JD vs the AI-improved draft.
//  The recruiter can accept the improved version, edit it, or dismiss.
//  This is the iOS surface for Pillar 3 (JD evolution) and the JD agent output.
//

import SwiftUI

struct JDDraftReviewView: View {
    let positionId: String?
    let queueItemId: String?
    @StateObject private var viewModel = JDDraftReviewViewModel()
    @State private var editedDraft = ""
    @State private var showingEditor = false

    var body: some View {
        Group {
            if viewModel.isLoading {
                ProgressView("Loading analysis…")
            } else if let suggestions = viewModel.suggestions {
                ScrollView {
                    VStack(spacing: 20) {
                        // Quality score + issue count
                        HStack(spacing: 16) {
                            ScoreCard(
                                title: "JD quality",
                                value: "\(suggestions.jdAgentOutput?.qualityScore ?? 0)",
                                suffix: "/100",
                                color: qualityColor(suggestions.jdAgentOutput?.qualityScore ?? 0)
                            )
                            ScoreCard(
                                title: "Issues found",
                                value: "\(suggestions.jdAgentOutput?.issues?.count ?? 0)",
                                suffix: "",
                                color: (suggestions.jdAgentOutput?.issues?.count ?? 0) > 0 ? .orange : .green
                            )
                        }
                        .padding(.horizontal)

                        // Issues list
                        if let issues = suggestions.jdAgentOutput?.issues, !issues.isEmpty {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Issues")
                                    .font(.headline)
                                    .padding(.horizontal)
                                ForEach(issues.indices, id: \.self) { i in
                                    let issue = issues[i]
                                    VStack(alignment: .leading, spacing: 4) {
                                        HStack {
                                            Image(systemName: "flag.fill")
                                                .font(.caption)
                                                .foregroundStyle(severityColor(issue.severity))
                                            Text(issue.type.replacingOccurrences(of: "_", with: " ").capitalized)
                                                .font(.subheadline.weight(.semibold))
                                        }
                                        if let detail = issue.detail {
                                            Text(detail).font(.caption).foregroundStyle(.secondary)
                                        }
                                        if let rec = issue.recommendation {
                                            Label(rec, systemImage: "wand.and.stars")
                                                .font(.caption)
                                                .foregroundStyle(.blue)
                                        }
                                    }
                                    .padding(12)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .background(Color(.systemBackground))
                                    .clipShape(RoundedRectangle(cornerRadius: 10))
                                    .shadow(color: .black.opacity(0.05), radius: 4)
                                    .padding(.horizontal)
                                }
                            }
                        }

                        // AI improved draft
                        if let improved = suggestions.jdImprovedDraft {
                            VStack(alignment: .leading, spacing: 8) {
                                HStack {
                                    Label("AI-improved draft", systemImage: "wand.and.stars")
                                        .font(.headline)
                                    Spacer()
                                    Button("Edit") {
                                        editedDraft = improved
                                        showingEditor = true
                                    }
                                    .font(.subheadline)
                                }
                                .padding(.horizontal)

                                Text(improved)
                                    .font(.callout)
                                    .padding(12)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .background(Color(.systemBackground))
                                    .clipShape(RoundedRectangle(cornerRadius: 10))
                                    .shadow(color: .black.opacity(0.05), radius: 4)
                                    .padding(.horizontal)
                            }

                            // Accept / dismiss actions
                            HStack(spacing: 12) {
                                Button {
                                    viewModel.acceptDraft(improved)
                                } label: {
                                    Label("Accept draft", systemImage: "checkmark.circle.fill")
                                        .frame(maxWidth: .infinity)
                                }
                                .buttonStyle(.borderedProminent)
                                .tint(.green)
                            }
                            .padding(.horizontal)
                            .padding(.bottom)
                        }
                    }
                    .padding(.top)
                }
            } else {
                ContentUnavailableView(
                    "No analysis yet",
                    systemImage: "doc.text.magnifyingglass",
                    description: Text("Drop a JD draft in the inbox or submit one from the dashboard.")
                )
            }
        }
        .navigationTitle("JD Review")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            if let pid = positionId { viewModel.load(positionId: pid) }
        }
        .sheet(isPresented: $showingEditor) {
            JDDraftEditorSheet(text: $editedDraft, onSave: { draft in
                viewModel.acceptDraft(draft)
                showingEditor = false
            })
        }
    }

    private func qualityColor(_ score: Int) -> Color {
        score >= 80 ? .green : score >= 60 ? .orange : .red
    }

    private func severityColor(_ severity: String?) -> Color {
        switch severity {
        case "high": return .red
        case "medium": return .orange
        default: return .secondary
        }
    }
}

// MARK: - Supporting views

struct ScoreCard: View {
    let title: String
    let value: String
    let suffix: String
    let color: Color

    var body: some View {
        VStack(spacing: 4) {
            HStack(alignment: .lastTextBaseline, spacing: 2) {
                Text(value)
                    .font(.title2.bold())
                    .foregroundStyle(color)
                Text(suffix)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(12)
        .background(Color(.secondarySystemGroupedBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

struct JDDraftEditorSheet: View {
    @Binding var text: String
    let onSave: (String) -> Void
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            TextEditor(text: $text)
                .padding()
                .navigationTitle("Edit draft")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                    ToolbarItem(placement: .confirmationAction) {
                        Button("Save") { onSave(text); dismiss() }
                    }
                }
        }
    }
}
