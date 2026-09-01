# SleepMind v1 Scope Audit — Quick Reference

## Feature Status at a Glance

### ✅ IN SCOPE (Keep for v1)

**Core Features (18 directories)**
| Directory | Files | Status | SCOPE.md Ref |
|-----------|-------|--------|--------------|
| Briefing/ | 5 | ✓ Core hero screen | E1 |
| Coach/ | 3 | ✓ Top-level tab (AI coach chat) | NEW v1 |
| Diagnostics/ | 2 | ✓ Dev-only debug view | Profile |
| Errors/ | 1 | ✓ Supporting | Infrastructure |
| Health/ | 1 | ✓ Recovery detail views | D1 |
| Intelligence/ | 16 | ✓ All support v1 Workouts/Recovery | Supporting |
| N3Trigger/ | 22 | ✓✓✓ CORE overnight engine | CORE |
| Notifications/ | 1 | ✓ Supporting | Supporting |
| Nutrition/ | 9 | ✓ Meal logging | C1–C3 |
| Onboarding/ | 1 | ✓ Profile setup | A4 |
| Race/ | 8 | ✓ Race mode | F1–F2 |
| Recovery/ | 4 | ✓ Sleep & recovery tracking | D1–D2 |
| Settings/ | 5 | ✓ Account, notifications, privacy | G1–G3 |
| Shell/ | 4 | ✓ Root navigation (5-tab interface) | Navigation |
| Shared/ | 1 | ✓ Supporting (AppGroup) | Supporting |
| Subscription/ | 2 | ✓ Paywall (StoreKit 2) | Paid model |
| Watch/ | 4 | ✓ Watch companion | Companion |
| Workouts/ | 11 | ✓ Training logging | B1–B6 |
| **TOTAL** | **114 files** | **KEEP ALL** | — |

