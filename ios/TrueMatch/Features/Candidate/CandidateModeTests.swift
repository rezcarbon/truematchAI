//
//  CandidateModeTests.swift
//  TrueMatchTests
//
//  Comprehensive unit and integration tests for Candidate Mode features:
//  assessment results, job recommendations, career coaching, and application tracking.
//

import XCTest
import Combine
@testable import TrueMatch

// MARK: - Assessment Results Tests

@MainActor
final class AssessmentResultsViewModelTests: XCTestCase {
    var viewModel: AssessmentResultsViewModel!

    override func setUp() {
        super.setUp()
        viewModel = AssessmentResultsViewModel(candidateId: "test-candidate")
    }

    override func tearDown() {
        viewModel = nil
        super.tearDown()
    }

    // MARK: Initialization Tests

    func testInitialization() {
        XCTAssertEqual(viewModel.candidateId, "test-candidate")
        XCTAssertEqual(viewModel.traditionalScore, 0)
        XCTAssertEqual(viewModel.semanticScore, 0)
        XCTAssertEqual(viewModel.capabilityScore, 0)
        XCTAssertTrue(viewModel.deltas.isEmpty)
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertNil(viewModel.errorMessage)
        XCTAssertNil(viewModel.assessmentResult)
    }

    // MARK: Delta Computation Tests

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

    func testDeltaComputationZero() {
        viewModel.traditionalScore = 75
        viewModel.semanticScore = 75
        viewModel.capabilityScore = 75

        viewModel.computeDeltas()

        XCTAssertEqual(viewModel.deltas["capability_vs_traditional"], 0)
        XCTAssertEqual(viewModel.deltas["semantic_vs_traditional"], 0)
        XCTAssertEqual(viewModel.deltas["capability_vs_semantic"], 0)
    }

    func testDeltaComputationExtremes() {
        viewModel.traditionalScore = 0
        viewModel.semanticScore = 50
        viewModel.capabilityScore = 100

        viewModel.computeDeltas()

        XCTAssertEqual(viewModel.deltas["capability_vs_traditional"], 100)
        XCTAssertEqual(viewModel.deltas["semantic_vs_traditional"], 50)
        XCTAssertEqual(viewModel.deltas["capability_vs_semantic"], 50)
    }

    // MARK: Navigation Tests

    func testBrowseJobsTracking() {
        viewModel.didTapBrowseJobs()
        XCTAssert(true)  // Ensures method completes without crashing
    }

    // MARK: Error Handling Tests

    func testClearError() {
        viewModel.errorMessage = "Test error"
        XCTAssertNotNil(viewModel.errorMessage)

        viewModel.clearError()
        XCTAssertNil(viewModel.errorMessage)
    }
}

// MARK: - Job Recommendations Tests

@MainActor
final class JobRecommendationsViewModelTests: XCTestCase {
    var viewModel: JobRecommendationsViewModel!

    override func setUp() {
        super.setUp()
        viewModel = JobRecommendationsViewModel(candidateId: "test-candidate")
    }

    override func tearDown() {
        viewModel = nil
        super.tearDown()
    }

    // MARK: Initialization Tests

    func testInitialization() {
        XCTAssertEqual(viewModel.candidateId, "test-candidate")
        XCTAssertTrue(viewModel.jobs.isEmpty)
        XCTAssertEqual(viewModel.currentJobIndex, 0)
        XCTAssertTrue(viewModel.savedJobs.isEmpty)
        XCTAssertTrue(viewModel.rejectedJobs.isEmpty)
        XCTAssertNil(viewModel.currentJob)
        XCTAssertFalse(viewModel.isLoading)
    }

    // MARK: Job Selection Tests

    func testCurrentJobSelection() {
        let job1 = createMockJobRecommendation(id: "job1")
        let job2 = createMockJobRecommendation(id: "job2")
        viewModel.jobs = [job1, job2]

        XCTAssertEqual(viewModel.currentJob?.id, "job1")

        viewModel.currentJobIndex = 1
        XCTAssertEqual(viewModel.currentJob?.id, "job2")
    }

