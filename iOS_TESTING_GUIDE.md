# 🍎 TrueMatch iOS Testing Guide
**Network Configuration**: Ready for Simulator & iPhone Testing  
**Backend**: Accessible at http://192.168.1.15:8000  
**Status**: ✅ All systems ready

---

## YOUR NETWORK SETUP

| Component | Address | Port | Status |
|-----------|---------|------|--------|
| Laptop IP | 192.168.1.15 | — | ✅ Verified |
| Backend API | 192.168.1.15 | 8000 | ✅ Running |
| Frontend Web | 192.168.1.15 | 3000 | ✅ Running |
| iOS Simulator | localhost | 8000 | ✅ Can access |
| iPhone (on WiFi) | 192.168.1.15 | 8000 | ✅ Can access |

---

## PHASE 1: TEST IN SIMULATOR (5-10 minutes)

### Step 1: Build in Xcode
```
1. Xcode should be open with TrueMatch project
2. Select Product → Run (⌘R)
   OR click the Play button (▶) in toolbar
3. Wait for build to complete (2-3 minutes)
4. Simulator will launch with the app
```

### Step 2: Test Core Flows
- [ ] **Splash Screen**: App loads properly
- [ ] **Login Screen**: Form displays correctly
- [ ] **Test Login**: 
  - Email: candidate@truematch.test
  - Password: (try any password, should validate against backend)
- [ ] **Home Screen**: Dashboard loads
- [ ] **Navigation**: Can navigate between tabs
- [ ] **Chat**: Chat interface visible and responsive
- [ ] **CV Upload**: Can see file picker or upload interface

### Step 3: Monitor Backend Logs
```bash
# In a terminal, watch backend logs:
tail -f /tmp/truematch-backend-network.log

# You should see API requests from simulator like:
# GET /api/v1/auth/me
# POST /api/v1/auth/login
# etc.
```

---

## PHASE 2: TEST ON PHYSICAL iPhone (10-15 minutes)

### Step 1: Connect iPhone
1. **USB Connection**: Connect iPhone to laptop with USB cable
2. **Trust**: On iPhone, tap "Trust" when prompted
3. **Xcode Detection**: iPhone should appear in Xcode's device list

### Step 2: Select iPhone as Target
1. In Xcode toolbar, select your iPhone device (not simulator)
2. You should see: "iPhone (15.x)" or your actual iPhone model

### Step 3: Update iOS App Configuration
1. **Find API Configuration File** (likely one of):
   - `App/Config.swift`
   - `App/AppDelegate.swift`
   - `Core/Network/APIClient.swift`
   - `Utilities/APIConfiguration.swift`

2. **Update API Host**:
   - Find: `API_HOST = "localhost"` or `API_HOST = "127.0.0.1"`
   - Change to: `API_HOST = "192.168.1.15"`
   - Ensure port 8000 is set

3. **Example change**:
   ```swift
   // Before:
   let API_BASE_URL = "http://localhost:8000/api/v1"
   
   // After:
   let API_BASE_URL = "http://192.168.1.15:8000/api/v1"
   ```

### Step 4: Build & Deploy to iPhone
1. Press ⌘R (or Product → Run)
2. Wait for build and deployment (2-3 minutes)
3. App will appear on iPhone home screen
4. Tap app icon to launch

### Step 5: Test iPhone Flows
- [ ] **Splash Screen**: App loads on iPhone
- [ ] **Network Connection**: No connection errors
- [ ] **Login Screen**: Form displays correctly
- [ ] **Test Login**: Enter test credentials
- [ ] **Dashboard**: View assessments
- [ ] **Resume Upload**: Upload CV from Files app
- [ ] **Assessment Flow**: Create assessment against JD
- [ ] **Chat**: Test chat interface
- [ ] **Navigation**: Swipe between tabs

---

## TESTING SCENARIOS

### Scenario 1: User Login (Both Platforms)
**Test Credentials**:
```
Email: candidate@truematch.test
Password: test
Role: Candidate
```

**Expected Flow**:
1. Enter email/password
2. Backend validates (should see request in logs)
3. Token returned
4. User logged in
5. Dashboard visible

