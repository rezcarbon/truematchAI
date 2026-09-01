# SleepMind v1 Scope Audit — Complete Findings

**Date**: 2026-07-23  
**Audited**: ~/Documents/codebase/SleepMind  
**Scope Source**: SCOPE.md + CLAUDE.md

---

## Executive Summary

### Key Findings
- **18 Feature directories**: 13 fully in-scope, 4 out-of-scope, 1 mixed
- **127 Service files**: ~30 in-scope, ~97 out-of-scope (many DCourtKit inheritance/Phase 2+)
- **Out-of-Scope Views to Remove**: Community/, Shop/, Search/, Coaching/ (4 directories)
- **Out-of-Scope Services to Remove**: ~80 files (Multimodal, Voice, IPFS, Commerce, Legacy AI, etc.)
- **Code Ready for Curation**: Intelligence/ fully supports v1, Settings/ needs minor audits

---

## v1 Scope Definition (from SCOPE.md)

### ✓ MUST INCLUDE IN v1
**A. Onboarding** (4 screens)
- Welcome / value prop
- Firebase sign-in (Apple/Google/email)
- HealthKit permissions (sleep, HRV, RHR, workouts, active energy)
- Hyrox profile setup (race date, station PBs, training frequency)

**B. Training Logging** (6 screens)
- Today's session card
- Workout builder (warmup/blocks/cooldown, 8 Hyrox stations, run intervals, strength)
- In-workout player (timer, set tracker, station UI)
- Apple Watch companion (minimal: start/stop, lap, HR view)
- Post-workout summary (RPE, notes, auto HR/calories)
- Training history (calendar + list)

**C. Nutrition Logging** (3 screens)
- Today's nutrition (meals, water, protein)
- Add meal (barcode scan via Open Food Facts + manual entry + recents)
- Macro targets

**D. Sleep & Recovery** (2 screens)
- Last night (sleep stages, N3 duration, HRV, RHR)
- Recovery trend (7-day / 30-day)

**E. Morning Briefing** (1 hero screen)
- Readiness score (0–100)
- One-sentence recommendation
- "Why" card (3 bullets: sleep, training load, nutrition)
- Race countdown card
- "Start suggested session" CTA
- "Tell me more" expanded reasoning

**F. Race Mode** (2 screens)
- Race countdown (days, phase, per-station readiness)
- Taper plan (auto-generated 14-day when race < 21 days)

**G. Settings** (3 screens)
- Account / subscription
- Notifications (briefing time, training reminders)
- Privacy & data (export, delete, on-device info)

**OVERNIGHT ENGINE** — N3-triggered on-device AI processing
- Trigger: HealthKit N3 detection + BGProcessingTask
- Pipeline: Collect 24h data → Foundation Models → Claude API → Persist briefing → Notify
- Patent-critical telemetry: `processing_completed_during_sleep_vs_on_wake`

**WATCH COMPANION** (minimal UI, no native watch app)

**SUBSCRIPTION** (Paid-only: $14.99/mo or $119.99/yr Pro, 7-day free trial)

### ✗ EXPLICITLY OUT OF SCOPE FOR v1
- Social feed, friends, leaderboards, XP, badges
- OCR/Marathon/CrossFit modes (Phase 2)
- WHOOP / Oura / Garmin sync (Phase 2)
- Watch-native workout app (Phase 2)
- CarPlay, Widgets, Spotlight extension (Phase 2)
- Free tier (Phase 3)
- Android (Phase 3)

---

## FEATURE VIEWS AUDIT

### ✅ IN SCOPE — Core v1 Features (13 directories)

#### 1. **Briefing/** — Morning Briefing Hero Screen (E1)
| File | Purpose | Status |
|------|---------|--------|
| MorningBriefingView.swift | Hero readiness score + recommendation display | ✓ IN SCOPE |
| BriefingModels.swift | Data models for briefing | ✓ IN SCOPE |
| DailyCheckInCard.swift | Daily check-in card UI | ✓ IN SCOPE |
| InsightSuggestionsCard.swift | AI suggestions card | ✓ IN SCOPE |
| RecommendedSession.swift | Recommended workout suggestion | ✓ IN SCOPE |

