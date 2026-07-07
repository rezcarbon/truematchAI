import XCTest
@testable import TrueMatch

final class AssessmentResultsViewModelTests: XCTestCase {
    var viewModel: AssessmentResultsViewModel!
    var mockAPIClient: MockAPIClient!
    var mockAssessmentCache: MockAssessmentCache!

    override func setUp() {
        super.setUp()
        mockAPIClient = MockAPIClient()
        mockAssessmentCache = MockAssessmentCache()
        viewModel = AssessmentResultsViewModel(
            apiClient: mockAPIClient,
            assessmentCache: mockAssessmentCache
        )
    }

    override func tearDown() {
        viewModel = nil
        mockAPIClient = nil
        mockAssessmentCache = nil
        super.tearDown()
    }

    // MARK: - loadAssessment Tests

    func testLoadAssessmentSuccess() {
        // Arrange
        let assessmentID = "assessment123"
        let mockAssessment = mockAssessmentData(id: assessmentID)
        mockAPIClient.mockAssessmentResult = .success(mockAssessment)

        var loadedAssessment: AssessmentResult?
        var loadError: Error?

        // Act
        viewModel.loadAssessment(id: assessmentID) { result in
            switch result {
            case .success(let assessment):
                loadedAssessment = assessment
            case .failure(let error):
                loadError = error
            }
        }

        // Assert
        XCTAssertNil(loadError)
        XCTAssertNotNil(loadedAssessment)
        XCTAssertEqual(loadedAssessment?.id, assessmentID)
    }

    func testLoadAssessmentFromCache() {
        // Arrange
        let assessmentID = "assessment123"
        let cachedAssessment = mockAssessmentData(id: assessmentID)
        mockAssessmentCache.mockCachedAssessment = cachedAssessment

        var loadedAssessment: AssessmentResult?

        // Act
        viewModel.loadAssessment(id: assessmentID) { result in
            if case .success(let assessment) = result {
                loadedAssessment = assessment
            }
        }

        // Assert
        XCTAssertNotNil(loadedAssessment)
        XCTAssertTrue(mockAssessmentCache.getCacheCalled)
    }

    func testLoadAssessmentFailureHandling() {
        // Arrange
        let assessmentID = "assessment123"
        let mockError = NSError(domain: "test", code: 404, userInfo: nil)
        mockAPIClient.mockAssessmentResult = .failure(mockError)

        var errorReceived: Error?

        // Act
        viewModel.loadAssessment(id: assessmentID) { result in
            if case .failure(let error) = result {
                errorReceived = error
            }
        }

        // Assert
        XCTAssertNotNil(errorReceived)
    }

    // MARK: - computeDeltas Tests

    func testComputeDeltasWithPreviousAssessment() {
        // Arrange
        let currentAssessment = AssessmentResult(
            id: "curr",
            timestamp: Date(),
            scores: [
                AssessmentScore(category: "leadership", value: 0.85),
                AssessmentScore(category: "communication", value: 0.90)
            ]
        )

        let previousAssessment = AssessmentResult(
            id: "prev",
            timestamp: Date(timeIntervalSinceNow: -86400),
            scores: [
                AssessmentScore(category: "leadership", value: 0.75),
                AssessmentScore(category: "communication", value: 0.80)
            ]
        )

        // Act
        let deltas = viewModel.computeDeltas(
            current: currentAssessment,
            previous: previousAssessment
        )

        // Assert
        XCTAssertEqual(deltas.count, 2)
        XCTAssertEqual(deltas["leadership"], 0.10, accuracy: 0.01)
        XCTAssertEqual(deltas["communication"], 0.10, accuracy: 0.01)
    }

    func testComputeDeltasNegativeImprovement() {
        // Arrange
        let currentAssessment = AssessmentResult(
            id: "curr",
            timestamp: Date(),
            scores: [
                AssessmentScore(category: "teamwork", value: 0.70)
            ]
        )

        let previousAssessment = AssessmentResult(
            id: "prev",
            timestamp: Date(timeIntervalSinceNow: -86400),
            scores: [
                AssessmentScore(category: "teamwork", value: 0.80)
            ]
        )

        // Act
        let deltas = viewModel.computeDeltas(
            current: currentAssessment,
            previous: previousAssessment
        )

        // Assert
        XCTAssertEqual(deltas["teamwork"], -0.10, accuracy: 0.01)
    }

    func testComputeDeltasEmptyPrevious() {
        // Arrange
        let currentAssessment = AssessmentResult(
            id: "curr",
            timestamp: Date(),
            scores: [
                AssessmentScore(category: "skills", value: 0.88)
            ]
        )

        // Act
        let deltas = viewModel.computeDeltas(
            current: currentAssessment,
            previous: nil
        )

        // Assert
        XCTAssertTrue(deltas.isEmpty)
    }

    // MARK: - generateReport Tests

    func testGenerateReportIncludesScores() {
        // Arrange
        let assessment = mockAssessmentData(id: "report123")
        viewModel.currentAssessment = assessment

        // Act
        let report = viewModel.generateReport()

        // Assert
        XCTAssertNotNil(report)
        XCTAssertTrue(report.contains("leadership"))
        XCTAssertTrue(report.contains("communication"))
    }

    func testGenerateReportIncludesDeltas() {
        // Arrange
        let current = mockAssessmentData(id: "curr")
        let previous = mockAssessmentData(id: "prev")
        viewModel.currentAssessment = current
        viewModel.previousAssessment = previous

        // Act
        let report = viewModel.generateReport()

        // Assert
        XCTAssertNotNil(report)
        XCTAssertTrue(report.contains("improvement"))
    }

    func testGenerateReportFormatting() {
        // Arrange
        let assessment = mockAssessmentData(id: "format123")
        viewModel.currentAssessment = assessment

        // Act
        let report = viewModel.generateReport()

        // Assert
        XCTAssertTrue(report.contains("Assessment Report"))
        XCTAssertTrue(report.contains("Scores:"))
    }

    // MARK: - Helper Methods

    private func mockAssessmentData(id: String) -> AssessmentResult {
        return AssessmentResult(
            id: id,
            timestamp: Date(),
            scores: [
                AssessmentScore(category: "leadership", value: 0.85),
                AssessmentScore(category: "communication", value: 0.90),
                AssessmentScore(category: "teamwork", value: 0.80)
            ]
        )
    }
}
