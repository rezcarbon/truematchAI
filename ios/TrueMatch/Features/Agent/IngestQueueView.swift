//
//  IngestQueueView.swift
//  TrueMatch
//
//  Live view of the autonomous ingest queue. Recruiters can approve, reject, or
//  reassign every CV and JD draft the agents have picked up — from their phone.
//

import SwiftUI

struct IngestQueueView: View {
    var filterStatus: String? = nil
    @StateObject private var viewModel = IngestQueueViewModel()

    var body: some View {
        Group {
            if viewModel.isLoading {
                ProgressView("Loading queue…")
            } else if viewModel.items.isEmpty {
                ContentUnavailableView(
                    "Queue is empty",
                    systemImage: "tray",
                    description: Text(filterStatus == nil ? "No items in the ingest queue." : "No items with status '\(filterStatus!)'.")
                )
            } else {
                List(viewModel.items) { item in
                    NavigationLink(destination: IngestItemDetailView(item: item, viewModel: viewModel)) {
                        IngestQueueRow(item: item)
                    }
                }
            }
        }
        .navigationTitle(filterStatus.map { "\($0.replacingOccurrences(of: "_", with: " ").capitalized)" } ?? "Ingest Queue")
        .refreshable { viewModel.load(status: filterStatus) }
        .onAppear { viewModel.load(status: filterStatus) }
        .alert("Error", isPresented: $viewModel.hasError) {
            Button("OK", role: .cancel) {}
        } message: { Text(viewModel.errorMessage ?? "Unknown error") }
    }
}

// MARK: - Row

struct IngestQueueRow: View {
    let item: IngestQueueItem

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Image(systemName: item.ingestType == "cv" ? "person.text.rectangle" : "doc.text")
                    .foregroundStyle(.secondary)
                Text(item.ingestType == "cv" ? "CV" : "JD Draft")
                    .font(.subheadline.weight(.semibold))
                Spacer()
                StatusBadge(status: item.status)
            }
            HStack {
                Label(item.source.capitalized, systemImage: item.source == "email" ? "envelope" : "folder")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Spacer()
                Text(item.createdAt.prefix(10))
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
            }
        }
        .padding(.vertical, 2)
    }
}

// MARK: - Status badge

struct StatusBadge: View {
    let status: String
    var body: some View {
        Text(status.replacingOccurrences(of: "_", with: " ").capitalized)
            .font(.caption2.weight(.medium))
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(color(for: status).opacity(0.15))
            .foregroundStyle(color(for: status))
            .clipShape(Capsule())
    }
    private func color(for s: String) -> Color {
        switch s {
        case "completed": return .green
        case "awaiting_review": return .orange
        case "failed", "rejected": return .red
        case "processing": return .blue
        default: return .secondary
        }
    }
}

// MARK: - Detail + actions

struct IngestItemDetailView: View {
    let item: IngestQueueItem
    @ObservedObject var viewModel: IngestQueueViewModel
    @State private var notes = ""
    @State private var reassignPositionId = ""
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        Form {
            Section("Item") {
                LabeledContent("Type", value: item.ingestType == "cv" ? "CV" : "JD Draft")
                LabeledContent("Source", value: item.source.capitalized)
                LabeledContent("Status", value: item.status)
                LabeledContent("Retries", value: "\(item.retryCount)")
                if let err = item.lastError {
                    VStack(alignment: .leading) {
                        Text("Error").foregroundStyle(.secondary).font(.caption)
                        Text(err).font(.caption).foregroundStyle(.red)
                    }
                }
            }

            if item.ingestType == "jd_draft", let output = item.jdAgentOutput {
                Section("JD Analysis") {
                    LabeledContent("Quality score", value: "\(output.qualityScore ?? 0)/100")
                    if let issues = output.issues, !issues.isEmpty {
                        Text("\(issues.count) issue(s) found")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                }
                Section {
                    NavigationLink("View AI-improved draft") {
                        JDDraftReviewView(positionId: item.positionId, queueItemId: item.id)
                    }
                }
            }

            if item.status == "awaiting_review" {
                Section("Review notes") {
                    TextField("Optional notes…", text: $notes, axis: .vertical)
                        .lineLimit(3)
                }

                if item.ingestType == "cv" {
                    Section("Reassign to position (optional)") {
                        TextField("Position ID (UUID)", text: $reassignPositionId)
                            .autocorrectionDisabled()
                    }
                }

                Section {
                    Button("Approve") {
                        if !reassignPositionId.isEmpty {
                            viewModel.reassign(id: item.id, positionId: reassignPositionId, notes: notes)
                        } else {
                            viewModel.approve(id: item.id, notes: notes)
                        }
                        dismiss()
                    }
                    .tint(.green)

                    Button("Reject", role: .destructive) {
                        viewModel.reject(id: item.id, notes: notes)
                        dismiss()
                    }
                }
            }
        }
        .navigationTitle("Queue item")
        .navigationBarTitleDisplayMode(.inline)
    }
}
