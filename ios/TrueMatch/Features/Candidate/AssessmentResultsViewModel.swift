//
//  AssessmentResultsViewModel.swift
//  TrueMatch
//
//  Manages assessment results with score visualization, delta computation,
//  strengths/gaps display, and learning path recommendations.
//

import Foundation
import SwiftUI
import Combine
import SwiftData

@MainActor
final class AssessmentResultsViewModel: ObservableObject {
    @Published var assessmentResult: AssessmentResult?
    @Published var traditionalScore: Double = 0
    @Published var semanticScore: Double = 0
    @Published var capabilityScore: Double = 0
    @Published var deltas: [String: Double] = [:]
    @Published var strengths: [SkillEvidence] = []
    @Published var skillGaps: [SkillEvidence] = []
    @Published var learningPaths: [LearningPath] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var viewedAt: Date?

    private let api = APIClient.shared
    private let candidateId: String

    init(candidateId: String) {
        self.candidateId = candidateId
    }

    // MARK: - Loading

    func loadAssessment() async {
        isLoading = true
        defer { isLoading = false }

        do {
            let assessment = try await api.request(
                endpoint: .candidateAssessment(candidateId: candidateId),
                type: AssessmentResult.self
            )
            self.assessmentResult = assessment
            await extractScores()
            computeDeltas()
            self.strengths = assessment.strengths.sorted { $0.confidenceScore > $1.confidenceScore }
            self.skillGaps = assessment.skillGaps.sorted { $0.confidenceScore > $1.confidenceScore }
            self.learningPaths = assessment.learningPaths.sorted { $0.estimatedHours }
            self.viewedAt = Date()
        } catch {
            TrueMatchLogger.log(.error, "Assessment: load failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }

    private func extractScores() async {
        guard let assessment = assessmentResult else { return }

        for score in assessment.scores {
            switch score.type {
            case "traditional":
                self.traditionalScore = score.score
            case "semantic":
                self.semanticScore = score.score
            case "capability":
                self.capabilityScore = score.score
            default:
                break
            }
        }
    }

    private func computeDeltas() {
        // Delta = Capability - Traditional
        let capabilityVsTraditional = capabilityScore - traditionalScore
        deltas["capability_vs_traditional"] = capabilityVsTraditional

        // Delta = Semantic - Traditional
        let semanticVsTraditional = semanticScore - traditionalScore
        deltas["semantic_vs_traditional"] = semanticVsTraditional

        // Delta = Capability - Semantic
        let capabilityVsSemantic = capabilityScore - semanticScore
        deltas["capability_vs_semantic"] = capabilityVsSemantic
    }

    // MARK: - Navigation

    func didTapBrowseJobs() {
        TrueMatchLogger.log(.info, "Assessment: browse jobs tapped")
        // Navigation is handled by parent view
    }
}
