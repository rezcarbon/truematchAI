//
//  HistoryView.swift
//  TrueMatch
//
//  Lists past assessments. Skeleton: reads cached assessments from SwiftData and
//  falls back to preview data for development.
//

import SwiftUI
import SwiftData

struct HistoryView: View {
    @Environment(\.trueMatchTheme) private var theme
    @Query(sort: \CachedAssessment.createdAt, order: .reverse) private var cached: [CachedAssessment]

    var body: some View {
        NavigationStack {
            Group {
                if cached.isEmpty {
                    previewList
                } else {
                    cachedList
                }
            }
            .navigationTitle("History")
        }
    }

    private var cachedList: some View {
        List(cached) { item in
            NavigationLink {
                AssessmentResultView(assessmentId: item.id)
            } label: {
                row(title: item.positionTitle ?? "Assessment",
                    traditional: item.traditionalScore,
                    capability: item.capabilityScore,
                    counter: item.counterRecommended,
                    date: item.createdAt)
            }
        }
    }

    private var previewList: some View {
        List(PreviewData.assessmentList) { item in
            NavigationLink {
                AssessmentResultView(assessmentId: item.id, usePreview: true)
            } label: {
                row(title: "Candidate \(item.id.suffix(4))",
                    traditional: item.traditionalScore?.score,
                    capability: item.capabilityScore?.score,
                    counter: item.counterRecommendation?.triggered ?? false,
                    date: item.createdAt ?? .now)
            }
        }
    }

    private func row(title: String, traditional: Double?, capability: Double?, counter: Bool, date: Date) -> some View {
        VStack(alignment: .leading, spacing: theme.spacing.xxs) {
            HStack {
                Text(title)
                    .font(theme.typography.headline)
                Spacer()
                if counter {
                    TMBadge(text: "Counter-rec", kind: .warning, icon: "arrow.uturn.up")
                }
            }
            HStack(spacing: theme.spacing.sm) {
                if let traditional {
                    Label("\(Int(traditional))", systemImage: "doc.plaintext")
                        .font(theme.typography.caption)
                        .foregroundStyle(theme.colors.traditional)
                }
                if let capability {
                    Label("\(Int(capability))", systemImage: "sparkles")
                        .font(theme.typography.caption)
                        .foregroundStyle(theme.colors.capability)
                }
                Spacer()
                Text(date.shortTimestamp)
                    .font(theme.typography.chip)
                    .foregroundStyle(Color.tmTextTertiary)
            }
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    HistoryView()
}
