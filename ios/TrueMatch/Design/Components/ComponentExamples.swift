//
//  ComponentExamples.swift
//  TrueMatch
//
//  Practical examples and integration patterns for the custom component library.
//  Demonstrates usage of TMSkillRadar, TMDecisionBadge, and offline queue integration.
//

import SwiftUI
import SwiftData

// MARK: - Full Decision Assessment View

struct DecisionAssessmentView: View {
    let candidateName: String
    let assessmentScore: Double
    let traditionalScore: Double
    let capabilityScore: Double
    let skillDimensions: [SkillDimension]
    let decision: TMDecision

    @Environment(\.trueMatchTheme) private var theme
    @Environment(\.modelContext) private var modelContext

    var body: some View {
        ScrollView {
            VStack(spacing: theme.spacing.lg) {
                // Header
                VStack(alignment: .leading, spacing: theme.spacing.xs) {
                    Text(candidateName)
                        .font(theme.typography.title)
                        .foregroundStyle(Color.tmTextPrimary)

                    Text("Assessment Results")
                        .font(theme.typography.caption)
                        .foregroundStyle(Color.tmTextSecondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(theme.spacing.sm)

                // Decision Badge
                TMDecisionBadge(
                    decision: decision,
                    size: .large,
                    showConfidence: true,
                    actionLabel: "View Details",
                    onAction: { /* handle */ }
                )
                .tmDecisionSurface()

                // Score Comparison
                VStack(spacing: theme.spacing.md) {
                    Text("Score Comparison")
                        .tmSectionHeader()

                    HStack(spacing: theme.spacing.lg) {
                        TMScoreGauge(
                            score: traditionalScore,
                            label: "Traditional",
                            tint: theme.colors.traditional,
                            size: 120
                        )

                        TMScoreGauge(
                            score: capabilityScore,
                            label: "Capability",
                            tint: theme.colors.capability,
                            size: 120
                        )
                    }
                    .frame(maxWidth: .infinity)

                    TMDeltaBar(
                        traditionalScore: traditionalScore,
                        capabilityScore: capabilityScore
                    )
                    .padding(theme.spacing.sm)
                }
                .tmDataVisualization()

                // Skill Assessment
                VStack(spacing: theme.spacing.md) {
                    Text("Skill Assessment")
                        .tmSectionHeader()

                    TMSkillRadar(
                        dimensions: skillDimensions,
                        size: 220,
                        showLegend: true,
                        showGrid: true,
                        gridLevels: 5
                    )
                }
                .tmDataVisualization()

                // Action Buttons
                VStack(spacing: theme.spacing.sm) {
                    Button(action: { /* accept */ }) {
                        Text("Accept Recommendation")
                            .font(theme.typography.headline)
                            .frame(maxWidth: .infinity)
                            .padding(theme.spacing.sm)
                            .background(theme.colors.success)
                            .foregroundStyle(.white)
                            .clipShape(RoundedRectangle(cornerRadius: theme.radii.md))
                    }

                    Button(action: { /* reject */ }) {
                        Text("Request Review")
                            .font(theme.typography.headline)
                            .frame(maxWidth: .infinity)
                            .padding(theme.spacing.sm)
                            .background(Color.gray.opacity(0.1))
                            .foregroundStyle(Color.tmTextPrimary)
                            .clipShape(RoundedRectangle(cornerRadius: theme.radii.md))
                    }
                }
                .padding(theme.spacing.sm)
            }
            .padding(theme.spacing.md)
        }
    }
}

// MARK: - Offline Queue Monitor View

struct OfflineQueueMonitorView: View {
    @StateObject private var queueManager = OfflineQueueManagerExtended.shared
    @Environment(\.trueMatchTheme) private var theme
    @Environment(\.modelContext) private var modelContext
    @State private var selectedItem: OfflineQueueItem?

    var body: some View {
        NavigationView {
            VStack(spacing: theme.spacing.md) {
                // Status Summary
                VStack(spacing: theme.spacing.sm) {
                    HStack {
                        Text("Sync Status")
                            .tmSectionHeader()
                        Spacer()
                        if queueManager.syncState?.isSyncing == true {
                            ProgressView()
                                .scaleEffect(0.8)
                        }
                    }

                    HStack(spacing: theme.spacing.md) {
                        StatusCard(
                            title: "Pending",
                            value: queueManager.pendingCount(in: modelContext),
                            color: theme.colors.info
                        )
                        StatusCard(
                            title: "Failed",
                            value: queueManager.failedCount(in: modelContext),
                            color: theme.colors.error
                        )
                        StatusCard(
                            title: "Conflicts",
                            value: queueManager.conflicts.count,
                            color: theme.colors.warning
                        )
                    }
                }
                .tmDataVisualization()

                // Queue Items List
                List {
                    Section("Queue Items") {
                        if queueManager.queueItems.isEmpty {
                            Text("No pending items")
                                .foregroundStyle(Color.tmTextSecondary)
                        } else {
                            ForEach(queueManager.queueItems) { item in
                                QueueItemRow(item: item, theme: theme)
                                    .onTapGesture {
                                        selectedItem = item
                                    }
                            }
                        }
                    }

                    if !queueManager.conflicts.isEmpty {
                        Section("Conflicts") {
                            ForEach(queueManager.conflicts) { conflict in
                                ConflictRow(conflict: conflict, theme: theme)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Offline Queue")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Menu {
                        Button("Sync Now") {
                            Task {
                                await queueManager.flush(in: modelContext)
                            }
                        }
                        Button("Retry Failed") {
                            Task {
                                await queueManager.retryFailed(in: modelContext)
                            }
                        }
                        Button("Cleanup") {
                            queueManager.removeCompleted(in: modelContext)
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
        }
        .onAppear {
            queueManager.fetchQueueItems(in: modelContext)
            queueManager.fetchConflicts(in: modelContext)
        }
    }
}

// MARK: - Helper Views

struct StatusCard: View {
    let title: String
    let value: Int
    let color: Color

    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(alignment: .center, spacing: theme.spacing.xs) {
            Text("\(value)")
                .font(.system(size: 24, weight: .bold, design: .rounded))
                .foregroundStyle(color)

            Text(title)
                .font(theme.typography.caption)
                .foregroundStyle(Color.tmTextSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(theme.spacing.sm)
        .background(color.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: theme.radii.sm))
    }
}

struct QueueItemRow: View {
    let item: OfflineQueueItem
    let theme: TrueMatchTheme

    var statusBadgeKind: TMBadgeKind {
        switch item.status {
        case .pending:
            return .info
        case .processing:
            return .info
        case .completed:
            return .success
        case .failed:
            return .error
        case .conflict:
            return .warning
        case .paused:
            return .neutral
        }
    }

    var body: some View {
        HStack(spacing: theme.spacing.sm) {
            VStack(alignment: .leading, spacing: theme.spacing.xxs) {
                Text(item.actionType)
                    .font(theme.typography.headline)
                    .foregroundStyle(Color.tmTextPrimary)

                if let resourceId = item.resourceId {
                    Text(resourceId)
                        .font(theme.typography.chip)
                        .foregroundStyle(Color.tmTextSecondary)
                }

                if let error = item.lastError {
                    Text(error)
                        .font(theme.typography.helper)
                        .foregroundStyle(theme.colors.error)
                        .lineLimit(1)
                }
            }

            Spacer()

            VStack(alignment: .trailing, spacing: theme.spacing.xxs) {
                TMBadge(
                    text: item.status.rawValue.capitalized,
                    kind: statusBadgeKind
                )

                if item.isRetryable {
                    Text("Retry \(item.retryCount)/\(item.maxRetries)")
                        .font(theme.typography.helper)
                        .foregroundStyle(Color.tmTextTertiary)
                }
            }
        }
        .padding(TMLayoutPattern.compactListPadding)
        .tmCompactList()
    }
}

struct ConflictRow: View {
    let conflict: SyncConflict
    let theme: TrueMatchTheme

    var body: some View {
        HStack(spacing: theme.spacing.sm) {
            VStack(alignment: .leading, spacing: theme.spacing.xxs) {
                Text(conflict.conflictType.rawValue)
                    .font(theme.typography.headline)
                    .foregroundStyle(Color.tmTextPrimary)

                Text(conflict.resolutionStrategy.rawValue)
                    .font(theme.typography.caption)
                    .foregroundStyle(Color.tmTextSecondary)
            }

            Spacer()

            VStack(alignment: .trailing, spacing: theme.spacing.xxs) {
                if conflict.isResolved {
                    TMBadge(text: "Resolved", kind: .success, icon: "checkmark")
                } else {
                    TMBadge(text: "Pending", kind: .warning, icon: "exclamationmark")
                }
            }
        }
        .padding(TMLayoutPattern.compactListPadding)
        .tmCompactList()
    }
}

// MARK: - Skill Radar Showcase

struct SkillRadarShowcaseView: View {
    @Environment(\.trueMatchTheme) private var theme

    let mockSkills = [
        SkillDimension(id: "python", label: "Python", value: 85, target: 80, category: .technical),
        SkillDimension(id: "swift", label: "Swift", value: 72, target: 90, category: .technical),
        SkillDimension(id: "architecture", label: "Architecture", value: 78, category: .technical),
        SkillDimension(id: "leadership", label: "Leadership", value: 88, category: .behavioral),
        SkillDimension(id: "communication", label: "Communication", value: 82, category: .behavioral),
        SkillDimension(id: "domain", label: "Domain Knowledge", value: 65, category: .domain),
    ]

    var body: some View {
        VStack(spacing: theme.spacing.lg) {
            Text("Skill Assessment")
                .font(theme.typography.title)
                .frame(maxWidth: .infinity, alignment: .leading)

            // Candidate's skill radar
            VStack(spacing: theme.spacing.md) {
                Text("Technical Readiness")
                    .font(theme.typography.headline)
                    .frame(maxWidth: .infinity, alignment: .leading)

                TMSkillRadar(
                    dimensions: mockSkills,
                    size: 240,
                    showLegend: true,
                    animationDuration: 0.6,
                    showGrid: true,
                    gridLevels: 5
                )
            }
            .tmDataVisualization()

            Spacer()
        }
        .padding(theme.spacing.md)
    }
}

// MARK: - Batch Assessment View

struct BatchAssessmentView: View {
    @StateObject private var queueManager = OfflineQueueManagerExtended.shared
    @Environment(\.trueMatchTheme) private var theme
    @Environment(\.modelContext) private var modelContext
    @State private var selectedBatch: BatchOperation?

    var body: some View {
        VStack(spacing: theme.spacing.lg) {
            Text("Batch Assessments")
                .tmSectionHeader()

            List {
                ForEach(queueManager.batchOperations) { batch in
                    VStack(alignment: .leading, spacing: theme.spacing.xs) {
                        HStack {
                            Text(batch.operationType)
                                .font(theme.typography.headline)
                                .foregroundStyle(Color.tmTextPrimary)

                            Spacer()

                            TMBadge(
                                text: batch.status.rawValue.capitalized,
                                kind: statusToBadgeKind(batch.status)
                            )
                        }

                        HStack(spacing: theme.spacing.sm) {
                            ProgressView(value: batch.percentComplete)
                                .frame(maxWidth: .infinity)

                            Text("\(Int(batch.percentComplete * 100))%")
                                .font(theme.typography.chip)
                                .foregroundStyle(Color.tmTextSecondary)
                                .monospacedDigit()
                        }

                        HStack(spacing: theme.spacing.md) {
                            Text("\(batch.completedItems) completed")
                                .font(theme.typography.chip)
                                .foregroundStyle(Color.tmTextSecondary)

                            Text("\(batch.failedItems) failed")
                                .font(theme.typography.chip)
                                .foregroundStyle(theme.colors.error)
                        }
                    }
                    .padding(theme.spacing.sm)
                }
            }
        }
    }
}

// MARK: - Helpers

func statusToBadgeKind(_ status: BatchOperation.BatchStatus) -> TMBadgeKind {
    switch status {
    case .pending:
        return .info
    case .inProgress:
        return .info
    case .completed:
        return .success
    case .partiallyCompleted:
        return .warning
    case .failed:
        return .error
    case .cancelled:
        return .neutral
    }
}

// MARK: - Preview

#Preview {
    let mockDecision = TMDecision.recommended(confidence: 92)
    let mockSkills = [
        SkillDimension(id: "python", label: "Python", value: 85, target: 80, category: .technical),
        SkillDimension(id: "swift", label: "Swift", value: 72, target: 90, category: .technical),
        SkillDimension(id: "leadership", label: "Leadership", value: 78, category: .behavioral),
        SkillDimension(id: "communication", label: "Communication", value: 88, category: .behavioral),
        SkillDimension(id: "domain", label: "Domain Knowledge", value: 65, category: .domain),
        SkillDimension(id: "analytics", label: "Analytics", value: 92, category: .domain),
    ]

    DecisionAssessmentView(
        candidateName: "Sarah Chen",
        assessmentScore: 87,
        traditionalScore: 42,
        capabilityScore: 87,
        skillDimensions: mockSkills,
        decision: mockDecision
    )
}
