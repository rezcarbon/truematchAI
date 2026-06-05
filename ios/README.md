# TrueMatch iOS

The iOS client for **TrueMatch**, an AI-embodied hiring-assessment platform.
TrueMatch scores a candidate two ways — a traditional keyword/ATS match and a
demonstrated-**capability** score — surfaces the gap between them, and (when
warranted) issues a counter-recommendation to advance candidates the keyword
filter would have rejected.

This is a **thin client**: all scoring, narrative generation, trajectory
analysis, and governance evaluation happen on the hosted backend. The app only
renders results, caches them for offline viewing, and manages auth.

- Target: **iOS 17+**, **SwiftUI**, **SwiftData**
- Base API: `https://api.truematch.ai/v1` (Bearer JWT)
- Keychain service: `ai.truematch.app`
- URL scheme: `truematch://`

---

## Architecture

```
TrueMatch/
├── App/                 App entry, configuration, app state, app delegate
├── Core/
│   ├── Networking/      APIClient (actor), endpoints, models, WS, offline queue, NWPathMonitor
│   ├── Auth/            SessionManager (Keychain), SingpassAuthManager, AuthStateManager
│   ├── Persistence/     SwiftData models + LocalStore + SyncEngine
│   └── Notifications/   Push registration + tap routing (assessment-ready)
├── Design/              Theme + reusable components (TM*)
├── Extensions/          String / View / Date helpers
├── Utilities/           Logger, haptics, deep-link routing
├── Features/
│   ├── Onboarding/      Welcome, SignUp, Login
│   ├── ResumeUpload/    Upload flow + ViewModel + DocumentPicker + text/supplementary input
│   ├── Assessment/      Result screen + dual-score, narrative, trajectory, gap, governance views
│   ├── JobMatching/     Positions list (skeleton)
│   ├── Profile/         Profile (skeleton)
│   ├── History/         Past assessments (cached) (skeleton)
│   └── Settings/        Settings + sign out (skeleton)
└── Preview Content/     PreviewData.swift (realistic sample assessment)
```

### Key data flow
1. User picks a resume file (or pastes text) + a job description.
2. `ResumeUploadViewModel` uploads the file (`POST /files/upload`) then creates an
   assessment (`POST /assessments`).
3. `AssessmentResultView` loads the assessment. If it is still `processing`, a
   `WebSocketClient` streams live stage/progress updates until completion.
4. The completed `AssessmentResponse` is cached to SwiftData (`CachedAssessment`)
   for offline viewing in History.

### Governance is display-only
The `Governance` model and `GovernanceStatusView` render coherence / consistency
/ fidelity status, scores, deltas, bias flags, and the audit id **exactly as the
backend returns them**. The client computes no thresholds and makes no
pass/fail decisions. Badge colours are a purely presentational mapping of the
backend status string.

---

## What was ported vs. newly built

### Ported (adapted from an existing internal SwiftUI thin-client)
Infrastructure was reused and re-skinned for TrueMatch. Files were renamed,
the domain models replaced, identifiers rebranded (`ai.truematch.app`,
`truematch://`), and the logger/theme/types renamed to `TrueMatch*` / `TM*`.

- **Core/Networking**: `APIClient` (actor, JWT bearer; added multipart upload),
  `APIEndpoints` (replaced with TrueMatch surface), `APIModels` (replaced with
  assessment/score models), `NetworkMonitor` (as-is), `OfflineQueue`
  (retargeted to assessment creation), `WebSocketClient` (retargeted to
  assessment progress streaming).
- **Core/Auth**: `SessionManager`, `SingpassAuthManager`, `AuthStateManager`
  (added email/password login + signup).
- **Core/Persistence**: `LocalStore`, `SyncEngine`, plus new SwiftData models
  `CachedAssessment`, `CachedProfile`, `ResumeCache`.
- **Core/Notifications**: `PushNotificationManager`, `NotificationHandler`
  (adapted to assessment-ready / decision-update categories).
- **Design**: `TrueMatchTheme`, `TMButton`, `TMCard`, `TMTextField`, `LoadingView`.
- **Extensions/Utilities**: String/View/Date extensions, `TrueMatchLogger`,
  `HapticManager`, `DeepLinkHandler`.
- **App**: `TrueMatchApp`, `AppState`, `AppConfiguration`, `AppDelegate`.

### Newly built for TrueMatch
- Design components: **`TMScoreGauge`** (circular gauge), **`TMDeltaBar`**,
  **`TMBadge`**, **`TMNarrativeBlock`**.
- **Features/Onboarding**: `OnboardingView`, `SignUpView`, `LoginView`.
- **Features/ResumeUpload**: `ResumeUploadView`, `ResumeUploadViewModel`,
  `DocumentPicker`, `ResumeTextInput`, `SupplementaryInfoView`.
- **Features/Assessment**: `AssessmentResultView`, `AssessmentViewModel`,
  `DualScoreView`, `CapabilityNarrativeView`, `TrajectoryView`,
  `GapAnalysisView`, `GovernanceStatusView`.
- **Features/JobMatching · Profile · History · Settings**: skeletons.
- **Preview Content/PreviewData.swift**.

See `PORTING_NOTES.md` for a per-file source/adaptation breakdown.

---

## Building

The `.xcodeproj` is **generated from `project.yml`** (the source of truth) and is
gitignored. The project + Info.plist + asset catalog + localization are wired and
the app **compiles cleanly for the iOS Simulator** (verified with Xcode 26 /
iOS 17 SDK, 0 errors).

### Generate + build

```bash
brew install xcodegen                # if not installed
cd TrueMatch/ios
xcodegen generate                    # produces TrueMatch.xcodeproj from project.yml
open TrueMatch.xcodeproj

# Or build headless (no signing needed):
xcodebuild -project TrueMatch.xcodeproj -scheme TrueMatch \
  -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' \
  build CODE_SIGNING_ALLOWED=NO
```

`xcodegen` synthesizes `Info.plist` from the `info:` block in `project.yml`
(URL scheme `truematch`, `UIBackgroundModes` remote-notification + fetch, and the
`BGTaskSchedulerPermittedIdentifiers` for sync/maintenance — all verified in the
built product). Resources live under `TrueMatch/Resources/`:
`Assets.xcassets` (AppIcon slot + AccentColor), `Localizable.xcstrings`
(EN / ZH-Hans / MS / TA). Push entitlement: `TrueMatch/TrueMatch.entitlements`
(`aps-environment`); add a Team in Xcode signing to run on device.

### Manual setup (alternative)
1. **File → New → Project → iOS App**. Product name `TrueMatch`, interface
   SwiftUI, language Swift, storage **SwiftData**, bundle id `ai.truematch.app`.
2. Delete the auto-generated `TrueMatchApp.swift` / `ContentView.swift`.
3. Drag the `TrueMatch/` source folder into the project ("create groups").
4. Add the `Preview Content` group; mark `PreviewData.swift` as part of the app
   target (it is referenced by debug previews).
5. Set **Deployment Target = iOS 17.0**.
6. Add capabilities: **Push Notifications**, **Background Modes**
   (Remote notifications + Background fetch).
7. Register BGTask identifiers `ai.truematch.app.sync` and
   `ai.truematch.app.maintenance` under `BGTaskSchedulerPermittedIdentifiers`.
8. Add the URL scheme `truematch` (URL Types).
9. Build & run.

> The `.xcodeproj` is regenerated from `project.yml` (and gitignored), so edit
> `project.yml` — not the generated project — for build-setting changes.
