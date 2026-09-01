//
//  CandidateAssessmentResultsView.swift
//  TrueMatch
//
//  Displays three-signal assessment gauges (Traditional, Semantic, Capability),
//  delta visualization, strengths section with evidence, skill gaps with learning
//  paths, and call-to-action button.
//

import SwiftUI

struct CandidateAssessmentResultsView: View {
    @StateObject private var viewModel: AssessmentResultsViewModel
    @State private var showJobRecommendations = false
    @Environment(\.trueMatchTheme) var theme

    init(candidateId: String) {
        _viewModel = StateObject(wrappedValue: AssessmentResultsViewModel(candidateId: candidateId))
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: theme.spacing.lg) {
                    // Header
                    VStack(spacing: theme.spacing.sm) {
                        Text("Your Assessment Results")
                            .font(theme.typography.title)
                            .frame(maxWidth: .infinity, alignment: .leading)

                        Text("Personalized insights across three evaluation signals")
                            .font(theme.typography.caption)
                            .foregroundColor(.gray)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .padding(.horizontal, theme.spacing.sm)

                    // Three-Signal Gauges
                    if !viewModel.isLoading {
                        VStack(spacing: theme.spacing.md) {
                            HStack(spacing: theme.spacing.md) {
                                ScoreGaugeView(
                                    label: "Traditional",
                                    score: viewModel.traditionalScore,
                                    color: theme.colors.traditional
                                )
                                .accessibilityLabel("Traditional Assessment Score")
                                .accessibilityValue("\(String(format: "%.0f", viewModel.traditionalScore)) percent")

                                ScoreGaugeView(
                                    label: "Semantic",
                                    score: viewModel.semanticScore,
                                    color: theme.colors.primary
                                )
                                .accessibilityLabel("Semantic Assessment Score")
                                .accessibilityValue("\(String(format: "%.0f", viewModel.semanticScore)) percent")
                            }

                            HStack(spacing: theme.spacing.md) {
                                ScoreGaugeView(
                                    label: "Capability",
                                    score: viewModel.capabilityScore,
                                    color: theme.colors.capability
                                )
                                .accessibilityLabel("Capability Assessment Score")
                                .accessibilityValue("\(String(format: "%.0f", viewModel.capabilityScore)) percent")
                                .frame(maxWidth: .infinity)

                                Spacer()
                            }
                        }
                        .padding(theme.spacing.sm)
                        .background(Color(.systemGray6))
                        .cornerRadius(theme.cornerRadii.md)
                        .padding(.horizontal, theme.spacing.sm)

                        // Delta Visualization
                        if !viewModel.deltas.isEmpty {
                            DeltaVisualizationView(deltas: viewModel.deltas, theme: theme)
                                .padding(.horizontal, theme.spacing.sm)
                        }
                    }

                    // Strengths Section
                    VStack(spacing: theme.spacing.sm) {
                        HStack {
                            Label("Your Strengths", systemImage: "star.fill")
                                .font(theme.typography.headline)
                                .foregroundColor(theme.colors.success)

                            Spacer()

                            Text("\(viewModel.strengths.count)")
                                .font(theme.typography.caption)
                                .foregroundColor(.gray)
                        }
                        .padding(.horizontal, theme.spacing.sm)

                        if viewModel.strengths.isEmpty && !viewModel.isLoading {
                            Text("No strengths identified yet")
                                .font(theme.typography.body)
                                .foregroundColor(.gray)
                                .padding(theme.spacing.sm)
                        } else {
                            LazyVStack(spacing: theme.spacing.sm) {
                                ForEach(viewModel.strengths.prefix(5)) { strength in
                                    StrengthCardView(strength: strength, theme: theme)
                                }
                            }
                            .padding(.horizontal, theme.spacing.sm)
                        }
                    }

                    // Skill Gaps Section
                    VStack(spacing: theme.spacing.sm) {
                        HStack {
                            Label("Skill Gaps", systemImage: "exclamationmark.circle.fill")
                                .font(theme.typography.headline)
                                .foregroundColor(theme.colors.warning)

                            Spacer()

                            Text("\(viewModel.skillGaps.count)")
                                .font(theme.typography.caption)
                                .foregroundColor(.gray)
                        }
                        .padding(.horizontal, theme.spacing.sm)

                        if viewModel.skillGaps.isEmpty && !viewModel.isLoading {
                            Text("No significant gaps identified")
                                .font(theme.typography.body)
                                .foregroundColor(.gray)
                                .padding(theme.spacing.sm)
                        } else {
                            LazyVStack(spacing: theme.spacing.sm) {
                                ForEach(viewModel.skillGaps.prefix(5)) { gap in
                                    SkillGapCardView(gap: gap, theme: theme)
                                }
                            }
                            .padding(.horizontal, theme.spacing.sm)
                        }
                    }

                    // Learning Paths Section
                    if !viewModel.learningPaths.isEmpty {
                        VStack(spacing: theme.spacing.sm) {
                            HStack {
                                Label("Recommended Learning Paths", systemImage: "book.fill")
                                    .font(theme.typography.headline)
                                    .foregroundColor(theme.colors.primary)

                                Spacer()
                            }
                            .padding(.horizontal, theme.spacing.sm)

                            LazyVStack(spacing: theme.spacing.sm) {
                                ForEach(viewModel.learningPaths.prefix(3)) { path in
                                    LearningPathCardView(path: path, theme: theme)
                                }
                            }
                            .padding(.horizontal, theme.spacing.sm)
                        }
                    }

                    // Call-to-Action
                    Button {
                        showJobRecommendations = true
                    } label: {
                        HStack {
                            Image(systemName: "briefcase.fill")
                            Text("Browse Jobs")
                                .font(theme.typography.headline)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(theme.spacing.sm)
                        .background(theme.colors.primary)
                        .foregroundColor(.white)
                        .cornerRadius(theme.cornerRadii.md)
                    }
                    .accessibilityLabel("Browse Jobs")
                    .accessibilityHint("Navigate to job recommendations based on your assessment results")
                    .padding(.horizontal, theme.spacing.sm)
                    .padding(.vertical, theme.spacing.md)
                }
            }
            .navigationTitle("Assessment Results")
            .navigationBarTitleDisplayMode(.inline)
            .navigationDestination(isPresented: $showJobRecommendations) {
                CandidateJobRecommendationsView(candidateId: viewModel.candidateId)
            }
            .task {
                if viewModel.assessmentResult == nil {
                    await viewModel.loadAssessment()
                }
            }
            .overlay {
                if viewModel.isLoading {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(Color.black.opacity(0.1))
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
        }
    }
}

// MARK: - Score Gauge

struct ScoreGaugeView: View {
    let label: String
    let score: Double
    let color: Color
    @Environment(\.trueMatchTheme) var theme

