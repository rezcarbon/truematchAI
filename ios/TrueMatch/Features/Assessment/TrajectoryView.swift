//
//  TrajectoryView.swift
//  TrueMatch
//

import SwiftUI

struct TrajectoryView: View {
    let trajectory: Trajectory
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(spacing: theme.spacing.sm) {
            TMCard {
                VStack(alignment: .leading, spacing: theme.spacing.xs) {
                    HStack(spacing: theme.spacing.xxs) {
                        Image(systemName: directionIcon)
                            .foregroundStyle(theme.colors.secondary)
                        Text("Trajectory")
                            .font(theme.typography.headline)
                            .foregroundStyle(Color.tmTextPrimary)
                        Spacer()
                        TMBadge(text: trajectory.direction.capitalized, kind: .info)
                    }

                    HStack(spacing: theme.spacing.lg) {
                        metric("Velocity", "\(Int((trajectory.velocity * 100).rounded()))")
                        metric("Domain crossings", "\(trajectory.domainCrossings)")
                    }

                    Text(trajectory.narrative)
                        .font(theme.typography.body)
                        .foregroundStyle(Color.tmTextSecondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }

            if !trajectory.invisibleCredentials.isEmpty {
                TMNarrativeBlock(
                    title: "Invisible credentials",
                    systemImage: "eye.slash",
                    narrative: "Strengths the resume's titles and keywords don't surface:",
                    evidence: trajectory.invisibleCredentials,
                    accent: theme.colors.secondary
                )
            }
        }
    }

    private var directionIcon: String {
        switch trajectory.direction.lowercased() {
        case "accelerating": return "chart.line.uptrend.xyaxis"
        case "declining": return "chart.line.downtrend.xyaxis"
        default: return "chart.line.flattrend.xyaxis"
        }
    }

    private func metric(_ label: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(value)
                .font(theme.typography.title)
                .foregroundStyle(theme.colors.secondary)
                .monospacedDigit()
            Text(label)
                .font(theme.typography.chip)
                .foregroundStyle(Color.tmTextSecondary)
        }
    }
}

#Preview {
    ScrollView {
        TrajectoryView(trajectory: PreviewData.sampleAssessment.trajectory!)
            .padding()
    }
}
