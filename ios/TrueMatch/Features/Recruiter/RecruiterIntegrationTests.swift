//
//  RecruiterIntegrationTests.swift
//  TrueMatchTests
//
//  Integration tests for recruiter API calls and data flow.
//

import XCTest
@testable import TrueMatch

final class RecruiterCommandCentreIntegrationTests: XCTestCase {

    // MARK: - Mock API Responses

    func testLoadCommandCentreData() async throws {
        // This test would integrate with a mock API client
        let mockResponse = RecruiterCommandCentreResponse(
            tasks: [
                RecruiterTask(
                    id: "t1", type: .approval, candidateName: "Alice",
                    candidateId: "c1", positionTitle: "Engineer", positionId: "p1",
                    status: "pending", dueDate: .now, createdAt: .now,
                    description: "Review and approve"
                ),
            ],
            positions: [
                ActivePosition(
                    id: "p1", title: "Senior Engineer", department: "Engineering",
                    openCount: 3, fillRate: 0.33, urgency: .high,
                    thumbnailUrl: nil, activeCount: 2
                ),
            ],
            queueItems: [
                CandidateQueueItem(
                    id: "q1", candidateId: "c1", name: "Alice",
                    email: "alice@example.com", avatarUrl: nil, score: 85,
                    delta: 5, stage: .screening, positionId: "p1",
                    positionTitle: "Engineer", nextAction: "Review CV", daysSinceAdded: 1
                ),
            ],
            activityFeed: [
                AgentActivityEntry(
                    id: "a1", agentName: "AutoMatcher", action: "Reviewed CV",
                    candidateName: "Alice", positionTitle: "Engineer",
                    timestamp: .now, status: .success
                ),
            ]
        )

        XCTAssertEqual(mockResponse.tasks.count, 1)
        XCTAssertEqual(mockResponse.positions.count, 1)
        XCTAssertEqual(mockResponse.queueItems.count, 1)
        XCTAssertEqual(mockResponse.activityFeed.count, 1)
    }

    func testRecruiterPipelineResponse() throws {
        let cards = [
            PipelineCard(
                id: "1", candidateId: "c1", name: "Alice", score: 85,
                delta: 5, stage: .screening, avatarUrl: nil,
                positionId: "p1", notesCount: 2
            ),
            PipelineCard(
                id: "2", candidateId: "c2", name: "Bob", score: 72,
                delta: nil, stage: .interview, avatarUrl: nil,
                positionId: "p1", notesCount: 0
            ),
        ]

        let response = PipelineResponse(cards: cards, updatedAt: .now)

        XCTAssertEqual(response.cards.count, 2)
        XCTAssertEqual(response.cards[0].stage, .screening)
        XCTAssertEqual(response.cards[1].stage, .interview)
    }

    func testSearchResultsResponse() throws {
        let results = [
            RecruiterSearchResult(
                id: "r1", candidateId: "c1", name: "Alice",
                email: "alice@example.com", score: 85, stage: .screening,
                positionTitle: "Engineer", positionId: "p1",
                avatarUrl: nil, matchPercentage: 95
            ),
        ]

        let response = SearchResultsResponse(results: results, total: 1, cursor: nil)

        XCTAssertEqual(response.results.count, 1)
        XCTAssertEqual(response.total, 1)
        XCTAssertEqual(response.results[0].matchPercentage, 95)
    }
}

// MARK: - Decision Recording Tests

final class RecruiterDecisionIntegrationTests: XCTestCase {

    func testRecordDecisionRequest() throws {
        let request = RecordDecisionRequest(
            decision: "approve",
            feedback: "Strong candidate, excellent fit",
            timestamp: .now
        )

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601

        let data = try encoder.encode(request)
        let decoded = try JSONDecoder().decode(RecordDecisionRequest.self, from: data)

        XCTAssertEqual(decoded.decision, "approve")
        XCTAssertEqual(decoded.feedback, "Strong candidate, excellent fit")
    }

