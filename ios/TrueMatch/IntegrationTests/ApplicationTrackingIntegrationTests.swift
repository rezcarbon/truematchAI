import XCTest
@testable import TrueMatch

final class ApplicationTrackingIntegrationTests: XCTestCase {
    var applicationAPI: ApplicationAPI!
    var timelineManager: TimelineManager!
    var persistenceManager: PersistenceManager!
    var networkMonitor: NetworkMonitor!

    override func setUp() {
        super.setUp()
        networkMonitor = NetworkMonitor()
        applicationAPI = ApplicationAPI(networkMonitor: networkMonitor)
        timelineManager = TimelineManager()
        persistenceManager = PersistenceManager()
    }

    override func tearDown() {
        applicationAPI = nil
        timelineManager = nil
        persistenceManager = nil
        networkMonitor = nil
        super.tearDown()
    }

    // MARK: - Fetch Applications Tests

    func testFetchApplications() {
        // Arrange
        let expectation = XCTestExpectation(description: "fetch applications")

        // Act
        applicationAPI.fetchApplications { result in
            switch result {
            case .success(let applications):
                XCTAssertNotNil(applications)
                expectation.fulfill()
            case .failure(let error):
                XCTFail("Failed to fetch applications: \(error)")
            }
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)
    }

    func testFetchApplicationsByStatus() {
        // Arrange
        let status = ApplicationStatus.pending
        let expectation = XCTestExpectation(description: "fetch by status")

        // Act
        applicationAPI.fetchApplications(status: status) { result in
            if case .success(let applications) = result {
                for app in applications {
                    XCTAssertEqual(app.status, status)
                }
                expectation.fulfill()
            }
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)
    }

    func testFetchApplicationDetails() {
        // Arrange
        let applicationID = "app_123"
        let expectation = XCTestExpectation(description: "fetch details")

        // Act
        applicationAPI.fetchApplicationDetails(id: applicationID) { result in
            if case .success(let details) = result {
                XCTAssertEqual(details.id, applicationID)
                expectation.fulfill()
            }
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)
    }

    // MARK: - Timeline Tests

    func testBuildApplicationTimeline() {
        // Arrange
        let events = [
            TimelineEvent(
                id: "e1",
                timestamp: Date(timeIntervalSinceNow: -86400),
                type: .submitted,
                description: "Application submitted"
            ),
            TimelineEvent(
                id: "e2",
                timestamp: Date(timeIntervalSinceNow: -43200),
                type: .reviewed,
                description: "Application reviewed"
            ),
            TimelineEvent(
                id: "e3",
                timestamp: Date(),
                type: .interview,
                description: "Interview scheduled"
            )
        ]

        // Act
        let timeline = timelineManager.buildTimeline(from: events)

        // Assert
        XCTAssertEqual(timeline.count, 3)
        XCTAssertEqual(timeline[0].type, .submitted)
        XCTAssertEqual(timeline[1].type, .reviewed)
        XCTAssertEqual(timeline[2].type, .interview)
    }

    func testTimelineChronologicalOrder() {
        // Arrange
        let events = [
            TimelineEvent(
                id: "e3",
                timestamp: Date(),
                type: .offer,
                description: "Offer received"
            ),
            TimelineEvent(
                id: "e1",
                timestamp: Date(timeIntervalSinceNow: -86400),
                type: .submitted,
                description: "Submitted"
            ),
            TimelineEvent(
                id: "e2",
                timestamp: Date(timeIntervalSinceNow: -43200),
                type: .interview,
                description: "Interview"
            )
        ]

        // Act
        let timeline = timelineManager.buildTimeline(from: events)

        // Assert - verify chronological order despite random input order
        for i in 0..<(timeline.count - 1) {
            XCTAssertLessThanOrEqual(
                timeline[i].timestamp.timeIntervalSince1970,
                timeline[i + 1].timestamp.timeIntervalSince1970
            )
        }
    }

    func testTimelineStatusTransitions() {
        // Arrange
        let applicationID = "trans_app"
        let events = [
            TimelineEvent(id: "e1", timestamp: Date(timeIntervalSinceNow: -259200), type: .submitted, description: ""),
            TimelineEvent(id: "e2", timestamp: Date(timeIntervalSinceNow: -86400), type: .screening, description: ""),
            TimelineEvent(id: "e3", timestamp: Date(timeIntervalSinceNow: -43200), type: .interview, description: ""),
            TimelineEvent(id: "e4", timestamp: Date(), type: .offer, description: "")
        ]

        // Act
        let timeline = timelineManager.buildTimeline(from: events)

        // Assert
        XCTAssertEqual(timeline.count, 4)
        XCTAssertTrue(timeline[0].type == .submitted)
        XCTAssertTrue(timeline[timeline.count - 1].type == .offer)
    }

    // MARK: - Application Persistence Tests

    func testSaveApplication() {
        // Arrange
        let application = Application(
            id: "save_app_1",
            jobTitle: "Software Engineer",
            companyName: "Tech Corp",
            appliedDate: Date(),
            status: .pending
        )

        let expectation = XCTestExpectation(description: "application saved")

        // Act
        persistenceManager.saveApplication(application) { result in
            if case .success = result {
                expectation.fulfill()
            }
        }

        // Assert
        wait(for: [expectation], timeout: 5.0)

        let saved = persistenceManager.fetchApplication(id: "save_app_1")
        XCTAssertNotNil(saved)
        XCTAssertEqual(saved?.jobTitle, "Software Engineer")
    }

