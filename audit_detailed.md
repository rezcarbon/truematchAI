# SleepMind v1 Scope Audit - Detailed Findings

## VERIFIED SCOPE (from SCOPE.md)
### v1 MUST INCLUDE
- A. Onboarding & accounts (4 screens)
- B. Training logging (6 screens) → Features/Workouts/
- C. Nutrition logging (3 screens) → Features/Nutrition/
- D. Sleep & recovery (2 screens) → Features/Recovery/
- E. Morning Briefing (1 screen) → Features/Briefing/
- F. Race mode (2 screens) → Features/Race/
- G. Settings (3 screens)
- Overnight Engine → Features/N3Trigger/
- Watch Companion → Features/Watch/
- Subscription (paywall) → Features/Subscription/

### v1 EXPLICITLY EXCLUDES
- Social feed, friends, leaderboards
- OCR/Marathon/CrossFit modes
- WHOOP / Oura / Garmin
- Watch-native workout app (companion only)
- CarPlay, Widgets, Spotlight extension
- Free tier
- Android

---

## FEATURE AUDIT BY DIRECTORY

### IN SCOPE - Core v1 Features

#### Briefing/ (CORE)
- BriefingModels.swift
- DailyCheckInCard.swift
- InsightSuggestionsCard.swift
- MorningBriefingView.swift
- RecommendedSession.swift
**Status**: IN SCOPE - This is E1 from SCOPE.md (Morning Briefing hero screen)

#### N3Trigger/ (CORE - Overnight Engine)
- N3Trigger.swift - Core trigger orchestration
- OvernightPipeline.swift - Main pipeline
- OvernightScheduler.swift
- SafetyNetScheduler.swift
- SleepKitObserver.swift - HealthKit observer
- ClaudeBriefingService.swift - Claude API integration
- ReadinessScorer.swift - On-device readiness scoring
- OnDeviceBriefingBuilder.swift
- BriefingInputCollector.swift
- BriefingNotificationScheduler.swift
- InsightPacketGenerator.swift
- SMInsightPacket.swift
- ProcessingOriginTelemetry.swift - Patent-critical telemetry
- [+8 more engine components]
**Status**: IN SCOPE - Core v1 differentiator

#### Nutrition/ (SCOPE SECTION C)
- TodayNutritionView.swift - C1 Today's nutrition
- AddMealView.swift - C2 Add meal UI
- BarcodeScannerView.swift - Barcode scanning (Open Food Facts)
- FoodSearchView.swift - Food search
- MacroTargetsView.swift - C3 Macro targets
- EatTabView.swift - Main nutrition tab view
- Nutrition.swift - Models/orchestration
- NutritionModels.swift
- OpenFoodFactsClient.swift - Open Food Facts API
**Status**: IN SCOPE - Exactly matches SCOPE.md C1-C3

#### Onboarding/ (SCOPE SECTION A)
- BaselineAssessmentView.swift - User profile/baseline setup
**Status**: IN SCOPE - Part of A4 (Hyrox profile setup)

#### Race/ (SCOPE SECTION F)
- Race.swift
- RaceModels.swift
- RaceReadiness.swift
- RaceReadinessView.swift - F1 Race countdown + readiness
- StationGoal.swift
- StationGoalsEditor.swift
- TaperPlanGenerator.swift - Taper plan generator
- TaperPlanView.swift - F2 Taper plan display
**Status**: IN SCOPE - Exactly matches SCOPE.md F1-F2

#### Recovery/ (SCOPE SECTION D)
- Recovery.swift
- RecoveryModels.swift
- RecoveryTabView.swift - D1 Last night, D2 Trend view
- WatchPoints.swift
**Status**: IN SCOPE - Exactly matches SCOPE.md D1-D2

#### Shell/ (Root Navigation)
- SleepMindMainView.swift - Main tab view
- SleepMindOnboardingView.swift - Onboarding flow
- SleepMindRootView.swift - App root
- TodayAccessories.swift
**Status**: IN SCOPE - Root view infrastructure

#### Subscription/ (Paywall)
- PaywallView.swift - StoreKit 2 paywall UI
- SubscriptionManager.swift - StoreKit 2 subscription logic
**Status**: IN SCOPE - Required for v1 paid model ($14.99/mo)

#### Watch/ (SCOPE B4 - Apple Watch Companion)
- WatchConnectivityManager.swift - WatchConnectivity orchestration
- WatchEventRouter.swift
- WatchSessionProtocol.swift
- HealthKitWorkoutWriter.swift
**Status**: IN SCOPE - Apple Watch companion (minimal UI as per SCOPE.md)

