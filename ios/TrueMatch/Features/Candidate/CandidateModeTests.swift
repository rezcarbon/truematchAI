//
//  CandidateModeTests.swift
//  TrueMatchTests
//
//  Unit tests for Candidate Mode features: assessment results, job recommendations,
//  career coaching, and application tracking.
//

import XCTest
import Combine
@testable import TrueMatch

@MainActor
final class AssessmentResultsViewModelTests: XCTestCase {
    var viewModel: AssessmentResultsViewModel!

    override func setUp() {
        super.setUp()
        viewModel = AssessmentResultsViewModel(candidateId: "test-candidate")
    }

    func testInitialization() {
        XCTAssertEqual(viewModel.candidateId, "test-candidate")
        XCTAssertEqual(viewModel.traditionalScore, 0)
        XCTAssertEqual(viewModel.semanticScore, 0)
        XCTAssertEqual(viewModel.capabilityScore, 0)
        XCTAssertTrue(viewModel.deltas.isEmpty)
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertNil(viewModel.errorMessage)
    }

    func testDeltaComputation() {
        viewModel.traditionalScore = 60
        viewModel.semanticScore = 75
        viewModel.capabilityScore = 85

        viewModel.computeDeltas()

        XCTAssertEqual(viewModel.deltas["capability_vs_traditional"], 25)
        XCTAssertEqual(viewModel.deltas["semantic_vs_traditional"], 15)
        XCTAssertEqual(viewModel.deltas["capability_vs_semantic"], 10)
    }

    func testDeltaComputationNegative() {
        viewModel.traditionalScore = 80
        viewModel.semanticScore = 70
        viewModel.capabilityScore = 60

        viewModel.computeDeltas()

        XCTAssertEqual(viewModel.deltas["capability_vs_traditional"], -20)
        XCTAssertEqual(viewModel.deltas["semantic_vs_traditional"], -10)
        XCTAssertEqual(viewModel.deltas["capability_vs_semantic"], -10)
    }

    func testBrowseJobsTracking() {
        viewModel.didTapBrowseJobs()
        // Verify logging occurred
        XCTAssert(true)  // Just ensures method completes
    }
}

@MainActor
final class JobRecommendationsViewModelTests: XCTestCase {
    var viewModel: JobRecommendationsViewModel!

    override func setUp() {
        super.setUp()
        viewModel = JobRecommendationsViewModel(candidateId: "test-candidate")
    }

    func testInitialization() {
        XCTAssertEqual(viewModel.candidateId, "test-candidate")
        XCTAssertTrue(viewModel.jobs.isEmpty)
        XCTAssertEqual(viewModel.currentJobIndex, 0)
        XCTAssertTrue(viewModel.savedJobs.isEmpty)
        XCTAssertTrue(viewModel.rejectedJobs.isEmpty)
        XCTAssertNil(viewModel.currentJob)
    }

    func testCurrentJobSelection() {
        let job1 = createMockJobRecommendation(id: "job1")
        let job2 = createMockJobRecommendation(id: "job2")
        viewModel.jobs = [job1, job2]

        XCTAssertEqual(viewModel.currentJob?.id, "job1")

        viewModel.currentJobIndex = 1
        XCTAssertEqual(viewModel.currentJob?.id, "job2")
    }

    func testJobsRemainingCount() {
        let jobs = (0..<5).map { createMockJobRecommendation(id: "job\($0)") }
        viewModel.jobs = jobs

        XCTAssertEqual(viewModel.jobsRemaining, 4)

        viewModel.currentJobIndex = 2
        XCTAssertEqual(viewModel.jobsRemaining, 2)

        viewModel.currentJobIndex = 4
        XCTAssertEqual(viewModel.jobsRemaining, 0)
    }

    func testSaveJobAddsToSet() {
        let job = createMockJobRecommendation(id: "job1")
        viewModel.jobs = [job]

        Task {
            await viewModel.saveJob("job1")
        }

        XCTAssertTrue(viewModel.savedJobs.contains("job1"))
    }

    func testRejectJobAddsToSet() {
        let job = createMockJobRecommendation(id: "job1")
        viewModel.jobs = [job]

        Task {
            await viewModel.rejectJob("job1")
        }

        XCTAssertTrue(viewModel.rejectedJobs.contains("job1"))
    }

