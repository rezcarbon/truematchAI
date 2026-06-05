//
//  OfflineQueue.swift
//  TrueMatch
//

import Foundation
import SwiftData

// MARK: - Offline Action Model

@Model
final class OfflineAction {
    @Attribute(.unique) var id: String
    var actionType: String
    var payload: String
    var createdAt: Date
    var retryCount: Int
    var maxRetries: Int
    var status: String // pending, processing, completed, failed
    var lastError: String?

    init(
        id: String = UUID().uuidString,
        actionType: String,
        payload: String,
        createdAt: Date = .now,
        retryCount: Int = 0,
        maxRetries: Int = 3,
        status: String = "pending",
        lastError: String? = nil
    ) {
        self.id = id
        self.actionType = actionType
        self.payload = payload
        self.createdAt = createdAt
        self.retryCount = retryCount
        self.maxRetries = maxRetries
        self.status = status
        self.lastError = lastError
    }
}

// MARK: - Offline Queue Manager

@MainActor
final class OfflineQueueManager: ObservableObject {
    static let shared = OfflineQueueManager()

    @Published var pendingCount: Int = 0
    private var isProcessing = false

    private init() {}

    // MARK: - Enqueue

    func enqueue(actionType: String, payload: String, in context: ModelContext) {
        let action = OfflineAction(actionType: actionType, payload: payload)
        context.insert(action)
        try? context.save()
        updateCount(in: context)
        TrueMatchLogger.log(.info, "Enqueued offline action: \(actionType)")
    }

    /// Queues a "create assessment" request to be retried when connectivity returns.
    func enqueueAssessment(fileId: String, supplementary: String?, jobDescription: String?, in context: ModelContext) {
        let payloadDict: [String: String] = [
            "fileId": fileId,
            "supplementary": supplementary ?? "",
            "jobDescription": jobDescription ?? ""
        ]
        guard let data = try? JSONEncoder().encode(payloadDict),
              let payloadString = String(data: data, encoding: .utf8) else {
            return
        }
        enqueue(actionType: "create_assessment", payload: payloadString, in: context)
    }

    // MARK: - Flush (Process Pending)

    func flush(in context: ModelContext) async {
        guard !isProcessing else { return }
        isProcessing = true
        defer { isProcessing = false }

        let descriptor = FetchDescriptor<OfflineAction>(
            predicate: #Predicate { $0.status == "pending" },
            sortBy: [SortDescriptor(\.createdAt)]
        )

        guard let actions = try? context.fetch(descriptor), !actions.isEmpty else {
            return
        }

        TrueMatchLogger.log(.info, "Flushing \(actions.count) offline actions")

        for action in actions {
            action.status = "processing"
            try? context.save()

            do {
                try await processAction(action)
                action.status = "completed"
                TrueMatchLogger.log(.info, "Offline action completed: \(action.id)")
            } catch {
                action.retryCount += 1
                action.lastError = error.localizedDescription

                if action.retryCount >= action.maxRetries {
                    action.status = "failed"
                    TrueMatchLogger.log(.error, "Offline action permanently failed: \(action.id)")
                } else {
                    action.status = "pending"
                    TrueMatchLogger.log(.warning, "Offline action will retry (\(action.retryCount)/\(action.maxRetries)): \(action.id)")
                }
            }

            try? context.save()
        }

        updateCount(in: context)
    }

    // MARK: - Retry Failed

    func retryFailed(in context: ModelContext) async {
        let descriptor = FetchDescriptor<OfflineAction>(
            predicate: #Predicate { $0.status == "failed" },
            sortBy: [SortDescriptor(\.createdAt)]
        )

        guard let failedActions = try? context.fetch(descriptor), !failedActions.isEmpty else {
            return
        }

        for action in failedActions {
            action.status = "pending"
            action.retryCount = 0
        }
        try? context.save()

        await flush(in: context)
    }

    // MARK: - Query

    func pendingActionCount(in context: ModelContext) -> Int {
        let descriptor = FetchDescriptor<OfflineAction>(
            predicate: #Predicate { $0.status == "pending" }
        )
        return (try? context.fetchCount(descriptor)) ?? 0
    }

    func failedActionCount(in context: ModelContext) -> Int {
        let descriptor = FetchDescriptor<OfflineAction>(
            predicate: #Predicate { $0.status == "failed" }
        )
        return (try? context.fetchCount(descriptor)) ?? 0
    }

    // MARK: - Cleanup

    func removeCompleted(in context: ModelContext) {
        let descriptor = FetchDescriptor<OfflineAction>(
            predicate: #Predicate { $0.status == "completed" }
        )
        if let completed = try? context.fetch(descriptor) {
            for action in completed {
                context.delete(action)
            }
            try? context.save()
        }
    }

    // MARK: - Process Single Action

    private func processAction(_ action: OfflineAction) async throws {
        switch action.actionType {
        case "create_assessment":
            try await processCreateAssessment(action)
        default:
            try await processBatchSync(action)
        }
    }

    private func processCreateAssessment(_ action: OfflineAction) async throws {
        guard let data = action.payload.data(using: .utf8),
              let payload = try? JSONDecoder().decode([String: String].self, from: data),
              let fileId = payload["fileId"] else {
            throw OfflineQueueError.invalidPayload
        }

        let request = CreateAssessmentRequest(
            fileId: fileId,
            supplementary: payload["supplementary"]?.isEmpty == false ? payload["supplementary"] : nil,
            jobDescription: payload["jobDescription"]?.isEmpty == false ? payload["jobDescription"] : nil
        )
        _ = try await APIClient.shared.request(
            endpoint: .createAssessment(request),
            type: AssessmentResponse.self
        )
    }

    private func processBatchSync(_ action: OfflineAction) async throws {
        let actionPayload = OfflineActionPayload(
            localId: action.id,
            actionType: action.actionType,
            payload: action.payload,
            createdAt: action.createdAt
        )

        let syncRequest = SyncRequest(actions: [actionPayload])
        _ = try await APIClient.shared.request(
            endpoint: .syncOfflineActions(request: syncRequest),
            type: SyncResponse.self
        )
    }

    // MARK: - Update Count

    private func updateCount(in context: ModelContext) {
        pendingCount = pendingActionCount(in: context)
    }
}

// MARK: - Errors

enum OfflineQueueError: LocalizedError {
    case invalidPayload

    var errorDescription: String? {
        switch self {
        case .invalidPayload: return "Invalid offline action payload"
        }
    }
}