#### 2. **Coach/** — AI Coach Chat (Top-Level Tab)
| File | Purpose | Status |
|------|---------|--------|
| CoachChatView.swift | Chat list + thread UI | ✓ IN SCOPE |
| CoachChatModels.swift | Conversation + message models | ✓ IN SCOPE |
| CoachChatService.swift | LLM integration for coach replies | ✓ IN SCOPE |
**Note**: Wired into main 5-tab interface (SleepMindMainView.swift). Comment: "Coach was added as a top-level tab in v1 of this IA... confirmed by research (Whoop's Coach tab)"

#### 3. **Diagnostics/** — Debug/MetricKit View (Profile → Diagnostics)
| File | Purpose | Status |
|------|---------|--------|
| DiagnosticsView.swift | MetricKit digest (crashes, CPU, memory) | ✓ DEV-ONLY (v1) |
| MetricsCollector.swift | Metric collection | ✓ DEV-ONLY (v1) |
**Note**: "For a developer (or TestFlight tester filing a bug)". Non-core but useful for beta.

#### 4. **Errors/** — Error Handling
| File | Purpose | Status |
|------|---------|--------|
| SMErrorScreen.swift | Error display screen | ✓ SUPPORTING |

#### 5. **Health/** — Health Metric Detail Views (Recovery Tab)
| File | Purpose | Status |
|------|---------|--------|
| HealthMetricDetailView.swift | Detail view for HRV, RHR, Sleep hours, N3 | ✓ IN SCOPE |
**Metrics**: HRV, RHR, Sleep hours, N3 deep sleep — part of Recovery feature (D1).

#### 6. **Intelligence/** — Training Intelligence (CORE SUPPORTING)
| File | Purpose | Usage | Status |
|------|---------|-------|--------|
| ExerciseDatabase.swift | Exercise library + fuzzy matching | Used by Workouts (InWorkoutPlayerView, PostWorkoutSummaryView) | ✓ IN SCOPE |
| TrainingMethodology.swift | Methodology definitions (Push/Pull/Legs, etc.) | Used by MethodologyPickerView | ✓ IN SCOPE |
| MethodologyPickerView.swift | Select training methodology | Used by WorkoutLibraryView | ✓ IN SCOPE |
| ProgressionEngine.swift | Exercise weight/rep progression suggestions | Used by InWorkoutPlayerView | ✓ IN SCOPE |
| MuscleGroup.swift | Muscle group enum + display | Used by ExerciseDatabase, TrainingMethodology | ✓ IN SCOPE |
| DailyWorkoutGenerator.swift | AI workout generation based on methodology + recovery | Used by TodayWorkoutCard (Today tab, Train tab) | ✓ IN SCOPE |
| TodayWorkoutCard.swift | "Start today's workout" card | Shown on Today + Train tabs | ✓ IN SCOPE |
| SetProgressionCard.swift | Display progression suggestion UI | Used by InWorkoutPlayerView | ✓ IN SCOPE |
| RestTimerView.swift | Rest timer between sets | Used by InWorkoutPlayerView | ✓ IN SCOPE |
| PlateauAlertCard.swift | Performance plateau alert | Used by RecoveryTabView | ✓ IN SCOPE |
| PlateauDetector.swift | Detect exercise plateaus | Used by PlateauAlertCard | ✓ IN SCOPE |
| RecoveryMapView.swift | Recovery status visualization | Used by RecoveryTabView | ✓ IN SCOPE |
| VolumeTrackingView.swift | Training volume progress | Used by RecoveryTabView | ✓ IN SCOPE |
| ExerciseHistory.swift | Exercise logging utilities | Used by PostWorkoutSummaryView (logExerciseHistory) | ✓ IN SCOPE |
| RecoveryMap.swift | Recovery status model | Supporting RecoveryMapView | ✓ IN SCOPE |
| VolumeTracker.swift | Volume tracking model | Supporting VolumeTrackingView | ✓ IN SCOPE |

**Conclusion**: All 16 Intelligence files support v1 core features. KEEP ALL.

