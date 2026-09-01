# Priority 2 Quick Reference

## 🚀 Quick Start

### Start Backend
```bash
cd ~/Desktop/TrueMatch/backend
alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Start Frontend
```bash
cd ~/Desktop/TrueMatch/web
npm run dev
```

### Access Pages
- **Pipeline:** http://localhost:3000/recruiter/pipeline
- **Three-Signal Analytics:** http://localhost:3000/admin/analytics/three-signal
- **Pipeline Analytics:** http://localhost:3000/admin/analytics/pipeline
- **Source Analytics:** http://localhost:3000/admin/analytics/sources

---

## 📁 Files Created/Modified

### Priority 2A: API Integration

#### New Files
```
web/src/hooks/useATSPipeline.ts
web/src/hooks/useATSInterviews.ts
```

#### Modified Files
```
web/src/app/recruiter/pipeline/page.tsx  (now uses real API data)
```

### Priority 2B: Components

#### New Files
```
web/src/components/ats/CandidateDetailModal.tsx
web/src/components/ats/ScorecardForm.tsx
```

### Priority 2C: Analytics

#### New Files
```
web/src/app/admin/analytics/three-signal/page.tsx
```

#### Modified Files
```
web/src/app/admin/layout.tsx  (added navigation links)
```

---

## 🔗 API Endpoints

### Interview Operations
```
POST   /api/proxy/ats/interviews
       Schedule an interview

GET    /api/proxy/ats/applications/{applicationId}/interviews
       List interviews for a candidate

POST   /api/proxy/ats/scorecards
       Submit interview scorecard

GET    /api/proxy/ats/scorecards/{scorecardId}
       Get scorecard details
```

### Pipeline Operations
```
GET    /api/proxy/ats/positions/{positionId}/pipeline
       Get candidates in pipeline

PATCH  /api/proxy/ats/applications/{applicationId}
       Update candidate stage

GET    /api/proxy/assessments?resume_id=X&position_id=Y
       Get three-signal scores
```

---

## 🎯 Component Usage

### useATSPipeline Hook
```typescript
import { useATSPipeline } from '@/hooks/useATSPipeline';

const { candidates, loading, error, updateStage, refetch } = 
  useATSPipeline(positionId);

// Update candidate stage
await updateStage(applicationId, 'technical');
```

### useATSInterviews Hooks
```typescript
import { 
  useScheduleInterview, 
  useApplicationInterviews,
  useSubmitScorecard 
} from '@/hooks/useATSInterviews';

// Schedule interview
const { scheduleInterview, loading } = useScheduleInterview();
await scheduleInterview(appId, positionId, interviewerIds, 'zoom');

// Fetch interviews
const { interviews, fetchInterviews } = useApplicationInterviews(appId);

// Submit scorecard
const { submitScorecard, loading } = useSubmitScorecard();
await submitScorecard(interviewId, scores, feedback, recommendation);
```

### CandidateDetailModal
```typescript
import { CandidateDetailModal } from '@/components/ats/CandidateDetailModal';

<CandidateDetailModal
  applicationId={candidate.id}
  candidateName={candidate.name}
  candidateEmail={candidate.email}
  keywordScore={candidate.keywordScore}
  semanticScore={candidate.semanticScore}
  capabilityScore={candidate.capabilityScore}
  resumeText={candidate.resumeText}
  appliedAt={candidate.appliedAt}
  source={candidate.source}
  stage={candidate.stage}
  onClose={() => setShowDetailModal(false)}
  onScheduleInterview={() => setShowScheduler(true)}
/>
```

### ScorecardForm
```typescript
import { ScorecardForm } from '@/components/ats/ScorecardForm';

<ScorecardForm
  interviewId={interviewId}
  candidateName={candidateName}
  positionTitle={positionTitle}
  onSuccess={() => handleSuccess()}
  onClose={() => setShowScorecard(false)}
