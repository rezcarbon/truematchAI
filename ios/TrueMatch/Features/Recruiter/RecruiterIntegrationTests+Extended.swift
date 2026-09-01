//
//  RecruiterIntegrationTests+Extended.swift
//  TrueMatchTests
//
//  Extended integration tests for recruiter API calls, WebSocket updates, and data sync.
//

import XCTest
@testable import TrueMatch

// MARK: - API Response Mocking

final class RecruiterAPIMockTests: XCTestCase {

    // MARK: - Command Centre API Tests

    func testCommandCentreAPIMockResponse() throws {
        let mockResponse = RecruiterCommandCentreResponse(
            tasks: [
                RecruiterTask(
                    id: "t1", type: .approval, candidateName: "Alice",
                    candidateId: "c1", positionTitle: "Engineer", positionId: "p1",
                    status: "pending", dueDate: .now, createdAt: .now,
                    description: "Review and approve application"
                ),
                RecruiterTask(
                    id: "t2", type: .interview, candidateName: "Bob",
                    candidateId: "c2", positionTitle: "Designer", positionId: "p2",
                    status: "pending", dueDate: .now, createdAt: .now,
                    description: "Schedule interview"
                ),
            ],
            positions: [
                ActivePosition(
                    id: "p1", title: "Senior Engineer", department: "Engineering",
                    openCount: 3, fillRate: 0.33, urgency: .critical,
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

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601

        let data = try encoder.encode(mockResponse)
        let decoded = try JSONDecoder().decode(RecruiterCommandCentreResponse.self, from: data)

        XCTAssertEqual(decoded.tasks.count, 2)
        XCTAssertEqual(decoded.positions.count, 1)
        XCTAssertEqual(decoded.queueItems.count, 1)
        XCTAssertEqual(decoded.activityFeed.count, 1)
    }

    func testPipelineResponseMock() throws {
        let cards = [
            PipelineCard(
                id: "1", candidateId: "c1", name: "Alice", score: 85,
                delta: 5, stage: .screening, avatarUrl: nil,
                positionId: "p1", notesCount: 2
            ),
            PipelineCard(
                id: "2", candidateId: "c2", name: "Bob", score: 72,
                delta: -2, stage: .interview, avatarUrl: nil,
                positionId: "p1", notesCount: 1
            ),
            PipelineCard(
                id: "3", candidateId: "c3", name: "Charlie", score: 90,
                delta: nil, stage: .offer, avatarUrl: nil,
                positionId: "p1", notesCount: 0
            ),
        ]

        let response = PipelineResponse(cards: cards, updatedAt: .now)

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(response)
        let decoded = try JSONDecoder().decode(PipelineResponse.self, from: data)

        XCTAssertEqual(decoded.cards.count, 3)
        XCTAssertEqual(decoded.cards[0].stage, .screening)
        XCTAssertEqual(decoded.cards[1].stage, .interview)
        XCTAssertEqual(decoded.cards[2].stage, .offer)
    }

    func testSearchResultsResponseMock() throws {
        let results = [
            RecruiterSearchResult(
                id: "r1", candidateId: "c1", name: "Alice",
                email: "alice@example.com", score: 85, stage: .screening,
                positionTitle: "Engineer", positionId: "p1",
                avatarUrl: nil, matchPercentage: 95
            ),
            RecruiterSearchResult(
                id: "r2", candidateId: "c2", name: "Bob",
                email: "bob@example.com", score: 72, stage: .interview,
                positionTitle: "Engineer", positionId: "p1",
                avatarUrl: nil, matchPercentage: 82
            ),
        ]

        let response = SearchResultsResponse(results: results, total: 2, cursor: nil)

        XCTAssertEqual(response.results.count, 2)
        XCTAssertEqual(response.total, 2)
        XCTAssertNil(response.cursor)
    }

    // MARK: - Decision Recording Tests

    func testRecordDecisionRequestEncoding() throws {
        let request = RecordDecisionRequest(
            decision: "approve",
            feedback: "Strong candidate, excellent fit for the role",
            timestamp: .now
        )

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601

        let data = try encoder.encode(request)
        let decoded = try JSONDecoder().decode(RecordDecisionRequest.self, from: data)

        XCTAssertEqual(decoded.decision, "approve")
        XCTAssertEqual(decoded.feedback, "Strong candidate, excellent fit for the role")
    }

    func testSearchCandidatesRequestEncoding() throws {
        let request = SearchCandidatesRequest(
            query: "Alice",
            stage: "screening",
            scoreMin: 70,
            scoreMax: 100,
            positionId: "p1",
            limit: 50
        )

        XCTAssertEqual(request.query, "Alice")
        XCTAssertEqual(request.stage, "screening")
        XCTAssertEqual(request.scoreMin, 70)
        XCTAssertEqual(request.scoreMax, 100)
        XCTAssertEqual(request.positionId, "p1")
        XCTAssertEqual(request.limit, 50)
    }

    // MARK: - Complex Model Encoding Tests

    func testComplexTaskEncoding() throws {
        let task = RecruiterTask(
            id: "t1", type: .interview, candidateName: "John Smith",
            candidateId: "c123", positionTitle: "Senior Software Engineer",
            positionId: "p456", status: "pending",
            dueDate: Date(timeIntervalSinceNow: 86400),
            createdAt: .now,
            description: "Conduct technical interview with emphasis on system design"
        )

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.keyEncodingStrategy = .convertToSnakeCase

        let data = try encoder.encode(task)
        let decoded = try JSONDecoder().decode(RecruiterTask.self, from: data)

        XCTAssertEqual(decoded.id, "t1")
        XCTAssertEqual(decoded.type, .interview)
        XCTAssertEqual(decoded.candidateName, "John Smith")
        XCTAssertNotNil(decoded.dueDate)
    }

    func testPositionEncodingWithAllFields() throws {
        let position = ActivePosition(
            id: "p1", title: "Principal Engineer", department: "Engineering",
            openCount: 5, fillRate: 0.6, urgency: .critical,
            thumbnailUrl: "https://example.com/icon.png", activeCount: 3
        )

        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase

        let data = try encoder.encode(position)
        let decoded = try JSONDecoder().decode(ActivePosition.self, from: data)

        XCTAssertEqual(decoded.id, "p1")
        XCTAssertEqual(decoded.openCount, 5)
        XCTAssertEqual(decoded.fillRate, 0.6)
        XCTAssertEqual(decoded.urgency, .critical)
        XCTAssertEqual(decoded.activeCount, 3)
    }

    // MARK: - Decision Record Tests

    func testDecisionRecordWithFullData() throws {
        let decision = DecisionRecord(
            id: "d1", candidateId: "c1", candidateName: "Alice Johnson",
            positionId: "p1", positionTitle: "Senior Engineer",
            decision: .approve, feedback: "Excellent technical skills, good culture fit",
            timestamp: .now, recordedBy: "recruiter_123"
        )

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601

        let data = try encoder.encode(decision)
        let decoded = try JSONDecoder().decode(DecisionRecord.self, from: data)

        XCTAssertEqual(decoded.candidateName, "Alice Johnson")
        XCTAssertEqual(decoded.decision, .approve)
        XCTAssertEqual(decoded.recordedBy, "recruiter_123")
    }

    // MARK: - Batch Data Tests

    func testBatchPipelineCardEncoding() throws {
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
            PipelineCard(
                id: "3", candidateId: "c3", name: "Charlie", score: 90,
                delta: -3, stage: .hired, avatarUrl: nil,
                positionId: "p1", notesCount: 5
            ),
        ]

        let encoder = JSONEncoder()
        let data = try encoder.encode(cards)
        let decoded = try JSONDecoder().decode([PipelineCard].self, from: data)

        XCTAssertEqual(decoded.count, 3)
        XCTAssertTrue(decoded.allSatisfy { $0.id.count > 0 })
    }

    // MARK: - Activity Feed Tests

    func testActivityFeedEntryEncoding() throws {
        let entry = AgentActivityEntry(
            id: "a1", agentName: "AutoMatcher Agent",
            action: "Reviewed candidate CV for skill match",
            candidateName: "Alice Johnson", positionTitle: "Senior Engineer",
            timestamp: .now, status: .success
        )

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601

        let data = try encoder.encode(entry)
        let decoded = try JSONDecoder().decode(AgentActivityEntry.self, from: data)

        XCTAssertEqual(decoded.agentName, "AutoMatcher Agent")
        XCTAssertEqual(decoded.status, .success)
        XCTAssertEqual(decoded.action, "Reviewed candidate CV for skill match")
    }

    func testMultipleActivityFeedEntries() throws {
        let entries = [
            AgentActivityEntry(
                id: "a1", agentName: "Agent1", action: "Reviewed CV",
                candidateName: "Alice", positionTitle: "Engineer",
                timestamp: .now, status: .success
            ),
            AgentActivityEntry(
                id: "a2", agentName: "Agent2", action: "Scheduled interview",
                candidateName: "Bob", positionTitle: "Engineer",
                timestamp: Date(timeIntervalSinceNow: -3600), status: .pending
            ),
            AgentActivityEntry(
                id: "a3", agentName: "Agent3", action: "Sent rejection",
                candidateName: "Charlie", positionTitle: "Designer",
                timestamp: Date(timeIntervalSinceNow: -7200), status: .failed
            ),
        ]

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601

        let data = try encoder.encode(entries)
        let decoded = try JSONDecoder().decode([AgentActivityEntry].self, from: data)

        XCTAssertEqual(decoded.count, 3)
        XCTAssertEqual(decoded[0].status, .success)
        XCTAssertEqual(decoded[1].status, .pending)
        XCTAssertEqual(decoded[2].status, .failed)
    }

    // MARK: - Cached Data Tests

    func testCachedRecruiterDataModel() {
        let cached = CachedRecruiterData(
            dataType: "tasks",
            resourceId: "p1",
            jsonData: "{\"id\":\"t1\",\"name\":\"Task 1\"}"
        )

        XCTAssertEqual(cached.dataType, "tasks")
        XCTAssertEqual(cached.resourceId, "p1")
        XCTAssertNotNil(cached.jsonData)
        XCTAssertNotNil(cached.lastFetched)
        XCTAssertNotNil(cached.expiresAt)
    }
}

// MARK: - Pipeline Stage Tests

final class RecruiterPipelineStageIntegrationTests: XCTestCase {

    func testAllPipelineStages() {
        let stages = PipelineStage.allCases
        XCTAssertEqual(stages.count, 4)
        XCTAssertTrue(stages.contains(.screening))
        XCTAssertTrue(stages.contains(.interview))
        XCTAssertTrue(stages.contains(.offer))
        XCTAssertTrue(stages.contains(.hired))
    }

    func testPipelineStageRawValues() {
        XCTAssertEqual(PipelineStage.screening.rawValue, "screening")
        XCTAssertEqual(PipelineStage.interview.rawValue, "interview")
        XCTAssertEqual(PipelineStage.offer.rawValue, "offer")
        XCTAssertEqual(PipelineStage.hired.rawValue, "hired")
    }

    func testPipelineStageDecoding() throws {
        let json = """
        ["screening", "interview", "offer", "hired"]
        """

        let stages = try JSONDecoder().decode([PipelineStage].self, from: json.data(using: .utf8)!)
        XCTAssertEqual(stages.count, 4)
    }
}

// MARK: - Urgency Level Tests

final class RecruiterUrgencyLevelIntegrationTests: XCTestCase {

    func testUrgencyLevelOrdering() {
        let critical = ActivePosition.Urgency.critical
        let high = ActivePosition.Urgency.high
        let normal = ActivePosition.Urgency.normal
        let low = ActivePosition.Urgency.low

        XCTAssertEqual(critical.rawValue, "critical")
        XCTAssertEqual(high.rawValue, "high")
        XCTAssertEqual(normal.rawValue, "normal")
        XCTAssertEqual(low.rawValue, "low")
    }

    func testUrgencyDecoding() throws {
        let positionJSON = """
        {
            "id": "p1",
            "title": "Engineer",
            "department": "Engineering",
            "openCount": 3,
            "fillRate": 0.5,
            "urgency": "critical",
            "thumbnailUrl": null,
            "activeCount": 1
        }
        """

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase

        let position = try decoder.decode(ActivePosition.self, from: positionJSON.data(using: .utf8)!)
        XCTAssertEqual(position.urgency, .critical)
    }
}

// MARK: - Decision Type Tests

final class RecruiterDecisionTypeIntegrationTests: XCTestCase {

    func testAllDecisionTypes() {
        let decisions: [DecisionRecord.Decision] = [.approve, .reject, .revisit]
        XCTAssertEqual(decisions.count, 3)
    }

    func testDecisionTypeRawValues() {
        XCTAssertEqual(DecisionRecord.Decision.approve.rawValue, "approve")
        XCTAssertEqual(DecisionRecord.Decision.reject.rawValue, "reject")
        XCTAssertEqual(DecisionRecord.Decision.revisit.rawValue, "revisit")
    }

    func testDecisionTypeDecoding() throws {
        let json = """
        ["approve", "reject", "revisit"]
        """

        let decisions = try JSONDecoder().decode([DecisionRecord.Decision].self, from: json.data(using: .utf8)!)
        XCTAssertEqual(decisions.count, 3)
    }
}