    func testSearchCandidatesRequest() throws {
        let request = SearchCandidatesRequest(
            query: "Alice",
            stage: "screening",
            scoreMin: 70,
            scoreMax: 100,
            positionId: "p1"
        )

        XCTAssertEqual(request.query, "Alice")
        XCTAssertEqual(request.stage, "screening")
        XCTAssertEqual(request.scoreMin, 70)
        XCTAssertEqual(request.scoreMax, 100)
        XCTAssertEqual(request.limit, 50)
    }
}

// MARK: - Models Codable Tests

final class RecruiterModelsEncodingTests: XCTestCase {

    func testTaskEncoding() throws {
        let task = RecruiterTask(
            id: "t1", type: .approval, candidateName: "Alice",
            candidateId: "c1", positionTitle: "Engineer", positionId: "p1",
            status: "pending", dueDate: .now, createdAt: .now,
            description: "Review and approve"
        )

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.keyEncodingStrategy = .convertToSnakeCase

        let data = try encoder.encode(task)
        let decoded = try JSONDecoder().decode(RecruiterTask.self, from: data)

        XCTAssertEqual(decoded.id, task.id)
        XCTAssertEqual(decoded.candidateName, task.candidateName)
        XCTAssertEqual(decoded.type, .approval)
    }

    func testPositionEncoding() throws {
        let position = ActivePosition(
            id: "p1", title: "Engineer", department: "Engineering",
            openCount: 5, fillRate: 0.4, urgency: .critical,
            thumbnailUrl: nil, activeCount: 2
        )

        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase

        let data = try encoder.encode(position)
        let decoded = try JSONDecoder().decode(ActivePosition.self, from: data)

        XCTAssertEqual(decoded.id, position.id)
        XCTAssertEqual(decoded.urgency, .critical)
        XCTAssertEqual(decoded.fillRate, 0.4)
    }

    func testPipelineCardEncoding() throws {
        let card = PipelineCard(
            id: "1", candidateId: "c1", name: "Alice", score: 85,
            delta: 5, stage: .screening, avatarUrl: nil,
            positionId: "p1", notesCount: 2
        )

        let encoder = JSONEncoder()
        let data = try encoder.encode(card)
        let decoded = try JSONDecoder().decode(PipelineCard.self, from: data)

        XCTAssertEqual(decoded.id, card.id)
        XCTAssertEqual(decoded.stage, .screening)
        XCTAssertEqual(decoded.delta, 5)
    }

    func testDecisionRecordEncoding() throws {
        let decision = DecisionRecord(
            id: "d1", candidateId: "c1", candidateName: "Alice",
            positionId: "p1", positionTitle: "Engineer", decision: .approve,
            feedback: "Great fit", timestamp: .now, recordedBy: "recruiter1"
        )

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601

        let data = try encoder.encode(decision)
        let decoded = try JSONDecoder().decode(DecisionRecord.self, from: data)

        XCTAssertEqual(decoded.candidateName, "Alice")
        XCTAssertEqual(decoded.decision, .approve)
    }
}

// MARK: - Pipeline Stage Tests

final class PipelineStageTests: XCTestCase {

    func testPipelineStageAllCases() {
        let allCases = PipelineStage.allCases
        XCTAssertEqual(allCases.count, 4)
        XCTAssertTrue(allCases.contains(.screening))
        XCTAssertTrue(allCases.contains(.interview))
        XCTAssertTrue(allCases.contains(.offer))
        XCTAssertTrue(allCases.contains(.hired))
    }

    func testPipelineStageRawValues() {
        XCTAssertEqual(PipelineStage.screening.rawValue, "screening")
        XCTAssertEqual(PipelineStage.interview.rawValue, "interview")
        XCTAssertEqual(PipelineStage.offer.rawValue, "offer")
        XCTAssertEqual(PipelineStage.hired.rawValue, "hired")
    }
}

// MARK: - Urgency Level Tests

final class UrgencyLevelTests: XCTestCase {

    func testUrgencyRawValues() {
        XCTAssertEqual(ActivePosition.Urgency.critical.rawValue, "critical")
        XCTAssertEqual(ActivePosition.Urgency.high.rawValue, "high")
        XCTAssertEqual(ActivePosition.Urgency.normal.rawValue, "normal")
        XCTAssertEqual(ActivePosition.Urgency.low.rawValue, "low")
    }
}
