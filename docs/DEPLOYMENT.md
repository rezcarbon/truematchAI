# TrueMatch Deployment Runbook

**Document Version:** 1.0  
**Last Updated:** 2026-06-07  
**Status:** Production Ready

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Post-Deployment Verification](#post-deployment-verification)
5. [Rollback Procedures](#rollback-procedures)
6. [Common Issues](#common-issues)

---

## Pre-Deployment Checklist

### Configuration & Secrets
- [ ] `SECRET_KEY` set in `.env` (32+ characters)
- [ ] `JWT_SECRET` set and securely generated
- [ ] `ANTHROPIC_API_KEY` set to valid Claude API key
- [ ] `DATABASE_URL` points to correct database
- [ ] `REDIS_URL` points to accessible Redis instance
- [ ] `ENCRYPTION_KEY` and `ENCRYPTION_INDEX_KEY` configured
- [ ] CORS origins updated for target domain
- [ ] Email configuration set (SMTP credentials)
- [ ] AWS credentials set if S3 enabled

### Code & Dependencies
- [ ] All tests passing (`pytest`)
- [ ] No linting errors (`ruff check`)
- [ ] No type errors (`pyright`)
- [ ] Database migrations applied
- [ ] Dependencies installed and locked
- [ ] Git working tree clean
- [ ] Version bumped in `app/main.py`

### Infrastructure
- [ ] PostgreSQL database accessible
- [ ] Redis instance running
- [ ] S3 bucket created (if using S3)
- [ ] SSL/TLS certificates installed
- [ ] Load balancer configured
- [ ] DNS updated (if applicable)

### Monitoring & Logging
- [ ] Prometheus configured to scrape metrics
- [ ] Grafana dashboards imported
- [ ] AlertManager connected
- [ ] Log aggregation (Loki) ready
- [ ] Error tracking (Sentry) configured

---

## Local Development Setup

### 1. Prerequisites

```bash
# Check Python version
python3 --version  # Should be 3.10+

# Check Docker is installed
docker --version
docker-compose --version

# Check PostgreSQL is installed
psql --version

# Check Redis is running
redis-cli ping
```

### 2. Environment Setup

```bash
cd ~/Desktop/TrueMatch/backend

# Copy template
cp .env.example .env

# Edit .env with your values
nano .env

# Key variables to set:
# - ENVIRONMENT=staging
# - DATABASE_URL=postgresql+asyncpg://truematch:password@localhost:5432/truematch
# - ANTHROPIC_API_KEY=sk-ant-xxxxx
# - SECRET_KEY=<generate new secret key>
# - JWT_SECRET=<secure random string>
```

### 3. Database Setup

```bash
# Create database and user
psql -U postgres -c "CREATE USER truematch WITH PASSWORD 'password';"
psql -U postgres -c "CREATE DATABASE truematch OWNER truematch;"

# Run migrations
cd backend
alembic upgrade head
```

### 4. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies (optional)
pip install -r requirements-dev.txt
```

### 5. Start Services

```bash
# Start backend
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# In another terminal, start frontend
cd web
npm install
npm run dev

# In another terminal, start Celery worker
cd backend
celery -A app.workers.celery_app worker --loglevel=info

# In another terminal, start Celery Beat (scheduler)
celery -A app.workers.celery_app beat --loglevel=info
```

### 6. Verify Setup

```bash
# Test API
curl http://localhost:8000/health

# Test frontend
open http://localhost:3000

# Test Celery
celery -A app.workers.celery_app inspect active

# Test database
python -c "from app.database import engine; print(engine)"
```

---

## Production Deployment

### 1. Pre-Flight Checks

```bash
# Run deployment verification script
./scripts/verify-deployment.sh

# Should output:
# ✅ All tests passing
# ✅ Database migrations applied
# ✅ Dependencies installed
# ✅ Configuration validated
# ✅ Secrets configured
```

### 2. Database Backup

```bash
# Create backup before deployment
./scripts/backup_database.sh

# Verify backup
ls -lh ./backups/
```

### 3. Deploy Backend

```bash
# Option A: Docker Compose
docker-compose -f docker-compose.yml up -d

# Option B: Manual deployment
# Stop old instance
systemctl stop truematch-backend

# Deploy new code
git pull origin main
python -m pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start new instance
systemctl start truematch-backend

# Verify
curl https://api.truematch.ai/health
```

### 4. Deploy Frontend

```bash
# Option A: Docker Compose
docker-compose -f docker-compose.web.yml up -d

# Option B: Manual deployment
cd web
git pull origin main
npm install
npm run build
npm run start

# Verify
curl https://app.truematch.ai
```

### 5. Start Background Workers

```bash
# Start Celery worker
celery -A app.workers.celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  --logfile=/var/log/truematch/celery-worker.log \
  --detach

# Start Celery Beat scheduler
celery -A app.workers.celery_app beat \
  --loglevel=info \
  --logfile=/var/log/truematch/celery-beat.log \
  --detach
```

### 6. Start Monitoring Stack

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Verify
curl http://localhost:9090     # Prometheus
curl http://localhost:3001     # Grafana (admin/admin)
curl http://localhost:3100     # Loki
```

---

## Post-Deployment Verification

### 1. Health Checks

```bash
# Liveness check (process up)
curl https://api.truematch.ai/livez
# Expected: {"status": "ok"}

# Readiness check (dependencies up)
curl https://api.truematch.ai/readyz
# Expected: {"status": "ready", "components": {...}}

# Application health
curl https://api.truematch.ai/health
# Expected: {"status": "ok", "environment": "production"}
```

### 2. Smoke Tests

```bash
# Test authentication
curl -X POST https://api.truematch.ai/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePassword123!"}'

# Test resume upload
curl -X POST https://api.truematch.ai/api/v1/resumes \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/resume.pdf"

# Test CV analysis
curl -X POST https://api.truematch.ai/api/v1/cv-analysis \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"resume_id": "uuid", "target_role": "Senior Backend Engineer"}'
```

### 3. Database Verification

```bash
# Check database connectivity
psql -h api.truematch.ai -U truematch -d truematch -c "SELECT VERSION();"

# Check table counts
psql -h api.truematch.ai -U truematch -d truematch -c "SELECT COUNT(*) FROM users;"

# Check recent backups
ls -lh ./backups/ | head -5
```

### 4. Logs Review

```bash
# Backend logs
docker-compose logs -f backend

# Frontend logs
docker-compose logs -f web

# Worker logs
docker-compose logs -f celery-worker

# Errors in last hour
grep "ERROR" /var/log/truematch/*.log | tail -20
```

### 5. Monitoring Verification

```bash
# Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets'

# Check for alerts
curl -s http://localhost:9093/api/v1/alerts | jq '.data'

# Grafana dashboard
open http://localhost:3001/d/truematch-api
```

---

## Rollback Procedures

### Immediate Rollback (< 1 hour after deployment)

```bash
# Stop new version
docker-compose down

# Restore from backup
./scripts/restore_database.sh ./backups/truematch_backup_<timestamp>.sql.gz

# Start old version
git checkout HEAD~1
docker-compose up -d

# Verify
curl https://api.truematch.ai/health
```

### Gradual Rollback (Blue-Green Deployment)

```bash
# If using blue-green:
# 1. Load balancer has two target groups: blue (prod), green (staging)
# 2. Current traffic on blue
# 3. Deploy new version to green
# 4. If issues detected, switch traffic back to blue

# Switch traffic to blue (old version)
aws elbv2 modify-listener \
  --listener-arn arn:aws:elasticloadbalancing:... \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...:targetgroup/blue/...
```

### Database-Only Rollback

```bash
# If only database migrations failed:
alembic downgrade -1

# Verify app still works
curl https://api.truematch.ai/health

# If multiple revisions needed
alembic downgrade -5
```

---

## Common Issues

### Issue: Database Connection Refused

**Symptoms:** 
```
ERROR: could not translate host name "db.example.com" to address
```

**Solution:**
```bash
# Verify DATABASE_URL in .env
echo $DATABASE_URL

# Test connection
psql -h <host> -U <user> -d <database>

# Check PostgreSQL is running
systemctl status postgresql

# Check firewall
sudo iptables -L | grep 5432
```

### Issue: Redis Connection Timeout

**Symptoms:**
```
ERROR: Error 111 connecting to 127.0.0.1:6379
```

**Solution:**
```bash
# Check Redis is running
redis-cli ping

# Restart Redis
systemctl restart redis-server

# Check Redis configuration
cat /etc/redis/redis.conf | grep bind
```

### Issue: High Memory Usage

**Symptoms:**
```
MemoryError: Unable to allocate 2.5 GiB for an array
```

**Solution:**
```bash
# Check current memory usage
docker stats

# Limit memory for containers
docker-compose down
# Edit docker-compose.yml and add:
# services:
#   backend:
#     mem_limit: 2g

# Restart
docker-compose up -d

# Monitor memory
watch -n 1 'docker stats'
```

### Issue: SSL/TLS Certificate Errors

**Symptoms:**
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solution:**
```bash
# Regenerate self-signed certificate (local only!)
openssl req -x509 -newkey rsa:4096 -nodes \
  -out backend/certs/cert.pem \
  -keyout backend/certs/key.pem \
  -days 365

# For production, use Let's Encrypt
certbot certonly --standalone -d api.truematch.ai

# Copy to nginx/load balancer
sudo cp /etc/letsencrypt/live/api.truematch.ai/fullchain.pem /etc/nginx/ssl/
sudo cp /etc/letsencrypt/live/api.truematch.ai/privkey.pem /etc/nginx/ssl/
```

### Issue: Celery Tasks Not Processing

**Symptoms:**
```
Task is in "pending" state indefinitely
```

**Solution:**
```bash
# Check Celery worker status
celery -A app.workers.celery_app inspect active

# Restart worker
systemctl restart celery-worker

# Clear failed tasks
celery -A app.workers.celery_app purge

# Check Redis queue
redis-cli KEYS "celery*" | head -10
```

---

## Deployment Checklist Template

Copy this checklist before each deployment:

```
Date: ____________________
Deployed By: ____________________
Version: ____________________

PRE-DEPLOYMENT:
[ ] Tests passing
[ ] Migrations reviewed
[ ] Configuration verified
[ ] Database backup created
[ ] Team notified

DEPLOYMENT:
[ ] Backend deployed
[ ] Database migrated
[ ] Frontend deployed
[ ] Workers started
[ ] Monitoring started

POST-DEPLOYMENT:
[ ] Health checks passing
[ ] Smoke tests passed
[ ] Logs reviewed for errors
[ ] Performance metrics normal
[ ] Team notified of completion

ROLLBACK (if needed):
[ ] Issue identified
[ ] Rollback initiated
[ ] Services restored
[ ] Database restored
[ ] Tests run
[ ] Team notified
[ ] Incident documented
```

---

## Support & Escalation

### On-Call Rotation
- **Primary:** [Name] - [Phone] - [Slack]
- **Secondary:** [Name] - [Phone] - [Slack]

### Escalation Contacts
- **Database DBA:** [Name] - [Phone]
- **Infrastructure:** [Name] - [Phone]
- **Security:** [Name] - [Phone]

### Communication Channels
- **Status Page:** status.truematch.ai
- **Slack Channel:** #truematch-incidents
- **Email:** ops@truematch.ai
- **PagerDuty:** https://truematch.pagerduty.com

