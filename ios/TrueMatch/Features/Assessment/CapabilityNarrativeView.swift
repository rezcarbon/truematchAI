//
//  CapabilityNarrativeView.swift
//  TrueMatch
//

import SwiftUI

struct CapabilityNarrativeView: View {
    let capability: CapabilityScore
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(spacing: theme.spacing.sm) {
            TMNarrativeBlock(
                title: "Capability narrative",
                systemImage: "sparkles",
                narrative: capability.narrative,
                evidence: capability.evidence,
                accent: theme.colors.capability
            )

            componentsCard
        }
    }

    private var componentsCard: some View {
        TMCard {
            VStack(alignment: .leading, spacing: theme.spacing.xs) {
                Text("Capability components")
                    .font(theme.typography.headline)
                    .foregroundStyle(Color.tmTextPrimary)

                component("Demonstrated capability", capability.components.demonstratedCapability)
                component("Domain depth", capability.components.domainDepth)
                component("Trajectory strength", capability.components.trajectoryStrength)
                component("Learning velocity", capability.components.learningVelocity)
                component("Leadership evidence", capability.components.leadershipEvidence)
            }
        }
    }

    private func component(_ label: String, _ value: Double) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(label)
                    .font(theme.typography.caption)
                    .foregroundStyle(Color.tmTextSecondary)
                Spacer()
                Text("\(Int((value * 100).rounded()))")
                    .font(theme.typography.chip)
                    .foregroundStyle(theme.colors.capability)
                    .monospacedDigit()
            }
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Capsule().fill(Color.gray.opacity(0.12)).frame(height: 6)
                    Capsule().fill(theme.colors.capability)
                        .frame(width: geo.size.width * min(max(value, 0), 1), height: 6)
                }
            }
            .frame(height: 6)
        }
    }
}

#Preview {
    ScrollView {
        CapabilityNarrativeView(capability: PreviewData.sampleAssessment.capabilityScore!)
            .padding()
    }
}
