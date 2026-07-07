# 🔐 TrueMatch Test Access Credentials
**Environment**: Development/Testing  
**Generated**: 2026-07-06  
**Status**: ✅ ACTIVE

---

## 📋 QUICK REFERENCE TABLE

| Role | Email | Password | Access URL | Status |
|------|-------|----------|-----------|--------|
| **Admin** | `admin@truematch.local` | `admin123` | http://localhost:3000/login | ✅ Ready |
| **Recruiter** | `recruiter_test_@test.com` | Dynamic (see fixtures) | http://localhost:3000/login | ✅ Fixture-based |
| **Candidate** | `candidate_test_@test.com` | Dynamic (see fixtures) | http://localhost:3000/login | ✅ Fixture-based |

---

## 🔑 DETAILED ACCESS CREDENTIALS

### 1️⃣ ADMIN ACCOUNT

**Role**: Full Platform Access  
**Created By**: `create_test_admin.py` script  
**Scope**: System administration, user management, governance oversight

```
📧 Email:       admin@truematch.local
🔐 Password:    admin123
🌐 Login URL:   http://localhost:3000/login
📊 Dashboard:   http://localhost:3000/dashboard
```

**Access Permissions**:
- ✅ User management (create/edit/delete users)
- ✅ View all assessments
- ✅ Governance oversight & compliance monitoring
- ✅ System configuration
- ✅ Audit logs access
- ✅ Role assignment

**How to Create**:
```bash
cd /Users/modvader/Documents/codebase/truematch/backend
python create_test_admin.py
```

**JWT Token Signature**:
- `role`: "admin"
- `sub`: User UUID from database
- `exp`: 30 minutes (default)

---

### 2️⃣ RECRUITER ACCOUNT

**Role**: Hiring Team Member  
**Created By**: Test fixtures in `conftest.py`  
**Scope**: Assessment management, candidate evaluation, hiring workflows

```
📧 Email Pattern:      recruiter_test_[UUID]@test.com
🔐 Password:           hash (system-generated)
🌐 Login URL:          http://localhost:3000/login
📊 Dashboard:          http://localhost:3000/dashboard
```

**Access Permissions**:
- ✅ CV assessment capability
- ✅ JD analysis capability
- ✅ CV-to-JD alignment scoring
- ✅ View own team assessments
- ✅ Export reports
- ✅ Candidate search & filtering

**How to Create in Tests**:
```python
# From conftest.py
@pytest.fixture
async def recruiter_user(db_session, company):
    user = User(
        email=f"recruiter_test_{uuid4()}@test.com",
        password_hash="hash",
        role="recruiter",
        company_id=company.id,
    )
    db_session.add(user)
    await db_session.commit()
    return user
```

**Fixture Token Generator**:
```python
@pytest.fixture
async def recruiter_token(recruiter_user):
    return create_access_token(
        subject=str(recruiter_user.id), 
        role="recruiter"
    )
```

**JWT Token Signature**:
- `role`: "recruiter"
- `sub`: User UUID from database
- `exp`: 30 minutes (default)

---

### 3️⃣ CANDIDATE ACCOUNT

**Role**: Job Seeker / Self-Assessment User  
**Created By**: Signup flow or test fixtures  
**Scope**: CV assessment, skill verification, career insights

```
📧 Email Pattern:      candidate_test_[UUID]@test.com
🔐 Password:           Self-set during signup
🌐 Login URL:          http://localhost:3000/login
📊 Dashboard:          http://localhost:3000/dashboard
📋 Assessment:         http://localhost:3000/assessment
```

**Access Permissions**:
- ✅ Upload & assess own CV
- ✅ Self-assessment questionnaire
- ✅ View personal skill scores
- ✅ Get improvement recommendations
- ✅ Track assessment history
- ✅ Download reports (own data)
- ❌ View other candidates

**How to Create**:
```python
# Via signup form
POST /api/v1/auth/signup
{
  "email": "candidate_test@example.com",
  "password": "SecurePassword123",
  "display_name": "John Doe"
}

# Or via test fixture
@pytest.fixture
async def candidate_user(db_session, company):
    user = User(
        email=f"candidate_test_{uuid4()}@test.com",
        password_hash=hash_password_sync("password123"),
        role="candidate",
        company_id=company.id,
    )
    db_session.add(user)
    await db_session.commit()
    return user
```

**JWT Token Signature**:
- `role`: "candidate"
- `sub`: User UUID from database
- `exp`: 30 minutes (default)

