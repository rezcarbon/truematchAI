import XCTest
@testable import TrueMatch

final class RecruiterCommandCentreViewModelTests: XCTestCase {
    var viewModel: RecruiterCommandCentreViewModel!
    var mockAPIClient: MockAPIClient!
    var mockCacheManager: MockCacheManager!

    override func setUp() {
        super.setUp()
        mockAPIClient = MockAPIClient()
        mockCacheManager = MockCacheManager()
        viewModel = RecruiterCommandCentreViewModel(
            apiClient: mockAPIClient,
            cacheManager: mockCacheManager
        )
    }

    override func tearDown() {
        viewModel = nil
        mockAPIClient = nil
        mockCacheManager = nil
        super.tearDown()
    }

    // MARK: - loadData Tests

    func testLoadDataSuccess() {
        // Arrange
        let mockPipeline = mockPipelineData()
        mockAPIClient.mockPipelineResult = .success(mockPipeline)

        var loadedPipeline: PipelineData?
        var loadError: Error?

        // Act
        viewModel.loadData { result in
            switch result {
            case .success(let pipeline):
                loadedPipeline = pipeline
            case .failure(let error):
                loadError = error
            }
        }

        // Assert
        XCTAssertNil(loadError)
        XCTAssertNotNil(loadedPipeline)
        XCTAssertEqual(loadedPipeline?.candidates.count, mockPipeline.candidates.count)
    }

    func testLoadDataFailure() {
        // Arrange
        let mockError = NSError(domain: "test", code: -1, userInfo: nil)
        mockAPIClient.mockPipelineResult = .failure(mockError)

        var loadError: Error?

        // Act
        viewModel.loadData { result in
            if case .failure(let error) = result {
                loadError = error
            }
        }

        // Assert
        XCTAssertNotNil(loadError)
    }

    func testLoadDataUsesCache() {
        // Arrange
        let cachedPipeline = mockPipelineData()
        mockCacheManager.mockCachedPipeline = cachedPipeline

        var loadedPipeline: PipelineData?

        // Act
        viewModel.loadData { result in
            if case .success(let pipeline) = result {
                loadedPipeline = pipeline
            }
        }

        // Assert
        XCTAssertNotNil(loadedPipeline)
        XCTAssertTrue(mockCacheManager.getCacheCalled)
    }

    // MARK: - refresh Tests

    func testRefreshUpdatesPipeline() {
        // Arrange
        let updatedPipeline = mockPipelineData()
        mockAPIClient.mockPipelineResult = .success(updatedPipeline)

        let expectation = XCTestExpectation(description: "refresh completes")

        // Act
        viewModel.refresh {
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 2.0)
        XCTAssertTrue(mockAPIClient.fetchPipelineCalled)
    }

    func testRefreshCachesResult() {
        // Arrange
        let mockPipeline = mockPipelineData()
        mockAPIClient.mockPipelineResult = .success(mockPipeline)

        let expectation = XCTestExpectation(description: "refresh and cache")

        // Act
        viewModel.refresh {
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 2.0)
        XCTAssertTrue(mockCacheManager.setCacheCalled)
    }

    // MARK: - advanceCandidate Tests

    func testAdvanceCandidateSuccess() {
        // Arrange
        let candidateID = "candidate123"
        let newStatus = CandidateStatus.interview
        mockAPIClient.mockUpdateResult = .success(())

        var updateError: Error?
        let expectation = XCTestExpectation(description: "candidate advanced")

        // Act
        viewModel.advanceCandidate(id: candidateID, to: newStatus) { result in
            if case .failure(let error) = result {
                updateError = error
            }
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 2.0)
        XCTAssertNil(updateError)
        XCTAssertTrue(mockAPIClient.updateCandidateStatusCalled)
    }

    func testAdvanceCandidateUpdatesFeedback() {
        // Arrange
        let candidateID = "candidate123"
        let newStatus = CandidateStatus.offer
        mockAPIClient.mockUpdateResult = .success(())

        let expectation = XCTestExpectation(description: "candidate advanced")

        // Act
        viewModel.advanceCandidate(id: candidateID, to: newStatus) { _ in
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 2.0)
        XCTAssertTrue(viewModel.lastAdvancedCandidateID == candidateID)
    }

    func testAdvanceCandidateFailureHandling() {
        // Arrange
        let candidateID = "candidate123"
        let mockError = NSError(domain: "test", code: 500, userInfo: nil)
        mockAPIClient.mockUpdateResult = .failure(mockError)

        var errorReceived: Error?
        let expectation = XCTestExpectation(description: "advance failed")

        // Act
        viewModel.advanceCandidate(id: candidateID, to: .interview) { result in
            if case .failure(let error) = result {
                errorReceived = error
            }
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 2.0)
        XCTAssertNotNil(errorReceived)
    }

    // MARK: - Helper Methods

    private func mockPipelineData() -> PipelineData {
        return PipelineData(
            candidates: [
                Candidate(id: "1", name: "John Doe", status: .new),
                Candidate(id: "2", name: "Jane Smith", status: .screening)
            ],
            stats: PipelineStats(total: 2, byStage: [:])
        )
    }
}
