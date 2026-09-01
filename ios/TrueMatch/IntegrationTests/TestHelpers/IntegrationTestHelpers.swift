import Foundation
@testable import TrueMatch

// MARK: - Integration Test Base Class

class IntegrationTestBase {
    var apiClient: APIClient?
    var cacheManager: CacheManager?
    var offlineQueueManager: OfflineQueueManager?
    var networkMonitor: NetworkMonitor?
    var webSocketManager: WebSocketManager?

    func setupRealServices() {
        networkMonitor = NetworkMonitor()
        apiClient = APIClient(networkMonitor: networkMonitor!)
        cacheManager = CacheManager()
        offlineQueueManager = OfflineQueueManager()
        webSocketManager = WebSocketManager()
    }

    func teardownRealServices() {
        webSocketManager?.disconnect()
        cacheManager?.clearCache()
        offlineQueueManager?.clearQueue()
    }

    func waitForNetworkChange(timeout: TimeInterval = 5.0) {
        let expectation = XCTestExpectation(description: "network change")
        networkMonitor?.addConnectionChangeListener {
            expectation.fulfill()
        }
        // Will timeout if no change occurs
    }

    func simulateNetworkScenario(_ scenario: NetworkScenario) {
        switch scenario {
        case .offline:
            networkMonitor?.simulateOffline()
        case .online:
            networkMonitor?.simulateOnline()
        case .slowConnection:
            // Simulate slow network by adding delays
            break
        case .unreliable:
            // Simulate unreliable network with intermittent failures
            break
        }
    }

    enum NetworkScenario {
        case offline
        case online
        case slowConnection
        case unreliable
    }
}

// MARK: - Test Data Generators

class IntegrationTestDataGenerator {
    static func generateLargePipeline(size: Int = 100) -> PipelineData {
        let candidates = (0..<size).map { i in
            Candidate(
                id: "integration_candidate_\(i)",
                name: "Integration Test Candidate \(i)",
                status: CandidateStatus.allCases[i % CandidateStatus.allCases.count]
            )
        }
        return PipelineData(candidates: candidates, stats: PipelineStats(total: size, byStage: [:]))
    }

    static func generateConcurrentOperations(count: Int = 10) -> [OfflineOperation] {
        return (0..<count).map { i in
            OfflineOperation(
                id: "op_\(i)",
                type: "candidate_update",
                data: [
                    "candidateId": AnyCodable("candidate_\(i)"),
                    "status": AnyCodable("screening"),
                    "timestamp": AnyCodable(Date().timeIntervalSince1970)
                ]
            )
        }
    }

    static func generateChatConversation(messageCount: Int = 20) -> [ChatMessage] {
        var messages: [ChatMessage] = []
        var currentTime = Date()

        for i in 0..<messageCount {
            let sender = i % 2 == 0 ? "user" : "assistant"
            messages.append(
                ChatMessage(
                    id: "msg_\(i)",
                    sender: sender,
                    content: "Integration test message \(i)",
                    timestamp: currentTime
                )
            )
            currentTime.addTimeInterval(30) // Space out messages
        }

        return messages
    }
}

// MARK: - Async Test Utilities

class AsyncTestHelper {
    static func waitForCondition(
        _ condition: @escaping () -> Bool,
        timeout: TimeInterval = 5.0,
        checkInterval: TimeInterval = 0.1
    ) -> Bool {
        let deadline = Date().addingTimeInterval(timeout)

        while Date() < deadline {
            if condition() {
                return true
            }
            Thread.sleep(forTimeInterval: checkInterval)
        }

        return false
    }

    static func executeSequentially(
        _ operations: [(@escaping () -> Void) -> Void],
        completion: @escaping () -> Void
    ) {
        guard !operations.isEmpty else {
            completion()
            return
        }

        var remainingOps = operations
        let firstOp = remainingOps.removeFirst()

        firstOp {
            executeSequentially(remainingOps, completion: completion)
        }
    }

    static func executeConcurrently(
        _ operations: [(@escaping () -> Void) -> Void],
        completion: @escaping () -> Void
    ) {
        let group = DispatchGroup()

        for operation in operations {
            group.enter()
            operation {
                group.leave()
            }
        }

        group.notify(queue: .main, execute: completion)
    }
}

// MARK: - Network Simulation

class NetworkSimulator {
    var isSimulatingLatency = false
    var latencyMs: UInt32 = 100

    var isSimulatingFailure = false
    var failureRate: Double = 0.5 // 50% failure rate

    func addLatency(toOperation operation: @escaping () -> Void) {
        if isSimulatingLatency {
            DispatchQueue.global().asyncAfter(deadline: .now() + .milliseconds(Int(latencyMs))) {
                operation()
            }
        } else {
            operation()
        }
    }

    func shouldSimulateFailure() -> Bool {
        guard isSimulatingFailure else { return false }
        return Double.random(in: 0...1) < failureRate
    }

