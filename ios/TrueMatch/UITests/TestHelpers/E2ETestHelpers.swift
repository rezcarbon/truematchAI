import XCTest

// MARK: - E2E Test Base

class E2ETestBase: XCTestCase {
    var app: XCUIApplication!
    var performanceMonitor: E2EPerformanceMonitor!

    override func setUpWithError() throws {
        continueAfterFailure = false
        performanceMonitor = E2EPerformanceMonitor()

        app = XCUIApplication()
        app.launchArguments = ["UI_TESTING"]
        app.launchEnvironment = ["SIMULATOR": "true"]
        app.launch()

        // Wait for app to stabilize
        sleep(2)
    }

    override func tearDownWithError() throws {
        app.terminate()
    }

    // MARK: - Common Navigation

    func navigateToPipeline() {
        let pipelineTab = app.tabBars.buttons["Pipeline"]
        waitForElement(pipelineTab, timeout: 5)
        pipelineTab.tap()
    }

    func navigateToJobs() {
        let jobsTab = app.tabBars.buttons["Jobs"]
        waitForElement(jobsTab, timeout: 5)
        jobsTab.tap()
    }

    func navigateToCareerCoach() {
        let coachTab = app.tabBars.buttons["Career Coach"]
        waitForElement(coachTab, timeout: 5)
        coachTab.tap()
    }

    func navigateToProfile() {
        let profileTab = app.tabBars.buttons["Profile"]
        waitForElement(profileTab, timeout: 5)
        profileTab.tap()
    }

    func dismissAlert() {
        let alert = app.alerts.firstMatch
        if alert.waitForExistence(timeout: 1) {
            let okButton = alert.buttons["OK"]
            if okButton.exists {
                okButton.tap()
            }
        }
    }

    // MARK: - Element Interactions

    func waitForElement(_ element: XCUIElement, timeout: TimeInterval = 5) {
        let predicate = NSPredicate(format: "exists == 1")
        let expectation = XCTestExpectation(description: "Element exists")

        DispatchQueue.global().async {
            if element.waitForExistence(timeout: timeout) {
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: timeout + 1)
    }

    func tapElement(_ element: XCUIElement, timeout: TimeInterval = 5) {
        waitForElement(element, timeout: timeout)
        element.tap()
    }

    func typeText(_ text: String, in element: XCUIElement, timeout: TimeInterval = 5) {
        waitForElement(element, timeout: timeout)
        element.tap()
        element.typeText(text)
    }

    func scrollUp(in element: XCUIElement) {
        element.swipeUp()
    }

    func scrollDown(in element: XCUIElement) {
        element.swipeDown()
    }

    // MARK: - Assertions

    func assertElementExists(_ element: XCUIElement, timeout: TimeInterval = 5) {
        XCTAssertTrue(element.waitForExistence(timeout: timeout), "Element does not exist")
    }

    func assertElementDoesNotExist(_ element: XCUIElement, timeout: TimeInterval = 5) {
        let result = element.waitForExistence(timeout: timeout)
        XCTAssertFalse(result, "Element exists when it should not")
    }

    func assertLabelContains(_ element: XCUIElement, text: String, timeout: TimeInterval = 5) {
        waitForElement(element, timeout: timeout)
        XCTAssertTrue(element.label.contains(text), "Label does not contain expected text: \(text)")
    }

    // MARK: - Data Entry

    func fillForm(with data: [String: String]) {
        for (fieldID, value) in data {
            let field = app.textFields[fieldID]
            typeText(value, in: field)
        }
    }

    func selectDropdownOption(_ dropdownID: String, option: String) {
        let dropdown = app.buttons[dropdownID]
        tapElement(dropdown)

        let optionButton = app.buttons[option]
        tapElement(optionButton)
    }

    // MARK: - Search and Filter

    func searchFor(_ term: String) {
        let searchField = app.searchFields.firstMatch
        waitForElement(searchField, timeout: 5)
        typeText(term, in: searchField)
    }

    func applyFilter(_ filterName: String, value: String) {
        let filterButton = app.buttons["filter_button"]
        tapElement(filterButton)

        let filterOption = app.buttons[filterName]
        tapElement(filterOption)

        let filterValue = app.buttons[value]
        tapElement(filterValue)

        let applyButton = app.buttons["apply_filter"]
        tapElement(applyButton)
    }

    // MARK: - Performance Tracking

    func startPerformanceTracking(label: String) {
        performanceMonitor.startMeasurement(label: label)
    }

    func endPerformanceTracking(label: String) {
        performanceMonitor.endMeasurement(label: label)
    }

    func getPerformanceStats(label: String) -> E2EPerformanceMonitor.Stats? {
        return performanceMonitor.getStatistics(label: label)
    }
}

// MARK: - Performance Monitor

class E2EPerformanceMonitor {
    private var measurements: [String: [TimeInterval]] = [:]
    private var startTimes: [String: Date] = [:]

