//
//  RecruiterDecisionView.swift
//  TrueMatch
//
//  One-tap approve/reject interface with quick decision templates, feedback
//  input, and offer recording capability.
//

import SwiftUI

struct RecruiterDecisionView: View {
    @StateObject private var viewModel = RecruiterDecisionViewModel()
    @Environment(\.trueMatchTheme) private var theme
    @State private var showCandidateSelector = false

    var body: some View {
        NavigationStack {
            VStack(spacing: theme.spacing.md) {
                if let candidate = viewModel.selectedCandidate {
                    DecisionPanel(viewModel: viewModel, candidate: candidate, theme: theme)
                } else {
                    // Empty state prompting candidate selection
                    VStack(spacing: theme.spacing.md) {
                        Image(systemName: "hand.thumbsup.fill")
                            .font(.system(size: 48))
                            .foregroundStyle(theme.colors.primary)

                        Text("Make a Decision")
                            .font(theme.typography.title)

                        Text("Select a candidate from your queue to approve, reject, or revisit")
                            .font(theme.typography.body)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)

                        Button {
                            showCandidateSelector = true
                        } label: {
                            Text("Select Candidate")
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(TMButtonStyle())
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .center)
                    .padding(theme.spacing.md)
                }
            }
            .navigationTitle("Decision Center")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                if viewModel.selectedCandidate != nil {
                    ToolbarItem(placement: .navigationBarTrailing) {
                        Button("Clear") {
                            viewModel.clearSelection()
                        }
                    }
                }
            }
            .alert("Error", isPresented: Binding(
                get: { viewModel.errorMessage != nil },
                set: { if !$0 { viewModel.errorMessage = nil } }
            )) {
                Button("OK", role: .cancel) { viewModel.errorMessage = nil }
            } message: {
                Text(viewModel.errorMessage ?? "")
            }
            .sheet(isPresented: $showCandidateSelector) {
                CandidateSelectorSheet(viewModel: viewModel)
            }
        }
    }
}

// MARK: - Decision Panel

private struct DecisionPanel: View {
    @ObservedObject var viewModel: RecruiterDecisionViewModel
    let candidate: CandidateQueueItem
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        ScrollView {
            VStack(spacing: theme.spacing.md) {
                // Candidate Header
                CandidateHeader(candidate: candidate, theme: theme)

                Divider()

                // Decision Buttons (3 quick options)
                VStack(spacing: theme.spacing.sm) {
                    Text("What's your decision?")
                        .font(theme.typography.headline)
                        .frame(maxWidth: .infinity, alignment: .leading)

                    HStack(spacing: theme.spacing.sm) {
                        DecisionButton(
                            title: "Approve",
                            icon: "checkmark.circle.fill",
                            color: .green,
                            isSelected: viewModel.selectedDecision == .approve,
                            action: {
                                viewModel.selectedDecision = .approve
                            }
                        )

                        DecisionButton(
                            title: "Reject",
                            icon: "xmark.circle.fill",
                            color: .red,
                            isSelected: viewModel.selectedDecision == .reject,
                            action: {
                                viewModel.selectedDecision = .reject
                            }
                        )

                        DecisionButton(
                            title: "Revisit",
                            icon: "clock.fill",
                            color: .orange,
                            isSelected: viewModel.selectedDecision == .revisit,
                            action: {
                                viewModel.selectedDecision = .revisit
                            }
                        )
                    }
                }
                .padding(theme.spacing.sm)
                .background(Color(.secondarySystemBackground))
                .clipShape(RoundedRectangle(cornerRadius: theme.radii.md))

                // Templates
                if !viewModel.availableTemplates.isEmpty {
                    VStack(alignment: .leading, spacing: theme.spacing.xs) {
                        Text("Quick Templates")
                            .font(theme.typography.headline)

                        VStack(spacing: theme.spacing.xs) {
                            ForEach(viewModel.availableTemplates, id: \.self) { template in
                                TemplateButton(
                                    template: template,
                                    isSelected: viewModel.selectedTemplate == template,
                                    action: {
                                        viewModel.selectTemplate(template)
                                    }
                                )
                            }
                        }
                    }
                }

                // Feedback Input
                VStack(alignment: .leading, spacing: theme.spacing.xs) {
                    Text("Additional Feedback")
                        .font(theme.typography.headline)

                    TextEditor(text: $viewModel.feedbackText)
                        .frame(minHeight: 100)
                        .padding(theme.spacing.xs)
                        .background(Color(.secondarySystemBackground))
                        .clipShape(RoundedRectangle(cornerRadius: theme.radii.md))
                        .overlay {
                            RoundedRectangle(cornerRadius: theme.radii.md)
                                .stroke(Color(.separator), lineWidth: 1)
                        }
                }

                // Action Buttons
                if let decision = viewModel.selectedDecision {
                    VStack(spacing: theme.spacing.sm) {
                        Button {
                            Task {
                                await viewModel.recordDecision(decision)
                            }
                        } label: {
                            HStack {
                                Image(systemName: "checkmark.square.fill")
                                Text("Record Decision")
                            }
                            .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(TMButtonStyle(tint: decisionColor(decision)))
                        .disabled(viewModel.isSubmitting)

                        if decision == .approve {
                            Button {
                                Task {
                                    await viewModel.prepareOffer()
                                }
                            } label: {
                                HStack {
                                    Image(systemName: "star.fill")
                                    Text("Prepare Offer")
                                }
                                .frame(maxWidth: .infinity)
                            }
                            .buttonStyle(TMButtonStyle(tint: theme.colors.accent))
                        }
                    }
                }

                Spacer()
            }
            .padding(theme.spacing.md)
        }
        .overlay {
            if viewModel.isSuccessful {
                SuccessOverlay(theme: theme)
            }
        }
    }

