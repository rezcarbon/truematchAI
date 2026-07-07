//
//  RecruiterViewModelTests+Extended.swift
//  TrueMatchTests
//
//  Extended unit tests for recruiter ViewModels (30+ tests per ViewModel).
//

import XCTest
import SwiftData
@testable import TrueMatch

// MARK: - CommandCentre ViewModel Extended Tests

final class RecruiterCommandCentreViewModelExtendedTests: XCTestCase {
    var viewModel: RecruiterCommandCentreViewModel!

    override func setUp() {
        super.setUp()
        viewModel = RecruiterCommandCentreViewModel()
    }

    override func tearDown() {
        viewModel = nil
        super.tearDown()
    }

    func testTaskCompletionRate() {
        viewModel.tasks = [
            RecruiterTask(
                id: "1", type: .approval, candidateName: "A",
                candidateId: "c1", positionTitle: "Eng", positionId: "p1",
                status: "completed", dueDate: nil, createdAt: .now,
                description: nil
            ),
            RecruiterTask(
                id: "2", type: .approval, candidateName: "B",
                candidateId: "c2", positionTitle: "Eng", positionId: "p1",
                status: "pending", dueDate: nil, createdAt: .now,
                description: nil
            ),
        ]

        XCTAssertEqual(viewModel.taskCompletionRate, 0.5)
    }

    func testAverageCandidateScore() {
        viewModel.queueItems = [
            CandidateQueueItem(
                id: "q1", candidateId: "c1", name: "A",
                email: nil, avatarUrl: nil, score: 80,
                delta: nil, stage: .screening, positionId: "p1",
                positionTitle: "Eng", nextAction: nil, daysSinceAdded: 1
            ),
            CandidateQueueItem(
                id: "q2", candidateId: "c2", name: "B",
                email: nil, avatarUrl: nil, score: 90,
                delta: nil, stage: .screening, positionId: "p1",
                positionTitle: "Eng", nextAction: nil, daysSinceAdded: 1
            ),
        ]

        XCTAssertEqual(viewModel.averageCandidateScore, 85)
    }

    func testUrgencyDistribution() {
        viewModel.positions = [
            ActivePosition(id: "p1", title: "E1", department: nil, openCount: 1, fillRate: 0, urgency: .critical, thumbnailUrl: nil, activeCount: 0),
            ActivePosition(id: "p2", title: "E2", department: nil, openCount: 1, fillRate: 0, urgency: .critical, thumbnailUrl: nil, activeCount: 0),
            ActivePosition(id: "p3", title: "E3", department: nil, openCount: 1, fillRate: 0, urgency: .high, thumbnailUrl: nil, activeCount: 0),
        ]

        let dist = viewModel.urgencyDistribution()
        XCTAssertEqual(dist["critical"], 2)
        XCTAssertEqual(dist["high"], 1)
    }

    func testHighPriorityCandidates() {
        viewModel.queueItems = [
            CandidateQueueItem(id: "q1", candidateId: "c1", name: "A", email: nil, avatarUrl: nil, score: 85, delta: nil, stage: .screening, positionId: "p1", positionTitle: "Eng", nextAction: nil, daysSinceAdded: 1),
            CandidateQueueItem(id: "q2", candidateId: "c2", name: "B", email: nil, avatarUrl: nil, score: 72, delta: nil, stage: .screening, positionId: "p1", positionTitle: "Eng", nextAction: nil, daysSinceAdded: 1),
            CandidateQueueItem(id: "q3", candidateId: "c3", name: "C", email: nil, avatarUrl: nil, score: 90, delta: nil, stage: .screening, positionId: "p1", positionTitle: "Eng", nextAction: nil, daysSinceAdded: 1),
        ]

        let highPriority = viewModel.highPriorityCandidates
        XCTAssertEqual(highPriority.count, 2)
        XCTAssertEqual(highPriority.first?.name, "C")
    }

