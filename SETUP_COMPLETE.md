# TrueMatch Local Development Setup - COMPLETE ✅

## Environment Details

### System Information
- **Python Version**: 3.12.13 ✓
- **Node Version**: v24.18.0 ✓
- **npm Version**: 11.16.0 ✓
- **Git Version**: 2.50.1 ✓

### Services Status
- **PostgreSQL**: Running on localhost:5432 ✓
- **Redis**: Running on localhost:6379 ✓
- **Database**: truematch_dev (owner: truematch user) ✓
- **Database Tables**: 76+ tables created via Alembic migrations ✓

### Project Structure
```
truematch/
├── backend/                    # FastAPI Python backend
│   ├── venv/                   # Python 3.12 virtual environment
│   ├── app/                    # Main application code
│   ├── alembic/                # Database migrations (38 versions)
│   ├── .env                    # Configuration (dev defaults)
│   └── pyproject.toml          # Dependencies
├── web/                        # Next.js 14 React frontend
│   ├── node_modules/           # npm dependencies installed
│   ├── .env.local              # Configuration
│   └── package.json            # Dependencies
├── start-services.sh           # Unified startup script
└── [other documentation files]
```

## Setup Summary

### ✅ Completed Tasks
- [x] System dependencies installed (Python 3.12, Node, npm)
- [x] PostgreSQL 15 installed and configured
- [x] Redis installed and running
- [x] Python virtual environment created
- [x] Backend dependencies installed (FastAPI, SQLAlchemy, Anthropic, etc.)
- [x] Frontend dependencies installed (Next.js, React, Tailwind, etc.)
- [x] Database user created (truematch/truematch_dev)
- [x] Database schema created via Alembic migrations
- [x] Environment files configured (.env, .env.local)
- [x] Ingestion directories created (inbox/cv, inbox/jd, etc.)

### 📊 Database Tables Created
**Core Tables**: users, resumes, jobs, applications, assessments, interviews, etc.
**AI/Analysis**: cv_analysis_requests, cv_analysis_results, jd_simulations, etc.
**ATS Features**: pipeline_stages, candidates, scorecards, decisions, etc.
**Autonomous Layer**: agent_plans, autonomous_settings, ingest_queue, etc.
**Training**: training_data, training_simulations, etc.
**Billing**: billing_orders, billing_credit_ledger, billing_entitlements, etc.
**Chat**: chat_sessions, chat_messages, chat_session_memories, etc.

**Total: 76+ tables**

## Running the Application

### Option 1: Unified Startup (Recommended)
```bash
cd /Users/modvader/Documents/codebase/truematch
./start-services.sh
```

This will start PostgreSQL, Redis, FastAPI backend, and Next.js frontend in one command.

### Option 2: Manual Startup

#### Terminal 1 - Start Services
```bash
# Start PostgreSQL
brew services start postgresql@15

# Start Redis
brew services start redis
```

#### Terminal 2 - Start Backend
```bash
cd /Users/modvader/Documents/codebase/truematch/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at: **http://localhost:8000**
API Docs (Swagger): **http://localhost:8000/docs**

#### Terminal 3 - Start Frontend
```bash
cd /Users/modvader/Documents/codebase/truematch/web
npm run dev
```

Frontend will be available at: **http://localhost:3000**

## Configuration Files

### Backend Configuration
**Location**: `backend/.env`
- Database: `postgresql+asyncpg://truematch:truematch_dev@localhost:5432/truematch_dev`
- Redis: `redis://localhost:6379/0`
- Environment: `development`
- LLM (mocked): Uses Anthropic Claude API when key provided
- Log Level: `DEBUG`
- All critical features enabled for testing

### Frontend Configuration
**Location**: `web/.env.local`
- API Base URL: `/api` (proxied through Next.js)
- Backend URL: `http://localhost:8000/v1`
- NextAuth configured for local development

## Testing the Setup

