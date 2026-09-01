//
//  RecruiterPipelineView.swift
//  TrueMatch
//
//  Kanban board for recruiter pipeline: drag-drop cards between Screening,
//  Interview, Offer, and Hired columns with score deltas and quick actions.
//

import SwiftUI

struct RecruiterPipelineView: View {
    @StateObject private var viewModel = RecruiterPipelineViewModel()
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Header with stats
                PipelineHeader(stats: viewModel.stats, theme: theme)

                if viewModel.isLoading {
                    SkeletonPipeline(theme: theme)
                } else {
                    // Kanban board
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(alignment: .top, spacing: theme.spacing.sm) {
                            PipelineColumn(
                                stage: .screening,
                                cards: viewModel.screeningCards,
                                viewModel: viewModel,
                                theme: theme
                            )

                            PipelineColumn(
                                stage: .interview,
                                cards: viewModel.interviewCards,
                                viewModel: viewModel,
                                theme: theme
                            )

                            PipelineColumn(
                                stage: .offer,
                                cards: viewModel.offerCards,
                                viewModel: viewModel,
                                theme: theme
                            )

                            PipelineColumn(
                                stage: .hired,
                                cards: viewModel.hiredCards,
                                viewModel: viewModel,
                                theme: theme
                            )
                        }
                        .padding(theme.spacing.sm)
                    }
                }
            }
            .navigationTitle("Pipeline")
            .navigationBarTitleDisplayMode(.inline)
            .alert("Error", isPresented: Binding(
                get: { viewModel.errorMessage != nil },
                set: { if !$0 { viewModel.errorMessage = nil } }
            )) {
                Button("OK", role: .cancel) { viewModel.errorMessage = nil }
            } message: {
                Text(viewModel.errorMessage ?? "")
            }
        }
        .onAppear {
            Task { await viewModel.loadPipeline() }
        }
    }
}

// MARK: - Header

private struct PipelineHeader: View {
    let stats: PipelineStats
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.xs) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Pipeline")
                        .font(theme.typography.title)
                    Text("\(stats.total) candidates")
                        .font(theme.typography.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                if stats.pendingMoves > 0 {
                    Label("\(stats.pendingMoves) pending", systemImage: "network")
                        .font(theme.typography.chip)
                        .foregroundStyle(theme.colors.warning)
                }
            }
            .padding(theme.spacing.sm)

            // Stage progress indicators
            HStack(spacing: theme.spacing.xs) {
                StatPill("Screening", count: stats.screeningCount, color: theme.colors.info)
                StatPill("Interview", count: stats.interviewCount, color: theme.colors.warning)
                StatPill("Offer", count: stats.offerCount, color: theme.colors.accent)
                StatPill("Hired", count: stats.hiredCount, color: theme.colors.success)
            }
            .padding(.horizontal, theme.spacing.sm)
            .padding(.bottom, theme.spacing.sm)
        }
        .background(Color(.systemBackground))
    }
}

private struct StatPill: View {
    let label: String
    let count: Int
    let color: Color
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(spacing: 2) {
            Text("\(count)")
                .font(theme.typography.headline)
                .foregroundStyle(color)
            Text(label)
                .font(theme.typography.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, theme.spacing.xs)
        .background(color.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: theme.radii.sm))
    }
}

// MARK: - Column

private struct PipelineColumn: View {
    let stage: PipelineStage
    let cards: [PipelineCard]
    @ObservedObject var viewModel: RecruiterPipelineViewModel
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.xs) {
            HStack {
                Text(stage.rawValue.capitalized)
                    .font(theme.typography.headline)
                Spacer()
                Text("\(cards.count)")
                    .font(theme.typography.chip)
                    .foregroundStyle(.white)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(columnColor)
                    .clipShape(Capsule())
            }
            .padding(.horizontal, theme.spacing.xs)

            VStack(spacing: theme.spacing.xs) {
                ForEach(cards) { card in
                    PipelineCardView(
                        card: card,
                        stage: stage,
                        viewModel: viewModel,
                        theme: theme
                    )
                }

                if cards.isEmpty {
                    VStack(spacing: theme.spacing.xs) {
                        Image(systemName: "inbox.fill")
                            .font(.system(size: 20))
                            .foregroundStyle(.secondary.opacity(0.5))
                        Text("Empty")
                            .font(theme.typography.caption)
                            .foregroundStyle(.secondary)
                    }
                    .frame(height: 60)
                    .frame(maxWidth: .infinity)
                    .background(Color(.secondarySystemBackground))
                    .clipShape(RoundedRectangle(cornerRadius: theme.radii.md))
                }
            }
        }
        .frame(minWidth: 280)
    }

    private var columnColor: Color {
        switch stage {
        case .screening: return theme.colors.info
        case .interview: return theme.colors.warning
        case .offer: return theme.colors.accent
        case .hired: return theme.colors.success
        }
    }
}