#### 7. **N3Trigger/** — Overnight Engine (CORE)
| File | Purpose | Status |
|------|---------|--------|
| N3Trigger.swift | Core trigger orchestration | ✓ CORE |
| OvernightPipeline.swift | Main overnight processing pipeline | ✓ CORE |
| SleepKitObserver.swift | HealthKit N3 observer + BGProcessingTask registration | ✓ CORE |
| ClaudeBriefingService.swift | Claude API integration for briefing generation | ✓ CORE |
| ReadinessScorer.swift | On-device readiness score (0-100) | ✓ CORE |
| OnDeviceBriefingBuilder.swift | On-device briefing construction | ✓ CORE |
| BriefingInputCollector.swift | Gather 24h data (workouts, nutrition, sleep) | ✓ CORE |
| BriefingNotificationScheduler.swift | Schedule local notification for wake | ✓ CORE |
| InsightPacketGenerator.swift | Generate insight packets for detail views | ✓ CORE |
| SMInsightPacket.swift | Insight packet model | ✓ CORE |
| ProcessingOriginTelemetry.swift | **PATENT-CRITICAL**: Track sleep vs. on-wake processing | ✓ CORE |
| OvernightScheduler.swift | Scheduler for pipeline execution | ✓ CORE |
| SafetyNetScheduler.swift | Fallback on-wake execution | ✓ CORE |
| BriefingInputs.swift | Input data model | ✓ CORE |
| BreathingDisturbancesReader.swift | Sleep disturbance analysis | ✓ CORE |
| FocusIndexScorer.swift | Focus/readiness scoring | ✓ CORE |
| GaussianPerturbation.swift | Noise injection for telemetry privacy | ✓ CORE |
| MaintenanceOperation.swift | Maintenance tasks | ✓ CORE |
| OperationPriorityScorer.swift | Priority scoring for operations | ✓ CORE |
| OperationStateStore.swift | State persistence | ✓ CORE |
| PipelineCheckpoint.swift | Checkpoint tracking | ✓ CORE |
| SemanticKnowledgeGraph.swift | Knowledge graph for insights | ✓ CORE |

**Conclusion**: All 22 files are CORE v1 differentiator. KEEP ALL.

#### 8. **Notifications/** — Local Notification Orchestration
| File | Purpose | Status |
|------|---------|--------|
| NotificationCenter.swift | Local notification scheduling (briefing alert, training reminders) | ✓ IN SCOPE |

#### 9. **Nutrition/** — Nutrition Logging (C1–C3)
| File | Purpose | Status |
|------|---------|--------|
| TodayNutritionView.swift | C1 Today's nutrition (meals, water, protein) | ✓ IN SCOPE |
| AddMealView.swift | C2 Add meal UI | ✓ IN SCOPE |
| BarcodeScannerView.swift | Barcode scan (Open Food Facts API) | ✓ IN SCOPE |
| FoodSearchView.swift | Food search + manual entry | ✓ IN SCOPE |
| MacroTargetsView.swift | C3 Macro target setup | ✓ IN SCOPE |
| EatTabView.swift | Main Eat tab orchestration | ✓ IN SCOPE |
| Nutrition.swift | Root view + orchestration | ✓ IN SCOPE |
| NutritionModels.swift | Data models | ✓ IN SCOPE |
| OpenFoodFactsClient.swift | Open Food Facts API client | ✓ IN SCOPE |

**Conclusion**: Exact match to SCOPE.md C1–C3. KEEP ALL.

#### 10. **Onboarding/** — Account Setup (A1–A4)
| File | Purpose | Status |
|------|---------|--------|
| BaselineAssessmentView.swift | A4 Hyrox profile setup (race date, station goals, training frequency) | ✓ IN SCOPE |

#### 11. **Race/** — Race Mode (F1–F2)
| File | Purpose | Status |
|------|---------|--------|
| RaceReadinessView.swift | F1 Race countdown + per-station readiness vs. target | ✓ IN SCOPE |
| TaperPlanView.swift | F2 Taper plan display (14-day auto-generated when < 21 days) | ✓ IN SCOPE |
| Race.swift | Root view orchestration | ✓ IN SCOPE |
| RaceModels.swift | Data models | ✓ IN SCOPE |
| RaceReadiness.swift | Readiness calculation | ✓ IN SCOPE |
| StationGoal.swift | Station goal model | ✓ IN SCOPE |
| StationGoalsEditor.swift | Edit station goals | ✓ IN SCOPE |
| TaperPlanGenerator.swift | Auto-generate taper plan | ✓ IN SCOPE |

**Conclusion**: Exact match to SCOPE.md F1–F2. KEEP ALL.

