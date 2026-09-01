//
//  AgentDashboardView.swift
//  TrueMatch
//
//  The TrueMatch agent command centre — monitor what the autonomous agents are
//  doing and send instructions on the go. This is the iOS front door to the
//  agentic ATS: CVs being picked up, JD drafts being reviewed, and one-tap
//  triggers to run assessments anywhere.
//

import SwiftUI

struct AgentDashboardView: View {
    @StateObject private var viewModel = AgentDashboardViewModel()

    var body: some View {
        NavigationStack {
            List {
                // ── Live status banner ─────────────────────────────────────
                Section {
                    HStack(spacing: 12) {
                        ZStack {
                            Circle()
                                .fill(viewModel.wsConnected ? Color.green.opacity(0.15) : Color.gray.opacity(0.15))
                                .frame(width: 40, height: 40)
                            Image(systemName: viewModel.wsConnected ? "antenna.radiowaves.left.and.right" : "antenna.radiowaves.left.and.right.slash")
                                .foregroundStyle(viewModel.wsConnected ? .green : .secondary)
                        }
                        VStack(alignment: .leading, spacing: 2) {
                            Text(viewModel.wsConnected ? "Agents active" : "Agents offline")
                                .font(.subheadline.weight(.semibold))
                            Text(viewModel.wsConnected ? "Monitoring CV & JD inboxes" : "Connect to see live events")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                        if viewModel.wsConnected {
                            Image(systemName: "circle.fill")
                                .font(.caption2)
                                .foregroundStyle(.green)
                        }
                    }
                    .padding(.vertical, 4)
                }

                // ── Queue summary ──────────────────────────────────────────
                Section("Queue") {
                    NavigationLink(destination: IngestQueueView()) {
                        LabeledContent {
                            if viewModel.pendingCount > 0 {
                                TMBadge(text: "\(viewModel.pendingCount)", kind: .warning)
                            }
                        } label: {
                            Label("Ingest queue", systemImage: "tray.2")
                        }
                    }
                    NavigationLink(destination: IngestQueueView(filterStatus: "awaiting_review")) {
                        LabeledContent {
                            if viewModel.reviewCount > 0 {
                                TMBadge(text: "\(viewModel.reviewCount)", kind: .error)
                            }
                        } label: {
                            Label("Awaiting review", systemImage: "person.badge.clock")
                        }
                    }
                }

                // ── Recent events (live from WebSocket) ────────────────────
                if !viewModel.recentEvents.isEmpty {
                    Section("Live events") {
                        ForEach(viewModel.recentEvents) { event in
                            HStack(spacing: 10) {
                                Image(systemName: event.icon)
                                    .foregroundStyle(event.color)
                                    .frame(width: 22)
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(event.title)
                                        .font(.subheadline)
                                    Text(event.subtitle)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                    }
                }

                // ── Quick actions ──────────────────────────────────────────
                Section("Quick actions") {
                    Button {
                        viewModel.showTrigger = true
                    } label: {
                        Label("Trigger assessment", systemImage: "play.circle")
                    }
                    Button {
                        viewModel.showJDDraft = true
                    } label: {
                        Label("Submit JD draft", systemImage: "doc.badge.plus")
                    }
                    NavigationLink(destination: IngestQueueView(filterStatus: "jd_draft")) {
                        Label("JD drafts in review", systemImage: "doc.text.magnifyingglass")
                    }
                }
            }
            .navigationTitle("Agent Control")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        viewModel.refreshQueue()
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
            .refreshable { viewModel.refreshQueue() }
            .onAppear { viewModel.connect() }
            .onDisappear { viewModel.disconnect() }
            .sheet(isPresented: $viewModel.showTrigger) {
                AgentTriggerSheet(onSubmit: viewModel.triggerAssessment)
            }
            .sheet(isPresented: $viewModel.showJDDraft) {
                JDDraftSheet(onSubmit: viewModel.submitJDDraft)
            }
        }
    }
}

// MARK: - Supporting views

struct AgentTriggerSheet: View {
    let onSubmit: (String, String?) -> Void
    @State private var resumeId = ""
    @State private var jdText = ""
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section("Resume") {
                    TextField("Resume ID (UUID)", text: $resumeId)
                        .autocorrectionDisabled()
                }
                Section("Job description (optional)") {
                    TextEditor(text: $jdText)
                        .frame(height: 140)
                }
            }
            .navigationTitle("Trigger assessment")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Run") {
                        guard !resumeId.isEmpty else { return }
                        onSubmit(resumeId, jdText.isEmpty ? nil : jdText)
                        dismiss()
                    }
                    .disabled(resumeId.isEmpty)
                }
            }
        }
    }
}

struct JDDraftSheet: View {
    let onSubmit: (String, String?) -> Void
    @State private var jdText = ""
    @State private var title = ""
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section("Role title") {
                    TextField("e.g. Senior AI Engineer", text: $title)
                }
                Section("Paste JD draft") {
                    TextEditor(text: $jdText)
                        .frame(height: 200)
                }
            }
            .navigationTitle("Submit JD draft")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Analyse") {
                        guard jdText.count > 20 else { return }
                        onSubmit(jdText, title.isEmpty ? nil : title)
                        dismiss()
                    }
                    .disabled(jdText.count < 20)
                }
            }
        }
    }
}
