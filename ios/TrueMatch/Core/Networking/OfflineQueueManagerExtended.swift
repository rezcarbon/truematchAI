//
//  OfflineQueueManagerExtended.swift
//  TrueMatch
//
//  Extended offline queue with advanced SwiftData models for sync state tracking,
//  conflict resolution, batch operations, and network state management.
//

import Foundation
import SwiftData

// MARK: - Sync Status Model

@Model
final class SyncState {
    @Attribute(.unique) var id: String = "sync_state"
    var lastSyncTime: Date?
    var lastSuccessfulSyncTime: Date?
    var isSyncing: Bool = false
    var pendingCount: Int = 0
    var failedCount: Int = 0
    var syncConflictCount: Int = 0
    var lastSyncError: String?
    var networkQuality: NetworkQualityLevel = .unknown

    init() {}

    enum NetworkQualityLevel: String, Codable {
        case unknown
        case poor
        case fair
        case good
        case excellent
    }
}

// MARK: - Offline Queue Item (Enhanced)

@Model
final class OfflineQueueItem {
    @Attribute(.unique) var id: String
    var actionType: String
    var resourceId: String? // For grouping related actions
    var resourceType: String? // assessment, profile, decision, etc.
    var payload: String // JSON-encoded
    var createdAt: Date
    var enqueuedAt: Date
    var updatedAt: Date
    var priority: QueuePriority = .normal
    var retryCount: Int = 0
    var maxRetries: Int = 3
    var status: QueueItemStatus = .pending
    var lastError: String?
    var lastErrorTimestamp: Date?
    var estimatedSizeBytes: Int = 0
    var dependencies: [String] = [] // IDs of items that must complete first
    @Relationship(deleteRule: .cascade, inverse: \SyncConflict.queueItem) var conflicts: [SyncConflict] = []

    init(
        id: String = UUID().uuidString,
        actionType: String,
        resourceId: String? = nil,
        resourceType: String? = nil,
        payload: String,
        priority: QueuePriority = .normal,
        maxRetries: Int = 3
    ) {
        self.id = id
        self.actionType = actionType
        self.resourceId = resourceId
        self.resourceType = resourceType
        self.payload = payload
        self.priority = priority
        self.maxRetries = maxRetries
        self.createdAt = .now
        self.enqueuedAt = .now
        self.updatedAt = .now
    }

    enum QueueItemStatus: String, Codable {
        case pending
        case processing
        case completed
        case failed
        case conflict
        case paused
    }

    enum QueuePriority: String, Codable {
        case critical = "0"
        case high = "1"
        case normal = "2"
        case low = "3"

        var sortOrder: Int {
            switch self {
            case .critical: return 0
            case .high: return 1
            case .normal: return 2
            case .low: return 3
            }
        }
    }

    var isRetryable: Bool {
        status == .failed && retryCount < maxRetries
    }

    var canProcess: Bool {
        status == .pending && dependencies.isEmpty
    }

    func markFailed(error: String) {
        self.status = .failed
        self.lastError = error
        self.lastErrorTimestamp = .now
        self.updatedAt = .now
    }

    func incrementRetry() {
        self.retryCount += 1
        self.updatedAt = .now
        if retryCount < maxRetries {
            self.status = .pending
        } else {
            self.status = .failed
        }
    }
}

// MARK: - Sync Conflict Model

@Model
final class SyncConflict {
    @Attribute(.unique) var id: String
    var queueItem: OfflineQueueItem?
    var conflictType: ConflictType
    var localVersion: String // JSON snapshot
    var remoteVersion: String // JSON snapshot
    var resolvedVersion: String? // JSON snapshot after resolution
    var createdAt: Date
    var resolvedAt: Date?
    var resolutionStrategy: ResolutionStrategy = .manual

    init(
        id: String = UUID().uuidString,
        queueItem: OfflineQueueItem? = nil,
        conflictType: ConflictType,
        localVersion: String,
        remoteVersion: String
    ) {
        self.id = id
        self.queueItem = queueItem
        self.conflictType = conflictType
        self.localVersion = localVersion
        self.remoteVersion = remoteVersion
        self.createdAt = .now
    }

    enum ConflictType: String, Codable {
        case versionMismatch // Different timestamps
        case fieldDivergence // Same resource, different fields
        case deletionConflict // Local and remote deletions
        case constraintViolation // Violates business rules
        case dataIntegrity // Integrity check failed
    }

