# TrueMatch Screenshot Capture Guide
**Quick Manual Guide** | Estimated Time: 10-15 minutes

---

## ✅ SERVERS STATUS

Frontend: `http://localhost:3001` ✅  
Backend: `http://localhost:8000` (starting...)

---

## 🎯 WHAT TO CAPTURE (8 Core Screenshots)

Each screenshot should show the UI clearly for your slide deck.

### 1. **Login Page** (2 min)
**URL:** `http://localhost:3001/login`
- **What to show:** Clean login form, TrueMatch branding
- **Screenshot name:** `01_login_page.png`
- **Tip:** Take screenshot at full desktop size (1920x1080 or similar)

### 2. **Admin Dashboard** (2 min)
**URL:** `http://localhost:3001/admin/dashboard`
- **Credentials:** rez@mustafarai.com / Immortal
- **What to show:** System health metrics, governance status, KPIs
- **Screenshot name:** `02_admin_dashboard.png`
- **Tip:** Scroll to show full dashboard layout

### 3. **Recruiter Dashboard** (2 min)
**URL:** `http://localhost:3001/recruiter/dashboard`
- **What to show:** Command centre, task strip, active positions
- **Screenshot name:** `03_recruiter_dashboard.png`
- **Tip:** This is the main hiring command centre

### 4. **Candidate Dashboard** (2 min)
**URL:** `http://localhost:3001/candidate/dashboard`
- **What to show:** Recent assessments, recommendations, matched jobs
- **Screenshot name:** `04_candidate_dashboard.png`
- **Tip:** Shows career development features

### 5. **Chat Interface** (2 min)
**URL:** `http://localhost:3001/chat`
- **What to show:** Claude conversation interface
- **Screenshot name:** `05_chat_interface.png`
- **Tip:** Type a sample question to show active chat

### 6. **Assessment Results** (2 min)
**URL:** `http://localhost:3001/recruiter/candidates`
- **What to show:** Candidate assessments with 3-signal scores
- **Screenshot name:** `06_assessment_results.png`
- **Tip:** Click on a candidate to show detailed assessment

### 7. **Pipeline Kanban** (2 min)
**URL:** `http://localhost:3001/recruiter/positions`
- **What to show:** Drag-drop pipeline with candidate cards
- **Screenshot name:** `07_pipeline_kanban.png`
- **Tip:** Key visual of recruiter workflow

### 8. **JD Quality Analysis** (2 min)
**URL:** `http://localhost:3001/recruiter/jd-simulation`
- **What to show:** JD scoring interface with Fix recommendations
- **Screenshot name:** `08_jd_analysis.png`
- **Tip:** Shows AI-powered JD improvement feature

---

## 📸 HOW TO CAPTURE SCREENSHOTS

### **Method 1: Mac Built-in (Fastest)**
1. Press `Shift + Cmd + 4`
2. Click and drag to select the browser window
3. Screenshot saves to Desktop
4. Move to: `/Users/modvader/Documents/codebase/truematch/screenshots/`
5. Rename to match format above (01_login_page.png, etc.)

### **Method 2: Chrome DevTools**
1. Open Chrome DevTools: `Cmd + Option + I`
2. Click Menu (3 dots) → More tools → Screenshots → Capture full page
3. Save with proper name (01_login_page.png, etc.)

### **Method 3: Automated Script (if Selenium installed)**
```bash
cd /Users/modvader/Documents/codebase/truematch/
pip install selenium
python capture_screenshots.py
```
This will automatically capture all 10 screenshots.

---

## 🚀 QUICK FLOW

**1. Open Browser:**
```
Open Chrome
Go to http://localhost:3001/login
```

**2. Create Screenshots Folder:**
```bash
mkdir -p /Users/modvader/Documents/codebase/truematch/screenshots
```

**3. For Each Screenshot:**
1. Navigate to URL
2. Login with credentials (if needed)
3. Wait 2-3 seconds for page to fully load
4. Take screenshot (Shift + Cmd + 4)
5. Save as `01_login_page.png`, `02_admin_dashboard.png`, etc.

**4. Move to Folder:**
```bash
mv ~/Desktop/*login_page.png /Users/modvader/Documents/codebase/truematch/screenshots/
# Repeat for all screenshots
```

---

## 🔑 TEST CREDENTIALS

**Admin:**
```
Email: rez@mustafarai.com
Password: Immortal
```

**Recruiter (if available):**
```
Email: recruiter@truematch.local
Password: recruiter123
```

**Candidate:**
```
Email: candidate@truematch.local
Password: candidate123
```

---

## 💡 SCREENSHOT BEST PRACTICES

✅ **DO:**
- Capture at full screen or large window size
- Show complete UI elements
- Include navigation/headers
- Wait 2-3 seconds for page to fully load
- Use consistent window size (1920x1080 ideal)

❌ **DON'T:**
- Capture with browser tabs/toolbars showing private info
- Take zoomed-in partial screenshots
- Include password in any screenshot
- Take blurry/out-of-focus images

---

## 📂 WHERE TO SAVE

Save all screenshots to:
```
/Users/modvader/Documents/codebase/truematch/screenshots/
```

File naming format:
```
01_login_page.png
02_admin_dashboard.png
03_recruiter_dashboard.png
04_candidate_dashboard.png
05_chat_interface.png
06_assessment_results.png
07_pipeline_kanban.png
08_jd_analysis.png
```

---

## ✅ VERIFICATION

After capturing, verify all files:
```bash
ls -lh /Users/modvader/Documents/codebase/truematch/screenshots/
```

Should show:
```
01_login_page.png (100-200 KB)
02_admin_dashboard.png (150-250 KB)
03_recruiter_dashboard.png (150-250 KB)
04_candidate_dashboard.png (150-250 KB)
05_chat_interface.png (100-200 KB)
06_assessment_results.png (150-250 KB)
07_pipeline_kanban.png (150-300 KB)
08_jd_analysis.png (150-250 KB)
```

---

## ⏱️ TIMING

**Total time:** 10-15 minutes for all 8 screenshots

**Timeline:**
- 1 min: Navigate & login
- 2 min per screenshot (includes wait time)
- 1 min: Organize files

---

## 🆘 TROUBLESHOOTING

**"Page won't load"**
- Wait 3-5 seconds for page to fully render
- Refresh page (Cmd + R)
- Check backend is running: `curl http://localhost:8000/docs`

**"Login fails"**
- Verify credentials above
- Clear browser cache (Cmd + Shift + Delete)
- Check backend is ready

**"Screenshot quality poor"**
- Ensure window is maximized
- Use Shift + Cmd + 4 for better control
- Try Chrome DevTools screenshot method

---

## 🎬 NEXT STEPS AFTER CAPTURING

1. ✅ Capture all 8 screenshots
2. ✅ Save to `/truematch/screenshots/` folder
3. ✅ Embed in your PowerPoint/Keynote slides
4. ✅ Follow slide outline from `TRUEMATCH_INTEGRATED_SLIDES.md`
5. ✅ Add speaker notes
6. ✅ Rehearse (2-3 times)

---

**Estimated total time to presentation-ready: 4-5 hours**
- Screenshots: 15 minutes
- Slide design: 2-3 hours
- Speaker notes: 30 minutes
- Rehearsal: 45 minutes

Good luck! 🚀
