# CoachingAgentService Integration Guide

## Quick Start

### 1. Update Your Config.xcconfig

Ensure your `Config.xcconfig` has the required API keys:

```xcconfig
ANTHROPIC_API_KEY = sk-ant-your-actual-key-here
```

### 2. Verify Provider Availability Before Messaging

```swift
let service = CoachingAgentService(
    modelContext: modelContext,
    llmProvider: claudeProvider,
    providerType: .claude
)

// Check service is ready
let available = await service.isAvailable()
guard available else {
    print("AI service unavailable - try again later")
    return
}
```

### 3. Send Message with Error Handling

```swift
let result = await service.sendMessage(
    threadId: threadId,
    userMessage: "How can I improve my sleep?",
    userContext: userContext
)

switch result {
case .success(let aiResponse):
    // Display response to user
    displayMessage(aiResponse, role: .assistant)

case .failure(let error):
    switch error {
    case .providerUnavailable:
        showAlert("AI service temporarily unavailable. Please try again later.")
    
    case .rateLimited(let retryAfter):
        showAlert("Please wait \(Int(retryAfter)) seconds before sending another message.")
    
    case .networkError(let description, let retryable):
        if retryable {
            showAlert("Network error: \(description). Retrying...")
        } else {
            showAlert("Network error: \(description)")
        }
    
    case .threadNotFound:
        showAlert("Conversation not found. Starting new conversation...")
    
    case .llmError(let description):
        showAlert("AI error: \(description)")
    
    default:
        showAlert("Unexpected error: \(error.localizedDescription)")
    }
}
```

---

## Error Handling Patterns

### Pattern 1: Simple Alert

```swift
let result = await service.sendMessage(threadId: id, userMessage: msg)
if case .success(let response) = result {
    // Handle success
} else if case .failure(let error) = result {
    let userMessage = error.errorDescription ?? "An error occurred"
    showAlert(userMessage)
}
```

### Pattern 2: Retry with Backoff

```swift
func sendMessageWithRetry(_ message: String, threadId: String, maxAttempts: Int = 3) async {
    for attempt in 1...maxAttempts {
        let result = await service.sendMessage(threadId: threadId, userMessage: message)
        
        switch result {
        case .success(let response):
            displayMessage(response)
            return
        
        case .failure(let error):
            if case .rateLimited(let retryAfter) = error {
                try? await Task.sleep(nanoseconds: UInt64(retryAfter * 1_000_000_000))
                continue
            } else if case .networkError(_, let retryable) = error, retryable, attempt < maxAttempts {
                try? await Task.sleep(nanoseconds: 500_000_000)  // Wait 0.5s
                continue
            } else {
                showAlert("Failed to send message: \(error.localizedDescription)")
                return
            }
        }
    }
}
```

### Pattern 3: Graceful Degradation

```swift
let result = await service.sendMessage(threadId: id, userMessage: msg, userContext: context)

switch result {
case .success(let response):
    displayAIResponse(response)

case .failure(.providerUnavailable):
    // Fall back to preset responses
    displayOfflineResponse("I'm currently offline. Here's a pre-built response...")

case .failure(let error):
    // Partial functionality
    showToast(error.errorDescription ?? "Service unavailable")
}
```

---

## Configuration Guide

### Rate Limiting Customization

Create a custom rate limiter if needed:

```swift
// Create with custom limits
let rateLimiter = await RateLimiter(maxPerSecond: 3, maxPerMinute: 30)

// Initialize service with custom rate limiter
let service = CoachingAgentService(
    modelContext: modelContext,
    llmProvider: provider,
    providerType: .claude,
    rateLimiter: rateLimiter
)

// Reset for testing
await rateLimiter.reset()
```

### Logging Configuration

Monitor service activity via os.Logger:

```swift
// In Console.app, filter by subsystem "health.sovv.app"
// Category: "CoachingAgent"

// Or programmatically
let logger = Logger(subsystem: "health.sovv.app", category: "CoachingAgent")

// Enable detailed logging (Xcode scheme settings)
// Product → Scheme → Edit Scheme → Run → Environment Variables
// Set: OS_LOG_DEFAULT=DEBUG
```

---

## Testing Guide

### Run All Tests

```bash
xcodebuild test -project SleepMind.xcodeproj \
  -scheme SleepMind \
  -destination 'platform=iOS Simulator,name=iPhone 15 Pro' \
  -only-testing 'SleepMindTests/CoachingAgentServiceTests'
```

### Test Specific Scenario

```bash
# Test end-to-end flow
xcodebuild test -project SleepMind.xcodeproj \
  -scheme SleepMind \
  -destination 'platform=iOS Simulator,name=iPhone 15 Pro' \
  -only-testing 'SleepMindTests/CoachingAgentServiceTests/testSendMessageSuccessfulFlow'

# Test error handling
xcodebuild test -project SleepMind.xcodeproj \
  -scheme SleepMind \
  -destination 'platform=iOS Simulator,name=iPhone 15 Pro' \
  -only-testing 'SleepMindTests/CoachingAgentServiceTests/testSendMessageWhenProviderUnavailable'
```

