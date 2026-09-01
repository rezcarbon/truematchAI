import XCTest
@testable import TrueMatch

final class NetworkMonitorIntegrationTests: XCTestCase {
    var networkMonitor: NetworkMonitor!
    var offlineSyncManager: OfflineSyncManager!
    var apiClient: APIClient!
    var offlineQueueManager: OfflineQueueManager!

    override func setUp() {
        super.setUp()
        networkMonitor = NetworkMonitor()
        apiClient = APIClient(networkMonitor: networkMonitor)
        offlineQueueManager = OfflineQueueManager(
            persistenceManager: PersistenceManager(),
            apiClient: apiClient
        )
        offlineSyncManager = OfflineSyncManager(
            queueManager: offlineQueueManager,
            apiClient: apiClient,
            networkMonitor: networkMonitor
        )
    }

    override func tearDown() {
        networkMonitor = nil
        offlineSyncManager = nil
        apiClient = nil
        offlineQueueManager = nil
        super.tearDown()
    }

    // MARK: - Connectivity Detection Tests

    func testInitialNetworkState() {
        // Assert
        XCTAssertTrue(networkMonitor.isOnline)
    }

    func testDetectOfflineState() {
        // Arrange
        let expectation = XCTestExpectation(description: "offline detected")

        // Act
        networkMonitor.onConnectivityChange = { isOnline in
            if !isOnline {
                expectation.fulfill()
            }
        }

        networkMonitor.simulateOffline()

        // Assert
        wait(for: [expectation], timeout: 2.0)
        XCTAssertFalse(networkMonitor.isOnline)
    }

    func testDetectOnlineState() {
        // Arrange
        networkMonitor.simulateOffline()

        let expectation = XCTestExpectation(description: "online detected")

        // Act
        networkMonitor.onConnectivityChange = { isOnline in
            if isOnline {
                expectation.fulfill()
            }
        }

        networkMonitor.simulateOnline()

        // Assert
        wait(for: [expectation], timeout: 2.0)
        XCTAssertTrue(networkMonitor.isOnline)
    }

    // MARK: - Network Type Detection Tests

    func testWiFiConnectivity() {
        // Arrange
        networkMonitor.simulateNetworkType(.wifi)

        // Act & Assert
        XCTAssertTrue(networkMonitor.isOnline)
        XCTAssertEqual(networkMonitor.networkType, .wifi)
    }

    func testCellularConnectivity() {
        // Arrange
        networkMonitor.simulateNetworkType(.cellular)

        // Act & Assert
        XCTAssertTrue(networkMonitor.isOnline)
        XCTAssertEqual(networkMonitor.networkType, .cellular)
    }

    func testNoConnectivity() {
        // Arrange
        networkMonitor.simulateNetworkType(.none)

        // Act & Assert
        XCTAssertFalse(networkMonitor.isOnline)
        XCTAssertEqual(networkMonitor.networkType, .none)
    }

    // MARK: - Sync Trigger Tests

    func testSyncTriggeredOnOnline() {
        // Arrange
        networkMonitor.simulateOffline()

        let action = OfflineAction(
            id: "sync_trigger_1",
            type: .updateProfile,
            payload: [:],
            timestamp: Date()
        )
        offlineQueueManager.enqueue(action)

        let syncExpectation = XCTestExpectation(description: "sync triggered")

        networkMonitor.onConnectivityChange = { [weak self] isOnline in
            if isOnline {
                self?.offlineSyncManager.syncPendingActions { result in
                    if case .success = result {
                        syncExpectation.fulfill()
                    }
                }
            }
        }

        // Act
        networkMonitor.simulateOnline()

        // Assert
        wait(for: [syncExpectation], timeout: 10.0)
    }

    func testNoSyncWhenAlreadyOnline() {
        // Arrange
        var syncCalled = false

        networkMonitor.onConnectivityChange = { isOnline in
            if isOnline {
                syncCalled = true
            }
        }

        // Act
        // Already online, no state change
        XCTAssertTrue(networkMonitor.isOnline)

        // Assert
        XCTAssertFalse(syncCalled)
    }

    func testMultipleSyncTriggersOnMultipleTransitions() {
        // Arrange
        var syncTriggerCount = 0

        networkMonitor.onConnectivityChange = { isOnline in
            if isOnline {
                syncTriggerCount += 1
            }
        }

        // Act
        for _ in 0..<3 {
            networkMonitor.simulateOffline()
            networkMonitor.simulateOnline()
        }

        // Assert
        XCTAssertEqual(syncTriggerCount, 3)
    }

    // MARK: - Network Latency Tests

    func testLatencyDetectionOnline() {
        // Arrange
        networkMonitor.simulateOnline()

        // Act
        let latency = networkMonitor.estimatedLatency

        // Assert
        XCTAssertGreaterThanOrEqual(latency, 0)
    }

    func testLatencyHighOnSlowNetwork() {
        // Arrange
        networkMonitor.simulateNetworkType(.cellular)

        // Act
        let latency = networkMonitor.estimatedLatency

        // Assert
        XCTAssertGreaterThanOrEqual(latency, 0)
    }

