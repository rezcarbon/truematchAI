# TrueMatch Component Library & Theme System

Comprehensive iOS SwiftUI component library and extended theme system for TrueMatch, including data visualization components, decision surfaces, and offline queue management.

## Overview

The TrueMatch design system consists of:

1. **TrueMatchTheme** - Base theme with colors, typography, spacing
2. **TrueMatchThemeExtended** - Extended theme with semantic colors, layout patterns, and component tokens
3. **Custom Components** - Reusable UI components for specific use cases
4. **Offline Queue System** - Full SwiftData-based offline queue manager

---

## Extended Theme (TrueMatchThemeExtended.swift)

### Semantic Decision Colors

Use these colors for hiring/matching decisions:

```swift
@Environment(\.tmColors) var colors

// Positive decision
colors.decisionPositive  // #38A169 (green)

// Negative decision
colors.decisionNegative  // #E53E3E (red)

// Neutral decision
colors.decisionNeutral   // #A0AEC0 (gray)

// Requires escalation
colors.decisionEscalation // #D69E2E (amber)
```

### Skill Assessment Colors

Color scheme for proficiency levels (0-100%):

```swift
colors.skillMastery      // #22863A (80-100%)
colors.skillStrong       // #38A169 (60-79%)
colors.skillModerate     // #D69E2E (40-59%)
colors.skillDeveloping   // #E2A76F (20-39%)
colors.skillFoundational // #E53E3E (0-19%)
```

### Gradient Sets

Pre-built gradients for common patterns:

```swift
// Positive progression
colors.gradientPositive

// Warning/risk
colors.gradientWarning

// Critical issues
colors.gradientError

// Skill spectrum (foundational → mastery)
colors.gradientSkillSpectrum
```

### Extended Typography

Additional font scales beyond base theme:

```swift
@Environment(\.trueMatchTheme) var theme

// Extra-large display
Text("87").font(theme.typography.displayLarge)

// Monospaced metrics
Text("Score: 92").font(theme.typography.monospacedMetric)

// Larger body text
Text(description).font(theme.typography.bodyLarge)

// Small helper text
Text("Last updated").font(theme.typography.helper)
```

### Layout Patterns

Pre-defined padding patterns for consistency:

```swift
// Standard card padding
VStack { /* content */ }
    .padding(TMLayoutPattern.cardPadding)

// Modal/full-sheet padding
VStack { /* content */ }
    .padding(TMLayoutPattern.modalPadding)

// Compact list item
HStack { /* content */ }
    .padding(TMLayoutPattern.compactListPadding)

// Dense grid item
VStack { /* content */ }
    .padding(TMLayoutPattern.gridItemPadding)
```

### Component Tokens

Tokens for specific component sizing and behavior:

```swift
// Radar chart
TMComponentTokens.Radar.axisStrokeWidth
TMComponentTokens.Radar.gridStrokeWidth
TMComponentTokens.Radar.dataPointRadius
TMComponentTokens.Radar.gridLevelCount
TMComponentTokens.Radar.animationDuration

// Decision badge
TMComponentTokens.DecisionBadge.cornerRadius
TMComponentTokens.DecisionBadge.padding
TMComponentTokens.DecisionBadge.iconSize
TMComponentTokens.DecisionBadge.minWidth

// Score gauge
TMComponentTokens.Gauge.minSize
TMComponentTokens.Gauge.maxSize
TMComponentTokens.Gauge.defaultLineWidth
TMComponentTokens.Gauge.animationDelay
```

### Theme-aware Modifiers

Apply consistent styling to surfaces:

```swift
// Elevated decision surface
VStack { /* content */ }
    .tmDecisionSurface()

// Data visualization styling
ZStack { /* chart */ }
    .tmDataVisualization()

// Compact list item
HStack { /* item */ }
    .tmCompactList()

// Monospaced metric styling
Text("92")
    .tmMonospacedMetric(theme)
```

---

## Custom Components

### TMScoreGauge

Circular gauge for displaying 0–100 scores.

**Usage:**

```swift
TMScoreGauge(
    score: 87,
    label: "Capability Score",
    tint: theme.colors.capability,
    size: 140,
    lineWidth: 14
)
```

**Parameters:**
- `score: Double` - Score on 0–100 scale
- `label: String?` - Optional label below gauge
- `tint: Color` - Gauge color
- `size: CGFloat` - Gauge diameter (default: 140)
- `lineWidth: CGFloat` - Stroke width (default: 14)

**Animation:** Animates in on appearance using theme's slow animation curve.

---

### TMDeltaBar

Horizontal bar visualizing the gap between two scores.