    var body: some View {
        VStack(spacing: theme.spacing.xxs) {
            ZStack {
                // Background circle
                Circle()
                    .stroke(Color(.systemGray6), lineWidth: 8)

                // Score arc
                Circle()
                    .trim(from: 0, to: CGFloat(score / 100))
                    .stroke(color, style: StrokeStyle(lineWidth: 8, lineCap: .round))
                    .rotationEffect(.degrees(-90))

                // Center text
                VStack(spacing: theme.spacing.xxxs) {
                    Text(String(format: "%.0f", score))
                        .font(theme.typography.headline)
                        .fontWeight(.bold)

                    Text("%")
                        .font(theme.typography.caption)
                        .foregroundColor(.gray)
                }
            }
            .frame(height: 100)

            Text(label)
                .font(theme.typography.caption)
                .foregroundColor(.gray)
        }
        .frame(maxWidth: .infinity)
    }
}

// MARK: - Delta Visualization

struct DeltaVisualizationView: View {
    let deltas: [String: Double]
    let theme: TrueMatchTheme

    var body: some View {
        VStack(spacing: theme.spacing.sm) {
            Text("Score Deltas")
                .font(theme.typography.headline)
                .frame(maxWidth: .infinity, alignment: .leading)

            ForEach(Array(deltas.sorted { $0.key < $1.key }), id: \.key) { key, value in
                HStack(spacing: theme.spacing.sm) {
                    Text(deltaLabel(for: key))
                        .font(theme.typography.body)
                        .frame(maxWidth: .infinity, alignment: .leading)

                    HStack(spacing: theme.spacing.xxs) {
                        Image(systemName: value >= 0 ? "arrow.up.right" : "arrow.down.left")
                            .font(.caption)

                        Text(String(format: "%+.0f%%", value))
                            .font(theme.typography.headline)
                    }
                    .foregroundColor(value >= 0 ? theme.colors.deltaPositive : theme.colors.deltaNegative)
                }
                .padding(.horizontal, theme.spacing.sm)
                .padding(.vertical, theme.spacing.xs)
                .background(Color(.systemGray6))
                .cornerRadius(theme.cornerRadii.sm)
            }
        }
        .padding(theme.spacing.sm)
        .background(Color(.systemBackground))
        .cornerRadius(theme.cornerRadii.md)
    }