#### Workouts/ (SCOPE SECTION B)
- WorkoutModels.swift
- HyroxProfile.swift - User profile with Hyrox data
- HyroxStation.swift - Hyrox station definitions + StationType enum
- WorkoutBuilderView.swift - B2 Workout builder (warmup/blocks/cooldown)
- InWorkoutPlayerView.swift - B3 In-workout player (timer, sets, HR view)
- PostWorkoutSummaryView.swift - B5 Post-workout summary (RPE, notes, HR/calories)
- WorkoutLibraryView.swift - B6 Training history (calendar + list)
- StationInputView.swift - Station-specific UI during workout
- WorkoutDraft.swift - Draft workout model
- SMWorkoutImpact.swift
- WorkoutImpactAnalyzer.swift
**Status**: IN SCOPE - Exactly matches SCOPE.md B1-B6

#### Settings/ (SCOPE SECTION G + Partial)
- NotificationSettingsView.swift - G2 Notification settings (briefing time, training reminders)
- PrivacyDataView.swift - G3 Privacy & data export
- DataExportService.swift - Data export functionality
- AIKeySettingsView.swift - API key management (dev-oriented)
- LanguagePickerView.swift - Language selection (OUT - no i18n in v1)
- LiveChatView.swift - Support chat (QUESTIONABLE)
- SandowProfileViews.swift - Generic profile views
**Status**: PARTIALLY IN SCOPE - G2, G3 required; language/chat questionable

#### Shared/
- AppGroup.swift - App Group coordination (iOS ↔ Watch)
**Status**: IN SCOPE - Supporting infrastructure

#### Notifications/
- NotificationCenter.swift - Local notification orchestration
**Status**: IN SCOPE - Supporting service

---

### OUT OF SCOPE - Explicitly Excluded

#### Community/ (EXPLICIT EXCLUSION - "No social, no leaderboards in v1")
- CommunityViews.swift - Feed, posts, comments
- CommunityModels.swift
- CommunityRTDBService.swift - Real-time DB sync
- CommunityModerationService.swift - Moderation
**Status**: OUT OF SCOPE - Violates "No social/leaderboards in v1" from SCOPE.md

#### Shop/ (NOT IN SCOPE - Product marketplace)
- ProductRecommendationView.swift - Product recommendations with body analysis
**Status**: OUT OF SCOPE - Not mentioned in SCOPE.md v1 features

#### Search/ (QUESTIONABLE - No dedicated search in v1)
- GlobalSearchView.swift - Global search (mentions content across app)
**Status**: OUT OF SCOPE - No search feature listed in SCOPE.md

---

### QUESTIONABLE / PARTIALLY-IMPLEMENTED

#### Coach/ (AI Coach Chat - Wired into Profile)
- CoachChatView.swift - Comment: "Wired into Profile → 'AI Coach' for v1"
- CoachChatModels.swift
- CoachChatService.swift
**Status**: IN SCOPE (but disabled/not wired) - Comment says v1 but may not be fully implemented
**Decision needed**: Is AI Coach chat part of v1 or Phase 2?

#### Coaching/ (Separate coaching service)
- CoachingChatView.swift - Similar to Coach but uses different service
**Status**: UNCLEAR - Possible duplicate/superseded implementation

#### Diagnostics/ (MetricKit diagnostics)
- DiagnosticsView.swift - Comment: "Profile → Diagnostics... for a developer (or TestFlight tester)"
- MetricsCollector.swift
**Status**: IN SCOPE (dev-only) - Useful for beta testing, non-core

#### Errors/ (Error handling)
- SMErrorScreen.swift - Error display screen
**Status**: IN SCOPE (supporting) - Required for error handling

#### Health/ (Health metrics detail view)
- HealthMetricDetailView.swift - Detailed view for HRV, RHR, Sleep hours, N3
**Status**: IN SCOPE - Supports Recovery tab detail views

#### Intelligence/ (Advanced training intelligence)
- DailyWorkoutGenerator.swift - AI workout generation (FUTURE?)
- ExerciseDatabase.swift - Exercise library
- ExerciseHistory.swift - History tracking
- MethodologyPickerView.swift - Training methodology selection
- PlateauDetector.swift - Performance plateau detection
- ProgressionEngine.swift - Progression algorithms
- TrainingMethodology.swift - Methodology definitions
- VolumeTracker.swift - Training volume tracking
- RestTimerView.swift
- RecoveryMapView.swift
- SetProgressionCard.swift
- TodayWorkoutCard.swift
- VolumeTrackingView.swift
- [+2 more files]
**Status**: OUT OF SCOPE (Advanced Phase 2+) - Comment in MethodologyPickerView says "The AI builds workouts based on your chosen methodology" but daily workout generation is not in v1 scope. These appear to be Phase 2+ features, some possibly used by Briefing/recommended session.

