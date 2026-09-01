//
//  GapAnalysisView.swift
//  TrueMatch
//
//  Shows the keyword gap (matched / missing) from the traditional score and the
//  job-description quality critique.
//

import SwiftUI

struct GapAnalysisView: View {
    let traditional: TraditionalScore
    var jdQuality: JDQuality?

    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(spacing: theme.spacing.sm) {
            keywordCard
            if let jdQuality {
                jdQualityCard(jdQuality)
            }
        }
    }

    private var keywordCard: some View {
        TMCard {
            VStack(alignment: .leading, spacing: theme.spacing.sm) {
                Text("Keyword gap")
                    .font(theme.typography.headline)
                    .foregroundStyle(Color.tmTextPrimary)

                if let explanation = traditional.explanation {
                    Text(explanation)
                        .font(theme.typography.caption)
                        .foregroundStyle(Color.tmTextSecondary)
                        .fixedSize(horizontal: false, vertical: true)
                }

                if !traditional.matchedKeywords.isEmpty {
                    keywordSection("Matched", traditional.matchedKeywords, kind: .success)
                }
                if !traditional.missingKeywords.isEmpty {
                    keywordSection("Missing", traditional.missingKeywords, kind: .error)
                }
            }
        }
    }

    private func keywordSection(_ title: String, _ keywords: [String], kind: TMBadgeKind) -> some View {
        VStack(alignment: .leading, spacing: theme.spacing.xxs) {
            Text(title)
                .font(theme.typography.chip)
                .foregroundStyle(Color.tmTextTertiary)
            FlowLayout(spacing: theme.spacing.xxs) {
                ForEach(keywords, id: \.self) { keyword in
                    TMBadge(text: keyword, kind: kind)
                }
            }
        }
    }

    private func jdQualityCard(_ jd: JDQuality) -> some View {
        TMCard {
            VStack(alignment: .leading, spacing: theme.spacing.xs) {
                HStack {
                    Text("Job description quality")
                        .font(theme.typography.headline)
                        .foregroundStyle(Color.tmTextPrimary)
                    Spacer()
                    Text("\(Int(jd.score.rounded()))/100")
                        .font(theme.typography.headline)
                        .foregroundStyle(qualityColor(jd.score))
                        .monospacedDigit()
                }

                if !jd.issues.isEmpty {
                    bulletList("Issues", jd.issues, icon: "exclamationmark.triangle", color: theme.colors.warning)
                }
                if !jd.recommendations.isEmpty {
                    bulletList("Recommendations", jd.recommendations, icon: "lightbulb", color: theme.colors.info)
                }
            }
        }
    }

    private func bulletList(_ title: String, _ items: [String], icon: String, color: Color) -> some View {
        VStack(alignment: .leading, spacing: theme.spacing.xxs) {
            Text(title)
                .font(theme.typography.chip)
                .foregroundStyle(Color.tmTextTertiary)
            ForEach(items, id: \.self) { item in
                HStack(alignment: .top, spacing: theme.spacing.xxs) {
                    Image(systemName: icon)
                        .font(.system(size: 12))
                        .foregroundStyle(color)
                        .padding(.top, 1)
                    Text(item)
                        .font(theme.typography.caption)
                        .foregroundStyle(Color.tmTextSecondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
    }

    private func qualityColor(_ score: Double) -> Color {
        if score >= 75 { return theme.colors.success }
        if score >= 50 { return theme.colors.warning }
        return theme.colors.error
    }
}

// MARK: - Simple Flow Layout

struct FlowLayout: Layout {
    var spacing: CGFloat = 8

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let maxWidth = proposal.width ?? .infinity
        var rows: [[CGSize]] = [[]]
        var x: CGFloat = 0
        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if x + size.width > maxWidth, !(rows.last?.isEmpty ?? true) {
                rows.append([])
                x = 0
            }
            rows[rows.count - 1].append(size)
            x += size.width + spacing
        }
        let height = rows.reduce(0) { acc, row in
            acc + (row.map(\.height).max() ?? 0) + spacing
        }
        return CGSize(width: maxWidth == .infinity ? x : maxWidth, height: max(height - spacing, 0))
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        var x = bounds.minX
        var y = bounds.minY
        var rowHeight: CGFloat = 0
        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if x + size.width > bounds.maxX, x > bounds.minX {
                x = bounds.minX
                y += rowHeight + spacing
                rowHeight = 0
            }
            subview.place(at: CGPoint(x: x, y: y), proposal: ProposedViewSize(size))
            x += size.width + spacing
            rowHeight = max(rowHeight, size.height)
        }
    }
}

#Preview {
    ScrollView {
        GapAnalysisView(
            traditional: PreviewData.sampleAssessment.traditionalScore!,
            jdQuality: PreviewData.sampleAssessment.jdQuality
        )
        .padding()
    }
}
