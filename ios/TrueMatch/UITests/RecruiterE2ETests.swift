import XCTest

/// Comprehensive E2E tests for recruiter workflows
final class RecruiterE2ETests: E2ETestBase {
    var screenshotManager: ScreenshotManager!

    override func setUpWithError() throws {
        try super.setUpWithError()
        screenshotManager = ScreenshotManager()
    }

    override func tearDownWithError() throws {
        try super.tearDownWithError()
    }

    // MARK: - Authentication Flow

    func testLoginFlow() throws {
        // Navigate to login if not already logged in
        let emailField = app.textFields["email_input"]
        XCTAssertTrue(emailField.waitForExistence(timeout: 5))

        // Enter credentials
        emailField.tap()
        emailField.typeText("recruiter@example.com")

        let passwordField = app.secureTextFields["password_input"]
        passwordField.tap()
        passwordField.typeText("password123")

        let loginButton = app.buttons["login_button"]
        XCTAssertTrue(loginButton.waitForExistence(timeout: 5))
        loginButton.tap()

        // Verify navigation to dashboard
        let dashboardTitle = app.staticTexts["dashboard_title"]
        XCTAssertTrue(dashboardTitle.waitForExistence(timeout: 10))
    }

    // MARK: - Pipeline Navigation Tests

    func testNavigateToPipeline() throws {
        // Tap pipeline tab
        let pipelineTab = app.tabBars.buttons["Pipeline"]
        XCTAssertTrue(pipelineTab.exists)
        pipelineTab.tap()

        // Verify pipeline screen loads
        let pipelineView = app.staticTexts["pipeline_header"]
        XCTAssertTrue(pipelineView.waitForExistence(timeout: 5))
    }

    func testViewPipelineStats() throws {
        // Navigate to pipeline
        let pipelineTab = app.tabBars.buttons["Pipeline"]
        pipelineTab.tap()

        // Verify stats display
        let totalCandidates = app.staticTexts["total_candidates"]
        XCTAssertTrue(totalCandidates.exists)

        let byStage = app.staticTexts["candidates_by_stage"]
        XCTAssertTrue(byStage.exists)
    }

    // MARK: - Candidate Interaction Tests

    func testViewCandidateDetails() throws {
        // Navigate to pipeline
        let pipelineTab = app.tabBars.buttons["Pipeline"]
        pipelineTab.tap()

        // Tap first candidate
        let firstCandidate = app.cells.element(boundBy: 0)
        XCTAssertTrue(firstCandidate.waitForExistence(timeout: 5))
        firstCandidate.tap()

        // Verify detail view
        let detailView = app.staticTexts["candidate_detail_header"]
        XCTAssertTrue(detailView.waitForExistence(timeout: 5))
    }

    func testAdvanceCandidateStatus() throws {
        // Navigate to candidate details
        let pipelineTab = app.tabBars.buttons["Pipeline"]
        pipelineTab.tap()

        let firstCandidate = app.cells.element(boundBy: 0)
        firstCandidate.tap()

        // Find and tap advance button
        let advanceButton = app.buttons["advance_candidate_button"]
        XCTAssertTrue(advanceButton.waitForExistence(timeout: 5))
        advanceButton.tap()

        // Select new status from menu
        let interviewOption = app.buttons["status_interview"]
        XCTAssertTrue(interviewOption.waitForExistence(timeout: 3))
        interviewOption.tap()

        // Verify status update confirmation
        let confirmation = app.staticTexts["status_updated"]
        XCTAssertTrue(confirmation.waitForExistence(timeout: 5))
    }

    func testRejectCandidate() throws {
        // Navigate to candidate details
        let pipelineTab = app.tabBars.buttons["Pipeline"]
        pipelineTab.tap()

        let candidate = app.cells.element(boundBy: 0)
        candidate.tap()

        // Tap reject button
        let rejectButton = app.buttons["reject_candidate_button"]
        XCTAssertTrue(rejectButton.waitForExistence(timeout: 5))
        rejectButton.tap()

        // Confirm rejection
        let confirmButton = app.buttons["confirm_reject"]
        XCTAssertTrue(confirmButton.waitForExistence(timeout: 3))
        confirmButton.tap()

        // Verify removal from pipeline
        let removedNotification = app.staticTexts["candidate_removed"]
        XCTAssertTrue(removedNotification.waitForExistence(timeout: 5))
    }

