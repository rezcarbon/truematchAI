//
//  OfflineQueueSetup.swift
//  TrueMatch
//
//  Integration guide for setting up the offline queue manager with the app lifecycle.
//  Shows how to configure, monitor, and use the offline queue in your app.
//

import SwiftUI
import SwiftData
import Combine

// MARK: - Offline Queue Configuration

struct OfflineQueueConfiguration {
    /// Maximum number of retry attempts per item
    var maxRetries: Int = 3

    /// Time interval for automatic sync attempts
    var autoSyncInterval: TimeInterval = 30

    /// Maximum time to keep failed items before removal
    var failedItemRetentionDays: Int = 30

    /// Enable automatic sync on app return to foreground
    var enableAutoSyncOnForeground: Bool = true

    /// Size limit for individual queue item payloads (in bytes)
    var maxPayloadSizeBytes: Int = 5_000_000
}

// MARK: - Offline Queue Lifecycle Manager

@MainActor
final class OfflineQueueLifecycleManager: NSObject, ObservableObject {
    static let shared = OfflineQueueLifecycleManager()

    @Published var isInitialized = false
    @Published var autoSyncTimer: Timer?
    @Published var networkMonitor = NetworkQualityMonitor()

    private var modelContext: ModelContext?
    private var cancellables = Set<AnyCancellable>()
    private let configuration: OfflineQueueConfiguration

    private override init() {
        self.configuration = OfflineQueueConfiguration()
        super.init()
    }

    // MARK: - Initialization

    func initialize(with modelContext: ModelContext) {
        self.modelContext = modelContext

        let queueManager = OfflineQueueManagerExtended.shared
        queueManager.configure(with: modelContext)

        // Fetch initial state
        queueManager.fetchQueueItems(in: modelContext)
        queueManager.fetchConflicts(in: modelContext)
        queueManager.fetchBatchOperations(in: modelContext)

        // Setup lifecycle observers
        setupLifecycleObservers()

        // Start auto-sync
        startAutoSync()

        TrueMatchLogger.log(.info, "Offline queue lifecycle manager initialized")
        self.isInitialized = true
    }

    // MARK: - Lifecycle Observers

    private func setupLifecycleObservers() {
        let notificationCenter = NotificationCenter.default

        // App will resign active (backgrounding)
        notificationCenter.publisher(for: UIApplication.willResignActiveNotification)
            .receive(on: DispatchQueue.main)
            .sink { [weak self] _ in
                self?.handleAppWillResignActive()
            }
            .store(in: &cancellables)

        // App did become active (returning from background)
        notificationCenter.publisher(for: UIApplication.didBecomeActiveNotification)
            .receive(on: DispatchQueue.main)
            .sink { [weak self] _ in
                self?.handleAppDidBecomeActive()
            }
            .store(in: &cancellables)

        // App will terminate
        notificationCenter.publisher(for: UIApplication.willTerminateNotification)
            .receive(on: DispatchQueue.main)
            .sink { [weak self] _ in
                self?.handleAppWillTerminate()
            }
            .store(in: &cancellables)
    }

    private func handleAppWillResignActive() {
        // Pause auto-sync to save battery
        pauseAutoSync()
        TrueMatchLogger.log(.info, "Offline queue paused (app backgrounding)")
    }

    private func handleAppDidBecomeActive() {
        guard let modelContext = modelContext else { return }

        if configuration.enableAutoSyncOnForeground {
            Task {
                TrueMatchLogger.log(.info, "Syncing offline queue (app returning to foreground)")
                await OfflineQueueManagerExtended.shared.flush(in: modelContext)
            }
        }

        // Resume auto-sync
        resumeAutoSync()
    }

    private func handleAppWillTerminate() {
        pauseAutoSync()
        TrueMatchLogger.log(.info, "Offline queue manager terminated")
    }

    // MARK: - Auto Sync