---

## SERVICE AUDIT

### IN SCOPE - Core Services

#### Health Services
- HealthKitManager.swift - HealthKit data access
- HealthKitService.swift - HealthKit queries/observations
- Health/HealthKitBackfillService.swift - Backfill historical data
**Status**: IN SCOPE - Core to v1

#### LLM/AI Provider Services (v1-Required)
- FoundationModelsWrapper.swift - Apple Foundation Models (on-device)
- AnthropicAPIHandler.swift - Claude API integration
- LLMSkills/WebFetchSkill.swift - LLM skill definition
**Status**: IN SCOPE - Core to overnight engine

#### Firebase Services (v1-Required)
- SovvRTDB.swift - Firebase Realtime DB access
- SovvPushService.swift - APNs/push notifications
**Status**: IN SCOPE - Auth + data sync infrastructure

#### Core App Services
- UserManager.swift - User auth management
- UserManager+RGFirebaseAuth.swift - Firebase auth integration
- UserManager+RGOAuth.swift - OAuth integration
- BootStateManager.swift - App boot orchestration
- OnboardingManager.swift - Onboarding state management
- GlobalSettings.swift - App-wide settings
- AnalyticsManager.swift - Analytics tracking
- CrashReportingManager.swift - Crash reporting
- Logger.swift - Debug logging
- DebugLogger.swift - Additional debug logging
**Status**: IN SCOPE - Supporting infrastructure

#### Keychain & Encryption
- KeychainManager.swift - Secure storage
- EncryptionService.swift - Encryption operations
- AIKeychain.swift - API key storage
**Status**: IN SCOPE - Required for security

#### Notifications
- NotificationCenter.swift - Local notification scheduling
**Status**: IN SCOPE - Core to briefing delivery

#### Assets
- Assets/ExerciseSpriteService.swift - Exercise image assets
**Status**: IN SCOPE - Supporting Workouts feature

#### Network & Config
- APIService.swift - HTTP client
- APIOrchestrator.swift - API orchestration
- NetworkStatusManager.swift - Network state detection
**Status**: IN SCOPE - Infrastructure

---

### OUT OF SCOPE - Phase 2/3 or Clearly Out-of-Scope

#### Multimodal/Vision Services (NOT IN v1)
- MultiModalAIIntegration.swift
- MultiModalAdvancedCapabilities.swift
- MultiModalModels.swift
- Vision/BodyAnalysisModels.swift - Body analysis (used by Shop/Product recommendations)
**Status**: OUT OF SCOPE - Not in v1 scope

#### Voice Services (NOT IN v1)
- VoiceService.swift
- VoiceCommandProcessor.swift
- VoiceConversationManager.swift
- VoiceAudioManager.swift
- VoiceConfigLoader.swift
- VoiceServiceCoordinator.swift
- VoiceServiceExtensions.swift
- VoiceServiceNSIPIntegration.swift
- VoiceServiceTest.swift
- VoiceModels.swift
- SpeechProcessor.swift
- LiveTranslationService.swift
- LiveTranslationSupport.swift
- MLXTranslationWrapper.swift
- MLXMemoryManager.swift
- TranslationService.swift
**Status**: OUT OF SCOPE - No voice/translation in v1

#### Distributed Storage (IPFS) - Deferred
- IPFSStorageManager.swift - IPFS storage ("not yet implemented")
- ArweaveStorageManager.swift - Arweave storage
- ExternalDriveStorageManager.swift
- ShardPersistenceManager.swift
- ShardRegistry.swift
**Status**: OUT OF SCOPE - Deferred distributed storage (mention in SCOPE.md strip candidates)

#### Commerce/Shopping (NOT IN v1)
- Commerce/ProductRecommendationService.swift
- Commerce/CartValidationService.swift
**Status**: OUT OF SCOPE - Not in v1 scope

#### Advanced AI/Analytics (Phase 2+)
- AdvancedAnalyticsEngine.swift
- AutonomousProblemSolver.swift
- CoachingAgentService.swift - Advanced coaching (separate from chat)
- AILifeAwarenessService.swift
**Status**: OUT OF SCOPE - Phase 2+

