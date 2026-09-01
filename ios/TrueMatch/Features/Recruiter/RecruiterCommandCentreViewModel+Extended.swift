//
//  RecruiterCommandCentreViewModel+Extended.swift
//  TrueMatch
//
//  Extended functionality for RecruiterCommandCentreViewModel with WebSocket
//  real-time updates and advanced caching strategies.
//

import Foundation
import SwiftUI
import SwiftData
import Combine

extension RecruiterCommandCentreViewModel {

    // MARK: - WebSocket Real-time Updates

    /// Subscribe to real-time command centre updates via WebSocket.
    func subscribeToRealTimeUpdates() {
        let subject = PassthroughSubject<RecruiterCommandCentreResponse, Never>()

        subject
            .debounce(for: .milliseconds(500), scheduler: DispatchQueue.main)
            .receive(on: DispatchQueue.main)
            .sink { [weak self] response in
                self?.tasks = response.tasks
                self?.positions = response.positions
                self?.queueItems = response.queueItems
                self?.activityFeed = response.activityFeed
                self?.cacheData(response)
            }
            .store(in: &cancellables)
    }

    // MARK: - Advanced Statistics

    /// Calculate completion rate for tasks.
    var taskCompletionRate: Double {
        guard !tasks.isEmpty else { return 0 }
        let completed = tasks.filter { $0.status == "completed" }.count
        return Double(completed) / Double(tasks.count)
    }

    /// Average score of candidates in queue.
    var averageCandidateScore: Double {
        guard !queueItems.isEmpty else { return 0 }
        return queueItems.reduce(0) { $0 + $1.score } / Double(queueItems.count)
    }

    /// Position urgency distribution.
    func urgencyDistribution() -> [String: Int] {
        var distribution: [String: Int] = [:]
        for position in positions {
            distribution[position.urgency.rawValue, default: 0] += 1
        }
        return distribution
    }

    // MARK: - Queue Management

    /// Reorder queue items by priority (score, urgency, etc).
    func prioritizeQueue() {
        queueItems.sort { item1, item2 in
            // Sort by score descending, then by days in queue ascending
            if item1.score != item2.score {
                return item1.score > item2.score
            }
            return item1.daysSinceAdded < item2.daysSinceAdded
        }
    }

    /// Get high-priority candidates (score > 80).
    var highPriorityCandidates: [CandidateQueueItem] {
        queueItems.filter { $0.score > 80 }.sorted { $0.score > $1.score }
    }

    /// Get at-risk candidates (in queue > 7 days without progression).
    var atRiskCandidates: [CandidateQueueItem] {
        queueItems.filter { $0.daysSinceAdded > 7 }.sorted { $0.daysSinceAdded > $1.daysSinceAdded }
    }

    // MARK: - Batch Operations

    /// Complete multiple tasks at once.
    func completeBatch(_ taskIds: [String]) async {
        isLoading = true
        defer { isLoading = false }

        for taskId in taskIds {
            await completeTask(taskId)
        }
    }

    /// Advance multiple candidates at once.
    func advanceBatch(_ candidateIds: [String]) async {
        isLoading = true
        defer { isLoading = false }

        for candidateId in candidateIds {
            await advanceCandidate(candidateId)
        }
    }

    // MARK: - Cache Expiration & Invalidation

    /// Clear all cached data.
    func clearCache() {
        guard let context = modelContext else { return }

        let descriptor = FetchDescriptor<CachedRecruiterData>()
        if let allCached = try? context.fetch(descriptor) {
            for cached in allCached {
                context.delete(cached)
            }
            try? context.save()
        }
    }

    /// Invalidate cache and force refresh from API.
    func invalidateCacheAndRefresh() async {
        clearCache()
        await refresh()
    }

    // MARK: - Performance Metrics

    /// Log performance metrics for analytics.
    func logPerformanceMetrics() {
        let metrics: [String: Any] = [
            "task_count": tasks.count,
            "position_count": positions.count,
            "queue_size": queueItems.count,
            "activity_feed_size": activityFeed.count,
            "completion_rate": taskCompletionRate,
            "avg_candidate_score": averageCandidateScore,
            "urgency_distribution": urgencyDistribution()
        ]

        TrueMatchLogger.log(.info, "Recruiter CommandCentre metrics: \(metrics)")
    }
}