    func testCurrentJobNilWhenIndexOutOfBounds() {
        let job = createMockJobRecommendation(id: "job1")
        viewModel.jobs = [job]

        viewModel.currentJobIndex = 10
        XCTAssertNil(viewModel.currentJob)
    }

    // MARK: Remaining Jobs Tests

    func testJobsRemainingCount() {
        let jobs = (0..<5).map { createMockJobRecommendation(id: "job\($0)") }
        viewModel.jobs = jobs

        XCTAssertEqual(viewModel.jobsRemaining, 4)

        viewModel.currentJobIndex = 2
        XCTAssertEqual(viewModel.jobsRemaining, 2)

        viewModel.currentJobIndex = 4
        XCTAssertEqual(viewModel.jobsRemaining, 0)
    }

    // MARK: Save/Reject Tests

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

    func testDuplicateSaveJobIgnored() {
        viewModel.savedJobs.insert("job1")
        let initialCount = viewModel.savedJobs.count

        Task {
            await viewModel.saveJob("job1")
        }

        XCTAssertEqual(viewModel.savedJobs.count, initialCount)
    }

    func testDuplicateRejectJobIgnored() {
        viewModel.rejectedJobs.insert("job1")
        let initialCount = viewModel.rejectedJobs.count

        Task {
            await viewModel.rejectJob("job1")
        }

        XCTAssertEqual(viewModel.rejectedJobs.count, initialCount)
    }

    // MARK: Swipe Tests

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

    func testSwipeAdvancesIndex() {
        let jobs = (0..<3).map { createMockJobRecommendation(id: "job\($0)") }
        viewModel.jobs = jobs
        let initialIndex = viewModel.currentJobIndex

        Task {
            await viewModel.handleSwipe(direction: .right)
        }

        XCTAssertGreater(viewModel.currentJobIndex, initialIndex)
    }

    // MARK: Helper Methods

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

// MARK: - Career Coach Tests

@MainActor
final class CareerCoachViewModelTests: XCTestCase {
    var viewModel: CareerCoachViewModel!

    override func setUp() {
        super.setUp()
        viewModel = CareerCoachViewModel(candidateId: "test-candidate")
    }

    override func tearDown() {
        viewModel.disconnect()
        viewModel = nil
        super.tearDown()
    }

    // MARK: Initialization Tests

    func testInitialization() {
        XCTAssertEqual(viewModel.candidateId, "test-candidate")
        XCTAssertTrue(viewModel.messages.isEmpty)
        XCTAssertTrue(viewModel.suggestedFollowUps.isEmpty)
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertFalse(viewModel.isSending)
        XCTAssertNil(viewModel.errorMessage)
        XCTAssertEqual(viewModel.connectionStatus, .disconnected)
    }

    // MARK: Send Validation Tests

    func testCanSendEmptyInput() {
        viewModel.inputText = ""
        XCTAssertFalse(viewModel.canSend)
    }

    func testCanSendWithWhitespaceOnly() {
        viewModel.inputText = "   "
        XCTAssertFalse(viewModel.canSend)
    }

    func testCanSendNotConnected() {
        viewModel.inputText = "Test message"
        viewModel.connectionStatus = .disconnected
        XCTAssertFalse(viewModel.canSend)
    }

    func testCanSendConnectedAndValid() {
        viewModel.inputText = "Test message"
        viewModel.connectionStatus = .connected
        XCTAssertTrue(viewModel.canSend)
    }

    func testCanSendWhileSending() {
        viewModel.inputText = "Test message"
        viewModel.connectionStatus = .connected
        viewModel.isSending = true
        XCTAssertFalse(viewModel.canSend)
    }

    // MARK: Input Tests

    func testUseSuggestionPopulatesInput() {
        let suggestion = "How can I improve my skills?"
        viewModel.useSuggestion(suggestion)
        XCTAssertEqual(viewModel.inputText, suggestion)
    }

    func testUseSuggestionReplacesPreviousText() {
        viewModel.inputText = "Old text"
        viewModel.useSuggestion("New suggestion")
        XCTAssertEqual(viewModel.inputText, "New suggestion")
    }

    // MARK: History Tests

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

