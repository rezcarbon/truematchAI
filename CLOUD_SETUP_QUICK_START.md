# Cloud Setup Quick Start Guide
## Deploy AI-Native TrueMatch for Autonomous Agent Testing

**Choose Your Path:**

---

## 🥇 FASTEST & CHEAPEST: Hetzner

**Cost:** $5.29/month  
**Setup Time:** 10 minutes  
**Best For:** MVP testing, autonomous agent prototyping

### Step-by-Step

```bash
# 1. Sign up: https://www.hetzner.com
# 2. Create CPX11 server (4 vCPU, 8GB RAM)
# 3. Get IP address from email
# 4. SSH in:

ssh root@<your-server-ip>

# 5. Run deployment script
cd /tmp
curl -O https://raw.githubusercontent.com/yourusername/TrueMatch/main/scripts/deploy-hetzner.sh
bash deploy-hetzner.sh

# 6. Access services:
# API: http://<your-server-ip>:8000
# Grafana: http://<your-server-ip>:3001 (admin/admin)
# Database: postgresql://user@localhost/truematch
```

### After Deployment

```bash
# Test autonomous agent
curl -X POST http://<ip>:8000/api/v1/cv-analysis \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"resume_id": "uuid", "target_role": "Engineer"}'

# Monitor in Grafana
open http://<ip>:3001

# View logs
docker-compose logs -f backend
```

---

## 🥈 MOST RELIABLE: DigitalOcean

**Cost:** $18+/month  
**Setup Time:** 5 minutes  
**Best For:** Production testing, reliability focused

### Step-by-Step

```bash
# 1. Sign up: https://www.digitalocean.com ($200 free credit)
# 2. Click "Create" → "Droplets"
# 3. Choose "Docker" app
# 4. Select "$18/month" (6 vCPU, 12GB)
# 5. Create

# 6. SSH in:
ssh root@<your-droplet-ip>

# 7. Deploy (Docker already installed)
git clone https://github.com/yourusername/TrueMatch.git
cd TrueMatch
docker-compose up -d

# 8. Access
# API: http://<your-droplet-ip>:8000
# Grafana: http://<your-droplet-ip>:3001
```

### Optional: Add Managed Database

```bash
# In DigitalOcean dashboard:
# 1. Click "Create" → "Databases"
# 2. Choose PostgreSQL ($10/month)
# 3. Update backend/.env with connection string
# 4. Restart: docker-compose restart backend
```

---

## 🚀 SCALE TESTING: Hetzner + Vast.ai (Hybrid)

**Cost:** $5 (Hetzner) + $30-50 (Vast.ai) = $35-55/month  
**Setup Time:** 15 minutes  
**Best For:** Testing 8-16 concurrent autonomous agents

### Architecture

```
Hetzner CPX11 (Always On)
├─ PostgreSQL database
├─ Redis cache
├─ API server
└─ Admin agent

Vast.ai Instance (On Demand)
├─ 4-8 Celery worker processes
├─ Concurrent agents (4-16)
└─ High-speed processing

Both connect to:
└─ Claude API (for AI processing)
```

### Setup

```bash
# 1. Deploy Hetzner (see above)

# 2. Get database connection string:
# In Hetzner instance:
docker-compose logs database | grep CONNECTION

# 3. Sign up at https://www.vast.ai
# 4. In Vast.ai dashboard:
#    - Search: "pytorch" or "cuda"
#    - Select instance with 8GB+ RAM
#    - Click "Rent"

# 5. SSH into Vast.ai instance
# 6. Deploy TrueMatch worker:
git clone <repo>
cd TrueMatch
export DATABASE_URL="<from-hetzner>"
docker-compose run --rm backend celery -A app.workers.celery_app worker

# 7. Monitor in Hetzner Grafana
# http://<hetzner-ip>:3001
```

---

## 💡 DECISION MATRIX

```
Your Choice = Your Situation + Your Budget

┌─────────────────────────────────────────────────────────────┐
│ WHAT'S YOUR PRIORITY?                                       │
├─────────────────────────────────────────────────────────────┤

❓ Cost is everything
├─→ Hetzner CPX11 ($5/month)
└─→ Total: $12 with Claude API

❓ I want to test multiple agents simultaneously  
├─→ Hetzner CPX21 ($10) + Vast.ai ($30-50)
└─→ Total: $50-70/month for 8-16 agents

❓ I want reliability and easy scaling
├─→ DigitalOcean Droplet ($18)
└─→ Total: $33 with Claude API

❓ I want everything managed
├─→ DigitalOcean App Platform ($12+)
├─→ Add Managed Database ($10)
└─→ Total: $37+/month

❓ I need GPU for embeddings testing
├─→ Vast.ai GPU Instance ($0.30/hr)
└─→ Total: Varies by usage (good for bursts)

❓ I want serverless/pay-per-execution
├─→ RunPod Serverless ($0.50-3/hr)
└─→ Only if <4 hours/day usage
```

---

## Quick Comparison