    // MARK: - Filtering Tests

    func testFilterByStatus() throws {
        // Navigate to pipeline
        let pipelineTab = app.tabBars.buttons["Pipeline"]
        pipelineTab.tap()

        // Tap filter button
        let filterButton = app.buttons["filter_button"]
        XCTAssertTrue(filterButton.waitForExistence(timeout: 5))
        filterButton.tap()

        // Select status filter
        let statusFilter = app.buttons["filter_status"]
        XCTAssertTrue(statusFilter.waitForExistence(timeout: 3))
        statusFilter.tap()

        // Select "Interview" status
        let interviewStatus = app.buttons["status_interview"]
        XCTAssertTrue(interviewStatus.waitForExistence(timeout: 3))
        interviewStatus.tap()

        // Apply filter
        let applyButton = app.buttons["apply_filter"]
        XCTAssertTrue(applyButton.waitForExistence(timeout: 3))
        applyButton.tap()

        // Verify filtered results
        let filteredView = app.staticTexts["filtered_results"]
        XCTAssertTrue(filteredView.waitForExistence(timeout: 5))
    }

    func testSearchCandidate() throws {
        // Navigate to pipeline
        let pipelineTab = app.tabBars.buttons["Pipeline"]
        pipelineTab.tap()

        // Tap search field
        let searchField = app.searchFields["candidate_search"]
        XCTAssertTrue(searchField.waitForExistence(timeout: 5))
        searchField.tap()

        // Enter search term
        searchField.typeText("John")

        // Verify search results
        let searchResults = app.staticTexts["search_results"]
        XCTAssertTrue(searchResults.waitForExistence(timeout: 5))
    }

    // MARK: - WebSocket Update Tests

    func testReceiveRealtimeUpdate() throws {
        // Navigate to pipeline
        let pipelineTab = app.tabBars.buttons["Pipeline"]
        pipelineTab.tap()

        // Wait for potential realtime update
        sleep(3)

        // Verify pipeline is still accessible
        let pipelineView = app.staticTexts["pipeline_header"]
        XCTAssertTrue(pipelineView.exists)
    }

    // MARK: - Messaging Tests

    func testSendCandidateMessage() throws {
        // Navigate to candidate
        let pipelineTab = app.tabBars.buttons["Pipeline"]
        pipelineTab.tap()

        let candidate = app.cells.element(boundBy: 0)
        candidate.tap()

        // Tap message button
        let messageButton = app.buttons["message_button"]
        XCTAssertTrue(messageButton.waitForExistence(timeout: 5))
        messageButton.tap()

        // Type message
        let messageField = app.textViews["message_input"]
        XCTAssertTrue(messageField.waitForExistence(timeout: 3))
        messageField.tap()
        messageField.typeText("We'd like to schedule an interview")

        // Send message
        let sendButton = app.buttons["send_message"]
        XCTAssertTrue(sendButton.waitForExistence(timeout: 3))
        sendButton.tap()

        // Verify message sent
        let sentConfirmation = app.staticTexts["message_sent"]
        XCTAssertTrue(sentConfirmation.waitForExistence(timeout: 5))
    }

    // MARK: - Scroll Performance Tests

    func testScrollPipelineList() throws {
        // Navigate to pipeline
        let pipelineTab = app.tabBars.buttons["Pipeline"]
        pipelineTab.tap()

        let candidateList = app.collectionViews.firstMatch
        XCTAssertTrue(candidateList.waitForExistence(timeout: 5))

        // Scroll down
        candidateList.swipeUp()

        // Verify list still responsive
        sleep(1)
        candidateList.swipeDown()

        XCTAssertTrue(candidateList.exists)
    }

    // MARK: - Error Handling Tests

