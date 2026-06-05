//
//  TMNarrativeBlock.swift
//  TrueMatch
//
//  Renders a titled narrative paragraph with an optional list of supporting
//  evidence points. Used for the capability narrative, trajectory narrative,
//  and counter-recommendation reasoning.
//

import SwiftUI

struct TMNarrativeBlock: View {
    let title: String
    var systemImage: String? = nil
    let narrative: String
    var evidence: [String] = []
    var accent: Color = TrueMatchTheme.accentColor

    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        TMCard {
            VStack(alignment: .leading, spacing: theme.spacing.xs) {
                HStack(spacing: theme.spacing.xxs) {
                    if let systemImage {
                        Image(systemName: systemImage)
                            .foregroundStyle(accent)
                    }
                    Text(title)
                        .font(theme.typography.headline)
                        .foregroundStyle(Color.tmTextPrimary)
                }

                Text(narrative)
                    .font(theme.typography.body)
                    .foregroundStyle(Color.tmTextSecondary)
                    .fixedSize(horizontal: false, vertical: true)

                if !evidence.isEmpty {
                    Divider()
                    VStack(alignment: .leading, spacing: theme.spacing.xxs) {
                        ForEach(Array(evidence.enumerated()), id: \.offset) { _, point in
                            HStack(alignment: .top, spacing: theme.spacing.xxs) {
                                Image(systemName: "checkmark.circle.fill")
                                    .font(.system(size: 13))
                                    .foregroundStyle(accent)
                                    .padding(.top, 1)
                                Text(point)
                                    .font(theme.typography.caption)
                                    .foregroundStyle(Color.tmTextSecondary)
                                    .fixedSize(horizontal: false, vertical: true)
                            }
                        }
                    }
                }
            }
        }
    }
}

#Preview {
    ScrollView {
        TMNarrativeBlock(
            title: "Capability narrative",
            systemImage: "sparkles",
            narrative: "The candidate demonstrates strong cross-domain delivery, repeatedly shipping ambiguous, high-ownership initiatives ahead of formal titles.",
            evidence: [
                "Led a 6-engineer migration with no prior platform title",
                "Self-taught the domain in under a quarter",
                "Mentored two peers who were later promoted"
            ]
        )
        .padding()
    }
}