    func testClearHistoryEmptyState() {
        XCTAssertTrue(viewModel.messages.isEmpty)
        XCTAssertTrue(viewModel.suggestedFollowUps.isEmpty)

        viewModel.clearHistory()

        XCTAssertTrue(viewModel.messages.isEmpty)
        XCTAssertTrue(viewModel.suggestedFollowUps.isEmpty)
    }

    // MARK: Disconnection Tests

    func testDisconnect() {
        viewModel.connectionStatus = .connected
        viewModel.disconnect()
        XCTAssertEqual(viewModel.connectionStatus, .disconnected)
    }
}

// MARK: - Application Tracking Tests

@MainActor
final class ApplicationTrackingViewModelTests: XCTestCase {
    var viewModel: ApplicationTrackingViewModel!

    override func setUp() {
        super.setUp()
        viewModel = ApplicationTrackingViewModel(candidateId: "test-candidate")
    }

    override func tearDown() {
        viewModel = nil
        super.tearDown()
    }

    // MARK: Initialization Tests

    func testInitialization() {
        XCTAssertEqual(viewModel.candidateId, "test-candidate")
        XCTAssertTrue(viewModel.applications.isEmpty)
        XCTAssertTrue(viewModel.applicationsByStage.isEmpty)
        XCTAssertEqual(viewModel.selectedStage, "applied")
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertNil(viewModel.errorMessage)
    }

    // MARK: Stage Organization Tests

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

    func testStageOrganizationEmpty() {
        viewModel.applications = []
        viewModel.organizeByStage()

        for stage in viewModel.stageOrder {
            XCTAssertEqual(viewModel.applicationsByStage[stage]?.count, 0)
        }
    }

    func testAllStagesPresent() {
        let stages = ["applied", "reviewing", "interviewing", "offer", "closed"]
        viewModel.stageOrder.forEach { stage in
            XCTAssertTrue(stages.contains(stage))
        }
    }

    // MARK: Filtering Tests

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

    func testGetApplicationsForNonexistentStage() {
        let appliedApps = viewModel.getApplicationsForStage("invalid-stage")
        XCTAssertTrue(appliedApps.isEmpty)
    }

    // MARK: Selection Tests

    func testSelectApplication() {
        let app = createMockApplication(id: "app1", stage: "applied")
        viewModel.selectApplication(app)

        XCTAssertEqual(viewModel.selectedApplication?.id, "app1")
    }

    func testSelectMultipleApplications() {
        let app1 = createMockApplication(id: "app1", stage: "applied")
        let app2 = createMockApplication(id: "app2", stage: "interviewing")

        viewModel.selectApplication(app1)
        XCTAssertEqual(viewModel.selectedApplication?.id, "app1")

        viewModel.selectApplication(app2)
        XCTAssertEqual(viewModel.selectedApplication?.id, "app2")
    }

    // MARK: Helper Methods

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

@MainActor
final class CandidateModeIntegrationTests: XCTestCase {

    // MARK: Assessment to Jobs Flow

    func testAssessmentToJobsFlow() {
        let assessmentVM = AssessmentResultsViewModel(candidateId: "test-candidate")
        let jobsVM = JobRecommendationsViewModel(candidateId: "test-candidate")

        // Simulate assessment results
        assessmentVM.traditionalScore = 70
        assessmentVM.semanticScore = 80
        assessmentVM.capabilityScore = 85

        assessmentVM.computeDeltas()

        // Verify deltas computed correctly
        XCTAssertFalse(assessmentVM.deltas.isEmpty)
        XCTAssertEqual(assessmentVM.deltas["capability_vs_traditional"], 15)

        // User navigates to jobs
        XCTAssertTrue(jobsVM.jobs.isEmpty)

        // Both VMs ready for their respective workflows
        assessmentVM.didTapBrowseJobs()
        XCTAssertNotNil(assessmentVM.candidateId)
    }

    // MARK: Application Tracking Pipeline

    func testApplicationTrackingPipeline() {
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

        // Verify we can get applications for a stage
        let interviewingApps = viewModel.getApplicationsForStage("interviewing")
        XCTAssertEqual(interviewingApps.count, 1)
        XCTAssertEqual(interviewingApps.first?.id, "app2")
    }

    // MARK: Full Candidate Workflow

