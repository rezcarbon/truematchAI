//
//  RecruiterSearchViewModel.swift
//  TrueMatch
//
//  Manages candidate search with name/skills/status filtering and debounced
//  API calls for efficient search.
//

import Foundation
import SwiftUI
import Combine

@MainActor
final class RecruiterSearchViewModel: ObservableObject {
    @Published var searchText: String = ""
    @Published var selectedStage: PipelineStage?
    @Published var scoreMin: Double = 0
    @Published var scoreMax: Double = 100

    @Published var results: [RecruiterSearchResult] = []
    @Published var isSearching = false
    @Published var hasSearched = false
    @Published var errorMessage: String?

    private let api = APIClient.shared
    private var cancellables = Set<AnyCancellable>()
    private var searchTask: Task<Void, Never>?

    // MARK: - Initialization

    init() {
        // Debounced search on text change
        $searchText
            .debounce(for: 0.5, scheduler: RunLoop.main)
            .sink { [weak self] _ in
                self?.searchTask?.cancel()
                self?.searchTask = Task {
                    await self?.performSearch()
                }
            }
            .store(in: &cancellables)
    }

    // MARK: - Search

    private func performSearch() async {
        guard !searchText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            results = []
            hasSearched = false
            return
        }

        isSearching = true
        defer { isSearching = false }
        hasSearched = true

        do {
            let request = SearchCandidatesRequest(
                query: searchText,
                stage: selectedStage?.rawValue,
                scoreMin: scoreMin,
                scoreMax: scoreMax,
                positionId: nil
            )

            let response = try await api.request(
                endpoint: .recruiterSearchCandidates(request),
                type: SearchResultsResponse.self
            )

            await MainActor.run {
                self.results = response.results
                self.errorMessage = nil
            }
        } catch {
            TrueMatchLogger.log(.error, "Recruiter: search failed: \(error)")
            await MainActor.run {
                self.errorMessage = error.localizedDescription
                self.results = []
            }
        }
    }

    /// Manually trigger search.
    func search() async {
        await performSearch()
    }

    /// Clear search results.
    func clearSearch() {
        searchText = ""
        results = []
        hasSearched = false
        selectedStage = nil
        scoreMin = 0
        scoreMax = 100
        errorMessage = nil
    }

    // MARK: - Filters

    func setStageFilter(_ stage: PipelineStage?) {
        selectedStage = stage
        searchTask?.cancel()
        searchTask = Task {
            await self.performSearch()
        }
    }

    func setScoreRange(min: Double, max: Double) {
        scoreMin = min
        scoreMax = max
        searchTask?.cancel()
        searchTask = Task {
            await self.performSearch()
        }
    }

    // MARK: - Quick Actions

    func quickActionTapped(_ action: String, for result: RecruiterSearchResult) async {
        switch action {
        case "review":
            TrueMatchLogger.log(.info, "Opening CV for \(result.name)")
        case "schedule":
            TrueMatchLogger.log(.info, "Scheduling interview for \(result.name)")
        case "send_offer":
            TrueMatchLogger.log(.info, "Preparing offer for \(result.name)")
        default:
            break
        }
    }
}
