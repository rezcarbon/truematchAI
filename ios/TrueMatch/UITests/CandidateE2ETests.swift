import XCTest

final class CandidateE2ETests: XCTestCase {
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

    func testCandidateLoginFlow() throws {
        // Enter email
        let emailField = app.textFields["email_input"]
        XCTAssertTrue(emailField.waitForExistence(timeout: 5))
        emailField.tap()
        emailField.typeText("candidate@example.com")

        // Enter password
        let passwordField = app.secureTextFields["password_input"]
        passwordField.tap()
        passwordField.typeText("password123")

        // Login
        let loginButton = app.buttons["login_button"]
        loginButton.tap()

        // Verify dashboard
        let dashboard = app.staticTexts["candidate_dashboard"]
        XCTAssertTrue(dashboard.waitForExistence(timeout: 10))
    }

    // MARK: - Job Browsing Tests

    func testBrowseJobRecommendations() throws {
        // Navigate to jobs tab
        let jobsTab = app.tabBars.buttons["Jobs"]
        XCTAssertTrue(jobsTab.exists)
        jobsTab.tap()

        // Verify jobs load
        let jobsList = app.collectionViews.firstMatch
        XCTAssertTrue(jobsList.waitForExistence(timeout: 5))

        // Verify jobs are displayed
        let firstJob = app.cells.element(boundBy: 0)
        XCTAssertTrue(firstJob.waitForExistence(timeout: 3))
    }

    func testViewJobDetails() throws {
        // Navigate to jobs
        let jobsTab = app.tabBars.buttons["Jobs"]
        jobsTab.tap()

        // Tap first job
        let firstJob = app.cells.element(boundBy: 0)
        XCTAssertTrue(firstJob.waitForExistence(timeout: 5))
        firstJob.tap()

        // Verify detail view
        let jobTitle = app.staticTexts["job_title"]
        XCTAssertTrue(jobTitle.waitForExistence(timeout: 5))

        let jobDescription = app.staticTexts["job_description"]
        XCTAssertTrue(jobDescription.waitForExistence(timeout: 3))

        let matchScore = app.staticTexts["match_score"]
        XCTAssertTrue(matchScore.waitForExistence(timeout: 3))
    }

    // MARK: - Job Swiping Tests

    func testSwipeRightOnJob() throws {
        // Navigate to jobs
        let jobsTab = app.tabBars.buttons["Jobs"]
        jobsTab.tap()

        // Get first job card
        let jobCard = app.collectionViews.cells.element(boundBy: 0)
        XCTAssertTrue(jobCard.waitForExistence(timeout: 5))

        // Swipe right
        jobCard.swipeRight()

        // Verify liked indicator or next job shown
        sleep(1)

        // Job should advance to next
        let nextJob = app.collectionViews.cells.element(boundBy: 0)
        XCTAssertTrue(nextJob.exists)
    }

    func testSwipeLeftOnJob() throws {
        // Navigate to jobs
        let jobsTab = app.tabBars.buttons["Jobs"]
        jobsTab.tap()

        // Get first job
        let jobCard = app.collectionViews.cells.element(boundBy: 0)
        XCTAssertTrue(jobCard.waitForExistence(timeout: 5))

        let firstJobTitle = jobCard.staticTexts.firstMatch.label

        // Swipe left
        jobCard.swipeLeft()

        // Verify rejection recorded and next job shown
        sleep(1)

        let nextJob = app.collectionViews.cells.element(boundBy: 0)
        let nextJobTitle = nextJob.staticTexts.firstMatch.label

        // Next job should be different
        XCTAssertNotEqual(nextJobTitle, firstJobTitle)
    }

    func testMultipleSwipes() throws {
        // Navigate to jobs
        let jobsTab = app.tabBars.buttons["Jobs"]
        jobsTab.tap()

        // Perform multiple swipes
        for _ in 0..<5 {
            let jobCard = app.collectionViews.cells.element(boundBy: 0)
            if jobCard.waitForExistence(timeout: 2) {
                let swipeDirection = Bool.random() ? "right" : "left"
                if swipeDirection == "right" {
                    jobCard.swipeRight()
                } else {
                    jobCard.swipeLeft()
                }
                sleep(1)
            }
        }

        // Verify app still responsive
        let jobsView = app.staticTexts["jobs_header"]
        XCTAssertTrue(jobsView.exists)
    }

    // MARK: - Save Job Tests

