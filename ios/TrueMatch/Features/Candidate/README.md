# Candidate Mode Implementation

Complete iOS implementation of the TrueMatch Candidate Mode with four core features:

## Features Overview

### 1. Assessment Results (`CandidateAssessmentResultsView` + `AssessmentResultsViewModel`)

Displays comprehensive assessment results with multi-signal analysis:

**Components:**
- **Three-Signal Gauges**: Visual representation of Traditional, Semantic, and Capability scores
- **Delta Visualization**: Computed differences between score types showing insights
- **Strengths Section**: Ranked by confidence with evidence links
- **Skill Gaps**: Identified gaps with learning paths
- **Call-to-Action**: "Browse Jobs" button for navigation

**ViewModel Responsibilities:**
- Load assessment data from API (`/candidates/{candidateId}/assessment`)
- Extract and organize scores
- Compute deltas (Capability vs Traditional, Semantic vs Traditional, Capability vs Semantic)
- Track assessment viewing events
- Sort strengths and gaps by confidence

**Key Methods:**
```swift
func loadAssessment() async
private func extractScores() async
private func computeDeltas()
func didTapBrowseJobs()
```

---

### 2. Job Recommendations (`CandidateJobRecommendationsView` + `JobRecommendationsViewModel`)

Interactive swipe-based job browsing experience:

**Components:**
- **Full-Screen Job Cards**: Detailed job information with expandable sections
- **Three-Score Match Display**: Traditional, Semantic, and Capability scores
- **Skills Radar**: Required skills with match percentages
- **Swipe Gestures**: Left to reject, right to save/like
- **Action Menu**: Save, Apply, and Pass options

**ViewModel Responsibilities:**
- Load paginated job recommendations
- Handle swipe gestures (left/right)
- Track saved and rejected jobs
- Persist likes/dislikes to backend
- Load more jobs when running low
- Navigate to job application

**Gesture Handling:**
- Swipe left (> -100 threshold): Reject job → `RejectJobRequest`
- Swipe right (> +100 threshold): Save job → `SaveJobRequest`
- Return to center: Cancel swipe

**Key Methods:**
```swift
func loadJobs() async
func handleSwipe(direction: SwipeDirection) async
func saveCurrentJob() async
func rejectCurrentJob() async
func applyForCurrentJob()
```

**API Endpoints Used:**
- `GET /candidates/{id}/jobs/recommendations?limit=20&offset=0`
- `POST /candidates/{id}/jobs/{jobId}/save`
- `POST /candidates/{id}/jobs/{jobId}/reject`

---

### 3. Career Coach (`CandidateCareerCoachView` + `CareerCoachViewModel`)

Real-time career guidance with WebSocket connection:

**Components:**
- **Chat Interface**: Scrolling message transcript
- **Message Composer**: Input with send button
- **Structured Responses**: Numbered steps, resources, and action items
- **Suggested Follow-ups**: Quick-tap suggestions
- **Connection Status**: Real-time indicator

**ViewModel Responsibilities:**
- Establish WebSocket connection to `/candidate/coach/{sessionId}`
- Send messages via WebSocket
- Receive and parse structured responses
- Track message history
- Manage connection lifecycle
- Extract suggested follow-ups

**Message Types:**
- **User Messages**: Simple text messages
- **Assistant Messages**: May include `StructuredResponse` with:
  - `steps[]`: Numbered action steps with resources
  - `resources[]`: External learning resources
  - `actionItems[]`: Checklist items
  - `nextSteps[]`: Suggested follow-up questions

**Key Methods:**
```swift
func connectWebSocket() async
func send() async
private func receiveMessages()
func clearHistory()
func useSuggestion(_ suggestion: String)
func disconnect()
```

**WebSocket Message Format:**
```json
{
  "type": "message",
  "content": "User message text"
}
```

---

### 4. Application Tracking (`CandidateApplicationTrackingView` + `ApplicationTrackingViewModel`)

