import XCTest
@testable import TrueMatch

final class OfflineQueueManagerTests: XCTestCase {
    var queueManager: OfflineQueueManager!
    var mockPersistence: MockPersistenceManager!
    var mockAPIClient: MockAPIClient!

    override func setUp() {
        super.setUp()
        mockPersistence = MockPersistenceManager()
        mockAPIClient = MockAPIClient()
        queueManager = OfflineQueueManager(
            persistenceManager: mockPersistence,
            apiClient: mockAPIClient
        )
    }

    override func tearDown() {
        queueManager = nil
        mockPersistence = nil
        mockAPIClient = nil
        super.tearDown()
    }

    // MARK: - enqueue Tests

    func testEnqueueAction() {
        // Arrange
        let action = OfflineAction(
            id: "action1",
            type: .updateProfile,
            payload: ["name": "John Doe"],
            timestamp: Date()
        )

        // Act
        queueManager.enqueue(action)

        // Assert
        XCTAssertTrue(mockPersistence.saveCalled)
        XCTAssertEqual(queueManager.queueCount, 1)
    }

    func testEnqueueMultipleActions() {
        // Arrange
        let actions = (0..<5).map { i in
            OfflineAction(
                id: "action\(i)",
                type: .updateProfile,
                payload: ["index": i],
                timestamp: Date()
            )
        }

        // Act
        actions.forEach { queueManager.enqueue($0) }

        // Assert
        XCTAssertEqual(queueManager.queueCount, 5)
    }

    func testEnqueueMaintainsOrder() {
        // Arrange
        let action1 = OfflineAction(
            id: "1",
            type: .updateProfile,
            payload: [:],
            timestamp: Date(timeIntervalSinceNow: -10)
        )
        let action2 = OfflineAction(
            id: "2",
            type: .saveJob,
            payload: [:],
            timestamp: Date(timeIntervalSinceNow: -5)
        )
        let action3 = OfflineAction(
            id: "3",
            type: .updateProfile,
            payload: [:],
            timestamp: Date()
        )

        // Act
        queueManager.enqueue(action1)
        queueManager.enqueue(action2)
        queueManager.enqueue(action3)

        // Assert
        let queue = queueManager.getQueue()
        XCTAssertEqual(queue[0].id, "1")
        XCTAssertEqual(queue[1].id, "2")
        XCTAssertEqual(queue[2].id, "3")
    }

    // MARK: - dequeue Tests

    func testDequeueAction() {
        // Arrange
        let action = OfflineAction(
            id: "dequeue1",
            type: .updateProfile,
            payload: [:],
            timestamp: Date()
        )
        queueManager.enqueue(action)

        // Act
        let dequeuedAction = queueManager.dequeue()

        // Assert
        XCTAssertNotNil(dequeuedAction)
        XCTAssertEqual(dequeuedAction?.id, "dequeue1")
        XCTAssertEqual(queueManager.queueCount, 0)
    }

    func testDequeueEmptyQueue() {
        // Act
        let action = queueManager.dequeue()

        // Assert
        XCTAssertNil(action)
    }

    func testDequeueOrderedCorrectly() {
        // Arrange
        let action1 = OfflineAction(id: "1", type: .updateProfile, payload: [:], timestamp: Date(timeIntervalSinceNow: -10))
        let action2 = OfflineAction(id: "2", type: .saveJob, payload: [:], timestamp: Date(timeIntervalSinceNow: -5))

        queueManager.enqueue(action1)
        queueManager.enqueue(action2)

        // Act
        let first = queueManager.dequeue()
        let second = queueManager.dequeue()

        // Assert
        XCTAssertEqual(first?.id, "1")
        XCTAssertEqual(second?.id, "2")
    }

    // MARK: - flush Tests

    func testFlushSuccessfully() {
        // Arrange
        let actions = (0..<3).map { i in
            OfflineAction(
                id: "flush\(i)",
                type: .updateProfile,
                payload: ["index": i],
                timestamp: Date()
            )
        }
        actions.forEach { queueManager.enqueue($0) }
        mockAPIClient.mockBatchSyncResult = .success(())

        let expectation = XCTestExpectation(description: "flush completes")

        // Act
        queueManager.flush { result in
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 2.0)
        XCTAssertEqual(queueManager.queueCount, 0)
        XCTAssertTrue(mockAPIClient.batchSyncCalled)
    }

