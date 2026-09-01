# SleepMind v1 — Files to Remove for Scope Compliance

## View/Feature Directories (DELETE ENTIRE DIRECTORIES)

```bash
rm -rf SleepMind/Features/Community/
rm -rf SleepMind/Features/Shop/
rm -rf SleepMind/Features/Search/
rm -rf SleepMind/Features/Coaching/
```

### Community/ (4 files)
- CommunityViews.swift
- CommunityModels.swift
- CommunityRTDBService.swift
- CommunityModerationService.swift

**Reason**: Explicit v1 exclusion — "No social, no leaderboards in v1" per SCOPE.md

### Shop/ (1 directory)
- ProductRecommendationView.swift

**Reason**: Product marketplace not in v1 scope. Requires Vision/multimodal body analysis.

### Search/ (1 directory)
- GlobalSearchView.swift

**Reason**: Global search not in v1 scope.

### Coaching/ (1 directory)
- CoachingChatView.swift

**Reason**: Superseded by Coach/. Duplicate implementation; Coach/ is the active tab.

---

## Settings Views (DELETE SPECIFIC FILES)

```bash
rm SleepMind/Features/Settings/LanguagePickerView.swift
rm SleepMind/Features/Settings/LiveChatView.swift  # OPTIONAL — review first
```

### LanguagePickerView.swift
**Reason**: No i18n (internationalization) in v1. English-only per CLAUDE.md.

### LiveChatView.swift
**Reason**: Support chat not in SCOPE.md v1 features. (OPTIONAL — owner decision if keeping for support)

---

## Service Files (DELETE)

### Multimodal/Vision (3 files)
```bash
rm SleepMind/Services/MultiModalAIIntegration.swift
rm SleepMind/Services/MultiModalAdvancedCapabilities.swift
rm SleepMind/Services/Vision/BodyAnalysisModels.swift
```

### Voice/Translation (16 files)
```bash
rm SleepMind/Services/VoiceService.swift
rm SleepMind/Services/VoiceCommandProcessor.swift
rm SleepMind/Services/VoiceConversationManager.swift
rm SleepMind/Services/VoiceAudioManager.swift
rm SleepMind/Services/VoiceConfigLoader.swift
rm SleepMind/Services/VoiceServiceCoordinator.swift
rm SleepMind/Services/VoiceServiceExtensions.swift
rm SleepMind/Services/VoiceServiceNSIPIntegration.swift
rm SleepMind/Services/VoiceServiceTest.swift
rm SleepMind/Services/VoiceModels.swift
rm SleepMind/Services/SpeechProcessor.swift
rm SleepMind/Services/LiveTranslationService.swift
rm SleepMind/Services/LiveTranslationSupport.swift
rm SleepMind/Services/MLXTranslationWrapper.swift
rm SleepMind/Services/MLXMemoryManager.swift
rm SleepMind/Services/TranslationService.swift
```

### Distributed Storage (5 files)
```bash
rm SleepMind/Services/IPFSStorageManager.swift
rm SleepMind/Services/ArweaveStorageManager.swift
rm SleepMind/Services/ExternalDriveStorageManager.swift
rm SleepMind/Services/ShardPersistenceManager.swift
rm SleepMind/Services/ShardRegistry.swift
```

### Commerce (2 files)
```bash
rm SleepMind/Services/Commerce/ProductRecommendationService.swift
rm SleepMind/Services/Commerce/CartValidationService.swift
```

### Advanced AI (4 files)
```bash
rm SleepMind/Services/AdvancedAnalyticsEngine.swift
rm SleepMind/Services/AutonomousProblemSolver.swift
rm SleepMind/Services/AI/CoachingAgentService.swift  # Different from Coach feature
rm SleepMind/Services/AILifeAwarenessService.swift
```

### Search (1 file)
```bash
rm SleepMind/Services/Search/VectorSearchService.swift
```

### DCourtKit Legacy Strip Candidates (~60 files)

Per CLAUDE.md "Strip candidates (deferred — dedicated pass once sovv code stabilises)":

**AI/LLM (9 files)**
```bash
rm SleepMind/Services/OpenAIAPIHandler.swift
rm SleepMind/Services/HuggingFaceAPIHandler.swift
rm SleepMind/Services/MiniMaxAPIHandler.swift
rm SleepMind/Services/RemoteLLMHandler.swift
rm SleepMind/Services/InferenceOrchestration.swift
rm SleepMind/Services/NSIPModels.swift
rm SleepMind/Services/NSIPService.swift
rm SleepMind/Services/PromptMemoryInjector.swift
rm SleepMind/Services/ConceptExtractor.swift
```