    func simulateSlowNetwork(latencyMs: UInt32 = 500) {
        isSimulatingLatency = true
        self.latencyMs = latencyMs
    }

    func simulateUnreliableNetwork(failureRate: Double = 0.3) {
        isSimulatingFailure = true
        self.failureRate = failureRate
    }

    func resetSimulation() {
        isSimulatingLatency = false
        isSimulatingFailure = false
    }
}

// MARK: - Data Consistency Checker

class DataConsistencyChecker {
    func validatePipelineConsistency(_ pipeline: PipelineData) -> [ConsistencyError] {
        var errors: [ConsistencyError] = []

        // Check for duplicate candidate IDs
        let ids = pipeline.candidates.map { $0.id }
        let uniqueIds = Set(ids)
        if ids.count != uniqueIds.count {
            errors.append(.duplicateIds)
        }

        // Check stats match actual count
        if pipeline.stats.total != pipeline.candidates.count {
            errors.append(.statsMismatch)
        }

        // Check all statuses are valid
        let invalidStatuses = pipeline.candidates.filter { candidate in
            !CandidateStatus.allCases.contains(candidate.status)
        }
        if !invalidStatuses.isEmpty {
            errors.append(.invalidStatus)
        }

        return errors
    }

    func validateChatHistory(_ messages: [ChatMessage]) -> [ConsistencyError] {
        var errors: [ConsistencyError] = []

        // Check messages are ordered
        for i in 0..<messages.count - 1 {
            if messages[i].timestamp > messages[i + 1].timestamp {
                errors.append(.messagesOutOfOrder)
                break
            }
        }

        // Check for empty messages
        let emptyMessages = messages.filter { $0.content.trimmingCharacters(in: .whitespaces).isEmpty }
        if !emptyMessages.isEmpty {
            errors.append(.emptyContent)
        }

        return errors
    }

    enum ConsistencyError {
        case duplicateIds
        case statsMismatch
        case invalidStatus
        case messagesOutOfOrder
        case emptyContent
        case unknownFormat
    }
}

// MARK: - Performance Measurement

class PerformanceMeasurer {
    private var startTime: CFAbsoluteTime = 0
    private var measurements: [String: [TimeInterval]] = [:]

    func startMeasurement() {
        startTime = CFAbsoluteTimeGetCurrent()
    }

    func endMeasurement(label: String) -> TimeInterval {
        let elapsed = CFAbsoluteTimeGetCurrent() - startTime
        if measurements[label] == nil {
            measurements[label] = []
        }
        measurements[label]?.append(elapsed)
        return elapsed
    }

    func getStatistics(for label: String) -> PerformanceStats? {
        guard let times = measurements[label], !times.isEmpty else { return nil }

        let sorted = times.sorted()
        let average = times.reduce(0, +) / Double(times.count)
        let median = times.count % 2 == 0
            ? (sorted[times.count / 2 - 1] + sorted[times.count / 2]) / 2
            : sorted[times.count / 2]

        return PerformanceStats(
            count: times.count,
            min: sorted.first ?? 0,
            max: sorted.last ?? 0,
            average: average,
            median: median
        )
    }

    struct PerformanceStats {
        let count: Int
        let min: TimeInterval
        let max: TimeInterval
        let average: TimeInterval
        let median: TimeInterval
    }
}

// MARK: - Mock Completion Handlers

class CompletionTracker {
    private(set) var completionCalls: [String: Int] = [:]

    func recordCompletion(for operation: String) {
        completionCalls[operation, default: 0] += 1
    }

    func getCompletionCount(for operation: String) -> Int {
        return completionCalls[operation] ?? 0
    }

    func resetTracking() {
        completionCalls.removeAll()
    }
}

// MARK: - State Validator

class StateValidator {
    func validateAppState(
        cacheValid: Bool,
        networkConnected: Bool,
        queueEmpty: Bool,
        webSocketConnected: Bool
    ) -> Bool {
        // Define valid state combinations
        if networkConnected {
            // Online: cache can be any state, queue should be empty
            return queueEmpty
        } else {
            // Offline: cache should be valid, queue state doesn't matter
            return cacheValid
        }
    }

    func getExpectedBehavior(
        networkState: NetworkState,
        dataAvailability: DataAvailability
    ) -> ExpectedBehavior {
        switch (networkState, dataAvailability) {
        case (.online, .cached):
            return .fetchAndUpdateCache
        case (.online, .notCached):
            return .fetchAndCache
        case (.offline, .cached):
            return .useCache
        case (.offline, .notCached):
            return .failWithError
        }
    }

    enum NetworkState {
        case online
        case offline
    }

    enum DataAvailability {
        case cached
        case notCached
    }

    enum ExpectedBehavior {
        case fetchAndUpdateCache
        case fetchAndCache
        case useCache
        case failWithError
    }
}
