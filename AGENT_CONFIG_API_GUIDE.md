# Agent Configuration API Guide

## Overview

The Agent Configuration API enables recruiters and admins to customize agent behavior (instructions, tools, parameters) without code changes. All configurations are versioned, audited, and require approval before activation.

## Architecture

```
Recruiter creates config (DRAFT)
    ↓
Recruiter submits for approval (PENDING_APPROVAL)
    ↓
Admin reviews & validates governance (runs safety checks)
    ↓
Admin approves (APPROVED)
    ↓
Admin activates (ACTIVE) ← goes live
    ↓
Chat agents load custom config automatically
    ↓
Fallback to hardcoded defaults if config unavailable
```

## Configuration Workflow

### 1. Create Configuration

**Endpoint:** `POST /api/v1/agent-configs/`

**Permission:** Recruiter, Admin

**Request:**
```json
{
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_type": "recruiter",
  "role": "recruiter",
  "name": "Cultural Fit Screener",
  "description": "Enhanced screening focused on cultural alignment",
  "instructions": "You are a recruiter assistant focused on assessing cultural fit. Evaluate candidates for:\n1. Team values alignment\n2. Communication style\n3. Work environment fit\nBe fair, unbiased, and inclusive. Flag any potential unconscious bias.",
  "tools_enabled": ["analyze", "rank", "clarify"],
  "tool_parameters": {
    "analyze": {
      "max_length": 5000
    },
    "rank": {
      "scale": 1-5
    }
  },
  "agent_parameters": {
    "temperature": 0.7,
    "max_tokens": 2000
  }
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "company_id": "550e8400-e29b-41d4-a716-446655440001",
  "agent_type": "recruiter",
  "role": "recruiter",
  "name": "Cultural Fit Screener",
  "status": "draft",
  "version_number": 1,
  "is_default": false,
  "created_at": "2026-07-16T14:30:00Z",
  "approved_at": null
}
```

### 2. Update Configuration (Draft Only)

**Endpoint:** `PUT /api/v1/agent-configs/{config_id}`

**Permission:** Config creator, Admin

**Request:**
```json
{
  "instructions": "You are a recruiter assistant...",
  "tools_enabled": ["analyze", "rank", "clarify"],
  "change_reason": "Added clarify tool for better context gathering"
}
```

**Notes:**
- Only works if config is in DRAFT status
- Creates new version automatically
- All previous versions preserved for audit/rollback

### 3. Validate Configuration

**Endpoint:** `GET /api/v1/agent-configs/{config_id}/validate`

**Permission:** Any authenticated user

**Response:**
```json
{
  "config_id": "550e8400-e29b-41d4-a716-446655440000",
  "version_number": 1,
  "validation": {
    "safety_passed": true,
    "fairness_score": 85,
    "warnings": [
      "Instructions mention 'email' - consider PII handling"
    ],
    "errors": []
  },
  "version_checks": {
    "has_instructions": true,
    "has_tools": true,
    "change_documented": true,
    "submitted_properly": false
  },
  "approval_items": [
    {
      "item": "Safety validation",
      "status": "passed",
      "details": "No safety issues found"
    },
    {
      "item": "Fairness score",
      "status": "passed",
      "details": "Score: 85/100"
    }
  ],
  "recommendation": "approve"
}
```

**Validation Checks:**
- **Safety patterns:** Detects "bypass governance", "disable fairness", etc.
- **PII detection:** Warns if instructions mention sensitive terms
- **Tool combinations:** Validates tool compatibility
- **Parameter ranges:** Temperature (0-2), max_tokens (100-4096)
- **Fairness awareness:** Scores based on fairness language

### 4. Submit for Approval

**Endpoint:** `POST /api/v1/agent-configs/{config_id}/submit-for-approval`

