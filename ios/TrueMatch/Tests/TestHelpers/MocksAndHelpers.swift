import Foundation
@testable import TrueMatch

// MARK: - Mock API Client

class MockAPIClient: APIClientProtocol {
    // Pipeline
    var mockPipelineResult: Result<PipelineData, Error>?
    var fetchPipelineCalled = false
    var lastFetchPipelineCompletion: ((Result<PipelineData, Error>) -> Void)?

    // Candidate Updates
    var mockUpdateResult: Result<Void, Error>?
    var updateCandidateStatusCalled = false
    var lastUpdatedCandidateID: String?
    var lastUpdatedStatus: CandidateStatus?

    // Swiping
    var mockSwipeResult: Result<Void, Error>?
    var recordSwipeCalled = false
    var lastSwipeDirection: SwipeDirection?
    var lastSwipedJobID: String?

    // Jobs
    var mockJobsResult: Result<[JobRecommendation], Error>?
    var fetchJobsCalled = false

    // Assessment
    var mockAssessmentResult: Result<AssessmentResult, Error>?
    var fetchAssessmentCalled = false

    // Messages
    var mockMessageResult: Result<ChatMessage, Error>?
    var sendMessageCalled = false
    var lastSentMessage: ChatMessage?

    // Chat
    var mockChatHistoryResult: Result<[ChatMessage], Error>?
    var fetchChatHistoryCalled = false

    func fetchPipeline(completion: @escaping (Result<PipelineData, Error>) -> Void) {
        fetchPipelineCalled = true
        lastFetchPipelineCompletion = completion
        if let result = mockPipelineResult {
            completion(result)
        }
    }

    func updateCandidateStatus(
        candidateID: String,
        status: CandidateStatus,
        completion: @escaping (Result<Void, Error>) -> Void
    ) {
        updateCandidateStatusCalled = true
        lastUpdatedCandidateID = candidateID
        lastUpdatedStatus = status
        if let result = mockUpdateResult {
            completion(result)
        }
    }

    func recordSwipe(
        jobID: String,
        direction: SwipeDirection,
        completion: @escaping (Result<Void, Error>) -> Void
    ) {
        recordSwipeCalled = true
        lastSwipedJobID = jobID
        lastSwipeDirection = direction
        if let result = mockSwipeResult {
            completion(result)
        }
    }

    func fetchJobs(completion: @escaping (Result<[JobRecommendation], Error>) -> Void) {
        fetchJobsCalled = true
        if let result = mockJobsResult {
            completion(result)
        }
    }

    func fetchAssessment(id: String, completion: @escaping (Result<AssessmentResult, Error>) -> Void) {
        fetchAssessmentCalled = true
        if let result = mockAssessmentResult {
            completion(result)
        }
    }

    func sendMessage(
        _ message: ChatMessage,
        completion: @escaping (Result<ChatMessage, Error>) -> Void
    ) {
        sendMessageCalled = true
        lastSentMessage = message
        if let result = mockMessageResult {
            completion(result)
        }
    }

    func fetchChatHistory(completion: @escaping (Result<[ChatMessage], Error>) -> Void) {
        fetchChatHistoryCalled = true
        if let result = mockChatHistoryResult {
            completion(result)
        }
    }
}

// MARK: - Mock Cache Manager

class MockCacheManager: CacheManagerProtocol {
    var getCacheCalled = false
    var setCacheCalled = false
    var clearCacheCalled = false

    var mockCachedPipeline: PipelineData?
    var mockCachedJobs: [JobRecommendation]?
    var mockCachedAssessment: AssessmentResult?

    func getCachedPipeline() -> PipelineData? {
        getCacheCalled = true
        return mockCachedPipeline
    }

    func setCachedPipeline(_ pipeline: PipelineData) {
        setCacheCalled = true
        mockCachedPipeline = pipeline
    }

    func getCachedJobs() -> [JobRecommendation]? {
        return mockCachedJobs
    }

    func setCachedJobs(_ jobs: [JobRecommendation]) {
        mockCachedJobs = jobs
    }

    func getCachedAssessment(id: String) -> AssessmentResult? {
        return mockCachedAssessment
    }

    func setCachedAssessment(_ assessment: AssessmentResult) {
        mockCachedAssessment = assessment
    }

    func clearCache() {
        clearCacheCalled = true
        mockCachedPipeline = nil
        mockCachedJobs = nil
        mockCachedAssessment = nil
    }

    func pruneExpiredCache() {
        // Prune logic
    }
}

// MARK: - Mock Persistence Manager

class MockPersistenceManager: PersistenceManagerProtocol {
    var saveCalled = false
    var loadCalled = false
    var deleteCalled = false

    var mockSaveResult: Result<Void, Error>?
    var mockLoadResult: Result<[String: Any], Error>?
    var mockDeleteResult: Result<Void, Error>?

    var savedData: [String: Any] = [:]

    func save(_ data: [String: Any], for key: String, completion: @escaping (Result<Void, Error>) -> Void) {
        saveCalled = true
        savedData[key] = data
        if let result = mockSaveResult {
            completion(result)
        }
    }

