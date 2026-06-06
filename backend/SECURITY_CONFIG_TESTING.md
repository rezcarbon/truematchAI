# Security Configuration Testing Guide

This guide demonstrates how to test all 8 critical security configuration fixes.

## Prerequisites

```bash
cd ~/Desktop/TrueMatch/backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Phase 1: Startup Secret Validation

### Test 1.1: Missing ENCRYPTION_KEY in Production

**Expected:** Application fails to start with helpful error message

```bash
# Set to production environment with no encryption
export ENVIRONMENT=production
export ENCRYPTION_KEY=""
export ENCRYPTION_INDEX_KEY=""

# Try to start the app
python -m app.main
# Expected Error:
# ❌ Configuration validation failed:
#   - ENCRYPTION_KEY and ENCRYPTION_INDEX_KEY are required in production. 
#     Generate with: python -c "import secrets; print(secrets.token_hex(32))"
```

### Test 1.2: Weak JWT_SECRET in Production

**Expected:** Application fails with validation error

```bash
export JWT_SECRET="weak"  # Only 4 characters
export ENVIRONMENT=production

python -m app.main
# Expected Error:
# ❌ Configuration validation failed:
#   - JWT_SECRET is too short (4 chars). Minimum 32 characters required.
```

### Test 1.3: Placeholder AWS Credentials in Production

**Expected:** Application fails with credential error

```bash
export AWS_ACCESS_KEY_ID="placeholder"
export AWS_SECRET_ACCESS_KEY="placeholder"
export ENVIRONMENT=production

python -m app.main
# Expected Error:
# ❌ Configuration validation failed:
#   - AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY contain 'placeholder'. 
#     These must be set to real AWS credentials in production.
```

### Test 1.4: Invalid Database URL

**Expected:** Application fails with database error

```bash
export DATABASE_URL="mysql://localhost/truematch"  # Wrong database type

python -m app.main
# Expected Error:
# ❌ Configuration validation failed:
#   - DATABASE_URL must be a PostgreSQL URL (postgresql://...), got: mysql://...
```

### Test 1.5: Development Mode Tolerates Weak Secrets

**Expected:** Application starts with warnings

```bash
export ENVIRONMENT=development
export JWT_SECRET="weak"  # Only 4 characters
export ENCRYPTION_KEY=""  # Not configured

python -m app.main
# Expected Output:
# ⚠️ Configuration validation passed with 2 warning(s)
# - JWT_SECRET is short (4 chars). Consider using 32+ characters for better security.
# - Field-level encryption is not configured. PII will be stored unencrypted.
```

### Test 1.6: Valid Configuration Passes

**Expected:** Application starts successfully

```bash
export ENVIRONMENT=production
export ENCRYPTION_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
export ENCRYPTION_INDEX_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
export JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/truematch"
export REDIS_URL="redis://localhost:6379/0"
export AWS_ACCESS_KEY_ID="AKIA1234567890ABCDEF"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

python -m app.main
# Expected Output:
# ✅ Configuration validation passed
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Phase 2: Token Denylist & Revocation

### Test 2.1: Token Revocation on Logout

**Expected:** Token is revoked and subsequent requests fail

```bash
# 1. Start the app
python -m app.main &
APP_PID=$!

# 2. Login to get tokens
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}' \
  > /tmp/tokens.json

ACCESS_TOKEN=$(jq -r '.access_token' /tmp/tokens.json)
echo "Access token: $ACCESS_TOKEN"

# 3. Use token to access protected endpoint - should work
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  http://localhost:8000/api/v1/auth/me
# Expected: 200 OK with user data

# 4. Logout to revoke token
curl -X DELETE -H "Authorization: Bearer $ACCESS_TOKEN" \
  http://localhost:8000/api/v1/auth/session
# Expected: 204 No Content

# 5. Try to use revoked token - should fail
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  http://localhost:8000/api/v1/auth/me
# Expected: 401 Unauthorized with message "Token has been revoked"

kill $APP_PID
```

### Test 2.2: Revoke All User Tokens

**Expected:** All tokens for user are invalidated

This requires direct Redis/API access. See implementation:

```python
# In a test file:
from app.core.token_denylist import TokenDenylist
from app.deps import get_redis

async def test_revoke_all_user_tokens():
    redis = await get_redis()
    denylist = TokenDenylist(redis)
    
    user_id = UUID("12345678-1234-1234-1234-123456789012")
    
    # Revoke all tokens for user
    revoked_count = await denylist.revoke_all_user_tokens(user_id)
    assert revoked_count > 0
    
    await redis.close()
```

### Test 2.3: Token Denylist Statistics

```python
async def test_denylist_stats():
    redis = await get_redis()
    denylist = TokenDenylist(redis)
    
    stats = await denylist.get_denylist_stats()
    print(f"Denylist size: {stats['denylist_size']}")
    print(f"User token indices: {stats['user_token_indices']}")
    
    assert stats['denylist_size'] >= 0
```

## Phase 3: Secret Generation

### Test 3.1: Generate Secrets

