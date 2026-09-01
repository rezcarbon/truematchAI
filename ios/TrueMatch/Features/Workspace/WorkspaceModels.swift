//
//  WorkspaceModels.swift
//  TrueMatch
//
//  DTOs for the recruiter/admin workspace features (reviews, decisions, JD
//  simulation, dashboards, governance, compliance). All map 1:1 to verified
//  backend responses. The APIClient decoder uses `.convertFromSnakeCase`.
//

import Foundation

// MARK: - Assessments (recruiter review queue)

struct AssessmentSummaryDTO: Codable, Identifiable {
    let id: String
    let resumeId: String
    let positionId: String
    let userId: String
    let status: String
    let traditionalScore: Int?
    let capabilityScore: Int?
    let scoreDelta: Int?
    let counterRecTriggered: Bool?
}

struct AssessmentListResponse: Codable {
    let items: [AssessmentSummaryDTO]
    let total: Int
    let page: Int
    let pageSize: Int
}

// MARK: - Decisions

/// POST /decisions — records a hiring decision (and drives the learning loop).
struct DecisionRequest: Codable {
    let assessmentId: String
    let positionId: String
    let decision: String           // advance | reject | hold | interview | hire
    let aiRecommendationFollowed: Bool
    let overrideReasoning: String?
}

struct DecisionResponseDTO: Codable {
    let id: String
    let decision: String
}

// MARK: - JD Simulation

struct JDSimRequest: Codable {
    let jdText: String
    let simulationType: String      // requirement_fit | market_comparison | candidate_archetype
}

struct JDSimStartResponse: Codable {
    let simulationId: String
    let status: String
}

struct CreepWarningDTO: Codable, Identifiable {
    var id: String { issue }
    let severity: String
    let issue: String
    let suggestion: String?
}

struct WordingSuggestionDTO: Codable, Identifiable {
    var id: String { capabilityArea }
    let capabilityArea: String
    let reasoning: String
}

struct JDSimResultDTO: Codable {
    let simulationId: String
    let status: String
    let qualityScore: Int?
    let requirementDifficultyScore: Int?
    let marketPositioning: String?
    let bestArchetypeFit: String?
    let creepWarnings: [CreepWarningDTO]?
    let capabilityVerbiageSuggestions: [WordingSuggestionDTO]?
    let missingSections: [String]?
    let qualityIssues: [String]?
}

// MARK: - Recruiter metrics (dashboard)

struct RecruiterMetricValues: Codable {
    let candidatesReviewed: Int
    let interviewsScheduled: Int
    let offersMade: Int
    let hireRate: Double
    let avgTimeToHire: Int
}

struct RecruiterMetricEntry: Codable, Identifiable {
    var id: String { recruiterId }
    let recruiterId: String
    let recruiterName: String?
    let metrics: RecruiterMetricValues
}

struct RecruiterMetricsResponse: Codable {
    let recruiters: [RecruiterMetricEntry]
}

// MARK: - Admin metrics (dashboard)

struct AdminGovernanceCounts: Codable {
    let pending: Int
    let approved: Int
    let rejected: Int
    let escalated: Int
    let total: Int
}

struct AdminLast: Codable {
    let totalSessions: Int
}

struct AdminSystemHealth: Codable {
    let status: String
    let last24Hours: AdminLast
    let last7Days: AdminLast
    let governance: AdminGovernanceCounts
}

struct AdminMetricsData: Codable {
    let systemHealth: AdminSystemHealth
}

struct AdminMetricsResponse: Codable {
    let status: String
    let data: AdminMetricsData
}

// MARK: - Governance reviews

struct GovernanceReviewItemDTO: Codable, Identifiable {
    let id: String
    let resourceId: String?
    let reviewType: String?
    let status: String
    let failureReason: String?
}

struct GovernanceReviewListResponse: Codable {
    let items: [GovernanceReviewItemDTO]
    let total: Int
    let pending: Int
    let approved: Int
    let rejected: Int
    let escalated: Int
}

struct ApproveReviewRequest: Codable {
    let decision: String   // approved | rejected | escalated
    let notes: String?
}

// MARK: - Compliance system status

struct ComplianceLearning: Codable {
    let weightUpdates: Int
    let capabilitiesLearned: Int
    let credentialEquivalencies: Int
    let totalUpdatesApplied: Int
}

struct ComplianceProvenance: Codable {
    let recordsCreated: Int
}

struct ComplianceStatusResponse: Codable {
    // `.convertFromSnakeCase` maps phase_c_provenance → phaseCProvenance, etc.
    let status: String
    let phaseCProvenance: ComplianceProvenance
    let phaseDLearning: ComplianceLearning
}