    func load(for key: String, completion: @escaping (Result<[String: Any], Error>) -> Void) {
        loadCalled = true
        if let result = mockLoadResult {
            completion(result)
        } else if let data = savedData[key] as? [String: Any] {
            completion(.success(data))
        }
    }

    func delete(for key: String, completion: @escaping (Result<Void, Error>) -> Void) {
        deleteCalled = true
        savedData.removeValue(forKey: key)
        if let result = mockDeleteResult {
            completion(result)
        }
    }
}

// MARK: - Mock Assessment Cache

class MockAssessmentCache: AssessmentCacheProtocol {
    var getCacheCalled = false
    var setCacheCalled = false

    var mockCachedAssessment: AssessmentResult?

    func getCachedAssessment(id: String) -> AssessmentResult? {
        getCacheCalled = true
        return mockCachedAssessment
    }

    func setCachedAssessment(_ assessment: AssessmentResult) {
        setCacheCalled = true
        mockCachedAssessment = assessment
    }

    func getAllCachedAssessments() -> [AssessmentResult] {
        return mockCachedAssessment.map { [$0] } ?? []
    }

    func clearCache() {
        mockCachedAssessment = nil
    }
}

// MARK: - Mock Offline Queue Manager

class MockOfflineQueueManager: OfflineQueueManagerProtocol {
    var enqueueCalled = false
    var flushCalled = false
    var retryCalled = false

    var mockFlushResult: Result<Void, Error>?
    var queuedOperations: [OfflineOperation] = []

    func enqueue(_ operation: OfflineOperation) {
        enqueueCalled = true
        queuedOperations.append(operation)
    }

    func flush(completion: @escaping (Result<Void, Error>) -> Void) {
        flushCalled = true
        if let result = mockFlushResult {
            completion(result)
        }
    }

    func retry(completion: @escaping (Result<Void, Error>) -> Void) {
        retryCalled = true
        if let result = mockFlushResult {
            completion(result)
        }
    }

    func getPendingOperationCount() -> Int {
        return queuedOperations.count
    }

    func clearQueue() {
        queuedOperations.removeAll()
    }
}

// MARK: - Mock Network Monitor

class MockNetworkMonitor: NetworkMonitorProtocol {
    var isConnected = true
    var isOnWiFi = true

    var connectionChangeCallbacks: [() -> Void] = []

    func addConnectionChangeListener(_ callback: @escaping () -> Void) {
        connectionChangeCallbacks.append(callback)
    }

    func removeConnectionChangeListener() {
        connectionChangeCallbacks.removeAll()
    }

    func simulateOffline() {
        isConnected = false
        notifyListeners()
    }

    func simulateOnline() {
        isConnected = true
        notifyListeners()
    }

    private func notifyListeners() {
        connectionChangeCallbacks.forEach { $0() }
    }
}

// MARK: - Mock WebSocket Manager

class MockWebSocketManager: WebSocketManagerProtocol {
    var isConnected = false
    var connectCalled = false
    var disconnectCalled = false
    var sendCalled = false

    var onMessageReceived: ((WebSocketMessage) -> Void)?
    var onConnectionStatusChanged: ((Bool) -> Void)?

    var messageQueue: [WebSocketMessage] = []

    func connect(completion: @escaping () -> Void) {
        connectCalled = true
        isConnected = true
        onConnectionStatusChanged?(true)
        completion()
    }

    func disconnect() {
        disconnectCalled = true
        isConnected = false
        onConnectionStatusChanged?(false)
    }

    func send(_ message: WebSocketMessage) {
        sendCalled = true
        messageQueue.append(message)
    }

    func simulateDisconnection() {
        isConnected = false
        onConnectionStatusChanged?(false)
    }

    func simulateMessageReceived(_ message: WebSocketMessage) {
        onMessageReceived?(message)
    }
}

// MARK: - Test Data Builders

class TestDataBuilder {
    static func makePipelineData(candidateCount: Int = 2) -> PipelineData {
        let candidates = (0..<candidateCount).map { i in
            Candidate(
                id: "candidate_\(i)",
                name: "Candidate \(i)",
                status: CandidateStatus.allCases[i % CandidateStatus.allCases.count]
            )
        }

        return PipelineData(
            candidates: candidates,
            stats: PipelineStats(total: candidateCount, byStage: [:])
        )
    }

    static func makeJobRecommendations(count: Int = 5) -> [JobRecommendation] {
        return (0..<count).map { i in
            JobRecommendation(
                id: "job_\(i)",
                title: "Job Title \(i)",
                matchScore: Double.random(in: 0.5...1.0)
            )
        }
    }

    static func makeAssessmentResult(id: String = "assessment_1") -> AssessmentResult {
        return AssessmentResult(
            id: id,
            timestamp: Date(),
            scores: [
                AssessmentScore(category: "leadership", value: 0.85),
                AssessmentScore(category: "communication", value: 0.90),
                AssessmentScore(category: "teamwork", value: 0.80),
                AssessmentScore(category: "problem_solving", value: 0.88)
            ]
        )
    }

