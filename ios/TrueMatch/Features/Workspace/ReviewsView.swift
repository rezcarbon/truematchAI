//
//  ReviewsView.swift
//  TrueMatch
//
//  Recruiter review queue: list assessments, see the dual scores + delta, and
//  record a hiring decision (which drives the server-side learning loop).
//

import SwiftUI

@MainActor
final class ReviewsViewModel: ObservableObject {
    @Published var assessments: [AssessmentSummaryDTO] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var bannerMessage: String?

    private let api = APIClient.shared

    func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let resp = try await api.request(endpoint: .listAssessments(), type: AssessmentListResponse.self)
            assessments = resp.items
        } catch {
            TrueMatchLogger.log(.error, "Reviews load failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }

    func recordDecision(_ a: AssessmentSummaryDTO, decision: String, followedAI: Bool, notes: String?) async {
        do {
            let req = DecisionRequest(
                assessmentId: a.id,
                positionId: a.positionId,
                decision: decision,
                aiRecommendationFollowed: followedAI,
                overrideReasoning: notes
            )
            let resp = try await api.request(endpoint: .recordDecision(req), type: DecisionResponseDTO.self)
            bannerMessage = "Decision recorded: \(resp.decision)"
        } catch {
            TrueMatchLogger.log(.error, "Record decision failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }
}

struct ReviewsView: View {
    @StateObject private var viewModel = ReviewsViewModel()

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.isLoading && viewModel.assessments.isEmpty {
                    ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if viewModel.assessments.isEmpty {
                    ContentUnavailableViewCompat(
                        title: "No assessments",
                        systemImage: "doc.text.magnifyingglass",
                        message: "Completed candidate assessments will appear here for review."
                    )
                } else {
                    List(viewModel.assessments) { a in
                        NavigationLink(destination: ReviewDetailView(assessment: a, viewModel: viewModel)) {
                            AssessmentRow(assessment: a)
                        }
                    }
                }
            }
            .navigationTitle("Reviews")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button { Task { await viewModel.load() } } label: { Image(systemName: "arrow.clockwise") }
                }
            }
            .refreshable { await viewModel.load() }
            .task { await viewModel.load() }
            .alert("Something went wrong",
                   isPresented: Binding(get: { viewModel.errorMessage != nil },
                                        set: { if !$0 { viewModel.errorMessage = nil } })) {
                Button("OK", role: .cancel) { viewModel.errorMessage = nil }
            } message: { Text(viewModel.errorMessage ?? "") }
        }
    }
}

struct AssessmentRow: View {
    let assessment: AssessmentSummaryDTO
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("Candidate \(String(assessment.userId.prefix(8)))")
                    .font(.subheadline.weight(.semibold))
                Spacer()
                TMBadge(text: assessment.status.replacingOccurrences(of: "_", with: " ").capitalized,
                        kind: assessment.status == "completed" ? .success : .warning)
            }
            HStack(spacing: 14) {
                ScorePill(label: "ATS", value: assessment.traditionalScore)
                ScorePill(label: "Capability", value: assessment.capabilityScore)
                if let d = assessment.scoreDelta {
                    Text(d >= 0 ? "+\(d)" : "\(d)")
                        .font(.caption.weight(.bold))
                        .foregroundStyle(d > 0 ? .green : .secondary)
                }
                if assessment.counterRecTriggered == true {
                    Image(systemName: "sparkle.magnifyingglass").foregroundStyle(TrueMatchTheme.brandAccent)
                }
            }
        }
        .padding(.vertical, 2)
    }
}

struct ScorePill: View {
    let label: String
    let value: Int?
    var body: some View {
        VStack(spacing: 1) {
            Text("\(value ?? 0)").font(.callout.weight(.bold))
            Text(label).font(.caption2).foregroundStyle(.secondary)
        }
    }
}

struct ReviewDetailView: View {
    let assessment: AssessmentSummaryDTO
    @ObservedObject var viewModel: ReviewsViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var notes = ""
    @State private var submitting = false

    private let decisions: [(String, String)] = [
        ("hire", "Hire"), ("interview", "Interview"), ("advance", "Advance"),
        ("hold", "Hold"), ("reject", "Reject"),
    ]

    var body: some View {
        Form {
            Section("Scores") {
                LabeledContent("Traditional ATS", value: "\(assessment.traditionalScore ?? 0)")
                LabeledContent("Capability", value: "\(assessment.capabilityScore ?? 0)")
                LabeledContent("Delta", value: "\(assessment.scoreDelta ?? 0)")
                LabeledContent("Status", value: assessment.status.replacingOccurrences(of: "_", with: " ").capitalized)
                if assessment.counterRecTriggered == true {
                    Label("Counter-recommendation triggered", systemImage: "sparkle.magnifyingglass")
                        .foregroundStyle(TrueMatchTheme.brandAccent)
                }
            }
            Section("Notes (optional)") {
                TextEditor(text: $notes).frame(height: 90)
            }
            Section("Record decision") {
                ForEach(decisions, id: \.0) { value, label in
                    Button {
                        Task {
                            submitting = true
                            await viewModel.recordDecision(
                                assessment, decision: value,
                                followedAI: !(assessment.counterRecTriggered == true),
                                notes: notes.isEmpty ? nil : notes
                            )
                            submitting = false
                            await viewModel.load()
                            dismiss()
                        }
                    } label: {
                        HStack {
                            Text(label)
                            Spacer()
                            if value == "hire" { Image(systemName: "checkmark.seal.fill").foregroundStyle(.green) }
                            if value == "reject" { Image(systemName: "xmark.octagon.fill").foregroundStyle(.red) }
                        }
                    }
                    .disabled(submitting)
                }
            }
        }
        .navigationTitle("Review")
        .navigationBarTitleDisplayMode(.inline)
    }
}

/// Small backport so the views compile on iOS 17 without ContentUnavailableView
/// availability fuss.
struct ContentUnavailableViewCompat: View {
    let title: String
    let systemImage: String
    let message: String
    var body: some View {
        VStack(spacing: 10) {
            Image(systemName: systemImage).font(.system(size: 40)).foregroundStyle(TrueMatchTheme.accentColor)
            Text(title).font(.headline)
            Text(message).font(.subheadline).foregroundStyle(.secondary).multilineTextAlignment(.center)
        }.padding(40)
    }
}