#### 12. **Recovery/** — Sleep & Recovery (D1–D2)
| File | Purpose | Status |
|------|---------|--------|
| RecoveryTabView.swift | D1 Last night view (sleep stages, N3, HRV, RHR) + D2 7/30-day trend | ✓ IN SCOPE |
| Recovery.swift | Root orchestration | ✓ IN SCOPE |
| RecoveryModels.swift | Data models | ✓ IN SCOPE |
| WatchPoints.swift | Watch-related data | ✓ IN SCOPE |

**Conclusion**: Exact match to SCOPE.md D1–D2. KEEP ALL.

#### 13. **Shell/** — App Root & Navigation
| File | Purpose | Status |
|------|---------|--------|
| SleepMindRootView.swift | App root (auth check, splash) | ✓ IN SCOPE |
| SleepMindMainView.swift | 5-tab main view (Today, Coach, Eat, Train, Recovery) | ✓ IN SCOPE |
| SleepMindOnboardingView.swift | Onboarding flow | ✓ IN SCOPE |
| TodayAccessories.swift | Today tab accessories | ✓ IN SCOPE |

**Conclusion**: Root navigation. KEEP ALL.

#### 14. **Subscription/** — Paywall & StoreKit 2
| File | Purpose | Status |
|------|---------|--------|
| PaywallView.swift | Paywall UI ($14.99/mo or $119.99/yr) | ✓ IN SCOPE |
| SubscriptionManager.swift | StoreKit 2 subscription logic | ✓ IN SCOPE |

**Conclusion**: Required for v1 paid model. KEEP ALL.

#### 15. **Watch/** — Apple Watch Companion
| File | Purpose | Status |
|------|---------|--------|
| WatchConnectivityManager.swift | WatchConnectivity orchestration (iOS ↔ watchOS) | ✓ IN SCOPE |
| WatchEventRouter.swift | Event routing | ✓ IN SCOPE |
| WatchSessionProtocol.swift | Session protocol | ✓ IN SCOPE |
| HealthKitWorkoutWriter.swift | Write workouts to HealthKit from watch | ✓ IN SCOPE |

**Conclusion**: Minimal watch companion as per SCOPE.md. KEEP ALL.

#### 16. **Workouts/** — Training Logging (B1–B6)
| File | Purpose | Status |
|------|---------|--------|
| WorkoutLibraryView.swift | B6 Training history (calendar + list) + methodology picker | ✓ IN SCOPE |
| WorkoutBuilderView.swift | B2 Workout builder (warmup/blocks/cooldown, 8 stations) | ✓ IN SCOPE |
| InWorkoutPlayerView.swift | B3 In-workout player (timer, sets, station UI, HR view) | ✓ IN SCOPE |
| PostWorkoutSummaryView.swift | B5 Post-workout summary (RPE, notes, auto HR/calories) | ✓ IN SCOPE |
| HyroxProfile.swift | User profile with Hyrox-specific data | ✓ IN SCOPE |
| HyroxStation.swift | Hyrox station definitions + StationType enum | ✓ IN SCOPE |
| WorkoutModels.swift | Data models (Workout, WorkoutBlock, WorkoutSet) | ✓ IN SCOPE |
| WorkoutDraft.swift | Draft workout model (in-progress) | ✓ IN SCOPE |
| StationInputView.swift | Station-specific UI during workout | ✓ IN SCOPE |
| WorkoutImpactAnalyzer.swift | Workout impact analysis | ✓ IN SCOPE |
| SMWorkoutImpact.swift | Workout impact model | ✓ IN SCOPE |

**Conclusion**: Exact match to SCOPE.md B1–B6. KEEP ALL.

#### 17. **Settings/** — Account, Notifications, Privacy (G1–G3)
| File | Purpose | Status |
|------|---------|--------|
| NotificationSettingsView.swift | G2 Briefing time, training reminders | ✓ IN SCOPE |
| PrivacyDataView.swift | G3 Data export, delete, on-device info | ✓ IN SCOPE |
| DataExportService.swift | Data export implementation | ✓ IN SCOPE |
| SandowProfileViews.swift | Generic profile views (account, subscription) | ✓ IN SCOPE |
| AIKeySettingsView.swift | API key management (dev-oriented, optional v1) | ⚠️ OPTIONAL |
| LanguagePickerView.swift | Language selection | ✗ OUT OF SCOPE (no i18n in v1) |
| LiveChatView.swift | Support chat | ⚠️ QUESTIONABLE (not in SCOPE.md) |