/>
```

---

## 📊 Three-Signal Analytics

### Score Interpretation
- **Green (80+):** Strong match for position
- **Yellow (60-79):** Acceptable candidate
- **Red (<60):** Likely not a fit

### Signals
1. **Keyword Match** - Resume keyword overlap with JD
2. **Semantic Match** - Concept and meaning alignment
3. **Capability Assessment** - LLM evaluation of actual abilities

### What the Dashboard Shows
- Average scores for each signal
- Distribution of scores (80-100, 60-79, 0-59)
- Signal alignment (perfect/good/divergent)
- Candidate ranking by overall fit
- Trend indicators vs. average
- Actionable insights

---

## ✅ Testing Checklist

### 2A: API Integration
- [ ] Load http://localhost:3000/recruiter/pipeline
- [ ] Verify candidates display in Kanban
- [ ] Check three-signal scores appear
- [ ] Drag candidate to new stage
- [ ] Verify API call updates data
- [ ] Check toast notification appears

### 2B: Components
- [ ] Click on candidate name → detail modal opens
- [ ] Check Overview tab shows scores
- [ ] Check Resume tab shows content
- [ ] Check Interviews tab loads
- [ ] Click "Schedule Interview" from modal
- [ ] Fill scorecard form with all fields
- [ ] Submit scorecard → success toast

### 2C: Analytics
- [ ] Load http://localhost:3000/admin/analytics/three-signal
- [ ] Verify KPI cards show averages
- [ ] Check score distribution chart
- [ ] Verify signal alignment shows correct badges
- [ ] Check candidate ranking
- [ ] Verify insights are displayed

---

## 🔍 Data Flow

### Kanban Pipeline
```
useATSPipeline hook
  ↓ fetch /api/proxy/ats/positions/{id}/pipeline
  ↓ enrich with assessment scores
  ↓ update local state
  ↓ PipelineBoard displays candidates
  ↓ user drag-and-drop
  ↓ updateStage() called
  ↓ PATCH /api/proxy/ats/applications/{id}
  ↓ optimistic update + refetch
```

### Candidate Details
```
CandidateDetailModal renders
  ↓ user clicks "Interviews" tab
  ↓ useApplicationInterviews.fetchInterviews()
  ↓ GET /api/proxy/ats/applications/{id}/interviews
  ↓ interview list displayed
```

### Scorecard Submission
```
ScorecardForm opens
  ↓ user rates competencies
  ↓ provides feedback
  ↓ selects recommendation
  ↓ clicks Submit
  ↓ useSubmitScorecard() called
  ↓ POST /api/proxy/ats/scorecards
  ↓ success toast + modal closes
```

---

## 🐛 Troubleshooting

### Issue: Candidates not loading
**Solution:** 
- Check backend is running on port 8000
- Verify position exists (check database)
- Check browser console for API errors
- Run `GET /api/proxy/ats/positions/{positionId}/pipeline` in Postman

### Issue: Three-signal scores empty
**Solution:**
- Ensure assessments have been run
- Check `GET /api/proxy/assessments` endpoint
- Verify resume_id and position_id are correct

### Issue: Drag-and-drop not working
**Solution:**
- Check that candidateId matches application ID
- Verify updateStage() is being called
- Check network tab for PATCH request
- Verify backend returns success response

### Issue: Scorecard form won't submit
**Solution:**
- Ensure all 5 competencies are rated
- Check that recommendation is selected
- Verify interviewId is correct
- Check console for validation errors

---

## 📚 Documentation

### Detailed Docs
- **PRIORITY_2_IMPLEMENTATION_STATUS.md** - Full implementation details
- **BACKEND_TESTING_GUIDE.md** - API testing with curl
- **ATS_IMPLEMENTATION_SUMMARY.md** - Complete project overview

### Code Comments
- Check inline comments in each file for specific implementation details
- JSDoc comments on hooks explain parameters and return types
- Component props documented with TypeScript interfaces

---

## 🎨 UI Components Used

### From Shadcn/ui
- Card, CardContent, CardHeader, CardTitle
- Button (with variants)
- Badge
- Dialog/Modal (for forms)

### From Lucide Icons
- Loader2, X, Download, MessageCircle, Calendar
- TrendingUp, TrendingDown, Filter, BarChart3
- AlertCircle, Save

### Custom Components
- PageHeader
- ToastProvider
- AppShell

---

## 🚀 Next Steps

### What to Test Next
1. **End-to-end workflow:** Create app → schedule interview → submit scorecard
2. **Error handling:** Try operations with invalid IDs
3. **Loading states:** Observe spinners during operations
4. **Responsive design:** Test on mobile/tablet/desktop

### What Could Be Added Later
- WebSocket for real-time updates
- Email notifications for interviews
- Calendar integration
- Bulk actions
- Advanced filtering
- PDF export

---

## 💾 Database Tables

### New Tables (Priority 2)
- `applications` - Tracks candidate applications
- `interviews` - Interview scheduling
- `interview_slots` - Interviewer availability
- `scorecards` - Interview feedback

### Data Relationships
```
resume ──→ application ──→ interview ──→ scorecard
             ↓
          position
```

---

## 🔐 Security Notes

- All API calls include JWT token (auto-handled by fetch)
- Scorecard data encrypted before storage
- Audit trail logs all changes
- Role-based access (recruiter/admin)
- CORS configured for frontend domain

---

## 📞 API Documentation

### Swagger Docs
Open browser to: http://localhost:8000/docs

Shows:
- All available endpoints
- Request/response schemas
- Try-it-out interface
- Error responses

---

**Last Updated:** 2026-06-05  
**Status:** ✅ Priority 2A-2C COMPLETE  
**Ready for Testing:** YES  
**Next Phase:** Priority 3 (Advanced Features)