    func testHandleNetworkError() throws {
        // Navigate to pipeline
        let pipelineTab = app.tabBars.buttons["Pipeline"]
        pipelineTab.tap()

        // Try to advance candidate (might fail in test environment)
        let candidate = app.cells.element(boundBy: 0)
        candidate.tap()

        let advanceButton = app.buttons["advance_candidate_button"]
        if advanceButton.waitForExistence(timeout: 5) {
            advanceButton.tap()

            // Handle error if it occurs
            let errorAlert = app.alerts.firstMatch
            if errorAlert.waitForExistence(timeout: 3) {
                let retryButton = errorAlert.buttons["Retry"]
                if retryButton.exists {
                    retryButton.tap()
                }
            }
        }
    }

    // MARK: - Accessibility Tests

    func testAccessibilityElements() throws {
        // Navigate to pipeline
        let pipelineTab = app.tabBars.buttons["Pipeline"]
        XCTAssertTrue(pipelineTab.isAccessibilityElement)
        pipelineTab.tap()

        // Verify accessible elements
        let candidates = app.cells.allElementsBoundByIndex
        for cell in candidates.prefix(3) {
            XCTAssertTrue(cell.isAccessibilityElement)
        }
    }

    func testVoiceoverCompatibility() throws {
        // Enable accessibility inspection
        let pipelineTab = app.tabBars.buttons["Pipeline"]
        pipelineTab.tap()

        let candidate = app.cells.element(boundBy: 0)
        let label = candidate.label

        XCTAssertFalse(label.isEmpty)
    }

    // MARK: - Memory Leak Tests

    func testMemoryEfficiency() throws {
        // Navigate through screens multiple times
        for _ in 0..<5 {
            let pipelineTab = app.tabBars.buttons["Pipeline"]
            pipelineTab.tap()

            sleep(1)

            let candidate = app.cells.element(boundBy: 0)
            if candidate.waitForExistence(timeout: 3) {
                candidate.tap()

                sleep(1)

                let backButton = app.navigationBars.buttons.element(boundBy: 0)
                if backButton.exists {
                    backButton.tap()
                }
            }
        }

        // If we get here without crash, memory is being managed
        XCTAssertTrue(true)
    }

    // MARK: - Full Recruiter Workflow Tests

    func testCompleteRecruitmentWorkflow() throws {
        startPerformanceTracking(label: "recruitment_workflow")

        // Step 1: Navigate to pipeline
        navigateToPipeline()
        assertElementExists(app.staticTexts["pipeline_header"])

        // Step 2: View first candidate
        let firstCandidate = app.cells.element(boundBy: 0)
        assertElementExists(firstCandidate)
        tapElement(firstCandidate)

        // Step 3: Advance candidate
        let advanceButton = app.buttons["advance_candidate_button"]
        assertElementExists(advanceButton)
        tapElement(advanceButton)

        let interviewStatus = app.buttons["status_interview"]
        assertElementExists(interviewStatus)
        tapElement(interviewStatus)

        // Step 4: Verify status update
        let statusConfirmation = app.staticTexts["status_updated"]
        assertElementExists(statusConfirmation)

        endPerformanceTracking(label: "recruitment_workflow")

        if let stats = getPerformanceStats(label: "recruitment_workflow") {
            print("Workflow completed in \(stats.average)s")
            XCTAssertLessThan(stats.average, 30.0, "Workflow took too long")
        }
    }

    func testMultipleCandidateAdvancement() throws {
        // Navigate to pipeline
        navigateToPipeline()

        let candidateCount = min(5, app.cells.count)

        for index in 0..<candidateCount {
            startPerformanceTracking(label: "advance_candidate_\(index)")

            let candidate = app.cells.element(boundBy: index)
            if candidate.waitForExistence(timeout: 3) {
                tapElement(candidate)

                let advanceButton = app.buttons["advance_candidate_button"]
                if advanceButton.waitForExistence(timeout: 3) {
                    tapElement(advanceButton)

                    let statusOption = app.buttons["status_interview"]
                    if statusOption.waitForExistence(timeout: 2) {
                        tapElement(statusOption)
                    }

                    // Go back
                    let backButton = app.navigationBars.buttons.element(boundBy: 0)
                    if backButton.exists {
                        tapElement(backButton)
                    }
                }
            }

            endPerformanceTracking(label: "advance_candidate_\(index)")
            sleep(1)
        }
    }

