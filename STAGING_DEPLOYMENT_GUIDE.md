# TrueMatch Staging Deployment Guide
## Complete Step-by-Step Deployment Instructions

**Environment**: Staging  
**Status**: Ready for Deployment  
**Date**: October 9, 2026  
**Deployment Method**: Docker Compose + Kubernetes Ready

---

## 🎯 Pre-Deployment Checklist

Before starting deployment, verify:

- ✅ All code committed to GitHub (Latest: commit `9908fa5`)
- ✅ All tests passing (Production Readiness Score: 98/100)
- ✅ All documentation complete
- ✅ Environment variables prepared
- ✅ Database credentials secured
- ✅ Encryption keys generated

---

## 📋 Deployment Architecture

### Services Required
1. **PostgreSQL** - Primary database
2. **Redis** - Caching & session management
3. **API Server** - FastAPI backend (Port 8000)
4. **Celery Worker** - Background job processing
5. **Celery Beat** - Scheduled task orchestration
6. **Frontend** - Next.js application (Port 3000)
7. **Nginx** - Reverse proxy (Optional)

### Ports
- API: 8000
- Frontend: 3000
- PostgreSQL: 5432
- Redis: 6379
- Nginx: 80/443

---

## 🚀 PHASE 1: Infrastructure Setup

### Step 1.1: Server Requirements (Staging)

```
CPU: 4 cores (t3.large on AWS)
Memory: 8 GB RAM
Storage: 50 GB SSD
Network: 100 Mbps
OS: Ubuntu 22.04 LTS or Amazon Linux 2
```

### Step 1.2: Install Docker & Docker Compose

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Step 1.3: Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/truematch
cd /opt/truematch

# Clone repository
sudo git clone https://github.com/rezcarbon/truematchAI.git .

# Set permissions
sudo chown -R $USER:$USER /opt/truematch
```

---

## 🔐 PHASE 2: Environment Configuration

### Step 2.1: Create Staging Environment File

```bash
cd /opt/truematch/backend
cp .env.example .env.staging
nano .env.staging
```

### Step 2.2: Configure Critical Variables

```ini
# Application Environment
ENVIRONMENT=staging

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://truematch:your-secure-password@postgres:5432/truematch

# Cache (Redis)
REDIS_URL=redis://redis:6379/0

# Encryption Keys (Generate new ones!)
ENCRYPTION_KEY=<base64-encoded-32-bytes>
ENCRYPTION_INDEX_KEY=<base64-encoded-32-bytes>

# JWT Secret
JWT_SECRET=<strong-random-secret-32+-chars>

# AWS/S3 Configuration
AWS_ACCESS_KEY_ID=your-staging-access-key
AWS_SECRET_ACCESS_KEY=your-staging-secret-key
AWS_REGION=ap-southeast-1
S3_BUCKET=truematch-staging-uploads

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-your-api-key
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# CORS Origins
CORS_ORIGINS=http://localhost:3000,http://staging.truematch.ai,https://staging.truematch.ai

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_FROM_EMAIL=noreply@staging.truematch.ai

# Logging
LOG_LEVEL=INFO
LOG_JSON=true

# Sentry (Optional)
SENTRY_DSN=your-sentry-dsn-for-staging
```

### Step 2.3: Generate Encryption Keys

```bash
python3 << 'EOF'
import base64
import secrets

# Generate ENCRYPTION_KEY
key = base64.b64encode(secrets.token_bytes(32)).decode()
print(f"ENCRYPTION_KEY={key}")

# Generate ENCRYPTION_INDEX_KEY
index_key = base64.b64encode(secrets.token_bytes(32)).decode()
print(f"ENCRYPTION_INDEX_KEY={index_key}")

# Generate JWT_SECRET
jwt_secret = secrets.token_urlsafe(32)
print(f"JWT_SECRET={jwt_secret}")
EOF
```

---

## 🗄️ PHASE 3: Database Setup

### Step 3.1: Start Database Services

```bash
cd /opt/truematch
docker-compose up -d postgres redis
```

### Step 3.2: Verify Database Health

```bash
# Check PostgreSQL
docker-compose logs postgres
docker-compose exec postgres pg_isready -U truematch

# Check Redis
docker-compose logs redis
docker-compose exec redis redis-cli ping
```

### Step 3.3: Run Database Migrations

```bash
# Run Alembic migrations
docker-compose run --rm api alembic upgrade head