**Status**: G2–G3 required. Remove LanguagePickerView. Review LiveChatView (optional). Keep AIKeySettingsView (dev-useful).

#### 18. **Shared/** — App Group Coordination
| File | Purpose | Status |
|------|---------|--------|
| AppGroup.swift | App Group sync (iOS ↔ Watch) | ✓ IN SCOPE |

---

### ❌ OUT OF SCOPE — Must Remove (4 directories)

#### **Community/** — Social Feed, Posts, Leaderboards
**Violates**: SCOPE.md "No social, no leaderboards in v1"

| File | Purpose | Status |
|------|---------|--------|
| CommunityViews.swift | Feed, posts, comments, articles, workshops | ✗ REMOVE |
| CommunityModels.swift | Post, Article, Workshop models | ✗ REMOVE |
| CommunityRTDBService.swift | Firebase Realtime DB sync for social | ✗ REMOVE |
| CommunityModerationService.swift | Content moderation | ✗ REMOVE |

**Action**: DELETE entire Features/Community/ directory.

#### **Shop/** — Product Recommendations
**Reason**: Not in SCOPE.md v1 features. Requires body analysis (Vision multimodal).

| File | Purpose | Status |
|------|---------|--------|
| ProductRecommendationView.swift | AI product recommendations (skincare, supplements, etc.) | ✗ REMOVE |

**Action**: DELETE entire Features/Shop/ directory.

#### **Search/** — Global Search
**Reason**: No dedicated search in SCOPE.md v1 features.

| File | Purpose | Status |
|------|---------|--------|
| GlobalSearchView.swift | Global search across app content | ✗ REMOVE |

**Action**: DELETE entire Features/Search/ directory.

#### **Coaching/** — Coaching Conversation Thread
**Reason**: Duplicate/superseded by Coach/. Separate implementation of similar functionality.

| File | Purpose | Status |
|------|---------|--------|
| CoachingChatView.swift | Chat view (uses CoachingAgentService) | ✗ REMOVE |

**Action**: DELETE entire Features/Coaching/ directory (Coach/ is the active implementation).

---

## SERVICE AUDIT

### ✅ IN SCOPE — Core Services (~30 files)

#### Core App Infrastructure (12 files)
- **UserManager.swift** — Firebase/OAuth authentication
- **UserManager+RGFirebaseAuth.swift** — Firebase Auth provider
- **UserManager+RGOAuth.swift** — OAuth provider
- **BootStateManager.swift** — App boot orchestration
- **OnboardingManager.swift** — Onboarding flow state
- **GlobalSettings.swift** — App-wide settings
- **AnalyticsManager.swift** — Event tracking (telemetry required for patent evidence)
- **CrashReportingManager.swift** — Crash reporting
- **Logger.swift** — Debug logging
- **DebugLogger.swift** — Additional debug logging
- **NetworkStatusManager.swift** — Network connectivity detection
- **PersistentHistoryService.swift** — SwiftData change tracking (may be in-use)

#### Health & HealthKit (3 files)
- **HealthKitManager.swift** — HealthKit data access (sleep, HRV, RHR, workouts)
- **HealthKitService.swift** — HealthKit queries/observations
- **Health/HealthKitBackfillService.swift** — Backfill historical HealthKit data

#### LLM/AI Providers (3 files)
- **FoundationModelsWrapper.swift** — Apple Foundation Models (on-device)
- **AnthropicAPIHandler.swift** — Claude API integration (for overnight briefing)
- **LLMSkills/WebFetchSkill.swift** — LLM skill definition

#### Firebase & Notifications (2 files)
- **SovvRTDB.swift** — Firebase Realtime DB (user data sync)
- **SovvPushService.swift** — APNs/push notifications

#### Security & Encryption (3 files)
- **KeychainManager.swift** — Secure credential storage
- **EncryptionService.swift** — Data encryption operations
- **AIKeychain.swift** — API key secure storage

#### Network & Config (3 files)
- **APIService.swift** — HTTP client
- **APIOrchestrator.swift** — API orchestration
- **ConfigOrchestrator.swift** — Configuration management (may be dev-only)

#### Assets (1 file)
- **Assets/ExerciseSpriteService.swift** — Exercise images + sprites

#### Notifications (1 file)
- **NotificationCenter.swift** — Local notification scheduling

---

### ❌ OUT OF SCOPE — Must Remove (~97 files)