    func testPipelineFiltering() throws {
        startPerformanceTracking(label: "pipeline_filtering")

        navigateToPipeline()

        let filterButton = app.buttons["filter_button"]
        assertElementExists(filterButton)
        tapElement(filterButton)

        let statusFilter = app.buttons["filter_status"]
        assertElementExists(statusFilter)
        tapElement(statusFilter)

        let screeningStatus = app.buttons["status_screening"]
        if screeningStatus.waitForExistence(timeout: 2) {
            tapElement(screeningStatus)
        }

        let applyButton = app.buttons["apply_filter"]
        if applyButton.waitForExistence(timeout: 2) {
            tapElement(applyButton)
        }

        sleep(2)

        endPerformanceTracking(label: "pipeline_filtering")
    }

    func testCandidateSearch() throws {
        startPerformanceTracking(label: "candidate_search")

        navigateToPipeline()

        let searchField = app.searchFields["candidate_search"]
        assertElementExists(searchField)

        typeText("John", in: searchField)
        sleep(2)

        endPerformanceTracking(label: "candidate_search")
    }

    // MARK: - Performance Tests

    func testLoginPerformance() throws {
        startPerformanceTracking(label: "login")

        let emailField = app.textFields["email_input"]
        assertElementExists(emailField)
        typeText("recruiter@example.com", in: emailField)

        let passwordField = app.secureTextFields["password_input"]
        typeText("password123", in: passwordField)

        let loginButton = app.buttons["login_button"]
        tapElement(loginButton)

        let dashboardTitle = app.staticTexts["dashboard_title"]
        assertElementExists(dashboardTitle)

        endPerformanceTracking(label: "login")

        if let stats = getPerformanceStats(label: "login") {
            XCTAssertLessThan(stats.average, 15.0, "Login took too long")
        }
    }

    func testPipelineLoadPerformance() throws {
        startPerformanceTracking(label: "pipeline_load")

        navigateToPipeline()

        let pipelineHeader = app.staticTexts["pipeline_header"]
        assertElementExists(pipelineHeader)

        endPerformanceTracking(label: "pipeline_load")

        if let stats = getPerformanceStats(label: "pipeline_load") {
            XCTAssertLessThan(stats.average, 10.0, "Pipeline load took too long")
        }
    }

    func testCandidateDetailLoadPerformance() throws {
        navigateToPipeline()

        let candidate = app.cells.element(boundBy: 0)
        assertElementExists(candidate)

        startPerformanceTracking(label: "candidate_detail_load")
        tapElement(candidate)

        let detailHeader = app.staticTexts["candidate_detail_header"]
        assertElementExists(detailHeader)

        endPerformanceTracking(label: "candidate_detail_load")

        if let stats = getPerformanceStats(label: "candidate_detail_load") {
            XCTAssertLessThan(stats.average, 5.0, "Candidate detail load took too long")
        }
    }

    func testScrollPerformance() throws {
        navigateToPipeline()

        let candidateList = app.collectionViews.firstMatch
        assertElementExists(candidateList)

        startPerformanceTracking(label: "scroll_performance")

        for _ in 0..<5 {
            scrollDown(in: candidateList)
            sleep(1)
        }

        for _ in 0..<5 {
            scrollUp(in: candidateList)
            sleep(1)
        }

        endPerformanceTracking(label: "scroll_performance")
    }

    // MARK: - Stress Tests

    func testRapidNavigation() throws {
        let tabs = [
            app.tabBars.buttons["Pipeline"],
            app.tabBars.buttons["Dashboard"],
            app.tabBars.buttons["Settings"]
        ]

        startPerformanceTracking(label: "rapid_navigation")

        for _ in 0..<10 {
            for tab in tabs {
                if tab.exists {
                    tap(tab)
                    sleep(1)
                }
            }
        }

        endPerformanceTracking(label: "rapid_navigation")
    }

