import XCTest
@testable import TrueMatch

final class JobRecommendationsViewModelTests: XCTestCase {
    var viewModel: JobRecommendationsViewModel!
    var mockAPIClient: MockAPIClient!
    var mockPersistenceManager: MockPersistenceManager!

    override func setUp() {
        super.setUp()
        mockAPIClient = MockAPIClient()
        mockPersistenceManager = MockPersistenceManager()
        viewModel = JobRecommendationsViewModel(
            apiClient: mockAPIClient,
            persistenceManager: mockPersistenceManager
        )
    }

    override func tearDown() {
        viewModel = nil
        mockAPIClient = nil
        mockPersistenceManager = nil
        super.tearDown()
    }

    // MARK: - loadJobs Tests

    func testLoadJobsSuccess() {
        // Arrange
        let mockJobs = [
            JobRecommendation(id: "job1", title: "iOS Developer", matchScore: 0.95),
            JobRecommendation(id: "job2", title: "Senior Engineer", matchScore: 0.87)
        ]
        mockAPIClient.mockJobsResult = .success(mockJobs)

        var loadedJobs: [JobRecommendation]?
        var loadError: Error?

        // Act
        viewModel.loadJobs { result in
            switch result {
            case .success(let jobs):
                loadedJobs = jobs
            case .failure(let error):
                loadError = error
            }
        }

        // Assert
        XCTAssertNil(loadError)
        XCTAssertNotNil(loadedJobs)
        XCTAssertEqual(loadedJobs?.count, 2)
        XCTAssertEqual(loadedJobs?.first?.matchScore, 0.95)
    }

    func testLoadJobsSortedByMatchScore() {
        // Arrange
        let mockJobs = [
            JobRecommendation(id: "job1", title: "iOS Developer", matchScore: 0.75),
            JobRecommendation(id: "job2", title: "Senior Engineer", matchScore: 0.95),
            JobRecommendation(id: "job3", title: "Junior Dev", matchScore: 0.60)
        ]
        mockAPIClient.mockJobsResult = .success(mockJobs)

        var loadedJobs: [JobRecommendation]?

        // Act
        viewModel.loadJobs { result in
            if case .success(let jobs) = result {
                loadedJobs = jobs
            }
        }

        // Assert
        XCTAssertEqual(loadedJobs?.first?.matchScore, 0.95)
        XCTAssertEqual(loadedJobs?.last?.matchScore, 0.60)
    }

    func testLoadJobsFailureHandling() {
        // Arrange
        let mockError = NSError(domain: "test", code: -1, userInfo: nil)
        mockAPIClient.mockJobsResult = .failure(mockError)

        var errorReceived: Error?

        // Act
        viewModel.loadJobs { result in
            if case .failure(let error) = result {
                errorReceived = error
            }
        }

        // Assert
        XCTAssertNotNil(errorReceived)
    }

    // MARK: - handleSwipe Tests

    func testHandleSwipeRight() {
        // Arrange
        let jobID = "job1"
        let expectation = XCTestExpectation(description: "swipe handled")

        // Act
        viewModel.handleSwipe(jobID: jobID, direction: .right) {
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 1.0)
        XCTAssertTrue(mockAPIClient.recordSwipeCalled)
        XCTAssertEqual(mockAPIClient.lastSwipeDirection, .right)
    }

    func testHandleSwipeLeft() {
        // Arrange
        let jobID = "job2"
        let expectation = XCTestExpectation(description: "swipe handled")

        // Act
        viewModel.handleSwipe(jobID: jobID, direction: .left) {
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 1.0)
        XCTAssertTrue(mockAPIClient.recordSwipeCalled)
        XCTAssertEqual(mockAPIClient.lastSwipeDirection, .left)
    }

    func testSwipeResultsInUpdatedQueue() {
        // Arrange
        let initialJobs = [
            JobRecommendation(id: "job1", title: "Developer", matchScore: 0.9),
            JobRecommendation(id: "job2", title: "Engineer", matchScore: 0.85)
        ]
        viewModel.currentJobs = initialJobs

        let expectation = XCTestExpectation(description: "swipe updates queue")
        mockAPIClient.mockSwipeResult = .success(())

        // Act
        viewModel.handleSwipe(jobID: "job1", direction: .right) {
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 1.0)
        XCTAssertEqual(viewModel.currentJobs.count, initialJobs.count - 1)
    }

    // MARK: - saveJob Tests

    func testSaveJobSuccess() {
        // Arrange
        let jobID = "job1"
        mockPersistenceManager.mockSaveResult = .success(())

        var saveError: Error?
        let expectation = XCTestExpectation(description: "job saved")

        // Act
        viewModel.saveJob(jobID: jobID) { result in
            if case .failure(let error) = result {
                saveError = error
            }
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 1.0)
        XCTAssertNil(saveError)
        XCTAssertTrue(mockPersistenceManager.saveCalled)
    }

    func testSaveJobUpdatesLocalState() {
        // Arrange
        let jobID = "job1"
        mockPersistenceManager.mockSaveResult = .success(())

        let expectation = XCTestExpectation(description: "job saved")

        // Act
        viewModel.saveJob(jobID: jobID) { _ in
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 1.0)
        XCTAssertTrue(viewModel.savedJobs.contains(jobID))
    }

    func testSaveJobFailureHandling() {
        // Arrange
        let jobID = "job1"
        let mockError = NSError(domain: "test", code: 500, userInfo: nil)
        mockPersistenceManager.mockSaveResult = .failure(mockError)

        var errorReceived: Error?
        let expectation = XCTestExpectation(description: "save failed")

        // Act
        viewModel.saveJob(jobID: jobID) { result in
            if case .failure(let error) = result {
                errorReceived = error
            }
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 1.0)
        XCTAssertNotNil(errorReceived)
        XCTAssertFalse(viewModel.savedJobs.contains(jobID))
    }

    // MARK: - Performance Tests

    func testLoadJobsPerformance() {
        // Arrange
        let largeJobSet = (0..<100).map { i in
            JobRecommendation(
                id: "job\(i)",
                title: "Job \(i)",
                matchScore: Double.random(in: 0.5...1.0)
            )
        }
        mockAPIClient.mockJobsResult = .success(largeJobSet)

        measure {
            viewModel.loadJobs { _ in }
        }
    }
}