#### Multimodal/Vision (3 files)
- MultiModalAIIntegration.swift
- MultiModalAdvancedCapabilities.swift
- Vision/BodyAnalysisModels.swift

#### Voice/Translation (16 files)
- VoiceService.swift, VoiceCommandProcessor.swift, VoiceConversationManager.swift
- VoiceAudioManager.swift, VoiceConfigLoader.swift, VoiceServiceCoordinator.swift
- VoiceServiceExtensions.swift, VoiceServiceNSIPIntegration.swift, VoiceServiceTest.swift
- VoiceModels.swift, SpeechProcessor.swift
- LiveTranslationService.swift, LiveTranslationSupport.swift
- MLXTranslationWrapper.swift, MLXMemoryManager.swift, TranslationService.swift

#### Distributed Storage (5 files)
- IPFSStorageManager.swift (IPFS)
- ArweaveStorageManager.swift (Arweave)
- ExternalDriveStorageManager.swift
- ShardPersistenceManager.swift
- ShardRegistry.swift

#### Commerce/Shopping (2 files)
- Commerce/ProductRecommendationService.swift
- Commerce/CartValidationService.swift

#### Advanced AI/Analytics (4 files)
- AdvancedAnalyticsEngine.swift
- AutonomousProblemSolver.swift
- CoachingAgentService.swift (advanced coaching, not chat)
- AILifeAwarenessService.swift

#### Search (1 file)
- Search/VectorSearchService.swift

#### DCourtKit Legacy/Inheritance (~60 files)
Listed in CLAUDE.md as "strip candidates" and unused by sovv:

**AI/LLM (9 files)**:
- OpenAIAPIHandler.swift (we use Anthropic)
- HuggingFaceAPIHandler.swift
- MiniMaxAPIHandler.swift
- RemoteLLMHandler.swift
- InferenceOrchestration.swift
- NSIPModels.swift, NSIPService.swift
- PromptMemoryInjector.swift
- ConceptExtractor.swift

**Storage & Persistence (6 files)**:
- CloudStorageProvider.swift
- DatabaseMiddleware.swift
- DatabaseResetService.swift
- MemoryLogger.swift
- SQLiteMemoryManager.swift
- Secrets+Memory.swift

**System/Boot (5 files)**:
- PositronicBootSystem.swift
- PrimeDirectiveEnforcer.swift
- StealthEvolutionManager.swift
- EvolutionEventManager.swift
- ProtocolEventManager.swift

**Config/Management (7 files)**:
- JSONConfigManager.swift
- ServerConfigManager.swift
- Admin/AdminManagementService.swift
- VersionManager.swift
- DeviceCapabilityManager.swift
- ProductionGuardrails.swift
- ProductionMetricsLogger.swift

**Utilities (10 files)**:
- BraveSearchService.swift
- BundledAPIKeys.swift
- CodeAnalyzer.swift
- DepthEstimator.swift
- DigitalCourtTips.swift
- DocumentProcessor.swift
- EmbeddedInstinctsManager.swift
- FrequencyReferenceManager.swift
- WebScrapingEngine.swift
- TimeContextService.swift

**Misc (8 files)**:
- CallScreeningService.swift
- OpenSSHKeyDecryptor.swift
- SSHConnectionManager.swift, SSHTypes.swift
- SoulGlobalsLoader.swift
- SparkEngineTypes.swift
- UnifiedMultiModalTypes.swift
- UserLoggerService.swift
- iOS18PrivacyManager.swift

**Auth (1 file)**:
- Authentication/EmailOTPService.swift (Firebase handles auth)

---

## SUMMARY & RECOMMENDATIONS

### ✅ KEEP FOR v1 (Approved)
| Category | Count | Notes |
|----------|-------|-------|
| Feature Directories | 18 | 13 core + 4 supporting + 1 mixed (Settings) |
| Core Workouts | 11 files | B1–B6 complete |
| Nutrition | 9 files | C1–C3 complete |
| Recovery | 4 files | D1–D2 complete |
| Briefing | 5 files | E1 complete |
| Race Mode | 8 files | F1–F2 complete |
| N3 Overnight Engine | 22 files | **CORE v1 differentiator** |
| Coach Chat | 3 files | Top-level tab (active) |
| Intelligence | 16 files | All supporting v1 Workouts/Recovery |
| Services (Core) | ~30 files | HealthKit, Firebase, LLM, Auth, Notifications |

