# Recruiter Mode Implementation

A comprehensive iOS feature set for TrueMatch recruiters, providing command centre dashboard, Kanban pipeline management, candidate search, and one-tap decision recording.

## Overview

Recruiter Mode enables efficient hiring workflows with:
- **Command Centre**: Dashboard with today's tasks, active positions, candidate queue, agent activity
- **Pipeline**: Kanban board with drag-drop between Screening → Interview → Offer → Hired
- **Search**: Full-text search with filtering by stage and score range
- **Decisions**: One-tap approve/reject/revisit with quick feedback templates
- **Settings**: Recruiter preferences and profile management

## Architecture

### Files Structure

```
Features/Recruiter/
├── RecruiterModels.swift          # Data models & API types
├── RecruiterCommandCentreViewModel.swift
├── RecruiterCommandCentreView.swift
├── RecruiterPipelineViewModel.swift
├── RecruiterPipelineView.swift
├── RecruiterSearchViewModel.swift
├── RecruiterCandidateSearchView.swift
├── RecruiterDecisionViewModel.swift
├── RecruiterDecisionView.swift
├── RecruiterTabView.swift         # Tab navigation (5 tabs)
├── RecruiterViewModelTests.swift  # Unit tests (~20+ tests)
└── RecruiterIntegrationTests.swift # Integration tests
```

### Design Patterns

**@MainActor ViewModels**
All ViewModels are marked with `@MainActor` and use `@Published` properties for reactive UI updates.

```swift
@MainActor
final class RecruiterCommandCentreViewModel: ObservableObject {
    @Published var tasks: [RecruiterTask] = []
    @Published var isLoading = false
    // ...
}
```

**SwiftData Caching**
Offline-first caching via `CachedRecruiterData` model for resilience during network outages.

**Combine Publishers**
Debounced search (0.5s) for efficient API calls; automatic screen layout reflow with animations.

**Error Handling**
User-facing error alerts; detailed logging with `TrueMatchLogger`; graceful degradation with cached data.

## Data Models

### Core Entities

**RecruiterTask** — Approvals, interviews, offers
- Type: approval | interview | offer
- Status: pending | completed | rejected
- Fields: candidateName, positionTitle, dueDate, description

**ActivePosition** — Open roles with fill rates
- Urgency: critical | high | normal | low
- Fields: openCount, fillRate (0-1), activeCount

**PipelineCard** — Candidate in pipeline
- Stage: screening | interview | offer | hired
- Score & delta (score change)
- notesCount for quick reference

**RecruiterSearchResult** — Search result with match %
- Includes candidate score, position, match percentage
- Embeds avatarUrl for async image loading

**DecisionRecord** — Hiring decision audit trail
- Decision: approve | reject | revisit
- Fields: feedback, timestamp, recordedBy

### API Requests/Responses

**RecruiterCommandCentreResponse**
```swift
struct RecruiterCommandCentreResponse: Codable {
    let tasks: [RecruiterTask]
    let positions: [ActivePosition]
    let queueItems: [CandidateQueueItem]
    let activityFeed: [AgentActivityEntry]
}
```

**RecordDecisionRequest**
```swift
struct RecordDecisionRequest: Codable {
    let decision: String // "approve", "reject", "revisit"
    let feedback: String?
    let timestamp: Date
}
```

## Views & Features

### 1. Command Centre (`RecruiterCommandCentreView`)

**Layout**
- Header with refresh button
- Today's Tasks (up to 3, grouped by type: approval/interview/offer)
- Active Positions Carousel (horizontal scroll)
- Work Queue (top 5 candidates with quick actions)
- Activity Feed (last 24 hours)

**Features**
- Color-coded task types (info/warning/success)
- Urgency badges on positions (critical → red, high → orange, etc.)
- Quick "advance candidate" button on each queue item
- Pull-to-refresh from top
- Filtered views: todaysTasks, pendingTasks, criticalPositions, upcomingTasks

**Accessibility**
- VoiceOver labels on all interactive elements
- Semantic HTML in list presentations
- Large touch targets (44x44 min)

### 2. Pipeline (`RecruiterPipelineView`)

**Layout**
- Horizontal scrolling Kanban board (4 columns)
- Column headers with candidate counts
- Pipeline stats bar (screening/interview/offer/hired)
- Pending sync indicator

**Features**
- **Drag & Drop**: Move cards between columns (optimistic update + async sync)
- **Score Delta**: Visual indicator of score change (+/- triangle)
- **Context Menu**: Long-press to move to stage or archive
- **Real-time Updates**: WebSocket ready (future enhancement)
- **Offline Queue**: Failed moves queued for sync
- **Card Selection**: Tap to select, shows border highlight