```bash
cd ~/Desktop/TrueMatch/backend
python scripts/generate_secrets.py

# Expected Output:
# ======================================================================
# TrueMatch Backend Secrets Generator
# ======================================================================
# 
# IMPORTANT:
# - Keep these secrets secure; store in a secrets manager
# - Never commit .env file to git
# - Different environments (dev, staging, prod) need different secrets
# ...
# 
# ENCRYPTION_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0
# ENCRYPTION_INDEX_KEY=...
# JWT_SECRET=...
```

### Test 3.2: Validate Generated Secrets

```bash
# Generate and validate
SECRETS=$(python scripts/generate_secrets.py 2>/dev/null | grep -E "^(ENCRYPTION|JWT)" | tail -3)

# Create temp .env with generated secrets
echo "ENVIRONMENT=production" > /tmp/test.env
echo "$SECRETS" >> /tmp/test.env
echo "DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db" >> /tmp/test.env
echo "REDIS_URL=redis://localhost:6379/0" >> /tmp/test.env
echo "AWS_ACCESS_KEY_ID=test" >> /tmp/test.env
echo "AWS_SECRET_ACCESS_KEY=test" >> /tmp/test.env

# Load and validate
export $(cat /tmp/test.env | xargs)

python -c "
from app.core.config_validator import SecretValidator
from app.config import settings

validator = SecretValidator(settings)
try:
    validator.validate_all()
    print('✅ All generated secrets are valid')
except ValueError as e:
    print(f'❌ {e}')
"
```

## Phase 4: Configuration Validator Tests

### Test 4.1: Validator Error Collection

```python
# In test_config_validator.py
from app.core.config_validator import SecretValidator
from unittest.mock import Mock

def test_validator_collects_multiple_errors():
    mock_settings = Mock()
    mock_settings.is_production = True
    mock_settings.encryption_key = ""
    mock_settings.encryption_index_key = ""
    mock_settings.jwt_secret = "weak"
    mock_settings.database_url = "invalid"
    mock_settings.redis_url = ""
    mock_settings.aws_access_key_id = "placeholder"
    mock_settings.aws_secret_access_key = "placeholder"
    mock_settings.s3_bucket = ""
    mock_settings.singpass_sig_jwk_path = ""
    mock_settings.singpass_enc_jwk_path = ""
    
    validator = SecretValidator(mock_settings)
    validator.validate_all()
    
    # Should have collected multiple errors, not failed on first
    assert len(validator.errors) > 3
```

### Test 4.2: Environment-Specific Rules

```python
def test_production_strict_validation():
    mock_settings = Mock()
    mock_settings.is_production = True
    mock_settings.jwt_secret = "short"  # Too short
    
    validator = SecretValidator(mock_settings)
    validator.validate_jwt_secret()
    
    # Should error in production
    assert len(validator.errors) > 0
    assert any("too short" in e for e in validator.errors)

def test_development_warning_only():
    mock_settings = Mock()
    mock_settings.is_production = False
    mock_settings.jwt_secret = "short"  # Too short
    
    validator = SecretValidator(mock_settings)
    validator.validate_jwt_secret()
    
    # Should warn, not error, in development
    assert len(validator.errors) == 0
    assert len(validator.warnings) > 0
```

## Phase 5: Integration Tests

### Test 5.1: Full Startup Validation Pipeline

```bash
pytest tests/test_config_startup.py::test_startup_validation_runs
```

### Test 5.2: Token Denylist Integration

```bash
pytest tests/test_token_denylist.py -v
```

### Test 5.3: Logout Endpoint Integration

```bash
pytest tests/test_auth_logout.py::test_logout_revokes_token -v
```

## Manual Testing Checklist

- [ ] Generate secrets using `scripts/generate_secrets.py`
- [ ] Copy generated secrets to `.env`
- [ ] Start app: `python -m app.main` - should pass validation
- [ ] Login and logout - token should be revoked
- [ ] Try using revoked token - should get 401
- [ ] Check Redis denylist: `redis-cli KEYS "token_denylist:*"`
- [ ] Start in staging mode - should require strong secrets
- [ ] Start in production mode with weak JWT - should fail
- [ ] Review logs for security configuration warnings/errors

## Expected Log Output

```
✅ Configuration validation passed
Encryption enabled: true
S3 enabled: true
Singpass configured: false
Environment: production
```

## Troubleshooting

### "Redis connection failed"
- Ensure Redis is running: `redis-cli ping` should return "PONG"
- Check REDIS_URL format: `redis://localhost:6379/0`

### "Database connection failed"
- Ensure PostgreSQL is running
- Check DATABASE_URL format: `postgresql+asyncpg://user:pass@host:port/db`

### "Configuration validation failed"
- Run validator with verbose errors: `python -c "from app.core.config_validator import SecretValidator; from app.config import settings; SecretValidator(settings).validate_all()"`
- Check all required env vars are set

## Security Notes

- Never log actual secret values (validator logs hashes/lengths only)
- Secrets should be rotated in production on a regular schedule
- Use environment variables or secrets manager, never hardcode
- Different environments should have completely different secrets
- Backup encrypted secrets securely (hardware security module, etc.)