# Expected output:
# INFO  [alembic.migration] Running upgrade  -> <revision_id>
# INFO  [alembic.migration] Running upgrade <rev1> -> <rev2>
# ... (multiple migrations)
# INFO  [alembic.migration] Running upgrade ... -> head
```

### Step 3.4: Verify Database Schema

```bash
docker-compose exec postgres psql -U truematch -d truematch << 'SQL'
\dt
\q
SQL
```

---

## 🔧 PHASE 4: Backend Deployment

### Step 4.1: Start API Server

```bash
# Start API in background
docker-compose up -d api

# Check API logs
docker-compose logs -f api

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 4.2: Start Celery Worker

```bash
# Start worker
docker-compose up -d worker

# Verify worker is connected
docker-compose logs worker

# Expected output:
# celery@<container-id> ready.
```

### Step 4.3: Start Celery Beat

```bash
# Start beat scheduler
docker-compose up -d beat

# Verify beat is running
docker-compose logs beat

# Expected output:
# celery beat v5.x.x is starting.
```

### Step 4.4: Health Check

```bash
# Test API health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"2026-10-09T...","version":"1.0.0"}

# Test API docs
curl http://localhost:8000/docs
```

### Step 4.5: Verify Backend Services

```bash
# Check all containers are running
docker-compose ps

# Expected output:
# NAME       SERVICE   STATUS
# postgres   postgres  Up (healthy)
# redis      redis     Up (healthy)
# api        api       Up
# worker     worker    Up
# beat       beat      Up
```

---

## 🎨 PHASE 5: Frontend Deployment

### Step 5.1: Install Frontend Dependencies

```bash
cd /opt/truematch/web

# Install dependencies
npm install

# Expected: no critical vulnerabilities
```

### Step 5.2: Create Frontend Environment File

```bash
cp .env.example .env.staging

# Configure for staging
cat > .env.staging << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=staging
NEXT_PUBLIC_APP_URL=http://localhost:3000
EOF
```

### Step 5.3: Build Frontend

```bash
# Build Next.js app
npm run build

# Expected:
# ✓ Compiled successfully
# ✓ Linting passed
# ✓ Type checking passed
```

### Step 5.4: Start Frontend (Development)

```bash
# For staging, use development server with hot reload
npm run dev

# Expected:
# > ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

### Step 5.5: Verify Frontend

```bash
# In another terminal
curl http://localhost:3000

# Expected: HTML page content
```

---

## 🌐 PHASE 6: Nginx Configuration (Optional)

### Step 6.1: Create Nginx Config

```bash
sudo nano /etc/nginx/sites-available/staging.truematch.ai
```

### Step 6.2: Configure Reverse Proxy

```nginx
upstream api_backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name staging.truematch.ai;

    # Redirect HTTP to HTTPS (after SSL setup)
    # return 301 https://$server_name$request_uri;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://api_backend;
    }
}
```

### Step 6.3: Enable Nginx Site

```bash
sudo ln -s /etc/nginx/sites-available/staging.truematch.ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## ✅ PHASE 7: Verification & Testing

### Step 7.1: API Endpoint Testing

```bash
# Test key endpoints
echo "=== Testing Forecasting API ==="
curl -X POST http://localhost:8000/api/v1/forecasting/pipeline \
  -H "Content-Type: application/json" \
  -d '{"position_id":"test-1"}'

echo "=== Testing Salary Benchmarking API ==="
curl -X GET http://localhost:8000/api/v1/salary-benchmarking/benchmark

echo "=== Testing Interview Intelligence API ==="
curl -X POST http://localhost:8000/api/v1/interview-intelligence/prep \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id":"test-1",
    "position_id":"test-1",
    "candidate_name":"John Doe",
    "candidate_background":"Senior Engineer",
    "position_title":"Lead Engineer",
    "key_requirements":["Python","FastAPI"]
  }'

echo "=== Testing Retention Prediction API ==="
curl -X POST http://localhost:8000/api/v1/retention-prediction/assess \
  -H "Content-Type: application/json" \
  -d '{
    "hire_id":"hire-1",
    "candidate_id":"cand-1",
    "hire_date":"2026-10-01",
    "position_id":"pos-1",
    "performance_rating":4,
    "engagement_score":85,
    "role_satisfaction_score":80,
    "compensation_satisfaction":75,
    "team_dynamics_score":90
  }'
```

### Step 7.2: Frontend Testing