### ❌ REMOVE FOR v1 (Action Required)
| Category | Count | Action |
|----------|-------|--------|
| Community/ | 4 files | DELETE — Violates "no social" |
| Shop/ | 1 directory | DELETE — Not in scope |
| Search/ | 1 directory | DELETE — Not in scope |
| Coaching/ | 1 directory | DELETE — Superseded by Coach/ |
| Settings (bad views) | 2 files | REMOVE: LanguagePickerView, LiveChatView |
| Multimodal/Vision | 3 files | DELETE |
| Voice/Translation | 16 files | DELETE |
| Distributed Storage (IPFS) | 5 files | DELETE |
| Commerce | 2 files | DELETE |
| Advanced AI | 4 files | DELETE |
| Search (Vector) | 1 file | DELETE |
| DCourtKit Legacy | ~60 files | DELETE (strip candidates per CLAUDE.md) |

### 🔄 REVIEW FOR v1 (Owner Decision)
| Item | Status | Decision |
|------|--------|----------|
| AIKeySettingsView.swift | DEV-ONLY | Keep (useful for TestFlight) or remove (user-facing) |
| ConfigOrchestrator.swift | UNCLEAR | Verify if used by runtime config |
| MultiModalModels.swift | UNUSED | Delete (orphaned) |

---

## Phase 1 Action Checklist (Pre-v1 Ship)

### Deletions (High Priority)
- [ ] `rm -rf Features/Community/`
- [ ] `rm -rf Features/Shop/`
- [ ] `rm -rf Features/Search/`
- [ ] `rm -rf Features/Coaching/`
- [ ] `rm Features/Settings/LanguagePickerView.swift`
- [ ] `rm Services/MultiModalAIIntegration.swift`
- [ ] `rm Services/MultiModalAdvancedCapabilities.swift`
- [ ] `rm Services/Vision/BodyAnalysisModels.swift`
- [ ] `rm Services/Voice*.swift` (all 16 voice files)
- [ ] `rm Services/IPFSStorageManager.swift`
- [ ] `rm Services/ArweaveStorageManager.swift`
- [ ] `rm Services/Commerce/*.swift`
- [ ] Remove all ~60 DCourtKit legacy files (listed in CLAUDE.md strip candidates)

### Audits (Medium Priority)
- [ ] Verify no navigation paths reference deleted features
- [ ] Verify no lingering imports of deleted files
- [ ] Review AIKeySettingsView (dev-only vs. user-facing decision)
- [ ] Review LiveChatView (support chat — in or out?)
- [ ] Verify LanguagePickerView removal doesn't break Settings UI

### Testing (High Priority)
- [ ] Run `xcodebuild build` to catch import errors
- [ ] TestFlight beta: ensure all deleted features unreachable
- [ ] Verify 5-tab navigation (Today/Coach/Eat/Train/Recovery) fully functional
- [ ] Verify N3 overnight engine works end-to-end
- [ ] Verify Briefing generation + notification delivery

---

## Phase 2 Action Checklist (Post-v1, Dead Code Pass)

- [ ] Remove all "strip candidates" from DCourtKit (comprehensive audit)
- [ ] Remove unused Service files (audit import dependency graph)
- [ ] Remove test files / example code
- [ ] Audit Comments/TODO/FIXME for deferred Phase 2+ work

---

## Notes

### Patent-Critical Telemetry
`Features/N3Trigger/ProcessingOriginTelemetry.swift` is required for IPOS C-02 patent prosecution. Ensure `processing_completed_during_sleep_vs_on_wake` counter is instrumented from day one.

### Coach vs. Coaching
- **Coach/** (KEEP) — Active CoachChatView wired into main 5-tab interface. Wired into Profile → AI Coach for v1.
- **Coaching/** (REMOVE) — Separate CoachingChatView; appears to be superseded. Uses different service (CoachingAgentService vs. CoachChatService).

### Intelligence/ Fully In-Scope
Despite large directory (16 files), all files support core v1 Workouts + Recovery features:
- Workout builder/player uses: ExerciseDatabase, ProgressionEngine, RestTimerView, SetProgressionCard
- Today's workout generation: DailyWorkoutGenerator, MethodologyPickerView, TrainingMethodology
- Recovery tab uses: RecoveryMapView, VolumeTrackingView, PlateauAlertCard/DetectorR

---

**End of Audit**