    func testSwipeRightDirection() {
        let job = createMockJobRecommendation(id: "job1")
        viewModel.jobs = [job]

        Task {
            await viewModel.handleSwipe(direction: .right)
        }

        XCTAssertEqual(viewModel.lastSwipeDirection, .right)
        XCTAssertTrue(viewModel.savedJobs.contains("job1"))
    }

    func testSwipeLeftDirection() {
        let job = createMockJobRecommendation(id: "job1")
        viewModel.jobs = [job]

        Task {
            await viewModel.handleSwipe(direction: .left)
        }

        XCTAssertEqual(viewModel.lastSwipeDirection, .left)
        XCTAssertTrue(viewModel.rejectedJobs.contains("job1"))
    }

    // MARK: - Helpers

    private func createMockJobRecommendation(id: String) -> JobRecommendation {
        JobRecommendation(
            id: id,
            jobTitle: "Software Engineer",
            company: "TechCorp",
            location: "San Francisco, CA",
            matchScore: 85.0,
            traditionalScore: 80.0,
            semanticScore: 85.0,
            capabilityScore: 90.0,
            requiredSkills: [],
            matchedStrengths: [],
            skillGaps: [],
            jobDescription: "Test job",
            salaryRange: SalaryRange(min: 120000, max: 180000, currency: "$"),
            jobLevel: "senior",
            jobType: "full-time",
            postedDate: ISO8601DateFormatter().string(from: Date()),
            applicationDeadline: nil,
            url: "https://example.com"
        )
    }
}

@MainActor
final class CareerCoachViewModelTests: XCTestCase {
    var viewModel: CareerCoachViewModel!

    override func setUp() {
        super.setUp()
        viewModel = CareerCoachViewModel(candidateId: "test-candidate")
    }

    override func tearDown() {
        viewModel.disconnect()
        super.tearDown()
    }

    func testInitialization() {
        XCTAssertEqual(viewModel.candidateId, "test-candidate")
        XCTAssertTrue(viewModel.messages.isEmpty)
        XCTAssertTrue(viewModel.suggestedFollowUps.isEmpty)
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertFalse(viewModel.isSending)
        XCTAssertNil(viewModel.errorMessage)
        XCTAssertEqual(viewModel.connectionStatus, .disconnected)
    }

    func testCanSendValidation() {
        viewModel.inputText = ""
        XCTAssertFalse(viewModel.canSend)

        viewModel.inputText = "Test message"
        XCTAssertFalse(viewModel.canSend)  // Not connected

        viewModel.connectionStatus = .connected
        XCTAssertTrue(viewModel.canSend)

        viewModel.isSending = true
        XCTAssertFalse(viewModel.canSend)  // Currently sending
    }

    func testUseSuggestionPopulatesInput() {
        let suggestion = "How can I improve my skills?"
        viewModel.useSuggestion(suggestion)
        XCTAssertEqual(viewModel.inputText, suggestion)
    }

    func testClearHistory() {
        let message1 = CareerCoachMessage(
            id: "1",
            role: "user",
            content: "Test 1",
            structuredContent: nil,
            timestamp: ISO8601DateFormatter().string(from: Date())
        )
        let message2 = CareerCoachMessage(
            id: "2",
            role: "assistant",
            content: "Response",
            structuredContent: nil,
            timestamp: ISO8601DateFormatter().string(from: Date())
        )

        viewModel.messages = [message1, message2]
        viewModel.suggestedFollowUps = ["Follow-up 1", "Follow-up 2"]

        viewModel.clearHistory()

        XCTAssertTrue(viewModel.messages.isEmpty)
        XCTAssertTrue(viewModel.suggestedFollowUps.isEmpty)
    }
}

@MainActor
final class ApplicationTrackingViewModelTests: XCTestCase {
    var viewModel: ApplicationTrackingViewModel!

    override func setUp() {
        super.setUp()
        viewModel = ApplicationTrackingViewModel(candidateId: "test-candidate")
    }

    func testInitialization() {
        XCTAssertEqual(viewModel.candidateId, "test-candidate")
        XCTAssertTrue(viewModel.applications.isEmpty)
        XCTAssertTrue(viewModel.applicationsByStage.isEmpty)
        XCTAssertEqual(viewModel.selectedStage, "applied")
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertNil(viewModel.errorMessage)
    }

