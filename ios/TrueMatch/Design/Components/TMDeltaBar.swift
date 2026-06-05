//
//  TMDeltaBar.swift
//  TrueMatch
//
//  Horizontal bar that visualises the gap (delta) between the traditional
//  score and the capability score for a candidate.
//

import SwiftUI

struct TMDeltaBar: View {
    let traditionalScore: Double
    let capabilityScore: Double
    var height: CGFloat = 28

    @Environment(\.trueMatchTheme) private var theme

    private var delta: Double { capabilityScore - traditionalScore }
    private var deltaColor: Color {
        delta >= 0 ? theme.colors.deltaPositive : theme.colors.deltaNegative
    }

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.xxs) {
            HStack {
                Text("Capability vs. traditional")
                    .font(theme.typography.caption)
                    .foregroundStyle(Color.tmTextSecondary)
                Spacer()
                Text(deltaText)
                    .font(theme.typography.headline)
                    .foregroundStyle(deltaColor)
                    .monospacedDigit()
            }

            GeometryReader { geo in
                let width = geo.size.width
                let tradFrac = clamped(traditionalScore / 100)
                let capFrac = clamped(capabilityScore / 100)
                let lo = min(tradFrac, capFrac)
                let hi = max(tradFrac, capFrac)

                ZStack(alignment: .leading) {
                    Capsule()
                        .fill(Color.gray.opacity(0.12))
                        .frame(height: height)

                    // The delta span between the two scores.
                    Capsule()
                        .fill(deltaColor.opacity(0.25))
                        .frame(width: max((hi - lo) * width, 2), height: height)
                        .offset(x: lo * width)

                    marker(at: tradFrac * width, color: theme.colors.traditional, glyph: "doc.plaintext")
                    marker(at: capFrac * width, color: theme.colors.capability, glyph: "sparkles")
                }
            }
            .frame(height: height)

            HStack {
                legend(color: theme.colors.traditional, text: "Traditional \(Int(traditionalScore.rounded()))")
                Spacer()
                legend(color: theme.colors.capability, text: "Capability \(Int(capabilityScore.rounded()))")
            }
        }
    }

    private var deltaText: String {
        let sign = delta >= 0 ? "+" : ""
        return "\(sign)\(Int(delta.rounded())) pts"
    }

    private func clamped(_ v: Double) -> Double { min(max(v, 0), 1) }

    private func marker(at x: CGFloat, color: Color, glyph: String) -> some View {
        Image(systemName: glyph)
            .font(.system(size: height * 0.42, weight: .bold))
            .foregroundStyle(.white)
            .frame(width: height, height: height)
            .background(Circle().fill(color))
            .offset(x: min(max(x - height / 2, 0), 1_000_000))
    }

    private func legend(color: Color, text: String) -> some View {
        HStack(spacing: 4) {
            Circle().fill(color).frame(width: 8, height: 8)
            Text(text)
                .font(theme.typography.chip)
                .foregroundStyle(Color.tmTextSecondary)
        }
    }
}

#Preview {
    VStack(spacing: 32) {
        TMDeltaBar(traditionalScore: 42, capabilityScore: 87)
        TMDeltaBar(traditionalScore: 78, capabilityScore: 64)
    }
    .padding()
}
