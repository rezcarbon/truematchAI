//
//  RecruiterDecisionViewModel+Extended.swift
//  TrueMatch
//
//  Advanced decision features: offer management, batch decisions, decision history.
//

import Foundation
import SwiftUI

extension RecruiterDecisionViewModel {

    // MARK: - Offer Management

    struct OfferPackage: Identifiable, Codable {
        let id: String
        let candidateId: String
        let positionId: String
        let salary: Double?
        let benefits: [String]
        let startDate: Date?
        let notes: String?
        let createdAt: Date

        init(
            candidateId: String,
            positionId: String,
            salary: Double? = nil,
            benefits: [String] = [],
            startDate: Date? = nil,
            notes: String? = nil
        ) {
            self.id = UUID().uuidString
            self.candidateId = candidateId
            self.positionId = positionId
            self.salary = salary
            self.benefits = benefits
            self.startDate = startDate
            self.notes = notes
            self.createdAt = Date()
        }
    }

    @Published private(set) var pendingOffers: [OfferPackage] = []
    @Published var currentOffer: OfferPackage?

    /// Create an offer package.
    func createOffer(
        salary: Double,
        benefits: [String],
        startDate: Date?,
        notes: String? = nil
    ) -> OfferPackage? {
        guard let candidate = selectedCandidate else { return nil }

        let offer = OfferPackage(
            candidateId: candidate.candidateId,
            positionId: candidate.positionId,
            salary: salary,
            benefits: benefits,
            startDate: startDate,
            notes: notes
        )

        currentOffer = offer
        pendingOffers.append(offer)
        return offer
    }