**Storage & Persistence (6 files)**
```bash
rm SleepMind/Services/CloudStorageProvider.swift
rm SleepMind/Services/DatabaseMiddleware.swift
rm SleepMind/Services/DatabaseResetService.swift
rm SleepMind/Services/MemoryLogger.swift
rm SleepMind/Services/SQLiteMemoryManager.swift
rm SleepMind/Services/Secrets+Memory.swift
```

**System/Boot (5 files)**
```bash
rm SleepMind/Services/PositronicBootSystem.swift
rm SleepMind/Services/PrimeDirectiveEnforcer.swift
rm SleepMind/Services/StealthEvolutionManager.swift
rm SleepMind/Services/EvolutionEventManager.swift
rm SleepMind/Services/ProtocolEventManager.swift
```

**Config/Management (7 files)**
```bash
rm SleepMind/Services/JSONConfigManager.swift
rm SleepMind/Services/ServerConfigManager.swift
rm SleepMind/Services/Admin/AdminManagementService.swift
rm SleepMind/Services/VersionManager.swift
rm SleepMind/Services/DeviceCapabilityManager.swift
rm SleepMind/Services/ProductionGuardrails.swift
rm SleepMind/Services/ProductionMetricsLogger.swift
```

**Utilities (10 files)**
```bash
rm SleepMind/Services/BraveSearchService.swift
rm SleepMind/Services/BundledAPIKeys.swift
rm SleepMind/Services/CodeAnalyzer.swift
rm SleepMind/Services/DepthEstimator.swift
rm SleepMind/Services/DigitalCourtTips.swift
rm SleepMind/Services/DocumentProcessor.swift
rm SleepMind/Services/EmbeddedInstinctsManager.swift
rm SleepMind/Services/FrequencyReferenceManager.swift
rm SleepMind/Services/WebScrapingEngine.swift
rm SleepMind/Services/TimeContextService.swift
```

**Networking (4 files)**
```bash
rm SleepMind/Services/SSHConnectionManager.swift
rm SleepMind/Services/SSHTypes.swift
rm SleepMind/Services/OpenSSHKeyDecryptor.swift
rm SleepMind/Services/CallScreeningService.swift
```

**Misc (7 files)**
```bash
rm SleepMind/Services/SoulGlobalsLoader.swift
rm SleepMind/Services/SparkEngineTypes.swift
rm SleepMind/Services/UnifiedMultiModalTypes.swift
rm SleepMind/Services/UserLoggerService.swift
rm SleepMind/Services/iOS18PrivacyManager.swift
rm SleepMind/Services/Authentication/EmailOTPService.swift
rm SleepMind/Services/Models/LiveTranslationTypes.swift
```

---

## Files to REVIEW (Owner Decision Required)

### AIKeySettingsView.swift
**Location**: `SleepMind/Features/Settings/AIKeySettingsView.swift`
**Status**: DEV-ONLY but user-visible
**Decision**: 
- KEEP if TestFlight beta needs ability to manage API keys
- REMOVE if want to hide from users (use build config instead)

### ConfigOrchestrator.swift
**Location**: `SleepMind/Services/ConfigOrchestrator.swift`
**Status**: UNCLEAR usage
**Decision**: Verify if used by runtime initialization. If not, DELETE.

### MultiModalModels.swift
**Location**: `SleepMind/Services/MultiModalModels.swift`
**Status**: UNUSED (imported by deleted files only)
**Decision**: DELETE (orphaned after multimodal removals)

---

## Verification Steps

After deletions, run:

```bash
# 1. Build check
xcodebuild build -project SleepMind.xcodeproj \
  -scheme SleepMind \
  -destination 'platform=iOS Simulator,name=iPhone 15 Pro'

# 2. Import errors
grep -r "import.*Community\|import.*Shop\|import.*Search\|import.*Coaching" \
  SleepMind --include="*.swift" | grep -v "^Binary"

# 3. Navigation verification
grep -r "Community\|Shop\|Search\|Coaching" \
  SleepMind/Features/Shell --include="*.swift"

# 4. Confirm 5-tab interface
grep -A 30 "enum SleepMindTab" SleepMind/Features/Shell/SleepMindMainView.swift
```

---

## Summary

| Category | Files | Action |
|----------|-------|--------|
| View Directories | 4 dirs | DELETE |
| Settings Views | 2 files | DELETE |
| Multimodal/Vision | 3 files | DELETE |
| Voice/Translation | 16 files | DELETE |
| Distributed Storage | 5 files | DELETE |
| Commerce | 2 files | DELETE |
| Advanced AI | 4 files | DELETE |
| Search (Vector) | 1 file | DELETE |
| DCourtKit Legacy | ~60 files | DELETE |
| **TOTAL TO REMOVE** | **~97 files** | **DELETE** |
| Review/Decision | 3 files | OWNER DECISION |