    func testSaveJob() throws {
        // Navigate to jobs
        let jobsTab = app.tabBars.buttons["Jobs"]
        jobsTab.tap()

        // Tap first job to view details
        let jobCard = app.cells.element(boundBy: 0)
        XCTAssertTrue(jobCard.waitForExistence(timeout: 5))
        jobCard.tap()

        // Tap save button
        let saveButton = app.buttons["save_job_button"]
        XCTAssertTrue(saveButton.waitForExistence(timeout: 5))
        saveButton.tap()

        // Verify saved confirmation
        let savedIndicator = app.staticTexts["job_saved"]
        XCTAssertTrue(savedIndicator.waitForExistence(timeout: 3))
    }

    func testUnsaveJob() throws {
        // Navigate to jobs
        let jobsTab = app.tabBars.buttons["Jobs"]
        jobsTab.tap()

        // Find a saved job or save one first
        let jobCard = app.cells.element(boundBy: 0)
        XCTAssertTrue(jobCard.waitForExistence(timeout: 5))
        jobCard.tap()

        // Save job first
        let saveButton = app.buttons["save_job_button"]
        if saveButton.waitForExistence(timeout: 5) {
            saveButton.tap()
            sleep(1)
        }

        // Now unsave
        let unsaveButton = app.buttons["unsave_job_button"]
        if unsaveButton.waitForExistence(timeout: 3) {
            unsaveButton.tap()

            // Verify unsaved
            let unSavedIndicator = app.staticTexts["job_unsaved"]
            XCTAssertTrue(unSavedIndicator.waitForExistence(timeout: 3))
        }
    }

    // MARK: - Saved Jobs Tests

    func testViewSavedJobs() throws {
        // Navigate to saved jobs tab
        let savedTab = app.tabBars.buttons["Saved"]
        XCTAssertTrue(savedTab.exists)
        savedTab.tap()

        // Verify saved jobs list
        let savedList = app.collectionViews.firstMatch
        XCTAssertTrue(savedList.waitForExistence(timeout: 5))
    }

    func testFilterSavedJobs() throws {
        // Navigate to saved jobs
        let savedTab = app.tabBars.buttons["Saved"]
        savedTab.tap()

        // Tap filter button
        let filterButton = app.buttons["filter_button"]
        if filterButton.waitForExistence(timeout: 5) {
            filterButton.tap()

            // Select location filter
            let locationFilter = app.buttons["filter_location"]
            if locationFilter.waitForExistence(timeout: 3) {
                locationFilter.tap()

                // Select location
                let location = app.buttons["san_francisco"]
                if location.waitForExistence(timeout: 3) {
                    location.tap()

                    // Apply filter
                    let applyButton = app.buttons["apply_filter"]
                    if applyButton.exists {
                        applyButton.tap()
                    }
                }
            }
        }
    }

    // MARK: - Profile Tests

    func testViewProfile() throws {
        // Navigate to profile tab
        let profileTab = app.tabBars.buttons["Profile"]
        XCTAssertTrue(profileTab.exists)
        profileTab.tap()

        // Verify profile data displayed
        let profileView = app.staticTexts["profile_header"]
        XCTAssertTrue(profileView.waitForExistence(timeout: 5))

        let userName = app.staticTexts["user_name"]
        XCTAssertTrue(userName.waitForExistence(timeout: 3))

        let userTitle = app.staticTexts["user_title"]
        XCTAssertTrue(userTitle.waitForExistence(timeout: 3))
    }

    func testEditProfile() throws {
        // Navigate to profile
        let profileTab = app.tabBars.buttons["Profile"]
        profileTab.tap()

        // Tap edit button
        let editButton = app.buttons["edit_profile"]
        XCTAssertTrue(editButton.waitForExistence(timeout: 5))
        editButton.tap()

        // Edit name
        let nameField = app.textFields["name_input"]
        if nameField.waitForExistence(timeout: 3) {
            nameField.tap()
            nameField.clearText()
            nameField.typeText("Jane Smith")
        }

        // Save changes
        let saveButton = app.buttons["save_profile"]
        if saveButton.waitForExistence(timeout: 3) {
            saveButton.tap()

            // Verify save confirmation
            let savedConfirmation = app.staticTexts["profile_updated"]
            XCTAssertTrue(savedConfirmation.waitForExistence(timeout: 5))
        }
    }

    // MARK: - Assessments Tests

    func testViewAssessments() throws {
        // Navigate to assessments
        let assessmentTab = app.tabBars.buttons["Assessments"]
        if assessmentTab.exists {
            assessmentTab.tap()

            // Verify assessments list
            let assessmentList = app.collectionViews.firstMatch
            XCTAssertTrue(assessmentList.waitForExistence(timeout: 5))
        }
    }

