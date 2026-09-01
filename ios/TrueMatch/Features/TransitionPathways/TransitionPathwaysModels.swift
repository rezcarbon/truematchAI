import Foundation

// Wire format is snake_case; APIClient uses .convertFromSnakeCase / .convertToSnakeCase.

struct TransitionStartRequest: Codable {
    let resumeId: String
    let currentRole: String?
    let target: String?
}

struct TransitionStartResponse: Codable {
    let analysisId: String
    let status: String
}

struct CourseRecommendationDTO: Codable {
    let capability: String
    let title: String
    let provider: String
    let url: String?
    let format: String?
    let durationWeeks: Int?
    let level: String?
    let relevance: String?
}

struct UpskillingItemDTO: Codable {
    let capability: String
    let why: String?
    let how: String?
    let recommendedTraining: [CourseRecommendationDTO]?
}

struct TransitionTimelineDTO: Codable {
    let monthsMin: Int
    let monthsMax: Int
    let confidence: String
    let basis: String?
}

struct TransitionOptionDTO: Codable {
    let role: String
    let direction: String         // lateral | upward | adjacent
    let feasibility: String       // READY | STRETCH | ASPIRATIONAL
    let rationale: String
    let transferableStrengths: [String]?
    let upskillingGap: [UpskillingItemDTO]?
    let timeline: TransitionTimelineDTO?
    let evidenceStrength: String  // HIGH | MEDIUM | WEAK
}

struct TransitionResultDTO: Codable {
    let analysisId: String
    let status: String            // pending | analyzing | completed | failed
    let currentRole: String?
    let sourceLanguage: String?
    let capabilityScore: Int?
    let readinessSummary: String?
    let transitionOptions: [TransitionOptionDTO]?
    let honestyNotes: String?
    let droppedUngrounded: Int?
    let error: String?
}

// --- Phase 3: longitudinal tracking ---------------------------------------

struct TransitionTrackRequest: Codable {
    let enabled: Bool
}

struct TransitionTrackResponse: Codable {
    let tracking: Bool
    let nextReviewAt: String?
}

struct TrajectoryPointDTO: Codable {
    let analysisId: String
    let date: String?
    let capabilityScore: Int?
    let options: Int
    let ready: Int
    let stretch: Int
    let aspirational: Int
    let topRole: String?
}