### Manual Testing Checklist

- [ ] Create conversation (verify database save)
- [ ] Send message with provider available (verify AI response)
- [ ] Send message with provider unavailable (verify error)
- [ ] Send multiple messages quickly (verify rate limiting)
- [ ] Simulate network offline (verify error classification)
- [ ] Check logs in Console.app (verify all operations logged)
- [ ] Delete/archive conversations (verify database updates)

---

## Monitoring & Debugging

### Check Provider Health

```swift
let healthy = await service.isAvailable()
print("Provider health: \(healthy ? "✅ OK" : "❌ FAILED")")
```

### Monitor Rate Limiting

```swift
let result = await service.sendMessage(threadId: id, userMessage: msg)
if case .failure(.rateLimited(let retryAfter)) = result {
    print("Rate limited. Retry after: \(retryAfter)s")
}
```

### View Detailed Logs

```bash
# Terminal: real-time log viewing
log stream --predicate 'subsystem=="health.sovv.app"' --level debug

# Filter by category
log stream --predicate 'subsystem=="health.sovv.app" AND category=="CoachingAgent"'

# Export logs for analysis
log collect --output ~/coaching_logs.logarchive
```

---

## Performance Tips

### Reduce Latency

1. **Pre-check availability** outside the hot path:
   ```swift
   // Once at app launch
   let available = await service.isAvailable()
   
   // Then in UI
   if !available {
       showOfflineMessage()
   }
   ```

2. **Batch operations** when possible:
   ```swift
   let threads = await service.listConversations(userId: userId)
   // Use batch fetch instead of individual getConversation() calls
   ```

3. **Cache user context** to avoid rebuilding:
   ```swift
   let cachedContext = UserContext(
       userId: userId,
       fitnessLevel: user.fitnessLevel,
       goals: user.goals
   )
   // Reuse across multiple sendMessage calls
   ```

### Optimize Database

```swift
// Limit fetch results
var descriptor = FetchDescriptor<ConversationThread>(predicate: predicate)
descriptor.fetchLimit = 50  // Don't fetch all conversations
descriptor.sortBy = [SortDescriptor(\.updatedAt, order: .reverse)]
```

---

## Troubleshooting

### "Provider unavailable" on every call

**Cause**: API key not configured or invalid

**Fix**:
```swift
// Check Config.xcconfig has valid ANTHROPIC_API_KEY
// Verify it doesn't start with "YOUR_" or "$("

// Programmatically verify
let provider = ClaudeAPIProvider()
let available = await provider.isAvailable()  // Should be true
```

### "Rate limited" too frequently

**Cause**: Rate limit thresholds too low

**Fix**:
```swift
// Adjust limits (e.g., for beta testing)
let limiter = await RateLimiter(maxPerSecond: 10, maxPerMinute: 120)
let service = CoachingAgentService(
    modelContext: modelContext,
    llmProvider: provider,
    providerType: .claude,
    rateLimiter: limiter
)
```

### Conversation not saving

**Cause**: Database error after LLM response

**Fix**:
```swift
// The service returns success even if DB save fails after AI response
// This prevents data loss if both succeed or only one fails

// Check logs for database errors
log stream --predicate 'category=="CoachingAgent"' --level error
```

### Retry backoff causing long delays

**Cause**: Multiple transient failures triggering retries

**Fix**:
```swift
// Service automatically limits max delay to 10 seconds
// If delays too long for UX, increase maxRequestsPerSecond

let limiter = await RateLimiter(maxPerSecond: 10, maxPerMinute: 90)
// More lenient rate limit = fewer retries
```

---

## Security Considerations

### API Key Protection

✅ **Do**: Store API key in Config.xcconfig (gitignored)  
❌ **Don't**: Commit Config.xcconfig to version control  
❌ **Don't**: Log API keys (logger uses privacy:.public)  
❌ **Don't**: Pass API key in URL parameters  

### Privacy & Logging

- User IDs logged for tracing (privacy: .public)
- Message content NOT logged (security)
- API responses NOT logged (privacy)
- Only metadata (attempt counts, status codes) logged

### Network Security

```swift
// ClaudeAPIProvider uses:
// - HTTPS only (api.anthropic.com)
// - Bearer token auth (Authorization header)
// - Standard URLSession (uses system trust store)
// - 60-second timeout (prevents hanging connections)
```

---

## Summary

The enhanced CoachingAgentService provides:

1. **Reliable**: Retries transient failures automatically
2. **Safe**: Comprehensive error handling & recovery
3. **Observable**: Detailed logging for debugging
4. **Performant**: Rate limiting prevents overload
5. **Testable**: Full test suite with mocks
6. **Documented**: Config guide & inline comments

For questions or issues, check:
- Tests in `CoachingAgentServiceTests.swift`
- Logs via `log stream --predicate 'subsystem=="health.sovv.app"'`
- Error recovery suggestions in `CoachingError.recoverySuggestion`
