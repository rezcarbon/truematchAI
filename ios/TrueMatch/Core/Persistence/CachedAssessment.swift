//
//  CachedAssessment.swift
//  TrueMatch
//

import Foundation
import SwiftData

/// Local cache of a completed (or in-progress) assessment. The full structured
/// scores are stored as a JSON blob so the on-disk model stays simple while
/// still allowing the original `AssessmentResponse` to be reconstructed offline.
@Model
final class CachedAssessment {
    @Attribute(.unique) var id: String
    var status: String                 // queued, processing, completed, failed
    var traditionalScore: Double?
    var capabilityScore: Double?
    var delta: Double?
    var counterRecommended: Bool
    var positionTitle: String?
    var responseJSON: String?          // JSON-encoded AssessmentResponse
    var createdAt: Date
    var syncStatus: String             // pending, synced, failed

    init(
        id: String = UUID().uuidString,
        status: String,
        traditionalScore: Double? = nil,
        capabilityScore: Double? = nil,
        delta: Double? = nil,
        counterRecommended: Bool = false,
        positionTitle: String? = nil,
        responseJSON: String? = nil,
        createdAt: Date = .now,
        syncStatus: String = "synced"
    ) {
        self.id = id
        self.status = status
        self.traditionalScore = traditionalScore
        self.capabilityScore = capabilityScore
        self.delta = delta
        self.counterRecommended = counterRecommended
        self.positionTitle = positionTitle
        self.responseJSON = responseJSON
        self.createdAt = createdAt
        self.syncStatus = syncStatus
    }

    /// Reconstructs the full `AssessmentResponse` from the cached JSON blob.
    func decodedResponse() -> AssessmentResponse? {
        guard let json = responseJSON, let data = json.data(using: .utf8) else { return nil }
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return try? decoder.decode(AssessmentResponse.self, from: data)
    }
}
