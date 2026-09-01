//
//  RecruiterCandidateSearchView.swift
//  TrueMatch
//
//  Candidate search with name/skills/status filtering, results list, and
//  quick action buttons for reviewing, scheduling, and sending offers.
//

import SwiftUI

struct RecruiterCandidateSearchView: View {
    @StateObject private var viewModel = RecruiterSearchViewModel()
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Search bar
                SearchBar(text: $viewModel.searchText, theme: theme)
                    .padding(theme.spacing.sm)

                if viewModel.hasSearched {
                    if viewModel.isSearching {
                        VStack {
                            ProgressView()
                                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .center)
                        }
                    } else if viewModel.results.isEmpty {
                        EmptySearchState(theme: theme)
                    } else {
                        // Results
                        ScrollView {
                            VStack(spacing: theme.spacing.xs) {
                                ForEach(viewModel.results) { result in
                                    SearchResultCard(
                                        result: result,
                                        viewModel: viewModel,
                                        theme: theme
                                    )
                                }
                            }
                            .padding(theme.spacing.sm)
                        }
                    }
                } else {
                    // Empty state before search
                    VStack(spacing: theme.spacing.md) {
                        Image(systemName: "magnifyingglass")
                            .font(.system(size: 40))
                            .foregroundStyle(.secondary)
                        Text("Search Candidates")
                            .font(theme.typography.title)
                        Text("Find candidates by name, skills, or status")
                            .font(theme.typography.body)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .center)
                }

                // Filter bar (collapsible)
                FilterBar(viewModel: viewModel, theme: theme)
            }
            .navigationTitle("Candidate Search")
            .navigationBarTitleDisplayMode(.inline)
            .alert("Error", isPresented: Binding(
                get: { viewModel.errorMessage != nil },
                set: { if !$0 { viewModel.errorMessage = nil } }
            )) {
                Button("OK", role: .cancel) { viewModel.errorMessage = nil }
            } message: {
                Text(viewModel.errorMessage ?? "")
            }
        }
    }
}

// MARK: - Search Bar

private struct SearchBar: View {
    @Binding var text: String
    @Environment(\.trueMatchTheme) private var theme
    @FocusState private var isFocused: Bool

    var body: some View {
        HStack(spacing: theme.spacing.xs) {
            Image(systemName: "magnifyingglass")
                .foregroundStyle(.secondary)

            TextField("Search by name, skills...", text: $text, axis: .vertical)
                .lineLimit(1...2)
                .focused($isFocused)

            if !text.isEmpty {
                Button {
                    text = ""
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(.secondary)
                }
            }
        }
        .padding(.horizontal, theme.spacing.sm)
        .padding(.vertical, theme.spacing.xs)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: theme.radii.lg))
    }
}

// MARK: - Filter Bar

private struct FilterBar: View {
    @ObservedObject var viewModel: RecruiterSearchViewModel
    @Environment(\.trueMatchTheme) private var theme
    @State private var showFilters = false

