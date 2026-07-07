import XCTest
@testable import TrueMatch

final class LocalStoreTests: XCTestCase {
    var localStore: LocalStore!
    var testFileURL: URL!

    override func setUp() {
        super.setUp()

        let tempDir = FileManager.default.temporaryDirectory
        testFileURL = tempDir.appendingPathComponent("testStore.sqlite")

        localStore = LocalStore(storageURL: testFileURL)
    }

    override func tearDown() {
        try? FileManager.default.removeItem(at: testFileURL)
        localStore = nil
        super.tearDown()
    }

    // MARK: - Create/Write Tests

    func testCreateRecord() throws {
        // Arrange
        let record: [String: Any] = [
            "id": "record1",
            "name": "Test Record",
            "timestamp": Date().timeIntervalSince1970
        ]

        // Act
        try localStore.save(record, forKey: "test_record_1")

        // Assert
        let retrieved = try localStore.fetch(key: "test_record_1")
        XCTAssertNotNil(retrieved)
        XCTAssertEqual(retrieved?["id"] as? String, "record1")
    }

    func testCreateMultipleRecords() throws {
        // Arrange
        let records = (0..<10).map { i -> [String: Any] in
            [
                "id": "record\(i)",
                "index": i,
                "timestamp": Date().timeIntervalSince1970
            ]
        }

        // Act
        for (index, record) in records.enumerated() {
            try localStore.save(record, forKey: "record\(index)")
        }

        // Assert
        for i in 0..<10 {
            let retrieved = try localStore.fetch(key: "record\(i)")
            XCTAssertNotNil(retrieved)
            XCTAssertEqual(retrieved?["id"] as? String, "record\(i)")
        }
    }

    // MARK: - Read/Fetch Tests

    func testFetchExistingRecord() throws {
        // Arrange
        let record: [String: Any] = [
            "id": "fetch_test",
            "data": "important_data"
        ]
        try localStore.save(record, forKey: "fetch_key")

        // Act
        let retrieved = try localStore.fetch(key: "fetch_key")

        // Assert
        XCTAssertNotNil(retrieved)
        XCTAssertEqual(retrieved?["data"] as? String, "important_data")
    }

    func testFetchNonexistentRecord() throws {
        // Act
        let retrieved = try localStore.fetch(key: "nonexistent_key")

        // Assert
        XCTAssertNil(retrieved)
    }

    func testFetchAllRecords() throws {
        // Arrange
        let records = (0..<5).map { i -> [String: Any] in
            ["id": "all\(i)", "value": i]
        }

        for (index, record) in records.enumerated() {
            try localStore.save(record, forKey: "all\(index)")
        }

        // Act
        let allRecords = try localStore.fetchAll()

        // Assert
        XCTAssertGreaterThanOrEqual(allRecords.count, 5)
    }

    // MARK: - Update Tests

    func testUpdateRecord() throws {
        // Arrange
        var record: [String: Any] = [
            "id": "update_test",
            "version": 1
        ]
        try localStore.save(record, forKey: "update_key")

        // Act
        record["version"] = 2
        record["updated"] = true
        try localStore.save(record, forKey: "update_key")

        // Assert
        let retrieved = try localStore.fetch(key: "update_key")
        XCTAssertEqual(retrieved?["version"] as? Int, 2)
        XCTAssertEqual(retrieved?["updated"] as? Bool, true)
    }

    func testUpdateMultipleRecords() throws {
        // Arrange
        for i in 0..<5 {
            try localStore.save(["id": "multi\(i)", "status": "initial"], forKey: "multi\(i)")
        }

        // Act
        for i in 0..<5 {
            var record = try localStore.fetch(key: "multi\(i)") ?? [:]
            record["status"] = "updated"
            try localStore.save(record, forKey: "multi\(i)")
        }

        // Assert
        for i in 0..<5 {
            let retrieved = try localStore.fetch(key: "multi\(i)")
            XCTAssertEqual(retrieved?["status"] as? String, "updated")
        }
    }

    // MARK: - Delete Tests

    func testDeleteRecord() throws {
        // Arrange
        try localStore.save(["id": "delete_test"], forKey: "delete_key")

        // Act
        try localStore.delete(key: "delete_key")

        // Assert
        let retrieved = try localStore.fetch(key: "delete_key")
        XCTAssertNil(retrieved)
    }

    func testDeleteNonexistentRecord() throws {
        // Act & Assert - should not throw
        XCTAssertNoThrow {
            try localStore.delete(key: "nonexistent_delete")
        }
    }

    func testDeleteMultipleRecords() throws {
        // Arrange
        let keys = (0..<5).map { "delete_multi\($0)" }
        for (index, key) in keys.enumerated() {
            try localStore.save(["id": "record\(index)"], forKey: key)
        }

        // Act
        for key in keys {
            try localStore.delete(key: key)
        }

        // Assert
        for key in keys {
            let retrieved = try localStore.fetch(key: key)
            XCTAssertNil(retrieved)
        }
    }

    // MARK: - Pruning Tests

