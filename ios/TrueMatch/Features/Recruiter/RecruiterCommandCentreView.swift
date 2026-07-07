//
//  RecruiterCommandCentreView.swift
//  TrueMatch
//
//  Command centre displays today's tasks, active positions carousel, candidate
//  work queue, and agent activity feed. Accessible via large touch targets and
//  full VoiceOver support.
//

import SwiftUI
import SwiftData

struct RecruiterCommandCentreView: View {
    @StateObject private var viewModel = RecruiterCommandCentreViewModel()
    @Environment(\.modelContext) private var modelContext
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: theme.spacing.md) {
                    // Header with refresh
                    HStack {
                        Text("Command Centre")
                            .font(theme.typography.title)
                        Spacer()
                        Button {
                            Task { await viewModel.refresh() }
                        } label: {
                            Image(systemName: "arrow.clockwise")
                                .font(.system(size: 16, weight: .semibold))
                        }
                        .disabled(viewModel.isRefreshing)
                    }
                    .padding(.horizontal, theme.spacing.sm)

                    if viewModel.isLoading && viewModel.tasks.isEmpty {
                        SkeletonCommandCentre()
                    } else {
                        // Today's Tasks
                        TasksSection(
                            tasks: viewModel.todaysTasks,
                            viewModel: viewModel
                        )

                        // Active Positions Carousel
                        PositionsCarousel(
                            positions: viewModel.positions,
                            theme: theme
                        )

                        // Candidate Queue
                        QueueSection(
                            items: viewModel.queueItems,
                            viewModel: viewModel,
                            theme: theme
                        )

                        // Agent Activity Feed
                        ActivityFeedSection(
                            entries: viewModel.recentActivity,
                            theme: theme
                        )
                    }
                }
                .padding(.vertical, theme.spacing.sm)
            }
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
            viewModel.setupContext(modelContext)
        }
    }
}

// MARK: - Tasks Section

private struct TasksSection: View {
    let tasks: [RecruiterTask]
    @ObservedObject var viewModel: RecruiterCommandCentreViewModel
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.xs) {
            Text("Today's Tasks")
                .tmSectionHeader()
                .padding(.horizontal, theme.spacing.sm)

            if tasks.isEmpty {
                VStack(spacing: theme.spacing.xs) {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 28))
                        .foregroundStyle(theme.colors.success)
                    Text("All caught up!")
                        .font(theme.typography.body)
                    Text("No tasks due today")
                        .font(theme.typography.caption)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity)
                .padding(theme.spacing.md)
                .background(theme.colors.success.opacity(0.08))
                .clipShape(RoundedRectangle(cornerRadius: theme.radii.md))
                .padding(.horizontal, theme.spacing.sm)
            } else {
                VStack(spacing: theme.spacing.xs) {
                    ForEach(tasks.prefix(3)) { task in
                        TaskCard(task: task, viewModel: viewModel, theme: theme)
                    }
                }
                .padding(.horizontal, theme.spacing.sm)
            }
        }
    }
}

private struct TaskCard: View {
    let task: RecruiterTask
    @ObservedObject var viewModel: RecruiterCommandCentreViewModel
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.xs) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(task.type.rawValue.capitalized)
                        .font(theme.typography.chip)
                        .foregroundStyle(.white)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(taskColor)
                        .clipShape(Capsule())

                    Text(task.candidateName)
                        .font(theme.typography.headline)

                    Text(task.positionTitle)
                        .font(theme.typography.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                Button {
                    Task { await viewModel.completeTask(task.id) }
                } label: {
                    Image(systemName: "checkmark.circle")
                        .font(.system(size: 24))
                        .foregroundStyle(theme.colors.primary)
                }
                .accessibilityLabel("Complete task: \(task.candidateName)")
            }
        }
        .tmCard()
    }

    private var taskColor: Color {
        switch task.type {
        case .approval: return theme.colors.info
        case .interview: return theme.colors.warning
        case .offer: return theme.colors.success
        }
    }
}

// MARK: - Positions Carousel

private struct PositionsCarousel: View {
    let positions: [ActivePosition]
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.xs) {
            Text("Active Positions")
                .tmSectionHeader()
                .padding(.horizontal, theme.spacing.sm)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: theme.spacing.sm) {
                    ForEach(positions) { position in
                        PositionCard(position: position, theme: theme)
                    }
                }
                .padding(.horizontal, theme.spacing.sm)
            }
        }
    }
}

private struct PositionCard: View {
    let position: ActivePosition
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.xs) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(position.title)
                        .font(theme.typography.headline)
                        .lineLimit(1)

                    if let dept = position.department {
                        Text(dept)
                            .font(theme.typography.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                Spacer()
                UrgencyBadge(urgency: position.urgency, theme: theme)
            }

            Divider()

            HStack(spacing: theme.spacing.md) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("\(position.openCount)")
                        .font(theme.typography.headline)
                        .foregroundStyle(theme.colors.primary)
                    Text("Open")
                        .font(theme.typography.caption)
                        .foregroundStyle(.secondary)
                }

                ProgressView(value: position.fillRate)
                    .frame(height: 4)

                VStack(alignment: .trailing, spacing: 2) {
                    Text("\(Int(position.fillRate * 100))%")
                        .font(theme.typography.headline)
                    Text("Filled")
                        .font(theme.typography.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .tmCard()
        .frame(minWidth: 240)
    }
}

