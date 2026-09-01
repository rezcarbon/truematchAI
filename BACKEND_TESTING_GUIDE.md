# Backend ATS Features Testing Guide

## Setup

### 1. Run Database Migration
```bash
cd ~/Desktop/TrueMatch/backend
source .venv/bin/activate
alembic upgrade head
```

### 2. Restart Backend
```bash
pkill -f uvicorn
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 3. Get Authentication Token

First, sign up or login to get a JWT token:

```bash
# Signup
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "recruiter@test.com",
    "password": "testpass123",
    "role": "recruiter"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "recruiter@test.com",
    "password": "testpass123"
  }'
```

Response will include `access_token`. Save it:
```bash
TOKEN="your_access_token_here"
```

---

## Test Cases

### Test 1: Create Application

**Endpoint:** `POST /api/v1/ats/applications`

```bash
curl -X POST http://localhost:8000/api/v1/ats/applications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "insert-real-uuid-here",
    "position_id": "insert-real-uuid-here",
    "source": "linkedin"
  }'
```

**Expected Response:**
- Status: `201 Created`
- Body: ApplicationResponse with id, stage (default: "applied"), timestamps

**Success Indicator:** Returns application object with `stage: "applied"`

---

### Test 2: Get Pipeline

**Endpoint:** `GET /api/v1/ats/positions/{position_id}/pipeline`

```bash
curl -X GET "http://localhost:8000/api/v1/ats/positions/{position_id}/pipeline" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
- Status: `200 OK`
- Body: Array of ApplicationResponse objects for that position

**Success Indicator:** Returns list of applications with their stages

---

### Test 3: Get Pipeline for Specific Stage

**Endpoint:** `GET /api/v1/ats/positions/{position_id}/pipeline?stage=phone_screen`

```bash
curl -X GET "http://localhost:8000/api/v1/ats/positions/{position_id}/pipeline?stage=phone_screen" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
- Status: `200 OK`
- Body: Array of ApplicationResponse objects in phone_screen stage only

**Success Indicator:** Returns only candidates in specified stage

---

### Test 4: Update Application Stage

**Endpoint:** `PATCH /api/v1/ats/applications/{application_id}`

```bash
curl -X PATCH http://localhost:8000/api/v1/ats/applications/{application_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stage": "phone_screen"
  }'
```

**Expected Response:**
- Status: `200 OK`
- Body: Updated ApplicationResponse with `stage: "phone_screen"` and updated `stage_entered_at`

**Success Indicator:** Application successfully moves to new stage

---

### Test 5: Schedule Interview

**Endpoint:** `POST /api/v1/ats/interviews`

```bash
curl -X POST http://localhost:8000/api/v1/ats/interviews \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": "{application_id}",
    "position_id": "{position_id}",
    "interviewer_ids": ["{interviewer_id_1}", "{interviewer_id_2}"],
    "meeting_platform": "google_meet"
  }'
```

**Expected Response:**
- Status: `201 Created`
- Body: InterviewResponse with id, status: "scheduled", scheduled_at

**Success Indicator:** Interview created successfully

---

### Test 6: Get Interview

**Endpoint:** `GET /api/v1/ats/interviews/{interview_id}`

```bash
curl -X GET http://localhost:8000/api/v1/ats/interviews/{interview_id} \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
- Status: `200 OK`
- Body: Full InterviewResponse with all details

**Success Indicator:** Interview details returned correctly

---

### Test 7: List Interviews for Application

**Endpoint:** `GET /api/v1/ats/applications/{application_id}/interviews`

```bash
curl -X GET "http://localhost:8000/api/v1/ats/applications/{application_id}/interviews" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
- Status: `200 OK`
- Body: InterviewListResponse with items array and pagination info

**Success Indicator:** Returns paginated interview list

---

### Test 8: Submit Scorecard

**Endpoint:** `POST /api/v1/ats/scorecards`

```bash
curl -X POST http://localhost:8000/api/v1/ats/scorecards \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "interview_id": "{interview_id}",
    "competency_scores": {
      "problem_solving": 4,
      "communication": 5,
      "technical_depth": 3
    },
    "feedback": "Strong candidate, great communication skills",
    "overall_recommendation": "yes"
  }'
