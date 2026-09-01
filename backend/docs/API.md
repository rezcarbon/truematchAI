# TrueMatch API Reference

**API Version:** 0.1.0  
**Base URL:** `http://localhost:8000` (development) or `https://api.truematch.ai` (production)  
**Documentation:** `/docs` (Swagger UI) or `/redoc` (ReDoc)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Rate Limiting](#rate-limiting)
3. [Error Handling](#error-handling)
4. [Endpoints](#endpoints)
   - [Auth](#auth)
   - [Assessments](#assessments)
   - [Positions](#positions)
   - [Decisions](#decisions)
   - [Profile](#profile)
   - [Files](#files)
   - [Agents](#agents)
   - [Admin](#admin)
5. [Examples](#examples)

---

## Authentication

The TrueMatch API uses **Bearer tokens** (JWT) for authentication.

### Obtaining a Token

#### Via Email/Password (Signup)
```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123",
    "display_name": "John Doe",
    "role": "candidate"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### Via Email/Password (Login)
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123"
  }'
```

#### Via Refresh Token
```bash
curl -X POST http://localhost:8000/api/v1/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }'
```

#### Via Singpass (Singapore NDI OIDC)
```bash
# 1. Initiate login
curl http://localhost:8000/api/v1/auth/singpass/init

# Response: {"auth_url": "https://...", "state": "abc123"}

# 2. User redirects to auth_url and authorizes
# 3. Complete login with authorization code
curl -X POST http://localhost:8000/api/v1/auth/singpass/callback \
  -H "Content-Type: application/json" \
  -d '{
    "state": "abc123",
    "code": "auth_code_from_singpass"
  }'
```

### Using the Token

Include the token in the `Authorization` header:

```bash
curl http://localhost:8000/api/v1/assessments \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Token Expiry

- **Access Token:** 30 minutes (configurable via `settings.access_token_expire_minutes`)
- **Refresh Token:** 7 days (configurable via `settings.refresh_token_expire_days`)

When an access token expires (HTTP 401), use the refresh token to obtain a new one.

### User Roles

- **candidate:** Can take self-assessments and view their own assessments
- **recruiter:** Can manage positions, create assessments, make hiring decisions
- **admin:** Can access governance configs, audit logs, analytics

---

## Rate Limiting

The API enforces **per-IP rate limiting**: 120 requests per 60 seconds (configurable).

When the rate limit is exceeded:
- **Status Code:** `429 Too Many Requests`
- **Header:** `Retry-After: <seconds>` (indicates how long to wait)

```bash
curl http://localhost:8000/api/v1/assessments \
  -H "Authorization: Bearer token"

# After 120 requests in 60 seconds:
# HTTP/1.1 429 Too Many Requests
# Retry-After: 45
```

**Exempt endpoints:** `/livez`, `/readyz`, `/health`, `/metrics`

---

## Error Handling

All errors follow the **RFC 7807 Problem Details for HTTP APIs** format.

### Error Response Structure

```json
{
  "type": "validation_error",
  "title": "Request Validation Failed",
  "status": 422,
  "detail": "The request body contains one or more validation errors",
  "request_id": "req-550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-06-03T10:30:00Z",
  "instance": "/api/v1/auth/signup",
  "errors": [
    {
      "field": "email",
      "message": "invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

### Common Error Types

| Type | Status | Description |
|------|--------|-------------|
| `validation_error` | 422 | Request body validation failed |
| `authentication_failed` | 401 | Missing or invalid token |
| `authorization_failed` | 403 | User lacks required permissions |
| `resource_not_found` | 404 | Resource does not exist |
| `conflict` | 409 | Resource conflict (e.g., email already registered) |
| `storage_error` | 503 | File storage (S3) unavailable |
| `external_service_error` | 503 | External service (LLM, Singpass) unavailable |
| `internal_error` | 500 | Unexpected server error |

### Error Response Headers

- `X-Request-ID` — Unique request identifier for debugging and log correlation
- `Retry-After` — (429 only) Seconds to wait before retrying

### Debugging Errors

Use the `request_id` header and `X-Request-ID` response header to correlate logs:

```bash
curl -i http://localhost:8000/api/v1/assessments/invalid-id \
  -H "Authorization: Bearer token"

# Response headers:
# X-Request-ID: req-550e8400-e29b-41d4-a716-446655440000

# Find logs with this request ID:
# grep "request_id=req-550e8400-e29b-41d4-a716-446655440000" /var/log/app.log
```

---

## Endpoints

### Auth

#### POST /api/v1/auth/signup
Create a new user account.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123",
    "display_name": "John Doe",
    "role": "candidate",
    "company_id": null
  }'
```

**Responses:**
- `201 Created` — User created, returns access and refresh tokens
- `422 Unprocessable Entity` — Validation error (invalid email, weak password)
- `409 Conflict` — Email already registered

**Fields:**
- `email` (required): Valid email address
- `password` (required): 8–128 characters
- `display_name` (optional): User's display name
- `role` (required): "candidate", "recruiter", or "admin"
- `company_id` (optional): UUID of the company (required for recruiters)

---

#### POST /api/v1/auth/login
Authenticate with email and password.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123"
  }'
```

**Responses:**
- `200 OK` — Returns access and refresh tokens
- `401 Unauthorized` — Invalid email or password
- `422 Unprocessable Entity` — Validation error

---

#### POST /api/v1/auth/refresh
Obtain a new access token using a refresh token.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }'
```

**Responses:**
- `200 OK` — Returns new access token
- `401 Unauthorized` — Invalid or expired refresh token

---

#### DELETE /api/v1/auth/session
Logout (discard tokens on client side).

**Request:**
```bash
curl -X DELETE http://localhost:8000/api/v1/auth/session \
  -H "Authorization: Bearer token"
```

**Responses:**
- `204 No Content` — Logged out successfully

---

#### GET /api/v1/auth/me
Get the current authenticated user's profile.

**Request:**
```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer token"
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "display_name": "John Doe",
  "role": "candidate",
  "company_id": null,
  "created_at": "2026-06-03T10:30:00Z"
}
```

---

### Assessments

#### POST /api/v1/assessments
Create an assessment (recruiter evaluates candidate against position).

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/assessments \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "550e8400-e29b-41d4-a716-446655440001",
    "position_id": "550e8400-e29b-41d4-a716-446655440002"
  }'
```

**Responses:**
- `201 Created` — Assessment created, processing queued
- `404 Not Found` — Resume or position not found
- `401 Unauthorized` — Not authenticated
- `403 Forbidden` — Insufficient permissions

---

#### POST /api/v1/assessments/self
Create a self-assessment (candidate evaluates themselves against a pasted JD).

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/assessments/self \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "550e8400-e29b-41d4-a716-446655440001",
    "jd_text": "We are looking for a Senior Backend Engineer with 5+ years of experience...",
    "position_title": "Senior Backend Engineer"
  }'
```

**Responses:**
- `201 Created` — Self-assessment created
- `404 Not Found` — Resume not found
- `403 Forbidden` — Candidate can only assess their own resume

---

#### GET /api/v1/assessments
List assessments (paginated).

**Request:**
```bash
curl "http://localhost:8000/api/v1/assessments?page=1&page_size=20" \
  -H "Authorization: Bearer token"
```

**Response:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "status": "completed",
      "traditional_score": 72,
      "semantic_score": 78,
      "capability_score": 85,
      "created_at": "2026-06-03T10:30:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

---

#### GET /api/v1/assessments/{id}
Get assessment details (narrative, scores, governance results).

**Request:**
```bash
curl http://localhost:8000/api/v1/assessments/550e8400-e29b-41d4-a716-446655440003 \
  -H "Authorization: Bearer token"
```

**Responses:**
- `200 OK` — Assessment details
- `404 Not Found` — Assessment not found
- `403 Forbidden` — Candidate cannot see others' assessments

---

### Positions

#### POST /api/v1/positions
Create a job position (recruiter only).

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/positions \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Backend Engineer",
    "description": "We are looking for a Senior Backend Engineer with 5+ years of experience...",
    "company_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Responses:**
- `201 Created` — Position created, JD analyzed
- `403 Forbidden` — Recruiter role required
- `422 Unprocessable Entity` — Invalid request (company_id required)

---

#### GET /api/v1/positions
List positions (paginated, recruiter/admin only).

**Request:**
```bash
curl "http://localhost:8000/api/v1/positions?page=1&page_size=20" \
  -H "Authorization: Bearer token"
```

---

### Decisions

#### POST /api/v1/decisions
Record a hiring decision (recruiter only).

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/decisions \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{
    "assessment_id": "550e8400-e29b-41d4-a716-446655440003",
    "position_id": "550e8400-e29b-41d4-a716-446655440002",
    "decision": "advance",
    "override_reasoning": "Strong technical fit despite lower score"
  }'
```

**Responses:**
- `201 Created` — Decision recorded
- `404 Not Found` — Assessment or position not found
- `409 Conflict` — Decision already made for this assessment

---

### Profile

#### GET /api/v1/profile
Get the current user's capability profile.

**Request:**
```bash
curl http://localhost:8000/api/v1/profile \
  -H "Authorization: Bearer token"
```

---

#### POST /api/v1/profile/export
Export user data (GDPR/PDPA compliance).

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/profile/export \
  -H "Authorization: Bearer token"
```

**Response:** ZIP file containing all user's assessments, decisions, and personal data.

---

#### POST /api/v1/profile/erase
Request account deletion (right to be forgotten).

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/profile/erase \
  -H "Authorization: Bearer token"
```

**Responses:**
- `204 No Content` — Deletion requested, will be processed asynchronously
- `400 Bad Request` — User has pending assessments

---

### Files

#### POST /api/v1/files/upload
Upload a resume file.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/files/upload \
  -H "Authorization: Bearer token" \
  -F "file=@resume.pdf"
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "filename": "resume.pdf",
  "size": 102400,
  "content_type": "application/pdf",
  "url": "https://s3.amazonaws.com/truematch-uploads/..."
}
```

---

### Agents

#### WebSocket /api/v1/agents/ws
Real-time event stream for agent activity.

**JavaScript Example:**
```javascript
const ws = new WebSocket("ws://localhost:8000/api/v1/agents/ws");

ws.onmessage = (event) => {
  const payload = JSON.parse(event.data);
  console.log(`Agent event: ${payload.event}`, payload);
  // {
  //   "id": "ingest-123",
  //   "event": "cv_ingested",
  //   "status": "completed"
  // }
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};
```

---

#### GET /api/v1/agents/queue
Get the ingestion queue status.

**Request:**
```bash
curl "http://localhost:8000/api/v1/agents/queue?status=awaiting_review" \
  -H "Authorization: Bearer token"
```

---

### Admin

#### GET /api/v1/admin/governance/config
Get governance configuration (admin only).

**Request:**
```bash
curl http://localhost:8000/api/v1/admin/governance/config \
  -H "Authorization: Bearer token"
```

---

#### GET /api/v1/admin/audit-trail
Get audit trail of assessments and decisions (admin only).

**Request:**
```bash
curl "http://localhost:8000/api/v1/admin/audit-trail?assessment_id=..." \
  -H "Authorization: Bearer token"
```

---

#### GET /api/v1/admin/analytics
Get platform analytics (admin only).

**Request:**
```bash
curl http://localhost:8000/api/v1/admin/analytics \
  -H "Authorization: Bearer token"
```

---

## Examples

### Complete Workflow: Candidate Self-Assessment

```bash
#!/bin/bash

# 1. Signup
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "candidate@example.com",
    "password": "SecurePassword123",
    "display_name": "Jane Smith",
    "role": "candidate"
  }')

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')
echo "Token: $ACCESS_TOKEN"

# 2. Upload resume
RESUME_ID=$(curl -s -X POST http://localhost:8000/api/v1/files/upload \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@resume.pdf" | jq -r '.id')

echo "Resume ID: $RESUME_ID"

# 3. Create self-assessment
ASSESSMENT=$(curl -s -X POST http://localhost:8000/api/v1/assessments/self \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "'$RESUME_ID'",
    "jd_text": "Senior Backend Engineer role. 5+ years Python/Go, distributed systems, gRPC.",
    "position_title": "Senior Backend Engineer"
  }')

ASSESSMENT_ID=$(echo "$ASSESSMENT" | jq -r '.id')
echo "Assessment ID: $ASSESSMENT_ID"

# 4. Poll for completion (check every 5 seconds)
for i in {1..20}; do
  RESULT=$(curl -s http://localhost:8000/api/v1/assessments/$ASSESSMENT_ID \
    -H "Authorization: Bearer $ACCESS_TOKEN")

  STATUS=$(echo "$RESULT" | jq -r '.status')
  echo "Status: $STATUS"

  if [ "$STATUS" = "completed" ]; then
    echo "Assessment complete!"
    echo "$RESULT" | jq '.'
    break
  fi

  sleep 5
done
```

---

## Support

For API questions or issues:
- Check the `/docs` endpoint for interactive API documentation
- Review error `request_id` in logs for debugging
- Contact support@truematch.ai with the `request_id`