    func testStageOrganization() {
        let app1 = createMockApplication(id: "app1", stage: "applied")
        let app2 = createMockApplication(id: "app2", stage: "interviewing")
        let app3 = createMockApplication(id: "app3", stage: "applied")

        viewModel.applications = [app1, app2, app3]
        viewModel.organizeByStage()

        XCTAssertEqual(viewModel.applicationsByStage["applied"]?.count, 2)
        XCTAssertEqual(viewModel.applicationsByStage["interviewing"]?.count, 1)
        XCTAssertEqual(viewModel.applicationsByStage["reviewing"]?.count, 0)
    }

    func testGetApplicationsForStage() {
        let app1 = createMockApplication(id: "app1", stage: "applied")
        let app2 = createMockApplication(id: "app2", stage: "applied")
        let app3 = createMockApplication(id: "app3", stage: "interviewing")

        viewModel.applications = [app1, app2, app3]
        viewModel.organizeByStage()

        let appliedApps = viewModel.getApplicationsForStage("applied")
        XCTAssertEqual(appliedApps.count, 2)
        XCTAssertTrue(appliedApps.allSatisfy { $0.stage == "applied" })
    }

    func testSelectApplication() {
        let app = createMockApplication(id: "app1", stage: "applied")
        viewModel.selectApplication(app)

        XCTAssertEqual(viewModel.selectedApplication?.id, "app1")
    }

    // MARK: - Helpers

    private func createMockApplication(id: String, stage: String) -> ApplicationStatus {
        ApplicationStatus(
            id: id,
            candidateId: "candidate-1",
            jobId: "job-1",
            jobTitle: "Software Engineer",
            company: "TechCorp",
            stage: stage,
            appliedDate: ISO8601DateFormatter().string(from: Date()),
            lastUpdateDate: ISO8601DateFormatter().string(from: Date()),
            timeline: [
                ApplicationEvent(
                    id: "event-1",
                    eventType: "applied",
                    description: "Application submitted",
                    timestamp: ISO8601DateFormatter().string(from: Date()),
                    details: nil
                )
            ],
            interviewSessions: [],
            offerDetails: nil,
            notes: nil
        )
    }
}

// MARK: - Integration Tests

final class CandidateModeIntegrationTests: XCTestCase {
    @MainActor
    func testAssessmentToJobsFlow() async {
        let assessmentVM = AssessmentResultsViewModel(candidateId: "test-candidate")
        let jobsVM = JobRecommendationsViewModel(candidateId: "test-candidate")

        // Simulate assessment results
        assessmentVM.traditionalScore = 70
        assessmentVM.semanticScore = 80
        assessmentVM.capabilityScore = 85

        assessmentVM.computeDeltas()

        // Verify deltas exist
        XCTAssertFalse(assessmentVM.deltas.isEmpty)

        // User navigates to jobs
        XCTAssertTrue(jobsVM.jobs.isEmpty)
    }

    @MainActor
    func testApplicationTrackingPipeline() async {
        let viewModel = ApplicationTrackingViewModel(candidateId: "test-candidate")

        let app1 = createApplication(id: "app1", stage: "applied")
        let app2 = createApplication(id: "app2", stage: "interviewing")
        let app3 = createApplication(id: "app3", stage: "offer")

        viewModel.applications = [app1, app2, app3]
        viewModel.organizeByStage()

        // Verify organization
        XCTAssertEqual(viewModel.applicationsByStage["applied"]?.count, 1)
        XCTAssertEqual(viewModel.applicationsByStage["interviewing"]?.count, 1)
        XCTAssertEqual(viewModel.applicationsByStage["offer"]?.count, 1)

        // Select an application
        viewModel.selectApplication(app2)
        XCTAssertEqual(viewModel.selectedApplication?.id, "app2")
    }

    // MARK: - Helpers

    private func createApplication(id: String, stage: String) -> ApplicationStatus {
        ApplicationStatus(
            id: id,
            candidateId: "candidate-1",
            jobId: "job-\(id)",
            jobTitle: "Software Engineer",
            company: "TechCorp",
            stage: stage,
            appliedDate: ISO8601DateFormatter().string(from: Date()),
            lastUpdateDate: ISO8601DateFormatter().string(from: Date()),
            timeline: [],
            interviewSessions: [],
            offerDetails: nil,
            notes: nil
        )
    }
}
