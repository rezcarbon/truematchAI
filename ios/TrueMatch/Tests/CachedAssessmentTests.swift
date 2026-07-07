import XCTest
@testable import TrueMatch

final class CachedAssessmentTests: XCTestCase {
    var testContainer: NSPersistentContainer!
    var modelContext: ModelContext!

    override func setUp() {
        super.setUp()
        testContainer = NSPersistentContainer(name: "TrueMatch")
        let description = NSPersistentStoreDescription()
        description.type = NSInMemoryStoreType
        testContainer.persistentStoreDescriptions = [description]

        testContainer.loadPersistentStores { _, error in
            XCTAssertNil(error)
        }

        modelContext = ModelContext(testContainer.mainContext)
    }

    override func tearDown() {
        testContainer = nil
        modelContext = nil
        super.tearDown()
    }

    // MARK: - Create Tests

    func testCreateCachedAssessment() {
        // Arrange
        let assessmentID = "test_assessment_1"
        let data: [String: Any] = [
            "scores": [
                ["category": "leadership", "value": 0.85],
                ["category": "communication", "value": 0.90]
            ]
        ]

        // Act
        let cached = CachedAssessment(
            id: assessmentID,
            data: data,
            syncStatus: .synced,
            lastUpdated: Date()
        )

        // Assert
        XCTAssertEqual(cached.id, assessmentID)
        XCTAssertEqual(cached.syncStatus, .synced)
        XCTAssertNotNil(cached.data)
    }

    func testCreateCachedAssessmentWithPendingStatus() {
        // Arrange
        let assessmentID = "pending_1"

        // Act
        let cached = CachedAssessment(
            id: assessmentID,
            data: [:],
            syncStatus: .pending,
            lastUpdated: Date()
        )

        // Assert
        XCTAssertEqual(cached.syncStatus, .pending)
    }

    // MARK: - Read Operations

    func testFetchCachedAssessment() throws {
        // Arrange
        let assessmentID = "fetch_test_1"
        let assessment = CachedAssessment(
            id: assessmentID,
            data: ["test": "data"],
            syncStatus: .synced,
            lastUpdated: Date()
        )
        try modelContext.save()

        // Act
        let fetched = try modelContext.fetch(
            CachedAssessment.self,
            predicate: #Predicate { $0.id == assessmentID }
        ).first

        // Assert
        XCTAssertNotNil(fetched)
        XCTAssertEqual(fetched?.id, assessmentID)
    }

    func testFetchNonexistentAssessment() throws {
        // Act
        let fetched = try modelContext.fetch(
            CachedAssessment.self,
            predicate: #Predicate { $0.id == "nonexistent" }
        ).first

        // Assert
        XCTAssertNil(fetched)
    }

    func testFetchBySyncStatus() throws {
        // Arrange
        let synced = CachedAssessment(
            id: "synced_1",
            data: [:],
            syncStatus: .synced,
            lastUpdated: Date()
        )
        let pending = CachedAssessment(
            id: "pending_1",
            data: [:],
            syncStatus: .pending,
            lastUpdated: Date()
        )
        try modelContext.save()

        // Act
        let pendingAssessments = try modelContext.fetch(
            CachedAssessment.self,
            predicate: #Predicate { $0.syncStatus == .pending }
        )

        // Assert
        XCTAssertEqual(pendingAssessments.count, 1)
        XCTAssertEqual(pendingAssessments.first?.id, "pending_1")
    }

    // MARK: - Update Operations

    func testUpdateAssessmentData() throws {
        // Arrange
        let assessmentID = "update_test_1"
        var assessment = CachedAssessment(
            id: assessmentID,
            data: ["version": "1"],
            syncStatus: .synced,
            lastUpdated: Date()
        )

        // Act
        assessment.data = ["version": "2"]
        try modelContext.save()

        // Assert
        let fetched = try modelContext.fetch(
            CachedAssessment.self,
            predicate: #Predicate { $0.id == assessmentID }
        ).first
        XCTAssertEqual(fetched?.data["version"] as? String, "2")
    }

