//
//  PositionModels.swift
//  TrueMatch
//
//  DTOs for the recruiter Positions + Pipeline views. The APIClient decoder uses
//  `.convertFromSnakeCase`, so wire fields like `jd_quality_score` map to
//  `jdQualityScore` here.
//

import Foundation

struct PositionDTO: Codable, Identifiable {
    let id: String
    let title: String
    let description: String?
    let status: String?
    let jdQualityScore: Int?
}

struct PositionListResponse: Codable {
    let items: [PositionDTO]
    let total: Int
}

/// One candidate in a position's pipeline (an Application row).
struct PipelineCandidateDTO: Codable, Identifiable {
    let id: String
    let resumeId: String?
    let userId: String?
    let stage: String
    let source: String?
}

// MARK: - JD quality (position detail)

struct JDIssueDTO: Codable, Identifiable {
    var id: String { type + (detail ?? "") }
    let type: String
    let severity: String?
    let detail: String?
    let recommendation: String?
}

struct JDIssuesWrapper: Codable {
    let issues: [JDIssueDTO]?
}

struct PositionDetailDTO: Codable {
    let id: String
    let title: String
    let description: String?
    let jdQualityScore: Int?
    let jdIssues: JDIssuesWrapper?
}
