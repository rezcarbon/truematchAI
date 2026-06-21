//
//  PositionsViewModel.swift
//  TrueMatch
//
//  Loads the recruiter's open positions and, per position, the candidates in its
//  pipeline. Closes part of the web/iOS parity gap (recruiters could not see
//  positions or pipelines on mobile).
//

import Foundation
import SwiftUI

@MainActor
final class PositionsViewModel: ObservableObject {
    @Published var positions: [PositionDTO] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let api = APIClient.shared

    func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let resp = try await api.request(endpoint: .listPositions, type: PositionListResponse.self)
            positions = resp.items
        } catch {
            TrueMatchLogger.log(.error, "Positions load failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }
}

@MainActor
final class PipelineViewModel: ObservableObject {
    @Published var candidates: [PipelineCandidateDTO] = []
    @Published var detail: PositionDetailDTO?
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let api = APIClient.shared

    func load(positionId: String) async {
        isLoading = true
        defer { isLoading = false }
        do {
            candidates = try await api.request(
                endpoint: .positionPipeline(id: positionId),
                type: [PipelineCandidateDTO].self
            )
        } catch {
            TrueMatchLogger.log(.error, "Pipeline load failed: \(error)")
            errorMessage = error.localizedDescription
        }
        // JD quality detail (independent of the pipeline call).
        do {
            detail = try await api.request(
                endpoint: .position(id: positionId),
                type: PositionDetailDTO.self
            )
        } catch {
            TrueMatchLogger.log(.warning, "Position detail load failed: \(error)")
        }
    }

    /// Group candidates by stage for a sectioned pipeline view.
    var byStage: [(stage: String, items: [PipelineCandidateDTO])] {
        let order = ["applied", "phone_screen", "technical", "onsite", "offer", "hired", "rejected"]
        let grouped = Dictionary(grouping: candidates, by: { $0.stage })
        return order.compactMap { stage in
            guard let items = grouped[stage], !items.isEmpty else { return nil }
            return (stage, items)
        }
    }
}