**Permission:** Config creator, Admin

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending_approval",
  "version_number": 1
}
```

**Workflow:**
- Changes status from DRAFT → PENDING_APPROVAL
- Marks current version as submitted
- Notifies admins of pending approval
- Records submission timestamp

### 5. View Approval Checklist (Admin)

**Endpoint:** `GET /api/v1/agent-configs/{config_id}/approval-checklist`

**Permission:** Admin only

**Response:**
```json
{
  "config_id": "550e8400-e29b-41d4-a716-446655440000",
  "version_number": 1,
  "agent_type": "recruiter",
  "role": "recruiter",
  "created_by": "550e8400-e29b-41d4-a716-446655440010",
  "submitted_at": "2026-07-16T14:30:00Z",
  "validation": {
    "safety_passed": true,
    "fairness_score": 85,
    "warnings": [],
    "errors": []
  },
  "version_checks": {
    "has_instructions": true,
    "has_tools": true,
    "change_documented": true,
    "submitted_properly": true
  },
  "approval_items": [
    {
      "item": "Safety validation",
      "status": "passed",
      "details": "No safety issues found"
    },
    {
      "item": "Fairness score",
      "status": "passed",
      "details": "Score: 85/100"
    },
    {
      "item": "Version documentation",
      "status": "passed",
      "details": "Change reason: Added clarify tool"
    },
    {
      "item": "Configuration completeness",
      "status": "passed",
      "details": "Instructions: ✓, Tools: ✓"
    }
  ],
  "recommendation": "approve"
}
```

### 6. Approve Configuration

**Endpoint:** `POST /api/v1/agent-configs/{config_id}/approve`

**Permission:** Admin only

**Request:**
```json
{
  "feedback": "Looks good. Fairness score is strong and safety checks pass."
}
```

**Validation:**
- Runs governance safety validation
- Returns 400 if validation fails
- Only proceeds if all checks pass
- Records approval timestamp and admin ID

**Response:**
```json
{
  "status": "approved",
  "approved_at": "2026-07-16T14:35:00Z",
  "approved_by_id": "550e8400-e29b-41d4-a716-446655440020"
}
```

### 7. Reject Configuration

**Endpoint:** `POST /api/v1/agent-configs/{config_id}/reject`

**Permission:** Admin only

**Request:**
```json
{
  "feedback": "Fairness score too low. Add language around bias awareness."
}
```

**Response:**
```json
{
  "status": "draft",
  "version_number": 1
}
```

**Effect:**
- Reverts config back to DRAFT status
- Preserves all versions for audit trail
- Records rejection reason
- Allows recruiter to make changes and resubmit

### 8. Activate Configuration

**Endpoint:** `POST /api/v1/agent-configs/{config_id}/activate`

**Permission:** Admin only

**Precondition:** Config must be in APPROVED status

**Response:**
```json
{
  "status": "active",
  "is_default": true,
  "activated_at": "2026-07-16T14:40:00Z"
}
```

**Effect:**
- Marks config as ACTIVE
- Deactivates all other active configs for same agent type
- All new chat sessions load this config
- Recorded in audit trail

### 9. View Configuration History

**Endpoint:** `GET /api/v1/agent-configs/{config_id}/versions`

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "config_id": "550e8400-e29b-41d4-a716-446655440001",
    "version_number": 3,
    "status": "active",
    "instructions": "...",
    "tools_enabled": ["analyze", "rank", "clarify"],
    "change_reason": "Enhanced fairness language",
    "activated_at": "2026-07-16T14:40:00Z"
  },
  {
    "version_number": 2,
    "status": "deprecated",
    "instructions": "...",
    "change_reason": "Added rank tool"
  },
  {
    "version_number": 1,
    "status": "deprecated",
    "instructions": "...",
    "change_reason": "Initial version"
  }
]
```

### 10. View Audit Trail