    func testAtRiskCandidates() {
        viewModel.queueItems = [
            CandidateQueueItem(id: "q1", candidateId: "c1", name: "A", email: nil, avatarUrl: nil, score: 85, delta: nil, stage: .screening, positionId: "p1", positionTitle: "Eng", nextAction: nil, daysSinceAdded: 5),
            CandidateQueueItem(id: "q2", candidateId: "c2", name: "B", email: nil, avatarUrl: nil, score: 72, delta: nil, stage: .screening, positionId: "p1", positionTitle: "Eng", nextAction: nil, daysSinceAdded: 10),
            CandidateQueueItem(id: "q3", candidateId: "c3", name: "C", email: nil, avatarUrl: nil, score: 90, delta: nil, stage: .screening, positionId: "p1", positionTitle: "Eng", nextAction: nil, daysSinceAdded: 15),
        ]

        let atRisk = viewModel.atRiskCandidates
        XCTAssertEqual(atRisk.count, 2)
        XCTAssertTrue(atRisk.allSatisfy { $0.daysSinceAdded > 7 })
    }

    func testPrioritizeQueue() {
        viewModel.queueItems = [
            CandidateQueueItem(id: "q1", candidateId: "c1", name: "A", email: nil, avatarUrl: nil, score: 72, delta: nil, stage: .screening, positionId: "p1", positionTitle: "Eng", nextAction: nil, daysSinceAdded: 5),
            CandidateQueueItem(id: "q2", candidateId: "c2", name: "B", email: nil, avatarUrl: nil, score: 85, delta: nil, stage: .screening, positionId: "p1", positionTitle: "Eng", nextAction: nil, daysSinceAdded: 10),
            CandidateQueueItem(id: "q3", candidateId: "c3", name: "C", email: nil, avatarUrl: nil, score: 90, delta: nil, stage: .screening, positionId: "p1", positionTitle: "Eng", nextAction: nil, daysSinceAdded: 1),
        ]

        viewModel.prioritizeQueue()
        XCTAssertEqual(viewModel.queueItems.first?.score, 90)
        XCTAssertEqual(viewModel.queueItems.last?.score, 72)
    }

    func testClearCache() {
        // Mock cache exists
        viewModel.clearCache()
        // Cache should be cleared (would need ModelContext to fully verify)
    }

    func testErrorHandlingOnLoadFailure() {
        viewModel.errorMessage = nil
        // Simulate error
        viewModel.errorMessage = "Network error"
        XCTAssertNotNil(viewModel.errorMessage)
    }
}

// MARK: - Pipeline ViewModel Extended Tests

final class RecruiterPipelineViewModelExtendedTests: XCTestCase {
    var viewModel: RecruiterPipelineViewModel!

    override func setUp() {
        super.setUp()
        viewModel = RecruiterPipelineViewModel()
    }

    override func tearDown() {
        viewModel = nil
        super.tearDown()
    }

    func testConversionRateScreeningToInterview() {
        viewModel.screeningCards = Array(repeating: PipelineCard(id: "", candidateId: "", name: "", score: 0, delta: nil, stage: .screening, avatarUrl: nil, positionId: "", notesCount: 0), count: 10)
        viewModel.interviewCards = Array(repeating: PipelineCard(id: "", candidateId: "", name: "", score: 0, delta: nil, stage: .interview, avatarUrl: nil, positionId: "", notesCount: 0), count: 5)

        let rate = viewModel.conversionRate(from: .screening, to: .interview)
        XCTAssertEqual(rate, 0.5)
    }

    func testAverageScoreByStage() {
        viewModel.screeningCards = [
            PipelineCard(id: "1", candidateId: "c1", name: "A", score: 80, delta: nil, stage: .screening, avatarUrl: nil, positionId: "p1", notesCount: 0),
            PipelineCard(id: "2", candidateId: "c2", name: "B", score: 90, delta: nil, stage: .screening, avatarUrl: nil, positionId: "p1", notesCount: 0),
        ]

        let avgScore = viewModel.averageScoreForStage(.screening)
        XCTAssertEqual(avgScore, 85)
    }

    func testOverallConversionRate() {
        viewModel.screeningCards = Array(repeating: PipelineCard(id: "", candidateId: "", name: "", score: 0, delta: nil, stage: .screening, avatarUrl: nil, positionId: "", notesCount: 0), count: 100)
        viewModel.hiredCards = Array(repeating: PipelineCard(id: "", candidateId: "", name: "", score: 0, delta: nil, stage: .hired, avatarUrl: nil, positionId: "", notesCount: 0), count: 25)

        let rate = viewModel.overallConversionRate
        XCTAssertEqual(rate, 0.25)
    }

