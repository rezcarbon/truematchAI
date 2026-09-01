# Porting Notes

Each TrueMatch file below lists its source (an internal SwiftUI thin-client app)
and an approximate **% adapted** — how much of the file was rewritten vs. carried
over structurally. "Source: NEW" means written from scratch for TrueMatch.

All ported files had: file headers neutralised to `TrueMatch`, identifiers
rebranded (`ai.truematch.app`, `truematch://`, `api.truematch.ai`), logger/theme
types renamed (`*Logger → TrueMatchLogger`, `Shanti*/JARVIS* → TrueMatch*/TM*`),
and **all patent / IP references stripped**. None of the prohibited terms appear
anywhere in the output (verified by scan).

| File | Source file | % adapted |
|------|-------------|-----------|
| **App** | | |
| `App/AppConfiguration.swift` | `App/AppConfiguration.swift` | 40% (URLs, scheme, BG ids, storage keys) |
| `App/AppState.swift` | `App/AppState.swift` | 45% (agent→assessment, removed language enum) |
| `App/AppDelegate.swift` | `App/AppDelegate.swift` | 35% (removed health/maintenance BGTask wiring) |
| `App/TrueMatchApp.swift` | `App/CommunityShantiApp.swift` | 60% (new schema, tabs, onOpenURL, removed accessibility) |
| **Core/Networking** | | |
| `Core/Networking/APIClient.swift` | `Core/Networking/APIClient.swift` | 20% (added multipart `upload`; otherwise as-is) |
| `Core/Networking/APIEndpoints.swift` | `Core/Networking/APIEndpoints.swift` | 80% (full TrueMatch endpoint surface) |
| `Core/Networking/APIModels.swift` | `Core/Networking/APIModels.swift` | 90% (assessment/score/governance models) |
| `Core/Networking/NetworkMonitor.swift` | `Core/Networking/NetworkMonitor.swift` | 5% (queue label only) |
| `Core/Networking/OfflineQueue.swift` | `Core/Networking/OfflineQueue.swift` | 35% (retargeted to assessment creation) |
| `Core/Networking/WebSocketClient.swift` | `Core/Networking/WebSocketClient.swift` | 45% (assessment progress events; dropped chat/governance-check events) |
| **Core/Auth** | | |
| `Core/Auth/SessionManager.swift` | `Core/Auth/SessionManager.swift` | 10% (keychain service rename) |
| `Core/Auth/SingpassAuthManager.swift` | `Core/Auth/SingpassAuthManager.swift` | 15% (rebrand, added invalidCredentials error) |
| `Core/Auth/AuthState.swift` | `Core/Auth/AuthState.swift` | 45% (added email/password login + signup, deleteSession) |
| **Core/Persistence** | | |
| `Core/Persistence/CachedAssessment.swift` | `Core/Persistence/CachedMessage.swift` | 85% (new domain model + JSON blob accessor) |
| `Core/Persistence/CachedProfile.swift` | `Core/Persistence/CachedAgentConfig.swift` | 85% (new domain model) |
| `Core/Persistence/ResumeCache.swift` | `Core/Persistence/CachedKnowledge.swift` | 85% (new domain model) |
| `Core/Persistence/LocalStore.swift` | `Core/Persistence/LocalStore.swift` | 70% (assessment/profile/resume upsert + prune) |
| `Core/Persistence/SyncEngine.swift` | `Core/Persistence/SyncEngine.swift` | 55% (assessment + profile sync) |
| **Core/Notifications** | | |
| `Core/Notifications/PushNotificationManager.swift` | `Core/Notifications/PushNotificationManager.swift` | 40% (assessment-ready/decision categories, no agent id) |
| `Core/Notifications/NotificationHandler.swift` | `Core/Notifications/NotificationHandler.swift` | 55% (assessment routing, dropped reminder/reorder logic) |
| **Design** | | |
| `Design/TrueMatchTheme.swift` | `Design/JARVISTheme.swift` | 35% (rebrand, score/governance colours, programmatic adaptive colours) |
| `Design/Components/TMButton.swift` | `Design/Components/JARVISButton.swift` | 10% (rename) |
| `Design/Components/TMCard.swift` | `Design/Components/JARVISCard.swift` | 20% (rename, trimmed footer) |
| `Design/Components/TMTextField.swift` | `Design/Components/JARVISTextField.swift` | 20% (rename, added secure field) |
| `Design/Components/LoadingView.swift` | `Design/Components/LoadingView.swift` | 20% (rename, copy) |
| `Design/Components/TMScoreGauge.swift` | NEW | 100% |
| `Design/Components/TMDeltaBar.swift` | NEW | 100% |
| `Design/Components/TMBadge.swift` | NEW | 100% |
| `Design/Components/TMNarrativeBlock.swift` | NEW | 100% |
| **Extensions / Utilities** | | |
| `Extensions/String+Extensions.swift` | `Extensions/String+Extensions.swift` | 5% (header) |
| `Extensions/View+Extensions.swift` | `Extensions/View+Extensions.swift` | 5% (header) |
| `Extensions/Date+Extensions.swift` | `Extensions/Date+Extensions.swift` | 10% (chatTimestamp→shortTimestamp) |
| `Utilities/TrueMatchLogger.swift` | `Utilities/JARVISLogger.swift` | 10% (rename, subsystem) |
| `Utilities/HapticManager.swift` | `Utilities/HapticManager.swift` | 15% (semantic helper rename) |
| `Utilities/DeepLinkHandler.swift` | `Utilities/DeepLinkHandler.swift` | 45% (assessment/position deep links) |
| **Features (NEW)** | | |
| `Features/Onboarding/OnboardingView.swift` | NEW | 100% |
| `Features/Onboarding/SignUpView.swift` | NEW | 100% |
| `Features/Onboarding/LoginView.swift` | NEW | 100% |
| `Features/ResumeUpload/ResumeUploadView.swift` | NEW | 100% |
| `Features/ResumeUpload/ResumeUploadViewModel.swift` | NEW | 100% |
| `Features/ResumeUpload/DocumentPicker.swift` | NEW | 100% |
| `Features/ResumeUpload/ResumeTextInput.swift` | NEW | 100% |
| `Features/ResumeUpload/SupplementaryInfoView.swift` | NEW | 100% |
| `Features/Assessment/AssessmentResultView.swift` | NEW | 100% |
| `Features/Assessment/AssessmentViewModel.swift` | NEW | 100% |
| `Features/Assessment/DualScoreView.swift` | NEW | 100% |
| `Features/Assessment/CapabilityNarrativeView.swift` | NEW | 100% |
| `Features/Assessment/TrajectoryView.swift` | NEW | 100% |
| `Features/Assessment/GapAnalysisView.swift` | NEW | 100% |
| `Features/Assessment/GovernanceStatusView.swift` | NEW (display-only) | 100% |
| `Features/JobMatching/JobMatchingView.swift` | NEW (skeleton) | 100% |
| `Features/Profile/ProfileView.swift` | NEW (skeleton) | 100% |
| `Features/History/HistoryView.swift` | NEW (skeleton) | 100% |
| `Features/Settings/SettingsView.swift` | NEW (skeleton) | 100% |
| `Preview Content/PreviewData.swift` | NEW | 100% |

## IP-safety verification
A scan of all `.swift` sources for the prohibited terms
(`kuramoto`, `lipschitz`, `tfnp`, `patent`, `physiological`, patent numbers,
`C-0x` claim ids, `PBM`, `PAE`, `embodiment`, `CommunityShanti`,
`Digital Court`, `JARVIS`) returned **zero matches**. `Singpass` is retained
only as the name of the third-party OAuth identity provider used by the
`/auth/singpass` endpoints — it carries no patent linkage.

Governance is strictly display-only: `GovernanceStatusView` and the `Governance`
model contain no threshold constants and no pass/fail computation.