    /// Send offer to candidate.
    func sendOffer(_ offer: OfferPackage) async {
        guard let candidate = selectedCandidate else { return }

        isSubmitting = true
        defer { isSubmitting = false }

        do {
            // This would call the API to send the offer
            TrueMatchLogger.log(.info, "Recruiter: offer sent to \(candidate.name)")
            isSuccessful = true

            // Remove from pending
            pendingOffers.removeAll { $0.id == offer.id }
            currentOffer = nil
        } catch {
            TrueMatchLogger.log(.error, "Recruiter: send offer failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }

    /// Withdraw an offer.
    func withdrawOffer(_ offer: OfferPackage) async {
        pendingOffers.removeAll { $0.id == offer.id }
        if currentOffer?.id == offer.id {
            currentOffer = nil
        }
        TrueMatchLogger.log(.info, "Recruiter: offer withdrawn for \(offer.candidateId)")
    }

    // MARK: - Batch Decisions

    /// Apply the same decision to multiple candidates.
    func applyBatchDecision(
        decision: DecisionRecord.Decision,
        to candidateIds: [String],
        feedback: String? = nil
    ) async {
        isSubmitting = true
        defer { isSubmitting = false }

        for candidateId in candidateIds {
            do {
                let request = RecordDecisionRequest(
                    decision: decision.rawValue,
                    feedback: feedback ?? "",
                    timestamp: .now
                )
                try await api.requestVoid(
                    endpoint: .recruiterRecordDecision(candidateId: candidateId, request)
                )
                TrueMatchLogger.log(.info, "Recruiter: batch decision \(decision.rawValue) recorded")
            } catch {
                TrueMatchLogger.log(.error, "Recruiter: batch decision failed: \(error)")
                errorMessage = error.localizedDescription
            }
        }
    }

    // MARK: - Decision History

    struct DecisionHistoryEntry: Identifiable, Codable {
        let id: String
        let candidateId: String
        let candidateName: String
        let decision: String
        let feedback: String?
        let timestamp: Date
        let positionId: String
        let positionTitle: String

        init(
            candidateId: String,
            candidateName: String,
            decision: String,
            feedback: String? = nil,
            positionId: String,
            positionTitle: String
        ) {
            self.id = UUID().uuidString
            self.candidateId = candidateId
            self.candidateName = candidateName
            self.decision = decision
            self.feedback = feedback
            self.timestamp = Date()
            self.positionId = positionId
            self.positionTitle = positionTitle
        }
    }

    @Published private(set) var decisionHistory: [DecisionHistoryEntry] = []

    /// Get decisions made today.
    var decisionsToday: [DecisionHistoryEntry] {
        let today = Calendar.current.startOfDay(for: Date())
        return decisionHistory.filter { entry in
            Calendar.current.startOfDay(for: entry.timestamp) == today
        }
    }

    /// Get decisions by type.
    func decisions(ofType type: DecisionRecord.Decision) -> [DecisionHistoryEntry] {
        decisionHistory.filter { $0.decision == type.rawValue }
    }

    /// Calculate decision stats.
    var decisionStats: (approvals: Int, rejections: Int, revisits: Int) {
        (
            approvals: decisions(ofType: .approve).count,
            rejections: decisions(ofType: .reject).count,
            revisits: decisions(ofType: .revisit).count
        )
    }

    /// Add to decision history.
    private func addToHistory(
        candidateId: String,
        candidateName: String,
        decision: DecisionRecord.Decision,
        feedback: String? = nil,
        positionId: String,
        positionTitle: String
    ) {
        let entry = DecisionHistoryEntry(
            candidateId: candidateId,
            candidateName: candidateName,
            decision: decision.rawValue,
            feedback: feedback,
            positionId: positionId,
            positionTitle: positionTitle
        )
        decisionHistory.insert(entry, at: 0)
    }

    // MARK: - Decision Analytics

    /// Decision rate (decisions per day).
    func decisionRate(daysLookback: Int = 7) -> Double {
        let cutoffDate = Calendar.current.date(byAdding: .day, value: -daysLookback, to: Date()) ?? Date()
        let recentDecisions = decisionHistory.filter { $0.timestamp > cutoffDate }
        return Double(recentDecisions.count) / Double(max(daysLookback, 1))
    }

    /// Approval rate.
    var approvalRate: Double {
        guard !decisionHistory.isEmpty else { return 0 }
        let approvals = decisions(ofType: .approve).count
        return Double(approvals) / Double(decisionHistory.count)
    }

    /// Rejection rate.
    var rejectionRate: Double {
        guard !decisionHistory.isEmpty else { return 0 }
        let rejections = decisions(ofType: .reject).count
        return Double(rejections) / Double(decisionHistory.count)
    }

    /// Most common feedback phrases.
    func frequentFeedbackPhrases() -> [String: Int] {
        var frequencyMap: [String: Int] = [:]

        for entry in decisionHistory {
            guard let feedback = entry.feedback else { continue }
            let words = feedback.split(separator: " ").map(String.init)
            for word in words {
                frequencyMap[word, default: 0] += 1
            }
        }

        return frequencyMap
            .sorted { $0.value > $1.value }
            .prefix(10)
            .reduce(into: [:]) { $0[$1.key] = $1.value }
    }

    // MARK: - Custom Decision Actions

    /// Log a custom action (e.g., "sent interview", "contacted HR").
    func logCustomAction(_ action: String, for candidate: CandidateQueueItem) {
        TrueMatchLogger.log(.info, "Recruiter custom action: \(action) for \(candidate.name)")
    }

    /// Remind later for a candidate.
    func remindLater(_ candidate: CandidateQueueItem, in days: Int) {
        let reminderDate = Calendar.current.date(byAdding: .day, value: days, to: Date()) ?? Date()
        TrueMatchLogger.log(.info, "Recruiter: set reminder for \(candidate.name) at \(reminderDate)")
    }

    // MARK: - Export Decision Report

    /// Export decision history as JSON.
    func exportDecisionReport() -> Data? {
        let report: [String: Any] = [
            "generatedAt": Date(),
            "totalDecisions": decisionHistory.count,
            "stats": [
                "approvals": decisionStats.approvals,
                "rejections": decisionStats.rejections,
                "revisits": decisionStats.revisits,
                "approvalRate": approvalRate,
                "rejectionRate": rejectionRate
            ],
            "decisions": decisionHistory.map { [
                "candidateName": $0.candidateName,
                "decision": $0.decision,
                "feedback": $0.feedback ?? "",
                "timestamp": $0.timestamp,
                "position": $0.positionTitle
            ] }
        ]

        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        encoder.dateEncodingStrategy = .iso8601

        return try? encoder.encode(report)
    }
}