    func testUpdateSyncStatus() throws {
        // Arrange
        let assessmentID = "sync_update_1"
        let assessment = CachedAssessment(
            id: assessmentID,
            data: [:],
            syncStatus: .pending,
            lastUpdated: Date()
        )
        try modelContext.save()

        // Act
        var fetched = try modelContext.fetch(
            CachedAssessment.self,
            predicate: #Predicate { $0.id == assessmentID }
        ).first!
        fetched.syncStatus = .synced
        try modelContext.save()

        // Assert
        let updated = try modelContext.fetch(
            CachedAssessment.self,
            predicate: #Predicate { $0.id == assessmentID }
        ).first
        XCTAssertEqual(updated?.syncStatus, .synced)
    }

    func testUpdateTimestamp() throws {
        // Arrange
        let assessmentID = "timestamp_1"
        let originalDate = Date(timeIntervalSinceNow: -3600)
        let assessment = CachedAssessment(
            id: assessmentID,
            data: [:],
            syncStatus: .synced,
            lastUpdated: originalDate
        )

        // Act
        let newDate = Date()
        var updated = try modelContext.fetch(
            CachedAssessment.self,
            predicate: #Predicate { $0.id == assessmentID }
        ).first!
        updated.lastUpdated = newDate
        try modelContext.save()

        // Assert
        let fetched = try modelContext.fetch(
            CachedAssessment.self,
            predicate: #Predicate { $0.id == assessmentID }
        ).first
        XCTAssertGreater(fetched!.lastUpdated.timeIntervalSince(originalDate), 3000)
    }

    // MARK: - Delete Operations

    func testDeleteCachedAssessment() throws {
        // Arrange
        let assessmentID = "delete_test_1"
        let assessment = CachedAssessment(
            id: assessmentID,
            data: [:],
            syncStatus: .synced,
            lastUpdated: Date()
        )

        // Act
        modelContext.delete(assessment)
        try modelContext.save()

        // Assert
        let fetched = try modelContext.fetch(
            CachedAssessment.self,
            predicate: #Predicate { $0.id == assessmentID }
        ).first
        XCTAssertNil(fetched)
    }

    // MARK: - Sync Status Tests

    func testFetchPendingSyncAssessments() throws {
        // Arrange
        let pending1 = CachedAssessment(
            id: "pending_sync_1",
            data: [:],
            syncStatus: .pending,
            lastUpdated: Date()
        )
        let pending2 = CachedAssessment(
            id: "pending_sync_2",
            data: [:],
            syncStatus: .pending,
            lastUpdated: Date()
        )
        let synced = CachedAssessment(
            id: "synced_1",
            data: [:],
            syncStatus: .synced,
            lastUpdated: Date()
        )
        try modelContext.save()

        // Act
        let pendingForSync = try modelContext.fetch(
            CachedAssessment.self,
            predicate: #Predicate { $0.syncStatus == .pending }
        )

        // Assert
        XCTAssertEqual(pendingForSync.count, 2)
    }

    // MARK: - Data Integrity Tests

    func testAssessmentDataPreservation() throws {
        // Arrange
        let complexData: [String: Any] = [
            "scores": [
                ["category": "leadership", "value": 0.85, "trend": "up"],
                ["category": "teamwork", "value": 0.92, "trend": "stable"]
            ],
            "metadata": [
                "assessor": "coach@example.com",
                "timestamp": "2026-07-08T10:00:00Z"
            ]
        ]
        let assessment = CachedAssessment(
            id: "complex_data_1",
            data: complexData,
            syncStatus: .synced,
            lastUpdated: Date()
        )

        // Act
        try modelContext.save()
        let fetched = try modelContext.fetch(
            CachedAssessment.self,
            predicate: #Predicate { $0.id == "complex_data_1" }
        ).first

        // Assert
        XCTAssertNotNil(fetched)
        XCTAssertEqual(
            fetched?.data["metadata"] as? [String: String],
            complexData["metadata"] as? [String: String]
        )
    }
}