### Scenario 2: Resume Upload
**Test Flow**:
1. On dashboard, find "Upload Resume" button
2. Select your resume PDF:
   - `/Users/modvader/Downloads/TrueMatch_Reezan_VenturePartner_OPTIMIZED_CV.pdf`
3. File uploads to backend (`POST /api/v1/resumes`)
4. Confirmation message appears
5. Resume appears in candidate list

### Scenario 3: Create Assessment
**Test Flow**:
1. Navigate to Assessments
2. Select a job description (from backend database)
3. Click "Create Assessment"
4. System processes:
   - Parses resume
   - Calculates 3-pillar scores
   - Runs governance gates
5. Results display:
   - Traditional ATS score
   - Semantic match score
   - Capability score
   - Governance results

### Scenario 4: Chat Interface
**Test Flow**:
1. Open Chat tab
2. See previous conversation history (if any)
3. Type a question (e.g., "What skills should I learn?")
4. Message sends to backend
5. AI response appears
6. Chat history persists across sessions

---

## DEBUGGING IF ISSUES OCCUR

### Connection Issues
```bash
# Test connectivity from laptop:
curl http://192.168.1.15:8000/docs

# Check backend is listening on all interfaces:
lsof -i :8000

# iPhone on same WiFi network?
# Settings → WiFi → Should show same WiFi as laptop
```

### Backend Logs
```bash
# Watch real-time logs:
tail -f /tmp/truematch-backend-network.log

# Search for errors:
grep -i "error\|exception" /tmp/truematch-backend-network.log

# See recent requests:
tail -50 /tmp/truematch-backend-network.log
```

### CORS Issues (iPhone can't connect)
If iPhone can't connect, check:
1. Backend CORS settings allow iPhone's network origin
2. Backend is listening on 0.0.0.0 (not 127.0.0.1)
3. Firewall isn't blocking port 8000
4. iPhone and laptop on same WiFi network

### Build Issues
1. In Xcode, clean: ⌘⇧K
2. Clean build folder: ⌘⇧K
3. Delete derived data: ~/Library/Developer/Xcode/DerivedData/
4. Rebuild: ⌘B

---

## SUCCESS CHECKLIST

### Simulator Testing ✓
- [ ] App builds without errors
- [ ] Splash screen displays
- [ ] Can navigate to login screen
- [ ] Form fields accept input
- [ ] Can see backend requests in logs

### iPhone Testing ✓
- [ ] iPhone connects via USB to Xcode
- [ ] API endpoint updated to 192.168.1.15
- [ ] App builds for iPhone
- [ ] App appears on iPhone home screen
- [ ] App launches without crashes
- [ ] Can navigate between screens
- [ ] Backend requests visible in logs
- [ ] No "connection refused" errors

### End-to-End Testing ✓
- [ ] Simulator: Full user flow works
- [ ] iPhone: Full user flow works
- [ ] Resume upload succeeds
- [ ] Assessments calculate correctly
- [ ] Chat sends/receives messages
- [ ] Governance gates validate assessments

---

## NEXT STEPS AFTER TESTING

1. **Record Results**
   - Note which flows work on simulator
   - Note which flows work on iPhone
   - Document any differences

2. **Identify Gaps**
   - Missing features visible in testing?
   - Performance issues?
   - UI/UX improvements needed?

3. **Integration Testing**
   - Test with your actual resume
   - Test against real job descriptions
   - Verify all 3 pillars scoring

4. **Production Readiness**
   - Performance profiling
   - Memory usage on iPhone
   - Battery impact
   - Network latency

---

## QUICK REFERENCE

**Start Simulator**: ⌘R in Xcode  
**Deploy to iPhone**: ⌘R with iPhone selected  
**View Logs**: `tail -f /tmp/truematch-backend-network.log`  
**Backend Health**: `curl http://192.168.1.15:8000/docs`  
**Stop Backend**: `pkill -f uvicorn`  
**Restart Backend**: `source venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`

---

## SUPPORT

If you encounter issues:
1. Check backend logs
2. Verify iPhone/laptop on same WiFi
3. Confirm API endpoint is 192.168.1.15:8000
4. Ensure backend process is running
5. Check Xcode build output for errors

**You're ready to test! 🚀**

