//
//  JobMatchingView.swift
//  TrueMatch
//
//  Skeleton: lists open positions a candidate can be matched against.
//

import SwiftUI

struct JobMatchingView: View {
    @Environment(\.trueMatchTheme) private var theme
    @State private var positions: [PositionResponse] = [PreviewData.samplePosition]

    var body: some View {
        NavigationStack {
            List(positions) { position in
                TMCard {
                    VStack(alignment: .leading, spacing: theme.spacing.xxs) {
                        Text(position.title)
                            .font(theme.typography.headline)
                            .foregroundStyle(Color.tmTextPrimary)
                        if let dept = position.department {
                            Text(dept)
                                .font(theme.typography.caption)
                                .foregroundStyle(Color.tmTextSecondary)
                        }
                        Text(position.jobDescription)
                            .font(theme.typography.caption)
                            .foregroundStyle(Color.tmTextTertiary)
                            .lineLimit(2)
                    }
                }
                .listRowSeparator(.hidden)
                .listRowBackground(Color.clear)
            }
            .listStyle(.plain)
            .navigationTitle("Positions")
            .task { await load() }
        }
    }

    private func load() async {
        do {
            let result = try await APIClient.shared.request(
                endpoint: .listPositions,
                type: [PositionResponse].self
            )
            positions = result
        } catch {
            TrueMatchLogger.log(.warning, "Falling back to preview positions: \(error.localizedDescription)")
        }
    }
}

#Preview {
    JobMatchingView()
}
