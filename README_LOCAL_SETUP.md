# 🚀 TrueMatch Local Development - Quick Start Guide

## Status: ✅ FULLY OPERATIONAL

Your TrueMatch codebase has been successfully recovered and configured for local development and testing.

---

## 🎯 What's Ready

- ✅ **Backend** (FastAPI + Python 3.12)
- ✅ **Frontend** (Next.js 14 + React 18)
- ✅ **Database** (PostgreSQL 15 with 76+ tables)
- ✅ **Cache** (Redis)
- ✅ **Dependencies** (All installed)
- ✅ **Configuration** (Development defaults)

---

## 🚀 Getting Started (2 Options)

### Option A: Automated (Recommended) ⭐
```bash
cd /Users/modvader/Documents/codebase/truematch
./start-services.sh
```

This single command:
1. Ensures PostgreSQL & Redis are running
2. Applies any pending database migrations
3. Starts FastAPI backend (port 8000)
4. Starts Next.js frontend (port 3000)

Then open your browser to **http://localhost:3000**

### Option B: Manual (Terminal per service)

**Terminal 1 - Backend**
```bash
cd /Users/modvader/Documents/codebase/truematch/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
→ Backend API: http://localhost:8000
→ Swagger Docs: http://localhost:8000/docs

**Terminal 2 - Frontend**
```bash
cd /Users/modvader/Documents/codebase/truematch/web
npm run dev
```
→ Frontend: http://localhost:3000

---

## 📊 Project Architecture

```
TrueMatch: AI-Powered ATS & Hiring Assessment Platform

┌─────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 14 + React 18 + TypeScript)             │
│  • Admin dashboard                                           │
│  • Candidate portal                                          │
│  • Job posting & analysis                                    │
│  • Interview scheduling & assessment                         │
└─────────────────────────────────────────────────────────────┘
                         ↕ /api proxy
┌─────────────────────────────────────────────────────────────┐
│  Backend (FastAPI + Python 3.12)                            │
│  • CV/JD analysis engine (Claude API)                        │
│  • ATS core (pipeline, candidates, assessments)             │
│  • Autonomous ingest layer (email, files)                    │
│  • Billing system (Stripe)                                   │
│  • Chat/AI conversations                                     │
│  • Training simulations                                      │
│  • Governance & compliance                                   │
└─────────────────────────────────────────────────────────────┘
         ↕ SQLAlchemy (async)    ↕ Redis
┌──────────────────────┐    ┌──────────────────────┐
│  PostgreSQL 15       │    │  Redis Cache         │
│  • 76+ tables        │    │  • Rate limiting     │
│  • Users, CVs, Jobs  │    │  • Session store     │
│  • Assessments, etc  │    │  • Task queue        │
└──────────────────────┘    └──────────────────────┘
```

---

## 🛠️ Key Features (All Ready)

### AI/ML Capabilities
- **CV/JD Analysis**: Upload resumes and job descriptions, Claude analyzes them
- **Semantic Matching**: AI-powered candidate-to-job matching
- **Transition Intelligence**: Career path predictions
- **Training Recommendations**: Personalized learning paths

### ATS Platform
- **Pipeline Management**: Organize candidates through stages
- **Interview Scheduling**: Calendar integration
- **Assessment Engine**: Custom assessments & scoring
- **Candidate Tracking**: Full candidate lifecycle

### Autonomous Features
- **Email Ingestion**: Auto-import CVs/JDs from email
- **Filesystem Ingestion**: Monitor folders for new documents
- **Auto-Approval Gates**: Intelligent decision making
- **Compliance Checks**: Bias detection, governance

### Business Features
- **Billing**: Stripe integration (ready)
- **Referrals**: Candidate referral program
- **Notifications**: Email, Slack, push notifications
- **Admin Controls**: Full governance settings

---

## 🧪 Testing Your Setup

### Backend Health Check
```bash
# Check API is running
curl http://localhost:8000/

# View API documentation
open http://localhost:8000/docs

# Check database
curl http://localhost:8000/api/health
```

### Frontend Health Check
```bash
# Frontend should load
open http://localhost:3000

# Check console for errors (F12)
```

### Database Health Check
```bash
# Connect to database
PGPASSWORD=truematch_dev psql -U truematch -h localhost -d truematch_dev