private struct UrgencyBadge: View {
    let urgency: ActivePosition.Urgency
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        Label(urgency.rawValue.capitalized, systemImage: urgencyIcon)
            .font(theme.typography.chip)
            .foregroundStyle(.white)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(urgencyColor)
            .clipShape(Capsule())
    }

    private var urgencyColor: Color {
        switch urgency {
        case .critical: return theme.colors.error
        case .high: return theme.colors.warning
        case .normal: return theme.colors.info
        case .low: return .gray
        }
    }

    private var urgencyIcon: String {
        switch urgency {
        case .critical: return "exclamationmark.circle.fill"
        case .high: return "exclamationmark.triangle.fill"
        case .normal: return "circle.fill"
        case .low: return "circle"
        }
    }
}

// MARK: - Queue Section

private struct QueueSection: View {
    let items: [CandidateQueueItem]
    @ObservedObject var viewModel: RecruiterCommandCentreViewModel
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.xs) {
            Text("Work Queue")
                .tmSectionHeader()
                .padding(.horizontal, theme.spacing.sm)

            VStack(spacing: theme.spacing.xs) {
                ForEach(items.prefix(5)) { item in
                    QueueItemCard(item: item, viewModel: viewModel, theme: theme)
                }
            }
            .padding(.horizontal, theme.spacing.sm)

            if items.count > 5 {
                NavigationLink(destination: RecruiterTabView(selectedTab: 1)) {
                    Text("View All (\(items.count))")
                        .font(theme.typography.headline)
                        .frame(maxWidth: .infinity, alignment: .center)
                        .padding(theme.spacing.sm)
                }
                .padding(.horizontal, theme.spacing.sm)
            }
        }
    }
}

private struct QueueItemCard: View {
    let item: CandidateQueueItem
    @ObservedObject var viewModel: RecruiterCommandCentreViewModel
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        HStack(spacing: theme.spacing.sm) {
            if let url = URL(string: item.avatarUrl ?? "") {
                AsyncImage(url: url) { phase in
                    switch phase {
                    case .success(let image):
                        image.resizable().scaledToFill()
                    default:
                        Image(systemName: "person.fill")
                            .foregroundStyle(.secondary)
                    }
                }
                .frame(width: 44, height: 44)
                .clipShape(Circle())
            } else {
                Image(systemName: "person.fill")
                    .frame(width: 44, height: 44)
                    .background(Circle().fill(.secondary.opacity(0.2)))
            }

            VStack(alignment: .leading, spacing: 2) {
                Text(item.name)
                    .font(theme.typography.headline)
                HStack(spacing: theme.spacing.xs) {
                    ScoreIndicator(score: item.score, delta: item.delta, theme: theme)
                    Text(item.stage.rawValue.capitalized)
                        .font(theme.typography.caption)
                        .foregroundStyle(.secondary)
                }
            }

            Spacer()

            Button {
                Task { await viewModel.advanceCandidate(item.candidateId) }
            } label: {
                Image(systemName: "arrow.right.circle.fill")
                    .font(.system(size: 22))
                    .foregroundStyle(theme.colors.primary)
            }
            .accessibilityLabel("Advance \(item.name)")
        }
        .tmCard()
    }
}

// MARK: - Score Indicator

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

// MARK: - Activity Feed Section

private struct ActivityFeedSection: View {
    let entries: [AgentActivityEntry]
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.xs) {
            Text("Activity Feed")
                .tmSectionHeader()
                .padding(.horizontal, theme.spacing.sm)

            VStack(alignment: .leading, spacing: theme.spacing.xs) {
                ForEach(entries.prefix(5)) { entry in
                    ActivityEntryView(entry: entry, theme: theme)
                }
            }
            .padding(.horizontal, theme.spacing.sm)
        }
    }
}

private struct ActivityEntryView: View {
    let entry: AgentActivityEntry
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        HStack(spacing: theme.spacing.sm) {
            Circle()
                .fill(statusColor)
                .frame(width: 8, height: 8)

            VStack(alignment: .leading, spacing: 2) {
                Text("\(entry.agentName): \(entry.action)")
                    .font(theme.typography.body)

                HStack {
                    Text(entry.candidateName)
                        .font(theme.typography.caption)
                        .foregroundStyle(.secondary)
                    Text("•")
                    Text(entry.timestamp.formatted(date: .omitted, time: .shortened))
                        .font(theme.typography.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(theme.spacing.xs)
    }

    private var statusColor: Color {
        switch entry.status {
        case .success: return .green
        case .pending: return .orange
        case .failed: return .red
        }
    }
}

// MARK: - Skeleton Loading State

private struct SkeletonCommandCentre: View {
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(spacing: theme.spacing.md) {
            ForEach(0..<3, id: \.self) { _ in
                RoundedRectangle(cornerRadius: theme.radii.md)
                    .fill(.secondary.opacity(0.2))
                    .frame(height: 80)
            }
        }
        .padding(.horizontal, theme.spacing.sm)
    }
}

// MARK: - Preview

#Preview {
    RecruiterCommandCentreView()
}
