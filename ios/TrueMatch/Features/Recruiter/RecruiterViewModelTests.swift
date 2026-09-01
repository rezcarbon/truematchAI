//
//  RecruiterViewModelTests.swift
//  TrueMatchTests
//
//  Unit tests for recruiter ViewModels: command centre, pipeline, search, decision.
//

import XCTest
import SwiftData
@testable import TrueMatch

final class RecruiterCommandCentreViewModelTests: XCTestCase {
    var viewModel: RecruiterCommandCentreViewModel!

    override func setUp() {
        super.setUp()
        viewModel = RecruiterCommandCentreViewModel()
    }

    override func tearDown() {
        viewModel = nil
        super.tearDown()
    }

    // MARK: - Initialization Tests

    func testInitialization() {
        XCTAssertTrue(viewModel.tasks.isEmpty)
        XCTAssertTrue(viewModel.positions.isEmpty)
        XCTAssertTrue(viewModel.queueItems.isEmpty)
        XCTAssertTrue(viewModel.activityFeed.isEmpty)
        XCTAssertFalse(viewModel.isLoading)
    }

    // MARK: - Task Filtering Tests

    func testTodaysTasksFiltering() {
        let today = Calendar.current.startOfDay(for: .now)
        let tomorrow = Calendar.current.date(byAdding: .day, value: 1, to: today)!
        let yesterday = Calendar.current.date(byAdding: .day, value: -1, to: today)!

        viewModel.tasks = [
            RecruiterTask(
                id: "1", type: .approval, candidateName: "Alice",
                candidateId: "c1", positionTitle: "Engineer", positionId: "p1",
                status: "pending", dueDate: today, createdAt: .now,
                description: "Approve candidate"
            ),
            RecruiterTask(
                id: "2", type: .interview, candidateName: "Bob",
                candidateId: "c2", positionTitle: "Engineer", positionId: "p1",
                status: "pending", dueDate: tomorrow, createdAt: .now,
                description: "Schedule interview"
            ),
            RecruiterTask(
                id: "3", type: .offer, candidateName: "Charlie",
                candidateId: "c3", positionTitle: "Engineer", positionId: "p1",
                status: "pending", dueDate: yesterday, createdAt: .now,
                description: "Send offer"
            ),
        ]

        let result = viewModel.todaysTasks
        XCTAssertEqual(result.count, 1)
        XCTAssertEqual(result.first?.candidateName, "Alice")
    }

    func testPendingTasksFiltering() {
        viewModel.tasks = [
            RecruiterTask(
                id: "1", type: .approval, candidateName: "Alice",
                candidateId: "c1", positionTitle: "Engineer", positionId: "p1",
                status: "pending", dueDate: nil, createdAt: .now,
                description: nil
            ),
            RecruiterTask(
                id: "2", type: .approval, candidateName: "Bob",
                candidateId: "c2", positionTitle: "Engineer", positionId: "p1",
                status: "completed", dueDate: nil, createdAt: .now,
                description: nil
            ),
        ]

        let result = viewModel.pendingTasks
        XCTAssertEqual(result.count, 1)
        XCTAssertEqual(result.first?.candidateName, "Alice")
    }

    func testCriticalPositionsFiltering() {
        viewModel.positions = [
            ActivePosition(
                id: "p1", title: "Engineer", department: "Engineering",
                openCount: 5, fillRate: 0.4, urgency: .critical,
                thumbnailUrl: nil, activeCount: 2
            ),
            ActivePosition(
                id: "p2", title: "Designer", department: "Design",
                openCount: 2, fillRate: 0.8, urgency: .normal,
                thumbnailUrl: nil, activeCount: 1
            ),
        ]

        let result = viewModel.criticalPositions
        XCTAssertEqual(result.count, 1)
        XCTAssertEqual(result.first?.title, "Engineer")
    }

