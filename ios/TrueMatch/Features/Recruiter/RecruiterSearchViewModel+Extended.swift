//
//  RecruiterSearchViewModel+Extended.swift
//  TrueMatch
//
//  Advanced search features: saved searches, search history, smart filters.
//

import Foundation
import SwiftUI
import Combine

extension RecruiterSearchViewModel {

    // MARK: - Search History

    @Published private(set) var searchHistory: [SearchHistory] = []

    /// Add to search history.
    func saveSearchHistory() {
        let entry = SearchHistory(
            query: searchText,
            stage: selectedStage?.rawValue,
            scoreRange: (scoreMin, scoreMax),
            timestamp: Date(),
            resultCount: results.count
        )
        searchHistory.insert(entry, at: 0)

        // Keep only last 20 searches
        if searchHistory.count > 20 {
            searchHistory.removeLast()
        }
    }

    /// Clear search history.
    func clearSearchHistory() {
        searchHistory.removeAll()
    }

    /// Restore a previous search.
    func restoreSearch(_ history: SearchHistory) async {
        searchText = history.query
        selectedStage = history.stage.flatMap { PipelineStage(rawValue: $0) }
        scoreMin = history.scoreRange.min
        scoreMax = history.scoreRange.max
        await performSearch()
    }

    // MARK: - Advanced Filtering

    /// Apply multiple filters at once.
    func applyFilters(
        stage: PipelineStage? = nil,
        scoreMin: Double? = nil,
        scoreMax: Double? = nil,
        matchThreshold: Double? = nil
    ) async {
        if let stage = stage {
            selectedStage = stage
        }
        if let scoreMin = scoreMin {
            self.scoreMin = scoreMin
        }
        if let scoreMax = scoreMax {
            self.scoreMax = scoreMax
        }

        // Filter results by match percentage if provided
        if let threshold = matchThreshold {
            results = results.filter { $0.matchPercentage >= threshold }
        }

        await performSearch()
    }

    /// Reset all filters.
    func resetAllFilters() async {
        selectedStage = nil
        scoreMin = 0
        scoreMax = 100
        await performSearch()
    }

    // MARK: - Saved Searches

    struct SavedSearch: Identifiable, Codable {
        let id: String
        let name: String
        let query: String?
        let stage: String?
        let scoreMin: Double
        let scoreMax: Double
        let createdAt: Date

        init(
            name: String,
            query: String? = nil,
            stage: String? = nil,
            scoreMin: Double = 0,
            scoreMax: Double = 100
        ) {
            self.id = UUID().uuidString
            self.name = name
            self.query = query
            self.stage = stage
            self.scoreMin = scoreMin
            self.scoreMax = scoreMax
            self.createdAt = Date()
        }
    }

    @Published private(set) var savedSearches: [SavedSearch] = []

    /// Save current search criteria.
    func saveCurrentSearch(as name: String) {
        let saved = SavedSearch(
            name: name,
            query: searchText,
            stage: selectedStage?.rawValue,
            scoreMin: scoreMin,
            scoreMax: scoreMax
        )
        savedSearches.append(saved)
    }

    /// Load a saved search.
    func loadSavedSearch(_ search: SavedSearch) async {
        searchText = search.query ?? ""
        selectedStage = search.stage.flatMap { PipelineStage(rawValue: $0) }
        scoreMin = search.scoreMin
        scoreMax = search.scoreMax
        await performSearch()
    }

    /// Delete a saved search.
    func deleteSavedSearch(_ search: SavedSearch) {
        savedSearches.removeAll { $0.id == search.id }
    }

    // MARK: - Result Sorting

    enum SearchResultSortOption: String, CaseIterable {
        case relevance = "Relevance"
        case scoreHighToLow = "Score (High to Low)"
        case scoreLowToHigh = "Score (Low to High)"
        case matchPercentage = "Match %"
        case recentlyAdded = "Recently Added"
    }

    @Published var sortOption: SearchResultSortOption = .relevance

    /// Sort results.
    func sortResults(_ option: SearchResultSortOption) {
        sortOption = option
        switch option {
        case .relevance:
            results.sort { ($0.name.levenshteinDistance(to: searchText)) < ($1.name.levenshteinDistance(to: searchText)) }
        case .scoreHighToLow:
            results.sort { $0.score > $1.score }
        case .scoreLowToHigh:
            results.sort { $0.score < $1.score }
        case .matchPercentage:
            results.sort { $0.matchPercentage > $1.matchPercentage }
        case .recentlyAdded:
            // Would require timestamp in model
            break
        }
    }

    // MARK: - Pagination

    @Published private(set) var currentPage: Int = 1
    @Published private(set) var hasMoreResults: Bool = false
    private var searchCursor: String?

    /// Load next page of results.
    func loadMoreResults() async {
        // This would use cursor-based pagination
        // Placeholder for future implementation
    }

    // MARK: - Batch Operations on Results

    /// Apply action to selected results.
    func applyActionToResults(
        action: String,
        selectedIndices: [Int]
    ) async {
        for index in selectedIndices {
            guard index < results.count else { continue }
            let result = results[index]

            switch action {
            case "approve":
                TrueMatchLogger.log(.info, "Approving \(result.name)")
            case "reject":
                TrueMatchLogger.log(.info, "Rejecting \(result.name)")
            case "send_offer":
                TrueMatchLogger.log(.info, "Sending offer to \(result.name)")
            default:
                break
            }
        }
    }

    // MARK: - Favorites/Starred Results

    @Published private(set) var favoriteResults: Set<String> = []

    func toggleFavorite(_ resultId: String) {
        if favoriteResults.contains(resultId) {
            favoriteResults.remove(resultId)
        } else {
            favoriteResults.insert(resultId)
        }
    }

    func isFavorited(_ resultId: String) -> Bool {
        favoriteResults.contains(resultId)
    }

    func getFavoritedResults() -> [RecruiterSearchResult] {
        results.filter { favoriteResults.contains($0.id) }
    }
}

// MARK: - Search History Model

struct SearchHistory: Identifiable, Codable {
    let id: String = UUID().uuidString
    let query: String
    let stage: String?
    let scoreRange: (min: Double, max: Double)
    let timestamp: Date
    let resultCount: Int
}

// MARK: - Helper Extension

extension String {
    /// Calculate Levenshtein distance for fuzzy matching.
    func levenshteinDistance(to other: String) -> Int {
        let from = Array(self)
        let to = Array(other)

        var costs = Array(0...to.count)

        for i in 1...from.count {
            costs[0] = i
            var lastValue = i - 1

            for j in 1...to.count {
                let newValue = costs[j] + (from[i - 1] == to[j - 1] ? 0 : 1)
                costs[j] = min(costs[j] + 1, newValue, lastValue + 1)
                lastValue = newValue
            }
        }

        return costs[to.count]
    }
}
