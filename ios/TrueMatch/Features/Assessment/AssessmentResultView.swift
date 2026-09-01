//
//  AssessmentResultView.swift
//  TrueMatch
//
//  Top-level assessment results screen. Composes the dual score, counter
//  recommendation, capability narrative, trajectory, gap analysis and the
//  display-only governance panel.
//

import SwiftUI
import SwiftData

struct AssessmentResultView: View {
    let assessmentId: String
    /// When true, loads bundled preview data instead of hitting the network.
    var usePreview: Bool = false

    @StateObject private var viewModel: AssessmentViewModel
    @Environment(\.trueMatchTheme) private var theme
    @Environment(\.modelContext) private var modelContext

    init(assessmentId: String, usePreview: Bool = false) {
        self.assessmentId = assessmentId
        self.usePreview = usePreview
        _viewModel = StateObject(wrappedValue: AssessmentViewModel(assessmentId: assessmentId))
    }

    var body: some View {
        ScrollView {
            VStack(spacing: theme.spacing.md) {
                if let assessment = viewModel.assessment {
                    if viewModel.isProcessing {
                        processingState
                    } else {
                        results(for: assessment)
                    }
                } else if viewModel.isLoading {
                    TMSkeletonView(lineCount: 6).padding()
                } else if let error = viewModel.errorMessage {
                    errorState(error)
                }
            }
            .padding(theme.spacing.lg)
        }
        .navigationTitle("Assessment")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await viewModel.load(usePreview: usePreview)
            viewModel.cache(in: modelContext)
        }
        .onDisappear { viewModel.disconnect() }
    }

    // MARK: - States

    private var processingState: some View {
        VStack(spacing: theme.spacing.md) {
            Image(systemName: "gearshape.2")
                .font(.system(size: 44))
                .foregroundStyle(theme.colors.primary)
            Text(viewModel.currentStage?.displayText ?? "Assessing candidate...")
                .font(theme.typography.headline)
            TMProgressLoading(progress: viewModel.progressPercent / 100, message: "Progress")
        }
        .padding(.vertical, theme.spacing.xl)
    }

    @ViewBuilder
    private func results(for assessment: AssessmentResponse) -> some View {
        if let traditional = assessment.traditionalScore,
           let capability = assessment.capabilityScore {
            DualScoreView(traditional: traditional, capability: capability, delta: assessment.delta)
        }

        if let counter = assessment.counterRecommendation, counter.triggered {
            counterRecommendationBanner(counter)
        }

        if let capability = assessment.capabilityScore {
            CapabilityNarrativeView(capability: capability)
        }

        if let trajectory = assessment.trajectory {
            TrajectoryView(trajectory: trajectory)
        }

        if let traditional = assessment.traditionalScore {
            GapAnalysisView(traditional: traditional, jdQuality: assessment.jdQuality)
        }

        if let governance = assessment.governance {
            GovernanceStatusView(governance: governance)
        }
    }

    private func counterRecommendationBanner(_ counter: CounterRecommendation) -> some View {
        TMCard(style: .elevated) {
            VStack(alignment: .leading, spacing: theme.spacing.xs) {
                HStack(spacing: theme.spacing.xxs) {
                    Image(systemName: "arrow.uturn.up.circle.fill")
                        .foregroundStyle(theme.colors.accent)
                    Text("Counter-recommendation")
                        .font(theme.typography.headline)
                        .foregroundStyle(Color.tmTextPrimary)
                    Spacer()
                    TMBadge(text: "Triggered", kind: .warning)
                }
                if let reasoning = counter.reasoning {
                    Text(reasoning)
                        .font(theme.typography.body)
                        .foregroundStyle(Color.tmTextSecondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                ForEach(counter.evidencePoints, id: \.self) { point in
                    HStack(alignment: .top, spacing: theme.spacing.xxs) {
                        Image(systemName: "checkmark.circle.fill")
                            .font(.system(size: 13))
                            .foregroundStyle(theme.colors.accent)
                            .padding(.top, 1)
                        Text(point)
                            .font(theme.typography.caption)
                            .foregroundStyle(Color.tmTextSecondary)
                    }
                }
            }
        }
    }

    private func errorState(_ message: String) -> some View {
        VStack(spacing: theme.spacing.sm) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 36))
                .foregroundStyle(theme.colors.error)
            Text(message)
                .font(theme.typography.caption)
                .foregroundStyle(Color.tmTextSecondary)
                .multilineTextAlignment(.center)
            TMButton(title: "Retry", variant: .secondary) {
                Task { await viewModel.load(usePreview: usePreview) }
            }
        }
        .padding(.vertical, theme.spacing.xl)
    }
}

#Preview {
    NavigationStack {
        AssessmentResultView(assessmentId: "preview", usePreview: true)
    }
}