**Endpoint:** `GET /api/v1/agent-configs/{config_id}/audit`

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "action": "activated",
    "actor_id": "550e8400-e29b-41d4-a716-446655440020",
    "actor_role": "admin",
    "reason": "Activated as current configuration",
    "changes": {},
    "created_at": "2026-07-16T14:40:00Z"
  },
  {
    "action": "approved",
    "actor_id": "550e8400-e29b-41d4-a716-446655440020",
    "actor_role": "admin",
    "reason": "Looks good. Fairness score is strong."
  },
  {
    "action": "submitted",
    "actor_id": "550e8400-e29b-41d4-a716-446655440010",
    "actor_role": "recruiter",
    "reason": "Submitted for approval"
  },
  {
    "action": "modified",
    "actor_id": "550e8400-e29b-41d4-a716-446655440010",
    "actor_role": "recruiter",
    "changes": {
      "instructions": {
        "before": "...",
        "after": "..."
      }
    }
  },
  {
    "action": "created",
    "actor_id": "550e8400-e29b-41d4-a716-446655440010",
    "actor_role": "recruiter"
  }
]
```

## Permission Matrix

| Operation | Recruiter | Admin |
|-----------|-----------|-------|
| Create | ✓ | ✓ |
| Update own DRAFT | ✓ | ✓ |
| Update any DRAFT | ✗ | ✓ |
| Submit own | ✓ | ✓ |
| Submit any | ✗ | ✓ |
| Approve | ✗ | ✓ |
| Reject | ✗ | ✓ |
| Activate | ✗ | ✓ |
| View config | ✓ | ✓ |
| View versions | ✓ | ✓ |
| View audit | ✓ | ✓ |
| View approval checklist | ✗ | ✓ |
| Run validation | ✓ | ✓ |

## Safety Validation Details

### Dangerous Patterns Blocked
- "ignore previous instructions"
- "bypass governance"
- "disable fairness"
- "ignore consent"
- "override rules"

### PII Terms Warned
- email
- phone
- ssn
- password
- api key
- secret

### Fairness Scoring
- Base: 100 points
- Dangerous pattern: -20 per occurrence
- PII mention: -5 per occurrence
- Unsafe parameter: -10 per issue
- No fairness language: -10
- Final score: max(0, total)

## Example: Complete Workflow

```bash
# 1. Create config
curl -X POST http://localhost:8000/api/v1/agent-configs/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "...",
    "agent_type": "recruiter",
    "role": "recruiter",
    "name": "v1 Recruiter",
    "instructions": "Fair and unbiased recruiter assistant.",
    "tools_enabled": ["analyze", "rank"],
    "tool_parameters": {},
    "agent_parameters": {"temperature": 0.7}
  }'
# Returns: config_id

# 2. Validate before submitting
curl http://localhost:8000/api/v1/agent-configs/{config_id}/validate \
  -H "Authorization: Bearer $TOKEN"
# Review: fairness_score, errors, warnings, recommendation

# 3. Submit for approval
curl -X POST http://localhost:8000/api/v1/agent-configs/{config_id}/submit-for-approval \
  -H "Authorization: Bearer $TOKEN"
# Status changes to: pending_approval

# 4. (As admin) Review checklist
curl http://localhost:8000/api/v1/agent-configs/{config_id}/approval-checklist \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 5. (As admin) Approve
curl -X POST http://localhost:8000/api/v1/agent-configs/{config_id}/approve \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"feedback": "Looks good!"}'
# Status changes to: approved

# 6. (As admin) Activate
curl -X POST http://localhost:8000/api/v1/agent-configs/{config_id}/activate \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# Status changes to: active
# Chat agents now load this config
```

## Errors

### 400 Bad Request
- Configuration in wrong status for operation
- Safety validation failed
- Invalid parameters

### 403 Forbidden
- User lacks permission for operation
- Only creator can update own configs
- Only admins can approve/activate

### 404 Not Found
- Config not found
- Version not found

## Status Lifecycle

```
DRAFT (editable)
  ↓ submit-for-approval
PENDING_APPROVAL (awaiting admin review)
  ├─ approve → APPROVED
  └─ reject → DRAFT
APPROVED (ready to activate)
  ↓ activate
ACTIVE (in production)
DEPRECATED (replaced by newer version)
```

## Best Practices

1. **Clear change reasons** — Document why each version was created
2. **Fairness-first language** — Include bias awareness in instructions
3. **Validate before submitting** — Use `/validate` endpoint before approval
4. **Review audit trail** — Check who changed what and when
5. **Version numbering** — Versions auto-increment (immutable)
6. **Fallback safety** — Config-less agents revert to hardcoded defaults

