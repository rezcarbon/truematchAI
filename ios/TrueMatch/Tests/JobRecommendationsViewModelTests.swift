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

    // MARK: - Batch Operations Tests

    func testHandleMultipleSwipesSequentially() {
        // Arrange
        let jobIDs = ["job1", "job2", "job3", "job4", "job5"]
        mockAPIClient.mockSwipeResult = .success(())

        let expectation = XCTestExpectation(description: "multiple swipes")
        expectation.expectedFulfillmentCount = jobIDs.count

        // Act
        for jobID in jobIDs {
            viewModel.handleSwipe(jobID: jobID, direction: .right) {
                expectation.fulfill()
            }
        }

        // Assert
        wait(for: [expectation], timeout: 5.0)
        XCTAssertEqual(mockAPIClient.recordSwipeCalled, true)
    }

    func testHandleSwipeWithNetworkError() {
        // Arrange
        let jobID = "job_error"
        let networkError = NSError(domain: "network", code: -1, userInfo: nil)
        mockAPIClient.mockSwipeResult = .failure(networkError)

        var receivedError: Error?
        let expectation = XCTestExpectation(description: "swipe with error")

        // Act
        viewModel.handleSwipe(jobID: jobID, direction: .left) {
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 2.0)
    }

    func testSwipeRightAddsToFavorites() {
        // Arrange
        let jobID = "job_favorite"
        mockAPIClient.mockSwipeResult = .success(())

        let expectation = XCTestExpectation(description: "swipe right")

        // Act
        viewModel.handleSwipe(jobID: jobID, direction: .right) {
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 1.0)
        XCTAssertEqual(mockAPIClient.lastSwipeDirection, .right)
    }

    func testSwipeLeftRemovesJob() {
        // Arrange
        let jobID = "job_reject"
        mockAPIClient.mockSwipeResult = .success(())

        let expectation = XCTestExpectation(description: "swipe left")

        // Act
        viewModel.handleSwipe(jobID: jobID, direction: .left) {
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 1.0)
        XCTAssertEqual(mockAPIClient.lastSwipeDirection, .left)
    }

    // MARK: - Job Details Tests

    func testJobDetailsAccuracy() {
        // Arrange
        let jobs = TestDataBuilder.makeJobRecommendations(count: 3)
        mockAPIClient.mockJobsResult = .success(jobs)

        var loadedJobs: [JobRecommendation]?

        // Act
        viewModel.loadJobs { result in
            if case .success(let jobs) = result {
                loadedJobs = jobs
            }
        }

        // Assert
        XCTAssertNotNil(loadedJobs)
        for (expected, actual) in zip(jobs, loadedJobs ?? []) {
            XCTAssertEqual(expected.id, actual.id)
            XCTAssertEqual(expected.title, actual.title)
        }
    }

    func testSaveMultipleJobs() {
        // Arrange
        let jobIDs = ["job1", "job2", "job3", "job4", "job5"]
        mockPersistenceManager.mockSaveResult = .success(())

        let expectation = XCTestExpectation(description: "save multiple jobs")
        expectation.expectedFulfillmentCount = jobIDs.count

        // Act
        for jobID in jobIDs {
            viewModel.saveJob(jobID: jobID) { _ in
                expectation.fulfill()
            }
        }

        // Assert
        wait(for: [expectation], timeout: 5.0)
        for jobID in jobIDs {
            XCTAssertTrue(viewModel.savedJobs.contains(jobID))
        }
    }

    func testUnsaveJob() {
        // Arrange
        let jobID = "job_to_unsave"
        mockPersistenceManager.mockSaveResult = .success(())

        let expectation1 = XCTestExpectation(description: "save job")
        let expectation2 = XCTestExpectation(description: "unsave job")

        // Act & Assert - Save first
        viewModel.saveJob(jobID: jobID) { _ in
            expectation1.fulfill()
        }

        wait(for: [expectation1], timeout: 1.0)
        XCTAssertTrue(viewModel.savedJobs.contains(jobID))

        // Act & Assert - Unsave
        viewModel.unsaveJob(jobID: jobID) { _ in
            expectation2.fulfill()
        }

        wait(for: [expectation2], timeout: 1.0)
        XCTAssertFalse(viewModel.savedJobs.contains(jobID))
    }

    // MARK: - Cache Tests

    func testLoadJobsUsesCache() {
        // Arrange
        let cachedJobs = TestDataBuilder.makeJobRecommendations(count: 5)
        mockPersistenceManager.mockLoadResult = .success(["jobs": cachedJobs])

        var loadedJobs: [JobRecommendation]?

        // Act
        viewModel.loadJobsFromCache { result in
            if case .success(let jobs) = result {
                loadedJobs = jobs
            }
        }

        // Assert
        XCTAssertNotNil(loadedJobs)
    }

    // MARK: - Data Validation Tests

    func testJobsAreSortedByScore() {
        // Arrange
        let unsortedJobs = [
            JobRecommendation(id: "job1", title: "Developer", matchScore: 0.70),
            JobRecommendation(id: "job2", title: "Engineer", matchScore: 0.95),
            JobRecommendation(id: "job3", title: "Lead", matchScore: 0.65),
            JobRecommendation(id: "job4", title: "Manager", matchScore: 0.88)
        ]
        mockAPIClient.mockJobsResult = .success(unsortedJobs)

        var loadedJobs: [JobRecommendation]?

        // Act
        viewModel.loadJobs { result in
            if case .success(let jobs) = result {
                loadedJobs = jobs
            }
        }

        // Assert
        guard let jobs = loadedJobs else { XCTFail("Jobs not loaded"); return }
        for i in 0..<jobs.count - 1 {
            XCTAssertGreaterThanOrEqual(jobs[i].matchScore, jobs[i + 1].matchScore)
        }
    }

    func testFilterJobsByMinimumScore() {
        // Arrange
        let jobs = [
            JobRecommendation(id: "job1", title: "Dev", matchScore: 0.95),
            JobRecommendation(id: "job2", title: "Eng", matchScore: 0.75),
            JobRecommendation(id: "job3", title: "Lead", matchScore: 0.55),
            JobRecommendation(id: "job4", title: "Mgr", matchScore: 0.85)
        ]

        // Act
        let filtered = viewModel.filterJobs(jobs, minScore: 0.80)

        // Assert
        XCTAssertEqual(filtered.count, 2)
        XCTAssertTrue(filtered.allSatisfy { $0.matchScore >= 0.80 })
    }

    // MARK: - Performance Tests

    func testLoadJobsPerformance() {
        // Arrange
        let largeJobSet = TestDataBuilder.makeJobRecommendations(count: 500)
        mockAPIClient.mockJobsResult = .success(largeJobSet)

        measure {
            viewModel.loadJobs { _ in }
        }
    }

    func testSwipePerformance() {
        // Arrange
        mockAPIClient.mockSwipeResult = .success(())

        let expectation = XCTestExpectation(description: "swipe performance")
        expectation.expectedFulfillmentCount = 100

        measure {
            for i in 0..<100 {
                viewModel.handleSwipe(jobID: "job_\(i)", direction: i % 2 == 0 ? .right : .left) {
                    expectation.fulfill()
                }
            }

            wait(for: [expectation], timeout: 10.0)
        }
    }

    func testSaveJobsPerformance() {
        // Arrange
        mockPersistenceManager.mockSaveResult = .success(())

        let expectation = XCTestExpectation(description: "save performance")
        expectation.expectedFulfillmentCount = 100

        measure {
            for i in 0..<100 {
                viewModel.saveJob(jobID: "job_\(i)") { _ in
                    expectation.fulfill()
                }
            }

            wait(for: [expectation], timeout: 10.0)
        }
    }
}