    enum ResolutionStrategy: String, Codable {
        case manual // Requires user decision
        case automatic // Resolved by algorithm
        case localWins // Use local version
        case remoteWins // Use remote version
        case merge // Merge both versions
    }

    var isResolved: Bool {
        resolvedAt != nil && resolvedVersion != nil
    }
}

// MARK: - Batch Operation Model

@Model
final class BatchOperation {
    @Attribute(.unique) var id: String
    var operationType: String // assess_multiple, bulk_review, etc.
    var status: BatchStatus = .pending
    var createdAt: Date
    var startedAt: Date?
    var completedAt: Date?
    var totalItems: Int
    var completedItems: Int = 0
    var failedItems: Int = 0
    var estimatedTimeRemainingSeconds: Int?
    var progress: Double = 0 // 0.0–1.0
    @Relationship(deleteRule: .cascade) var queueItems: [OfflineQueueItem] = []

    init(
        id: String = UUID().uuidString,
        operationType: String,
        totalItems: Int
    ) {
        self.id = id
        self.operationType = operationType
        self.totalItems = totalItems
        self.createdAt = .now
    }

    enum BatchStatus: String, Codable {
        case pending
        case inProgress
        case completed
        case partiallyCompleted
        case failed
        case cancelled
    }

    var isActive: Bool {
        status == .pending || status == .inProgress
    }

    var percentComplete: Double {
        totalItems == 0 ? 0 : Double(completedItems) / Double(totalItems)
    }
}

// MARK: - Network Quality Monitor

@MainActor
final class NetworkQualityMonitor: ObservableObject {
    @Published var currentQuality: SyncState.NetworkQualityLevel = .unknown
    @Published var isConnected: Bool = true
    @Published var connectionType: ConnectionType = .unknown

    enum ConnectionType: String, Codable {
        case unknown
        case wifi
        case cellular
        case wired
        case none
    }

    private var timer: Timer?

    init() {
        startMonitoring()
    }

    private func startMonitoring() {
        // Placeholder for network monitoring logic
        // In production, integrate with NWPathMonitor
    }

    func updateQuality(_ quality: SyncState.NetworkQualityLevel) {
        self.currentQuality = quality
    }
}

// MARK: - Extended Offline Queue Manager

@MainActor
final class OfflineQueueManagerExtended: ObservableObject {
    static let shared = OfflineQueueManagerExtended()

    @Published var syncState: SyncState?
    @Published var queueItems: [OfflineQueueItem] = []
    @Published var conflicts: [SyncConflict] = []
    @Published var batchOperations: [BatchOperation] = []
    @Published var networkQuality: SyncState.NetworkQualityLevel = .unknown

    private var modelContext: ModelContext?
    private var isProcessing = false
    private var syncTimer: Timer?

    private init() {}

    // MARK: - Setup

    func configure(with context: ModelContext) {
        self.modelContext = context
        loadSyncState(in: context)
    }

    // MARK: - Sync State Management

    private func loadSyncState(in context: ModelContext) {
        let descriptor = FetchDescriptor<SyncState>(
            predicate: #Predicate { $0.id == "sync_state" }
        )
        if let existing = try? context.fetch(descriptor).first {
            self.syncState = existing
        } else {
            let newState = SyncState()
            context.insert(newState)
            try? context.save()
            self.syncState = newState
        }
    }

    private func updateSyncState(_ update: (SyncState) -> Void, in context: ModelContext) {
        guard let syncState = syncState else { return }
        update(syncState)
        syncState.updatedAt = .now
        try? context.save()
    }

    // MARK: - Enqueue Operations

    func enqueue(
        actionType: String,
        resourceId: String? = nil,
        resourceType: String? = nil,
        payload: String,
        priority: OfflineQueueItem.QueuePriority = .normal,
        dependencies: [String] = [],
        in context: ModelContext
    ) {
        let item = OfflineQueueItem(
            actionType: actionType,
            resourceId: resourceId,
            resourceType: resourceType,
            payload: payload,
            priority: priority,
            maxRetries: 3
        )
        item.dependencies = dependencies
        item.estimatedSizeBytes = payload.utf8.count

        context.insert(item)
        try? context.save()

        fetchQueueItems(in: context)
        updateSyncState({ $0.pendingCount += 1 }, in: context)

        TrueMatchLogger.log(
            .info,
            "Enqueued offline action: \(actionType) [priority: \(priority.rawValue)]"
        )
    }

