# Manual Screenshot Save Guide
**Fastest Way: Save the 8 Screenshots from Chat**

All 8 screenshots have been captured and displayed above in the chat. Here's how to save them:

## Quick Steps (5 minutes total)

### For Each Screenshot (repeat 8 times):

1. **Find the screenshot in the chat** (scroll up to see them)
2. **Right-click on the image**
3. **Select "Save Image As..."**
4. **Navigate to:** `/Users/modvader/Documents/codebase/truematch/screenshots/`
5. **Save with the correct name:**

## Screenshots to Save (in order)

| # | Right-click on this... | Save as filename |
|---|---|---|
| 1 | Login page (clean form) | `01_login_page.png` |
| 2 | Admin dashboard (with metrics) | `02_admin_dashboard.png` |
| 3 | Recruiter command centre | `03_recruiter_dashboard.png` |
| 4 | Candidate dashboard (delta: +68) | `04_candidate_dashboard.png` |
| 5 | Chat interface (Admin tutorial) | `05_chat_interface.png` |
| 6 | Candidates list (6 candidates) | `06_assessment_results.png` |
| 7 | Positions list (4 open roles) | `07_pipeline_positions.png` |
| 8 | JD Simulation form | `08_jd_simulation.png` |

## Verification Checklist

After saving all 8 files, verify they're in the right place:

```bash
ls -lh /Users/modvader/Documents/codebase/truematch/screenshots/
```

You should see:
```
01_login_page.png
02_admin_dashboard.png
03_recruiter_dashboard.png
04_candidate_dashboard.png
05_chat_interface.png
06_assessment_results.png
07_pipeline_positions.png
08_jd_simulation.png
```

## Done! ✅

Once all 8 files are saved:
1. Open your presentation software
2. Follow `TRUEMATCH_INTEGRATED_SLIDES.md` outline
3. Embed screenshots in appropriate slides
4. Add speaker notes
5. Rehearse 2-3 times

**Total time remaining:** ~3 hours (slide design + rehearsal)

---

## Alternative: If Manual Download Fails

If you have trouble right-clicking on images in chat, you can:

1. Take screenshots of your own browser window showing each page
2. Save them with the same filenames
3. Place in `/Users/modvader/Documents/codebase/truematch/screenshots/`

**URLs to capture:**
- http://localhost:3001/login
- http://localhost:3001/admin/dashboard
- http://localhost:3001/recruiter/dashboard
- http://localhost:3001/candidate/dashboard
- http://localhost:3001/chat
- http://localhost:3001/recruiter/candidates
- http://localhost:3001/recruiter/positions
- http://localhost:3001/recruiter/jd-simulation

Use Mac screenshot shortcut: **Shift + Cmd + 4** to select and save each one.

---

**This is the fastest path forward! ✅**