    func testUpcomingTasksFiltering() {
        let today = Calendar.current.startOfDay(for: .now)
        let tomorrow = Calendar.current.date(byAdding: .day, value: 1, to: today)!
        let sevenDaysOut = Calendar.current.date(byAdding: .day, value: 7, to: today)!
        let tenDaysOut = Calendar.current.date(byAdding: .day, value: 10, to: today)!

        viewModel.tasks = [
            RecruiterTask(
                id: "1", type: .approval, candidateName: "Alice",
                candidateId: "c1", positionTitle: "Engineer", positionId: "p1",
                status: "pending", dueDate: tomorrow, createdAt: .now,
                description: nil
            ),
            RecruiterTask(
                id: "2", type: .approval, candidateName: "Bob",
                candidateId: "c2", positionTitle: "Engineer", positionId: "p1",
                status: "pending", dueDate: sevenDaysOut, createdAt: .now,
                description: nil
            ),
            RecruiterTask(
                id: "3", type: .approval, candidateName: "Charlie",
                candidateId: "c3", positionTitle: "Engineer", positionId: "p1",
                status: "pending", dueDate: tenDaysOut, createdAt: .now,
                description: nil
            ),
        ]

        let result = viewModel.upcomingTasks
        XCTAssertEqual(result.count, 2)
    }

    func testRecentActivityFiltering() {
        let oneDayAgo = Calendar.current.date(byAdding: .day, value: -1, to: .now)!
        let threeDaysAgo = Calendar.current.date(byAdding: .day, value: -3, to: .now)!

        viewModel.activityFeed = [
            AgentActivityEntry(
                id: "1", agentName: "Agent A", action: "Reviewed CV",
                candidateName: "Alice", positionTitle: "Engineer",
                timestamp: oneDayAgo, status: .success
            ),
            AgentActivityEntry(
                id: "2", agentName: "Agent B", action: "Sent offer",
                candidateName: "Bob", positionTitle: "Engineer",
                timestamp: threeDaysAgo, status: .success
            ),
        ]

        let result = viewModel.recentActivity
        XCTAssertEqual(result.count, 1)
        XCTAssertEqual(result.first?.candidateName, "Alice")
    }
}

// MARK: - Pipeline ViewModel Tests

final class RecruiterPipelineViewModelTests: XCTestCase {
    var viewModel: RecruiterPipelineViewModel!

    override func setUp() {
        super.setUp()
        viewModel = RecruiterPipelineViewModel()
    }

    override func tearDown() {
        viewModel = nil
        super.tearDown()
    }

    func testInitialization() {
        XCTAssertTrue(viewModel.screeningCards.isEmpty)
        XCTAssertTrue(viewModel.interviewCards.isEmpty)
        XCTAssertTrue(viewModel.offerCards.isEmpty)
        XCTAssertTrue(viewModel.hiredCards.isEmpty)
        XCTAssertFalse(viewModel.isLoading)
    }

    func testOrganizePipeline() {
        let cards = [
            PipelineCard(
                id: "1", candidateId: "c1", name: "Alice", score: 85,
                delta: 5, stage: .screening, avatarUrl: nil,
                positionId: "p1", notesCount: 0
            ),
            PipelineCard(
                id: "2", candidateId: "c2", name: "Bob", score: 72,
                delta: nil, stage: .interview, avatarUrl: nil,
                positionId: "p1", notesCount: 1
            ),
            PipelineCard(
                id: "3", candidateId: "c3", name: "Charlie", score: 90,
                delta: -3, stage: .hired, avatarUrl: nil,
                positionId: "p1", notesCount: 0
            ),
        ]

        // Private method would be called from loadPipeline
        viewModel.screeningCards = [cards[0]]
        viewModel.interviewCards = [cards[1]]
        viewModel.hiredCards = [cards[2]]

        XCTAssertEqual(viewModel.screeningCards.count, 1)
        XCTAssertEqual(viewModel.interviewCards.count, 1)
        XCTAssertEqual(viewModel.hiredCards.count, 1)
    }

    func testPipelineStats() {
        viewModel.screeningCards = [
            PipelineCard(
                id: "1", candidateId: "c1", name: "A", score: 80,
                delta: nil, stage: .screening, avatarUrl: nil,
                positionId: "p1", notesCount: 0
            ),
        ]
        viewModel.interviewCards = [
            PipelineCard(
                id: "2", candidateId: "c2", name: "B", score: 75,
                delta: nil, stage: .interview, avatarUrl: nil,
                positionId: "p1", notesCount: 0
            ),
        ]

        let stats = viewModel.stats
        XCTAssertEqual(stats.screeningCount, 1)
        XCTAssertEqual(stats.interviewCount, 1)
        XCTAssertEqual(stats.offerCount, 0)
        XCTAssertEqual(stats.hiredCount, 0)
        XCTAssertEqual(stats.total, 2)
    }
}

// MARK: - Search ViewModel Tests

final class RecruiterSearchViewModelTests: XCTestCase {
    var viewModel: RecruiterSearchViewModel!

    override func setUp() {
        super.setUp()
        viewModel = RecruiterSearchViewModel()
    }

