//
//  JobRecommendationsViewModel.swift
//  TrueMatch
//
//  Manages job recommendations with swipe gestures, like/dislike tracking,
//  and detailed job card display.
//

import Foundation
import SwiftUI
import Combine

@MainActor
final class JobRecommendationsViewModel: ObservableObject {
    @Published var jobs: [JobRecommendation] = []
    @Published var currentJobIndex: Int = 0
    @Published var savedJobs: Set<String> = []
    @Published var rejectedJobs: Set<String> = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var lastSwipeDirection: SwipeDirection?

    enum SwipeDirection {
        case left  // reject
        case right // save
    }

    private let api = APIClient.shared
    private let candidateId: String
    private let pageSize = 20
    private var currentOffset = 0
    private var hasMoreJobs = true

    init(candidateId: String) {
        self.candidateId = candidateId
    }

    var currentJob: JobRecommendation? {
        guard currentJobIndex < jobs.count else { return nil }
        return jobs[currentJobIndex]
    }

    var jobsRemaining: Int {
        jobs.count - currentJobIndex - 1
    }

    // MARK: - Loading

    func loadJobs() async {
        guard !isLoading && hasMoreJobs else { return }

        isLoading = true
        defer { isLoading = false }

        do {
            let request = GetJobRecommendationsRequest(
                candidateId: candidateId,
                limit: pageSize,
                offset: currentOffset
            )

            let response = try await api.request(
                endpoint: .candidateJobRecommendations(request: request),
                type: [JobRecommendation].self
            )

            if response.isEmpty {
                hasMoreJobs = false
            } else {
                jobs.append(contentsOf: response)
                currentOffset += response.count
            }
        } catch {
            TrueMatchLogger.log(.error, "JobRecommendations: load failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Swipe Handling

    func handleSwipe(direction: SwipeDirection) async {
        guard let job = currentJob else { return }

        switch direction {
        case .left:
            await rejectJob(job.id)
        case .right:
            await saveJob(job.id)
        }

        lastSwipeDirection = direction
        moveToNextJob()

        // Load more if needed
        if jobsRemaining < 5 {
            await loadJobs()
        }
    }

    func saveJob(_ jobId: String) async {
        guard !savedJobs.contains(jobId) else {
            TrueMatchLogger.log(.info, "JobRecommendations: job \(jobId) already saved")
            return
        }

        savedJobs.insert(jobId)

        let request = SaveJobRequest(candidateId: candidateId, jobId: jobId, saved: true)
        do {
            try await api.requestVoid(endpoint: .saveCandidateJob(request: request))
            TrueMatchLogger.log(.info, "JobRecommendations: saved job \(jobId)")
        } catch {
            TrueMatchLogger.log(.error, "JobRecommendations: save job failed: \(error)")
            savedJobs.remove(jobId)
            errorMessage = error.localizedDescription
        }
    }

    func rejectJob(_ jobId: String) async {
        guard !rejectedJobs.contains(jobId) else {
            TrueMatchLogger.log(.info, "JobRecommendations: job \(jobId) already rejected")
            return
        }

        rejectedJobs.insert(jobId)

        let request = RejectJobRequest(candidateId: candidateId, jobId: jobId)
        do {
            try await api.requestVoid(endpoint: .rejectCandidateJob(request: request))
            TrueMatchLogger.log(.info, "JobRecommendations: rejected job \(jobId)")
        } catch {
            TrueMatchLogger.log(.error, "JobRecommendations: reject job failed: \(error)")
            rejectedJobs.remove(jobId)
            errorMessage = error.localizedDescription
        }
    }

    private func moveToNextJob() {
        withAnimation(.easeInOut(duration: 0.3)) {
            if currentJobIndex < jobs.count - 1 {
                currentJobIndex += 1
            }
        }
    }

    // MARK: - Actions

    func saveCurrentJob() async {
        guard let job = currentJob else { return }
        await saveJob(job.id)
        moveToNextJob()
    }

    func rejectCurrentJob() async {
        guard let job = currentJob else { return }
        await rejectJob(job.id)
        moveToNextJob()
    }

    func applyForCurrentJob() {
        guard let job = currentJob else { return }
        TrueMatchLogger.log(.info, "JobRecommendations: apply for job \(job.id)")
        // Navigate to application flow or open URL
        if let url = URL(string: job.url) {
            UIApplication.shared.open(url)
        }
    }
}