    func enqueueBatch(
        operationType: String,
        items: [(actionType: String, resourceId: String?, payload: String)],
        in context: ModelContext
    ) -> String {
        let batchId = UUID().uuidString
        let batch = BatchOperation(
            id: batchId,
            operationType: operationType,
            totalItems: items.count
        )
        context.insert(batch)

        for item in items {
            let queueItem = OfflineQueueItem(
                actionType: item.actionType,
                resourceId: item.resourceId,
                resourceType: operationType,
                payload: item.payload,
                priority: .normal
            )
            queueItem.estimatedSizeBytes = item.payload.utf8.count
            context.insert(queueItem)
            batch.queueItems.append(queueItem)
        }

        try? context.save()
        fetchQueueItems(in: context)

        TrueMatchLogger.log(.info, "Created batch operation: \(operationType) with \(items.count) items")
        return batchId
    }

    // MARK: - Process Queue

    func flush(in context: ModelContext) async {
        guard !isProcessing else { return }
        isProcessing = true
        defer { isProcessing = false }

        updateSyncState({ $0.isSyncing = true; $0.lastSyncTime = .now }, in: context)

        let descriptor = FetchDescriptor<OfflineQueueItem>(
            predicate: #Predicate { $0.status == .pending },
            sortBy: [
                SortDescriptor(\.priority.rawValue),
                SortDescriptor(\.createdAt)
            ]
        )

        guard let items = try? context.fetch(descriptor), !items.isEmpty else {
            updateSyncState({
                $0.isSyncing = false
                $0.lastSuccessfulSyncTime = .now
            }, in: context)
            return
        }

        var failedCount = 0
        for item in items {
            // Check dependencies
            if !item.dependencies.isEmpty {
                let allDependenciesSatisfied = checkDependencies(item.dependencies, in: context)
                if !allDependenciesSatisfied {
                    continue
                }
            }

            item.status = .processing
            try? context.save()

            do {
                try await processQueueItem(item)
                item.status = .completed
                try? context.save()
                TrueMatchLogger.log(.info, "Offline item completed: \(item.id)")
            } catch {
                item.incrementRetry()
                item.lastError = error.localizedDescription
                item.lastErrorTimestamp = .now
                failedCount += 1
                try? context.save()

                TrueMatchLogger.log(
                    .warning,
                    "Offline item failed (\(item.retryCount)/\(item.maxRetries)): \(item.id)"
                )
            }
        }

        updateSyncState({
            $0.isSyncing = false
            $0.lastSuccessfulSyncTime = .now
            $0.failedCount = failedCount
        }, in: context)

        fetchQueueItems(in: context)
    }

    // MARK: - Conflict Resolution

    func resolveConflict(
        _ conflict: SyncConflict,
        using strategy: SyncConflict.ResolutionStrategy,
        in context: ModelContext
    ) async {
        conflict.resolutionStrategy = strategy
        conflict.resolvedAt = .now

        switch strategy {
        case .localWins:
            conflict.resolvedVersion = conflict.localVersion
        case .remoteWins:
            conflict.resolvedVersion = conflict.remoteVersion
        case .merge:
            // Attempt automatic merge
            if let merged = attemptMerge(local: conflict.localVersion, remote: conflict.remoteVersion) {
                conflict.resolvedVersion = merged
            } else {
                conflict.resolutionStrategy = .manual
                return
            }
        case .automatic, .manual:
            break
        }

        try? context.save()
        fetchConflicts(in: context)

        if let queueItem = conflict.queueItem, conflict.resolutionStrategy != .manual {
            queueItem.status = .pending
            queueItem.conflicts.removeAll { $0.id == conflict.id }
            try? context.save()
            fetchQueueItems(in: context)
        }
    }

    // MARK: - Retry Failed Items

    func retryFailed(in context: ModelContext) async {
        let descriptor = FetchDescriptor<OfflineQueueItem>(
            predicate: #Predicate { $0.status == .failed }
        )

        guard let failedItems = try? context.fetch(descriptor), !failedItems.isEmpty else {
            return
        }

        for item in failedItems {
            item.status = .pending
            item.retryCount = 0
            item.lastError = nil
            item.lastErrorTimestamp = nil
        }
        try? context.save()
        fetchQueueItems(in: context)

        await flush(in: context)
    }

    // MARK: - Cleanup

    func removeCompleted(in context: ModelContext) {
        let descriptor = FetchDescriptor<OfflineQueueItem>(
            predicate: #Predicate { $0.status == .completed }
        )
        if let completed = try? context.fetch(descriptor) {
            for item in completed {
                context.delete(item)
            }
            try? context.save()
            fetchQueueItems(in: context)
        }
    }

