//
//  SyncEngine.swift
//  TrueMatch
//

import Foundation
import SwiftData
import Combine

@MainActor
final class SyncEngine: ObservableObject {
    static let shared = SyncEngine()

    @Published var isSyncing: Bool = false
    @Published var lastSyncDate: Date?
    @Published var syncError: String?

    private init() {}

    func syncAll(context: ModelContext) async {
        guard !isSyncing else { return }
        isSyncing = true
        syncError = nil

        do {
            // 1. Push queued offline actions (e.g. assessments created offline).
            await OfflineQueueManager.shared.flush(in: context)

            // 2. Pull the latest assessment list and refresh the cache.
            try await syncAssessments(context: context)

            // 3. Refresh the user profile.
            try await syncProfile(context: context)

            lastSyncDate = .now
        } catch {
            syncError = error.localizedDescription
            TrueMatchLogger.log(.error, "Sync failed: \(error)")
        }

        isSyncing = false
    }

    private func syncAssessments(context: ModelContext) async throws {
        let response = try await APIClient.shared.request(
            endpoint: .listAssessments(),
            type: PaginatedResponse<AssessmentResponse>.self
        )
        for assessment in response.data {
            LocalStore.shared.saveAssessment(assessment, in: context)
        }
    }

    private func syncProfile(context: ModelContext) async throws {
        let profile = try await APIClient.shared.request(
            endpoint: .profile,
            type: UserProfileResponse.self
        )
        LocalStore.shared.saveProfile(profile, in: context)
    }
}