**Usage:**

```swift
TMDeltaBar(
    traditionalScore: 42,
    capabilityScore: 87
)
```

**Features:**
- Automatic color coding (green for positive delta, red for negative)
- Dual markers showing both score positions
- Legend with exact values
- Interactive delta visualization

**Parameters:**
- `traditionalScore: Double` - First score (0–100)
- `capabilityScore: Double` - Second score (0–100)
- `height: CGFloat` - Bar height (default: 28)

---

### TMSkillRadar (NEW)

Spider/radar chart for skill proficiency visualization across multiple dimensions.

**Usage:**

```swift
let dimensions = [
    SkillDimension(id: "python", label: "Python", value: 85, target: 80, category: .technical),
    SkillDimension(id: "leadership", label: "Leadership", value: 78, category: .behavioral),
    SkillDimension(id: "domain", label: "Domain Knowledge", value: 65, category: .domain),
]

TMSkillRadar(
    dimensions: dimensions,
    size: 240,
    showLegend: true,
    animationDuration: 0.6,
    showGrid: true,
    gridLevels: 5
)
```

**Features:**
- Multi-dimensional skill visualization
- Optional target values for comparison
- Skill category color coding
- Animated on appearance
- Grid and axis visualization
- Optional legend with values

**SkillDimension Properties:**
```swift
struct SkillDimension: Identifiable, Equatable {
    let id: String
    let label: String
    let value: Double           // 0–100
    let target: Double? = nil   // Optional comparison
    let category: SkillCategory = .technical
    
    enum SkillCategory {
        case technical   // Primary color
        case behavioral  // Secondary color
        case domain      // Accent color
        case foundational // Traditional color
    }
}
```

**Parameters:**
- `dimensions: [SkillDimension]` - Array of skill data
- `size: CGFloat` - Radar diameter (default: 240)
- `showLegend: Bool` - Display legend below chart (default: true)
- `animationDuration: Double` - Animation time (default: 0.6)
- `showGrid: Bool` - Display grid and axes (default: true)
- `gridLevels: Int` - Number of grid circles (default: 5)

---

### TMDecisionBadge (NEW)

Prominent badge component for hiring/matching decisions with confidence indicators.

**Usage:**

```swift
// Recommended decision
TMDecisionBadge(
    decision: .recommended(confidence: 92),
    size: .regular,
    showConfidence: true
)

// Counter-recommended with reason
TMDecisionBadge(
    decision: .counterRecommended(reason: "Skill mismatch in Python"),
    actionLabel: "View Details",
    onAction: { /* handle action */ }
)

// Escalated decision
TMDecisionBadge(
    decision: .escalated(priority: .high),
    actionLabel: "Escalate",
    onAction: { /* escalate */ }
)

// Neutral assessment
TMDecisionBadge(
    decision: .neutral(reason: "Insufficient information"),
    size: .compact
)

// Pending review
TMDecisionBadge(
    decision: .pending,
    size: .large
)
```

**Decision Types:**

```swift
enum TMDecision {
    case recommended(confidence: Double)    // 0–100
    case counterRecommended(reason: String = "")
    case pending
    case escalated(priority: EscalationPriority = .medium)
    case neutral(reason: String = "")
    
    enum EscalationPriority {
        case low       // Blue info icon
        case medium    // Amber warning icon
        case high      // Red error icon
        case critical  // Red filled error icon
    }
}
```

**Features:**
- Automatic color coding based on decision type
- Confidence percentage indicator with circular progress
- Optional action button
- Responsive sizing (compact, regular, large)
- Accessibility support

**Parameters:**
- `decision: TMDecision` - Decision to display
- `size: TMDecisionBadgeSize` - Badge size (.compact, .regular, .large)
- `showConfidence: Bool` - Display confidence indicator (default: true)
- `showIcon: Bool` - Display decision icon (default: true)
- `actionLabel: String?` - Optional action button label
- `onAction: (() -> Void)?` - Action handler

**Size Variants:**

| Size | Label Font | Icon Size |
|------|-----------|-----------|
| compact | caption (13) | 12 |
| regular | headline (17) | 16 |
| large | title (22) | 24 |

---

## Offline Queue System (OfflineQueueManagerExtended.swift)

Comprehensive offline-first data synchronization with conflict resolution and batch operations.

### SwiftData Models

#### OfflineQueueItem

Represents a single offline operation:

```swift
@Model
final class OfflineQueueItem {
    var id: String                          // Unique identifier
    var actionType: String                  // "create_assessment", etc.
    var resourceId: String?                 // For grouping related actions
    var resourceType: String?               // "assessment", "profile", etc.
    var payload: String                     // JSON-encoded payload
    var createdAt: Date
    var enqueuedAt: Date
    var updatedAt: Date
    var priority: QueuePriority             // critical, high, normal, low
    var retryCount: Int
    var maxRetries: Int
    var status: QueueItemStatus             // pending, processing, completed, failed, conflict, paused
    var lastError: String?
    var lastErrorTimestamp: Date?
    var estimatedSizeBytes: Int
    var dependencies: [String]              // IDs of items that must complete first
    var conflicts: [SyncConflict]           // Any conflicts during sync
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
    case critical  // Process first
    case high      // High priority
    case normal    // Standard
    case low       // Background
}
```

#### SyncState

Tracks overall synchronization state:

```swift
@Model
final class SyncState {
    var id: String              // Always "sync_state"
    var lastSyncTime: Date?
    var lastSuccessfulSyncTime: Date?
    var isSyncing: Bool
    var pendingCount: Int
    var failedCount: Int
    var syncConflictCount: Int
    var lastSyncError: String?
    var networkQuality: NetworkQualityLevel
}

enum NetworkQualityLevel: String, Codable {
    case unknown
    case poor
    case fair
    case good
    case excellent
}
```

#### SyncConflict

Represents a data synchronization conflict:

```swift
@Model
final class SyncConflict {
    var id: String
    var queueItem: OfflineQueueItem?        // Associated queue item
    var conflictType: ConflictType
    var localVersion: String                // JSON snapshot
    var remoteVersion: String               // JSON snapshot
    var resolvedVersion: String?            // After resolution
    var createdAt: Date
    var resolvedAt: Date?
    var resolutionStrategy: ResolutionStrategy
}

enum ConflictType: String, Codable {
    case versionMismatch
    case fieldDivergence
    case deletionConflict
    case constraintViolation
    case dataIntegrity
}

enum ResolutionStrategy: String, Codable {
    case manual
    case automatic
    case localWins
    case remoteWins
    case merge
}
```

#### BatchOperation

Tracks batch operations:

```swift
@Model
final class BatchOperation {
    var id: String
    var operationType: String               // "assess_multiple", etc.
    var status: BatchStatus
    var createdAt: Date
    var startedAt: Date?
    var completedAt: Date?
    var totalItems: Int
    var completedItems: Int
    var failedItems: Int
    var estimatedTimeRemainingSeconds: Int?
    var progress: Double                    // 0.0–1.0
    var queueItems: [OfflineQueueItem]
}

enum BatchStatus: String, Codable {
    case pending
    case inProgress
    case completed
    case partiallyCompleted
    case failed
    case cancelled
}
```

### Manager Usage

#### Setup

```swift
@Environment(\.modelContext) var modelContext

func setupOfflineQueue() {
    let manager = OfflineQueueManagerExtended.shared
    manager.configure(with: modelContext)
}
```

#### Enqueue Single Action

```swift
let manager = OfflineQueueManagerExtended.shared

let payload = try JSONEncoder().encode([
    "fileId": "file-123",
    "supplementary": "Additional info"
])
let payloadString = String(data: payload, encoding: .utf8) ?? ""

manager.enqueue(
    actionType: "create_assessment",
    resourceId: "file-123",
    resourceType: "assessment",
    payload: payloadString,
    priority: .high,
    in: modelContext
)
```

#### Enqueue Batch Operation

```swift
let batchItems: [(actionType: String, resourceId: String?, payload: String)] = [
    ("create_assessment", "file-1", "{...}"),
    ("create_assessment", "file-2", "{...}"),
    ("create_assessment", "file-3", "{...}"),
]

let batchId = manager.enqueueBatch(
    operationType: "assess_multiple",
    items: batchItems,
    in: modelContext
)
```

#### Process Pending Items

```swift
// Flush all pending items
await manager.flush(in: modelContext)

// Fetch current state
manager.fetchQueueItems(in: modelContext)
print("Pending: \(manager.pendingCount(in: modelContext))")
print("Failed: \(manager.failedCount(in: modelContext))")
```

#### Retry Failed Items

```swift
await manager.retryFailed(in: modelContext)
```

#### Resolve Conflicts

```swift
guard let conflict = manager.conflicts.first else { return }

// Automatic resolution
await manager.resolveConflict(
    conflict,
    using: .localWins,  // or .remoteWins, .merge, etc.
    in: modelContext
)

// Fetch updated conflicts
manager.fetchConflicts(in: modelContext)
```

#### Cleanup

```swift
// Remove completed items
manager.removeCompleted(in: modelContext)

// Remove items older than 30 days
manager.removeExpired(olderThanDays: 30, in: modelContext)
```