**Interactions**
```swift
// Drag & drop
await viewModel.moveCard(card, from: .screening, to: .interview)

// Optimistic: moves immediately, reverts on error
// Sync: queued for offline handling
```

### 3. Candidate Search (`RecruiterCandidateSearchView`)

**Layout**
- Search bar (clearable, with leading icon)
- Collapsible filter panel
- Results list with action buttons

**Filters**
- Stage: All | Screening | Interview | Offer | Hired
- Score Range: dual sliders (min/max)
- Clear All button

**Results**
- Avatar, name, email
- Stage badge, match %
- Score with semantic color (green ≥80, orange 60-80, red <60)
- Quick Actions: Review CV | Schedule Interview | Send Offer

**Search Logic**
- Debounced 0.5s (1000ms default)
- Full-text query + stage + score filters
- Limit 50 results per request
- Empty state before first search

### 4. Decision Center (`RecruiterDecisionView`)

**Layout**
- Candidate header (avatar, name, position, score, delta)
- 3 decision buttons (Approve/Reject/Revisit)
- Quick templates (5 per decision type)
- Feedback textarea
- Submit + Prepare Offer buttons

**Decision Templates**
**Approve** (pre-filled):
- "Strong candidate, moving to next stage."
- "Exceeds requirements, recommend interview."
- "Good fit for the role."
- "Meets all qualifications."
- "Highest priority candidate."

**Reject**:
- "Skills mismatch with role requirements."
- "Candidate withdrew application."
- "Better matches available."
- "Experience level doesn't align."
- "Cultural fit concerns."

**Revisit**:
- "Need more information before deciding."
- "Hold for future positions."
- "Promising but timeline doesn't align."
- "Waitlist for similar roles."

**Features**
- **Candidate Selector Sheet**: Modal to pick candidate from queue
- **Template Selection**: Auto-fills feedback
- **Custom Feedback**: Override template
- **Success Overlay**: Confirmation + 1s auto-clear
- **Offer Preparation**: Quick path to offer creation (Approve only)

### 5. Tab Navigation (`RecruiterTabView`)

**Tabs** (5 total):
1. **Command Centre** (square.grid.2x2)
2. **Pipeline** (rectangle.grid.1x2)
3. **Search** (magnifyingglass)
4. **Decisions** (hand.thumbsup)
5. **Settings** (gear)

**Tab Bar Styling**
- TrueMatchTheme.colors.primary for active tint
- Persistent across navigation

## API Integration

### Endpoints Added to APIEndpoints.swift

```swift
// Command Centre
static var recruiterCommandCentre: APIEndpoint

// Pipeline
static var recruiterPipeline: APIEndpoint

// Search
static func recruiterSearchCandidates(_ request: SearchCandidatesRequest) -> APIEndpoint

// Task Management
static func recruiterCompleteTask(taskId: String) -> APIEndpoint
static func recruiterAdvanceCandidate(candidateId: String) -> APIEndpoint

// Pipeline Drag-Drop
static func recruiterMoveCandidate(candidateId: String, stage: String) -> APIEndpoint

// Decisions
static func recruiterRecordDecision(candidateId: String, _ request: RecordDecisionRequest) -> APIEndpoint
```

### Request/Response Flow

**Example: Record Decision**
```
PUT /api/v1/recruiter/candidates/{candidateId}/decision
{
  "decision": "approve",
  "feedback": "Strong candidate...",
  "timestamp": "2025-07-08T10:30:00Z"
}
→ 200 OK (success state)
```

**Offline Sync**
Failed requests are queued in `OfflineQueueManager` and retried when network resumes.

## Styling

### TrueMatchTheme Integration

All views use `@Environment(\.trueMatchTheme)` for:
- **Colors**: primary, secondary, accent, success, warning, error
- **Typography**: display, title, headline, body, caption, chip
- **Spacing**: xxxs (4) → xxl (48)
- **Corner Radii**: xs (6) → lg (20)
- **Shadows**: subtle, medium, strong
- **Animations**: standard, quick, slow

### Example: Custom Card Styling
```swift
VStack { /* content */ }
    .tmCard()  // Applies padding, background, shadow, border radius
```

### Adaptive Colors
```swift
Color.tmTextPrimary    // Adapts to light/dark mode
Color.tmBackground    // Surface color
Color.tmTextSecondary  // 70% opacity white in dark
```

## Accessibility

### VoiceOver Support
- All interactive elements have `.accessibilityLabel()`
- Semantic roles (button, image, list)
- Non-decorative images labeled