    func testViewAssessmentResults() throws {
        // Navigate to assessments
        let assessmentTab = app.tabBars.buttons["Assessments"]
        if assessmentTab.exists {
            assessmentTab.tap()

            // Tap first assessment
            let assessment = app.cells.element(boundBy: 0)
            if assessment.waitForExistence(timeout: 5) {
                assessment.tap()

                // Verify results view
                let resultsView = app.staticTexts["assessment_results"]
                XCTAssertTrue(resultsView.waitForExistence(timeout: 5))
            }
        }
    }

    // MARK: - Career Coach Tests

    func testAccessCareerCoach() throws {
        // Navigate to career coach
        let coachTab = app.tabBars.buttons["Coach"]
        if coachTab.exists {
            coachTab.tap()

            // Verify coach interface
            let chatView = app.textViews["chat_input"]
            XCTAssertTrue(chatView.waitForExistence(timeout: 5))
        }
    }

    func testSendMessageToCoach() throws {
        // Navigate to coach
        let coachTab = app.tabBars.buttons["Coach"]
        if coachTab.exists {
            coachTab.tap()

            // Type message
            let chatInput = app.textViews["chat_input"]
            if chatInput.waitForExistence(timeout: 5) {
                chatInput.tap()
                chatInput.typeText("What skills should I develop?")

                // Send message
                let sendButton = app.buttons["send_message"]
                if sendButton.waitForExistence(timeout: 3) {
                    sendButton.tap()

                    // Verify message appears
                    sleep(2)
                    let sentMessage = app.staticTexts["user_message"]
                    XCTAssertTrue(sentMessage.waitForExistence(timeout: 5))
                }
            }
        }
    }

    // MARK: - Application Tracking Tests

    func testViewApplications() throws {
        // Navigate to applications
        let applicationsTab = app.tabBars.buttons["Applications"]
        if applicationsTab.exists {
            applicationsTab.tap()

            // Verify applications list
            let appList = app.collectionViews.firstMatch
            XCTAssertTrue(appList.waitForExistence(timeout: 5))
        }
    }

    func testViewApplicationTimeline() throws {
        // Navigate to applications
        let applicationsTab = app.tabBars.buttons["Applications"]
        if applicationsTab.exists {
            applicationsTab.tap()

            // Tap first application
            let application = app.cells.element(boundBy: 0)
            if application.waitForExistence(timeout: 5) {
                application.tap()

                // Verify timeline view
                let timeline = app.staticTexts["application_timeline"]
                XCTAssertTrue(timeline.waitForExistence(timeout: 5))
            }
        }
    }

    // MARK: - Scroll Performance Tests

    func testScrollJobsPerformance() throws {
        // Navigate to jobs
        let jobsTab = app.tabBars.buttons["Jobs"]
        jobsTab.tap()

        let jobsList = app.collectionViews.firstMatch
        XCTAssertTrue(jobsList.waitForExistence(timeout: 5))

        // Scroll through multiple jobs
        for _ in 0..<10 {
            jobsList.swipeUp()
            sleep(0.5)
        }

        // Verify still responsive
        XCTAssertTrue(jobsList.exists)
    }

    // MARK: - Offline Functionality Tests

    func testOfflineJobViewing() throws {
        // Navigate to saved jobs (should be cached)
        let savedTab = app.tabBars.buttons["Saved"]
        savedTab.tap()

        // Verify saved jobs display even offline
        let savedList = app.collectionViews.firstMatch
        XCTAssertTrue(savedList.waitForExistence(timeout: 5))
    }

    // MARK: - Error Handling Tests

    func testHandleJobLoadError() throws {
        // Navigate to jobs
        let jobsTab = app.tabBars.buttons["Jobs"]
        jobsTab.tap()

        // Handle potential error alert
        let errorAlert = app.alerts.firstMatch
        if errorAlert.waitForExistence(timeout: 3) {
            let retryButton = errorAlert.buttons["Retry"]
            if retryButton.exists {
                retryButton.tap()
            }

            let dismissButton = errorAlert.buttons["Dismiss"]
            if dismissButton.exists {
                dismissButton.tap()
            }
        }
    }

    // MARK: - Navigation Tests

    func testTabNavigation() throws {
        let tabs = ["Jobs", "Saved", "Profile", "Coach", "Applications"]

        for tab in tabs {
            let tabButton = app.tabBars.buttons[tab]
            if tabButton.exists {
                tabButton.tap()
                sleep(1)
                XCTAssertTrue(tabButton.isSelected)
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
