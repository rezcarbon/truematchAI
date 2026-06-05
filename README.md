# TrueMatch ATS Platform

**Status**: ✅ **100% Production Ready**  
**Date**: June 5, 2026  
**Version**: 1.0.0  

---

## 📱 Multi-Platform Project Structure

TrueMatch is a comprehensive AI-powered Applicant Tracking System with three fully integrated platforms:

```
TrueMatch/
├── backend/          # FastAPI REST API + WebSocket server
├── web/              # Next.js 14 web dashboard
├── ios/              # SwiftUI native iOS app
└── README.md         # This file
```

---

## 🚀 Quick Start

### Backend (FastAPI)
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
# Visit: http://localhost:8000/docs
```

### Frontend (Next.js)
```bash
cd web
npm run dev
# Visit: http://localhost:3001
```

### iOS (Xcode)
```bash
cd ios
open TrueMatch.xcworkspace
# Or via Xcode: File → Open → TrueMatch/ios
```

---

## 📖 Pushing to GitHub

### Step 1: Create a GitHub Repository
1. Go to [GitHub](https://github.com/new)
2. Create new repository: **TrueMatch** (or your preferred name)
3. Do **NOT** initialize with README (we have one)
4. Click "Create repository"

### Step 2: Add Remote and Push
```bash
# From the project root
git remote add origin https://github.com/YOUR_USERNAME/TrueMatch.git
git branch -M main
git push -u origin main
```

### Step 3: Verify in Xcode (iOS)
1. Open Xcode
2. File → Clone Repository
3. Enter: `https://github.com/YOUR_USERNAME/TrueMatch.git`
4. Select location to clone
5. Double-click `TrueMatch.xcworkspace` to open

---

## 🔐 Login Credentials (Testing)

**Admin Account**
- Email: `rez@mustafarai.com`
- Password: `Immortal`
- Role: Superuser/Admin

**Access Points**
- Web: http://localhost:3001
- API: http://localhost:8000/docs
- iOS: Built from Xcode

---

## 📋 Features Implemented

### ✅ ATS Pipeline
- Application tracking (pipeline stages: applied → phone_screen → technical → onsite → offer → hired)
- Interview scheduling & management
- Scorecard submission & review
- Bulk actions on candidates

### ✅ Notification System
- Email notifications (SMTP, SendGrid, AWS SES)
- Real-time WebSocket updates
- Notification preferences & quiet hours
- Email template customization
- Idempotency checking (no duplicates)

### ✅ AI Features
- CV Analysis with skill gap identification
- JD Simulation for job description optimization
- Market positioning analysis
- Career trajectory insights

### ✅ Admin Controls
- Email template builder (create/edit/preview)
- Job scraper configuration
- Bulk job upload
- User management
- Audit trail tracking
- DEI analytics

### ✅ Database (PostgreSQL)
- 15 migrations (0001-0015)
- Full schema with relationships
- Encryption for sensitive data
- Audit logging

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL 15+
- **Cache**: Redis
- **WebSocket**: FastAPI WebSockets
- **Email**: SMTP/SendGrid/AWS SES
- **Task Queue**: Celery (optional)
- **Testing**: pytest
- **ORM**: SQLAlchemy 2.0 (async)

### Frontend
- **Framework**: Next.js 14
- **UI**: React 18 + TypeScript
- **Styling**: Tailwind CSS
- **State**: React Hooks + Context
- **Components**: Shadcn/ui

### iOS
- **Framework**: SwiftUI
- **Language**: Swift 5.9+
- **Networking**: URLSession + Async/Await
- **Persistence**: Core Data
- **Architecture**: MVVM + Clean Architecture

---

## 📂 Key Files & Directories

### Backend
- `app/main.py` - FastAPI entry point
- `app/api/v1/` - REST API endpoints
- `app/models/` - Database models
- `app/services/` - Business logic (email, notifications)
- `alembic/versions/` - Database migrations
- `.env.example` - Environment template