    func startMeasurement(label: String) {
        startTimes[label] = Date()
    }

    func endMeasurement(label: String) -> TimeInterval? {
        guard let startTime = startTimes[label] else { return nil }

        let elapsed = Date().timeIntervalSince(startTime)
        if measurements[label] == nil {
            measurements[label] = []
        }
        measurements[label]?.append(elapsed)
        startTimes.removeValue(forKey: label)

        return elapsed
    }

    func getStatistics(label: String) -> Stats? {
        guard let times = measurements[label], !times.isEmpty else { return nil }

        let sorted = times.sorted()
        let average = times.reduce(0, +) / Double(times.count)
        let median = times.count % 2 == 0
            ? (sorted[times.count / 2 - 1] + sorted[times.count / 2]) / 2
            : sorted[times.count / 2]

        return Stats(
            count: times.count,
            min: sorted.first ?? 0,
            max: sorted.last ?? 0,
            average: average,
            median: median
        )
    }

    struct Stats {
        let count: Int
        let min: TimeInterval
        let max: TimeInterval
        let average: TimeInterval
        let median: TimeInterval
    }
}

// MARK: - Common Test Scenarios

class RecruiterTestScenarios {
    static func loginAsRecruiter(_ app: XCUIApplication) {
        let emailField = app.textFields["email_input"]
        emailField.waitForExistence(timeout: 5)
        emailField.tap()
        emailField.typeText("recruiter@example.com")

        let passwordField = app.secureTextFields["password_input"]
        passwordField.tap()
        passwordField.typeText("password123")

        let loginButton = app.buttons["login_button"]
        loginButton.tap()

        let dashboardTitle = app.staticTexts["dashboard_title"]
        _ = dashboardTitle.waitForExistence(timeout: 10)
    }

    static func viewCandidatePipeline(_ app: XCUIApplication) {
        let pipelineTab = app.tabBars.buttons["Pipeline"]
        _ = pipelineTab.waitForExistence(timeout: 5)
        pipelineTab.tap()

        let pipelineView = app.staticTexts["pipeline_header"]
        _ = pipelineView.waitForExistence(timeout: 5)
    }

    static func advanceCandidateToInterview(_ app: XCUIApplication) {
        let candidate = app.cells.element(boundBy: 0)
        _ = candidate.waitForExistence(timeout: 5)
        candidate.tap()

        let advanceButton = app.buttons["advance_candidate_button"]
        _ = advanceButton.waitForExistence(timeout: 5)
        advanceButton.tap()

        let interviewOption = app.buttons["status_interview"]
        _ = interviewOption.waitForExistence(timeout: 3)
        interviewOption.tap()

        let confirmation = app.staticTexts["status_updated"]
        _ = confirmation.waitForExistence(timeout: 5)
    }
}

class CandidateTestScenarios {
    static func loginAsCandidate(_ app: XCUIApplication) {
        let emailField = app.textFields["email_input"]
        emailField.waitForExistence(timeout: 5)
        emailField.tap()
        emailField.typeText("candidate@example.com")

        let passwordField = app.secureTextFields["password_input"]
        passwordField.tap()
        passwordField.typeText("password123")

        let loginButton = app.buttons["login_button"]
        loginButton.tap()

        let dashboardTitle = app.staticTexts["dashboard_title"]
        _ = dashboardTitle.waitForExistence(timeout: 10)
    }