    func testPruneOldRecords() throws {
        // Arrange
        let oldDate = Date(timeIntervalSinceNow: -86400 * 30) // 30 days ago
        let newDate = Date()

        try localStore.save(
            ["id": "old_record", "timestamp": oldDate.timeIntervalSince1970],
            forKey: "old"
        )
        try localStore.save(
            ["id": "new_record", "timestamp": newDate.timeIntervalSince1970],
            forKey: "new"
        )

        // Act
        try localStore.prune(olderThan: 86400 * 7) // 7 days

        // Assert
        let oldRetrieved = try localStore.fetch(key: "old")
        let newRetrieved = try localStore.fetch(key: "new")

        XCTAssertNil(oldRetrieved)
        XCTAssertNotNil(newRetrieved)
    }

    func testPruneBySize() throws {
        // Arrange - create records
        for i in 0..<20 {
            try localStore.save(
                ["id": "record\(i)", "data": String(repeating: "x", count: 1000)],
                forKey: "record\(i)"
            )
        }

        // Act
        try localStore.pruneBySize(maxSizeInBytes: 50000)

        // Assert
        let allRecords = try localStore.fetchAll()
        XCTAssertLess(allRecords.count, 20)
    }

    func testPruneEmptyStore() throws {
        // Act & Assert - should not throw
        XCTAssertNoThrow {
            try localStore.prune(olderThan: 86400)
        }
    }

    // MARK: - Encoding/Decoding Tests

    func testSaveComplexData() throws {
        // Arrange
        let complexData: [String: Any] = [
            "id": "complex_1",
            "strings": ["a", "b", "c"],
            "numbers": [1, 2, 3],
            "nested": [
                "deep": [
                    "value": "test"
                ]
            ]
        ]

        // Act
        try localStore.save(complexData, forKey: "complex")

        // Assert
        let retrieved = try localStore.fetch(key: "complex")
        XCTAssertNotNil(retrieved)
        XCTAssertEqual(retrieved?["id"] as? String, "complex_1")
    }

    func testSaveWithSpecialCharacters() throws {
        // Arrange
        let specialData: [String: Any] = [
            "id": "special_1",
            "text": "Hello 世界 🌍",
            "symbols": "!@#$%^&*()"
        ]

        // Act
        try localStore.save(specialData, forKey: "special")

        // Assert
        let retrieved = try localStore.fetch(key: "special")
        XCTAssertEqual(retrieved?["text"] as? String, "Hello 世界 🌍")
        XCTAssertEqual(retrieved?["symbols"] as? String, "!@#$%^&*()")
    }

    // MARK: - CRUD Batch Operations

    func testBatchCreate() throws {
        // Arrange
        let records = (0..<10).map { i -> ([String: Any], String) in
            (["id": "batch\(i)", "index": i], "batch\(i)")
        }

        // Act
        for (record, key) in records {
            try localStore.save(record, forKey: key)
        }

        // Assert
        for i in 0..<10 {
            let retrieved = try localStore.fetch(key: "batch\(i)")
            XCTAssertNotNil(retrieved)
        }
    }

    func testBatchUpdate() throws {
        // Arrange
        for i in 0..<5 {
            try localStore.save(["id": "batch_update\(i)", "status": "initial"], forKey: "bu\(i)")
        }

        // Act
        for i in 0..<5 {
            var record = try localStore.fetch(key: "bu\(i)") ?? [:]
            record["status"] = "updated"
            try localStore.save(record, forKey: "bu\(i)")
        }

        // Assert
        for i in 0..<5 {
            let retrieved = try localStore.fetch(key: "bu\(i)")
            XCTAssertEqual(retrieved?["status"] as? String, "updated")
        }
    }

    func testBatchDelete() throws {
        // Arrange
        let keys = (0..<5).map { "batch_delete\($0)" }
        for (index, key) in keys.enumerated() {
            try localStore.save(["id": "record\(index)"], forKey: key)
        }

        // Act
        for key in keys {
            try localStore.delete(key: key)
        }

        // Assert
        for key in keys {
            let retrieved = try localStore.fetch(key: key)
            XCTAssertNil(retrieved)
        }
    }

    // MARK: - Performance Tests

    func testSavePerformance() {
        measure {
            for i in 0..<100 {
                try? localStore.save(["id": "perf\(i)", "data": "test"], forKey: "perf\(i)")
            }
        }
    }

    func testFetchPerformance() throws {
        // Arrange
        for i in 0..<100 {
            try localStore.save(["id": "perf_fetch\(i)"], forKey: "pf\(i)")
        }

        // Act & Assert
        measure {
            for i in 0..<100 {
                _ = try? localStore.fetch(key: "pf\(i)")
            }
        }
    }

    // MARK: - Helper

    private func XCTAssertNoThrow(
        _ expression: () throws -> Void,
        _ message: @autoclosure () -> String = "",
        file: StaticString = #filePath,
        line: UInt = #line
    ) {
        do {
            try expression()
        } catch {
            XCTFail("Expected no throw, but threw: \(error)", file: file, line: line)
        }
    }
}
