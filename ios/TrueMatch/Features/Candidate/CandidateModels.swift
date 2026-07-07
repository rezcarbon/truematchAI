//
//  CandidateModels.swift
//  TrueMatch
//
//  DTOs and models for the Candidate Mode feature. Includes assessment results,
//  job recommendations, career coaching, and application tracking.
//

import Foundation
import SwiftData

// MARK: - Assessment Results

struct AssessmentScore: Codable, Identifiable {
    let id: String
    let type: String // "traditional", "semantic", "capability"
    let score: Double // 0-100
    let percentile: Double // 0-100
    let confidence: Double // 0-1
    let timestamp: String
}

struct SkillEvidence: Codable, Identifiable {
    let id: String
    let skillName: String
    let proficiency: String // "beginner", "intermediate", "advanced", "expert"
    let evidence: [String] // supporting excerpts or links
    let confidenceScore: Double
}

struct AssessmentResult: Codable, Identifiable {
    let id: String
    let candidateId: String
    let scores: [AssessmentScore]
    let strengths: [SkillEvidence]
    let skillGaps: [SkillEvidence]
    let learningPaths: [LearningPath]
    let createdAt: String
    let updatedAt: String
}

struct LearningPath: Codable, Identifiable {
    let id: String
    let skillName: String
    let currentLevel: String
    let targetLevel: String
    let resources: [LearningResource]
    let estimatedHours: Int
}

struct LearningResource: Codable, Identifiable {
    let id: String
    let title: String
    let resourceType: String // "course", "article", "tutorial", "book"
    let provider: String
    let url: String?
    let duration: Int? // in minutes
}

// MARK: - Job Recommendations

struct JobRecommendation: Codable, Identifiable {
    let id: String
    let jobTitle: String
    let company: String
    let location: String
    let matchScore: Double // 0-100
    let traditionalScore: Double
    let semanticScore: Double
    let capabilityScore: Double
    let requiredSkills: [SkillMatch]
    let matchedStrengths: [String]
    let skillGaps: [String]
    let jobDescription: String
    let salaryRange: SalaryRange?
    let jobLevel: String
    let jobType: String // "full-time", "contract", etc.
    let postedDate: String
    let applicationDeadline: String?
    let url: String
}

struct SkillMatch: Codable, Identifiable {
    let id: String
    let skillName: String
    let requiredLevel: String
    let candidateLevel: String
    let matchPercentage: Double
}

struct SalaryRange: Codable {
    let min: Int
    let max: Int
    let currency: String
}

// MARK: - Career Coaching

struct CareerCoachMessage: Codable, Identifiable {
    let id: String
    let role: String // "user" or "assistant"
    let content: String
    let structuredContent: StructuredResponse?
    let timestamp: String
}

struct StructuredResponse: Codable {
    let steps: [CoachingStep]?
    let resources: [CoachingResource]?
    let nextSteps: [String]?
    let actionItems: [String]?
}

struct CoachingStep: Codable, Identifiable {
    let id: String
    let stepNumber: Int
    let title: String
    let description: String
    let resources: [CoachingResource]?
}

struct CoachingResource: Codable, Identifiable {
    let id: String
    let title: String
    let resourceType: String
    let url: String?
    let duration: Int?
}

// MARK: - Application Tracking

struct ApplicationStatus: Codable, Identifiable {
    let id: String
    let candidateId: String
    let jobId: String
    let jobTitle: String
    let company: String
    let stage: String // "applied", "reviewing", "interviewing", "offer", "rejected", "closed"
    let appliedDate: String
    let lastUpdateDate: String
    let timeline: [ApplicationEvent]
    let interviewSessions: [InterviewSession]
    let offerDetails: OfferDetails?
    let notes: String?
}

struct ApplicationEvent: Codable, Identifiable {
    let id: String
    let eventType: String // "applied", "reviewed", "scheduled", "interviewed", "rejected", "offer"
    let description: String
    let timestamp: String
    let details: String?
}

struct InterviewSession: Codable, Identifiable {
    let id: String
    let interviewType: String // "phone", "technical", "behavioral", "final"
    let scheduledDate: String?
    let duration: Int? // in minutes
    let interviewer: String?
    let status: String // "scheduled", "completed", "cancelled"
    let feedbackReceived: Bool
    let prepMaterials: [InterviewPrepMaterial]?
}

struct InterviewPrepMaterial: Codable, Identifiable {
    let id: String
    let title: String
    let contentType: String // "guide", "question", "resource"
    let content: String
}

struct OfferDetails: Codable {
    let baseSalary: Int
    let bonus: Int?
    let equity: String?
    let benefits: [String]
    let startDate: String
    let offerLetterUrl: String?
    let responseDeadline: String?
    let status: String // "pending", "accepted", "declined"
}

// MARK: - Request Models

struct GetAssessmentRequest: Codable {
    let candidateId: String
}

struct GetJobRecommendationsRequest: Codable {
    let candidateId: String
    let limit: Int = 20
    let offset: Int = 0
}

struct SaveJobRequest: Codable {
    let candidateId: String
    let jobId: String
    let saved: Bool
}

struct RejectJobRequest: Codable {
    let candidateId: String
    let jobId: String
}

struct GetApplicationsRequest: Codable {
    let candidateId: String
}

// MARK: - SwiftData Models

@Model
final class CachedAssessmentResult {
    @Attribute(.unique) var id: String
    var candidateId: String
    var scores: [CachedAssessmentScore]
    var strengths: [CachedSkillEvidence]
    var skillGaps: [CachedSkillEvidence]
    var learningPaths: [CachedLearningPath]
    var createdAt: Date
    var updatedAt: Date
    var syncedAt: Date

    init(id: String, candidateId: String, scores: [CachedAssessmentScore],
         strengths: [CachedSkillEvidence], skillGaps: [CachedSkillEvidence],
         learningPaths: [CachedLearningPath], createdAt: Date, updatedAt: Date) {
        self.id = id
        self.candidateId = candidateId
        self.scores = scores
        self.strengths = strengths
        self.skillGaps = skillGaps
        self.learningPaths = learningPaths
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.syncedAt = Date()
    }
}

@Model
final class CachedAssessmentScore {
    var id: String
    var type: String
    var score: Double
    var percentile: Double
    var confidence: Double
    var timestamp: Date

    init(id: String, type: String, score: Double, percentile: Double,
         confidence: Double, timestamp: Date) {
        self.id = id
        self.type = type
        self.score = score
        self.percentile = percentile
        self.confidence = confidence
        self.timestamp = timestamp
    }
}

@Model
final class CachedSkillEvidence {
    var id: String
    var skillName: String
    var proficiency: String
    var evidence: [String]
    var confidenceScore: Double

    init(id: String, skillName: String, proficiency: String,
         evidence: [String], confidenceScore: Double) {
        self.id = id
        self.skillName = skillName
        self.proficiency = proficiency
        self.evidence = evidence
        self.confidenceScore = confidenceScore
    }
}

@Model
final class CachedLearningPath {
    var id: String
    var skillName: String
    var currentLevel: String
    var targetLevel: String
    var estimatedHours: Int

    init(id: String, skillName: String, currentLevel: String,
         targetLevel: String, estimatedHours: Int) {
        self.id = id
        self.skillName = skillName
        self.currentLevel = currentLevel
        self.targetLevel = targetLevel
        self.estimatedHours = estimatedHours
    }
}