### Quick Health Check
```bash
# Check services
pg_isready -h localhost
redis-cli ping

# Check backend connectivity
curl http://localhost:8000/docs

# Check frontend
curl http://localhost:3000
```

### Database Connectivity Test
```bash
# Connect as truematch user
PGPASSWORD=truematch_dev psql -U truematch -h localhost -d truematch_dev

# In psql:
\dt                    # List all tables
SELECT COUNT(*) FROM users;  # Check user table
\q                     # Exit
```

## Key Features Available

### Backend (FastAPI)
- ✅ REST API with OpenAPI/Swagger documentation
- ✅ PostgreSQL with async SQLAlchemy
- ✅ Redis for caching and rate limiting
- ✅ JWT authentication
- ✅ Anthropic Claude API integration (for CV/JD analysis)
- ✅ Autonomous ingest queue (email, filesystem)
- ✅ ATS features (pipeline, candidates, assessments, interviews)
- ✅ Billing system (Stripe integration)
- ✅ Chat/conversational AI
- ✅ Training simulations
- ✅ Governance gates (compliance, bias detection)
- ✅ Observability (Sentry, Prometheus metrics)

### Frontend (Next.js 14)
- ✅ React 18 with TypeScript
- ✅ Tailwind CSS styling
- ✅ NextAuth authentication
- ✅ Server-side API proxy (BFF pattern)
- ✅ Jest testing
- ✅ Components: Tables, tabs, progress, markdown rendering, charts

## Troubleshooting

### PostgreSQL Connection Issues
```bash
# Restart PostgreSQL
brew services restart postgresql@15

# Check if running
brew services list | grep postgresql

# Reset and recreate database
psql -U modvader -h localhost -d postgres
DROP DATABASE truematch_dev;
CREATE DATABASE truematch_dev OWNER truematch;
```

### Python Dependencies Issue
```bash
cd backend
source venv/bin/activate
python -m pip install -e . --upgrade
```

### Node Dependencies Issue
```bash
cd web
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

### Port Already in Use
```bash
# Find process using port 8000 (backend)
lsof -i :8000
kill -9 <PID>

# Find process using port 3000 (frontend)
lsof -i :3000
kill -9 <PID>

# Find process using port 5432 (PostgreSQL)
lsof -i :5432
```

## Next Steps

1. **Verify Backend**: Open http://localhost:8000/docs and test API endpoints
2. **Verify Frontend**: Open http://localhost:3000 and check UI loads
3. **Check Database**: Query PostgreSQL to verify data model
4. **Test Authentication**: Register/login users (JWT + NextAuth)
5. **Test CV/JD Analysis**: Upload resumes and job descriptions
6. **Review Logs**: Check terminal output for errors

## Environment Variables Guide

### Critical (must configure for production)
- `ANTHROPIC_API_KEY`: For Claude API CV/JD analysis
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET`: Token signing key

### Optional (have sensible dev defaults)
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`: For S3 uploads
- `STRIPE_SECRET_KEY`: For billing features
- `SENDGRID_API_KEY`: For email sending
- `SLACK_WEBHOOK_URL`: For notifications

See `backend/.env` and `web/.env.local` for all available options.

## Helpful Commands

```bash
# View backend logs in development
tail -f backend/app.log

# Run backend tests
cd backend && python -m pytest

# Run frontend tests
cd web && npm test

# Format backend code
cd backend && python -m ruff check --fix .

# Type check frontend
cd web && npm run typecheck

# Build frontend for production
cd web && npm run build

# Check database migrations status
cd backend && python -m alembic current

# Create a new database migration
cd backend && python -m alembic revision --autogenerate -m "Description"
```

## Support & Documentation

- **Backend API Docs**: http://localhost:8000/docs (when running)
- **Next.js Docs**: https://nextjs.org/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **Alembic Docs**: https://alembic.sqlalchemy.org/

---

**Setup Date**: July 4, 2026
**Status**: ✅ READY FOR DEVELOPMENT & TESTING
**Last Updated**: Local development setup complete