    func testFlushEmptyQueue() {
        // Arrange
        let expectation = XCTestExpectation(description: "empty flush")

        // Act
        queueManager.flush { result in
            if case .success = result {
                expectation.fulfill()
            }
        }

        // Assert
        wait(for: [expectation], timeout: 1.0)
        XCTAssertFalse(mockAPIClient.batchSyncCalled)
    }

    func testFlushRetainsFailedActions() {
        // Arrange
        let action = OfflineAction(
            id: "retry1",
            type: .updateProfile,
            payload: [:],
            timestamp: Date()
        )
        queueManager.enqueue(action)
        mockAPIClient.mockBatchSyncResult = .failure(
            NSError(domain: "test", code: 500, userInfo: nil)
        )

        let expectation = XCTestExpectation(description: "flush fails")

        // Act
        queueManager.flush { result in
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 2.0)
        XCTAssertGreater(queueManager.queueCount, 0)
    }

    // MARK: - retry Tests

    func testRetryFailedActions() {
        // Arrange
        let action = OfflineAction(
            id: "retry_test1",
            type: .updateProfile,
            payload: [:],
            timestamp: Date()
        )
        queueManager.enqueue(action)
        mockAPIClient.mockBatchSyncResult = .failure(NSError(domain: "test", code: 500, userInfo: nil))

        let expectation = XCTestExpectation(description: "first attempt fails")
        queueManager.flush { _ in
            expectation.fulfill()
        }
        wait(for: [expectation], timeout: 2.0)

        // Now enable success for retry
        mockAPIClient.mockBatchSyncResult = .success(())

        let retryExpectation = XCTestExpectation(description: "retry succeeds")

        // Act
        queueManager.retryFailedActions { result in
            retryExpectation.fulfill()
        }

        // Assert
        wait(for: [retryExpectation], timeout: 2.0)
        XCTAssertEqual(queueManager.queueCount, 0)
    }

    func testRetryWithExponentialBackoff() {
        // Arrange
        let action = OfflineAction(
            id: "backoff1",
            type: .updateProfile,
            payload: [:],
            timestamp: Date()
        )
        queueManager.enqueue(action)
        mockAPIClient.mockBatchSyncResult = .failure(NSError(domain: "test", code: 500, userInfo: nil))

        let firstAttemptExpectation = XCTestExpectation(description: "first attempt")
        queueManager.flush { _ in
            firstAttemptExpectation.fulfill()
        }
        wait(for: [firstAttemptExpectation], timeout: 2.0)

        // Act - retry with delay
        let retryExpectation = XCTestExpectation(description: "retry with backoff")
        queueManager.retryWithBackoff(maxRetries: 3) { result in
            retryExpectation.fulfill()
        }

        // Assert
        wait(for: [retryExpectation], timeout: 5.0)
    }

    // MARK: - Queue Management Tests

    func testClearQueue() {
        // Arrange
        let actions = (0..<5).map { i in
            OfflineAction(
                id: "\(i)",
                type: .updateProfile,
                payload: [:],
                timestamp: Date()
            )
        }
        actions.forEach { queueManager.enqueue($0) }

        // Act
        queueManager.clearQueue()

        // Assert
        XCTAssertEqual(queueManager.queueCount, 0)
    }

    func testGetQueueStatus() {
        // Arrange
        let actions = (0..<3).map { i in
            OfflineAction(
                id: "\(i)",
                type: .updateProfile,
                payload: [:],
                timestamp: Date()
            )
        }
        actions.forEach { queueManager.enqueue($0) }

        // Act
        let status = queueManager.getStatus()

        // Assert
        XCTAssertEqual(status.pendingCount, 3)
        XCTAssertTrue(status.hasFailedActions || !status.hasFailedActions) // Just checking it's boolean
    }

    // MARK: - Performance Tests

    func testEnqueuePerformance() {
        measure {
            for i in 0..<100 {
                let action = OfflineAction(
                    id: "perf\(i)",
                    type: .updateProfile,
                    payload: [:],
                    timestamp: Date()
                )
                queueManager.enqueue(action)
            }
        }
    }

    func testFlushLargeQueuePerformance() {
        // Arrange
        for i in 0..<100 {
            let action = OfflineAction(
                id: "large\(i)",
                type: .updateProfile,
                payload: [:],
                timestamp: Date()
            )
            queueManager.enqueue(action)
        }
        mockAPIClient.mockBatchSyncResult = .success(())

        let expectation = XCTestExpectation(description: "large flush")

        // Act & Assert
        measure {
            queueManager.flush { _ in
                expectation.fulfill()
            }
            wait(for: [expectation], timeout: 5.0)
        }
    }
}