    private func startAutoSync() {
        pauseAutoSync() // Ensure we start fresh

        autoSyncTimer = Timer.scheduledTimer(
            withTimeInterval: configuration.autoSyncInterval,
            repeats: true
        ) { [weak self] _ in
            self?.performAutoSync()
        }

        TrueMatchLogger.log(
            .info,
            "Auto-sync started with interval: \(configuration.autoSyncInterval)s"
        )
    }

    private func resumeAutoSync() {
        guard autoSyncTimer == nil else { return }
        startAutoSync()
    }

    private func pauseAutoSync() {
        autoSyncTimer?.invalidate()
        autoSyncTimer = nil
    }

    private func performAutoSync() {
        guard let modelContext = modelContext else { return }

        let queueManager = OfflineQueueManagerExtended.shared
        let pendingCount = queueManager.pendingCount(in: modelContext)

        if pendingCount > 0 {
            TrueMatchLogger.log(.debug, "Auto-sync triggered: \(pendingCount) pending items")
            Task {
                await queueManager.flush(in: modelContext)
            }
        }
    }

    // MARK: - Maintenance

    func performMaintenance(in modelContext: ModelContext) {
        let queueManager = OfflineQueueManagerExtended.shared

        // Remove old completed items
        queueManager.removeCompleted(in: modelContext)

        // Remove expired failed items
        queueManager.removeExpired(
            olderThanDays: configuration.failedItemRetentionDays,
            in: modelContext
        )

        TrueMatchLogger.log(.info, "Offline queue maintenance completed")
    }

    func deinit {
        pauseAutoSync()
        cancellables.removeAll()
    }
}

// MARK: - App State Integration

extension AppState {
    /// Setup offline queue when app initializes
    func setupOfflineQueue(with modelContext: ModelContext) {
        let lifecycleManager = OfflineQueueLifecycleManager.shared
        lifecycleManager.initialize(with: modelContext)

        // Perform maintenance daily
        scheduleOfflineQueueMaintenance(with: modelContext)
    }

    private func scheduleOfflineQueueMaintenance(with modelContext: ModelContext) {
        // Run maintenance once per day
        Timer.scheduledTimer(withTimeInterval: 86400, repeats: true) { _ in
            OfflineQueueLifecycleManager.shared.performMaintenance(in: modelContext)
        }
    }
}

// MARK: - View Integration

struct OfflineQueueAwareView<Content: View>: View {
    @StateObject private var queueManager = OfflineQueueManagerExtended.shared
    @StateObject private var lifecycleManager = OfflineQueueLifecycleManager.shared
    @Environment(\.modelContext) private var modelContext

    let content: (OfflineQueueManagerExtended) -> Content

    var body: some View {
        content(queueManager)
            .onAppear {
                if !lifecycleManager.isInitialized {
                    lifecycleManager.initialize(with: modelContext)
                }
            }
    }
}

// MARK: - Example App Initialization

/*
 Example of how to set up offline queue in your App:

 @main
 struct TrueMatchApp: App {
     @StateObject private var appState = AppState()
     let modelContainer: ModelContainer

     var body: some Scene {
         WindowGroup {
             RootSceneView()
                 .environmentObject(appState)
                 .modelContext(modelContainer.mainContext)
                 .onAppear {
                     appState.setupOfflineQueue(with: modelContainer.mainContext)
                 }
         }
         .modelContainer(modelContainer)
     }
 }
 */

// MARK: - Monitoring & Debugging