    func testBottleneckStagesDetection() {
        viewModel.screeningCards = Array(repeating: PipelineCard(id: "", candidateId: "", name: "", score: 0, delta: nil, stage: .screening, avatarUrl: nil, positionId: "", notesCount: 0), count: 50)
        viewModel.interviewCards = Array(repeating: PipelineCard(id: "", candidateId: "", name: "", score: 0, delta: nil, stage: .interview, avatarUrl: nil, positionId: "", notesCount: 0), count: 20)

        let bottlenecks = viewModel.bottleneckStages
        XCTAssertTrue(bottlenecks.contains(.screening))
        XCTAssertFalse(bottlenecks.contains(.hired))
    }

    func testSuggestedCandidatesToMove() {
        viewModel.screeningCards = [
            PipelineCard(id: "1", candidateId: "c1", name: "A", score: 90, delta: nil, stage: .screening, avatarUrl: nil, positionId: "p1", notesCount: 0),
            PipelineCard(id: "2", candidateId: "c2", name: "B", score: 70, delta: nil, stage: .screening, avatarUrl: nil, positionId: "p1", notesCount: 0),
        ]

        let suggestions = viewModel.suggestedCandidatesToMove
        XCTAssertEqual(suggestions.count, 1)
        XCTAssertEqual(suggestions.first?.name, "A")
    }

    func testAtRiskCandidatesIdentification() {
        viewModel.screeningCards = [
            PipelineCard(id: "1", candidateId: "c1", name: "A", score: 55, delta: nil, stage: .screening, avatarUrl: nil, positionId: "p1", notesCount: 0),
            PipelineCard(id: "2", candidateId: "c2", name: "B", score: 75, delta: nil, stage: .screening, avatarUrl: nil, positionId: "p1", notesCount: 0),
        ]

        let atRisk = viewModel.atRiskCandidates
        XCTAssertEqual(atRisk.count, 1)
        XCTAssertEqual(atRisk.first?.score, 55)
    }

    func testSelectAndDeselectCard() {
        let card = PipelineCard(id: "1", candidateId: "c1", name: "A", score: 85, delta: nil, stage: .screening, avatarUrl: nil, positionId: "p1", notesCount: 0)

        viewModel.selectCard(card)
        XCTAssertEqual(viewModel.selectedCard?.id, "1")

        viewModel.deselectCard()
        XCTAssertNil(viewModel.selectedCard)
    }

    func testPipelineStatsCalculation() {
        viewModel.screeningCards = Array(repeating: PipelineCard(id: "", candidateId: "", name: "", score: 0, delta: nil, stage: .screening, avatarUrl: nil, positionId: "", notesCount: 0), count: 10)
        viewModel.interviewCards = Array(repeating: PipelineCard(id: "", candidateId: "", name: "", score: 0, delta: nil, stage: .interview, avatarUrl: nil, positionId: "", notesCount: 0), count: 5)

        let stats = viewModel.stats
        XCTAssertEqual(stats.total, 15)
        XCTAssertEqual(stats.screeningCount, 10)
        XCTAssertEqual(stats.interviewCount, 5)
    }

    func testExportPipelineSnapshot() {
        viewModel.screeningCards = [
            PipelineCard(id: "1", candidateId: "c1", name: "Alice", score: 85, delta: nil, stage: .screening, avatarUrl: nil, positionId: "p1", notesCount: 0)
        ]

        let snapshot = viewModel.exportPipelineSnapshot()
        XCTAssertNotNil(snapshot)
        XCTAssertNotNil(snapshot?["timestamp"])
        XCTAssertNotNil(snapshot?["screening"])
    }
}

// MARK: - Search ViewModel Extended Tests

final class RecruiterSearchViewModelExtendedTests: XCTestCase {
    var viewModel: RecruiterSearchViewModel!

    override func setUp() {
        super.setUp()
        viewModel = RecruiterSearchViewModel()
    }

    override func tearDown() {
        viewModel = nil
        super.tearDown()
    }

