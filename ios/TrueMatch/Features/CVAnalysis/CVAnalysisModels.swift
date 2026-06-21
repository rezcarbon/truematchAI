//
//  CVAnalysisModels.swift
//  TrueMatch
//
//  DTOs for the candidate CV Analysis feature (gap analysis + improvement
//  recommendations). NOTE: this backend feature serializes its RESULT with
//  camelCase keys on the wire (alias_generator=to_camel), which pass through
//  the `.convertFromSnakeCase` decoder unchanged — so the Swift property names
//  below match the wire exactly. The START request/response use snake_case.
//

import Foundation

// MARK: - Start

struct CVAnalysisStartRequest: Codable {
    let resumeId: String
    let targetRole: String
    let targetSeniority: String   // junior | mid | senior | lead
}

struct CVAnalysisStartResponse: Codable {
    let analysisId: String
    let status: String
}

// MARK: - Result (camelCase on the wire)

struct CVGapItem: Codable, Identifiable {
    var id: String { capability }
    let capability: String
    let importance: String?
    let description: String?
    let howToImprove: String?
}

struct CVRecommendation: Codable, Identifiable {
    var id: String { suggestion }
    let category: String?
    let suggestion: String
    let priority: String?
    let example: String?
}

struct CVJobMatch: Codable, Identifiable {
    var id: String { jobTitle }
    let jobTitle: String
    let matchScore: Int?
    let whyFit: String?
}

struct CVAnalysisResultDTO: Codable {
    let analysisId: String
    let status: String
    let strengthSummary: String?
    let missingCapabilities: [CVGapItem]?
    let weaknessAreas: [CVGapItem]?
    let improvementSuggestions: [CVRecommendation]?
    let growthOpportunities: [String]?
    let trajectoryAnalysis: String?
    let marketPositioning: String?
    let totalMatchingJobs: Int?
    let topMatchingPositions: [CVJobMatch]?
}

// MARK: - Resume list (for the picker; /files/resumes is snake_case)

struct ResumeListItemDTO: Codable, Identifiable {
    let id: String
    let filename: String?
    let fileType: String
    let createdAt: String
}

struct ResumeListResponseDTO: Codable {
    let items: [ResumeListItemDTO]
    let total: Int
}
