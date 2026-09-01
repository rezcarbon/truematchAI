import XCTest
@testable import TrueMatch

final class CareerCoachIntegrationTests: XCTestCase {
    var chatAPI: ChatAPI!
    var webSocketManager: WebSocketManager!
    var chatStorage: ChatStorage!
    var networkMonitor: NetworkMonitor!

    override func setUp() {
        super.setUp()
        networkMonitor = NetworkMonitor()
        chatAPI = ChatAPI(networkMonitor: networkMonitor)
        webSocketManager = WebSocketManager()
        chatStorage = ChatStorage()
    }

    override func tearDown() {
        chatAPI = nil
        webSocketManager = nil
        chatStorage = nil
        networkMonitor = nil
        super.tearDown()
    }

    // MARK: - Send Message Tests

    func testSendChatMessage() {
        // Arrange
        let message = "What skills should I develop for AI roles?"
        let expectation = XCTestExpectation(description: "send message")

        // Act
        chatAPI.sendMessage(message) { result in
            switch result {
            case .success(let response):
                XCTAssertNotNil(response)
                XCTAssertFalse(response.isEmpty)
                expectation.fulfill()
            case .failure(let error):
                XCTFail("Failed to send message: \(error)")
            }
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)
    }

    func testSendMessageWithContext() {
        // Arrange
        let context = ChatContext(
            userProfile: "5 years iOS experience",
            currentRole: "Senior iOS Developer",
            goals: ["Learn AI/ML"]
        )

        let message = "Based on my background, which AI skills would be most valuable?"
        let expectation = XCTestExpectation(description: "send contextualized message")

        // Act
        chatAPI.sendMessage(message, context: context) { result in
            if case .success(let response) = result {
                expectation.fulfill()
            }
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)
    }

    func testMultipleTurnsConversation() {
        // Arrange
        let expectations = (0..<3).map { _ in
            XCTestExpectation(description: "turn completed")
        }

        let messages = [
            "Tell me about machine learning careers",
            "What's the typical salary range?",
            "How do I get started learning?"
        ]

        var conversationFlow: [String] = []

        // Act
        var completedTurns = 0
        for (index, message) in messages.enumerated() {
            chatAPI.sendMessage(message) { [weak self] result in
                if case .success(let response) = result {
                    conversationFlow.append(response)
                    completedTurns += 1
                }
                expectations[index].fulfill()
            }
        }

        // Assert
        wait(for: expectations, timeout: 30.0)
        XCTAssertEqual(conversationFlow.count, 3)
    }

    // MARK: - WebSocket Response Tests

    func testReceiveWebSocketResponse() {
        // Arrange
        let expectation = XCTestExpectation(description: "websocket response")

        let testMessage = "Here's my response to your question"

        // Act
        webSocketManager.connect { [weak self] in
            self?.webSocketManager.onMessageReceived = { message in
                XCTAssertEqual(message.text, testMessage)
                expectation.fulfill()
            }

            // Simulate receiving a response
            self?.webSocketManager.simulateMessageReceived(testMessage)
        }

        // Assert
        wait(for: [expectation], timeout: 5.0)
    }

    func testWebSocketRealtimeMessaging() {
        // Arrange
        let expectation = XCTestExpectation(description: "realtime messaging")
        expectation.expectedFulfillmentCount = 2

        // Act
        webSocketManager.connect { [weak self] in
            self?.chatAPI.sendMessage("What are data science trends?") { _ in
                expectation.fulfill()
            }

            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                self?.webSocketManager.onMessageReceived = { _ in
                    expectation.fulfill()
                }
                self?.webSocketManager.simulateMessageReceived("Emerging trends include...")
            }
        }