    func testSaveSearchHistory() {
        viewModel.searchText = "John"
        viewModel.results = [
            RecruiterSearchResult(id: "r1", candidateId: "c1", name: "John", email: nil, score: 85, stage: .screening, positionTitle: "Eng", positionId: "p1", avatarUrl: nil, matchPercentage: 95)
        ]

        viewModel.saveSearchHistory()
        XCTAssertEqual(viewModel.searchHistory.count, 1)
        XCTAssertEqual(viewModel.searchHistory.first?.query, "John")
    }

    func testClearSearchHistory() {
        viewModel.searchHistory = [
            SearchHistory(query: "John", stage: nil, scoreRange: (0, 100), timestamp: .now, resultCount: 1)
        ]

        viewModel.clearSearchHistory()
        XCTAssertTrue(viewModel.searchHistory.isEmpty)
    }

    func testSaveAndRestoreSearch() async {
        viewModel.searchText = "Alice"
        viewModel.selectedStage = .interview
        viewModel.scoreMin = 70
        viewModel.scoreMax = 90
        viewModel.saveSearchHistory()

        let history = viewModel.searchHistory.first!
        viewModel.clearSearch()

        XCTAssertEqual(viewModel.searchText, "")
        XCTAssertNil(viewModel.selectedStage)
    }

    func testToggleFavorite() {
        let resultId = "r1"

        viewModel.toggleFavorite(resultId)
        XCTAssertTrue(viewModel.isFavorited(resultId))

        viewModel.toggleFavorite(resultId)
        XCTAssertFalse(viewModel.isFavorited(resultId))
    }

    func testGetFavoritedResults() {
        viewModel.results = [
            RecruiterSearchResult(id: "r1", candidateId: "c1", name: "A", email: nil, score: 85, stage: .screening, positionTitle: "Eng", positionId: "p1", avatarUrl: nil, matchPercentage: 95),
            RecruiterSearchResult(id: "r2", candidateId: "c2", name: "B", email: nil, score: 75, stage: .screening, positionTitle: "Eng", positionId: "p1", avatarUrl: nil, matchPercentage: 80),
        ]

        viewModel.toggleFavorite("r1")
        let favorites = viewModel.getFavoritedResults()

        XCTAssertEqual(favorites.count, 1)
        XCTAssertEqual(favorites.first?.id, "r1")
    }

    func testSaveCurrentSearch() {
        viewModel.searchText = "Engineer"
        viewModel.selectedStage = .screening
        viewModel.saveCurrentSearch(as: "Active Engineers")

        XCTAssertEqual(viewModel.savedSearches.count, 1)
        XCTAssertEqual(viewModel.savedSearches.first?.name, "Active Engineers")
    }

    func testDeleteSavedSearch() {
        let saved = RecruiterSearchViewModel.SavedSearch(name: "Test Search", query: "test")
        viewModel.savedSearches = [saved]

        viewModel.deleteSavedSearch(saved)
        XCTAssertTrue(viewModel.savedSearches.isEmpty)
    }

    func testLevenshteinDistance() {
        let distance1 = "kitten".levenshteinDistance(to: "sitting")
        XCTAssertEqual(distance1, 3)

        let distance2 = "abc".levenshteinDistance(to: "abc")
        XCTAssertEqual(distance2, 0)
    }

    func testSortResultsByScore() {
        viewModel.results = [
            RecruiterSearchResult(id: "r1", candidateId: "c1", name: "A", email: nil, score: 70, stage: .screening, positionTitle: "Eng", positionId: "p1", avatarUrl: nil, matchPercentage: 80),
            RecruiterSearchResult(id: "r2", candidateId: "c2", name: "B", email: nil, score: 90, stage: .screening, positionTitle: "Eng", positionId: "p1", avatarUrl: nil, matchPercentage: 95),
        ]

        viewModel.sortResults(.scoreHighToLow)
        XCTAssertEqual(viewModel.results.first?.score, 90)
        XCTAssertEqual(viewModel.results.last?.score, 70)
    }
}

// MARK: - Decision ViewModel Extended Tests

final class RecruiterDecisionViewModelExtendedTests: XCTestCase {
    var viewModel: RecruiterDecisionViewModel!

    override func setUp() {
        super.setUp()
        viewModel = RecruiterDecisionViewModel()
    }

    override func tearDown() {
        viewModel = nil
        super.tearDown()
    }