    var body: some View {
        VStack(spacing: theme.spacing.xs) {
            Button {
                showFilters.toggle()
            } label: {
                HStack {
                    Image(systemName: "slider.horizontal.3")
                    Text("Filters")
                    Spacer()
                    Image(systemName: showFilters ? "chevron.up" : "chevron.down")
                }
                .font(theme.typography.body)
                .foregroundStyle(.primary)
                .padding(theme.spacing.sm)
                .frame(maxWidth: .infinity, alignment: .leading)
            }

            if showFilters {
                Divider()
                    .padding(.horizontal, theme.spacing.sm)

                VStack(spacing: theme.spacing.sm) {
                    // Stage filter
                    VStack(alignment: .leading, spacing: theme.spacing.xs) {
                        Text("Pipeline Stage")
                            .font(theme.typography.headline)

                        HStack(spacing: theme.spacing.xs) {
                            Button {
                                viewModel.setStageFilter(nil)
                            } label: {
                                Text("All")
                                    .font(theme.typography.chip)
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 6)
                                    .background(
                                        viewModel.selectedStage == nil
                                            ? theme.colors.primary
                                            : Color(.secondarySystemBackground)
                                    )
                                    .foregroundStyle(
                                        viewModel.selectedStage == nil ? .white : .primary
                                    )
                                    .clipShape(Capsule())
                            }

                            ForEach(PipelineStage.allCases, id: \.self) { stage in
                                Button {
                                    viewModel.setStageFilter(stage)
                                } label: {
                                    Text(stage.rawValue.capitalized)
                                        .font(theme.typography.chip)
                                        .padding(.horizontal, 12)
                                        .padding(.vertical, 6)
                                        .background(
                                            viewModel.selectedStage == stage
                                                ? theme.colors.primary
                                                : Color(.secondarySystemBackground)
                                        )
                                        .foregroundStyle(
                                            viewModel.selectedStage == stage ? .white : .primary
                                        )
                                        .clipShape(Capsule())
                                }
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    // Score range filter
                    VStack(alignment: .leading, spacing: theme.spacing.xs) {
                        Text("Score Range")
                            .font(theme.typography.headline)

                        HStack(spacing: theme.spacing.xs) {
                            Text("Min: \(Int(viewModel.scoreMin))")
                                .font(theme.typography.caption)

                            Slider(
                                value: $viewModel.scoreMin,
                                in: 0...100
                            )
                            .onChange(of: viewModel.scoreMin) { _, _ in
                                Task {
                                    await viewModel.search()
                                }
                            }
                        }

                        HStack(spacing: theme.spacing.xs) {
                            Text("Max: \(Int(viewModel.scoreMax))")
                                .font(theme.typography.caption)

                            Slider(
                                value: $viewModel.scoreMax,
                                in: 0...100
                            )
                            .onChange(of: viewModel.scoreMax) { _, _ in
                                Task {
                                    await viewModel.search()
                                }
                            }
                        }
                    }

                    // Clear filters button
                    Button {
                        viewModel.clearSearch()
                    } label: {
                        Label("Clear All", systemImage: "xmark.circle")
                            .frame(maxWidth: .infinity)
                            .padding(theme.spacing.xs)
                    }
                    .buttonStyle(TMButtonStyle(tint: theme.colors.error))
                }
                .padding(theme.spacing.sm)
            }
        }
        .background(Color(.systemBackground))
        .border(Color(.separator), width: 1)
    }
}

// MARK: - Empty State

private struct EmptySearchState: View {
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(spacing: theme.spacing.md) {
            Image(systemName: "binoculars")
                .font(.system(size: 40))
                .foregroundStyle(.secondary)
            Text("No Results")
                .font(theme.typography.title)
            Text("Try adjusting your search or filters")
                .font(theme.typography.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .center)
    }
}

// MARK: - Search Result Card

private struct SearchResultCard: View {
    let result: RecruiterSearchResult
    @ObservedObject var viewModel: RecruiterSearchViewModel
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.sm) {
            // Header
            HStack(spacing: theme.spacing.sm) {
                if let url = URL(string: result.avatarUrl ?? "") {
                    AsyncImage(url: url) { phase in
                        switch phase {
                        case .success(let image):
                            image.resizable().scaledToFill()
                        default:
                            Image(systemName: "person.fill")
                        }
                    }
                    .frame(width: 48, height: 48)
                    .clipShape(Circle())
                } else {
                    Image(systemName: "person.fill")
                        .frame(width: 48, height: 48)
                        .background(Circle().fill(.secondary.opacity(0.2)))
                }

                VStack(alignment: .leading, spacing: 2) {
                    Text(result.name)
                        .font(theme.typography.headline)

                    if let email = result.email {
                        Text(email)
                            .font(theme.typography.caption)
                            .foregroundStyle(.secondary)
                    }

                    HStack(spacing: theme.spacing.xs) {
                        Label(
                            result.stage.rawValue.capitalized,
                            systemImage: "circle.fill"
                        )
                        .font(theme.typography.chip)
                        .foregroundStyle(stageColor)

                        Text("•")

                        Text("\(Int(result.matchPercentage))% match")
                            .font(theme.typography.chip)
                            .foregroundStyle(theme.colors.capability)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                ScoreIndicator(score: result.score, theme: theme)
            }

            // Position
            HStack(spacing: theme.spacing.xs) {
                Image(systemName: "briefcase.fill")
                    .font(.system(size: 12))
                    .foregroundStyle(.secondary)
                Text(result.positionTitle)
                    .font(theme.typography.caption)
                    .foregroundStyle(.secondary)
            }

            // Quick Actions
            HStack(spacing: theme.spacing.xs) {
                Button {
                    Task { await viewModel.quickActionTapped("review", for: result) }
                } label: {
                    Label("Review", systemImage: "doc.text")
                        .font(theme.typography.chip)
                        .frame(maxWidth: .infinity)
                        .padding(theme.spacing.xs)
                        .background(theme.colors.primary.opacity(0.1))
                        .foregroundStyle(theme.colors.primary)
                        .clipShape(RoundedRectangle(cornerRadius: theme.radii.sm))
                }

                Button {
                    Task { await viewModel.quickActionTapped("schedule", for: result) }
                } label: {
                    Label("Interview", systemImage: "calendar")
                        .font(theme.typography.chip)
                        .frame(maxWidth: .infinity)
                        .padding(theme.spacing.xs)
                        .background(theme.colors.warning.opacity(0.1))
                        .foregroundStyle(theme.colors.warning)
                        .clipShape(RoundedRectangle(cornerRadius: theme.radii.sm))
                }

                Button {
                    Task { await viewModel.quickActionTapped("send_offer", for: result) }
                } label: {
                    Label("Offer", systemImage: "star.fill")
                        .font(theme.typography.chip)
                        .frame(maxWidth: .infinity)
                        .padding(theme.spacing.xs)
                        .background(theme.colors.success.opacity(0.1))
                        .foregroundStyle(theme.colors.success)
                        .clipShape(RoundedRectangle(cornerRadius: theme.radii.sm))
                }
            }
        }
        .tmCard()
    }

    private var stageColor: Color {
        switch result.stage {
        case .screening: return theme.colors.info
        case .interview: return theme.colors.warning
        case .offer: return theme.colors.accent
        case .hired: return theme.colors.success
        }
    }
}

private struct ScoreIndicator: View {
    let score: Double
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(spacing: 2) {
            Text("\(Int(score))")
                .font(theme.typography.headline)
                .foregroundStyle(scoreColor)

            Text("Score")
                .font(theme.typography.caption)
                .foregroundStyle(.secondary)
        }
    }

    private var scoreColor: Color {
        if score >= 80 {
            return theme.colors.success
        } else if score >= 60 {
            return theme.colors.warning
        } else {
            return theme.colors.error
        }
    }
}

// MARK: - Preview

#Preview {
    RecruiterCandidateSearchView()
}
