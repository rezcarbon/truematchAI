//
//  RecruiterModels.swift
//  TrueMatch
//
//  Data models for recruiter workflow: tasks, positions, candidates, pipeline stages.
//

import Foundation
import SwiftData

// MARK: - Recruiter Task (approvals, interviews, offers)

struct RecruiterTask: Identifiable, Codable, Hashable {
    let id: String
    let type: TaskType  // approval, interview, offer
    let candidateName: String
    let candidateId: String
    let positionTitle: String
    let positionId: String
    let status: String  // pending, completed, rejected
    let dueDate: Date?
    let createdAt: Date
    let description: String?

    enum TaskType: String, Codable {
        case approval = "approval"
        case interview = "interview"
        case offer = "offer"
    }
}

// MARK: - Active Position

struct ActivePosition: Identifiable, Codable, Hashable {
    let id: String
    let title: String
    let department: String?
    let openCount: Int
    let fillRate: Double  // 0.0 to 1.0
    let urgency: Urgency  // critical, high, normal, low
    let thumbnailUrl: String?
    let activeCount: Int  // candidates in active stage

    enum Urgency: String, Codable {
        case critical, high, normal, low
    }
}

// MARK: - Candidate in Queue

struct CandidateQueueItem: Identifiable, Codable, Hashable {
    let id: String
    let candidateId: String
    let name: String
    let email: String?
    let avatarUrl: String?
    let score: Double  // 0-100
    let delta: Double?  // score change
    let stage: PipelineStage
    let positionId: String
    let positionTitle: String
    let nextAction: String?  // "Review CV", "Schedule Interview", etc.
    let daysSinceAdded: Int
}

// MARK: - Pipeline Stage

enum PipelineStage: String, Codable, CaseIterable {
    case screening = "screening"
    case interview = "interview"
    case offer = "offer"
    case hired = "hired"
}

// MARK: - Pipeline Card (for Kanban)

struct PipelineCard: Identifiable, Codable, Hashable {
    let id: String
    let candidateId: String
    let name: String
    let score: Double
    let delta: Double?
    let stage: PipelineStage
    let avatarUrl: String?
    let positionId: String
    let notesCount: Int
}

// MARK: - Agent Activity Entry

struct AgentActivityEntry: Identifiable, Codable, Hashable {
    let id: String
    let agentName: String
    let action: String  // "Reviewed CV", "Sent offer", etc.
    let candidateName: String
    let positionTitle: String
    let timestamp: Date
    let status: ActivityStatus  // success, pending, failed

    enum ActivityStatus: String, Codable {
        case success, pending, failed
    }
}

// MARK: - Search Result

struct RecruiterSearchResult: Identifiable, Codable, Hashable {
    let id: String
    let candidateId: String
    let name: String
    let email: String?
    let score: Double
    let stage: PipelineStage
    let positionTitle: String
    let positionId: String
    let avatarUrl: String?
    let matchPercentage: Double
}

// MARK: - Decision Record

struct DecisionRecord: Identifiable, Codable {
    let id: String
    let candidateId: String
    let candidateName: String
    let positionId: String
    let positionTitle: String
    let decision: Decision  // approve, reject, revisit
    let feedback: String?
    let timestamp: Date
    let recordedBy: String?

    enum Decision: String, Codable {
        case approve, reject, revisit
    }
}

// MARK: - Cached Recruiter Data (SwiftData)

@Model
final class CachedRecruiterData {
    @Attribute(.unique) var id: String = UUID().uuidString
    var dataType: String  // "tasks", "positions", "queue", "activity", "pipeline"
    var resourceId: String?  // for filtering by position/candidate
    var jsonData: String?
    var lastFetched: Date
    var expiresAt: Date

    init(dataType: String, resourceId: String? = nil, jsonData: String? = nil) {
        self.dataType = dataType
        self.resourceId = resourceId
        self.jsonData = jsonData
        self.lastFetched = .now
        self.expiresAt = Calendar.current.date(byAdding: .hour, value: 1, to: .now) ?? .now
    }
}

// MARK: - API Requests

struct RecordDecisionRequest: Codable {
    let decision: String  // approve, reject, revisit
    let feedback: String?
    let timestamp: Date
}

struct SearchCandidatesRequest: Codable {
    let query: String?
    let stage: String?
    let scoreMin: Double?
    let scoreMax: Double?
    let positionId: String?
    let limit: Int = 50
}

// MARK: - API Responses

struct RecruiterCommandCentreResponse: Codable {
    let tasks: [RecruiterTask]
    let positions: [ActivePosition]
    let queueItems: [CandidateQueueItem]
    let activityFeed: [AgentActivityEntry]
}

struct PipelineResponse: Codable {
    let cards: [PipelineCard]
    let updatedAt: Date
}

struct SearchResultsResponse: Codable {
    let results: [RecruiterSearchResult]
    let total: Int
    let cursor: String?
}