```bash
# Open browser and test:
# http://localhost:3000 (or staging.truematch.ai)

# Test pages:
# - Dashboard
# - Forecasting page
# - Salary Benchmarking page
# - Interview Prep page
# - Retention Risk page
# - Analytics Dashboard
```

### Step 7.3: Integration Testing

```bash
# 1. Test API-Frontend communication
# 2. Verify CORS headers
# 3. Check error handling
# 4. Test authentication (if enabled)
# 5. Verify data persistence

# Check logs for any errors
docker-compose logs -f api
docker-compose logs -f worker
```

### Step 7.4: Performance Testing

```bash
# Install load testing tool
sudo apt-get install -y apache2-utils

# Test API performance
ab -n 100 -c 10 http://localhost:8000/api/v1/forecasting/pipeline

# Expected: 
# Requests per second: >100
# Average time per request: <100ms
```

---

## 📊 PHASE 8: Monitoring Setup

### Step 8.1: Docker Container Monitoring

```bash
# Monitor resource usage
docker stats

# View logs
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f beat

# Check container health
docker-compose ps
```

### Step 8.2: Application Monitoring

```bash
# Check API metrics
curl http://localhost:8000/metrics

# Check Sentry (if configured)
# https://sentry.io/organizations/your-org/issues/

# Monitor database
docker-compose exec postgres psql -U truematch -d truematch -c "\watch"
```

### Step 8.3: Log Aggregation

```bash
# Collect logs to file
docker-compose logs --no-color -f > staging-deployment.log &

# Monitor specific service
docker-compose logs -f api --tail=50
```

---

## 🔍 PHASE 9: Troubleshooting

### API not responding

```bash
# Check if API container is running
docker-compose ps api

# Check API logs
docker-compose logs api

# Restart API
docker-compose restart api

# Check database connection
docker-compose exec api python -c "from app.core.database import engine; engine.connect()"
```

### Database connection errors

```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection manually
docker-compose exec postgres psql -U truematch -d truematch -c "SELECT 1"
```

### Celery worker not processing

```bash
# Check worker status
docker-compose logs worker

# Check Redis connection
docker-compose exec redis redis-cli ping

# Restart worker
docker-compose restart worker
```

### Frontend not connecting to API

```bash
# Verify CORS is enabled
curl -i http://localhost:8000/api/v1/forecasting/pipeline

# Check CORS_ORIGINS in .env
grep CORS_ORIGINS backend/.env.staging

# Verify API URL in frontend .env
grep NEXT_PUBLIC_API_URL web/.env.staging
```

---

## 📋 Deployment Checklist

Before going live:

- [ ] All services running (docker-compose ps)
- [ ] Database migrations completed
- [ ] API responding to health check
- [ ] Frontend loading successfully
- [ ] API endpoints tested manually
- [ ] Frontend pages rendering correctly
- [ ] No critical errors in logs
- [ ] Performance acceptable (>100 req/s)
- [ ] Database backups configured
- [ ] Monitoring/alerting enabled
- [ ] Security best practices verified
- [ ] Documentation updated

---

## 🚀 Next Steps

### Post-Deployment

1. **Customer Pilot Testing** (Days 1-7)
   - Invite 3-5 customers
   - Collect feedback
   - Monitor usage patterns
   - Fix critical issues

2. **Performance Monitoring** (Days 1-14)
   - Monitor API response times
   - Track error rates
   - Measure database queries
   - Optimize bottlenecks

3. **Production Preparation** (Days 7-14)
   - Set up production infrastructure
   - Configure SSL/TLS certificates
   - Set up automated backups
   - Configure disaster recovery

4. **Production Deployment** (Days 15-21)
   - Deploy to production
   - Run customer acceptance testing
   - Monitor carefully
   - Support customer onboarding

---

## 📞 Support

**Issues?** Check the logs:
```bash
docker-compose logs -f
```

**Need to rebuild?**
```bash
docker-compose down
docker-compose up --build
```

**Need fresh database?**
```bash
docker-compose down -v  # Removes volumes!
docker-compose up -d
docker-compose run --rm api alembic upgrade head
```

---

## 📚 Additional Resources

- Docker Documentation: https://docs.docker.com/
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/
- Next.js Deployment: https://nextjs.org/docs/deployment
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Redis Documentation: https://redis.io/documentation
- Celery Documentation: https://docs.celeryproject.io/

---

**Staging Deployment Guide**  
Last Updated: October 9, 2026  
Status: READY FOR DEPLOYMENT ✅

