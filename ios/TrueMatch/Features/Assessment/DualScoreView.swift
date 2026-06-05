//
//  DualScoreView.swift
//  TrueMatch
//
//  Side-by-side traditional (ATS keyword) score and capability score, plus the
//  delta bar visualising the gap between them.
//

import SwiftUI

struct DualScoreView: View {
    let traditional: TraditionalScore
    let capability: CapabilityScore
    var delta: Double?

    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        TMCard(style: .elevated) {
            VStack(spacing: theme.spacing.md) {
                HStack(spacing: theme.spacing.xl) {
                    TMScoreGauge(
                        score: traditional.score,
                        label: "Traditional",
                        tint: theme.colors.traditional,
                        size: 120
                    )
                    TMScoreGauge(
                        score: capability.score,
                        label: "Capability",
                        tint: theme.colors.capability,
                        size: 120
                    )
                }
                .frame(maxWidth: .infinity)

                TMDeltaBar(
                    traditionalScore: traditional.score,
                    capabilityScore: capability.score
                )
            }
        }
    }
}

#Preview {
    DualScoreView(
        traditional: PreviewData.sampleAssessment.traditionalScore!,
        capability: PreviewData.sampleAssessment.capabilityScore!,
        delta: PreviewData.sampleAssessment.delta
    )
    .padding()
}
