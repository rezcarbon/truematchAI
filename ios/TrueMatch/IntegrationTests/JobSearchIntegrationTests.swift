import XCTest
@testable import TrueMatch

final class JobSearchIntegrationTests: XCTestCase {
    var jobSearchAPI: JobSearchAPI!
    var matchingEngine: MatchingEngine!
    var persistenceManager: PersistenceManager!
    var networkMonitor: NetworkMonitor!

    override func setUp() {
        super.setUp()
        networkMonitor = NetworkMonitor()
        jobSearchAPI = JobSearchAPI(networkMonitor: networkMonitor)
        matchingEngine = MatchingEngine()
        persistenceManager = PersistenceManager()
    }

    override func tearDown() {
        jobSearchAPI = nil
        matchingEngine = nil
        persistenceManager = nil
        networkMonitor = nil
        super.tearDown()
    }

    // MARK: - Load Jobs Tests

    func testLoadJobsWithFilters() {
        // Arrange
        let filters = JobFilters(
            location: "San Francisco, CA",
            industry: "Technology",
            minSalary: 120000,
            seniority: .mid
        )

        let expectation = XCTestExpectation(description: "load filtered jobs")

        // Act
        jobSearchAPI.loadJobs(filters: filters) { result in
            switch result {
            case .success(let jobs):
                XCTAssertNotNil(jobs)
                XCTAssertGreater(jobs.count, 0)
                // Verify filters applied
                for job in jobs {
                    XCTAssertTrue(
                        job.location.contains("San Francisco") || job.location.contains("CA")
                    )
                }
                expectation.fulfill()
            case .failure(let error):
                XCTFail("Failed to load jobs: \(error)")
            }
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)
    }

    func testLoadJobsDefaultFilters() {
        // Arrange
        let expectation = XCTestExpectation(description: "load default jobs")

        // Act
        jobSearchAPI.loadJobs { result in
            if case .success(let jobs) = result {
                XCTAssertGreater(jobs.count, 0)
                expectation.fulfill()
            }
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)
    }

    // MARK: - Match Scoring Tests

    func testComputeMatchScores() {
        // Arrange
        let userProfile = UserProfile(
            skills: ["iOS", "Swift", "REST APIs"],
            experience: 5,
            industries: ["Technology", "Finance"],
            seniority: .mid
        )

        let jobs = [
            Job(id: "1", title: "iOS Developer", requiredSkills: ["iOS", "Swift"]),
            Job(id: "2", title: "Backend Engineer", requiredSkills: ["Python", "Node.js"]),
            Job(id: "3", title: "Senior iOS Engineer", requiredSkills: ["iOS", "Swift", "REST APIs"])
        ]

        // Act
        let scores = matchingEngine.scoreJobs(jobs, against: userProfile)

        // Assert
        XCTAssertEqual(scores.count, jobs.count)
        XCTAssertGreater(scores[0], scores[1]) // iOS dev should score higher
        XCTAssertGreater(scores[2], scores[0]) // Senior role should score highest
    }

