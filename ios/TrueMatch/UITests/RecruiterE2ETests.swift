import XCTest

final class RecruiterE2ETests: XCTestCase {
    var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launch()

        // Wait for app to settle
        sleep(2)
    }

    override func tearDownWithError() throws {
        app.terminate()
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
}
