//
//  JDDraftReviewViewModel.swift
//  TrueMatch
//

import Foundation

@MainActor
final class JDDraftReviewViewModel: ObservableObject {
    @Published var suggestions: JDSuggestionsResponse?
    @Published var isLoading = false
    @Published var errorMessage: String?

    func load(positionId: String) {
        isLoading = true
        Task {
            defer { isLoading = false }
            do {
                suggestions = try await APIClient.shared.request(
                    endpoint: .jdSuggestions(positionId: positionId),
                    type: JDSuggestionsResponse.self
                )
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }

    /// The recruiter accepted the AI-improved (or hand-edited) draft.
    /// The position update is handled by the recruiter in the Positions flow;
    /// here we just log acceptance for the audit trail.
    func acceptDraft(_ draft: String) {
        TrueMatchLogger.log(.info, "JD draft accepted (\(draft.prefix(40))…)")
    }
}