**Examples**:
```swift
Button { /* ... */ }
    .accessibilityLabel("Complete task: \(task.candidateName)")
```

### Large Touch Targets
- Minimum 44×44 pt for all buttons
- Adequate spacing between interactive elements (8+ pt)

### Dark Mode
- All colors use adaptive strategies
- Contrast ratios meet WCAG AA (4.5:1+)
- Skeleton screens visible in both modes

## Testing

### Unit Tests (20+ tests in RecruiterViewModelTests.swift)

**Command Centre**
- `testTodaysTasksFiltering` — Calendar-based filtering
- `testPendingTasksFiltering` — Status filtering
- `testCriticalPositionsFiltering` — Urgency filtering
- `testUpcomingTasksFiltering` — 7-day window
- `testRecentActivityFiltering` — 24h window

**Pipeline**
- `testOrganizePipeline` — Card distribution across stages
- `testPipelineStats` — Count aggregation
- `testMoveCard` — Drag-drop validation (future)

**Search**
- `testInitialization` — Default state
- `testClearSearch` — Reset filters
- `testDebounce` — Search delay (future)

**Decision**
- `testSelectCandidate` — Candidate selection
- `testSelectTemplate` — Template auto-fill
- `testAvailableTemplates` — Decision-specific templates
- `testCanSubmit` — Form validation

### Integration Tests (RecruiterIntegrationTests.swift)

**Encoding/Decoding**
- `testTaskEncoding` — Snake_case + ISO8601 dates
- `testPositionEncoding` — Enum coding
- `testPipelineCardEncoding` — Delta field handling
- `testDecisionRecordEncoding` — Nested objects

**API Response Models**
- `testLoadCommandCentreData` — Mock response structure
- `testRecruiterPipelineResponse` — Card organization
- `testSearchResultsResponse` — Pagination + total count

**Model Enums**
- `testPipelineStageAllCases` — 4 stages present
- `testUrgencyRawValues` — Correct string mappings

### Running Tests
```bash
# Unit tests only
xcodebuild test -scheme TrueMatch -testPlan RecruiterTests

# Full suite
xcodebuild test -scheme TrueMatch

# With coverage
xcodebuild test -scheme TrueMatch -enableCodeCoverage YES
```

## Offline-First Caching

### SwiftData Model
```swift
@Model
final class CachedRecruiterData {
    var dataType: String  // "tasks", "positions", "queue", "activity", "pipeline"
    var resourceId: String?
    var jsonData: String?
    var lastFetched: Date
    var expiresAt: Date  // 1 hour TTL
}
```

### Caching Strategy
1. **Write**: Save response JSON after successful API call
2. **Expire**: Mark stale after 1 hour
3. **Read**: Load from cache on network error
4. **Sync**: Queue offline actions in `OfflineQueueManager`

### Example: Load with Fallback
```swift
do {
    let response = try await api.request(endpoint: .recruiterCommandCentre, ...)
    await cacheData(response)
    self.tasks = response.tasks
} catch {
    await loadFromCache()
    self.errorMessage = "Using cached data."
}
```

## Future Enhancements

1. **Real-time WebSocket Updates**: Live pipeline sync across recruiters
2. **Bulk Actions**: Select multiple candidates, batch move/decide
3. **Analytics**: Recruiter performance metrics, time-to-hire trends
4. **Offer Generation**: AI-powered offer template suggestions
5. **Candidate Notes**: Rich text notes per candidate
6. **Interview Scheduling**: Calendar integration for scheduling
7. **Push Notifications**: Task reminders, pipeline updates
8. **Offline Mode**: Full app functionality without network

## Troubleshooting

### Common Issues

**Q: Drag-drop not syncing**
A: Check network, verify APIClient error handling, inspect offline queue.

**Q: Search results empty**
A: Verify API endpoint, check request payload, inspect `SearchCandidatesRequest`.

**Q: Stale cached data**
A: Check TTL in `CachedRecruiterData.expiresAt`, clear cache manually.

**Q: VoiceOver missing labels**
A: Grep for interactive elements without `.accessibilityLabel()`.

### Logging

Enable detailed logging:
```swift
TrueMatchLogger.log(.debug, "Recruiter: custom message")
```

Check logs:
```
Xcode → Scheme → Edit → Pre-actions → Run Script:
  export OS_LOG_DEBUG=1
```

## References

- **Design System**: `TrueMatchTheme.swift`
- **Networking**: `APIClient.swift`, `APIEndpoints.swift`
- **Persistence**: `LocalStore.swift`, `CachedRecruiterData`
- **Similar Feature**: `Features/Chat/ChatViewModel.swift` (reference pattern)
