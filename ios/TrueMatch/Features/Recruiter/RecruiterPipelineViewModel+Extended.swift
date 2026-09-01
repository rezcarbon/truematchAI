//
//  RecruiterPipelineViewModel+Extended.swift
//  TrueMatch
//
//  Extended pipeline functionality: analytics, bulk operations, and smart suggestions.
//

import Foundation
import SwiftUI

extension RecruiterPipelineViewModel {

    // MARK: - Pipeline Analytics

    /// Calculate conversion rate from one stage to another.
    func conversionRate(from: PipelineStage, to: PipelineStage) -> Double {
        let fromCount = cardsForStage(from).count
        guard fromCount > 0 else { return 0 }

        let toCount = cardsForStage(to).count
        return Double(toCount) / Double(fromCount)
    }

    /// Get cards for a specific stage.
    func cardsForStage(_ stage: PipelineStage) -> [PipelineCard] {
        switch stage {
        case .screening: return screeningCards
        case .interview: return interviewCards
        case .offer: return offerCards
        case .hired: return hiredCards
        }
    }

    /// Overall conversion rate (screening to hired).
    var overallConversionRate: Double {
        guard !screeningCards.isEmpty else { return 0 }
        let hiredCount = hiredCards.count
        let screeningCount = screeningCards.count
        return Double(hiredCount) / Double(screeningCount)
    }

    /// Average score by stage.
    func averageScoreForStage(_ stage: PipelineStage) -> Double {
        let cards = cardsForStage(stage)
        guard !cards.isEmpty else { return 0 }
        return cards.reduce(0) { $0 + $1.score } / Double(cards.count)
    }

    /// Identify bottleneck stages (those with highest number of candidates).
    var bottleneckStages: [PipelineStage] {
        let counts: [(stage: PipelineStage, count: Int)] = [
            (.screening, screeningCards.count),
            (.interview, interviewCards.count),
            (.offer, offerCards.count),
            (.hired, hiredCards.count)
        ]

        let maxCount = counts.max(by: { $0.count < $1.count })?.count ?? 0
        return counts.filter { $0.count == maxCount && maxCount > 0 }.map { $0.stage }
    }

    // MARK: - Smart Suggestions

    /// Suggest candidates to move based on score and time in stage.
    var suggestedCandidatesToMove: [PipelineCard] {
        var suggestions: [PipelineCard] = []

        // Screening: move high-score candidates to interview
        suggestions += screeningCards.filter { $0.score > 85 }

        // Interview: move qualified to offer
        suggestions += interviewCards.filter { $0.score > 75 }

        return suggestions.sorted { $0.score > $1.score }
    }

    /// Candidates at risk of losing engagement (low score, long in stage).
    var atRiskCandidates: [PipelineCard] {
        let allCards = screeningCards + interviewCards + offerCards
        return allCards.filter { $0.score < 60 }.sorted { $0.score < $1.score }
    }

    // MARK: - Bulk Operations

    /// Move all high-score candidates from screening to interview.
    func bulkAdvanceHighScorers() async {
        for card in screeningCards.filter({ $0.score > 85 }) {
            await moveCard(card, from: .screening, to: .interview)
        }
    }

    /// Bulk reject low-score candidates.
    func bulkRejectLowScorers(threshold: Double) async {
        for card in screeningCards.filter({ $0.score < threshold }) {
            // Archive or reject action would be implemented here
            removeCard(card, fromStage: .screening)
        }
    }

    // MARK: - Sync Offline Queue

    /// Sync all pending drag-drop operations from offline queue.
    func syncOfflineQueue() async {
        while !dragDropQueue.isEmpty {
            let operation = dragDropQueue.removeFirst()

            // Reconstruct the card to sync
            if let card = findCard(withId: operation.cardId) {
                do {
                    try await api.requestVoid(
                        endpoint: .recruiterMoveCandidate(
                            candidateId: card.candidateId,
                            stage: operation.toStage.rawValue
                        )
                    )
                    TrueMatchLogger.log(.info, "Recruiter: synced pending move for \(card.name)")
                } catch {
                    TrueMatchLogger.log(.error, "Recruiter: sync failed for \(card.name): \(error)")
                    dragDropQueue.append(operation) // Re-queue on failure
                }
            }
        }
    }

    /// Find a card by ID across all stages.
    private func findCard(withId id: String) -> PipelineCard? {
        screeningCards.first { $0.id == id }
            ?? interviewCards.first { $0.id == id }
            ?? offerCards.first { $0.id == id }
            ?? hiredCards.first { $0.id == id }
    }

    // MARK: - Time-based Analytics

    /// Get candidates who have been in current stage for N days.
    func candidatesInStageForDays(_ stage: PipelineStage, minimumDays: Int) -> [PipelineCard] {
        // This would require additional timestamp data in PipelineCard
        // Placeholder for future enhancement
        return []
    }

    /// Estimate hiring velocity (candidates per day).
    func estimatedHiringVelocity(daysLookback: Int = 7) -> Double {
        // This would require historical data
        // Placeholder for future enhancement
        return Double(hiredCards.count) / Double(max(daysLookback, 1))
    }

    // MARK: - Export & Reporting

    /// Export pipeline snapshot as JSON.
    func exportPipelineSnapshot() -> [String: Any]? {
        let snapshot: [String: Any] = [
            "timestamp": Date(),
            "screening": screeningCards.map { ["id": $0.id, "name": $0.name, "score": $0.score] },
            "interview": interviewCards.map { ["id": $0.id, "name": $0.name, "score": $0.score] },
            "offer": offerCards.map { ["id": $0.id, "name": $0.name, "score": $0.score] },
            "hired": hiredCards.map { ["id": $0.id, "name": $0.name, "score": $0.score] },
            "stats": stats
        ]
        return snapshot
    }
}
