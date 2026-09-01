//
//  TMScoreGauge.swift
//  TrueMatch
//
//  Circular gauge for rendering a 0–100 score. Used for both the traditional
//  (ATS keyword) score and the capability score on the dual-score view.
//

import SwiftUI

struct TMScoreGauge: View {
    /// Score on a 0–100 scale.
    let score: Double
    var label: String? = nil
    var tint: Color = TrueMatchTheme.accentColor
    var size: CGFloat = 140
    var lineWidth: CGFloat = 14

    @Environment(\.trueMatchTheme) private var theme
    @State private var animatedFraction: Double = 0

    private var fraction: Double { min(max(score / 100, 0), 1) }

    var body: some View {
        VStack(spacing: theme.spacing.xxs) {
            ZStack {
                Circle()
                    .stroke(tint.opacity(0.15), lineWidth: lineWidth)

                Circle()
                    .trim(from: 0, to: animatedFraction)
                    .stroke(
                        tint,
                        style: StrokeStyle(lineWidth: lineWidth, lineCap: .round)
                    )
                    .rotationEffect(.degrees(-90))

                VStack(spacing: 0) {
                    Text("\(Int(score.rounded()))")
                        .font(.system(size: size * 0.3, weight: .bold, design: .rounded))
                        .foregroundStyle(Color.tmTextPrimary)
                        .monospacedDigit()
                    Text("/ 100")
                        .font(theme.typography.chip)
                        .foregroundStyle(Color.tmTextTertiary)
                }
            }
            .frame(width: size, height: size)

            if let label {
                Text(label)
                    .font(theme.typography.caption)
                    .foregroundStyle(Color.tmTextSecondary)
            }
        }
        .onAppear {
            withAnimation(theme.animations.slow) {
                animatedFraction = fraction
            }
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(label ?? "Score")
        .accessibilityValue("\(Int(score.rounded())) out of 100")
    }
}

#Preview {
    HStack(spacing: 24) {
        TMScoreGauge(score: 42, label: "Traditional", tint: Color(hex: 0x718096))
        TMScoreGauge(score: 87, label: "Capability", tint: Color(hex: 0x4C51BF))
    }
    .padding()
}
