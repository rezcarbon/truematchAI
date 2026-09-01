# AWS Free Tier Optimization for TrueMatch AI
## Complete Free Tier Analysis & Cost-Optimized Deployment Strategy

**Document Version:** 1.0  
**Region:** ap-southeast-1 (Singapore)  
**Target Budget:** <$100/month (Testing Phase)  
**Account Type:** New AWS Account (eligible for Free Tier)  
**Last Updated:** 2026-07-21

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [AWS Free Tier Overview](#aws-free-tier-overview)
3. [Free Tier Services in ap-southeast-1](#free-tier-services-in-ap-southeast-1)
4. [TrueMatch AI Architecture](#truematch-ai-architecture)
5. [Cost Analysis: Two Deployment Options](#cost-analysis-two-deployment-options)
6. [Recommended Configuration (Option A)](#recommended-configuration-option-a)
7. [Advanced Configuration (Option B)](#advanced-configuration-option-b)
8. [Free Tier Service Limits & Monitoring](#free-tier-service-limits-monitoring)
9. [Cost Tracking & Alerts](#cost-tracking-alerts)
10. [Upgrade Path to Production](#upgrade-path-to-production)

---

## Executive Summary

For TrueMatch AI testing deployment within a $100/month budget, **Option A (Docker Compose on EC2)** is strongly recommended:

| Metric | Option A | Option B | Budget |
|--------|----------|----------|--------|
| **Total Monthly Cost** | $1-2 | $84-90 | $100 |
| **Free Tier Services** | All (100%) | Partial (70%) | - |
| **Compute** | EC2 t3.micro | EKS + EC2 | - |
| **Database** | RDS db.t3.micro | RDS db.t3.micro | - |
| **Cache** | ElastiCache t3.micro | ElastiCache t3.micro | - |
| **Suitable For** | Testing & Validation | Staging & Near-Prod | - |

**Recommendation:** Start with Option A. It provides **$98 monthly buffer** for unexpected costs and allows full feature validation before committing to Kubernetes infrastructure.

---

## AWS Free Tier Overview

### Three Free Tier Categories

#### 1. **Always Free** (No expiration, no credit card required for some)
- Services that offer perpetual free tier
- No time limit
- Usage limits apply

#### 2. **12-Month Free** (Expires after account creation date)
- Full 12 months from account creation
- Specific usage allowances
- Exact renewal: 12 calendar months from account activation

#### 3. **Free Trial** (Limited time, specific services)
- SageMaker, Lookout services: 2 months
- Amazon Connect: 1 month trial included

### AWS Free Tier Key Facts for ap-southeast-1

- **Eligibility Window:** 12 months from new account creation
- **Region Availability:** Most services available in ap-southeast-1
- **Limits:** Strict monthly usage limits per service
- **Stacking:** Free tier does NOT stack across AWS accounts
- **Expiration:** Automatic billing begins month 13 if resources remain running

---

## Free Tier Services in ap-southeast-1

### Compute

#### EC2 (Elastic Compute Cloud)
**Free Tier Allowance (12-month):**
- 750 hours/month of t2.micro OR t3.micro instance
- Storage: 30GB EBS (General Purpose gp2 or gp3)
- Data transfer: 1GB/month outbound (within AWS: free; out to internet: first 1GB free)
- Elastic IP address: 1 free per month (charged if unassociated)

**Important Notes:**
- 750 hours/month = 31.25 hours/day = ~continuous operation if single instance
- t3.micro = 1 vCPU, 1GB RAM, burstable performance
- Ideal for Docker workloads in testing phase
- **Cost if exceeded:** $0.0116/hour (~$8.50/month for continuous running beyond free tier)

**Best Use:** Primary compute for Docker Compose deployment

---

#### EC2 Auto Scaling
- Free (pay only for launched instances)
- Scales within t3.micro free tier limits

---

#### EKS (Elastic Kubernetes Service)
**Free Tier Allowance:**
- **NONE** - EKS cluster management costs $0.10/hour (~$73/month)
- Control plane is NOT free
- Worker nodes (EC2 instances) must be paid for separately
- Worker nodes can use t3.micro free tier if within 750 hours

**Cost Breakdown (if using EKS):**
- EKS control plane: $73/month (always)
- 1x t3.micro node: $0/month (within free tier)
- Total: $73/month (even with free tier instance)

**Best Use:** Production staging only (budget permits with buffer)

---

#### Lightsail
- $3.50/month for lightsail instances (after free trial)
- 1-month free trial available
- NOT included in standard free tier
- Limited scalability for FastAPI with 54 endpoints

---

### Database

#### RDS (Relational Database Service)
**Free Tier Allowance (12-month):**
- 1x db.t3.micro instance: 750 hours/month (continuous operation)
- Database engines: PostgreSQL, MySQL, MariaDB (choose one per 12-month term)
- Storage: 20GB/month (combined data + logs)
- Backup storage: 20GB/month (automated backups)
- Manual snapshots: Free (counts toward 20GB limit)
- Multi-AZ: NO (paid option, ~$1.50/month additional)
- Data transfer: 1GB/month inbound/outbound (beyond: $0.02/GB)

**PostgreSQL Configuration:**
- db.t3.micro: 1 vCPU, 1GB RAM
- 20GB storage is sufficient for testing (54 API endpoints + typical test data)
- Auto backup retention: 7 days default (within 20GB backup limit)

**Cost if exceeded:**
- Additional storage: $0.115/GB/month
- Additional backup storage: $0.095/GB/month
- Data transfer: $0.02/GB

**Best Use:** Primary application database

---

#### DynamoDB
**Free Tier Allowance (12-month):**
- 25GB storage
- 200M request units/month (write/read combined)
- Not ideal for structured relational data (TrueMatch AI uses PostgreSQL)

---

#### Elasticache (Redis & Memcached)
**Free Tier Allowance (12-month):**
- 1x cache.t3.micro node: 750 hours/month
- Redis or Memcached
- Single node (no replication in free tier)
- Data backup: Snapshots manual only (free)
- Multi-AZ: NO (charged feature)

**Redis Configuration:**
- cache.t3.micro: Sufficient for session/job queue storage
- 500MB memory (for testing Celery job queue)
- Automatic failover: NOT available in free tier
- Cluster mode: NOT available in free tier

**Cost if exceeded:**
- cache.t3.small (next tier): ~$0.033/hour (~$24/month)

**Best Use:** Celery job queue and session store

---

#### DocumentDB
- MongoDB-compatible
- Minimum: db.t3.small ($0.12/hour = $87/month minimum)
- NOT in free tier for ap-southeast-1
- Not recommended for this budget

---

### Storage

#### S3 (Simple Storage Service)
**Free Tier Allowance (12-month):**
- 5GB storage
- 20,000 GET requests/month
- 2,000 PUT requests/month
- 100GB data transfer IN (worldwide, free)
- 1GB data transfer OUT per month (first)
- Beyond 1GB OUT: $0.085/GB (varies by region)

**Use Cases:**
- Application logs
- Test data snapshots
- Static assets (if needed)

**Cost:** $0 (within usage limits for testing)

---

#### EBS (Elastic Block Storage)
**Included in EC2 Free Tier:**
- 30GB/month gp2 or gp3
- No additional cost (part of EC2 allocation)
- Snapshots to S3: 5GB within S3 free tier

---

#### Glacier & Archive Storage
- $0.004/GB/month (archive)
- $0.0036/GB/month (deep archive)
- Retrieval costs separate
- Not needed for testing

---

### Networking

#### VPC (Virtual Private Cloud)
**Free Tier Allowance:**
- Unlimited VPCs (default VPC included)
- Subnets: Unlimited
- Route tables: Unlimited
- Network ACLs: Unlimited
- Security groups: Unlimited
- Elastic IP: 1 free/month per instance (charges if unassociated)

**Cost:** $0 (completely free)

---

#### NAT Gateway
- $32/month + data processing ($0.045/GB)
- Alternative: NAT instance (t3.micro, uses EC2 free tier)
- Recommended: Use NAT instance for testing (save ~$32/month)

---

#### Route53
**Free Tier Allowance:**
- Hosted zones: $0.50/zone/month
- Queries: 1M queries/month free
- Zone transfer: Free
- Health checks: $0.50/check/month (1 free for first 12 months)

**Cost:** $0.50-1/month for 1-2 zones

---

#### CloudFront
**Free Tier Allowance (12-month):**
- 1TB/month data transfer out
- 10M HTTP/HTTPS requests/month
- Free tier available

**Cost:** $0 (if within limits)

---

#### AWS Glue (Data Integration)
- Not needed for testing FastAPI application

---

### Monitoring & Management

#### CloudWatch
**Free Tier Allowance (12-month):**
- 10 custom metrics (basic monitoring)
- 1M API requests
- 3 dashboards
- 5GB log ingestion/month
- 1GB data scanned/month (Insights queries)

**Premium Features (Charged):**
- Detailed monitoring: $3.50 per metric/month
- Additional logs ingestion: $0.50/GB beyond 5GB
- Log Insights queries: $0.005 per GB scanned beyond 1GB

**Cost:** $0-5/month (mostly free for basic monitoring)

---

#### CloudTrail
**Free Tier Allowance:**
- 1 trail: Free (tracks management events only)
- S3 storage: Use S3 free tier
- Data events: $2/100k events

**Cost:** $0 (within limits)

---

#### AWS Systems Manager
- Free (basic features)
- Session Manager: Free for EC2 instances with IAM role
- Patch Manager: Free (patch scanning)

**Cost:** $0

---

#### Budget & Cost Explorer
- Free (monitor spending)
- Budgets: Up to 5 budgets in free tier
- Cost Anomaly Detection: Free

**Cost:** $0

---

### Container & Registry

#### ECR (Elastic Container Registry)
**Free Tier Allowance (12-month):**
- Unlimited repositories
- Storage: $0.10/GB/month per region
- Data transfer: $0.09/GB (same region ECR to EC2: free)

**Estimate for TrueMatch AI:**
- Docker image size: ~500MB-1GB
- If 2 images: 2GB storage
- Cost: $0.20/month

**Best Use:** Store FastAPI, Celery, and worker images

---

#### ECS (Elastic Container Service)
**Free Tier Allowance:**
- Cluster management: FREE
- Container management: FREE
- Pay only for underlying compute (EC2 or Fargate)

**Fargate Pricing (if used):**
- vCPU: $0.04048/hour (t3.micro equivalent)
- Memory: $0.00445/GB-hour
- NOT recommended (exceeds budget)

**EC2 Launch Type:** Use with free tier EC2 (recommended)

**Cost:** $0 (using EC2 free tier instances)

---

#### Lambda
**Free Tier Allowance (12-month):**
- 1M requests/month
- 400,000 GB-seconds/month compute
- Not ideal for continuous FastAPI application
- Better for scheduled tasks/microservices

---

### Analytics

#### Kinesis
- Minimum: $0.50/shard/day (~$15/month)
- Not needed for testing

---

### Machine Learning

#### SageMaker
- 2-month free trial
- After: Notebook instance (ml.t3.medium) costs ~$5/month
- Training: Hourly charges apply
- Not needed for application testing (if not using ML features)

---

### Identity & Security

#### IAM (Identity & Access Management)
**Free Tier Allowance:**
- Unlimited users, roles, policies
- MFA devices
- API access keys

**Cost:** $0 (completely free)

---

#### Secrets Manager
**Free Tier Allowance:**
- None (charged from first secret)
- Cost: $0.40/secret/month + $0.06/10k API calls

**Alternative:** Use Parameter Store (SSM) - free tier

---

#### Parameter Store (Systems Manager)
**Free Tier Allowance (12-month):**
- Standard parameters: Unlimited
- Advanced parameters: Charged ($0.04/parameter)
- API calls: 1M free/month

**Best Use:** Store configuration, secrets, database credentials

**Cost:** $0 (within limits)

---

#### KMS (Key Management Service)
**Free Tier Allowance:**
- 20k free requests/month (AWS-managed keys)
- Customer-managed keys: $1/month each

**Cost:** $0 (if using AWS-managed keys)

---

### Network Services

#### VPN (AWS Client VPN)
- $0.15/hour per connection + data processing
- Alternative: Use EC2 bastion host (free tier)

---

#### Direct Connect
- Physical connection required
- $0.30/hour per connection minimum
- Not needed for testing

---

### Application Services

#### SQS (Simple Queue Service)
**Free Tier Allowance (12-month):**
- 1M requests/month
- Sufficient for Celery task queue (alternative to Redis)

**Cost:** $0 (within limits)

---

#### SNS (Simple Notification Service)
**Free Tier Allowance (12-month):**
- 1M publish requests/month
- 100k email notifications/month
- SMS: Paid (~$0.00645/SMS)

**Cost:** $0 (within limits for notifications)

---

#### SES (Simple Email Service)
**Free Tier Allowance (12-month):**
- 62k outbound emails/month
- Sandbox mode: 200 emails/24h to verified addresses
- Ideal for transactional emails

**Cost:** $0 (within limits)

---

## TrueMatch AI Architecture

### Application Stack

```
┌─────────────────────────────────────────────┐
│         Client Applications                 │
├─────────────────────────────────────────────┤
│  API Gateway (Route53) → CloudFront (Cache) │
├─────────────────────────────────────────────┤
│  FastAPI Backend (54 Endpoints)             │
│  ├─ Deployment: Docker Container            │
│  ├─ Compute: EC2 t3.micro                   │
│  └─ Load Balancing: Application-level       │
├─────────────────────────────────────────────┤
│  Celery Workers                             │
│  ├─ Background Job Processing               │
│  ├─ Deployment: Docker Containers (1-2)     │
│  └─ Scheduling: Celery Beat                 │
├─────────────────────────────────────────────┤
│  Message Queue: Redis (ElastiCache)         │
│  └─ Cache: cache.t3.micro (500MB)           │
├─────────────────────────────────────────────┤
│  Database: PostgreSQL (RDS)                 │
│  └─ Instance: db.t3.micro (1GB RAM, 20GB)   │
├─────────────────────────────────────────────┤
│  Storage: S3 (logs, snapshots)              │
│  └─ Allocation: 5GB free tier               │
├─────────────────────────────────────────────┤
│  Monitoring: CloudWatch                     │
│  └─ Logs: 5GB/month free tier               │
└─────────────────────────────────────────────┘
```

### Resource Requirements (Testing Phase)

| Component | Requirement | Free Tier | Sufficient? |
|-----------|-------------|-----------|------------|
| FastAPI Server | 2-4 vCPU, 2-4GB RAM | 1 vCPU, 1GB | ✓ Adequate (burstable) |
| Celery Workers | 2-4 workers | 1 instance | ✓ Single instance (2-3 processes) |
| PostgreSQL | 20GB+ storage, high throughput | 20GB | ✓ Sufficient for test data |
| Redis | 1-2GB memory | 500MB | ✓ Adequate for job queue |
| Network | Moderate bandwidth | 1GB out/month | ⚠ Monitor closely |

---

## Cost Analysis: Two Deployment Options

### Option A: Docker Compose on EC2 (RECOMMENDED)

#### Architecture Overview

```
EC2 t3.micro Instance (1x)
├─ Docker Daemon
├─ FastAPI Container
├─ Celery Worker Container(s) - 2-3 processes
├─ Redis Container? OR ElastiCache
└─ PostgreSQL Client

RDS db.t3.micro (separate)
├─ PostgreSQL Database
└─ Automated Backups (20GB included)

ElastiCache cache.t3.micro (separate)
├─ Redis Instance
└─ Celery Job Queue
```

#### Detailed Cost Breakdown

| Service | Item | Free Tier | Usage | Cost/Month |
|---------|------|-----------|-------|------------|
| **EC2** | t3.micro instance | 750 hrs | 730 hrs | $0.00 |
| | EBS storage (30GB gp2) | 30GB | 30GB | $0.00 |
| | Elastic IP | 1 free/month | 1 | $0.00 |
| **RDS** | db.t3.micro instance | 750 hrs | 730 hrs | $0.00 |
| | Storage (20GB) | 20GB | 18GB | $0.00 |
| | Backup storage | 20GB | 2GB | $0.00 |
| | Data transfer OUT | 1GB | 0.5GB | $0.00 |
| **ElastiCache** | cache.t3.micro | 750 hrs | 730 hrs | $0.00 |
| | Data transfer | Included | Included | $0.00 |
| **ECR** | Private repositories | Unlimited | 1-2 | $0.00 |
| | Image storage | Unlimited | 2GB | $0.20 |
| **S3** | Storage | 5GB | 1GB | $0.00 |
| | Data transfer OUT | 1GB | 0.5GB | $0.00 |
| **CloudWatch** | Metrics (10 included) | 10 | 5 | $0.00 |
| | Logs (5GB included) | 5GB | 2GB | $0.00 |
| | Dashboards | 3 free | 2 | $0.00 |
| **Route53** | Hosted zone | - | 1 | $0.50 |
| **Other** | NAT instance (EC2) | Included | - | $0.00 |
| | Backup buffer | - | - | $2.00 |
| | **TOTAL** | | | **$2.70** |

#### Pros & Cons

**Pros:**
- Lowest cost ($2.70/month)
- Maximum free tier utilization (95%+)
- Docker Compose simplifies testing
- Can run full stack on single instance
- Easy to migrate to EKS later
- Excellent learning environment for Kubernetes
- ~$97 monthly buffer for cost overruns

**Cons:**
- Single point of failure (no high availability)
- No auto-scaling
- Limited to t3.micro burstable performance
- Not suitable for production traffic
- EC2/RDS in same AZ (not HA)
- Requires manual backup management
- May need performance tuning for 54 endpoints

---

### Option B: EKS with Minimal Node Configuration

#### Architecture Overview

```
EKS Cluster
├─ Control Plane (managed by AWS) - $73/month
├─ 1x t3.micro Node (worker)
│  ├─ FastAPI Pod(s) - 2-3 replicas
│  ├─ Celery Worker Pod(s) - 2-3 replicas
│  └─ System pods (etcd, kube-proxy, etc)
│
RDS db.t3.micro (separate)
└─ PostgreSQL Database

ElastiCache cache.t3.micro (separate)
└─ Redis Instance
```

#### Detailed Cost Breakdown

| Service | Item | Free Tier | Usage | Cost/Month |
|---------|------|-----------|-------|------------|
| **EKS** | Cluster management | NONE | 730 hrs | $73.00 |
| **EC2** | t3.micro node (1x) | 750 hrs | 730 hrs | $0.00 |
| | EBS storage (30GB) | 30GB | 30GB | $0.00 |
| **RDS** | db.t3.micro instance | 750 hrs | 730 hrs | $0.00 |
| | Storage (20GB) | 20GB | 18GB | $0.00 |
| | Backup storage | 20GB | 2GB | $0.00 |
| **ElastiCache** | cache.t3.micro | 750 hrs | 730 hrs | $0.00 |
| **ECR** | Image storage | - | 2GB | $0.20 |
| **S3** | Storage & transfer | 5GB+1GB | 1.5GB | $0.00 |
| **CloudWatch** | Metrics, logs, dashboards | Included | 2-5GB | $0.00 |
| | EKS control plane logs | - | - | $1.00 |
| **Route53** | Hosted zone | - | 1 | $0.50 |
| **Other** | Buffer/unexpected | - | - | $5.00 |
| | **TOTAL** | | | **$79.70** |

#### Pros & Cons

**Pros:**
- Production-grade orchestration
- Auto-scaling capabilities (minimal impact at 1 node)
- Service discovery built-in
- Rolling updates/zero-downtime deployment
- Kubernetes native (kubectl, helm)
- Staging environment parity with production
- Secrets management (Kubernetes secrets or Sealed Secrets)
- Still under $100/month budget

**Cons:**
- Baseline cost of $73/month (EKS control plane)
- Kubernetes complexity for testing
- Overkill for feature validation
- Still requires manual node management (1 node)
- Auto-scaling won't help single node
- More moving parts to troubleshoot
- Limited margin ($20) for cost overruns

---

## Recommended Configuration (Option A)

### Docker Compose on EC2 - Detailed Setup

#### Infrastructure Components

```yaml
# AWS Infrastructure
Infrastructure:
  VPC:
    CIDR: 10.0.0.0/16
    Subnets: 2 (private + public)
    NAT: t3.micro instance (no NAT Gateway charge)
    
  EC2:
    Instance Type: t3.micro
    vCPU: 1
    Memory: 1GB
    Storage: 30GB gp2 EBS
    OS: Amazon Linux 2 or Ubuntu 22.04
    Security Group: 
      - SSH (port 22): restricted source
      - HTTP (port 80): 0.0.0.0/0
      - HTTPS (port 443): 0.0.0.0/0
      - Custom: Celery ports (optional)
    
  RDS (PostgreSQL):
    Instance Class: db.t3.micro
    Storage: 20GB gp2
    Backup Retention: 7 days
    Parameter Group: postgres14 or postgres15
    Multi-AZ: No
    
  ElastiCache (Redis):
    Node Type: cache.t3.micro
    Engine: Redis 7.x
    Num Cache Nodes: 1
    Parameter Group: default
    AutoFailover: Disabled
    
  ECR:
    Repositories: 
      - truematch-api
      - truematch-worker
    Image Retention: 10 images per repo
```

#### Docker Compose Configuration

```yaml
version: '3.9'

services:
  # FastAPI Application
  api:
    image: <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-api:latest
    container_name: truematch-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://dbuser:dbpass@rds-endpoint:5432/truematchdb
      - REDIS_URL=redis://redis-endpoint:6379/0
      - ENV=staging
      - LOG_LEVEL=info
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Celery Worker
  worker:
    image: <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-worker:latest
    container_name: truematch-worker
    command: celery -A truematch.tasks worker --loglevel=info --concurrency=2
    environment:
      - DATABASE_URL=postgresql://dbuser:dbpass@rds-endpoint:5432/truematchdb
      - REDIS_URL=redis://redis-endpoint:6379/0
      - ENV=staging
    depends_on:
      - redis
    restart: unless-stopped

  # Celery Beat (Scheduler)
  beat:
    image: <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-worker:latest
    container_name: truematch-beat
    command: celery -A truematch.tasks beat --loglevel=info
    environment:
      - REDIS_URL=redis://redis-endpoint:6379/0
      - ENV=staging
    depends_on:
      - redis
    restart: unless-stopped

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: truematch-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl/:/etc/nginx/ssl/:ro
    depends_on:
      - api
    restart: unless-stopped
```

#### Database & Cache Setup (External Services)

**RDS PostgreSQL Configuration:**

```sql
-- Primary Database Setup
CREATE DATABASE truematchdb
    WITH ENCODING 'UTF8'
    LC_COLLATE 'en_US.UTF-8'
    LC_CTYPE 'en_US.UTF-8';

-- Create application user with limited privileges
CREATE USER appuser WITH PASSWORD '<strong-password>';
GRANT CONNECT ON DATABASE truematchdb TO appuser;
GRANT USAGE ON SCHEMA public TO appuser;
GRANT CREATE ON SCHEMA public TO appuser;

-- For initial schema creation
\c truematchdb
GRANT ALL PRIVILEGES ON SCHEMA public TO appuser;
```

**ElastiCache Redis Configuration:**

```
-- No configuration needed beyond AWS console defaults
-- Connection: redis://<elasticache-endpoint>:6379
-- Test connection: redis-cli -h <endpoint> ping
```

---

### Step-by-Step Implementation (Option A)

#### Phase 1: AWS Account & Network Setup (1 hour)

1. **Create AWS Account**
   - Sign up for new AWS account
   - Verify email
   - Enter payment method
   - Confirm in ap-southeast-1 region

2. **VPC Setup**
   ```bash
   # Create VPC
   VPC CIDR: 10.0.0.0/16
   DNS Resolution: Enable
   
   # Create Subnets
   Public Subnet: 10.0.1.0/24 (map public IP on launch)
   Private Subnet: 10.0.2.0/24
   
   # Create Internet Gateway
   Attach to VPC
   
   # Create Route Table
   Public routes: 0.0.0.0/0 → IGW
   Private routes: 0.0.0.0/0 → NAT instance
   ```

3. **Security Groups**
   ```
   EC2 Security Group:
   - Inbound SSH: 22 (your-ip/32)
   - Inbound HTTP: 80 (0.0.0.0/0)
   - Inbound HTTPS: 443 (0.0.0.0/0)
   - Outbound: all traffic
   
   RDS Security Group:
   - Inbound TCP 5432: from EC2 security group
   
   ElastiCache Security Group:
   - Inbound TCP 6379: from EC2 security group
   ```

#### Phase 2: Launch Compute Resources (1.5 hours)

1. **Launch EC2 Instance**
   ```bash
   # AMI Selection
   Amazon Linux 2 (Free Tier Eligible) OR Ubuntu 22.04 LTS
   
   # Instance Configuration
   Instance Type: t3.micro
   VPC: Your created VPC
   Subnet: Public Subnet
   Public IP: Enable
   IAM Role: Create role with:
     - AmazonEC2ContainerRegistryPowerUser (ECR access)
     - CloudWatchAgentServerPolicy (monitoring)
     - AmazonSSMManagedInstanceCore (Systems Manager)
   
   # Storage
   EBS Volume: 30GB gp2 (delete on terminate)
   
   # Security Group
   Use EC2 security group created above
   
   # Key Pair
   Create new key pair, download and secure
   ```

2. **Configure EC2 Instance**
   ```bash
   # SSH into instance
   ssh -i your-key.pem ec2-user@your-instance-ip
   
   # Update system
   sudo yum update -y  # Amazon Linux
   # OR
   sudo apt update && sudo apt upgrade -y  # Ubuntu
   
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   newgrp docker
   
   # Install Docker Compose
   mkdir -p ~/.docker/bin
   curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o ~/.docker/bin/docker-compose
   chmod +x ~/.docker/bin/docker-compose
   echo 'export PATH=$PATH:$HOME/.docker/bin' >> ~/.bashrc
   
   # Install AWS CLI
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   
   # Install Git & development tools
   sudo yum install git -y  # Amazon Linux
   # OR
   sudo apt install git -y  # Ubuntu
   
   # Configure AWS credentials (for ECR access)
   aws configure --profile default
   # Enter AWS Access Key ID
   # Enter AWS Secret Access Key
   # Region: ap-southeast-1
   # Output: json
   
   # Configure Docker for ECR authentication
   aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com
   ```

#### Phase 3: Database & Cache Setup (1 hour)

1. **Create RDS PostgreSQL Instance**
   ```bash
   # AWS Console Steps:
   1. Navigate to RDS → Databases → Create Database
   2. Engine: PostgreSQL
   3. Engine Version: 15.x (latest)
   4. Template: Free tier
   5. DB Instance Identifier: truematchdb
   6. Master Username: admin
   7. Master Password: <generate strong password>
   8. Instance Type: db.t3.micro
   9. Storage: 20GB, General Purpose (gp2)
   10. VPC: Your created VPC
   11. Public Accessibility: No (only from EC2)
   12. VPC Security Group: RDS security group
   13. Backup Retention: 7 days
   14. Monitoring: Enable Enhanced Monitoring (optional, free tier logs only)
   15. Create
   
   # Wait for instance to be available (5-10 min)
   ```

2. **Initialize Database**
   ```bash
   # From EC2 instance
   # Install postgres client
   sudo yum install postgresql15-client -y  # Amazon Linux
   # OR
   sudo apt install postgresql-client -y  # Ubuntu
   
   # Connect to RDS
   psql -h truematchdb.xxxxx.ap-southeast-1.rds.amazonaws.com \
        -U admin \
        -d postgres
   
   # Create application database and user
   CREATE DATABASE truematchdb
       WITH ENCODING 'UTF8'
       LC_COLLATE 'en_US.UTF-8'
       LC_CTYPE 'en_US.UTF-8';
   
   CREATE USER appuser WITH PASSWORD '<strong-password>';
   GRANT CONNECT ON DATABASE truematchdb TO appuser;
   
   # Exit psql
   \q
   ```

3. **Create ElastiCache Redis Cluster**
   ```bash
   # AWS Console Steps:
   1. Navigate to ElastiCache → Caches → Create
   2. Cluster Type: Redis
   3. Engine Version: 7.x
   4. Location: ap-southeast-1
   5. Node Type: cache.t3.micro
   6. Number of Nodes: 1
   7. Cluster Name: truematch-redis
   8. Cluster Mode: Disabled
   9. Automatic Failover: Disabled
   10. VPC: Your created VPC
   11. Subnet Group: Create new (or default)
   12. Security Group: ElastiCache security group
   13. Encryption: Optional (enable for production)
   14. Create
   
   # Wait for cluster to be available (5-10 min)
   ```

4. **Test Database & Cache Connectivity**
   ```bash
   # Test PostgreSQL
   psql -h <rds-endpoint> -U appuser -d truematchdb
   SELECT version();
   \q
   
   # Test Redis
   redis-cli -h <elasticache-endpoint>
   PING
   exit
   ```

#### Phase 4: Application Deployment (2-3 hours)

1. **Create ECR Repositories**
   ```bash
   # From EC2 instance
   aws ecr create-repository \
       --repository-name truematch-api \
       --region ap-southeast-1
   
   aws ecr create-repository \
       --repository-name truematch-worker \
       --region ap-southeast-1
   
   # Output: Repository URIs for Docker push
   ```

2. **Build & Push Docker Images**
   ```bash
   # Clone application repository
   cd /opt/truematch
   git clone <your-repo>
   
   # Build FastAPI image
   docker build -t truematch-api:latest \
       -f Dockerfile.api .
   
   docker tag truematch-api:latest \
       <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-api:latest
   
   docker push <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-api:latest
   
   # Build Worker image
   docker build -t truematch-worker:latest \
       -f Dockerfile.worker .
   
   docker tag truematch-worker:latest \
       <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-worker:latest
   
   docker push <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-worker:latest
   ```

3. **Create Docker Compose Configuration**
   ```bash
   # Create directory for deployment
   mkdir -p /opt/docker-compose
   cd /opt/docker-compose
   
   # Create docker-compose.yml (see configuration above)
   # Create .env file with credentials
   cat > .env << EOF
   DATABASE_URL=postgresql://appuser:<password>@<rds-endpoint>:5432/truematchdb
   REDIS_URL=redis://<elasticache-endpoint>:6379/0
   AWS_REGION=ap-southeast-1
   ENV=staging
   EOF
   
   # Secure .env file
   chmod 600 .env
   ```

4. **Launch Application Stack**
   ```bash
   # Pull images and start services
   docker-compose -f docker-compose.yml pull
   docker-compose -f docker-compose.yml up -d
   
   # Verify services
   docker-compose ps
   
   # Check logs
   docker-compose logs -f api
   docker-compose logs -f worker
   docker-compose logs -f beat
   ```

5. **Configure Systemd Service (for auto-restart)**
   ```bash
   # Create systemd service
   sudo tee /etc/systemd/system/docker-compose.service > /dev/null << EOF
   [Unit]
   Description=TrueMatch AI Docker Compose Service
   After=docker.service
   Requires=docker.service
   
   [Service]
   Type=oneshot
   RemainAfterExit=yes
   WorkingDirectory=/opt/docker-compose
   ExecStart=/usr/bin/docker-compose -f docker-compose.yml up -d
   ExecStop=/usr/bin/docker-compose -f docker-compose.yml down
   Restart=on-failure
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   # Enable and start service
   sudo systemctl daemon-reload
   sudo systemctl enable docker-compose
   sudo systemctl start docker-compose
   ```

---

## Advanced Configuration (Option B)

### EKS Setup - High Level Overview

#### Architecture

```
AWS Region: ap-southeast-1
├─ EKS Cluster (Managed Control Plane)
│  ├─ API Server
│  ├─ etcd (managed)
│  ├─ Scheduler
│  ├─ Controller Manager
│  └─ Node Group (1x t3.micro)
│
├─ RDS PostgreSQL (db.t3.micro)
├─ ElastiCache Redis (cache.t3.micro)
├─ ECR (Image Registry)
└─ Load Balancer (Application or Network LB)
```

#### EKS Cluster Creation

```bash
# Prerequisites
# 1. AWS CLI v2 installed
# 2. kubectl installed
# 3. eksctl installed (recommended)

# Create cluster using eksctl
eksctl create cluster \
  --name truematch-staging \
  --region ap-southeast-1 \
  --nodegroup-name truematch-workers \
  --node-type t3.micro \
  --nodes 1 \
  --nodes-min 1 \
  --nodes-max 1

# Wait for cluster creation (15-20 minutes)

# Update kubeconfig
aws eks update-kubeconfig \
  --name truematch-staging \
  --region ap-southeast-1

# Verify cluster
kubectl get nodes
kubectl get pods --all-namespaces
```

#### EKS Deployment Configuration

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: truematch-api
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: truematch-api
  template:
    metadata:
      labels:
        app: truematch-api
    spec:
      containers:
      - name: api
        image: <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: truematch-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: truematch-secrets
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: truematch-api-service
  namespace: default
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
  selector:
    app: truematch-api
```

#### Cost Comparison Summary

```
Detailed Cost Comparison (Monthly)

Option A (Docker Compose on EC2):        Option B (EKS):
├─ EC2 t3.micro      $0.00              ├─ EKS Control Plane    $73.00
├─ RDS db.t3.micro   $0.00              ├─ EC2 t3.micro         $0.00
├─ ElastiCache t3.m  $0.00              ├─ RDS db.t3.micro      $0.00
├─ ECR storage       $0.20              ├─ ElastiCache t3.m     $0.00
├─ S3                $0.00              ├─ ECR storage          $0.20
├─ Route53           $0.50              ├─ S3                   $0.00
├─ CloudWatch        $0.00              ├─ Route53              $0.50
├─ Other/buffer      $2.00              ├─ CloudWatch           $1.00
└─ TOTAL: $2.70      └─ TOTAL: $79.70

Savings with Option A: $77/month (97% cheaper)
Buffer margin (Option A): $97.30 for overages
Buffer margin (Option B): $20.30 for overages
```

---

## Free Tier Service Limits & Monitoring

### Critical Limits to Monitor

#### EC2 Instance Hours
```
Free Tier: 750 hours/month
Actual: 730 hours/month (31 days average)
Warning: Stop instances during testing when not needed
```

#### RDS Database Instance Hours
```
Free Tier: 750 hours/month
Actual: 730 hours/month
Warning: Do not create multiple db.t3.micro instances in same month
```

#### ElastiCache Node Hours
```
Free Tier: 750 hours/month
Actual: 730 hours/month
Warning: Do not create multiple cache.t3.micro nodes simultaneously
```

#### Data Transfer OUT
```
Free Tier: 1GB/month (first)
Beyond 1GB: $0.085/GB (ap-southeast-1 to internet)
Within AWS: FREE
Internal EC2 to RDS: FREE
Internal EC2 to ElastiCache: FREE
```

#### S3 Storage & Requests
```
Free Tier: 5GB storage, 20k GET, 2k PUT requests
Monitor: Use S3 lifecycle policies for old logs
```

#### RDS Storage
```
Free Tier: 20GB combined (data + automated backups)
Monitor: Regular monitoring of DB size
Backup space: Counts toward 20GB limit
```

### Monitoring Strategy

#### AWS Budget Alerts

```
1. Navigate to AWS Budgets
2. Create Budget for $100
3. Configure alerts:
   - 50% ($50): Email notification
   - 80% ($80): Email + SMS
   - 100% ($100): Critical alert
```

#### CloudWatch Custom Metrics

```
Create custom metrics to track:
1. EC2 Running Hours (compare to 750 limit)
2. RDS Running Hours (compare to 750 limit)
3. Data Transfer OUT (track usage vs 1GB free)
4. ElastiCache Running Hours (compare to 750 limit)
5. RDS Storage Size (track vs 20GB limit)
```

#### Daily Cost Check

```bash
# Get today's costs
aws ce get-cost-and-usage \
  --time-period Start=2026-07-21,End=2026-07-22 \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --region ap-southeast-1
```

#### CloudWatch Dashboards

```yaml
Custom Dashboard: Free Tier Monitoring
├─ EC2 Instance Running Time (target: <750 hrs)
├─ RDS Running Hours (target: <750 hrs)
├─ ElastiCache Running Hours (target: <750 hrs)
├─ Data Transfer OUT (target: <1GB)
├─ RDS Storage Usage (target: <20GB)
├─ ECR Storage Size (estimate: 2GB)
├─ Estimated Monthly Cost (running total)
└─ Service Health Checks
```

---

## Cost Tracking & Alerts

### Monthly Cost Monitoring

#### Set Up AWS Budgets

```
Budget 1: Free Tier Services
- Scope: EC2, RDS, ElastiCache
- Limit: $0.01 (free tier only)
- Alert: When usage detected beyond free tier

Budget 2: Total Application
- Scope: All services
- Limit: $100
- Alerts: 
  - 50%: $50 (informational)
  - 75%: $75 (warning)
  - 100%: $100 (critical)
```

#### Estimated Monthly Cost Formula

```
Total Cost = 
  (EC2 running hours / 750) × $0.0116 +
  (RDS running hours / 750) × estimated_hourly_rate +
  (ElastiCache hours / 750) × estimated_hourly_rate +
  (Data Transfer OUT GB - 1) × $0.085 +
  (ECR storage GB - 0) × $0.10 +
  (Route53 zones) × $0.50 +
  (Additional CloudWatch) × $0.50
```

#### Preventing Unexpected Costs

| Risk | Mitigation |
|------|-----------|
| Multiple EC2 instances | Delete/stop unused instances |
| Multiple RDS instances | Only 1 db.t3.micro per month |
| Multiple ElastiCache | Only 1 cache.t3.micro per month |
| Excess data transfer | Monitor bandwidth usage |
| Elastic IPs unassociated | Delete unassociated IPs ($0.43/month) |
| EBS snapshots | Delete old snapshots (counts toward S3) |
| RDS backup storage | Reduce retention period if needed |
| NAT Gateway (if used) | Use NAT instance instead ($32/month) |

### Free Tier Expiration Planning

**Timeline:**
- Month 1-12: Free tier active
- Month 13: Free tier expires for time-limited services
- Cost increase at month 13: ~$5-15/month (if no changes)

**Preparation:**
1. Document exact free tier expiration date
2. Plan upgrade or migration
3. Review unused services before month 12
4. Consider consolidation or scaling changes

---

## Upgrade Path to Production

### Phase-Based Scaling Strategy

```
Phase 1: Testing (Month 1-3)
├─ Deployment: Docker Compose on EC2 t3.micro
├─ Cost: ~$2-5/month
├─ Goals: Feature validation, performance testing
└─ Action: Monitor for scaling needs

    Phase 2: Staging (Month 4-6)
    ├─ Deployment: EKS cluster with 1-2 nodes
    ├─ Instance: t3.small or t3.medium nodes
    ├─ Cost: ~$100-200/month
    ├─ Goals: Production workload simulation, HA testing
    └─ Action: Performance benchmarking

        Phase 3: Production Ready (Month 7+)
        ├─ Deployment: EKS with auto-scaling
        ├─ Nodes: 3+ nodes (t3.large or larger)
        ├─ RDS: db.t3.small → db.t3.medium (or larger)
        ├─ Cost: $1,000+/month
        ├─ Goals: High availability, auto-scaling
        └─ Action: Deploy to production
```

### Migration Path: Docker Compose → EKS

#### Step 1: Prepare Application

```
Ensure application is containerized and stateless:
- No local file storage (use S3/EBS)
- Configuration via environment variables
- Graceful shutdown handling
- Health checks implemented
- Logging to stdout/stderr (CloudWatch)
```

#### Step 2: Create EKS Cluster

```bash
# No downtime migration strategy
1. Create new EKS cluster (parallel)
2. Deploy app to EKS (same version)
3. Validate functionality
4. Gradually shift traffic (DNS/LB)
5. Decommission Docker Compose setup
```

#### Step 3: Database & Cache Considerations

```
PostgreSQL:
- Create snapshot from free tier RDS
- Restore to new db.t3.small instance
- Update connection strings
- Test connectivity

Redis:
- ElastiCache cluster can remain unchanged
- Update endpoint in EKS deployment
- No migration needed
```

#### Step 4: Update CI/CD

```
Docker Compose:
- Build images locally
- Push to ECR
- SSH into EC2 and docker-compose pull/up

EKS:
- Build images in CI/CD
- Push to ECR
- Use helm or kubectl to deploy
- Automated deployment pipeline
```

---

## Summary & Recommendations

### Key Takeaways

1. **Option A (Docker Compose): $2.70/month**
   - Maximum free tier utilization
   - Ideal for testing and validation
   - Simple deployment and management
   - Quick iteration cycle
   - Recommended for phase 1

2. **Option B (EKS): $79.70/month**
   - Production-grade infrastructure
   - Automatic scaling capabilities
   - Kubernetes best practices
   - Better for staging validation
   - Still under $100/month budget

3. **Free Tier Window: 12 months**
   - Plan migration after 12 months
   - Document exact expiration date
   - Prepare upgrade strategy early

4. **Cost Control Measures**
   - AWS Budgets with alerts
   - CloudWatch custom metrics
   - Daily cost monitoring
   - Unused resource cleanup

### Action Checklist for Today

- [ ] Create new AWS account
- [ ] Enable billing alerts
- [ ] Choose between Option A or Option B
- [ ] Create VPC and security groups
- [ ] Launch EC2 instance (Option A) or EKS cluster (Option B)
- [ ] Set up RDS PostgreSQL
- [ ] Set up ElastiCache Redis
- [ ] Create ECR repositories
- [ ] Deploy application
- [ ] Configure monitoring and alerts
- [ ] Document endpoints and credentials

### Next Steps

1. **Immediate (This week):**
   - Set up AWS account and infrastructure
   - Deploy initial version
   - Validate connectivity

2. **Short term (Weeks 2-4):**
   - Run load testing
   - Monitor costs and performance
   - Iterate on configuration

3. **Medium term (Month 2-3):**
   - Plan Phase 2 migration if needed
   - Prepare EKS deployment
   - Document lessons learned

4. **Long term (Month 4+):**
   - Transition to production infrastructure
   - Implement auto-scaling
   - Optimize costs based on actual usage

---

**Document prepared for TrueMatch AI Testing Deployment**  
**Budget: <$100/month | Region: ap-southeast-1 | Free Tier Eligible: YES**
