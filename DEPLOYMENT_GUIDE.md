# TrueMatch Deployment Guide (EC2)

**Status:** Ready for Deployment  
**Components:** Admin Dashboard + Recruiter Dashboard + Billing System  
**Date:** September 3, 2026

---

## Pre-Deployment Checklist

### ✅ Completed
- [x] Admin Dashboard - 100% production-ready
- [x] Recruiter Dashboard - 100% production-ready
- [x] Billing System - Database migration created (0048)
- [x] All code committed to GitHub
- [x] Docker images built and ready
- [x] Environment templates prepared

### ⏳ Pending (Need EC2 Details)
- [ ] EC2 host/IP provided
- [ ] SSH key verified
- [ ] Environment variables configured
- [ ] Deployment executed

---

## What's Included in This Deployment

### Frontend (Next.js + React)
- **Admin Dashboard** (28 pages)
  - User management, audit logs, analytics, billing, compliance
  - Real API integration with 30+ endpoints
  - Error handling, loading states, empty states
  - Dark mode support
  - CSV/PDF export

- **Recruiter Dashboard** (19 pages)
  - Candidates, positions, applications, pipeline
  - Agents, internal mobility, decision tracking
  - Resume upload, JD optimization
  - Real API integration with 36+ endpoints

### Backend (FastAPI)
- **Admin Endpoints** (30+)
- **Recruiter Endpoints** (36+)
- **Billing Endpoints** (15+)
  - Stripe checkout, webhooks, order management
  - Entitlements, credits, coupons
  - Admin fulfillment queue, reporting
- **ATS Integration** (Lever, Greenhouse)

### Database
- **PostgreSQL** with all migrations including 0048 (billing system)
- **5 Billing Tables:**
  - billing_orders
  - billing_entitlements
  - billing_credit_ledger
  - billing_coupons
  - billing_webhook_events

### Redis
- Caching, rate limiting, session management

---

## Required Information to Proceed

Please provide your EC2 connection details:

```
EC2 Host/DNS:  ___________________________
EC2 Username:  ___________________________
SSH Key Path:  ___________________________
```

**Example:**
```
EC2 Host/DNS:  ec2-54-123-45-67.compute.amazonaws.com
EC2 Username:  ubuntu
SSH Key Path:  ~/.ssh/truematch-staging-key.pem
```

---

## Deployment Command (Once Details Provided)

```bash
cd /tmp/truematchAI
chmod +x scripts/deploy-ec2.sh

# Deploy to EC2
./scripts/deploy-ec2.sh ubuntu@YOUR_EC2_HOST main web/.env.production
```

This will:
1. SSH into your EC2 instance
2. Pull latest code from GitHub
3. Build Docker images
4. Stop running services
5. Start services with new code
6. Run database migrations (including billing system)
7. Perform health checks
8. Display deployment summary

---

## Expected Deployment Time
- **Total: 10-15 minutes**
  - Code pull & build: 5-10 minutes
  - Service startup: 2-3 minutes
  - Migrations: 1 minute
  - Health checks: 1 minute

---

## Post-Deployment Access

Once deployed successfully, you'll have access to:

| Component | URL |
|-----------|-----|
| Admin Dashboard | http://YOUR_EC2_HOST:3000/admin |
| Recruiter Dashboard | http://YOUR_EC2_HOST:3000/recruiter |
| API Health | http://YOUR_EC2_HOST:8000/health |
| Billing Catalog | http://YOUR_EC2_HOST:8000/api/v1/billing/catalog |

---

## Waiting for Your EC2 Details

Once you provide the EC2 connection information, I'll execute the deployment immediately.