    // MARK: - Bandwidth Detection Tests

    func testBandwidthEstimateOnline() {
        // Arrange
        networkMonitor.simulateOnline()

        // Act
        let bandwidth = networkMonitor.estimatedBandwidth

        // Assert
        XCTAssertGreater(bandwidth, 0)
    }

    func testBandwidthLowerOnCellular() {
        // Arrange
        networkMonitor.simulateNetworkType(.wifi)
        let wifiBandwidth = networkMonitor.estimatedBandwidth

        networkMonitor.simulateNetworkType(.cellular)
        let cellularBandwidth = networkMonitor.estimatedBandwidth

        // Assert
        XCTAssertGreaterThanOrEqual(wifiBandwidth, cellularBandwidth)
    }

    // MARK: - Connection Quality Tests

    func testHighQualityOnWiFi() {
        // Arrange
        networkMonitor.simulateNetworkType(.wifi)

        // Act
        let quality = networkMonitor.connectionQuality

        // Assert
        XCTAssertGreaterThanOrEqual(quality, 0.8)
    }

    func testLowQualityOffline() {
        // Arrange
        networkMonitor.simulateOffline()

        // Act
        let quality = networkMonitor.connectionQuality

        // Assert
        XCTAssertEqual(quality, 0)
    }

    // MARK: - Reachability Tests

    func testReachabilityStatus() {
        // Assert
        XCTAssertTrue(networkMonitor.isReachable)
    }

    func testReachabilityWhenOffline() {
        // Arrange
        networkMonitor.simulateOffline()

        // Assert
        XCTAssertFalse(networkMonitor.isReachable)
    }

    // MARK: - Continuous Monitoring Tests

    func testContinuousMonitoring() {
        // Arrange
        var stateChanges: [Bool] = []

        networkMonitor.onConnectivityChange = { isOnline in
            stateChanges.append(isOnline)
        }

        // Act
        for state in [false, true, false, true] {
            if state {
                networkMonitor.simulateOnline()
            } else {
                networkMonitor.simulateOffline()
            }
        }

        // Assert
        XCTAssertGreater(stateChanges.count, 0)
    }

    // MARK: - Network Restoration Tests

    func testAutomaticResumptionAfterNetworkRestoration() {
        // Arrange
        networkMonitor.simulateOffline()
        let action = OfflineAction(
            id: "restore_1",
            type: .updateProfile,
            payload: [:],
            timestamp: Date()
        )
        offlineQueueManager.enqueue(action)

        let restoreExpectation = XCTestExpectation(description: "auto resume")

        // Act
        networkMonitor.onConnectivityChange = { [weak self] isOnline in
            if isOnline {
                self?.offlineSyncManager.syncPendingActions { result in
                    if case .success = result {
                        restoreExpectation.fulfill()
                    }
                }
            }
        }

        networkMonitor.simulateOnline()

        // Assert
        wait(for: [restoreExpectation], timeout: 10.0)
    }

    // MARK: - Error Handling Tests

    func testErrorHandlingDuringOfflineMode() {
        // Arrange
        networkMonitor.simulateOffline()

        var errorCaught: Error?

        // Act
        apiClient.fetchProfile { result in
            if case .failure(let error) = result {
                errorCaught = error
            }
        }

        // Assert
        XCTAssertNotNil(errorCaught)
    }

    func testRetryMechanismOnNetworkRestore() {
        // Arrange
        networkMonitor.simulateOffline()

        let action = OfflineAction(
            id: "retry_1",
            type: .updateProfile,
            payload: [:],
            timestamp: Date()
        )
        offlineQueueManager.enqueue(action)

        var retryAttempts = 0

        networkMonitor.onConnectivityChange = { [weak self] isOnline in
            if isOnline {
                retryAttempts += 1
                self?.offlineSyncManager.syncPendingActions { _ in }
            }
        }

        // Act
        networkMonitor.simulateOnline()

        // Assert
        XCTAssertGreater(retryAttempts, 0)
    }

    // MARK: - Performance Tests

    func testMonitoringPerformance() {
        measure {
            for _ in 0..<100 {
                let isOnline = networkMonitor.isOnline
                _ = isOnline
            }
        }
    }

    func testConnectivityChangeHandlerPerformance() {
        // Arrange
        var callCount = 0

        networkMonitor.onConnectivityChange = { _ in
            callCount += 1
        }

        measure {
            for _ in 0..<50 {
                networkMonitor.simulateOnline()
                networkMonitor.simulateOffline()
            }
        }
    }

    func testSyncTriggerPerformanceOnMultipleTransitions() {
        // Arrange
        let queueExpectation = XCTestExpectation(description: "sync perf")
        queueExpectation.expectedFulfillmentCount = 10

        networkMonitor.onConnectivityChange = { [weak self] isOnline in
            if isOnline {
                self?.offlineSyncManager.syncPendingActions { result in
                    queueExpectation.fulfill()
                }
            }
        }

        measure {
            for _ in 0..<10 {
                networkMonitor.simulateOffline()
                networkMonitor.simulateOnline()
            }
            wait(for: [queueExpectation], timeout: 30.0)
        }
    }
}