### ObservableObject Properties

Monitor queue state reactively:

```swift
@StateObject private var queueManager = OfflineQueueManagerExtended.shared

VStack {
    Text("Pending: \(queueManager.queueItems.filter { $0.status == .pending }.count)")
    Text("Conflicts: \(queueManager.conflicts.count)")
    Text("Network Quality: \(queueManager.networkQuality.rawValue)")
}
.onAppear {
    queueManager.configure(with: modelContext)
}
```

### Integration with AppState

```swift
@MainActor
class AppState: ObservableObject {
    @StateObject private var offlineQueue = OfflineQueueManagerExtended.shared
    
    func setup(with context: ModelContext) {
        offlineQueue.configure(with: context)
        
        // Listen for connectivity changes
        Task {
            while true {
                try await Task.sleep(seconds: 30)
                await offlineQueue.flush(in: context)
            }
        }
    }
}
```

---

## Integration Examples

### Decision Surface View

```swift
struct DecisionSurfaceView: View {
    @Environment(\.trueMatchTheme) var theme
    let decision: TMDecision
    let skills: [SkillDimension]
    
    var body: some View {
        VStack(spacing: theme.spacing.lg) {
            // Decision badge
            TMDecisionBadge(
                decision: decision,
                size: .large,
                actionLabel: "Review",
                onAction: { /* navigate */ }
            )
            
            // Skill radar
            TMSkillRadar(
                dimensions: skills,
                size: 200,
                showLegend: true
            )
            
            // Additional details
            VStack { /* details */ }
                .tmDataVisualization()
        }
        .tmDecisionSurface()
    }
}
```

### Queue Monitor View

```swift
struct OfflineQueueMonitorView: View {
    @StateObject var queueManager = OfflineQueueManagerExtended.shared
    @Environment(\.modelContext) var modelContext
    
    var body: some View {
        List {
            Section("Sync Status") {
                HStack {
                    Text("Pending")
                    Spacer()
                    Text("\(queueManager.pendingCount(in: modelContext))")
                        .monospacedDigit()
                }
                
                HStack {
                    Text("Failed")
                    Spacer()
                    Text("\(queueManager.failedCount(in: modelContext))")
                        .monospacedDigit()
                }
                
                HStack {
                    Text("Conflicts")
                    Spacer()
                    Text("\(queueManager.conflicts.count)")
                        .monospacedDigit()
                }
            }
            
            Section("Queue Items") {
                ForEach(queueManager.queueItems) { item in
                    HStack {
                        Text(item.actionType)
                        Spacer()
                        TMBadge(
                            text: item.status.rawValue,
                            kind: statusToBadgeKind(item.status)
                        )
                    }
                }
            }
        }
    }
}
```

---

## Best Practices

1. **Color Usage**
   - Use semantic decision colors for hiring outcomes
   - Use skill colors for proficiency visualization
   - Use gradients for spectrum data (ranges, progressions)

2. **Component Sizing**
   - Use TMComponentTokens for consistent sizing
   - Scale components based on data density
   - Respect minimum sizes for touch targets (44pt)

3. **Offline Queue**
   - Always set maxRetries appropriately for action type
   - Use priorities to ensure critical actions sync first
   - Set dependencies for related operations
   - Monitor network quality before flushing

4. **Theme Access**
   - Access theme via `@Environment(\.trueMatchTheme)`
   - Use extended theme properties from TrueMatchThemeExtended
   - Apply modifiers instead of manual padding/styling

5. **Data Visualization**
   - Use TMSkillRadar for 4–8 dimensions max
   - Always provide meaningful axis labels
   - Consider accessibility (color + icons)
   - Test with actual data ranges

---

## File Locations

```
TrueMatch/
├── Design/
│   ├── TrueMatchTheme.swift
│   ├── TrueMatchThemeExtended.swift
│   ├── COMPONENT_LIBRARY.md (this file)
│   └── Components/
│       ├── TMScoreGauge.swift
│       ├── TMDeltaBar.swift
│       ├── TMSkillRadar.swift
│       ├── TMDecisionBadge.swift
│       ├── TMBadge.swift
│       └── ... other components
└── Core/Networking/
    ├── OfflineQueue.swift
    └── OfflineQueueManagerExtended.swift
```

---

## Version History

- **v2.0** - Added TMSkillRadar, TMDecisionBadge, TrueMatchThemeExtended, OfflineQueueManagerExtended
- **v1.0** - Initial TrueMatchTheme, basic components (TMScoreGauge, TMDeltaBar, etc.)