    func testMatchScoringConsistency() {
        // Arrange
        let profile = UserProfile(
            skills: ["Python", "Machine Learning"],
            experience: 3,
            industries: ["AI"],
            seniority: .junior
        )

        let job = Job(
            id: "ml_job",
            title: "ML Engineer",
            requiredSkills: ["Python", "Machine Learning"]
        )

        // Act
        let score1 = matchingEngine.scoreJob(job, against: profile)

        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            let score2 = self.matchingEngine.scoreJob(job, against: profile)

            // Assert
            XCTAssertEqual(score1, score2)
        }
    }

    // MARK: - Save Job Tests

    func testSaveJobLocally() {
        // Arrange
        let job = Job(
            id: "save_test_1",
            title: "Software Engineer",
            requiredSkills: []
        )

        let expectation = XCTestExpectation(description: "job saved")

        // Act
        persistenceManager.saveJob(job) { result in
            if case .success = result {
                expectation.fulfill()
            }
        }

        // Assert
        wait(for: [expectation], timeout: 5.0)

        let savedJob = persistenceManager.fetchJob(id: "save_test_1")
        XCTAssertNotNil(savedJob)
        XCTAssertEqual(savedJob?.title, "Software Engineer")
    }

    func testSaveMultipleJobs() {
        // Arrange
        let jobs = (0..<5).map { i in
            Job(id: "multi_save_\(i)", title: "Job \(i)", requiredSkills: [])
        }

        let expectation = XCTestExpectation(description: "jobs saved")
        expectation.expectedFulfillmentCount = jobs.count

        // Act
        for job in jobs {
            persistenceManager.saveJob(job) { result in
                if case .success = result {
                    expectation.fulfill()
                }
            }
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)

        for i in 0..<5 {
            let savedJob = persistenceManager.fetchJob(id: "multi_save_\(i)")
            XCTAssertNotNil(savedJob)
        }
    }

    func testUnsaveJob() {
        // Arrange
        let job = Job(id: "unsave_test", title: "Test Job", requiredSkills: [])

        let saveExpectation = XCTestExpectation(description: "save job")
        persistenceManager.saveJob(job) { _ in
            saveExpectation.fulfill()
        }
        wait(for: [saveExpectation], timeout: 5.0)

        let unsaveExpectation = XCTestExpectation(description: "unsave job")

        // Act
        persistenceManager.unsaveJob(id: "unsave_test") { result in
            if case .success = result {
                unsaveExpectation.fulfill()
            }
        }

        // Assert
        wait(for: [unsaveExpectation], timeout: 5.0)

        let savedJob = persistenceManager.fetchJob(id: "unsave_test")
        XCTAssertNil(savedJob)
    }

    // MARK: - Job Search Integration Tests

    func testSearchAndSaveWorkflow() {
        // Arrange
        let expectation = XCTestExpectation(description: "search and save workflow")

        // Act
        jobSearchAPI.loadJobs { [weak self] result in
            if case .success(let jobs) = result, let firstJob = jobs.first {
                self?.persistenceManager.saveJob(firstJob) { _ in
                    expectation.fulfill()
                }
            }
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)
    }

    func testFilteredSearchAndMatchScoring() {
        // Arrange
        let filters = JobFilters(
            location: "New York, NY",
            industry: "Finance",
            seniority: .senior
        )

        let userProfile = UserProfile(
            skills: ["Python", "Trading", "Financial Modeling"],
            experience: 8,
            industries: ["Finance"],
            seniority: .senior
        )

        let expectation = XCTestExpectation(description: "filter and score")

        // Act
        jobSearchAPI.loadJobs(filters: filters) { [weak self] result in
            if case .success(let jobs) = result {
                let scores = self?.matchingEngine.scoreJobs(jobs, against: userProfile) ?? []
                let sortedJobs = zip(jobs, scores)
                    .sorted { $0.1 > $1.1 }
                    .map { $0.0 }

                // Save top matches
                for job in sortedJobs.prefix(5) {
                    self?.persistenceManager.saveJob(job) { _ in }
                }

                expectation.fulfill()
            }
        }

        // Assert
        wait(for: [expectation], timeout: 15.0)
    }

    // MARK: - Offline Job Search Tests

    func testOfflineJobRetrieval() {
        // Arrange
        let job = Job(id: "offline_1", title: "Offline Test", requiredSkills: [])

        let saveExpectation = XCTestExpectation(description: "save for offline")
        persistenceManager.saveJob(job) { _ in
            saveExpectation.fulfill()
        }
        wait(for: [saveExpectation], timeout: 5.0)

        networkMonitor.simulateOffline()

        // Act
        let offlineJobs = persistenceManager.fetchAllJobs()

        // Assert
        XCTAssertGreater(offlineJobs.count, 0)
        XCTAssertTrue(offlineJobs.contains { $0.id == "offline_1" })
    }

    // MARK: - Performance Tests

    func testLoadJobsPerformance() {
        measure {
            let expectation = XCTestExpectation(description: "perf")
            jobSearchAPI.loadJobs { _ in
                expectation.fulfill()
            }
            wait(for: [expectation], timeout: 15.0)
        }
    }

    func testMatchScoringPerformance() {
        // Arrange
        let profile = UserProfile(
            skills: ["iOS", "Swift"],
            experience: 5,
            industries: ["Tech"],
            seniority: .mid
        )

        let jobs = (0..<100).map { i in
            Job(id: "\(i)", title: "Job \(i)", requiredSkills: [])
        }

        measure {
            _ = matchingEngine.scoreJobs(jobs, against: profile)
        }
    }

    func testSaveJobPerformance() {
        // Arrange
        let jobs = (0..<50).map { i in
            Job(id: "perf_\(i)", title: "Job \(i)", requiredSkills: [])
        }

        let expectation = XCTestExpectation(description: "perf save")
        expectation.expectedFulfillmentCount = jobs.count

        measure {
            for job in jobs {
                persistenceManager.saveJob(job) { _ in
                    expectation.fulfill()
                }
            }
            wait(for: [expectation], timeout: 30.0)
        }
    }
}
