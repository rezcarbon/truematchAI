//
//  AssessmentViewModel.swift
//  TrueMatch
//

import Foundation
import SwiftUI
import Combine
import SwiftData

@MainActor
final class AssessmentViewModel: ObservableObject {
    @Published var assessment: AssessmentResponse?
    @Published var isLoading = false
    @Published var errorMessage: String?

    // Live progress while the backend computes the assessment.
    @Published var progressPercent: Double = 0
    @Published var currentStage: AssessmentStage?

    private let socket = WebSocketClient()
    private var cancellables = Set<AnyCancellable>()

    let assessmentId: String

    init(assessmentId: String) {
        self.assessmentId = assessmentId
        observeSocket()
    }

    // MARK: - Load

    func load(usePreview: Bool = false) async {
        if usePreview {
            assessment = PreviewData.sampleAssessment
            return
        }

        isLoading = true
        errorMessage = nil
        do {
            let result = try await APIClient.shared.request(
                endpoint: .assessment(id: assessmentId),
                type: AssessmentResponse.self
            )
            assessment = result
            if result.status == .processing || result.status == .queued {
                socket.connect(assessmentId: assessmentId)
            }
        } catch {
            errorMessage = error.localizedDescription
            TrueMatchLogger.log(.error, "Failed to load assessment: \(error.localizedDescription)")
        }
        isLoading = false
    }

    func cache(in context: ModelContext) {
        guard let assessment else { return }
        LocalStore.shared.saveAssessment(assessment, in: context)
    }

    // MARK: - Streaming

    private func observeSocket() {
        socket.events
            .receive(on: DispatchQueue.main)
            .sink { [weak self] event in
                guard let self else { return }
                switch event {
                case .progress(let progress):
                    self.progressPercent = progress.percent
                    if let stage = progress.stage { self.currentStage = stage }
                case .stageUpdate(let stage):
                    self.currentStage = stage
                case .completed(let result):
                    self.assessment = result
                    self.socket.disconnect()
                case .error(let message):
                    self.errorMessage = message
                default:
                    break
                }
            }
            .store(in: &cancellables)
    }

    func disconnect() {
        socket.disconnect()
    }

    // MARK: - Derived display values

    var isProcessing: Bool {
        guard let assessment else { return false }
        return assessment.status == .processing || assessment.status == .queued
    }
}