    func removeExpired(olderThanDays: Int = 30, in context: ModelContext) {
        let cutoffDate = Date(timeIntervalSinceNow: -Double(olderThanDays * 86400))
        let descriptor = FetchDescriptor<OfflineQueueItem>(
            predicate: #Predicate { $0.createdAt < cutoffDate && $0.status == .failed }
        )
        if let expired = try? context.fetch(descriptor) {
            for item in expired {
                context.delete(item)
            }
            try? context.save()
            fetchQueueItems(in: context)
        }
    }

    // MARK: - Query Methods

    func fetchQueueItems(in context: ModelContext) {
        let descriptor = FetchDescriptor<OfflineQueueItem>(
            sortBy: [SortDescriptor(\.createdAt, order: .reverse)]
        )
        self.queueItems = (try? context.fetch(descriptor)) ?? []
    }

    func fetchConflicts(in context: ModelContext) {
        let descriptor = FetchDescriptor<SyncConflict>(
            sortBy: [SortDescriptor(\.createdAt, order: .reverse)]
        )
        self.conflicts = (try? context.fetch(descriptor)) ?? []
    }

    func fetchBatchOperations(in context: ModelContext) {
        let descriptor = FetchDescriptor<BatchOperation>(
            sortBy: [SortDescriptor(\.createdAt, order: .reverse)]
        )
        self.batchOperations = (try? context.fetch(descriptor)) ?? []
    }

    func pendingCount(in context: ModelContext) -> Int {
        let descriptor = FetchDescriptor<OfflineQueueItem>(
            predicate: #Predicate { $0.status == .pending }
        )
        return (try? context.fetchCount(descriptor)) ?? 0
    }

    func failedCount(in context: ModelContext) -> Int {
        let descriptor = FetchDescriptor<OfflineQueueItem>(
            predicate: #Predicate { $0.status == .failed }
        )
        return (try? context.fetchCount(descriptor)) ?? 0
    }

    // MARK: - Private Helpers

    private func checkDependencies(_ dependencies: [String], in context: ModelContext) -> Bool {
        let descriptor = FetchDescriptor<OfflineQueueItem>(
            predicate: #Predicate { dependencies.contains($0.id) && $0.status != .completed }
        )
        return (try? context.fetchCount(descriptor)) ?? 0 == 0
    }

    private func processQueueItem(_ item: OfflineQueueItem) async throws {
        switch item.actionType {
        case "create_assessment":
            try await processCreateAssessment(item)
        case "update_profile":
            try await processUpdateProfile(item)
        case "submit_decision":
            try await processSubmitDecision(item)
        default:
            try await processBatchSync(item)
        }
    }

    private func processCreateAssessment(_ item: OfflineQueueItem) async throws {
        guard let data = item.payload.data(using: .utf8),
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

    private func processUpdateProfile(_ item: OfflineQueueItem) async throws {
        _ = try await APIClient.shared.request(
            endpoint: .syncOfflineActions(request: SyncRequest(actions: [])),
            type: SyncResponse.self
        )
    }

    private func processSubmitDecision(_ item: OfflineQueueItem) async throws {
        _ = try await APIClient.shared.request(
            endpoint: .syncOfflineActions(request: SyncRequest(actions: [])),
            type: SyncResponse.self
        )
    }

    private func processBatchSync(_ item: OfflineQueueItem) async throws {
        let actionPayload = OfflineActionPayload(
            localId: item.id,
            actionType: item.actionType,
            payload: item.payload,
            createdAt: item.createdAt
        )

        let syncRequest = SyncRequest(actions: [actionPayload])
        _ = try await APIClient.shared.request(
            endpoint: .syncOfflineActions(request: syncRequest),
            type: SyncResponse.self
        )
    }

    private func attemptMerge(local: String, remote: String) -> String? {
        // Placeholder for merge logic
        // In production, implement JSON merging with conflict detection
        return local
    }
}

// MARK: - Errors

enum OfflineQueueExtendedError: LocalizedError {
    case invalidPayload
    case syncInProgress
    case conflictUnresolved
    case dependencyNotSatisfied

    var errorDescription: String? {
        switch self {
        case .invalidPayload:
            return "Invalid offline queue item payload"
        case .syncInProgress:
            return "Sync is already in progress"
        case .conflictUnresolved:
            return "Cannot process item with unresolved conflicts"
        case .dependencyNotSatisfied:
            return "Item dependencies have not been satisfied"
        }
    }
}