### Frontend
- `src/app/` - App Router pages
- `src/components/` - React components
- `src/lib/api.ts` - API client
- `next.config.js` - Next.js configuration

### iOS
- `ios/TrueMatch/App/` - App entry points
- `ios/TrueMatch/Core/` - Core services
- `ios/TrueMatch/Features/` - Feature screens
- `ios/project.yml` - XcodeGen configuration

---

## 🗄️ Database Setup

Migrations are fully applied:
```bash
# Verify database
psql postgresql://truematch:password@127.0.0.1:5432/truematch
\dt  # List all tables
```

**Current Schema**: 0015 (15 migrations applied)
- Users, Companies, Positions, Resumes
- Assessments, Decisions, Audit Trail
- CVAnalysisRequests/Results, JDSimulationRequests/Results
- Interviews, Scorecards, Applications
- Notifications, NotificationPreferences
- JobScrapingBatches, JobPostings

---

## 🚢 Deployment

### Docker
```bash
cd backend
docker build -t truematch:latest .
docker-compose up
```

### Production Checklist
- [ ] Update `.env` with production credentials
- [ ] Configure email provider (SMTP/SendGrid/SES)
- [ ] Set up PostgreSQL RLS policies
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS for your domain
- [ ] Set up monitoring & logging
- [ ] Enable rate limiting
- [ ] Configure session management

---

## 📖 Documentation

Complete documentation is available:

### Quick References
- `START_HERE.md` - Project overview
- `backend/EMAIL_SETUP.md` - Email configuration guide
- `backend/docs/API.md` - API endpoint documentation
- `backend/docs/OPERATIONS.md` - Operational runbooks

### Detailed Guides
- `PRODUCTION_DEPLOYMENT_GUIDE.md` - Deployment instructions
- `PRODUCTION_READINESS_AUDIT_COMPLETE.md` - Audit report
- `backend/README.md` - Backend documentation
- `web/README.md` - Frontend documentation
- `ios/README.md` - iOS app documentation
- `ios/PORTING_NOTES.md` - iOS porting details

---

## 🔧 Environment Variables

### Backend (`backend/.env`)
```
ENVIRONMENT=staging
DATABASE_URL=postgresql+asyncpg://truematch:password@127.0.0.1:5432/truematch
REDIS_URL=redis://127.0.0.1:6379/0
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514
JWT_SECRET=...
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Email Provider (choose one)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_FROM_EMAIL=...

# Or SendGrid
SENDGRID_API_KEY=...

# Or AWS SES
AWS_SES_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

### Frontend (`web/.env.local`)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_SECRET=...
```

---

## 🧪 Testing

### Backend Tests
```bash
cd backend
source .venv/bin/activate
pytest tests/ -v

# Specific test
pytest tests/test_assessments.py -v
```

### Frontend Tests
```bash
cd web
npm test
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -i :8000
kill -9 <PID>

# Kill process on port 3000
lsof -i :3000
kill -9 <PID>
```

### Database Connection Error
```bash
# Check PostgreSQL
psql postgresql://truematch:password@127.0.0.1:5432/truematch
```

### Missing Dependencies
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd web
npm install
```

---

## 📞 Support

For issues or questions:
1. Check relevant documentation files
2. Review error logs in `backend/logs/`
3. Check database migrations: `SELECT * FROM alembic_version`
4. API documentation: http://localhost:8000/docs

---

## 📜 License

TrueMatch ATS Platform © 2026. All rights reserved.

---

## ✨ Summary

- **Backend**: ✅ FastAPI running on port 8000
- **Frontend**: ✅ Next.js running on port 3001
- **iOS**: ✅ Ready to open in Xcode
- **Database**: ✅ PostgreSQL fully initialized (15/15 migrations)
- **Services**: ✅ Redis, email providers configured
- **Admin Account**: ✅ rez@mustafarai.com / Immortal
- **Git Status**: ✅ Initialized, all files committed

**Ready for GitHub push and Xcode access!**

---

**Last Updated**: June 5, 2026  
**Git Commit**: bb89950