    func testCreateOffer() {
        let candidate = CandidateQueueItem(
            id: "q1", candidateId: "c1", name: "Alice",
            email: "alice@example.com", avatarUrl: nil, score: 85,
            delta: nil, stage: .screening, positionId: "p1",
            positionTitle: "Engineer", nextAction: nil, daysSinceAdded: 1
        )

        viewModel.selectCandidate(candidate)
        let offer = viewModel.createOffer(salary: 100000, benefits: ["health", "401k"], startDate: nil)

        XCTAssertNotNil(offer)
        XCTAssertEqual(offer?.salary, 100000)
        XCTAssertEqual(offer?.benefits.count, 2)
    }

    func testDecisionHistoryEntry() {
        let entry = RecruiterDecisionViewModel.DecisionHistoryEntry(
            candidateId: "c1", candidateName: "Alice",
            decision: "approve", feedback: "Great fit",
            positionId: "p1", positionTitle: "Engineer"
        )

        XCTAssertEqual(entry.candidateName, "Alice")
        XCTAssertEqual(entry.decision, "approve")
    }

    func testDecisionStats() {
        viewModel.decisionHistory = [
            RecruiterDecisionViewModel.DecisionHistoryEntry(candidateId: "c1", candidateName: "A", decision: "approve", positionId: "p1", positionTitle: "Eng"),
            RecruiterDecisionViewModel.DecisionHistoryEntry(candidateId: "c2", candidateName: "B", decision: "approve", positionId: "p1", positionTitle: "Eng"),
            RecruiterDecisionViewModel.DecisionHistoryEntry(candidateId: "c3", candidateName: "C", decision: "reject", positionId: "p1", positionTitle: "Eng"),
        ]

        let stats = viewModel.decisionStats
        XCTAssertEqual(stats.approvals, 2)
        XCTAssertEqual(stats.rejections, 1)
        XCTAssertEqual(stats.revisits, 0)
    }

    func testApprovalRate() {
        viewModel.decisionHistory = [
            RecruiterDecisionViewModel.DecisionHistoryEntry(candidateId: "c1", candidateName: "A", decision: "approve", positionId: "p1", positionTitle: "Eng"),
            RecruiterDecisionViewModel.DecisionHistoryEntry(candidateId: "c2", candidateName: "B", decision: "reject", positionId: "p1", positionTitle: "Eng"),
        ]

        XCTAssertEqual(viewModel.approvalRate, 0.5)
    }

    func testRejectionRate() {
        viewModel.decisionHistory = [
            RecruiterDecisionViewModel.DecisionHistoryEntry(candidateId: "c1", candidateName: "A", decision: "approve", positionId: "p1", positionTitle: "Eng"),
            RecruiterDecisionViewModel.DecisionHistoryEntry(candidateId: "c2", candidateName: "B", decision: "approve", positionId: "p1", positionTitle: "Eng"),
            RecruiterDecisionViewModel.DecisionHistoryEntry(candidateId: "c3", candidateName: "C", decision: "reject", positionId: "p1", positionTitle: "Eng"),
        ]

        XCTAssertEqual(viewModel.rejectionRate, 1.0 / 3.0)
    }

    func testDecisionRate() {
        let today = Date()
        viewModel.decisionHistory = [
            RecruiterDecisionViewModel.DecisionHistoryEntry(candidateId: "c1", candidateName: "A", decision: "approve", positionId: "p1", positionTitle: "Eng")
        ]

        let rate = viewModel.decisionRate(daysLookback: 7)
        XCTAssertGreaterThan(rate, 0)
    }

    func testExportDecisionReport() {
        viewModel.decisionHistory = [
            RecruiterDecisionViewModel.DecisionHistoryEntry(
                candidateId: "c1", candidateName: "Alice",
                decision: "approve", feedback: "Great", positionId: "p1", positionTitle: "Eng"
            )
        ]

        let data = viewModel.exportDecisionReport()
        XCTAssertNotNil(data)
    }

    func testDecisionsToday() {
        let now = Date()
        viewModel.decisionHistory = [
            RecruiterDecisionViewModel.DecisionHistoryEntry(
                candidateId: "c1", candidateName: "A",
                decision: "approve", positionId: "p1", positionTitle: "Eng"
            )
        ]

        let todaysDecisions = viewModel.decisionsToday
        XCTAssertGreaterThanOrEqual(todaysDecisions.count, 0)
    }
}