# In PostgreSQL:
SELECT version();
\dt                              # List all tables
SELECT COUNT(*) FROM users;     # Check users table
\q
```

---

## 📁 Project Structure

```
/Users/modvader/Documents/codebase/truematch/
├── backend/
│   ├── venv/                    ← Python 3.12 virtual environment
│   ├── app/
│   │   ├── api/                 ← REST API endpoints
│   │   ├── models/              ← SQLAlchemy models
│   │   ├── services/            ← Business logic
│   │   └── main.py              ← FastAPI app entry
│   ├── alembic/                 ← Database migrations
│   ├── .env                     ← Backend config (dev)
│   └── pyproject.toml           ← Dependencies
│
├── web/
│   ├── app/                     ← Next.js app directory
│   ├── components/              ← React components
│   ├── public/                  ← Static assets
│   ├── .env.local               ← Frontend config (dev)
│   └── package.json             ← npm dependencies
│
├── start-services.sh            ← Unified startup script
├── SETUP_COMPLETE.md            ← Full setup documentation
├── README_LOCAL_SETUP.md        ← This file
└── [Documentation files]
```

---

## ⚙️ Configuration

### Backend (.env)
Located at: `backend/.env`

Critical settings:
- `DATABASE_URL`: PostgreSQL connection
- `REDIS_URL`: Redis cache connection
- `ANTHROPIC_API_KEY`: Claude API key (optional for dev - currently mocked)
- `JWT_SECRET`: Token signing key (change in production)

### Frontend (.env.local)
Located at: `web/.env.local`

Settings:
- `NEXT_PUBLIC_API_BASE_URL`: Frontend-facing API path
- `BACKEND_API_URL`: Server-side backend URL
- `NEXTAUTH_SECRET`: NextAuth session key

---

## 🔧 Common Tasks

### Add a New Backend Endpoint
```bash
cd backend
source venv/bin/activate

# Edit app/api/v1/routes/my_feature.py
# Then register in app/api/v1/router.py
# Test at http://localhost:8000/docs
```

### Add a New Frontend Page
```bash
cd web

# Create app/my-page/page.tsx (Next.js 14 app router)
# Styles in app/my-page/page.module.css or use Tailwind
# Test at http://localhost:3000/my-page
```

### Add a Database Migration
```bash
cd backend
source venv/bin/activate

# Auto-generate from model changes
python -m alembic revision --autogenerate -m "Add new_column"

# Review migration file in alembic/versions/
python -m alembic upgrade head
```

### Run Tests
```bash
# Backend tests
cd backend && source venv/bin/activate && python -m pytest

# Frontend tests
cd web && npm test
```

### Debug Database
```bash
PGPASSWORD=truematch_dev psql -U truematch -h localhost -d truematch_dev

# Useful commands:
# \dt              - List all tables
# \di              - List indexes
# \d table_name    - Describe table
# SELECT * FROM table LIMIT 5;
# \x on            - Extended display
```

---

## 📞 Getting Help

### Check Logs
```bash
# Backend logs (when running)
# Check terminal output where backend is running

# Database logs
tail -f /opt/homebrew/opt/postgresql@15/var/server.log

# Frontend logs (in browser console)
# Press F12 in browser
```

### Restart Services
```bash
# PostgreSQL
brew services restart postgresql@15

# Redis
brew services restart redis

# Kill and restart Node/Python processes
# (Or press Ctrl+C in their terminals and run again)
```

### Reset Everything
```bash
# WARNING: This deletes all local data!

# Stop services
brew services stop postgresql@15
brew services stop redis

# Clean up
rm -rf backend/venv backend/.env web/node_modules web/.env.local

# Restart and recreate
./start-services.sh
```

---

## 🎓 Learning Resources

- **Backend**: FastAPI docs http://localhost:8000/docs
- **Database**: PostgreSQL docs https://www.postgresql.org/docs/
- **Frontend**: Next.js docs https://nextjs.org/docs
- **ORM**: SQLAlchemy docs https://docs.sqlalchemy.org/
- **Migrations**: Alembic docs https://alembic.sqlalchemy.org/

---

## ✨ Next Steps

1. **Explore the API** → http://localhost:8000/docs
2. **Test the Frontend** → http://localhost:3000
3. **Upload a CV** → Test CV/JD analysis
4. **Create a Job** → Test job matching
5. **Read the code** → Understand the architecture

---

## 📝 Notes

- **Development Mode**: All features work locally; some external integrations (Anthropic API, Stripe, email) require API keys
- **Database**: PostgreSQL 15 with async connections via SQLAlchemy
- **Auto-reload**: Both backend (FastAPI) and frontend (Next.js) auto-reload on code changes
- **Time Zone**: All timestamps are UTC
- **Authentication**: JWT + NextAuth configured for local development

---

## 🚀 Ready to Code!

```bash
cd /Users/modvader/Documents/codebase/truematch
./start-services.sh
```

Open **http://localhost:3000** and start building!

---

**Last Setup**: July 4, 2026
**Status**: ✅ All Systems Operational
**Questions?**: Check SETUP_COMPLETE.md for detailed troubleshooting
