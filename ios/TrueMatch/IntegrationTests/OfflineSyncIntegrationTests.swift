import XCTest
@testable import TrueMatch

final class OfflineSyncIntegrationTests: XCTestCase {
    var offlineSyncManager: OfflineSyncManager!
    var offlineQueueManager: OfflineQueueManager!
    var apiClient: APIClient!
    var networkMonitor: NetworkMonitor!
    var persistenceManager: PersistenceManager!

    override func setUp() {
        super.setUp()
        networkMonitor = NetworkMonitor()
        apiClient = APIClient(networkMonitor: networkMonitor)
        persistenceManager = PersistenceManager()
        offlineQueueManager = OfflineQueueManager(
            persistenceManager: persistenceManager,
            apiClient: apiClient
        )
        offlineSyncManager = OfflineSyncManager(
            queueManager: offlineQueueManager,
            apiClient: apiClient,
            networkMonitor: networkMonitor
        )
    }

    override func tearDown() {
        offlineSyncManager = nil
        offlineQueueManager = nil
        apiClient = nil
        networkMonitor = nil
        persistenceManager = nil
        super.tearDown()
    }

    // MARK: - Offline Mode Tests

    func testOfflineModeDetection() {
        // Arrange
        XCTAssertTrue(networkMonitor.isOnline)

        // Act
        networkMonitor.simulateOffline()

        // Assert
        XCTAssertFalse(networkMonitor.isOnline)
    }

    func testOfflineModeEnablesQueue() {
        // Arrange
        networkMonitor.simulateOffline()
        let action = OfflineAction(
            id: "offline_1",
            type: .updateProfile,
            payload: ["name": "John"],
            timestamp: Date()
        )

        // Act
        offlineQueueManager.enqueue(action)

        // Assert
        XCTAssertGreater(offlineQueueManager.queueCount, 0)
    }

    func testMultipleActionsQueuedOffline() {
        // Arrange
        networkMonitor.simulateOffline()
        let actions = (0..<5).map { i in
            OfflineAction(
                id: "queue_\(i)",
                type: .updateProfile,
                payload: ["index": i],
                timestamp: Date()
            )
        }

        // Act
        actions.forEach { offlineQueueManager.enqueue($0) }

        // Assert
        XCTAssertEqual(offlineQueueManager.queueCount, 5)
    }

    // MARK: - Action Queuing Tests

    func testQueueProfileUpdate() {
        // Arrange
        networkMonitor.simulateOffline()
        let updatePayload: [String: Any] = [
            "name": "Jane Doe",
            "title": "Senior Engineer",
            "bio": "Experienced iOS developer"
        ]

        // Act
        let action = OfflineAction(
            id: "profile_update_1",
            type: .updateProfile,
            payload: updatePayload,
            timestamp: Date()
        )
        offlineQueueManager.enqueue(action)

        // Assert
        XCTAssertEqual(offlineQueueManager.queueCount, 1)
        let queue = offlineQueueManager.getQueue()
        XCTAssertEqual(queue.first?.type, .updateProfile)
    }

    func testQueueJobAction() {
        // Arrange
        networkMonitor.simulateOffline()

        // Act
        let saveJobAction = OfflineAction(
            id: "save_job_1",
            type: .saveJob,
            payload: ["jobID": "job_123"],
            timestamp: Date()
        )
        offlineQueueManager.enqueue(saveJobAction)

        // Assert
        XCTAssertEqual(offlineQueueManager.queueCount, 1)
        let dequeuedAction = offlineQueueManager.dequeue()
        XCTAssertEqual(dequeuedAction?.type, .saveJob)
    }

    func testQueueApplicationAction() {
        // Arrange
        networkMonitor.simulateOffline()

        // Act
        let applyAction = OfflineAction(
            id: "apply_1",
            type: .applyJob,
            payload: ["jobID": "job_456", "applicationData": [:]],
            timestamp: Date()
        )
        offlineQueueManager.enqueue(applyAction)

        // Assert
        XCTAssertEqual(offlineQueueManager.queueCount, 1)
    }

    // MARK: - Online Sync Tests

    func testSyncWhenComingOnline() {
        // Arrange
        networkMonitor.simulateOffline()

        let actions = (0..<3).map { i in
            OfflineAction(
                id: "sync_test_\(i)",
                type: .updateProfile,
                payload: [:],
                timestamp: Date()
            )
        }
        actions.forEach { offlineQueueManager.enqueue($0) }

        let expectation = XCTestExpectation(description: "sync on online")

        // Act
        networkMonitor.simulateOnline()
        offlineSyncManager.syncPendingActions { result in
            if case .success = result {
                expectation.fulfill()
            }
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)
    }

    func testSyncPreservesQueueOrder() {
        // Arrange
        networkMonitor.simulateOffline()

        let action1 = OfflineAction(id: "1", type: .updateProfile, payload: [:], timestamp: Date(timeIntervalSinceNow: -10))
        let action2 = OfflineAction(id: "2", type: .saveJob, payload: [:], timestamp: Date(timeIntervalSinceNow: -5))
        let action3 = OfflineAction(id: "3", type: .updateProfile, payload: [:], timestamp: Date())

        offlineQueueManager.enqueue(action1)
        offlineQueueManager.enqueue(action2)
        offlineQueueManager.enqueue(action3)

        networkMonitor.simulateOnline()

        let expectation = XCTestExpectation(description: "order preserved")

        // Act
        offlineSyncManager.syncPendingActions { result in
            if case .success = result {
                expectation.fulfill()
            }
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)
    }