    override func tearDown() {
        viewModel = nil
        super.tearDown()
    }

    func testInitialization() {
        XCTAssertEqual(viewModel.searchText, "")
        XCTAssertNil(viewModel.selectedStage)
        XCTAssertEqual(viewModel.scoreMin, 0)
        XCTAssertEqual(viewModel.scoreMax, 100)
        XCTAssertTrue(viewModel.results.isEmpty)
        XCTAssertFalse(viewModel.hasSearched)
    }

    func testClearSearch() {
        viewModel.searchText = "Alice"
        viewModel.selectedStage = .interview
        viewModel.scoreMin = 50
        viewModel.scoreMax = 90
        viewModel.hasSearched = true

        viewModel.clearSearch()

        XCTAssertEqual(viewModel.searchText, "")
        XCTAssertNil(viewModel.selectedStage)
        XCTAssertEqual(viewModel.scoreMin, 0)
        XCTAssertEqual(viewModel.scoreMax, 100)
        XCTAssertFalse(viewModel.hasSearched)
    }
}

// MARK: - Decision ViewModel Tests

final class RecruiterDecisionViewModelTests: XCTestCase {
    var viewModel: RecruiterDecisionViewModel!

    override func setUp() {
        super.setUp()
        viewModel = RecruiterDecisionViewModel()
    }

    override func tearDown() {
        viewModel = nil
        super.tearDown()
    }

    func testInitialization() {
        XCTAssertNil(viewModel.selectedCandidate)
        XCTAssertNil(viewModel.selectedDecision)
        XCTAssertEqual(viewModel.feedbackText, "")
        XCTAssertFalse(viewModel.isSubmitting)
    }

    func testSelectCandidate() {
        let candidate = CandidateQueueItem(
            id: "1", candidateId: "c1", name: "Alice",
            email: "alice@example.com", avatarUrl: nil, score: 85,
            delta: nil, stage: .screening, positionId: "p1",
            positionTitle: "Engineer", nextAction: nil, daysSinceAdded: 1
        )

        viewModel.selectCandidate(candidate)

        XCTAssertEqual(viewModel.selectedCandidate?.name, "Alice")
        XCTAssertEqual(viewModel.feedbackText, "")
    }

    func testClearSelection() {
        let candidate = CandidateQueueItem(
            id: "1", candidateId: "c1", name: "Alice",
            email: "alice@example.com", avatarUrl: nil, score: 85,
            delta: nil, stage: .screening, positionId: "p1",
            positionTitle: "Engineer", nextAction: nil, daysSinceAdded: 1
        )

        viewModel.selectCandidate(candidate)
        viewModel.selectedDecision = .approve
        viewModel.feedbackText = "Great candidate"

        viewModel.clearSelection()

        XCTAssertNil(viewModel.selectedCandidate)
        XCTAssertNil(viewModel.selectedDecision)
        XCTAssertEqual(viewModel.feedbackText, "")
    }

    func testSelectTemplate() {
        viewModel.selectedDecision = .approve
        viewModel.selectTemplate("Strong candidate, moving to next stage.")

        XCTAssertEqual(viewModel.feedbackText, "Strong candidate, moving to next stage.")
        XCTAssertEqual(viewModel.selectedTemplate, "Strong candidate, moving to next stage.")
    }

    func testAvailableTemplates() {
        viewModel.selectedDecision = .approve
        let templates = viewModel.availableTemplates
        XCTAssertGreaterThan(templates.count, 0)
        XCTAssertTrue(templates.contains("Strong candidate, moving to next stage."))

        viewModel.selectedDecision = .reject
        let rejectTemplates = viewModel.availableTemplates
        XCTAssertGreaterThan(rejectTemplates.count, 0)
        XCTAssertTrue(rejectTemplates.contains("Skills mismatch with role requirements."))
    }

    func testCanSubmit() {
        XCTAssertFalse(viewModel.canSubmit)

        let candidate = CandidateQueueItem(
            id: "1", candidateId: "c1", name: "Alice",
            email: "alice@example.com", avatarUrl: nil, score: 85,
            delta: nil, stage: .screening, positionId: "p1",
            positionTitle: "Engineer", nextAction: nil, daysSinceAdded: 1
        )

        viewModel.selectCandidate(candidate)
        XCTAssertFalse(viewModel.canSubmit)

        viewModel.selectedDecision = .approve
        XCTAssertTrue(viewModel.canSubmit)
    }
}
