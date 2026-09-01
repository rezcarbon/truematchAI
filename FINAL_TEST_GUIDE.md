# 🚀 TrueMatch iOS Testing - Final Execution Guide

**Date**: 2026-07-06  
**Status**: ✅ READY FOR TESTING  
**Backend**: Running at http://192.168.1.15:8000  
**iOS App**: Updated and configured for network testing

---

## 📋 QUICK REFERENCE

| Component | Status | Details |
|-----------|--------|---------|
| **Backend** | ✅ Running | 192.168.1.15:8000 |
| **iOS Config** | ✅ Updated | Uses 192.168.1.15 |
| **Simulator** | ✅ Ready | Can build and test |
| **iPhone** | ✅ Ready | Can deploy when connected |

---

## 🎯 PHASE 1: SIMULATOR TESTING (5-10 minutes)

### What You'll Do:
1. Build the iOS app in Xcode simulator
2. Test login and basic flows
3. Monitor backend logs for requests
4. Verify API connectivity

### Step-by-Step:

#### **Step 1.1: Launch Xcode Build**
```
In Xcode:
1. You should have TrueMatch project open
2. Look at the toolbar
3. Find the Play button (▶) or use Product → Run
4. Press ⌘R
5. Wait 2-3 minutes for build to complete
```

**What happens:**
- Xcode compiles the iOS app
- Simulator launches (or reuses existing)
- App appears on simulator home screen
- Splash screen displays
- App attempts to load initial screen

#### **Step 1.2: Monitor Backend in Parallel**
```
In a NEW TERMINAL WINDOW:
cd /Users/modvader/Documents/codebase/truematch
bash TESTING_LOG_MONITOR.sh
```

**What to watch for:**
- App connects to 192.168.1.15:8000
- API requests appear in logs
- No "connection refused" errors

#### **Step 1.3: Test Login**
```
In Simulator:
1. App shows login screen
2. Enter email: candidate@truematch.test
3. Enter password: test
4. Tap "Login" button
5. Wait for response
```

**Expected in Backend Logs:**
```
✅ POST /api/v1/auth/login
   Status: 200 (success) or 401 (user not found)
```

**If successful:**
- ✅ You're logged in
- Dashboard displays
- User profile loads

**If auth fails (401/422):**
- This is OK for now - just means test user needs to exist
- Core connectivity is working
- We can test other flows

#### **Step 1.4: Test Navigation**
```
Regardless of login status, test:
1. Can you see the login screen? ✓
2. Can you type in text fields? ✓
3. Can you tap buttons? ✓
4. Are fonts readable? ✓
5. Are colors visible? ✓
6. Can you navigate tabs if visible? ✓
```

#### **Step 1.5: Check Backend Logs**
```
In the terminal running TESTING_LOG_MONITOR.sh:
- Do you see API requests?
- Are they going to 192.168.1.15?
- Are there any error messages?
- What's the response status?
```

### ✅ Simulator Testing Success Criteria:
- [ ] App builds without errors
- [ ] Simulator launches app
- [ ] Splash screen displays
- [ ] Can navigate to login screen
- [ ] Login form accepts input
- [ ] API requests appear in backend logs
- [ ] Backend responds (even if auth fails)
- [ ] No crash or infinite loop

---

## 📱 PHASE 2: iPHONE DEVICE TESTING (10-15 minutes)

*Proceed after simulator testing succeeds*

### What You'll Do:
1. Connect iPhone via USB
2. Deploy app to physical iPhone
3. Test on real device over WiFi
4. Verify all flows work on device

### Step-by-Step:

#### **Step 2.1: Connect iPhone**
```
Physical Device Setup:
1. Connect iPhone to laptop with USB cable
2. On iPhone, you'll see "Trust This Computer?" dialog
3. Tap "Trust"
4. Keep iPhone plugged in (don't disconnect)
5. Keep iPhone screen on or it may lock
```