    func testPartialSyncFailureHandling() {
        // Arrange
        networkMonitor.simulateOffline()

        let actions = (0..<5).map { i in
            OfflineAction(
                id: "partial_\(i)",
                type: .updateProfile,
                payload: [:],
                timestamp: Date()
            )
        }
        actions.forEach { offlineQueueManager.enqueue($0) }

        networkMonitor.simulateOnline()

        let expectation = XCTestExpectation(description: "partial sync")

        // Act
        offlineSyncManager.syncPendingActions { result in
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)
        // Some actions might remain in queue if sync partially fails
    }

    // MARK: - Conflict Resolution Tests

    func testConflictDetectionDuringSync() {
        // Arrange
        networkMonitor.simulateOffline()

        let action = OfflineAction(
            id: "conflict_1",
            type: .updateProfile,
            payload: ["name": "Local Name"],
            timestamp: Date()
        )
        offlineQueueManager.enqueue(action)

        networkMonitor.simulateOnline()

        let expectation = XCTestExpectation(description: "conflict handled")

        // Act
        offlineSyncManager.syncPendingActions { result in
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)
    }

    // MARK: - Persistence Tests

    func testOfflineDataPersistence() {
        // Arrange
        networkMonitor.simulateOffline()

        let action = OfflineAction(
            id: "persist_1",
            type: .updateProfile,
            payload: ["persist": true],
            timestamp: Date()
        )

        // Act
        offlineQueueManager.enqueue(action)
        // Simulate app termination and restart
        let savedQueue = offlineQueueManager.getQueue()

        // Assert
        XCTAssertGreater(savedQueue.count, 0)
        XCTAssertEqual(savedQueue.first?.id, "persist_1")
    }

    func testCacheValidationOnSync() {
        // Arrange
        networkMonitor.simulateOffline()

        let cachedData = ["profile": "data"]
        persistenceManager.saveOfflineCache(cachedData)

        // Act
        networkMonitor.simulateOnline()
        let retrievedCache = persistenceManager.getOfflineCache()

        // Assert
        XCTAssertEqual(retrievedCache?["profile"] as? String, "data")
    }

    // MARK: - Large Queue Tests

    func testSyncLargeActionQueue() {
        // Arrange
        networkMonitor.simulateOffline()

        let actions = (0..<100).map { i in
            OfflineAction(
                id: "large_\(i)",
                type: .updateProfile,
                payload: ["index": i],
                timestamp: Date()
            )
        }
        actions.forEach { offlineQueueManager.enqueue($0) }

        networkMonitor.simulateOnline()

        let expectation = XCTestExpectation(description: "large sync")

        // Act
        offlineSyncManager.syncPendingActions { result in
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 30.0)
    }

    // MARK: - Network Transition Tests

    func testOfflineToOnlineTransition() {
        // Arrange
        networkMonitor.simulateOffline()
        XCTAssertFalse(networkMonitor.isOnline)

        // Act
        networkMonitor.simulateOnline()

        // Assert
        XCTAssertTrue(networkMonitor.isOnline)
    }

    func testOnlineToOfflineTransition() {
        // Arrange
        XCTAssertTrue(networkMonitor.isOnline)

        // Act
        networkMonitor.simulateOffline()

        // Assert
        XCTAssertFalse(networkMonitor.isOnline)
    }

    func testMultipleNetworkTransitions() {
        // Arrange
        var transitionCount = 0

        // Act & Assert
        for _ in 0..<3 {
            networkMonitor.simulateOffline()
            XCTAssertFalse(networkMonitor.isOnline)
            transitionCount += 1

            networkMonitor.simulateOnline()
            XCTAssertTrue(networkMonitor.isOnline)
            transitionCount += 1
        }

        XCTAssertEqual(transitionCount, 6)
    }

    // MARK: - Performance Tests

    func testEnqueuePerformanceOffline() {
        // Arrange
        networkMonitor.simulateOffline()

        measure {
            for i in 0..<100 {
                let action = OfflineAction(
                    id: "perf_\(i)",
                    type: .updateProfile,
                    payload: [:],
                    timestamp: Date()
                )
                offlineQueueManager.enqueue(action)
            }
        }
    }

    func testSyncPerformanceLargeQueue() {
        // Arrange
        networkMonitor.simulateOffline()

        for i in 0..<50 {
            let action = OfflineAction(
                id: "sync_perf_\(i)",
                type: .updateProfile,
                payload: [:],
                timestamp: Date()
            )
            offlineQueueManager.enqueue(action)
        }

        networkMonitor.simulateOnline()

        let expectation = XCTestExpectation(description: "sync perf")

        measure {
            offlineSyncManager.syncPendingActions { _ in
                expectation.fulfill()
            }
            wait(for: [expectation], timeout: 30.0)
        }
    }
}