        // Assert
        wait(for: [expectation], timeout: 10.0)
    }

    // MARK: - Chat History Tests

    func testSaveAndLoadChatHistory() {
        // Arrange
        let messages = [
            ChatMessage(id: "1", text: "Hi coach", sender: .user),
            ChatMessage(id: "2", text: "Hello! How can I help?", sender: .coach),
            ChatMessage(id: "3", text: "Tell me about career paths", sender: .user)
        ]

        let saveExpectation = XCTestExpectation(description: "history saved")
        saveExpectation.expectedFulfillmentCount = messages.count

        // Act
        for message in messages {
            chatStorage.saveMessage(message) { _ in
                saveExpectation.fulfill()
            }
        }

        wait(for: [saveExpectation], timeout: 10.0)

        // Load history
        let loadExpectation = XCTestExpectation(description: "history loaded")
        chatStorage.loadHistory { history in
            XCTAssertGreaterThanOrEqual(history.count, 3)
            loadExpectation.fulfill()
        }

        wait(for: [loadExpectation], timeout: 5.0)
    }

    func testHistoryPreservesContext() {
        // Arrange
        let userMessage = ChatMessage(
            id: "ctx1",
            text: "I want to transition from sales to product management",
            sender: .user
        )
        let coachResponse = ChatMessage(
            id: "ctx2",
            text: "That's a great transition. Your sales skills are valuable...",
            sender: .coach
        )

        let expectation = XCTestExpectation(description: "context preserved")
        expectation.expectedFulfillmentCount = 2

        // Act
        chatStorage.saveMessage(userMessage) { _ in
            expectation.fulfill()
        }

        chatStorage.saveMessage(coachResponse) { _ in
            expectation.fulfill()
        }

        wait(for: [expectation], timeout: 10.0)

        // Assert - verify order and content
        chatStorage.loadHistory { history in
            XCTAssertGreater(history.count, 0)
            let firstContextMessage = history.first { $0.id == "ctx1" }
            XCTAssertNotNil(firstContextMessage)
        }
    }

    func testClearChatHistory() {
        // Arrange
        let message = ChatMessage(id: "to_clear", text: "Clear me", sender: .user)

        let saveExpectation = XCTestExpectation(description: "save then clear")
        chatStorage.saveMessage(message) { _ in
            saveExpectation.fulfill()
        }

        wait(for: [saveExpectation], timeout: 5.0)

        let clearExpectation = XCTestExpectation(description: "cleared")

        // Act
        chatStorage.clearHistory { _ in
            clearExpectation.fulfill()
        }

        // Assert
        wait(for: [clearExpectation], timeout: 5.0)

        chatStorage.loadHistory { history in
            XCTAssertEqual(history.filter { $0.id == "to_clear" }.count, 0)
        }
    }

    // MARK: - Offline Chat Tests

    func testOfflineMessageQueue() {
        // Arrange
        networkMonitor.simulateOffline()

        let message = "Offline message"
        let expectation = XCTestExpectation(description: "offline queued")

        // Act
        chatAPI.sendMessage(message) { result in
            // In offline mode, should queue locally
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 5.0)
    }

    func testSyncOfflineMessages() {
        // Arrange
        networkMonitor.simulateOffline()

        let offlineMessage = "Message sent while offline"
        let offlineExpectation = XCTestExpectation(description: "offline message")

        chatAPI.sendMessage(offlineMessage) { _ in
            offlineExpectation.fulfill()
        }

        wait(for: [offlineExpectation], timeout: 5.0)

        // Now go online
        networkMonitor.simulateOnline()

        let syncExpectation = XCTestExpectation(description: "messages synced")

        // Act
        chatAPI.syncOfflineMessages { result in
            if case .success = result {
                syncExpectation.fulfill()
            }
        }

        // Assert
        wait(for: [syncExpectation], timeout: 10.0)
    }

    // MARK: - Integration Flow Tests

    func testCompleteCareerCoachFlow() {
        // Arrange
        let expectation = XCTestExpectation(description: "complete flow")
        expectation.expectedFulfillmentCount = 4

        // Act
        // 1. Send initial question
        chatAPI.sendMessage("I want to grow my career") { result in
            if case .success = result {
                expectation.fulfill()
            }
        }

        // 2. Save message to history
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) { [weak self] in
            let message = ChatMessage(
                id: "flow1",
                text: "I want to grow my career",
                sender: .user
            )
            self?.chatStorage.saveMessage(message) { _ in
                expectation.fulfill()
            }
        }

        // 3. Receive coach response
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) { [weak self] in
            self?.webSocketManager.connect { [weak self] in
                self?.webSocketManager.onMessageReceived = { message in
                    expectation.fulfill()
                }
                self?.webSocketManager.simulateMessageReceived("Great! Let's discuss your goals...")
            }
        }

        // 4. Save response
        DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) { [weak self] in
            let response = ChatMessage(
                id: "flow2",
                text: "Great! Let's discuss your goals...",
                sender: .coach
            )
            self?.chatStorage.saveMessage(response) { _ in
                expectation.fulfill()
            }
        }

        // Assert
        wait(for: [expectation], timeout: 30.0)
    }

    // MARK: - Performance Tests

    func testSendMessagePerformance() {
        measure {
            let expectation = XCTestExpectation(description: "perf")
            chatAPI.sendMessage("Performance test message") { _ in
                expectation.fulfill()
            }
            wait(for: [expectation], timeout: 15.0)
        }
    }

    func testLoadLargeChatHistoryPerformance() {
        // Arrange - create 100 messages
        let saveExpectations = (0..<100).map { _ in
            XCTestExpectation(description: "save")
        }

        for i in 0..<100 {
            let message = ChatMessage(
                id: "\(i)",
                text: "Message \(i)",
                sender: i % 2 == 0 ? .user : .coach
            )
            chatStorage.saveMessage(message) { _ in
                saveExpectations[i].fulfill()
            }
        }

        wait(for: saveExpectations, timeout: 30.0)

        // Act & Assert
        measure {
            let loadExpectation = XCTestExpectation(description: "perf load")
            chatStorage.loadHistory { _ in
                loadExpectation.fulfill()
            }
            wait(for: [loadExpectation], timeout: 5.0)
        }
    }
}