| Factor | Hetzner | DigitalOcean | Vast.ai | RunPod |
|--------|---------|--------------|---------|---------|
| **Cost** | $5 ⭐⭐⭐ | $18 ⭐⭐ | $0.20/hr ⭐⭐⭐ | Pay/execute ⭐⭐ |
| **Setup** | 10m ⭐⭐⭐ | 5m ⭐⭐⭐⭐ | 15m ⭐⭐ | 2m ⭐⭐⭐⭐⭐ |
| **Support** | Community ⭐ | Excellent ⭐⭐⭐⭐ | Marketplace ⭐⭐ | Good ⭐⭐⭐ |
| **Reliability** | 99.9% ⭐⭐⭐ | 99.99% ⭐⭐⭐⭐⭐ | 95% ⭐⭐ | 99% ⭐⭐⭐⭐ |
| **Scaling** | Manual | Auto ⭐⭐⭐⭐⭐ | Easy ⭐⭐⭐⭐ | Auto ⭐⭐⭐⭐⭐ |

---

## MY EXACT RECOMMENDATION FOR YOU

Based on your setup (testing AI-native autonomous agents):

### **Phase 1: This Week (Testing MVP)**
```
Deploy on: Hetzner CPX11
Cost: $5.29/month
Agents: 2-4 concurrent
Time to production: ~15 minutes

Command:
ssh root@<ip> < scripts/deploy-hetzner.sh
```

### **Phase 2: Next Week (Scale Testing)**
```
Add: Vast.ai instance ($30-50/month)
Agents: 8-16 concurrent
Celery workers: 8-16 processes
Can test full autonomous operation

Additional command:
export DATABASE_URL=<from-hetzner>
docker-compose run celery worker
```

### **Phase 3: Week 3+ (Production Validation)**
```
Upgrade to: DigitalOcean ($18/month)
Add managed DB: ($10/month)
Agents: 16-32+ concurrent
Production-ready infrastructure

Follow: DigitalOcean deploy steps above
```

**Total Cost Progression:**
- Week 1-2: $12/month (Hetzner + Claude)
- Week 3-4: $60/month (Hetzner + Vast.ai + Claude)
- Week 5+: $45/month (DigitalOcean + Claude)

---

## Environment Configuration

### For Any Provider

```bash
# backend/.env template
ENVIRONMENT=staging
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/truematch
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=sk-ant-xxxxx
SECRET_KEY=<generate-new>
JWT_SECRET=<generate-new>

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_PASSWORD=admin

# Cloud-specific
CLOUD_PROVIDER=hetzner  # or digitalocean, vast, runpod
INSTANCE_SIZE=cpx11     # hetzner specific
REGION=us-east-1        # your region
```

---

## Testing Autonomous Agents

Once deployed, test with:

```bash
# 1. Create test candidate
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -d '{"email": "agent1@test.com", "password": "Test123!"}'

# 2. Upload resume (creates test data)
curl -X POST http://localhost:8000/api/v1/resumes \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample-resume.pdf"

# 3. Trigger CV analysis (async, calls Claude)
curl -X POST http://localhost:8000/api/v1/cv-analysis \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"resume_id": "...", "target_role": "Senior Engineer"}'

# 4. Monitor task processing
curl http://localhost:8000/api/v1/cv-analysis/<id>

# 5. View metrics
open http://localhost:3001  # Grafana
```

---

## Monitoring & Logs

### Via Grafana (Built-in)

```bash
http://<your-ip>:3001
Username: admin
Password: admin

Dashboards:
├─ API Performance (requests/sec, latency)
├─ Database Health (connections, queries)
├─ Celery Workers (task queue depth, success rate)
└─ System Resources (CPU, memory, disk)
```

### Via Logs

```bash
# Backend logs
docker-compose logs -f backend

# Celery worker logs
docker-compose logs -f celery

# Database logs
docker-compose logs -f database

# All logs
docker-compose logs -f
```

---

## Troubleshooting

### "Connection refused" on port 8000
```bash
# Check if container is running
docker-compose ps

# Check logs
docker-compose logs backend

# Restart
docker-compose restart backend
```

### "Database connection error"
```bash
# Check database is running
docker-compose ps database

# Check credentials in .env
cat backend/.env | grep DATABASE

# Verify PostgreSQL is listening
docker-compose exec database psql -U user -c "SELECT 1"
```

### High CPU/Memory usage
```bash
# Check resource usage
docker stats

# Reduce worker concurrency
# Edit docker-compose.yml:
# CELERY_CONCURRENCY=2  (default: 4)

# Restart
docker-compose restart celery
```

---

## Next Steps

1. **Pick your provider** above (recommend Hetzner for MVP)
2. **Follow deployment steps** (15 minutes)
3. **Test autonomous agents** (create candidate, run CV analysis)
4. **Monitor in Grafana** (view metrics, logs)
5. **Scale when ready** (add Vast.ai or upgrade to DigitalOcean)

---

## Support

- **Detailed guide:** See `docs/CLOUD_INFRASTRUCTURE_ANALYSIS.md`
- **Deployment issues:** Check `docker-compose logs`
- **Agent issues:** Check `docs/DISASTER_RECOVERY.md`
- **Monitoring:** Visit Grafana at `http://<ip>:3001`

**Questions? Check the Full Analysis Document!**