---

## 🔗 API AUTHENTICATION

### JWT Token Header Format

```http
Authorization: Bearer <JWT_TOKEN>
```

### Token Generation (Backend)

```python
from app.core.security import create_access_token

# Admin token
admin_token = create_access_token(
    subject=str(admin_user.id),
    role="admin"
)

# Recruiter token
recruiter_token = create_access_token(
    subject=str(recruiter_user.id),
    role="recruiter"
)

# Candidate token
candidate_token = create_access_token(
    subject=str(candidate_user.id),
    role="candidate"
)
```

### Example API Call with Auth

```bash
curl -X POST http://localhost:8000/api/v1/assessments/cv \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "cv_text": "John Doe...",
    "role": "candidate"
  }'
```

---

## 🗂️ USER ROLE STRUCTURE

### Role Definitions (Enum)

```python
class UserRole(str, enum.Enum):
    candidate = "candidate"    # Job seeker / self-assessment
    recruiter = "recruiter"    # Hiring team member
    admin = "admin"            # System administrator
```

### User Model Fields

```python
class User:
    id: UUID                    # Unique user ID
    email: str                  # Email address (unique)
    password_hash: str          # Hashed password (bcrypt)
    role: UserRole             # candidate | recruiter | admin
    display_name: str          # User's display name
    location: str              # Geographic location
    headline: str              # User bio/headline
    company_id: UUID           # Associated company
    singpass_id: str           # Singapore SingPass ID (optional)
    created_at: datetime       # Account creation timestamp
    updated_at: datetime       # Last update timestamp
```

---

## 🧪 TEST DATABASE SETUP

### Automatic Test User Creation

The test suite creates temporary test users for each test:

```python
# In tests/conftest.py

# Admin user for tests
admin_user = User(
    email=f"admin_test_{uuid4()}@test.com",
    password_hash="hash",
    role="admin",
    company_id=company.id,
)

# Recruiter user for tests
recruiter_user = User(
    email=f"recruiter_test_{uuid4()}@test.com",
    password_hash="hash",
    role="recruiter",
    company_id=company.id,
)

# Token generation for API tests
admin_token = create_access_token(
    subject=str(admin_user.id), 
    role="admin"
)

recruiter_token = create_access_token(
    subject=str(recruiter_user.id), 
    role="recruiter"
)
```

### Running Tests with Test Users

```bash
# Run all tests (creates test users automatically)
pytest backend/tests/ -v

# Run specific test with a user
pytest backend/tests/test_assessments.py::test_recruiter_cv_assessment -v

# Run tests with custom database
TEST_DB_HOST=localhost TEST_DB_PORT=5432 pytest backend/tests/ -v
```

---

## 🔐 SECURITY NOTES

### Password Security

- **Admin**: Simple password for testing only (`admin123`)
  - ⚠️ Change immediately in production
  - Use strong, unique password in production

- **Test Users**: Temporary fixtures with hash-only storage
  - Passwords are NOT stored in test fixtures
  - Use `password_hash` field for direct DB access only

### Token Security

```
JWT_SECRET=your-dev-secret-key-change-me-in-production-this-is-not-secure
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

- ✅ Change `JWT_SECRET` in production
- ✅ Use HTTPS in production (not HTTP)
- ✅ Tokens expire after 30 minutes by default
- ✅ Refresh tokens available for longer sessions

### Environment Variables (`.env`)

```bash
# Development (current)
ENVIRONMENT=development
JWT_SECRET=your-dev-secret-key-change-me-in-production-this-is-not-secure