    func testUpdateApplicationStatus() {
        // Arrange
        let application = Application(
            id: "update_app",
            jobTitle: "Engineer",
            companyName: "Tech",
            appliedDate: Date(),
            status: .pending
        )

        let saveExpectation = XCTestExpectation(description: "save")
        persistenceManager.saveApplication(application) { _ in
            saveExpectation.fulfill()
        }
        wait(for: [saveExpectation], timeout: 5.0)

        let updateExpectation = XCTestExpectation(description: "update")

        // Act
        persistenceManager.updateApplicationStatus(
            id: "update_app",
            status: .interview
        ) { result in
            if case .success = result {
                updateExpectation.fulfill()
            }
        }

        // Assert
        wait(for: [updateExpectation], timeout: 5.0)

        let updated = persistenceManager.fetchApplication(id: "update_app")
        XCTAssertEqual(updated?.status, .interview)
    }

    func testFetchApplicationsByCompany() {
        // Arrange
        let company = "TechCorp"
        let apps = (0..<3).map { i in
            Application(
                id: "company_app_\(i)",
                jobTitle: "Role \(i)",
                companyName: company,
                appliedDate: Date(),
                status: .pending
            )
        }

        let saveExpectations = (0..<3).map { _ in XCTestExpectation(description: "save") }

        // Act
        for (index, app) in apps.enumerated() {
            persistenceManager.saveApplication(app) { _ in
                saveExpectations[index].fulfill()
            }
        }

        wait(for: saveExpectations, timeout: 10.0)

        // Assert
        let companyApps = persistenceManager.fetchApplications(company: company)
        XCTAssertEqual(companyApps.count, 3)
    }

    // MARK: - Integration Flow Tests

    func testCompleteApplicationTracking() {
        // Arrange
        let expectation = XCTestExpectation(description: "complete tracking")
        expectation.expectedFulfillmentCount = 3

        let applicationID = "flow_app"

        // Act
        // 1. Create and save application
        let application = Application(
            id: applicationID,
            jobTitle: "iOS Engineer",
            companyName: "Tech Company",
            appliedDate: Date(),
            status: .pending
        )

        persistenceManager.saveApplication(application) { _ in
            expectation.fulfill()
        }

        // 2. Update status to screening
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) { [weak self] in
            self?.persistenceManager.updateApplicationStatus(
                id: applicationID,
                status: .screening
            ) { _ in
                expectation.fulfill()
            }
        }

        // 3. Build and verify timeline
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) { [weak self] in
            self?.applicationAPI.fetchApplicationDetails(id: applicationID) { _ in
                expectation.fulfill()
            }
        }

        // Assert
        wait(for: [expectation], timeout: 15.0)
    }

    func testMultipleApplicationTracking() {
        // Arrange
        let companies = ["CompanyA", "CompanyB", "CompanyC"]
        let saveExpectations = (0..<3).map { _ in XCTestExpectation(description: "save") }

        // Act
        for (index, company) in companies.enumerated() {
            let app = Application(
                id: "multi_\(index)",
                jobTitle: "Role",
                companyName: company,
                appliedDate: Date(),
                status: .pending
            )
            persistenceManager.saveApplication(app) { _ in
                saveExpectations[index].fulfill()
            }
        }

        wait(for: saveExpectations, timeout: 10.0)

        // Assert
        for (index, company) in companies.enumerated() {
            let app = persistenceManager.fetchApplication(id: "multi_\(index)")
            XCTAssertEqual(app?.companyName, company)
        }
    }

    // MARK: - Offline Tracking Tests

    func testOfflineApplicationSaving() {
        // Arrange
        networkMonitor.simulateOffline()

        let application = Application(
            id: "offline_app",
            jobTitle: "Engineer",
            companyName: "Tech",
            appliedDate: Date(),
            status: .pending
        )

        let expectation = XCTestExpectation(description: "offline save")

        // Act
        persistenceManager.saveApplication(application) { result in
            if case .success = result {
                expectation.fulfill()
            }
        }

        // Assert
        wait(for: [expectation], timeout: 5.0)

        let saved = persistenceManager.fetchApplication(id: "offline_app")
        XCTAssertNotNil(saved)
    }

    // MARK: - Performance Tests

    func testFetchApplicationsPerformance() {
        measure {
            let expectation = XCTestExpectation(description: "perf")
            applicationAPI.fetchApplications { _ in
                expectation.fulfill()
            }
            wait(for: [expectation], timeout: 15.0)
        }
    }

    func testBuildLargeTimelinePerformance() {
        // Arrange
        let events = (0..<100).map { i in
            TimelineEvent(
                id: "\(i)",
                timestamp: Date(timeIntervalSince1970: Double(i)),
                type: .submitted,
                description: "Event \(i)"
            )
        }

        measure {
            _ = timelineManager.buildTimeline(from: events)
        }
    }

    func testSaveMultipleApplicationsPerformance() {
        // Arrange
        let applications = (0..<50).map { i in
            Application(
                id: "perf_\(i)",
                jobTitle: "Role",
                companyName: "Company",
                appliedDate: Date(),
                status: .pending
            )
        }

        let expectations = (0..<50).map { _ in XCTestExpectation(description: "save") }

        measure {
            for (index, app) in applications.enumerated() {
                persistenceManager.saveApplication(app) { _ in
                    expectations[index].fulfill()
                }
            }
            wait(for: expectations, timeout: 30.0)
        }
    }
}