    private func decisionColor(_ decision: DecisionRecord.Decision) -> Color {
        switch decision {
        case .approve: return .green
        case .reject: return .red
        case .revisit: return .orange
        }
    }
}

// MARK: - Candidate Header

private struct CandidateHeader: View {
    let candidate: CandidateQueueItem
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        HStack(spacing: theme.spacing.sm) {
            if let url = URL(string: candidate.avatarUrl ?? "") {
                AsyncImage(url: url) { phase in
                    switch phase {
                    case .success(let image):
                        image.resizable().scaledToFill()
                    default:
                        Image(systemName: "person.fill")
                    }
                }
                .frame(width: 56, height: 56)
                .clipShape(Circle())
            } else {
                Image(systemName: "person.fill")
                    .frame(width: 56, height: 56)
                    .background(Circle().fill(.secondary.opacity(0.2)))
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(candidate.name)
                    .font(theme.typography.headline)

                Text(candidate.positionTitle)
                    .font(theme.typography.caption)
                    .foregroundStyle(.secondary)

                HStack(spacing: theme.spacing.xs) {
                    Text("Score: \(Int(candidate.score))")
                        .font(theme.typography.chip)
                        .foregroundStyle(scoreColor(candidate.score))

                    if let delta = candidate.delta, delta != 0 {
                        Label("\(Int(abs(delta)))", systemImage: delta > 0 ? "triangle.fill" : "triangle.fill")
                            .font(theme.typography.chip)
                            .foregroundStyle(delta > 0 ? .green : .red)
                    }
                }
            }

            Spacer()
        }
        .tmCard()
    }

    private func scoreColor(_ score: Double) -> Color {
        if score >= 80 {
            return .green
        } else if score >= 60 {
            return .orange
        } else {
            return .red
        }
    }
}

// MARK: - Decision Button