Pipeline visualization and application management:

**Components:**
- **Pipeline Visualization**: 5-stage pipeline (Applied → Reviewing → Interviewing → Offer → Closed)
- **Stage-Based Filtering**: Tap stages to filter applications
- **Application Cards**: Summary with latest events and upcoming interviews
- **Detail Modal**: Expanded view with full timeline, interviews, and offer details
- **Timeline View**: Event history with timestamps
- **Interview Prep**: Materials and rescheduling options
- **Offer Management**: Accept/Decline with offer details display

**ViewModel Responsibilities:**
- Fetch applications from backend
- Organize applications by stage
- Track selected application
- Handle offer acceptance/decline
- Manage interview rescheduling tracking
- Sort by recency within stages

**Application States:**
1. **applied**: Initial application submission
2. **reviewing**: Under recruiter review
3. **interviewing**: Interview scheduled or in progress
4. **offer**: Offer received
5. **closed**: Application finalized (accepted/rejected)

**Key Methods:**
```swift
func loadApplications() async
private func organizeByStage()
func selectApplication(_ application: ApplicationStatus)
func getApplicationsForStage(_ stage: String) -> [ApplicationStatus]
func acceptOffer(_ application: ApplicationStatus) async
func declineOffer(_ application: ApplicationStatus) async
func rescheduleInterview(_ session: InterviewSession)
```

**API Endpoints Used:**
- `GET /candidates/{id}/applications`
- `POST /applications/{id}/offer/accept`
- `POST /applications/{id}/offer/decline`

---

## Data Models

### Assessment Related
- `AssessmentScore`: Individual score (Traditional/Semantic/Capability)
- `SkillEvidence`: Skill with proficiency and evidence
- `AssessmentResult`: Complete assessment with all scores and insights
- `LearningPath`: Recommended learning journey for a skill
- `LearningResource`: External resource (course, article, etc.)

### Job Related
- `JobRecommendation`: Complete job listing with match scores
- `SkillMatch`: Skill requirement with match percentage
- `SalaryRange`: Compensation information

### Career Coaching
- `CareerCoachMessage`: Single message in chat
- `StructuredResponse`: Formatted response with steps and resources
- `CoachingStep`: Numbered step with description and resources
- `CoachingResource`: Learning or reference material

### Application Tracking
- `ApplicationStatus`: Application with full pipeline info
- `ApplicationEvent`: Timeline event (applied, reviewed, etc.)
- `InterviewSession`: Interview appointment with prep materials
- `OfferDetails`: Compensation and benefits package

### SwiftData Models (For Offline Support)
- `CachedAssessmentResult`: Persisted assessment
- `CachedAssessmentScore`: Individual cached score
- `CachedSkillEvidence`: Cached skill evidence
- `CachedLearningPath`: Cached learning path

---

## Integration with Main App

### Adding to Tab View

Replace or enhance the existing `CandidateTabs` in `TrueMatchApp.swift`:

```swift
struct CandidateTabs: View {
    var body: some View {
        TabView {
            // New Candidate Mode (integrated)
            CandidateTabView()
                .tabItem { Label("Candidate", systemImage: "briefcase.circle") }
            
            // Existing tabs
            ChatView().tabItem { Label("Assistant", systemImage: "sparkles") }
            // ... other tabs
        }
    }
}
```

Or use `CandidateTabView` as a complete replacement for the candidate workspace.

---

## Accessibility Features

All views include:
- Semantic labels for screen readers
- High contrast colors for readability
- Keyboard navigation support
- VoiceOver-optimized buttons and controls
- Dynamic type support for text
- Proper ARIA labels on interactive elements

---

## Error Handling

Each ViewModel implements:
- Network error capture with user-friendly messages
- Retry mechanisms for failed requests
- Offline queue for critical actions (like saving jobs)
- Error alerts displayed to user