// MARK: - Card

private struct PipelineCardView: View {
    let card: PipelineCard
    let stage: PipelineStage
    @ObservedObject var viewModel: RecruiterPipelineViewModel
    @Environment(\.trueMatchTheme) private var theme

    @State private var dragOffset = CGSize.zero
    @State private var isShowingDetails = false

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.xs) {
            HStack {
                if let url = URL(string: card.avatarUrl ?? "") {
                    AsyncImage(url: url) { phase in
                        switch phase {
                        case .success(let image):
                            image.resizable().scaledToFill()
                        default:
                            Image(systemName: "person.fill")
                        }
                    }
                    .frame(width: 32, height: 32)
                    .clipShape(Circle())
                } else {
                    Image(systemName: "person.fill")
                        .frame(width: 32, height: 32)
                        .background(Circle().fill(.secondary.opacity(0.2)))
                }

                VStack(alignment: .leading, spacing: 2) {
                    Text(card.name)
                        .font(theme.typography.headline)
                        .lineLimit(1)

                    ScoreIndicator(score: card.score, delta: card.delta, theme: theme)
                }

                Spacer()

                Button {
                    isShowingDetails = true
                } label: {
                    Image(systemName: "ellipsis")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundStyle(.secondary)
                }
                .accessibilityLabel("Options for \(card.name)")
            }

            if card.notesCount > 0 {
                Label("\(card.notesCount) notes", systemImage: "note.text")
                    .font(theme.typography.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .tmCard()
        .overlay {
            if card == viewModel.selectedCard {
                RoundedRectangle(cornerRadius: theme.radii.md)
                    .stroke(theme.colors.primary, lineWidth: 2)
            }
        }
        .onTapGesture {
            viewModel.selectCard(card)
        }
        .contextMenu {
            ForEach(availableTransitions, id: \.self) { nextStage in
                Button {
                    Task {
                        await viewModel.moveCard(card, from: stage, to: nextStage)
                    }
                } label: {
                    Label("Move to \(nextStage.rawValue.capitalized)", systemImage: "arrow.right")
                }
            }

            Divider()

            Button(role: .destructive) {
                // Archive action
            } label: {
                Label("Archive", systemImage: "archivebox")
            }
        }
    }

    private var availableTransitions: [PipelineStage] {
        switch stage {
        case .screening: return [.interview, .hired]
        case .interview: return [.offer, .screening]
        case .offer: return [.hired, .interview]
        case .hired: return []
        }
    }
}

// MARK: - Skeleton Loading

private struct SkeletonPipeline: View {
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        ScrollView(.horizontal) {
            HStack(spacing: theme.spacing.sm) {
                ForEach(0..<4, id: \.self) { _ in
                    VStack(spacing: theme.spacing.xs) {
                        RoundedRectangle(cornerRadius: theme.radii.sm)
                            .fill(.secondary.opacity(0.2))
                            .frame(height: 16)

                        ForEach(0..<3, id: \.self) { _ in
                            RoundedRectangle(cornerRadius: theme.radii.md)
                                .fill(.secondary.opacity(0.2))
                                .frame(height: 100)
                        }
                    }
                    .frame(minWidth: 280)
                }
            }
            .padding(theme.spacing.sm)
        }
    }
}

private struct ScoreIndicator: View {
    let score: Double
    let delta: Double?
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        HStack(spacing: 4) {
            Text("\(Int(score))")
                .font(theme.typography.chip)
                .foregroundStyle(scoreColor)

            if let delta = delta, delta != 0 {
                HStack(spacing: 2) {
                    Image(systemName: delta > 0 ? "triangle.fill" : "triangle.fill")
                        .font(.system(size: 8))
                    Text("\(Int(abs(delta)))")
                        .font(theme.typography.chip)
                }
                .foregroundStyle(delta > 0 ? theme.colors.deltaPositive : theme.colors.deltaNegative)
            }
        }
    }

    private var scoreColor: Color {
        if score >= 80 {
            return theme.colors.success
        } else if score >= 60 {
            return theme.colors.warning
        } else {
            return theme.colors.error
        }
    }
}

// MARK: - Preview

#Preview {
    RecruiterPipelineView()
}