    private func deltaLabel(for key: String) -> String {
        switch key {
        case "capability_vs_traditional": return "Capability vs Traditional"
        case "semantic_vs_traditional": return "Semantic vs Traditional"
        case "capability_vs_semantic": return "Capability vs Semantic"
        default: return key
        }
    }
}

// MARK: - Strength Card

struct StrengthCardView: View {
    let strength: SkillEvidence
    let theme: TrueMatchTheme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.xs) {
            HStack {
                VStack(alignment: .leading, spacing: theme.spacing.xxxs) {
                    Text(strength.skillName)
                        .font(theme.typography.headline)

                    Text(strength.proficiency.capitalized)
                        .font(theme.typography.caption)
                        .foregroundColor(theme.colors.success)
                }

                Spacer()

                Text(String(format: "%.0f%%", strength.confidenceScore * 100))
                    .font(theme.typography.caption)
                    .foregroundColor(.gray)
            }

            if !strength.evidence.isEmpty {
                VStack(alignment: .leading, spacing: theme.spacing.xxxs) {
                    Text("Evidence")
                        .font(theme.typography.caption)
                        .foregroundColor(.gray)

                    ForEach(strength.evidence.prefix(2), id: \.self) { evidence in
                        HStack(spacing: theme.spacing.xs) {
                            Image(systemName: "checkmark.circle.fill")
                                .font(.caption)
                                .foregroundColor(theme.colors.success)

                            Text(evidence)
                                .font(theme.typography.caption)
                                .lineLimit(1)
                        }
                    }
                }
            }
        }
        .padding(theme.spacing.sm)
        .background(Color(.systemGray6))
        .cornerRadius(theme.cornerRadii.sm)
    }
}

// MARK: - Skill Gap Card

struct SkillGapCardView: View {
    let gap: SkillEvidence
    let theme: TrueMatchTheme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.xs) {
            HStack {
                VStack(alignment: .leading, spacing: theme.spacing.xxxs) {
                    Text(gap.skillName)
                        .font(theme.typography.headline)

                    HStack(spacing: theme.spacing.xs) {
                        Text("Current: \(gap.proficiency.capitalized)")
                            .font(theme.typography.caption)
                            .foregroundColor(.gray)

                        Text("→ Advanced")
                            .font(theme.typography.caption)
                            .foregroundColor(theme.colors.warning)
                    }
                }

                Spacer()

                Text(String(format: "%.0f%%", gap.confidenceScore * 100))
                    .font(theme.typography.caption)
                    .foregroundColor(.gray)
            }

            ProgressView(value: gap.confidenceScore)
                .tint(theme.colors.warning)
        }
        .padding(theme.spacing.sm)
        .background(Color(.systemGray6))
        .cornerRadius(theme.cornerRadii.sm)
    }
}

// MARK: - Learning Path Card

struct LearningPathCardView: View {
    let path: LearningPath
    let theme: TrueMatchTheme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.sm) {
            HStack {
                VStack(alignment: .leading, spacing: theme.spacing.xxxs) {
                    Text(path.skillName)
                        .font(theme.typography.headline)

                    Text("\(path.currentLevel) → \(path.targetLevel)")
                        .font(theme.typography.caption)
                        .foregroundColor(.gray)
                }

                Spacer()

                VStack(alignment: .trailing, spacing: theme.spacing.xxxs) {
                    Text("\(path.estimatedHours)h")
                        .font(theme.typography.caption)
                        .foregroundColor(.gray)

                    Text("estimated")
                        .font(theme.typography.caption)
                        .foregroundColor(.gray)
                }
            }

            if !path.resources.isEmpty {
                VStack(alignment: .leading, spacing: theme.spacing.xs) {
                    Text("\(path.resources.count) resources available")
                        .font(theme.typography.caption)
                        .foregroundColor(theme.colors.primary)
                }
            }
        }
        .padding(theme.spacing.sm)
        .background(Color(.systemGray6))
        .cornerRadius(theme.cornerRadii.sm)
    }
}

#Preview {
    CandidateAssessmentResultsView(candidateId: "preview-candidate")
        .environment(\.trueMatchTheme, TrueMatchTheme())
}