# Production (MUST CHANGE)
ENVIRONMENT=production
JWT_SECRET=<GENERATE-STRONG-RANDOM-SECRET>
```

---

## 🧑‍💼 ROLE-BASED ACCESS CONTROL (RBAC)

### Admin Capabilities
```
✅ /api/v1/admin/*           - Admin endpoints
✅ /api/v1/users/*           - User management
✅ /api/v1/governance/*      - Governance oversight
✅ /api/v1/assessments/*     - All assessments
✅ /api/v1/audit-logs/*      - Audit access
```

### Recruiter Capabilities
```
✅ /api/v1/assessments/cv    - CV assessment
✅ /api/v1/assessments/jd    - JD analysis
✅ /api/v1/assessments/alignment - CV-to-JD matching
✅ /api/v1/assessments/list  - View assessments
❌ /api/v1/admin/*           - No admin access
❌ /api/v1/users/*           - No user management
```

### Candidate Capabilities
```
✅ /api/v1/assessments/cv    - Self CV assessment
✅ /api/v1/assessments/recommendations - Get recommendations
✅ /api/v1/profile/*         - Profile management
❌ /api/v1/assessments/list  - Cannot see others' assessments
❌ /api/v1/admin/*           - No admin access
❌ /api/v1/recruiter/*       - No recruiter functions
```

---

## 📝 TESTING WORKFLOWS

### Workflow 1: Admin User Testing

```bash
# 1. Create admin account
cd backend
python create_test_admin.py

# 2. Login via web UI
# Email: admin@truematch.local
# Password: admin123
# URL: http://localhost:3000/login

# 3. Test admin functions
# - View all users
# - Manage assessments
# - Monitor governance
# - Access audit logs
```

### Workflow 2: Recruiter Testing

```bash
# 1. Run tests with recruiter fixture
pytest backend/tests/test_assessments.py -v -k recruiter

# 2. Or use API directly
TOKEN=$(python -c "from app.core.security import create_access_token; print(create_access_token(..., role='recruiter'))")

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/assessments/list

# 3. Test recruiter functions
# - Upload CV for assessment
# - Analyze job descriptions
# - Get CV-to-JD alignment scores
```

### Workflow 3: Candidate Testing

```bash
# 1. Signup via web UI
# URL: http://localhost:3000/signup
# Fill in: Email, Password, Name

# 2. Login as candidate
# Email: your-email@example.com
# Password: your-password

# 3. Test candidate functions
# - Upload resume
# - Self-assessment
# - View recommendations
# - Download reports
```

---

## 🛠️ TROUBLESHOOTING

### "User not found" Error

```
Status: 401 Unauthorized
Detail: "Not authenticated"
```

**Solutions**:
1. Check JWT token is valid (not expired)
2. Verify user exists in database
3. Ensure token includes correct `role`
4. Check `Authorization: Bearer <token>` header format

### "Invalid Credentials" Error

```
Status: 401 Unauthorized
Detail: "Invalid email or password"
```

**Solutions**:
1. Verify email address is correct
2. Check password (case-sensitive)
3. Ensure user account exists
4. Try creating test user with fixture

### "Permission Denied" Error

```
Status: 403 Forbidden
Detail: "Insufficient permissions"
```

**Solutions**:
1. Verify user has correct role
2. Check endpoint requires correct permission
3. Ensure JWT token includes role claim
4. Try with admin account to test access

### Test Database Issues

```
RuntimeError: Failed to create test database
```

**Solutions**:
```bash
# Check PostgreSQL is running
psql --version

# Verify PostgreSQL connection
psql -U postgres -h localhost -c "SELECT 1"

# Set test DB credentials
export TEST_DB_HOST=localhost
export TEST_DB_PORT=5432
export TEST_DB_USER=postgres
export TEST_DB_PASSWORD=yourpassword
```

---

## ✅ VERIFICATION CHECKLIST

- [x] Admin account created (`admin@truematch.local`)
- [x] Recruiter fixture available in tests
- [x] Candidate accounts can be created via signup
- [x] JWT token generation configured
- [x] Role-based access control enforced
- [x] Test database ready
- [x] Environment variables configured
- [x] Security settings in place

---

## 📊 SUMMARY

| Feature | Admin | Recruiter | Candidate |
|---------|-------|-----------|-----------|
| CV Assessment | ✅ View all | ✅ Run | ✅ Own only |
| JD Analysis | ✅ View all | ✅ Run | ❌ |
| User Management | ✅ Full | ❌ | ❌ |
| Governance | ✅ Monitor | ❌ | ❌ |
| Self-Assessment | ✅ View all | ✅ Run | ✅ Run |
| Reports | ✅ All | ✅ Team | ✅ Own |
| Audit Logs | ✅ Full | ❌ | ❌ |

---

## 🚀 NEXT STEPS

1. ✅ Create admin account: `python create_test_admin.py`
2. ✅ Login as admin: http://localhost:3000/login
3. ✅ Test recruiter functions via API
4. ✅ Create candidate accounts via signup
5. ✅ Run assessment workflows
6. ✅ Verify governance gates

**Status**: 🟢 All Test Access Ready

---

**Last Updated**: 2026-07-06  
**Maintained By**: TrueMatch Development Team  
**Security Level**: Development/Testing Only