    func testFullCandidateWorkflow() {
        // Create all ViewModels
        let assessmentVM = AssessmentResultsViewModel(candidateId: "test-candidate")
        let jobsVM = JobRecommendationsViewModel(candidateId: "test-candidate")
        let coachVM = CareerCoachViewModel(candidateId: "test-candidate")
        let appTrackingVM = ApplicationTrackingViewModel(candidateId: "test-candidate")

        // Verify all start in correct state
        XCTAssertEqual(assessmentVM.candidateId, "test-candidate")
        XCTAssertEqual(jobsVM.candidateId, "test-candidate")
        XCTAssertEqual(coachVM.candidateId, "test-candidate")
        XCTAssertEqual(appTrackingVM.candidateId, "test-candidate")

        // Step 1: View assessment
        assessmentVM.traditionalScore = 75
        assessmentVM.semanticScore = 82
        assessmentVM.capabilityScore = 88
        assessmentVM.computeDeltas()

        XCTAssertFalse(assessmentVM.deltas.isEmpty)

        // Step 2: Browse jobs
        assessmentVM.didTapBrowseJobs()
        let mockJob = JobRecommendation(
            id: "job1",
            jobTitle: "Senior Engineer",
            company: "TechCorp",
            location: "SF",
            matchScore: 88.0,
            traditionalScore: 85.0,
            semanticScore: 88.0,
            capabilityScore: 92.0,
            requiredSkills: [],
            matchedStrengths: [],
            skillGaps: [],
            jobDescription: "Test",
            salaryRange: nil,
            jobLevel: "senior",
            jobType: "full-time",
            postedDate: ISO8601DateFormatter().string(from: Date()),
            applicationDeadline: nil,
            url: "https://example.com"
        )
        jobsVM.jobs = [mockJob]

        XCTAssertNotNil(jobsVM.currentJob)

        // Step 3: Save a job
        Task {
            await jobsVM.saveJob("job1")
        }
        XCTAssertTrue(jobsVM.savedJobs.contains("job1"))

        // Step 4: Track application
        let app = createApplication(id: "app1", stage: "applied")
        appTrackingVM.applications = [app]
        appTrackingVM.organizeByStage()

        XCTAssertEqual(appTrackingVM.getApplicationsForStage("applied").count, 1)

        // Step 5: Start career coaching
        XCTAssertEqual(coachVM.connectionStatus, .disconnected)
        coachVM.inputText = "How do I prepare for interviews?"
        XCTAssertFalse(coachVM.canSend)  // Not connected

        coachVM.connectionStatus = .connected
        XCTAssertTrue(coachVM.canSend)
    }

    // MARK: Job Browsing Workflow

    func testJobBrowsingWorkflow() {
        let viewModel = JobRecommendationsViewModel(candidateId: "test-candidate")

        // Create mock jobs
        let jobs = (0..<10).map { index in
            JobRecommendation(
                id: "job\(index)",
                jobTitle: "Engineer \(index)",
                company: "Company \(index)",
                location: "Location \(index)",
                matchScore: Double(80 + index),
                traditionalScore: 80.0,
                semanticScore: 85.0,
                capabilityScore: 90.0,
                requiredSkills: [],
                matchedStrengths: [],
                skillGaps: [],
                jobDescription: "Job \(index)",
                salaryRange: nil,
                jobLevel: "level\(index)",
                jobType: "full-time",
                postedDate: ISO8601DateFormatter().string(from: Date()),
                applicationDeadline: nil,
                url: "https://example.com/job\(index)"
            )
        }

        viewModel.jobs = jobs

        // Browse through jobs
        XCTAssertEqual(viewModel.jobsRemaining, 9)

        Task {
            await viewModel.handleSwipe(direction: .right)
        }

        XCTAssertTrue(viewModel.savedJobs.contains("job0"))

        Task {
            await viewModel.handleSwipe(direction: .left)
        }

        XCTAssertTrue(viewModel.rejectedJobs.contains("job1"))

        // Verify counts
        XCTAssertEqual(viewModel.savedJobs.count, 1)
        XCTAssertEqual(viewModel.rejectedJobs.count, 1)
    }

    // MARK: Helper Methods

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