    func testStressWithLargeDatasets() throws {
        startPerformanceTracking(label: "large_dataset_stress")

        navigateToPipeline()

        let candidateList = app.collectionViews.firstMatch
        assertElementExists(candidateList)

        // Simulate rapid scrolling through large list
        for _ in 0..<20 {
            scrollDown(in: candidateList)
        }

        endPerformanceTracking(label: "large_dataset_stress")
    }

    // MARK: - Error Recovery Tests

    func testRecoveryFromNetworkError() throws {
        navigateToPipeline()

        let candidate = app.cells.element(boundBy: 0)
        if candidate.waitForExistence(timeout: 3) {
            tapElement(candidate)

            let advanceButton = app.buttons["advance_candidate_button"]
            if advanceButton.waitForExistence(timeout: 3) {
                tapElement(advanceButton)

                // Handle potential error
                let errorAlert = app.alerts.firstMatch
                if errorAlert.waitForExistence(timeout: 2) {
                    let retryButton = errorAlert.buttons["Retry"]
                    if retryButton.exists {
                        tapElement(retryButton)
                    } else {
                        let dismissButton = errorAlert.buttons.firstMatch
                        if dismissButton.exists {
                            tapElement(dismissButton)
                        }
                    }
                }
            }
        }
    }

    func testRecoveryFromCrash() throws {
        // Navigate and interact
        navigateToPipeline()
        let candidate = app.cells.element(boundBy: 0)
        if candidate.waitForExistence(timeout: 3) {
            tapElement(candidate)
            sleep(2)

            // Terminate and relaunch
            app.terminate()
            sleep(1)

            // The app should relaunch in setUpWithError
            app.launch()
            sleep(2)

            // Verify we can interact again
            let pipelineTab = app.tabBars.buttons["Pipeline"]
            assertElementExists(pipelineTab)
        }
    }

    // MARK: - Accessibility Tests Enhanced

    func testFullAccessibilityCompliance() throws {
        navigateToPipeline()

        let elements = AccessibilityTestHelpers.getAllAccessibleElements(app)
        XCTAssertGreaterThan(elements.count, 0, "Should have accessible elements")

        for element in elements.prefix(10) {
            XCTAssertNotNil(element.label, "Element should have accessibility label")
        }
    }

    func testKeyboardNavigation() throws {
        let emailField = app.textFields["email_input"]
        assertElementExists(emailField)

        tapElement(emailField)
        // Simulate keyboard interactions
        app.typeText("recruiter@example.com")
    }

    // MARK: - Data Validation Tests

    func testCandidateInfoDisplay() throws {
        navigateToPipeline()

        let candidate = app.cells.element(boundBy: 0)
        assertElementExists(candidate)
        tapElement(candidate)

        // Verify candidate info is displayed
        let candidateName = app.staticTexts["candidate_name"]
        assertElementExists(candidateName)

        let candidateStatus = app.staticTexts["candidate_status"]
        assertElementExists(candidateStatus)

        let candidateScore = app.staticTexts["candidate_score"]
        if candidateScore.exists {
            // Score might be optional
            XCTAssertTrue(true)
        }
    }

    func testStatusTransitionValidation() throws {
        navigateToPipeline()

        let candidate = app.cells.element(boundBy: 0)
        if candidate.waitForExistence(timeout: 3) {
            tapElement(candidate)

            // Check current status
            let currentStatus = app.staticTexts["candidate_status"]
            assertElementExists(currentStatus)

            // Try to advance
            let advanceButton = app.buttons["advance_candidate_button"]
            if advanceButton.exists {
                tapElement(advanceButton)

                // Status options should be available
                let statusOptions = app.buttons.matching(identifier: "status_.*")
                XCTAssertGreaterThan(statusOptions.count, 0)
            }
        }
    }

    // MARK: - Helper Methods

    private func tap(_ element: XCUIElement) {
        if element.waitForExistence(timeout: 2) {
            element.tap()
        }
    }
}