    static func makeChatMessage(id: String = "msg_1", sender: String = "user") -> ChatMessage {
        return ChatMessage(
            id: id,
            sender: sender,
            content: "Test message",
            timestamp: Date()
        )
    }

    static func makeChatHistory(messageCount: Int = 5) -> [ChatMessage] {
        return (0..<messageCount).map { i in
            ChatMessage(
                id: "msg_\(i)",
                sender: i % 2 == 0 ? "user" : "assistant",
                content: "Message \(i)",
                timestamp: Date(timeIntervalSinceNow: -Double(messageCount - i) * 60)
            )
        }
    }

    static func makeCandidate(id: String = "candidate_1", status: CandidateStatus = .new) -> Candidate {
        return Candidate(id: id, name: "Test Candidate", status: status)
    }
}

// MARK: - Test Extensions

extension XCTestCase {
    func waitForAsync(timeout: TimeInterval = 1.0, _ block: @escaping (@escaping () -> Void) -> Void) {
        let expectation = XCTestExpectation(description: "async operation")
        block {
            expectation.fulfill()
        }
        wait(for: [expectation], timeout: timeout)
    }

    func createTemporaryDirectory() -> URL {
        let temp = FileManager.default.temporaryDirectory
        let dir = temp.appendingPathComponent(UUID().uuidString)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }

    func cleanupTemporaryDirectory(_ url: URL) {
        try? FileManager.default.removeItem(at: url)
    }
}

// MARK: - Protocol Definitions

protocol APIClientProtocol {
    func fetchPipeline(completion: @escaping (Result<PipelineData, Error>) -> Void)
    func updateCandidateStatus(candidateID: String, status: CandidateStatus, completion: @escaping (Result<Void, Error>) -> Void)
    func recordSwipe(jobID: String, direction: SwipeDirection, completion: @escaping (Result<Void, Error>) -> Void)
    func fetchJobs(completion: @escaping (Result<[JobRecommendation], Error>) -> Void)
    func fetchAssessment(id: String, completion: @escaping (Result<AssessmentResult, Error>) -> Void)
    func sendMessage(_ message: ChatMessage, completion: @escaping (Result<ChatMessage, Error>) -> Void)
    func fetchChatHistory(completion: @escaping (Result<[ChatMessage], Error>) -> Void)
}

protocol CacheManagerProtocol {
    func getCachedPipeline() -> PipelineData?
    func setCachedPipeline(_ pipeline: PipelineData)
    func getCachedJobs() -> [JobRecommendation]?
    func setCachedJobs(_ jobs: [JobRecommendation])
    func getCachedAssessment(id: String) -> AssessmentResult?
    func setCachedAssessment(_ assessment: AssessmentResult)
    func clearCache()
    func pruneExpiredCache()
}

protocol PersistenceManagerProtocol {
    func save(_ data: [String: Any], for key: String, completion: @escaping (Result<Void, Error>) -> Void)
    func load(for key: String, completion: @escaping (Result<[String: Any], Error>) -> Void)
    func delete(for key: String, completion: @escaping (Result<Void, Error>) -> Void)
}

protocol AssessmentCacheProtocol {
    func getCachedAssessment(id: String) -> AssessmentResult?
    func setCachedAssessment(_ assessment: AssessmentResult)
    func getAllCachedAssessments() -> [AssessmentResult]
    func clearCache()
}

protocol OfflineQueueManagerProtocol {
    func enqueue(_ operation: OfflineOperation)
    func flush(completion: @escaping (Result<Void, Error>) -> Void)
    func retry(completion: @escaping (Result<Void, Error>) -> Void)
    func getPendingOperationCount() -> Int
    func clearQueue()
}

protocol NetworkMonitorProtocol {
    var isConnected: Bool { get }
    var isOnWiFi: Bool { get }
    func addConnectionChangeListener(_ callback: @escaping () -> Void)
    func removeConnectionChangeListener()
}

protocol WebSocketManagerProtocol {
    var isConnected: Bool { get }
    func connect(completion: @escaping () -> Void)
    func disconnect()
    func send(_ message: WebSocketMessage)
}

// MARK: - Model Stubs

enum SwipeDirection {
    case left
    case right
}

struct OfflineOperation: Codable {
    let id: String
    let type: String
    let data: [String: AnyCodable]
}

struct WebSocketMessage {
    enum MessageType {
        case pipelineUpdate
        case jobUpdate
        case chatMessage
        case assessmentUpdate
    }

    let type: MessageType
    let data: [String: Any]
}

struct AnyCodable: Codable {
    let value: Any

    init(_ value: Any) {
        self.value = value
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        if let val = value as? String {
            try container.encode(val)
        } else if let val = value as? Int {
            try container.encode(val)
        } else if let val = value as? Double {
            try container.encode(val)
        } else if let val = value as? Bool {
            try container.encode(val)
        }
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let value = try? container.decode(String.self) {
            self.value = value
        } else if let value = try? container.decode(Int.self) {
            self.value = value
        } else if let value = try? container.decode(Double.self) {
            self.value = value
        } else if let value = try? container.decode(Bool.self) {
            self.value = value
        } else {
            self.value = NSNull()
        }
    }
}
