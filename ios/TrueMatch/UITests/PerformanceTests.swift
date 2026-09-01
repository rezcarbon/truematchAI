import XCTest

final class PerformanceTests: XCTestCase {
    var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()

        // Set continuous performance measurement
        XCTAssert(!app.isRunning)
        app.launch()

        sleep(2)
    }

    override func tearDownWithError() throws {
        app.terminate()
    }

    // MARK: - App Launch Performance

    func testAppLaunchPerformance() throws {
        // This test measures the time to launch the app
        measure(metrics: [XCTOSSignpostMetric.applicationLaunch]) {
            app.launch()
        }
    }

    func testColdLaunchPerformance() throws {
        // Terminate and relaunch
        app.terminate()
        sleep(1)

        measure {
            app.launch()

            // Wait for dashboard to appear
            let dashboard = app.staticTexts["dashboard_title"]
            _ = dashboard.waitForExistence(timeout: 10)
        }
    }

    // MARK: - Jobs Tab Performance

    func testJobsScreenLoadPerformance() throws {
        measure {
            let jobsTab = app.tabBars.buttons["Jobs"]
            jobsTab.tap()

            // Wait for jobs to load
            let jobsList = app.collectionViews.firstMatch
            _ = jobsList.waitForExistence(timeout: 10)
        }
    }

    func testJobScrollingPerformance() throws {
        // Navigate to jobs
        let jobsTab = app.tabBars.buttons["Jobs"]
        jobsTab.tap()

        let jobsList = app.collectionViews.firstMatch
        _ = jobsList.waitForExistence(timeout: 10)

        measure {
            // Scroll through 20 job cards
            for _ in 0..<20 {
                jobsList.swipeUp()
            }
        }
    }

    func testJobDetailLoadPerformance() throws {
        // Navigate to jobs
        let jobsTab = app.tabBars.buttons["Jobs"]
        jobsTab.tap()

        let jobCard = app.cells.element(boundBy: 0)
        _ = jobCard.waitForExistence(timeout: 5)

        measure {
            jobCard.tap()

            // Wait for details to load
            let jobDetail = app.staticTexts["job_description"]
            _ = jobDetail.waitForExistence(timeout: 10)

            // Go back
            let backButton = app.navigationBars.buttons.element(boundBy: 0)
            if backButton.exists {
                backButton.tap()
            }
        }
    }

    // MARK: - Pipeline Performance

    func testPipelineLoadPerformance() throws {
        measure {
            let pipelineTab = app.tabBars.buttons["Pipeline"]
            pipelineTab.tap()

            // Wait for pipeline to load
            let pipelineView = app.staticTexts["pipeline_header"]
            _ = pipelineView.waitForExistence(timeout: 10)
        }
    }

    func testCandidateListScrollPerformance() throws {
        // Navigate to pipeline
        let pipelineTab = app.tabBars.buttons["Pipeline"]
        pipelineTab.tap()

        let candidateList = app.collectionViews.firstMatch
        _ = candidateList.waitForExistence(timeout: 5)

        measure {
            // Scroll through candidates
            for _ in 0..<15 {
                candidateList.swipeUp()
            }
        }
    }

    func testCandidateDetailLoadPerformance() throws {
        // Navigate to pipeline
        let pipelineTab = app.tabBars.buttons["Pipeline"]
        pipelineTab.tap()

        let candidate = app.cells.element(boundBy: 0)
        _ = candidate.waitForExistence(timeout: 5)

        measure {
            candidate.tap()

            // Wait for detail view
            let detailView = app.staticTexts["candidate_detail_header"]
            _ = detailView.waitForExistence(timeout: 10)

            // Go back
            let backButton = app.navigationBars.buttons.element(boundBy: 0)
            if backButton.exists {
                backButton.tap()
            }
        }
    }

    // MARK: - Memory Performance

    func testMemoryUsageNavigating() throws {
        measure(metrics: [XCTMemoryMetric()]) {
            // Navigate through tabs multiple times
            for _ in 0..<5 {
                let jobsTab = app.tabBars.buttons["Jobs"]
                jobsTab.tap()
                sleep(1)

                let profileTab = app.tabBars.buttons["Profile"]
                profileTab.tap()
                sleep(1)

                let pipelineTab = app.tabBars.buttons["Pipeline"]
                pipelineTab.tap()
                sleep(1)
            }
        }
    }

    func testMemoryLeakOnScrolling() throws {
        let jobsTab = app.tabBars.buttons["Jobs"]
        jobsTab.tap()

        let jobsList = app.collectionViews.firstMatch
        _ = jobsList.waitForExistence(timeout: 5)

        measure(metrics: [XCTMemoryMetric()]) {
            // Extended scrolling test
            for _ in 0..<50 {
                jobsList.swipeUp()
            }
        }
    }

    // MARK: - CPU Performance

    func testCPUUsageOnNavigation() throws {
        measure(metrics: [XCTCPUMetric()]) {
            let tabs = ["Jobs", "Profile", "Pipeline", "Coach"]

            for tab in tabs {
                let tabButton = app.tabBars.buttons[tab]
                if tabButton.exists {
                    tabButton.tap()
                    sleep(1)
                }
            }
        }
    }

    func testCPUUsageOnScrolling() throws {
        let jobsTab = app.tabBars.buttons["Jobs"]
        jobsTab.tap()

        let jobsList = app.collectionViews.firstMatch
        _ = jobsList.waitForExistence(timeout: 5)

        measure(metrics: [XCTCPUMetric()]) {
            for _ in 0..<30 {
                jobsList.swipeUp()
            }
        }
    }

    // MARK: - Animation Performance

    func testSwipeAnimationPerformance() throws {
        let jobsTab = app.tabBars.buttons["Jobs"]
        jobsTab.tap()

        let jobCard = app.collectionViews.cells.element(boundBy: 0)
        _ = jobCard.waitForExistence(timeout: 5)

        measure {
            for _ in 0..<20 {
                if jobCard.exists {
                    jobCard.swipeRight()
                }
                sleep(0.3)
            }
        }
    }

    // MARK: - Search Performance

    func testSearchPerformance() throws {
        let jobsTab = app.tabBars.buttons["Jobs"]
        jobsTab.tap()

        let searchField = app.searchFields["job_search"]
        _ = searchField.waitForExistence(timeout: 5)

        measure {
            searchField.tap()
            searchField.typeText("Engineer")

            // Wait for results
            sleep(2)

            // Clear search
            searchField.clearText()
        }
    }

    // MARK: - Rendering Performance

    func testFirstFrameRenderingPerformance() throws {
        measure(metrics: [XCTClockMetric()]) {
            let jobsTab = app.tabBars.buttons["Jobs"]
            jobsTab.tap()

            // Wait for first render
            let jobsList = app.collectionViews.firstMatch
            _ = jobsList.waitForExistence(timeout: 10)
        }
    }

    // MARK: - Startup Performance

    func testDashboardLoadPerformance() throws {
        // Go through login if needed
        let emailField = app.textFields["email_input"]

        if emailField.waitForExistence(timeout: 2) {
            emailField.tap()
            emailField.typeText("test@example.com")

            let passwordField = app.secureTextFields["password_input"]
            passwordField.tap()
            passwordField.typeText("password")

            let loginButton = app.buttons["login_button"]
            loginButton.tap()
        }

        measure {
            // Time to dashboard
            let dashboard = app.staticTexts["dashboard_title"]
            _ = dashboard.waitForExistence(timeout: 15)
        }
    }

    // MARK: - Network Performance

    func testAPIResponsePerformance() throws {
        let jobsTab = app.tabBars.buttons["Jobs"]
        jobsTab.tap()

        measure {
            // Fresh load of jobs
            let refreshButton = app.buttons["refresh_button"]
            if refreshButton.exists {
                refreshButton.tap()

                // Wait for data
                let jobsList = app.collectionViews.firstMatch
                _ = jobsList.waitForExistence(timeout: 15)
            }
        }
    }

    // MARK: - List Performance

    func testLargeListPerformance() throws {
        let pipelineTab = app.tabBars.buttons["Pipeline"]
        pipelineTab.tap()

        let candidateList = app.collectionViews.firstMatch
        _ = candidateList.waitForExistence(timeout: 5)

        measure {
            // Simulate scrolling through large list
            for _ in 0..<100 {
                candidateList.swipeUp()
            }
        }
    }

    // MARK: - Drag and Drop Performance

    func testDragDropPerformance() throws {
        let jobsTab = app.tabBars.buttons["Jobs"]
        jobsTab.tap()

        let jobCard = app.collectionViews.cells.element(boundBy: 0)
        _ = jobCard.waitForExistence(timeout: 5)

        measure {
            for _ in 0..<10 {
                if jobCard.exists {
                    jobCard.press(forDuration: 0.1, thenDragTo: app.staticTexts["favorites"])
                    sleep(0.5)
                }
            }
        }
    }

    // MARK: - Database Query Performance

    func testProfileLoadPerformance() throws {
        let profileTab = app.tabBars.buttons["Profile"]
        profileTab.tap()

        measure {
            let profileView = app.staticTexts["profile_header"]
            _ = profileView.waitForExistence(timeout: 10)
        }
    }

    // MARK: - Caching Performance

    func testCachedContentLoadPerformance() throws {
        // First load to populate cache
        let jobsTab = app.tabBars.buttons["Jobs"]
        jobsTab.tap()
        sleep(3)

        // Navigate away and back
        let profileTab = app.tabBars.buttons["Profile"]
        profileTab.tap()
        sleep(1)

        // Measure cached load
        measure {
            jobsTab.tap()
            let jobsList = app.collectionViews.firstMatch
            _ = jobsList.waitForExistence(timeout: 10)
        }
    }

    // MARK: - Concurrent Operations Performance

    func testConcurrentNavigationPerformance() throws {
        measure {
            for _ in 0..<5 {
                let jobsTab = app.tabBars.buttons["Jobs"]
                jobsTab.tap()
                sleep(0.5)

                let pipelineTab = app.tabBars.buttons["Pipeline"]
                pipelineTab.tap()
                sleep(0.5)
            }
        }
    }
}

// MARK: - UITextFieldExtension for testing

extension XCUIElement {
    func clearText() {
        guard let stringValue = value as? String else { return }
        let deleteString = String(repeating: XCUIKeyboardKey.delete.rawValue, count: stringValue.count)
        typeText(deleteString)
    }
}
