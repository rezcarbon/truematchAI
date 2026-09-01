import Foundation

/// Global test configuration
struct TestConfiguration {
    /// Test timeouts
    static let defaultTimeout: TimeInterval = 5.0
    static let longTimeout: TimeInterval = 15.0
    static let veryLongTimeout: TimeInterval = 30.0

    /// Performance thresholds (in seconds)
    static let performanceThresholds = PerformanceThresholds()

    /// Test data
    static let testDataConfig = TestDataConfig()

    /// Network simulation
    static let networkConfig = NetworkConfig()

    struct PerformanceThresholds {
        let loginTime: TimeInterval = 15.0
        let pipelineLoadTime: TimeInterval = 10.0
        let candidateDetailLoadTime: TimeInterval = 5.0
        let swipeResponseTime: TimeInterval = 1.0
        let messageResponseTime: TimeInterval = 5.0
        let batchOperationTime: TimeInterval = 2.0 // per operation
    }

    struct TestDataConfig {
        let candidateDataSize: Int = 100
        let jobDataSize: Int = 500
        let messageHistorySize: Int = 100
        let largeDatasetSize: Int = 1000
    }

    struct NetworkConfig {
        let slowNetworkLatencyMs: UInt32 = 500
        let unreliableNetworkFailureRate: Double = 0.3
        let connectionLossRecoveryTimeout: TimeInterval = 10.0
    }
}

/// Environment variables for testing
enum TestEnvironment: String {
    case unit = "UNIT_TESTS"
    case integration = "INTEGRATION_TESTS"
    case e2e = "E2E_TESTS"

    static var current: TestEnvironment {
        if CommandLine.arguments.contains("UNIT_TESTING") {
            return .unit
        } else if CommandLine.arguments.contains("INTEGRATION_TESTING") {
            return .integration
        } else if CommandLine.arguments.contains("UI_TESTING") {
            return .e2e
        }
        return .unit
    }
}

/// Test result tracking
class TestResultsCollector {
    private static let shared = TestResultsCollector()

    private(set) var results: [TestResult] = []

    func recordResult(
        name: String,
        category: String,
        duration: TimeInterval,
        status: TestStatus,
        coverage: Double? = nil
    ) {
        let result = TestResult(
            name: name,
            category: category,
            duration: duration,
            status: status,
            timestamp: Date(),
            coverage: coverage
        )
        results.append(result)
    }

    func getStatistics() -> TestStatistics {
        let passed = results.filter { $0.status == .passed }.count
        let failed = results.filter { $0.status == .failed }.count
        let skipped = results.filter { $0.status == .skipped }.count
        let totalDuration = results.map { $0.duration }.reduce(0, +)
        let avgCoverage = results.compactMap { $0.coverage }.isEmpty
            ? 0.0
            : results.compactMap { $0.coverage }.reduce(0, +) / Double(results.compactMap { $0.coverage }.count)

        return TestStatistics(
            totalTests: results.count,
            passedTests: passed,
            failedTests: failed,
            skippedTests: skipped,
            totalDuration: totalDuration,
            averageCoverage: avgCoverage
        )
    }

    struct TestResult {
        let name: String
        let category: String
        let duration: TimeInterval
        let status: TestStatus
        let timestamp: Date
        let coverage: Double?
    }

    struct TestStatistics {
        let totalTests: Int
        let passedTests: Int
        let failedTests: Int
        let skippedTests: Int
        let totalDuration: TimeInterval
        let averageCoverage: Double
    }
}

enum TestStatus {
    case passed
    case failed
    case skipped
}

/// Coverage tracking
struct CoverageTracker {
    static let shared = CoverageTracker()

    private(set) var coverage: [String: Double] = [:]

    mutating func recordCoverage(file: String, percentage: Double) {
        coverage[file] = percentage
    }

    func getTotalCoverage() -> Double {
        guard !coverage.isEmpty else { return 0.0 }
        return coverage.values.reduce(0, +) / Double(coverage.count)
    }

    func getCoverageReport() -> String {
        var report = "Coverage Report\n"
        report += "===============\n\n"

        for (file, percentage) in coverage.sorted(by: { $0.key < $1.key }) {
            report += "\(file): \(String(format: "%.1f", percentage))%\n"
        }

        report += "\nTotal Coverage: \(String(format: "%.1f", getTotalCoverage()))%\n"
        return report
    }
}

/// Mock configuration for different test scenarios
struct MockConfiguration {
    static let standard = MockConfiguration(
        shouldFailRequests: false,
        failureRate: 0.0,
        latencyMs: 0
    )

    static let slowNetwork = MockConfiguration(
        shouldFailRequests: false,
        failureRate: 0.0,
        latencyMs: 500
    )

    static let unreliableNetwork = MockConfiguration(
        shouldFailRequests: true,
        failureRate: 0.3,
        latencyMs: 200
    )

    static let offline = MockConfiguration(
        shouldFailRequests: true,
        failureRate: 1.0,
        latencyMs: 0
    )

    let shouldFailRequests: Bool
    let failureRate: Double
    let latencyMs: UInt32
}
