import XCTest
@testable import TrueMatch

final class RecruiterPipelineIntegrationTests: XCTestCase {
    var apiClient: APIClient!
    var webSocketManager: WebSocketManager!
    var cacheManager: CacheManager!
    var networkMonitor: NetworkMonitor!

    override func setUp() {
        super.setUp()
        networkMonitor = NetworkMonitor()
        apiClient = APIClient(networkMonitor: networkMonitor)
        webSocketManager = WebSocketManager()
        cacheManager = CacheManager()
    }

    override func tearDown() {
        apiClient = nil
        webSocketManager = nil
        cacheManager = nil
        networkMonitor = nil
        super.tearDown()
    }

    // MARK: - Fetch Pipeline Tests

    func testFetchPipelineSuccess() {
        // Arrange
        let expectation = XCTestExpectation(description: "fetch pipeline")

        // Act
        apiClient.fetchPipeline { result in
            switch result {
            case .success(let pipeline):
                XCTAssertNotNil(pipeline)
                XCTAssertGreaterThan(pipeline.candidates.count, 0)
                expectation.fulfill()
            case .failure(let error):
                XCTFail("Failed to fetch pipeline: \(error)")
            }
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)
    }

    func testFetchPipelineCaching() {
        // Arrange
        let expectation = XCTestExpectation(description: "pipeline cached")

        // Act
        apiClient.fetchPipeline { [weak self] result in
            if case .success(let pipeline) = result {
                self?.cacheManager.cachePipeline(pipeline)
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 10.0)

        // Assert
        let cachedPipeline = cacheManager.getCachedPipeline()
        XCTAssertNotNil(cachedPipeline)
    }

    // MARK: - Update Candidate Status Tests

    func testUpdateCandidateStatusSuccess() {
        // Arrange
        let candidateID = "test_candidate_123"
        let newStatus = CandidateStatus.interview
        let expectation = XCTestExpectation(description: "update status")

        // Act
        apiClient.updateCandidateStatus(
            candidateID: candidateID,
            status: newStatus
        ) { result in
            switch result {
            case .success:
                expectation.fulfill()
            case .failure(let error):
                XCTFail("Failed to update status: \(error)")
            }
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)
    }

    func testUpdateMultipleCandidatesSequentially() {
        // Arrange
        let candidateIDs = ["candidate1", "candidate2", "candidate3"]
        let statuses: [CandidateStatus] = [.screening, .interview, .offer]

        var updateCount = 0
        let expectation = XCTestExpectation(description: "update all candidates")
        expectation.expectedFulfillmentCount = candidateIDs.count

        // Act
        for (id, status) in zip(candidateIDs, statuses) {
            apiClient.updateCandidateStatus(candidateID: id, status: status) { result in
                if case .success = result {
                    updateCount += 1
                }
                expectation.fulfill()
            }
        }

        // Assert
        wait(for: [expectation], timeout: 15.0)
        XCTAssertEqual(updateCount, candidateIDs.count)
    }

    // MARK: - WebSocket Updates Tests

    func testWebSocketPipelineUpdate() {
        // Arrange
        let expectation = XCTestExpectation(description: "websocket update received")

        let statusChangeMessage = WebSocketMessage(
            type: .pipelineUpdate,
            data: [
                "candidateID": "ws_candidate_1",
                "newStatus": "interview",
                "timestamp": Date().timeIntervalSince1970
            ]
        )

        // Act
        webSocketManager.connect { [weak self] in
            self?.webSocketManager.send(statusChangeMessage)
        }

        webSocketManager.onMessageReceived = { message in
            if message.type == .pipelineUpdate {
                expectation.fulfill()
            }
        }

        // Assert
        wait(for: [expectation], timeout: 15.0)
    }

    func testWebSocketReconnection() {
        // Arrange
        let expectation = XCTestExpectation(description: "websocket reconnects")
        let maxReconnectAttempts = 3

        // Act
        webSocketManager.connect { }
        webSocketManager.simulateDisconnection()

        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            self.webSocketManager.connect { }
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 5.0)
        XCTAssertTrue(webSocketManager.isConnected)
    }

    // MARK: - Pipeline Sync Tests

    func testPipelineSyncWithOfflineMode() {
        // Arrange
        let expectation = XCTestExpectation(description: "offline pipeline sync")

        networkMonitor.simulateOffline()

        // Act
        apiClient.fetchPipeline { [weak self] result in
            if case .success = result {
                self?.cacheManager.cachePipeline(result)
            }
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 5.0)
    }

    func testPipelineUpdateConflictResolution() {
        // Arrange
        let candidateID = "conflict_candidate"
        let status1 = CandidateStatus.screening
        let status2 = CandidateStatus.interview

        let expectation = XCTestExpectation(description: "conflict resolved")
        expectation.expectedFulfillmentCount = 2

        var lastStatus: CandidateStatus?

        // Act
        // Simulate concurrent updates
        DispatchQueue.global().async {
            self.apiClient.updateCandidateStatus(
                candidateID: candidateID,
                status: status1
            ) { result in
                if case .success = result {
                    lastStatus = status1
                }
                expectation.fulfill()
            }
        }

        DispatchQueue.global().async {
            self.apiClient.updateCandidateStatus(
                candidateID: candidateID,
                status: status2
            ) { result in
                if case .success = result {
                    lastStatus = status2
                }
                expectation.fulfill()
            }
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)
        XCTAssertNotNil(lastStatus)
    }

    // MARK: - Performance Tests

    func testFetchPipelinePerformance() {
        measure {
            let expectation = XCTestExpectation(description: "performance test")
            apiClient.fetchPipeline { _ in
                expectation.fulfill()
            }
            wait(for: [expectation], timeout: 15.0)
        }
    }

    func testBatchUpdatePerformance() {
        // Arrange
        let updates = (0..<20).map { i in
            (id: "perf_candidate_\(i)", status: CandidateStatus.screening)
        }

        let expectation = XCTestExpectation(description: "batch update perf")
        expectation.expectedFulfillmentCount = updates.count

        measure {
            for update in updates {
                apiClient.updateCandidateStatus(
                    candidateID: update.id,
                    status: update.status
                ) { _ in
                    expectation.fulfill()
                }
            }
            wait(for: [expectation], timeout: 30.0)
        }
    }
}
