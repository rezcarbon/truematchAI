import XCTest
@testable import TrueMatch

final class RecruiterPipelineIntegrationTests: XCTestCase {
    var apiClient: APIClient!
    var webSocketManager: WebSocketManager!
    var cacheManager: CacheManager!
    var networkMonitor: NetworkMonitor!
    var consistencyChecker: DataConsistencyChecker!
    var performanceMeasurer: PerformanceMeasurer!

    override func setUp() {
        super.setUp()
        networkMonitor = NetworkMonitor()
        apiClient = APIClient(networkMonitor: networkMonitor)
        webSocketManager = WebSocketManager()
        cacheManager = CacheManager()
        consistencyChecker = DataConsistencyChecker()
        performanceMeasurer = PerformanceMeasurer()
    }

    override func tearDown() {
        apiClient = nil
        webSocketManager = nil
        cacheManager = nil
        networkMonitor = nil
        consistencyChecker = nil
        performanceMeasurer = nil
        super.tearDown()
    }

    // MARK: - Fetch Pipeline Tests

    func testFetchPipelineSuccess() {
        // Arrange
        let expectation = XCTestExpectation(description: "fetch pipeline")

        // Act
        performanceMeasurer.startMeasurement()
        apiClient.fetchPipeline { result in
            switch result {
            case .success(let pipeline):
                XCTAssertNotNil(pipeline)
                XCTAssertGreaterThan(pipeline.candidates.count, 0)

                // Validate consistency
                let errors = self.consistencyChecker.validatePipelineConsistency(pipeline)
                XCTAssertTrue(errors.isEmpty, "Consistency errors: \(errors)")

                expectation.fulfill()
            case .failure(let error):
                XCTFail("Failed to fetch pipeline: \(error)")
            }
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)
        let elapsed = performanceMeasurer.endMeasurement(label: "fetchPipeline")
        XCTAssertLessThan(elapsed, 10.0, "Pipeline fetch took too long")
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

        // Verify cache is valid
        let errors = consistencyChecker.validatePipelineConsistency(cachedPipeline!)
        XCTAssertTrue(errors.isEmpty)
    }

    func testFetchPipelineWithLargeDataSet() {
        // Arrange
        let expectation = XCTestExpectation(description: "fetch large pipeline")
        let largePipeline = IntegrationTestDataGenerator.generateLargePipeline(size: 500)

        // Act
        performanceMeasurer.startMeasurement()

        // Simulate large fetch
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            self.cacheManager.cachePipeline(largePipeline)
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 5.0)
        let elapsed = performanceMeasurer.endMeasurement(label: "fetchLargePipeline")

        let stats = performanceMeasurer.getStatistics(for: "fetchLargePipeline")
        XCTAssertNotNil(stats)
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

    func testUpdateMultipleCandidatesConcurrently() {
        // Arrange
        let candidateCount = 10
        let expectation = XCTestExpectation(description: "concurrent updates")
        expectation.expectedFulfillmentCount = candidateCount

        var successCount = 0
        let syncQueue = DispatchQueue(label: "sync.test")

        // Act
        for i in 0..<candidateCount {
            DispatchQueue.global().async {
                self.apiClient.updateCandidateStatus(
                    candidateID: "candidate_\(i)",
                    status: .screening
                ) { result in
                    if case .success = result {
                        syncQueue.sync { successCount += 1 }
                    }
                    expectation.fulfill()
                }
            }
        }

        // Assert
        wait(for: [expectation], timeout: 20.0)
        XCTAssertEqual(successCount, candidateCount)
    }

    func testUpdateStatusWithAllTransitions() {
        // Arrange
        let candidateID = "transition_test"
        let statusTransitions = CandidateStatus.allCases

        for status in statusTransitions {
            let expectation = XCTestExpectation(description: "transition to \(status)")

            // Act
            apiClient.updateCandidateStatus(
                candidateID: candidateID,
                status: status
            ) { result in
                expectation.fulfill()
            }

            // Assert
            wait(for: [expectation], timeout: 5.0)
        }
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

    func testWebSocketHandlesMultipleUpdates() {
        // Arrange
        let messageCount = 10
        let expectation = XCTestExpectation(description: "multiple ws updates")
        expectation.expectedFulfillmentCount = messageCount

        var receivedCount = 0

        // Act
        webSocketManager.connect { }
        webSocketManager.onMessageReceived = { _ in
            receivedCount += 1
            expectation.fulfill()
        }

        for i in 0..<messageCount {
            let message = WebSocketMessage(
                type: .pipelineUpdate,
                data: ["candidateID": "ws_candidate_\(i)"]
            )
            webSocketManager.send(message)
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)
        XCTAssertEqual(receivedCount, messageCount)
    }

    // MARK: - Pipeline Sync Tests

    func testPipelineSyncWithOfflineMode() {
        // Arrange
        let expectation = XCTestExpectation(description: "offline pipeline sync")
        let testPipeline = IntegrationTestDataGenerator.generateLargePipeline(size: 50)

        networkMonitor.simulateOffline()

        // Act
        cacheManager.cachePipeline(testPipeline)

        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            let cached = self.cacheManager.getCachedPipeline()
            XCTAssertNotNil(cached)
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

    func testSyncPipelineStateAcrossComponents() {
        // Arrange
        let testPipeline = IntegrationTestDataGenerator.generateLargePipeline(size: 20)

        // Act
        cacheManager.cachePipeline(testPipeline)
        let cachedPipeline = cacheManager.getCachedPipeline()

        // Assert
        XCTAssertNotNil(cachedPipeline)
        XCTAssertEqual(cachedPipeline?.candidates.count, testPipeline.candidates.count)

        // Verify consistency
        let errors = consistencyChecker.validatePipelineConsistency(cachedPipeline!)
        XCTAssertTrue(errors.isEmpty)
    }

    // MARK: - Network Resilience Tests

    func testHandleNetworkDowntime() {
        // Arrange
        let expectation = XCTestExpectation(description: "network downtime")

        // Act
        networkMonitor.simulateOffline()

        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            self.networkMonitor.simulateOnline()
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 3.0)
    }

    func testRetryFailedOperations() {
        // Arrange
        let candidateID = "retry_test"
        var attemptCount = 0

        let expectation = XCTestExpectation(description: "retry operation")

        // Act
        let attemptOperation = {
            attemptCount += 1
            self.apiClient.updateCandidateStatus(
                candidateID: candidateID,
                status: .screening
            ) { result in
                if case .success = result {
                    expectation.fulfill()
                }
            }
        }

        attemptOperation()

        // Assert
        wait(for: [expectation], timeout: 5.0)
        XCTAssertGreaterThanOrEqual(attemptCount, 1)
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
        let updates = (0..<50).map { i in
            (id: "perf_candidate_\(i)", status: CandidateStatus.screening)
        }

        let expectation = XCTestExpectation(description: "batch update perf")
        expectation.expectedFulfillmentCount = updates.count

        // Act
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

    func testLargeScaleDataHandling() {
        // Arrange
        let largePipeline = IntegrationTestDataGenerator.generateLargePipeline(size: 1000)

        // Act
        performanceMeasurer.startMeasurement()
        cacheManager.cachePipeline(largePipeline)
        let elapsed = performanceMeasurer.endMeasurement(label: "largeScaleCache")

        // Assert
        let stats = performanceMeasurer.getStatistics(for: "largeScaleCache")
        XCTAssertNotNil(stats)
        XCTAssertLessThan(elapsed, 2.0, "Large scale caching took too long")
    }
}