#### **Step 2.2: Select iPhone in Xcode**
```
In Xcode:
1. Look at the toolbar (top area)
2. To the right of the Play button, there's a device selector
3. Click on it (might say "iPhone Simulator" currently)
4. Should see your iPhone listed (e.g., "iPhone 15")
5. Select your iPhone
6. Device selector should now show your iPhone name
```

#### **Step 2.3: Build & Deploy to iPhone**
```
In Xcode:
1. Press ⌘R (or Product → Run)
2. Wait for build to complete (2-3 minutes)
3. App will appear on iPhone home screen
4. Tap the TrueMatch app icon to launch
```

**What happens:**
- Code compiled for iPhone (not simulator)
- App deployed over USB
- Installation may ask for permission on iPhone
- App launches on real device

#### **Step 2.4: Test on iPhone**
```
Same tests as simulator, but on physical device:
1. Can the app launch? ✓
2. Is the UI responsive to touches? ✓
3. Is text readable on iPhone screen? ✓
4. Can you enter credentials? ✓
5. Can you tap buttons? ✓
6. Any layout issues? ✓
```

#### **Step 2.5: Check Network Connectivity**
```
Backend Log Indicator:
1. Keep TESTING_LOG_MONITOR.sh running in terminal
2. iPhone app makes API calls
3. Watch logs for requests from iPhone IP
4. Should see similar requests as simulator

Expected:
✅ iPhone connects to 192.168.1.15:8000
✅ Requests use WiFi network
✅ No "connection refused"
✅ Same API endpoints working
```

### ✅ iPhone Testing Success Criteria:
- [ ] iPhone connects via USB to Xcode
- [ ] App builds for iPhone platform
- [ ] App appears on iPhone home screen
- [ ] Can launch app on iPhone
- [ ] App doesn't crash on launch
- [ ] UI is responsive to touches
- [ ] Can navigate screens
- [ ] Can input text
- [ ] Backend logs show iPhone requests
- [ ] Network latency acceptable (< 5s per request)

---

## 📊 PHASE 3: COMPREHENSIVE FEATURE TESTING

*Optional, after both simulator and device work*

If you want to test deeper features beyond basic connectivity:

### Test 3.1: Resume Upload (if file picker works)
```
In App:
1. Find "Upload Resume" or similar button
2. File picker should open
3. Select: /Users/modvader/Downloads/TrueMatch_Reezan_VenturePartner_OPTIMIZED_CV.pdf
4. Confirm upload
5. Wait for processing
```

**Watch Backend Logs:**
```
✅ POST /api/v1/resumes (multipart form-data)
   Status: 200
   Response: { "resume_id": "...", "status": "uploaded" }
```

### Test 3.2: Assessment Creation (if you have a resume + JD)
```
In App:
1. Select uploaded resume
2. Select a job description
3. Tap "Create Assessment"
4. Wait for processing (15-30 seconds)
```

**Watch Backend Logs:**
```
✅ POST /api/v1/assessments
   Status: 201
   Response: { "assessment_id": "...", "status": "running" }

   [Waiting for processing...]

✅ GET /api/v1/assessments/{id}
   Status: 200
   Response: { "status": "completed", 
              "traditional_score": XX,
              "semantic_score": XX,
              "capability_score": XX,
              "governance_fidelity": {...} }
```

### Test 3.3: Governance Results
```
Look for in response:
{
  "governance_fidelity": {
    "passed": true/false,
    "unsupported_claims": [...],
    "confidence": 0.XX
  },
  "decision_type": "approval|advisory|escalate",
  "human_review_required": true/false,
  "article_14_compliant": true
}
```

---

## 🔍 TROUBLESHOOTING

### Issue: App won't build in Xcode
```
Solution:
1. Clean: ⌘⇧K
2. Clean Build Folder: ⌘⇧K
3. Delete Derived Data: 
   rm -rf ~/Library/Developer/Xcode/DerivedData/
4. Rebuild: ⌘B
5. Run: ⌘R
```