```

**Expected Response:**
- Status: `201 Created`
- Body: ScorecardResponse with id, submitted_at timestamp

**Success Indicator:** Scorecard submitted and timestamped

---

### Test 9: Get Interview Scorecards

**Endpoint:** `GET /api/v1/ats/interviews/{interview_id}/scorecards`

```bash
curl -X GET http://localhost:8000/api/v1/ats/interviews/{interview_id}/scorecards \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
- Status: `200 OK`
- Body: Array of ScorecardResponse objects for that interview

**Success Indicator:** All scorecards for interview returned

---

### Test 10: Get Pipeline Analytics

**Endpoint:** `GET /api/v1/ats/positions/{position_id}/pipeline-analytics`

```bash
curl -X GET "http://localhost:8000/api/v1/ats/positions/{position_id}/pipeline-analytics" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
- Status: `200 OK`
- Body: PipelineAnalyticsResponse with:
  - `total_applications`: count
  - `by_stage`: array with stage, count, average/median days
  - `average_time_to_hire`: overall metric

**Success Indicator:** Analytics correctly aggregated

---

### Test 11: Get Source Analytics

**Endpoint:** `GET /api/v1/ats/source-analytics`

```bash
curl -X GET "http://localhost:8000/api/v1/ats/source-analytics?position_id={position_id}" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
- Status: `200 OK`
- Body: SourceAnalyticsResponse with:
  - `by_source`: array with source, applications count, hires, hire_rate

**Success Indicator:** Source effectiveness metrics calculated

---

## Complete Testing Workflow

Run these tests in order to verify the complete pipeline flow:

```bash
# 1. Set token
TOKEN="your_token_here"
POS_ID="your_position_id"
RES_ID="your_resume_id"

# 2. Create application
APP=$(curl -s -X POST http://localhost:8000/api/v1/ats/applications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"resume_id\": \"$RES_ID\", \"position_id\": \"$POS_ID\", \"source\": \"linkedin\"}")

APP_ID=$(echo $APP | jq -r '.id')
echo "Created application: $APP_ID"

# 3. Get pipeline
curl -s -X GET "http://localhost:8000/api/v1/ats/positions/$POS_ID/pipeline" \
  -H "Authorization: Bearer $TOKEN" | jq .

# 4. Update stage
curl -s -X PATCH http://localhost:8000/api/v1/ats/applications/$APP_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"stage": "phone_screen"}' | jq .

# 5. Schedule interview
INTERVIEW=$(curl -s -X POST http://localhost:8000/api/v1/ats/interviews \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"application_id\": \"$APP_ID\", \"position_id\": \"$POS_ID\", \"interviewer_ids\": [], \"meeting_platform\": \"google_meet\"}")

INT_ID=$(echo $INTERVIEW | jq -r '.id')
echo "Scheduled interview: $INT_ID"

# 6. Submit scorecard
curl -s -X POST http://localhost:8000/api/v1/ats/scorecards \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"interview_id\": \"$INT_ID\", \"competency_scores\": {\"problem_solving\": 4, \"communication\": 5}, \"overall_recommendation\": \"yes\"}" | jq .

# 7. Get analytics
curl -s -X GET "http://localhost:8000/api/v1/ats/positions/$POS_ID/pipeline-analytics" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

---

## Success Criteria

✅ All endpoints return correct HTTP status codes  
✅ Application stages update correctly  
✅ Interviews can be scheduled  
✅ Scorecards can be submitted  
✅ Analytics aggregate correctly  
✅ Data persists after restart  
✅ Pagination works on list endpoints  

---

## Common Issues & Troubleshooting

### Issue: 404 on endpoints
**Solution:** Make sure migration ran (`alembic upgrade head`)

### Issue: 401 Unauthorized
**Solution:** Ensure token is valid and included in Authorization header

### Issue: Foreign key errors
**Solution:** Ensure resume_id and position_id exist in database

### Issue: No candidates in pipeline
**Solution:** Create applications first via POST /api/v1/ats/applications

---

## Next: Frontend Integration

Once all backend tests pass, the frontend PipelineBoard component can:
1. Fetch candidates from `/api/v1/ats/positions/{id}/pipeline`
2. Update stages via `PATCH /api/v1/ats/applications/{id}`
3. Schedule interviews via `POST /api/v1/ats/interviews`
4. Show analytics from `/api/v1/ats/positions/{id}/pipeline-analytics`
