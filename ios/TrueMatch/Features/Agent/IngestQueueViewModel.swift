//
//  IngestQueueViewModel.swift
//  TrueMatch
//

import Foundation

@MainActor
final class IngestQueueViewModel: ObservableObject {
    @Published var items: [IngestQueueItem] = []
    @Published var isLoading = false
    @Published var hasError = false
    @Published var errorMessage: String?

    func load(status: String? = nil) {
        isLoading = true
        Task {
            defer { isLoading = false }
            do {
                items = try await APIClient.shared.request(
                    endpoint: .agentQueue(status: status),
                    type: [IngestQueueItem].self
                )
            } catch {
                errorMessage = error.localizedDescription
                hasError = true
            }
        }
    }

    func approve(id: String, notes: String?) {
        act { try await APIClient.shared.request(endpoint: .approveQueueItem(id: id, notes: notes?.nilIfEmpty), type: [String: String].self) }
    }

    func reject(id: String, notes: String?) {
        act { try await APIClient.shared.request(endpoint: .rejectQueueItem(id: id, notes: notes?.nilIfEmpty), type: [String: String].self) }
    }

    func reassign(id: String, positionId: String, notes: String?) {
        act { try await APIClient.shared.request(endpoint: .reassignQueueItem(id: id, positionId: positionId, notes: notes?.nilIfEmpty), type: [String: String].self) }
    }

    private func act(action: @escaping () async throws -> some Any) {
        Task {
            do {
                _ = try await action()
                load()
            } catch {
                errorMessage = error.localizedDescription
                hasError = true
            }
        }
    }
}

private extension String {
    var nilIfEmpty: String? { isEmpty ? nil : self }
}