    static func browseJobs(_ app: XCUIApplication) {
        let jobsTab = app.tabBars.buttons["Jobs"]
        _ = jobsTab.waitForExistence(timeout: 5)
        jobsTab.tap()

        let jobsList = app.collectionViews.firstMatch
        _ = jobsList.waitForExistence(timeout: 5)
    }

    static func swipeJobRight(_ app: XCUIApplication) {
        let jobCard = app.cells.element(boundBy: 0)
        _ = jobCard.waitForExistence(timeout: 5)

        let startCoordinate = jobCard.coordinate(withNormalizedOffset: CGVector(dx: 0, dy: 0))
        let endCoordinate = startCoordinate.withOffset(CGVector(dx: 300, dy: 0))
        startCoordinate.press(forDuration: 0, thenDragTo: endCoordinate)
    }

    static func saveJob(_ app: XCUIApplication) {
        let saveButton = app.buttons["save_job_button"]
        _ = saveButton.waitForExistence(timeout: 5)
        saveButton.tap()

        let confirmation = app.staticTexts["job_saved"]
        _ = confirmation.waitForExistence(timeout: 5)
    }

    static func chatWithCareerCoach(_ app: XCUIApplication, message: String) {
        let coachTab = app.tabBars.buttons["Career Coach"]
        _ = coachTab.waitForExistence(timeout: 5)
        coachTab.tap()

        let messageField = app.textViews["message_input"]
        _ = messageField.waitForExistence(timeout: 5)
        messageField.tap()
        messageField.typeText(message)

        let sendButton = app.buttons["send_message"]
        sendButton.tap()

        let response = app.staticTexts.firstMatch
        _ = response.waitForExistence(timeout: 10)
    }
}

// MARK: - Accessibility Helpers

class AccessibilityTestHelpers {
    static func verifyAccessibilityTree(_ app: XCUIApplication) -> Bool {
        let elements = app.children
        return elements.count > 0
    }

    static func getAllAccessibleElements(_ app: XCUIApplication) -> [XCUIElement] {
        var elements: [XCUIElement] = []

        // Collect all accessible elements
        for button in app.buttons.allElementsBoundByIndex {
            if button.isAccessibilityElement {
                elements.append(button)
            }
        }

        for cell in app.cells.allElementsBoundByIndex {
            if cell.isAccessibilityElement {
                elements.append(cell)
            }
        }

        for text in app.staticTexts.allElementsBoundByIndex {
            if text.isAccessibilityElement {
                elements.append(text)
            }
        }

        return elements
    }

    static func testVoiceoverLabels(_ app: XCUIApplication) {
        let elements = getAllAccessibleElements(app)
        for element in elements {
            let label = element.label
            let identifier = element.identifier
            print("Element: \(identifier), Label: \(label)")
        }
    }
}

// MARK: - Memory and Crash Detection

class StabilityTestHelpers {
    static func navigateMultipleTimes(_ app: XCUIApplication, times: Int = 10) {
        for _ in 0..<times {
            let tabs = app.tabBars.buttons.allElementsBoundByIndex
            if !tabs.isEmpty {
                tabs[Int.random(in: 0..<tabs.count)].tap()
                sleep(1)
            }
        }
    }

    static func performStressTest(_ app: XCUIApplication, duration: TimeInterval = 30) {
        let deadline = Date().addingTimeInterval(duration)

        while Date() < deadline {
            let elements = app.cells.allElementsBoundByIndex
            if !elements.isEmpty {
                let randomCell = elements[Int.random(in: 0..<elements.count)]
                randomCell.tap()
                sleep(1)

                let backButton = app.navigationBars.buttons.element(boundBy: 0)
                if backButton.exists {
                    backButton.tap()
                }
            }
        }
    }
}

// MARK: - Screenshot Utilities

class ScreenshotManager {
    private var screenshotCount = 0

    func captureScreenshot(_ app: XCUIApplication, named: String) {
        let screenshot = XCUIScreen.main.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "screenshot_\(named)_\(screenshotCount)"
        attachment.lifetime = .keepAlways
        screenshotCount += 1
    }
}