**Core Services (~30 files)**
- Health: HealthKitManager, HealthKitService, HealthKitBackfillService
- LLM: FoundationModelsWrapper, AnthropicAPIHandler, LLMSkills/*
- Firebase: SovvRTDB, SovvPushService
- Auth: UserManager + OAuth/Firebase extensions
- Core: BootStateManager, OnboardingManager, GlobalSettings, AnalyticsManager
- Crypto: KeychainManager, EncryptionService, AIKeychain
- Network: APIService, APIOrchestrator, NetworkStatusManager
- Other: Logger, CrashReportingManager, NotificationCenter, ExerciseSpriteService

---

### ❌ OUT OF SCOPE (Remove for v1)

**Feature Directories (4 directories, 6 files)**
| Directory | Files | Reason | Action |
|-----------|-------|--------|--------|
| Community/ | 4 | "No social/leaderboards" — explicit v1 exclusion | DELETE |
| Shop/ | 1 | Not in SCOPE.md; requires Vision/multimodal | DELETE |
| Search/ | 1 | Not in SCOPE.md v1 features | DELETE |
| Coaching/ | 1 | Superseded by Coach/; duplicate | DELETE |

**Settings Views (2 files)**
| File | Reason | Action |
|------|--------|--------|
| LanguagePickerView.swift | No i18n in v1 | DELETE |
| LiveChatView.swift | Not in SCOPE.md (optional) | DELETE/REVIEW |

**Services (97 files)**
| Category | Count | Examples | Action |
|----------|-------|----------|--------|
| Multimodal/Vision | 3 | MultiModalAI*, BodyAnalysis* | DELETE |
| Voice/Translation | 16 | VoiceService*, *Translation*, MLX* | DELETE |
| Distributed Storage | 5 | IPFS*, Arweave*, *Shard* | DELETE |
| Commerce | 2 | ProductRecommendation, CartValidation | DELETE |
| Advanced AI | 4 | AdvancedAnalytics, AutonomousProblem*, CoachingAgent* | DELETE |
| Search | 1 | VectorSearchService | DELETE |
| DCourtKit Legacy | ~60 | OpenAI*, HuggingFace*, *Boot*, *Stealth* | DELETE |

**TOTAL TO REMOVE**: ~105 files

---

## Key Statistics

| Metric | Count |
|--------|-------|
| Total View Files in Features/ | 114 |
| Total Service Files | 127 |
| **Kept for v1** | ~144 files (114 views + ~30 services) |
| **Removed for v1** | ~105 files |
| **Percentage to v1 Launch** | ~58% of codebase |

---

## Decision Matrix

### DEFINITELY REMOVE (No Review Needed)
- [ ] Community/ directory (violates "no social")
- [ ] Shop/ directory (not in scope)
- [ ] Search/ directory (not in scope)
- [ ] Coaching/ directory (superseded)
- [ ] LanguagePickerView.swift (no i18n)
- [ ] All Voice/Translation services (16 files)
- [ ] All Multimodal/Vision services (3 files)
- [ ] All Distributed Storage services (5 files)
- [ ] All Commerce services (2 files)
- [ ] All DCourtKit legacy strip candidates (~60 files per CLAUDE.md)

### OWNER REVIEW REQUIRED
- [ ] LiveChatView.swift — Keep for TestFlight support chat? (OWNER CALL)
- [ ] AIKeySettingsView.swift — Keep for dev key management? (OWNER CALL)
- [ ] ConfigOrchestrator.swift — Verify in-use before deletion (BRIEF CHECK)

---

## Main Views Architecture (v1)

```
SleepMind Root
├── Onboarding (auth + baseline)
│   └── BaselineAssessmentView
└── Main 5-Tab Interface
    ├── Today Tab
    │   ├── MorningBriefingView (E1)
    │   └── TodayWorkoutCard (workout suggestion)
    ├── Coach Tab
    │   └── CoachChatListView (AI coach chat)
    ├── Eat Tab
    │   ├── TodayNutritionView (C1)
    │   ├── AddMealView (C2)
    │   └── MacroTargetsView (C3)
    ├── Train Tab
    │   ├── WorkoutLibraryView (B6 + methodology picker)
    │   ├── WorkoutBuilderView (B2)
    │   ├── InWorkoutPlayerView (B3)
    │   └── PostWorkoutSummaryView (B5)
    └── Recovery Tab
        ├── RecoveryTabView (D1 + D2)
        ├── HealthMetricDetailView (detail drill-down)
        ├── PlateauAlertCard (plateau detection)
        ├── RecoveryMapView (recovery status)
        └── VolumeTrackingView (training volume)

Settings (Profile Avatar → Modal)
├── Subscription/Account (G1)
├── NotificationSettingsView (G2)
└── PrivacyDataView (G3)

Race Mode (accessible from Today/Race tab)
├── RaceReadinessView (F1)
└── TaperPlanView (F2)

Background (invisible to user)
├── N3Trigger (overnight engine) — CORE DIFFERENTIATOR
│   ├── SleepKitObserver (detect N3)
│   ├── OvernightPipeline (collect + process)
│   ├── ClaudeBriefingService (generate)
│   └── ProcessingOriginTelemetry (patent evidence)
└── Watch Companion (WatchConnectivityManager)
```

---

## Overnight Engine (Patent-Critical)

**Must Keep** (`Features/N3Trigger/` — 22 files)
- SleepKitObserver.swift — HealthKit N3 detection
- OvernightPipeline.swift — Main orchestration
- ClaudeBriefingService.swift — Claude API integration
- ProcessingOriginTelemetry.swift — **PATENT EVIDENCE** (processing_completed_during_sleep_vs_on_wake counter)
- All supporting components

**Why**: N3-triggered overnight processing is the patent-pending (IPOS C-02) differentiator. Must execute during sleep, not on-wake (reduce-to-practice requirement).

---

## Test Plan After Deletions

**Build**
```bash
xcodebuild build -project SleepMind.xcodeproj \
  -scheme SleepMind \
  -destination 'platform=iOS Simulator,name=iPhone 15 Pro'
```

**Navigation**
1. Onboarding → Auth → Baseline
2. Main 5-tab interface loads (Today/Coach/Eat/Train/Recovery)
3. Each tab accessible and functional
4. Settings accessible from Today avatar
5. No lingering references to deleted features

**Core Features**
1. Briefing: Generates and displays morning briefing
2. Workouts: Can create, start, log workout
3. Nutrition: Can log meal
4. Recovery: Can view sleep data + recovery trends
5. Race: Can set race date + view countdown
6. Notifications: Can enable briefing alert
7. Subscription: Can see paywall, start free trial

**Background**
1. N3 overnight engine initializes (check logs)
2. HealthKit permissions request works
3. Firebase auth works (sign-in flow)

---

## Files Per SCOPE.md Feature

| Feature | Screens | Directory | Files | Status |
|---------|---------|-----------|-------|--------|
| A. Onboarding | 4 | Onboarding/ | 1 | ✓ |
| B. Training | 6 | Workouts/ | 11 | ✓ |
| C. Nutrition | 3 | Nutrition/ | 9 | ✓ |
| D. Recovery | 2 | Recovery/ | 4 | ✓ |
| E. Briefing | 1 | Briefing/ | 5 | ✓ |
| F. Race | 2 | Race/ | 8 | ✓ |
| G. Settings | 3 | Settings/ | 5 | ✓ (2 to remove) |
| N3 Engine | N/A | N3Trigger/ | 22 | ✓ CORE |
| Coach Chat | N/A | Coach/ | 3 | ✓ NEW v1 |
| Watch | N/A | Watch/ | 4 | ✓ |
| Subscription | N/A | Subscription/ | 2 | ✓ |
| **TOTAL** | **~21** | **~11 dirs** | **74** | **✓** |

Supporting (Infrastructure)
- Shell/ (4), Health/ (1), Errors/ (1), Notifications/ (1), Shared/ (1), Intelligence/ (16), Diagnostics/ (2)

---

## Cleanup Phases

**Phase 1 (Pre-v1 Ship — This Week)**
- Remove 4 feature directories (Community, Shop, Search, Coaching)
- Remove 2 Settings views
- Remove ~97 service files (multimodal, voice, storage, legacy)
- Build test + deployment verification

**Phase 2 (Post-v1 Launch — Week 13+)**
- Audit imports + dead code
- Remove test files, example code
- Final cleanup of inherited components

