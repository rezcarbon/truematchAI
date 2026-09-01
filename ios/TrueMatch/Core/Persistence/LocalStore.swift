//
//  LocalStore.swift
//  TrueMatch
//

import Foundation
import SwiftData

@MainActor
final class LocalStore {
    static let shared = LocalStore()

    private init() {}

    private static let encoder: JSONEncoder = {
        let e = JSONEncoder()
        e.dateEncodingStrategy = .iso8601
        e.keyEncodingStrategy = .convertToSnakeCase
        return e
    }()

    // MARK: - Assessments

    func saveAssessment(_ response: AssessmentResponse, positionTitle: String? = nil, in context: ModelContext) {
        let json = (try? Self.encoder.encode(response)).flatMap { String(data: $0, encoding: .utf8) }

        // Upsert: delete any existing record with this id first.
        let id = response.id
        let descriptor = FetchDescriptor<CachedAssessment>(
            predicate: #Predicate { $0.id == id }
        )
        if let existing = try? context.fetch(descriptor) {
            for item in existing { context.delete(item) }
        }

        let cached = CachedAssessment(
            id: response.id,
            status: response.status.rawValue,
            traditionalScore: response.traditionalScore?.score,
            capabilityScore: response.capabilityScore?.score,
            delta: response.delta,
            counterRecommended: response.counterRecommendation?.triggered ?? false,
            positionTitle: positionTitle,
            responseJSON: json,
            createdAt: response.createdAt ?? .now,
            syncStatus: "synced"
        )
        context.insert(cached)
        try? context.save()
    }

    func fetchAssessments(in context: ModelContext) -> [CachedAssessment] {
        let descriptor = FetchDescriptor<CachedAssessment>(
            sortBy: [SortDescriptor(\.createdAt, order: .reverse)]
        )
        return (try? context.fetch(descriptor)) ?? []
    }

    func fetchAssessment(id: String, in context: ModelContext) -> CachedAssessment? {
        let descriptor = FetchDescriptor<CachedAssessment>(
            predicate: #Predicate { $0.id == id }
        )
        return (try? context.fetch(descriptor))?.first
    }

    // MARK: - Profile

    func saveProfile(_ response: UserProfileResponse, in context: ModelContext) {
        let userId = response.userId
        let descriptor = FetchDescriptor<CachedProfile>(
            predicate: #Predicate { $0.userId == userId }
        )
        if let existing = try? context.fetch(descriptor) {
            for item in existing { context.delete(item) }
        }

        let cached = CachedProfile(
            userId: response.userId,
            displayName: response.displayName,
            email: response.email,
            maskedNric: response.maskedNric,
            lastSynced: .now
        )
        context.insert(cached)
        try? context.save()
    }

    // MARK: - Resume Cache

    func saveResume(_ resume: ResumeCache, in context: ModelContext) {
        context.insert(resume)
        try? context.save()
    }

    // MARK: - Cleanup

    func pruneOldAssessments(olderThan days: Int = 90, in context: ModelContext) {
        let cutoff = Calendar.current.date(byAdding: .day, value: -days, to: .now)!
        let descriptor = FetchDescriptor<CachedAssessment>(
            predicate: #Predicate { $0.createdAt < cutoff && $0.syncStatus == "synced" }
        )
        if let old = try? context.fetch(descriptor) {
            for item in old {
                context.delete(item)
            }
            try? context.save()
        }
    }
}
