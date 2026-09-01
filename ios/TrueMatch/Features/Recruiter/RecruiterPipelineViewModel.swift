//
//  RecruiterPipelineViewModel.swift
//  TrueMatch
//
//  Manages the Kanban board pipeline state: drag-drop between columns, WebSocket
//  updates for real-time sync, and offline action queueing.
//

import Foundation
import SwiftUI
import Combine

@MainActor
final class RecruiterPipelineViewModel: ObservableObject {
    @Published var screeningCards: [PipelineCard] = []
    @Published var interviewCards: [PipelineCard] = []
    @Published var offerCards: [PipelineCard] = []
    @Published var hiredCards: [PipelineCard] = []

    @Published var isLoading = false
    @Published var isSyncingDragDrop = false
    @Published var selectedCard: PipelineCard?
    @Published var errorMessage: String?

    private let api = APIClient.shared
    private var cancellables = Set<AnyCancellable>()
    private var dragDropQueue: [(cardId: String, fromStage: PipelineStage, toStage: PipelineStage)] = []

    // MARK: - Initialization

    func loadPipeline() async {
        guard !isLoading else { return }
        isLoading = true
        defer { isLoading = false }

        do {
            let response = try await api.request(
                endpoint: .recruiterPipeline,
                type: PipelineResponse.self
            )
            await MainActor.run {
                self.organizePipeline(response.cards)
            }
        } catch {
            TrueMatchLogger.log(.error, "Recruiter: load pipeline failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }

    /// Organize cards into stage columns.
    private func organizePipeline(_ cards: [PipelineCard]) {
        screeningCards = cards.filter { $0.stage == .screening }
        interviewCards = cards.filter { $0.stage == .interview }
        offerCards = cards.filter { $0.stage == .offer }
        hiredCards = cards.filter { $0.stage == .hired }
    }

    // MARK: - Drag & Drop

    /// Move a card from one stage to another.
    func moveCard(_ card: PipelineCard, from sourceStage: PipelineStage, to targetStage: PipelineStage) async {
        // Optimistic update (move immediately)
        removeCard(card, fromStage: sourceStage)
        var updatedCard = card
        updatedCard = PipelineCard(
            id: card.id,
            candidateId: card.candidateId,
            name: card.name,
            score: card.score,
            delta: card.delta,
            stage: targetStage,
            avatarUrl: card.avatarUrl,
            positionId: card.positionId,
            notesCount: card.notesCount
        )
        addCard(updatedCard, toStage: targetStage)

        // Queue for offline sync
        dragDropQueue.append((card.id, sourceStage, targetStage))

        // Sync to backend
        isSyncingDragDrop = true
        defer { isSyncingDragDrop = false }

        do {
            try await api.requestVoid(
                endpoint: .recruiterMoveCandidate(
                    candidateId: card.candidateId,
                    stage: targetStage.rawValue
                )
            )
            TrueMatchLogger.log(.info, "Recruiter: card moved to \(targetStage.rawValue)")
            dragDropQueue.removeAll { $0.cardId == card.id }
        } catch {
            TrueMatchLogger.log(.error, "Recruiter: move card failed: \(error)")
            // Revert on error
            removeCard(updatedCard, fromStage: targetStage)
            addCard(card, toStage: sourceStage)
            errorMessage = "Could not move card. Reverted."
        }
    }

    private func removeCard(_ card: PipelineCard, fromStage stage: PipelineStage) {
        switch stage {
        case .screening:
            screeningCards.removeAll { $0.id == card.id }
        case .interview:
            interviewCards.removeAll { $0.id == card.id }
        case .offer:
            offerCards.removeAll { $0.id == card.id }
        case .hired:
            hiredCards.removeAll { $0.id == card.id }
        }
    }

    private func addCard(_ card: PipelineCard, toStage stage: PipelineStage) {
        switch stage {
        case .screening:
            screeningCards.append(card)
        case .interview:
            interviewCards.append(card)
        case .offer:
            offerCards.append(card)
        case .hired:
            hiredCards.append(card)
        }
    }

    // MARK: - Real-time Updates

    /// Subscribe to WebSocket updates for pipeline changes.
    func subscribeToUpdates() {
        // This would connect to a WebSocket endpoint for real-time updates
        // For now, we'll use polling or leave for future implementation
    }

    // MARK: - Card Details

    func selectCard(_ card: PipelineCard) {
        selectedCard = card
    }

    func deselectCard() {
        selectedCard = nil
    }

    // MARK: - Stats

    var stats: PipelineStats {
        PipelineStats(
            screeningCount: screeningCards.count,
            interviewCount: interviewCards.count,
            offerCount: offerCards.count,
            hiredCount: hiredCards.count,
            pendingMoves: dragDropQueue.count
        )
    }
}

// MARK: - Pipeline Statistics

struct PipelineStats: Equatable {
    let screeningCount: Int
    let interviewCount: Int
    let offerCount: Int
    let hiredCount: Int
    let pendingMoves: Int

    var total: Int {
        screeningCount + interviewCount + offerCount + hiredCount
    }
}