private struct DecisionButton: View {
    let title: String
    let icon: String
    let color: Color
    let isSelected: Bool
    let action: () -> Void
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.system(size: 24))
                Text(title)
                    .font(theme.typography.chip)
            }
            .frame(maxWidth: .infinity)
            .padding(theme.spacing.sm)
            .background(isSelected ? color.opacity(0.2) : Color.clear)
            .foregroundStyle(color)
            .clipShape(RoundedRectangle(cornerRadius: theme.radii.md))
            .overlay {
                if isSelected {
                    RoundedRectangle(cornerRadius: theme.radii.md)
                        .stroke(color, lineWidth: 2)
                }
            }
        }
    }
}

// MARK: - Template Button

private struct TemplateButton: View {
    let template: String
    let isSelected: Bool
    let action: () -> Void
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        Button(action: action) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(template)
                        .font(theme.typography.body)
                        .multilineTextAlignment(.leading)
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                if isSelected {
                    Image(systemName: "checkmark")
                        .font(.system(size: 14, weight: .semibold))
                }
            }
            .padding(theme.spacing.sm)
            .background(
                isSelected
                    ? theme.colors.primary.opacity(0.1)
                    : Color(.secondarySystemBackground)
            )
            .foregroundStyle(isSelected ? theme.colors.primary : .primary)
            .clipShape(RoundedRectangle(cornerRadius: theme.radii.md))
        }
    }
}

// MARK: - Success Overlay

private struct SuccessOverlay: View {
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(spacing: theme.spacing.md) {
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 48))
                .foregroundStyle(.green)

            Text("Decision Recorded")
                .font(theme.typography.title)

            Text("The candidate has been updated in the pipeline")
                .font(theme.typography.body)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.black.opacity(0.4))
        .clipShape(RoundedRectangle(cornerRadius: theme.radii.md))
    }
}

// MARK: - Candidate Selector Sheet

private struct CandidateSelectorSheet: View {
    @ObservedObject var viewModel: RecruiterDecisionViewModel
    @Environment(\.dismiss) private var dismiss
    @Environment(\.trueMatchTheme) private var theme

    // Mock data for now
    let mockCandidates = [
        CandidateQueueItem(
            id: "1", candidateId: "c1", name: "Alice Johnson",
            email: "alice@example.com", avatarUrl: nil, score: 85,
            delta: 5, stage: .screening, positionId: "p1",
            positionTitle: "Senior Engineer", nextAction: "Review CV",
            daysSinceAdded: 2
        ),
        CandidateQueueItem(
            id: "2", candidateId: "c2", name: "Bob Smith",
            email: "bob@example.com", avatarUrl: nil, score: 72,
            delta: -2, stage: .interview, positionId: "p1",
            positionTitle: "Senior Engineer", nextAction: "Schedule",
            daysSinceAdded: 5
        ),
    ]

    var body: some View {
        NavigationStack {
            List(mockCandidates) { candidate in
                Button {
                    viewModel.selectCandidate(candidate)
                    dismiss()
                } label: {
                    HStack(spacing: theme.spacing.sm) {
                        if let url = URL(string: candidate.avatarUrl ?? "") {
                            AsyncImage(url: url) { phase in
                                switch phase {
                                case .success(let image):
                                    image.resizable().scaledToFill()
                                default:
                                    Image(systemName: "person.fill")
                                }
                            }
                            .frame(width: 40, height: 40)
                            .clipShape(Circle())
                        } else {
                            Image(systemName: "person.fill")
                                .frame(width: 40, height: 40)
                                .background(Circle().fill(.secondary.opacity(0.2)))
                        }

                        VStack(alignment: .leading, spacing: 2) {
                            Text(candidate.name)
                                .font(theme.typography.headline)
                                .foregroundStyle(.primary)

                            HStack {
                                Text(candidate.positionTitle)
                                    .font(theme.typography.caption)
                                    .foregroundStyle(.secondary)

                                Text("•")

                                Text("\(Int(candidate.score))")
                                    .font(theme.typography.caption)
                                    .foregroundStyle(theme.colors.capability)
                            }
                        }

                        Spacer()

                        Image(systemName: "chevron.right")
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .navigationTitle("Select Candidate")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

// MARK: - Preview

#Preview {
    RecruiterDecisionView()
}