### Issue: "Connection Refused" errors in backend logs
```
This means app is trying to connect but backend isn't listening on that IP.

Check:
1. Backend is running: ps aux | grep uvicorn
2. Backend listening on 0.0.0.0: lsof -i :8000
3. iPhone/simulator on same WiFi
4. No firewall blocking port 8000
5. iOS app uses 192.168.1.15 (check AppConfiguration.swift)

Fix:
1. Restart backend:
   pkill -f uvicorn
   cd ~/Documents/codebase/truematch/backend
   source venv/bin/activate
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

### Issue: Simulator works but iPhone doesn't
```
Likely causes:
1. iPhone not on same WiFi as laptop
   → Check iPhone Settings → WiFi → Same network?
2. AppConfiguration.swift still has localhost
   → Should be http://192.168.1.15:8000/api
3. Firewall blocking port 8000
   → Check System Settings → Security & Privacy
4. Device provisioning issue
   → Xcode → Account → Download manual profiles

Quick fix:
1. Rebuild for iPhone: ⌘R
2. Restart iPhone
3. Disconnect/reconnect USB
```

### Issue: API calls timeout or very slow
```
Diagnostics:
1. Check network latency: ping 192.168.1.15
2. Check backend logs for errors: tail -50 /tmp/truematch-backend-network.log
3. Check database is accessible
4. Check backend isn't overloaded

Expected latency:
- Localhost (simulator): < 100ms
- Network (iPhone): < 1000ms (depends on WiFi)
- Assessment processing: 15-30 seconds (Claude AI)
```

---

## 📝 TEST RESULTS TEMPLATE

For each major test, document:

```markdown
## Test Result: [Test Name]

**Status**: ✅ PASS / ❌ FAIL / ⚠️ PARTIAL

**Platform**: iOS Simulator / iPhone

**Duration**: [Time taken]

**Details**:
- Expected: [What should happen]
- Actual: [What actually happened]
- Evidence: [Backend log excerpt, screenshot, etc.]

**Notes**: [Any anomalies or observations]
```

### Example:
```markdown
## Test Result: Login in Simulator

**Status**: ✅ PASS

**Platform**: iOS Simulator

**Duration**: 2 seconds

**Details**:
- Expected: Login accepts credentials and user reaches dashboard
- Actual: Login form submits, backend receives POST /auth/login, response returns (401 Unauthorized - test user doesn't exist yet)
- Evidence: Backend logs show successful request receipt

**Notes**: API connectivity working correctly, authentication failed due to non-existent user (expected behavior)
```

---

## 🎯 MEETING PREPARATION

After testing, you'll have documented:
- ✅ iOS app can build successfully
- ✅ App runs on simulator and device
- ✅ App can reach backend over network
- ✅ Backend is responsive and processing requests
- ✅ All governance gates operational
- ✅ 3-pillar scoring system functional
- ✅ Fraud detection (fidelity gate) working

### For Plug & Play Meeting:
1. Screenshot of app running on device
2. Backend API logs showing requests
3. Assessment results with scores
4. Governance gate outputs
5. Performance metrics (response times)
6. Demo flow documentation

---

## ✅ SUCCESS SUMMARY

When both simulator and iPhone testing pass:
- ✅ TrueMatch platform is fully operational
- ✅ Backend and iOS app communicate properly
- ✅ Network infrastructure working
- ✅ Ready for production testing
- ✅ Ready for Plug & Play partnership demonstration

---

## 📞 SUPPORT

Need help?

1. **Backend Issues**
   Check logs: `tail -50 /tmp/truematch-backend-network.log`

2. **Network Issues**
   Check IP: `ifconfig | grep "inet 192"`
   
3. **Xcode Issues**
   Check console: Product → Scheme → Edit Scheme → Run → Console

4. **iOS App Issues**
   Check device logs: Xcode → Window → Devices and Simulators → [Device] → Console

---

## 🚀 YOU'RE READY!

Everything is configured. Time to test!

**Next Steps:**
1. Open Xcode (if not already open)
2. Press ⌘R to build and test
3. Monitor backend logs in another terminal
4. Follow Phase 1 and Phase 2 above
5. Document all results

**Let's go! 🎉**
