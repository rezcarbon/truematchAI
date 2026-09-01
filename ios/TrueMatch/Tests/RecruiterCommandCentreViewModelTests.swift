import XCTest
@testable import TrueMatch

final class RecruiterCommandCentreViewModelTests: XCTestCase {
    var viewModel: RecruiterCommandCentreViewModel!
    var mockAPIClient: MockAPIClient!
    var mockCacheManager: MockCacheManager!
    var mockNetworkMonitor: MockNetworkMonitor!

    override func setUp() {
        super.setUp()
        mockAPIClient = MockAPIClient()
        mockCacheManager = MockCacheManager()
        mockNetworkMonitor = MockNetworkMonitor()
        viewModel = RecruiterCommandCentreViewModel(
            apiClient: mockAPIClient,
            cacheManager: mockCacheManager,
            networkMonitor: mockNetworkMonitor
        )
    }

    override func tearDown() {
        viewModel = nil
        mockAPIClient = nil
        mockCacheManager = nil
        mockNetworkMonitor = nil
        super.tearDown()
    }

    // MARK: - loadData Tests

    func testLoadDataSuccess() {
        // Arrange
        let mockPipeline = TestDataBuilder.makePipelineData(candidateCount: 5)
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
        XCTAssertEqual(loadedPipeline?.candidates.count, 5)
        XCTAssertTrue(mockAPIClient.fetchPipelineCalled)
    }

    func testLoadDataFailure() {
        // Arrange
        let mockError = NSError(domain: "test", code: -1, userInfo: [NSLocalizedDescriptionKey: "Network error"])
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
        XCTAssertEqual((loadError as NSError?)?.code, -1)
    }

    func testLoadDataUsesCache() {
        // Arrange
        let cachedPipeline = TestDataBuilder.makePipelineData(candidateCount: 3)
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
        XCTAssertEqual(loadedPipeline?.candidates.count, 3)
    }

    func testLoadDataWithOfflineNetwork() {
        // Arrange
        mockNetworkMonitor.simulateOffline()
        let cachedPipeline = TestDataBuilder.makePipelineData(candidateCount: 2)
        mockCacheManager.mockCachedPipeline = cachedPipeline

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
        XCTAssertNotNil(loadedPipeline)
        XCTAssertNil(loadError)
    }

    // MARK: - refresh Tests

    func testRefreshUpdatesPipeline() {
        // Arrange
        let updatedPipeline = TestDataBuilder.makePipelineData(candidateCount: 7)
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
        let mockPipeline = TestDataBuilder.makePipelineData(candidateCount: 4)
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

    func testRefreshWithNetworkError() {
        // Arrange
        let networkError = NSError(domain: "network", code: 503, userInfo: nil)
        mockAPIClient.mockPipelineResult = .failure(networkError)

        var receivedError: Error?
        let expectation = XCTestExpectation(description: "refresh fails")

        // Act
        viewModel.refresh {
            expectation.fulfill()
        }

        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            receivedError = self.viewModel.lastError
        }

        // Assert
        wait(for: [expectation], timeout: 2.0)
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
        XCTAssertEqual(mockAPIClient.lastUpdatedCandidateID, candidateID)
        XCTAssertEqual(mockAPIClient.lastUpdatedStatus, newStatus)
    }

    func testAdvanceCandidateWithAllStatuses() {
        // Arrange
        let candidateID = "candidate_status_test"
        let statuses = CandidateStatus.allCases
        mockAPIClient.mockUpdateResult = .success(())

        for status in statuses {
            let expectation = XCTestExpectation(description: "advance to \(status)")

            // Act
            viewModel.advanceCandidate(id: candidateID, to: status) { _ in
                expectation.fulfill()
            }

            // Assert
            wait(for: [expectation], timeout: 2.0)
            XCTAssertEqual(mockAPIClient.lastUpdatedStatus, status)
        }
    }

    func testAdvanceCandidateFailureHandling() {
        // Arrange
        let candidateID = "candidate123"
        let mockError = NSError(domain: "test", code: 500, userInfo: [NSLocalizedDescriptionKey: "Server error"])
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
        XCTAssertEqual((errorReceived as NSError?)?.code, 500)
    }

    func testAdvanceCandidateOfflineQueue() {
        // Arrange
        mockNetworkMonitor.simulateOffline()
        let candidateID = "candidate456"
        mockAPIClient.mockUpdateResult = .success(())

        let expectation = XCTestExpectation(description: "candidate queued")

        // Act
        viewModel.advanceCandidate(id: candidateID, to: .screening) { result in
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 2.0)
        XCTAssertTrue(viewModel.isOfflineMode)
    }

    // MARK: - Filter and Search Tests

    func testFilterCandidatesByStatus() {
        // Arrange
        let pipeline = TestDataBuilder.makePipelineData(candidateCount: 10)
        mockAPIClient.mockPipelineResult = .success(pipeline)

        var loadedPipeline: PipelineData?

        // Act
        viewModel.loadData { result in
            if case .success(let data) = result {
                loadedPipeline = data
            }
        }

        let filtered = viewModel.filterCandidates(by: .interview, from: loadedPipeline ?? pipeline)

        // Assert
        XCTAssertTrue(filtered.allSatisfy { $0.status == .interview })
    }

    func testSearchCandidates() {
        // Arrange
        let candidates = [
            TestDataBuilder.makeCandidate(id: "1"),
            TestDataBuilder.makeCandidate(id: "2"),
            TestDataBuilder.makeCandidate(id: "3")
        ]
        let pipeline = PipelineData(candidates: candidates, stats: PipelineStats(total: 3, byStage: [:]))

        // Act
        let results = viewModel.searchCandidates("Test", in: pipeline)

        // Assert
        XCTAssertGreaterThan(results.count, 0)
    }

    // MARK: - Performance Tests

    func testLoadDataPerformance() {
        // Arrange
        let largePipeline = TestDataBuilder.makePipelineData(candidateCount: 1000)
        mockAPIClient.mockPipelineResult = .success(largePipeline)

        // Act & Assert
        measure {
            viewModel.loadData { _ in }
        }
    }

    func testAdvanceMultipleCandidatesPerformance() {
        // Arrange
        mockAPIClient.mockUpdateResult = .success(())

        let candidateUpdates = (0..<100).map { "candidate_\($0)" }
        let expectation = XCTestExpectation(description: "batch advance")
        expectation.expectedFulfillmentCount = 100

        // Act
        measure {
            for candidateID in candidateUpdates {
                viewModel.advanceCandidate(id: candidateID, to: .screening) { _ in
                    expectation.fulfill()
                }
            }

            wait(for: [expectation], timeout: 10.0)
        }
    }

    // MARK: - Helper Methods

    private func mockPipelineData() -> PipelineData {
        return TestDataBuilder.makePipelineData(candidateCount: 2)
    }
}
