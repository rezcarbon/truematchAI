//
//  RecruiterDecisionViewModel.swift
//  TrueMatch
//
//  Manages one-tap approve/reject decisions with quick templates, feedback
//  input, and offer recording.
//

import Foundation
import SwiftUI

@MainActor
final class RecruiterDecisionViewModel: ObservableObject {
    @Published var selectedCandidate: CandidateQueueItem?
    @Published var selectedDecision: DecisionRecord.Decision?
    @Published var feedbackText: String = ""
    @Published var selectedTemplate: String?

    @Published var isSubmitting = false
    @Published var isSuccessful = false
    @Published var errorMessage: String?

    private let api = APIClient.shared

    // Decision templates
    let approvalTemplates = [
        "Strong candidate, moving to next stage.",
        "Exceeds requirements, recommend interview.",
        "Good fit for the role.",
        "Meets all qualifications.",
        "Highest priority candidate."
    ]

    let rejectionTemplates = [
        "Skills mismatch with role requirements.",
        "Candidate withdrew application.",
        "Better matches available.",
        "Experience level doesn't align.",
        "Cultural fit concerns."
    ]

    let revisitTemplates = [
        "Need more information before deciding.",
        "Hold for future positions.",
        "Promising but timeline doesn't align.",
        "Waitlist for similar roles."
    ]

    // MARK: - Candidate Selection

    func selectCandidate(_ candidate: CandidateQueueItem) {
        selectedCandidate = candidate
        feedbackText = ""
        selectedTemplate = nil
        selectedDecision = nil
        isSuccessful = false
    }

    func clearSelection() {
        selectedCandidate = nil
        feedbackText = ""
        selectedTemplate = nil
        selectedDecision = nil
        isSuccessful = false
    }

    // MARK: - Template Selection

    func selectTemplate(_ template: String) {
        selectedTemplate = template
        feedbackText = template
    }

    // MARK: - Decision Recording

    func recordDecision(_ decision: DecisionRecord.Decision) async {
        guard let candidate = selectedCandidate else { return }

        isSubmitting = true
        defer { isSubmitting = false }

        let request = RecordDecisionRequest(
            decision: decision.rawValue,
            feedback: feedbackText.trimmingCharacters(in: .whitespacesAndNewlines),
            timestamp: .now
        )

        do {
            try await api.requestVoid(
                endpoint: .recruiterRecordDecision(candidateId: candidate.candidateId, request)
            )

            await MainActor.run {
                self.isSuccessful = true
                TrueMatchLogger.log(.info, "Recruiter: decision recorded for \(candidate.name)")

                // Clear after 1 second for UX
                DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                    self.clearSelection()
                }
            }
        } catch {
            TrueMatchLogger.log(.error, "Recruiter: record decision failed: \(error)")
            await MainActor.run {
                self.errorMessage = error.localizedDescription
            }
        }
    }

    // MARK: - Quick Decision (no feedback)

    func quickApprove() async {
        await recordDecision(.approve)
    }

    func quickReject() async {
        await recordDecision(.reject)
    }

    func quickRevisit() async {
        await recordDecision(.revisit)
    }

    // MARK: - Offer Actions

    func prepareOffer() async {
        guard let candidate = selectedCandidate else { return }
        TrueMatchLogger.log(.info, "Recruiter: preparing offer for \(candidate.name)")
        // Trigger navigation to offer screen or present modal
    }

    // MARK: - Helpers

    var availableTemplates: [String] {
        guard let decision = selectedDecision else { return [] }
        switch decision {
        case .approve: return approvalTemplates
        case .reject: return rejectionTemplates
        case .revisit: return revisitTemplates
        }
    }

    var canSubmit: Bool {
        selectedCandidate != nil && selectedDecision != nil
    }
}