struct OfflineQueueDebugInfo: View {
    @StateObject private var queueManager = OfflineQueueManagerExtended.shared
    @Environment(\.trueMatchTheme) private var theme
    @Environment(\.modelContext) private var modelContext

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.md) {
            Text("Offline Queue Debug Info")
                .font(theme.typography.headline)

            // Sync State
            if let syncState = queueManager.syncState {
                Section("Sync State") {
                    DebugRow(label: "Syncing", value: syncState.isSyncing ? "Yes" : "No")
                    DebugRow(
                        label: "Last Sync",
                        value: formatDate(syncState.lastSyncTime)
                    )
                    DebugRow(
                        label: "Last Successful",
                        value: formatDate(syncState.lastSuccessfulSyncTime)
                    )
                    DebugRow(label: "Network Quality", value: syncState.networkQuality.rawValue)
                    DebugRow(label: "Pending Count", value: "\(syncState.pendingCount)")
                    DebugRow(label: "Failed Count", value: "\(syncState.failedCount)")
                    DebugRow(label: "Conflicts", value: "\(syncState.syncConflictCount)")
                }
            }

            // Queue Items
            Section("Queue Items") {
                let pending = queueManager.queueItems.filter { $0.status == .pending }
                let failed = queueManager.queueItems.filter { $0.status == .failed }

                DebugRow(label: "Total Items", value: "\(queueManager.queueItems.count)")
                DebugRow(label: "Pending", value: "\(pending.count)")
                DebugRow(label: "Failed", value: "\(failed.count)")
            }

            // Actions
            VStack(spacing: theme.spacing.xs) {
                Button("Sync Now") {
                    Task {
                        await queueManager.flush(in: modelContext)
                    }
                }
                .buttonStyle(.bordered)

                Button("Retry Failed") {
                    Task {
                        await queueManager.retryFailed(in: modelContext)
                    }
                }
                .buttonStyle(.bordered)

                Button("Cleanup") {
                    queueManager.removeCompleted(in: modelContext)
                    OfflineQueueLifecycleManager.shared.performMaintenance(in: modelContext)
                }
                .buttonStyle(.bordered)
            }
        }
        .padding(theme.spacing.md)
        .background(Color.gray.opacity(0.05))
        .clipShape(RoundedRectangle(cornerRadius: theme.radii.sm))
    }

    private func formatDate(_ date: Date?) -> String {
        guard let date = date else { return "Never" }
        let formatter = DateFormatter()
        formatter.dateStyle = .short
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

struct DebugRow: View {
    let label: String
    let value: String
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        HStack {
            Text(label)
                .font(theme.typography.caption)
                .foregroundStyle(Color.tmTextSecondary)
            Spacer()
            Text(value)
                .font(theme.typography.caption)
                .monospacedDigit()
                .foregroundStyle(Color.tmTextPrimary)
        }
    }
}

// MARK: - Usage Examples

/*
 Example 1: Enqueue an Assessment
 ================================

 func submitAssessment(fileId: String, in modelContext: ModelContext) {
     let payload = try JSONEncoder().encode([
         "fileId": fileId,
         "supplementary": "Additional context"
     ])
     let payloadString = String(data: payload, encoding: .utf8) ?? ""

     let manager = OfflineQueueManagerExtended.shared
     manager.enqueue(
         actionType: "create_assessment",
         resourceId: fileId,
         resourceType: "assessment",
         payload: payloadString,
         priority: .high,
         in: modelContext
     )
 }

 Example 2: Monitor Queue Status
 ================================

 @StateObject private var queueManager = OfflineQueueManagerExtended.shared
 @Environment(\.modelContext) private var modelContext

 var body: some View {
     Text("Pending: \(queueManager.pendingCount(in: modelContext))")
         .onAppear {
             queueManager.fetchQueueItems(in: modelContext)
         }
 }

 Example 3: Batch Operations
 ================================

 func assessMultipleCandidates(_ fileIds: [String], in modelContext: ModelContext) {
     let items: [(actionType: String, resourceId: String?, payload: String)] = fileIds.map { fileId in
         let payload = try? JSONEncoder().encode(["fileId": fileId])
         let payloadString = String(data: payload ?? Data(), encoding: .utf8) ?? ""
         return ("create_assessment", fileId, payloadString)
     }

     let manager = OfflineQueueManagerExtended.shared
     let batchId = manager.enqueueBatch(
         operationType: "assess_multiple",
         items: items,
         in: modelContext
     )

     // Monitor batch
     Task {
         while let batch = manager.batchOperations.first(where: { $0.id == batchId }) {
             print("Batch progress: \(Int(batch.percentComplete * 100))%")
             try await Task.sleep(nanoseconds: 1_000_000_000)
         }
     }
 }
 */
