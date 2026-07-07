import XCTest
@testable import TrueMatch

final class CareerCoachViewModelTests: XCTestCase {
    var viewModel: CareerCoachViewModel!
    var mockAPIClient: MockAPIClient!
    var mockChatStorage: MockChatStorage!
    var mockWebSocketManager: MockWebSocketManager!

    override func setUp() {
        super.setUp()
        mockAPIClient = MockAPIClient()
        mockChatStorage = MockChatStorage()
        mockWebSocketManager = MockWebSocketManager()
        viewModel = CareerCoachViewModel(
            apiClient: mockAPIClient,
            chatStorage: mockChatStorage,
            webSocketManager: mockWebSocketManager
        )
    }

    override func tearDown() {
        viewModel = nil
        mockAPIClient = nil
        mockChatStorage = nil
        mockWebSocketManager = nil
        super.tearDown()
    }

    // MARK: - sendMessage Tests

    func testSendMessageSuccess() {
        // Arrange
        let message = "What skills should I develop?"
        mockAPIClient.mockChatResult = .success(
            ChatMessage(id: "msg1", text: "You should focus on...", sender: .coach)
        )

        var response: ChatMessage?
        var sendError: Error?
        let expectation = XCTestExpectation(description: "message sent")

        // Act
        viewModel.sendMessage(message) { result in
            switch result {
            case .success(let msg):
                response = msg
            case .failure(let error):
                sendError = error
            }
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 2.0)
        XCTAssertNil(sendError)
        XCTAssertNotNil(response)
        XCTAssertEqual(response?.sender, .coach)
    }

    func testSendMessageStoresInHistory() {
        // Arrange
        let message = "How do I get better at interviews?"
        mockAPIClient.mockChatResult = .success(
            ChatMessage(id: "msg2", text: "Practice is key...", sender: .coach)
        )

        let expectation = XCTestExpectation(description: "message stored")

        // Act
        viewModel.sendMessage(message) { _ in
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 2.0)
        XCTAssertTrue(mockChatStorage.storeCalled)
        XCTAssertEqual(mockChatStorage.storedMessages.count, 2) // user + coach
    }

    func testSendMessageFailureHandling() {
        // Arrange
        let message = "Test message"
        let mockError = NSError(domain: "test", code: 500, userInfo: nil)
        mockAPIClient.mockChatResult = .failure(mockError)

        var errorReceived: Error?
        let expectation = XCTestExpectation(description: "send failed")

        // Act
        viewModel.sendMessage(message) { result in
            if case .failure(let error) = result {
                errorReceived = error
            }
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 2.0)
        XCTAssertNotNil(errorReceived)
    }

    func testSendMessageValidatesInput() {
        // Arrange
        let emptyMessage = ""
        var validationError: Error?

        // Act
        viewModel.sendMessage(emptyMessage) { result in
            if case .failure(let error) = result {
                validationError = error
            }
        }

        // Assert
        XCTAssertNotNil(validationError)
        XCTAssertFalse(mockAPIClient.sendMessageCalled)
    }

    // MARK: - receiveResponse Tests

    func testReceiveResponseUpdatesViewState() {
        // Arrange
        let response = ChatMessage(
            id: "msg3",
            text: "Here's my advice...",
            sender: .coach
        )

        let expectation = XCTestExpectation(description: "response received")

        // Act
        mockWebSocketManager.delegate = viewModel
        mockWebSocketManager.simulateMessageReceived(response) {
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 1.0)
        XCTAssertTrue(viewModel.messages.contains { $0.id == "msg3" })
    }

    func testReceiveResponseHandlesEmpty() {
        // Arrange
        let emptyResponse = ChatMessage(
            id: "msg4",
            text: "",
            sender: .coach
        )

        // Act
        viewModel.receiveResponse(emptyResponse)

        // Assert
        XCTAssertTrue(viewModel.messages.contains { $0.id == "msg4" })
    }

    func testReceiveResponseOrdersMaintained() {
        // Arrange
        let msg1 = ChatMessage(id: "1", text: "First", sender: .user)
        let msg2 = ChatMessage(id: "2", text: "Second", sender: .coach)
        let msg3 = ChatMessage(id: "3", text: "Third", sender: .user)

        // Act
        viewModel.addMessage(msg1)
        viewModel.receiveResponse(msg2)
        viewModel.addMessage(msg3)

        // Assert
        XCTAssertEqual(viewModel.messages[0].id, "1")
        XCTAssertEqual(viewModel.messages[1].id, "2")
        XCTAssertEqual(viewModel.messages[2].id, "3")
    }

    // MARK: - history Tests

    func testHistoryLoadsMessages() {
        // Arrange
        let mockMessages = [
            ChatMessage(id: "h1", text: "Previous message 1", sender: .user),
            ChatMessage(id: "h2", text: "Previous response 1", sender: .coach),
            ChatMessage(id: "h3", text: "Previous message 2", sender: .user)
        ]
        mockChatStorage.mockMessages = mockMessages

        let expectation = XCTestExpectation(description: "history loaded")

        // Act
        viewModel.loadHistory {
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 1.0)
        XCTAssertEqual(viewModel.messages.count, mockMessages.count)
    }

    func testHistoryPreservesSenderTypes() {
        // Arrange
        let mockMessages = [
            ChatMessage(id: "s1", text: "User message", sender: .user),
            ChatMessage(id: "s2", text: "Coach message", sender: .coach)
        ]
        mockChatStorage.mockMessages = mockMessages

        let expectation = XCTestExpectation(description: "senders preserved")

        // Act
        viewModel.loadHistory {
            expectation.fulfill()
        }

        // Assert
        wait(for: [expectation], timeout: 1.0)
        XCTAssertEqual(viewModel.messages[0].sender, .user)
        XCTAssertEqual(viewModel.messages[1].sender, .coach)
    }

    func testClearHistory() {
        // Arrange
        viewModel.messages = [
            ChatMessage(id: "c1", text: "Message to clear", sender: .user)
        ]

        // Act
        viewModel.clearHistory()

        // Assert
        XCTAssertTrue(viewModel.messages.isEmpty)
        XCTAssertTrue(mockChatStorage.clearCalled)
    }

    // MARK: - Performance Tests

    func testSendMessagePerformance() {
        // Arrange
        mockAPIClient.mockChatResult = .success(
            ChatMessage(id: "perf1", text: "Response", sender: .coach)
        )

        measure {
            let expectation = XCTestExpectation(description: "perf test")
            viewModel.sendMessage("Performance test message") { _ in
                expectation.fulfill()
            }
            wait(for: [expectation], timeout: 2.0)
        }
    }

    func testLargeHistoryLoadPerformance() {
        // Arrange
        var largeHistory: [ChatMessage] = []
        for i in 0..<100 {
            largeHistory.append(
                ChatMessage(
                    id: "\(i)",
                    text: "Message \(i)",
                    sender: i % 2 == 0 ? .user : .coach
                )
            )
        }
        mockChatStorage.mockMessages = largeHistory

        measure {
            let expectation = XCTestExpectation(description: "large history")
            viewModel.loadHistory {
                expectation.fulfill()
            }
            wait(for: [expectation], timeout: 2.0)
        }
    }
}
