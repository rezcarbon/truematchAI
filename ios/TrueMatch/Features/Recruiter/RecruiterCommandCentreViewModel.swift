//
//  RecruiterCommandCentreViewModel.swift
//  TrueMatch
//
//  Command centre for recruiters: displays today's tasks, active positions,
//  candidate work queue, and agent activity feed. Integrates with SwiftData
//  for offline-first caching.
//

import Foundation
import SwiftUI
import SwiftData
import Combine

@MainActor
final class RecruiterCommandCentreViewModel: ObservableObject {
    @Published var tasks: [RecruiterTask] = []
    @Published var positions: [ActivePosition] = []
    @Published var queueItems: [CandidateQueueItem] = []
    @Published var activityFeed: [AgentActivityEntry] = []

    @Published var isLoading = false
    @Published var isRefreshing = false
    @Published var errorMessage: String?

    private let api = APIClient.shared
    private let localStore = LocalStore.shared
    private var modelContext: ModelContext?
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Initialization

    func setupContext(_ context: ModelContext) {
        self.modelContext = context
        Task { await loadData() }
    }

    // MARK: - Data Loading

    /// Load all command centre data from API or cache.
    func loadData() async {
        guard isLoading == false else { return }
        isLoading = true
        defer { isLoading = false }

        do {
            let response = try await api.request(
                endpoint: .recruiterCommandCentre,
                type: RecruiterCommandCentreResponse.self
            )
            await MainActor.run {
                self.tasks = response.tasks
                self.positions = response.positions
                self.queueItems = response.queueItems
                self.activityFeed = response.activityFeed
                self.cacheData(response)
            }
        } catch {
            TrueMatchLogger.log(.error, "Recruiter: load command centre failed: \(error)")
            await loadFromCache()
            self.errorMessage = "Could not load data. Showing cached version."
        }
    }

    /// Pull-to-refresh from API.
    func refresh() async {
        isRefreshing = true
        defer { isRefreshing = false }

        do {
            let response = try await api.request(
                endpoint: .recruiterCommandCentre,
                type: RecruiterCommandCentreResponse.self
            )
            await MainActor.run {
                self.tasks = response.tasks
                self.positions = response.positions
                self.queueItems = response.queueItems
                self.activityFeed = response.activityFeed
                self.cacheData(response)
                self.errorMessage = nil
            }
        } catch {
            TrueMatchLogger.log(.error, "Recruiter: refresh failed: \(error)")
            self.errorMessage = error.localizedDescription
        }
    }

    /// Load data from SwiftData cache.
    private func loadFromCache() async {
        guard let context = modelContext else { return }

        let descriptor = FetchDescriptor<CachedRecruiterData>(
            predicate: #Predicate { $0.dataType == "tasks" && $0.expiresAt > Date() }
        )
        if let cached = try? context.fetch(descriptor).first,
           let json = cached.jsonData?.data(using: .utf8),
           let tasks = try? JSONDecoder().decode([RecruiterTask].self, from: json) {
            self.tasks = tasks
        }

        // Similar for other data types
        let posDescriptor = FetchDescriptor<CachedRecruiterData>(
            predicate: #Predicate { $0.dataType == "positions" && $0.expiresAt > Date() }
        )
        if let cached = try? context.fetch(posDescriptor).first,
           let json = cached.jsonData?.data(using: .utf8),
           let positions = try? JSONDecoder().decode([ActivePosition].self, from: json) {
            self.positions = positions
        }
    }

    /// Cache response data to SwiftData.
    private func cacheData(_ response: RecruiterCommandCentreResponse) {
        guard let context = modelContext else { return }

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601

        if let tasksJSON = try? encoder.encode(response.tasks),
           let tasksString = String(data: tasksJSON, encoding: .utf8) {
            let tasksCached = CachedRecruiterData(dataType: "tasks", jsonData: tasksString)
            context.insert(tasksCached)
        }

        if let posJSON = try? encoder.encode(response.positions),
           let posString = String(data: posJSON, encoding: .utf8) {
            let posCached = CachedRecruiterData(dataType: "positions", jsonData: posString)
            context.insert(posCached)
        }

        try? context.save()
    }

    // MARK: - Task Actions

    /// Mark a task as completed.
    func completeTask(_ taskId: String) async {
        do {
            try await api.requestVoid(endpoint: .recruiterCompleteTask(taskId: taskId))
            tasks.removeAll { $0.id == taskId }
            TrueMatchLogger.log(.info, "Recruiter: task \(taskId) completed")
        } catch {
            TrueMatchLogger.log(.error, "Recruiter: complete task failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Queue Actions

    /// Advance a candidate to the next stage in the pipeline.
    func advanceCandidate(_ candidateId: String) async {
        do {
            try await api.requestVoid(
                endpoint: .recruiterAdvanceCandidate(candidateId: candidateId)
            )
            if let index = queueItems.firstIndex(where: { $0.candidateId == candidateId }) {
                queueItems.remove(at: index)
            }
            TrueMatchLogger.log(.info, "Recruiter: candidate \(candidateId) advanced")
        } catch {
            TrueMatchLogger.log(.error, "Recruiter: advance candidate failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Filtered Views

    /// Today's tasks (due today).
    var todaysTasks: [RecruiterTask] {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)
        return tasks.filter { task in
            guard let dueDate = task.dueDate else { return false }
            return calendar.startOfDay(for: dueDate) == today
        }
    }

    /// Pending (overdue) tasks.
    var pendingTasks: [RecruiterTask] {
        tasks.filter { $0.status == "pending" }
    }

    /// Critical urgency positions.
    var criticalPositions: [ActivePosition] {
        positions.filter { $0.urgency == .critical }
    }

    /// Tasks due in next 7 days.
    var upcomingTasks: [RecruiterTask] {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)
        let sevenDaysOut = calendar.date(byAdding: .day, value: 7, to: today)!
        return tasks.filter { task in
            guard let dueDate = task.dueDate else { return false }
            let due = calendar.startOfDay(for: dueDate)
            return due > today && due <= sevenDaysOut
        }
    }

    /// Recent activity (last 24 hours).
    var recentActivity: [AgentActivityEntry] {
        let oneDayAgo = Calendar.current.date(byAdding: .day, value: -1, to: .now)!
        return activityFeed.filter { $0.timestamp > oneDayAgo }
    }
}