Example:
```swift
@Published var errorMessage: String?

.alert("Error", isPresented: Binding(...)) {
    Button("OK", role: .cancel) { viewModel.errorMessage = nil }
} message: {
    Text(viewModel.errorMessage ?? "")
}
```

---

## Performance Optimizations

### Lazy Loading
- Job recommendations loaded in pages (20 at a time)
- Load more when user gets within 5 cards of end
- Messages loaded on-demand in chat

### Caching
- SwiftData models for offline access
- Assessment results cached after loading
- Application list refreshed on demand

### Animations
- Smooth card transitions with `withAnimation`
- Debounced swipe gestures (0.3s easing)
- Lazy stack rendering for long lists

---

## Testing

Comprehensive test suite (`CandidateModeTests.swift`) includes:

### Unit Tests
- **AssessmentResultsViewModelTests**: Delta computation, score extraction
- **JobRecommendationsViewModelTests**: Swipe handling, job tracking
- **CareerCoachViewModelTests**: Connection management, message validation
- **ApplicationTrackingViewModelTests**: Pipeline organization, stage filtering

### Integration Tests
- Flow from assessment to job browsing
- Application pipeline state transitions
- Message history and connection lifecycle

### Key Test Scenarios
- Delta computation with positive/negative values
- Swipe gesture threshold validation
- WebSocket connection lifecycle
- Application reorganization on status change

Run tests with:
```bash
xcodebuild test -scheme TrueMatch -destination 'platform=iOS Simulator,name=iPhone 15'
```

---

## Architecture Patterns

### MVVM with Combine
- ViewModels use `@MainActor` for UI thread safety
- `@Published` properties for reactive UI updates
- Combine publishers for async operations

### SwiftUI Best Practices
- State management with `@StateObject`, `@State`, `@Environment`
- Reusable component views
- PreviewProvider for each major view
- Gesture recognizers for complex interactions

### Offline Support
- OfflineQueue integration for critical actions
- SwiftData caching for assessment and application data
- Graceful degradation when network unavailable

---

## API Contract

### Request Models
- `GetAssessmentRequest`
- `GetJobRecommendationsRequest`
- `SaveJobRequest`
- `RejectJobRequest`
- `GetApplicationsRequest`

### Response Models
- All models include `Identifiable` for list rendering
- Use snake_case on wire, camelCase in code (via decoder)
- Timestamps as ISO8601 strings

### Error Handling
- HTTP errors mapped to `APIError` enum
- 401 Unauthorized triggers re-authentication flow
- Network errors provide user-friendly messages

---

## Future Enhancements

1. **Interview Preparation**: Video interview simulator
2. **Salary Negotiation**: Insights on offer comparisons
3. **Progress Tracking**: Skill development over time
4. **Networking**: Connection with recruiters and other candidates
5. **Analytics**: Personal insights dashboard
6. **Notifications**: Real-time updates on applications and opportunities

---

## File Structure

```
Features/Candidate/
├── CandidateModels.swift                    # All data models
├── CandidateTabView.swift                   # Tab navigation
├── CandidateAssessmentResultsView.swift     # Assessment UI
├── AssessmentResultsViewModel.swift         # Assessment logic
├── CandidateJobRecommendationsView.swift    # Job browsing UI
├── JobRecommendationsViewModel.swift        # Job logic
├── CandidateCareerCoachView.swift           # Career coach UI
├── CareerCoachViewModel.swift               # Career coach logic
├── CandidateApplicationTrackingView.swift   # Application tracking UI
├── ApplicationTrackingViewModel.swift       # Application logic
├── CandidateModeTests.swift                 # Unit & integration tests
└── README.md                                # This file
```

---

## Support & Maintenance

For issues or questions:
1. Check test files for expected behavior
2. Review API contract in `APIEndpoints.swift`
3. Verify backend endpoints are implemented
4. Check network connectivity and authentication

All ViewModels are thread-safe with `@MainActor` decorator.
All views use TrueMatchTheme for consistent styling.