#### Admin/Management (Dev-Only or Not Needed)
- Admin/AdminManagementService.swift - Admin panel
- VersionManager.swift - Version tracking
- DeviceCapabilityManager.swift - Device features
- CallScreeningService.swift
- ConfigOrchestrator.swift
- ServerConfigManager.swift
- ProductionGuardrails.swift
- ProductionMetricsLogger.swift
**Status**: OUT OF SCOPE or DEV-ONLY - Not end-user facing

#### Legacy/Inherited (From DCourtKit - Strip Candidates)
- BraveSearchService.swift
- BundledAPIKeys.swift
- CloudStorageProvider.swift
- CodeAnalyzer.swift
- ConceptExtractor.swift
- DatabaseMiddleware.swift
- DatabaseResetService.swift
- DepthEstimator.swift
- DigitalCourtTips.swift
- DocumentProcessor.swift
- EmbeddedInstinctsManager.swift
- EvolutionEventManager.swift
- FrequencyReferenceManager.swift
- HuggingFaceAPIHandler.swift
- InferenceOrchestration.swift
- JSONConfigManager.swift
- MemoryLogger.swift
- MiniMaxAPIHandler.swift
- NSIPModels.swift / NSIPService.swift
- OpenAIAPIHandler.swift - OpenAI (we use Anthropic/Claude)
- OpenSSHKeyDecryptor.swift
- PersistentHistoryService.swift
- PositronicBootSystem.swift
- PrimeDirectiveEnforcer.swift
- PromptMemoryInjector.swift
- ProtocolEventManager.swift
- RemoteLLMHandler.swift
- Search/VectorSearchService.swift
- Secrets+Memory.swift
- SoulGlobalsLoader.swift
- SparkEngineTypes.swift
- StealthEvolutionManager.swift
- TimeContextService.swift
- UnifiedMultiModalTypes.swift
- UserLoggerService.swift
- WebScrapingEngine.swift
- iOS18PrivacyManager.swift
- Authentication/EmailOTPService.swift - Firebase handles auth
**Status**: OUT OF SCOPE - DCourtKit inheritance; listed as "strip candidates" in CLAUDE.md

#### Search (NOT IN v1)
- Search/VectorSearchService.swift - Semantic search (used by Shop)
**Status**: OUT OF SCOPE - Only used by Shop feature

---

## SUMMARY

### VIEWS TO KEEP FOR v1 (18 directories)
1. Briefing/ ✓
2. Coach/ ⚠️ (unclear if active)
3. Diagnostics/ ✓ (dev-only)
4. Errors/ ✓
5. Health/ ✓
6. N3Trigger/ ✓ (CORE)
7. Notifications/ ✓
8. Nutrition/ ✓
9. Onboarding/ ✓
10. Race/ ✓
11. Recovery/ ✓
12. Settings/ ⚠️ (needs curation)
13. Shared/ ✓
14. Shell/ ✓
15. Subscription/ ✓
16. Watch/ ✓
17. Workouts/ ✓
18. Intelligence/ ⚠️ (partially - check usage)

### VIEWS TO REMOVE FOR v1 (5 directories)
1. Community/ ✗ (social - explicitly excluded)
2. Coaching/ ✗ (unclear, possible duplicate)
3. Shop/ ✗ (not in scope)
4. Search/ ✗ (not in scope, used by Shop)
5. Intelligence/ ✗ (most files are Phase 2+ except supporting utilities)

### SERVICES TO KEEP FOR v1
- Core: HealthKit, Firebase, LLM providers (Anthropic/Foundation Models), Auth, Notifications
- Supporting: Keychain, Encryption, Analytics, Crash reporting, Network, Logging
- ~25 services minimum required

### SERVICES TO REMOVE FOR v1
- Multimodal, Voice, IPFS/Arweave, Commerce, Advanced AI, Vector search
- Legacy DCourtKit components
- ~80+ services to defer/remove

---

## RECOMMENDED ACTIONS

### Phase 1: Disable/Flag (before v1 ship)
- [ ] Remove Community/ feature directory
- [ ] Remove Shop/ feature directory  
- [ ] Remove Search/ feature directory
- [ ] Review and disable Intelligence/* UI views not used by Briefing
- [ ] Review Coach/ to confirm v1 status
- [ ] Remove Voice/* services
- [ ] Remove Multimodal/* services
- [ ] Remove IPFS/Arweave services
- [ ] Remove Commerce/* services
- [ ] Remove legacy AI/OpenAI handlers
- [ ] Audit Settings views for out-of-scope options

### Phase 2: Dead Code Pass (post-v1)
- [ ] Remove all "strip candidates" from DCourtKit (listed in CLAUDE.md)
- [ ] Audit Navigation paths to ensure out-of-scope features unreachable
- [ ] Remove Service files not imported by in-scope features

