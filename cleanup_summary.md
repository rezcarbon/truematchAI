# v1 Out-of-Scope Services Cleanup Summary

## Deleted Files
✅ **DCourtKit/DCourtKit/Services/ModalityFusionEngine.swift** 
   - Phase 3 feature (multimodal processing not in v1)
   - Was returning placeholder/empty values
   - Not used anywhere in codebase (only mentioned in a comment)

✅ **SleepMind/SleepMind/Services/ModalityFusionEngine.swift**
   - Same Phase 3 feature, deleted from both codebases

## Kept Files (Used in v1)
✅ **IPFSStorageManager.swift** 
   - Retained: Used by StorageRedundancyManager and Storage configuration views
   - Not out-of-scope for v1

## Updated Phase 5b References (Marked OUT-OF-SCOPE)
✅ **DCourtKit/DCourtKit/Views/Components/ReturnGPT/RGUpgradeModalView.swift**
   - Changed: "Phase 5b — Upgrade-to-Plus modal" → "OUT-OF-SCOPE for v1 — Phase 5b placeholder"

✅ **DCourtKit/DCourtKit/Views/Components/ReturnGPT/RGSettingsContainer.swift**
   - Changed: "Phase 5b — wired container" → "OUT-OF-SCOPE for v1 — partial only"
   - Updated comment: Chat history backend wiring marked as Phase 5b+ out-of-scope

✅ **DCourtKit/DCourtKit/Views/Components/ReturnGPT/RGChambersTabContent.swift**
   - Changed: "Phase 5b+: wire to StoreKit" → "OUT-OF-SCOPE v1: StoreKit wiring (Phase 5b+)"

✅ **SleepMind/SleepMind/Views/Components/ReturnGPT/RGSettingsContainer.swift**
   - Changed: "Phase 5b" → "OUT-OF-SCOPE for v1"

✅ **SleepMind/SleepMind/Views/Components/ReturnGPT/RGUpgradeModalView.swift**
   - Changed: "Phase 5b" → "OUT-OF-SCOPE for v1"

## Updated Phase 3 Feature Markers (Marked OUT-OF-SCOPE)
✅ **DCourtKit/DCourtKit/Services/MultiModalOrchestrationEngine.swift**
   - Changed: "⚠️ PHASE 3 FEATURE" → "⚠️ OUT-OF-SCOPE v1: PHASE 3 FEATURE"
   - Clarified: returns placeholder values, deferred to Phase 3+

✅ **DCourtKit/DCourtKit/Services/MultiModalAdvancedCapabilities.swift**
   - Changed: "⚠️ PHASE 3 FEATURE" → "⚠️ OUT-OF-SCOPE v1: PHASE 3 FEATURE"
   - Clarified: returns placeholder values, deferred to Phase 3+

## Remaining Status
- All Phase 5b references now clearly marked as OUT-OF-SCOPE for v1
- All Phase 3 out-of-scope features clearly marked with ⚠️ OUT-OF-SCOPE v1 prefix
- No other significant "stub" or "placeholder" implementations that need cleanup for v1
- AppleFoundationLLMProviderStub retained: valid compatibility fallback for iOS <26

## Notes
- IPFSStorageManager was flagged for deletion but is actually used in v1 (StorageRedundancyManager + views), so retained
- MultiModal features are partial: Vision working, Audio/cross-modal Phase 3, now clearly marked
- SocialAndCommunityService.swift doesn't exist yet (wasn't found in search)
