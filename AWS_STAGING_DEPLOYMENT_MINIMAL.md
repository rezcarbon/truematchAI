# AWS Staging Deployment - Minimal Cost Configuration
## Complete Implementation Guide for TrueMatch AI Testing Phase

**Document Version:** 1.0  
**Target Cost:** $1-2/month (Docker Compose) | $79-90/month (EKS)  
**Region:** ap-southeast-1 (Singapore)  
**Architecture:** Docker Compose on EC2 (Primary) / EKS (Alternative)  
**Database:** RDS PostgreSQL db.t3.micro  
**Cache:** ElastiCache Redis cache.t3.micro  
**Last Updated:** 2026-07-21

---

## Table of Contents

1. [Quick Start Guide](#quick-start-guide)
2. [Docker Compose Configuration](#docker-compose-configuration)
3. [EC2 Setup & Deployment](#ec2-setup-deployment)
4. [RDS PostgreSQL Configuration](#rds-postgresql-configuration)
5. [ElastiCache Redis Configuration](#elasticache-redis-configuration)
6. [Monitoring & Logging](#monitoring-logging)
7. [Troubleshooting Guide](#troubleshooting-guide)
8. [Backup & Recovery](#backup-recovery)
9. [Upgrade to EKS](#upgrade-to-eks)
10. [Cost Control Scripts](#cost-control-scripts)

---

## Quick Start Guide

### Estimated Setup Time: 3-4 hours

#### Prerequisites

1. **AWS Account**
   - New account (eligible for free tier)
   - Credit card added
   - Region set to ap-southeast-1
   - Billing alerts enabled

2. **Local Development Environment**
   - Docker installed and running
   - AWS CLI v2 installed
   - kubectl installed (optional, for EKS path)
   - Git installed
   - SSH client

3. **TrueMatch AI Application**
   - Code repository cloned locally
   - Dockerfiles prepared:
     - `Dockerfile.api` (FastAPI application)
     - `Dockerfile.worker` (Celery worker)
   - docker-compose.yml ready
   - Environment configuration files prepared

#### 30-Second Deployment Overview

```bash
# 1. Create AWS infrastructure (VPC, EC2, RDS, ElastiCache)
# 2. Connect to EC2 and install Docker
# 3. Build and push Docker images to ECR
# 4. Deploy docker-compose stack
# 5. Configure monitoring and backups
# Total: ~4 hours first time, ~30 min for updates
```

---

## Docker Compose Configuration

### Complete docker-compose.yml

```yaml
version: '3.9'

# Service network
networks:
  truematch:
    driver: bridge

# Named volumes
volumes:
  postgres_data:
    driver: local

services:
  # ===========================
  # FastAPI Web Application
  # ===========================
  api:
    image: ${AWS_ACCOUNT_ID}.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-api:latest
    container_name: truematch-api
    restart: unless-stopped
    
    ports:
      - "8000:8000"
    
    networks:
      - truematch
    
    environment:
      # Database Configuration
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${RDS_ENDPOINT}:5432/${DB_NAME}
      - DATABASE_POOL_SIZE=5
      - DATABASE_POOL_TIMEOUT=30
      
      # Redis/Cache Configuration
      - REDIS_URL=redis://${REDIS_ENDPOINT}:6379/0
      - REDIS_TIMEOUT=30
      
      # Application Settings
      - ENV=staging
      - DEBUG=false
      - LOG_LEVEL=info
      - WORKERS=2
      
      # Security
      - SECRET_KEY=${SECRET_KEY}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - CORS_ORIGINS=${CORS_ORIGINS}
      
      # AWS Configuration
      - AWS_REGION=ap-southeast-1
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    
    # Resource limits (t3.micro: 1 vCPU, 1GB RAM)
    # Reserve 256MB for API service
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M
    
    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    # Logging
    logging:
      driver: "awslogs"
      options:
        awslogs-group: "/truematch/api"
        awslogs-region: "ap-southeast-1"
        awslogs-stream-prefix: "docker"
    
    # Dependencies
    depends_on:
      - redis
    
    # Volume mounts
    volumes:
      - /opt/truematch/logs:/app/logs:rw

  # ===========================
  # Celery Worker Service
  # ===========================
  worker:
    image: ${AWS_ACCOUNT_ID}.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-worker:latest
    container_name: truematch-worker
    restart: unless-stopped
    
    command: >
      celery -A truematch.celery_app worker
      --loglevel=info
      --concurrency=2
      --time-limit=600
      --soft-time-limit=580
      --max-tasks-per-child=1000
    
    networks:
      - truematch
    
    environment:
      # Database Configuration
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${RDS_ENDPOINT}:5432/${DB_NAME}
      - DATABASE_POOL_SIZE=3
      
      # Redis/Celery Configuration
      - REDIS_URL=redis://${REDIS_ENDPOINT}:6379/0
      - CELERY_BROKER_URL=redis://${REDIS_ENDPOINT}:6379/0
      - CELERY_RESULT_BACKEND=redis://${REDIS_ENDPOINT}:6379/0
      
      # Application Settings
      - ENV=staging
      - LOG_LEVEL=info
      
      # AWS Configuration
      - AWS_REGION=ap-southeast-1
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    
    # Resource limits (t3.micro: 1 vCPU, 1GB RAM)
    # Reserve 300MB for worker service
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 300M
        reservations:
          cpus: '0.25'
          memory: 150M
    
    # Logging
    logging:
      driver: "awslogs"
      options:
        awslogs-group: "/truematch/worker"
        awslogs-region: "ap-southeast-1"
        awslogs-stream-prefix: "docker"
    
    # Dependencies
    depends_on:
      - redis
    
    # Volume mounts
    volumes:
      - /opt/truematch/logs:/app/logs:rw

  # ===========================
  # Celery Beat (Task Scheduler)
  # ===========================
  beat:
    image: ${AWS_ACCOUNT_ID}.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-worker:latest
    container_name: truematch-beat
    restart: unless-stopped
    
    command: >
      celery -A truematch.celery_app beat
      --loglevel=info
      --pidfile=/var/run/celery/beat.pid
      --scheduler django_celery_beat.schedulers:DatabaseScheduler
    
    networks:
      - truematch
    
    environment:
      # Database Configuration
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${RDS_ENDPOINT}:5432/${DB_NAME}
      
      # Redis/Celery Configuration
      - REDIS_URL=redis://${REDIS_ENDPOINT}:6379/0
      - CELERY_BROKER_URL=redis://${REDIS_ENDPOINT}:6379/0
      - CELERY_RESULT_BACKEND=redis://${REDIS_ENDPOINT}:6379/0
      
      # Application Settings
      - ENV=staging
      - LOG_LEVEL=info
      
      # AWS Configuration
      - AWS_REGION=ap-southeast-1
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    
    # Resource limits (beat is lightweight)
    deploy:
      resources:
        limits:
          cpus: '0.25'
          memory: 128M
        reservations:
          cpus: '0.1'
          memory: 64M
    
    # Logging
    logging:
      driver: "awslogs"
      options:
        awslogs-group: "/truematch/beat"
        awslogs-region: "ap-southeast-1"
        awslogs-stream-prefix: "docker"
    
    # Dependencies
    depends_on:
      - redis
    
    # Volume mounts
    volumes:
      - /opt/truematch/logs:/app/logs:rw
      - /opt/truematch/celery-schedule:/var/run/celery:rw

  # ===========================
  # Nginx Reverse Proxy
  # ===========================
  nginx:
    image: nginx:alpine
    container_name: truematch-nginx
    restart: unless-stopped
    
    ports:
      - "80:80"
      - "443:443"
    
    networks:
      - truematch
    
    volumes:
      # Nginx configuration
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      
      # SSL certificates (if using HTTPS)
      - ./nginx/ssl:/etc/nginx/ssl:ro
      
      # Static files (optional)
      - ./public:/usr/share/nginx/html:ro
    
    # Logging
    logging:
      driver: "awslogs"
      options:
        awslogs-group: "/truematch/nginx"
        awslogs-region: "ap-southeast-1"
        awslogs-stream-prefix: "docker"
    
    # Dependencies
    depends_on:
      - api
    
    # Health check
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  # ===========================
  # Redis Cache Service
  # ===========================
  redis:
    image: redis:7-alpine
    container_name: truematch-redis-local
    restart: unless-stopped
    
    # Note: This is optional local Redis for development
    # For production/staging, use AWS ElastiCache instead
    
    command: >
      redis-server
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --appendonly no
    
    networks:
      - truematch
    
    ports:
      - "6379:6379"
    
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '0.25'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 64M
    
    # Logging
    logging:
      driver: "awslogs"
      options:
        awslogs-group: "/truematch/redis-local"
        awslogs-region: "ap-southeast-1"
        awslogs-stream-prefix: "docker"
    
    # Health check
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

# ===========================
# Container Registry Credentials
# ===========================
# Add this to ~/.docker/config.json for ECR authentication:
# {
#   "credHelpers": {
#     "<account-id>.dkr.ecr.ap-southeast-1.amazonaws.com": "ecr-login"
#   }
# }
```

### Environment File (.env)

```bash
# Save as .env in docker-compose directory
# This file is loaded by docker-compose automatically

# AWS Account Information
AWS_ACCOUNT_ID=123456789012
AWS_REGION=ap-southeast-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# RDS PostgreSQL Configuration
RDS_ENDPOINT=truematchdb.c9akciq32.ap-southeast-1.rds.amazonaws.com
DB_NAME=truematchdb
DB_USER=appuser
DB_PASSWORD=YourStrongPassword123!@#

# ElastiCache Redis Configuration
REDIS_ENDPOINT=truematch-redis.xxxxx.ng.0001.apse1.cache.amazonaws.com

# FastAPI Configuration
SECRET_KEY=your-secret-key-here-min-32-chars-long-12345
ALLOWED_HOSTS=localhost,127.0.0.1,example.com
CORS_ORIGINS=http://localhost:3000,https://example.com

# Application Mode
ENV=staging
DEBUG=false
LOG_LEVEL=info

# Celery Configuration (for Celery worker)
CELERY_BROKER_URL=redis://truematch-redis.xxxxx.ng.0001.apse1.cache.amazonaws.com:6379/0
CELERY_RESULT_BACKEND=redis://truematch-redis.xxxxx.ng.0001.apse1.cache.amazonaws.com:6379/0

# Monitoring & Logging
SENTRY_DSN=https://example@sentry.io/123456
DATADOG_API_KEY=your-datadog-key-if-using
```

### Nginx Configuration

```nginx
# Save as nginx/nginx.conf

user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 20M;

    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml font/truetype font/opentype 
               application/vnd.ms-fontobject image/svg+xml;

    include /etc/nginx/conf.d/*.conf;
}
```

```nginx
# Save as nginx/conf.d/default.conf

upstream fastapi {
    server api:8000;
}

server {
    listen 80;
    server_name _;

    # Redirect HTTP to HTTPS (if SSL configured)
    # return 301 https://$host$request_uri;

    # API Endpoints
    location / {
        proxy_pass http://fastapi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://fastapi;
        proxy_set_header Host $host;
    }

    # Static files (if needed)
    location /static/ {
        alias /usr/share/nginx/html/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}

# HTTPS Configuration (optional, uncomment when certificates ready)
# server {
#     listen 443 ssl http2;
#     server_name example.com;
#
#     ssl_certificate /etc/nginx/ssl/cert.pem;
#     ssl_certificate_key /etc/nginx/ssl/key.pem;
#     ssl_protocols TLSv1.2 TLSv1.3;
#     ssl_ciphers HIGH:!aNULL:!MD5;
#
#     # Same location blocks as above
# }
```

---

## EC2 Setup & Deployment

### Step 1: Launch EC2 Instance

#### AWS Console Configuration

```
1. Navigate to EC2 Dashboard
2. Click "Launch Instance"
3. Name: truematch-staging-api
4. AMI: Amazon Linux 2 (t3.micro eligible)
   OR Ubuntu Server 22.04 LTS (t3.micro eligible)
5. Instance Type: t3.micro (1 vCPU, 1GB memory)
6. Key Pair: Create new "truematch-staging-key"
   Download and secure: chmod 600 truematch-staging-key.pem
7. Network:
   - VPC: Select your created VPC
   - Subnet: Public subnet (for outbound internet access)
   - Auto-assign public IP: Enable
   - Security Group: Create with rules:
     * SSH (22): from your-ip/32
     * HTTP (80): from 0.0.0.0/0
     * HTTPS (443): from 0.0.0.0/0
8. Storage: 30GB gp2 (free tier)
9. Advanced:
   - IAM Instance Profile: Create with:
     * AmazonEC2ContainerRegistryPowerUser
     * CloudWatchAgentServerPolicy
     * AmazonSSMManagedInstanceCore
10. Tags:
    - Name: truematch-staging
    - Environment: staging
    - Application: truematch-ai
11. Review and Launch
```

### Step 2: Connect to EC2 Instance

```bash
# From your local machine
chmod 600 truematch-staging-key.pem

# Get EC2 public IP from AWS Console
EC2_IP="<public-ip>"

# SSH into instance
ssh -i truematch-staging-key.pem ec2-user@$EC2_IP  # Amazon Linux
# OR
ssh -i truematch-staging-key.pem ubuntu@$EC2_IP    # Ubuntu

# Verify connection and update system
sudo yum update -y  # Amazon Linux 2
# OR
sudo apt update && sudo apt upgrade -y  # Ubuntu
```

### Step 3: Install Docker & Dependencies

#### For Amazon Linux 2

```bash
# Install Docker
sudo yum install -y docker git curl wget

# Add current user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Start Docker daemon
sudo systemctl start docker
sudo systemctl enable docker

# Verify Docker installation
docker --version
docker run hello-world

# Install Docker Compose
mkdir -p ~/.docker/bin
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o ~/.docker/bin/docker-compose
chmod +x ~/.docker/bin/docker-compose
echo 'export PATH=$PATH:$HOME/.docker/bin' >> ~/.bashrc
source ~/.bashrc
docker-compose --version

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version
```

#### For Ubuntu 22.04

```bash
# Install Docker using official repository
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Start Docker daemon
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version

# Install AWS CLI & Git
sudo apt install -y awscli git curl wget
aws --version
```

### Step 4: Configure AWS Credentials

```bash
# Configure AWS CLI with ECR access
aws configure --profile default

# When prompted, enter:
# AWS Access Key ID: <your-access-key>
# AWS Secret Access Key: <your-secret-key>
# Default region: ap-southeast-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

### Step 5: Login to ECR

```bash
# Get ECR login token (valid for 12 hours)
aws ecr get-login-password --region ap-southeast-1 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com

# Verify login by listing repositories
aws ecr describe-repositories --region ap-southeast-1
```

### Step 6: Deploy Application Stack

```bash
# Create application directory
mkdir -p /opt/truematch
cd /opt/truematch

# Clone or upload docker-compose files
# Option 1: Clone from git
git clone <your-repo-url> .

# Option 2: Upload files via SCP
# From local machine:
# scp -i truematch-staging-key.pem -r ./docker-compose/* ec2-user@$EC2_IP:/opt/truematch/

# Prepare environment file
# Edit .env with actual values:
# RDS_ENDPOINT, DB_PASSWORD, REDIS_ENDPOINT, AWS credentials, etc.
vi /opt/truematch/.env

# Make .env secure
chmod 600 /opt/truematch/.env

# Create necessary directories
mkdir -p logs celery-schedule nginx/conf.d nginx/ssl public

# Pull images from ECR
docker-compose pull

# Start services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f beat
docker-compose logs -f nginx
```

### Step 7: Create Systemd Service (Auto-Restart)

```bash
# Create service file
sudo tee /etc/systemd/system/docker-compose-truematch.service > /dev/null << 'EOF'
[Unit]
Description=TrueMatch AI Docker Compose Service
After=docker.service network-online.target
Wants=network-online.target
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/truematch
StandardOutput=journal
StandardError=journal

# Pre-start: login to ECR
ExecStartPre=/bin/bash -c 'aws ecr get-login-password --region ap-southeast-1 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com'

# Pull latest images
ExecStartPre=/usr/bin/docker-compose pull

# Start services
ExecStart=/usr/bin/docker-compose -f docker-compose.yml up -d

# Stop services
ExecStop=/usr/bin/docker-compose -f docker-compose.yml down

# Restart policy
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable docker-compose-truematch
sudo systemctl start docker-compose-truematch

# Check service status
sudo systemctl status docker-compose-truematch
sudo journalctl -u docker-compose-truematch -f
```

---

## RDS PostgreSQL Configuration

### Step 1: Create RDS Instance via AWS Console

```
Navigate to RDS Dashboard:

1. Databases → Create database
2. Engine selection: PostgreSQL
3. Version: PostgreSQL 15.x (latest)
4. Template: Free tier
5. DB instance identifier: truematchdb
6. Master username: admin
7. Master password: <generate-strong-password>
8. Instance class: db.t3.micro
9. Storage:
   - Type: General Purpose (gp2)
   - Allocated storage: 20GB
10. Network & Security:
    - VPC: Your created VPC
    - DB subnet group: Create new
    - Public accessibility: No
    - VPC security group: Create new "rds-postgres"
11. Database options:
    - Database name: truematchdb
    - Port: 5432
    - Character set: UTF8
12. Backup:
    - Automated backups: Enable
    - Backup retention: 7 days (free tier limit)
    - Backup window: 03:00 UTC
13. Monitoring:
    - Enable CloudWatch monitoring: Yes
    - Monitoring granularity: 60 seconds
14. Additional options:
    - Enable deletion protection: Yes (prevent accidental deletion)
    - Copy tags to snapshots: Yes
15. Estimated monthly cost: $0 (free tier)
16. Create database
```

### Step 2: Configure RDS Security Group

```bash
# From AWS Console, navigate to RDS instance security group

# Inbound rules:
# 1. PostgreSQL (5432)
#    Source: EC2 Security Group ID
#    This allows EC2 instance to connect to RDS

# Outbound rules:
# 1. All traffic (default)
```

### Step 3: Initialize Database

```bash
# From EC2 instance, install PostgreSQL client
sudo yum install -y postgresql15-client  # Amazon Linux
# OR
sudo apt install -y postgresql-client  # Ubuntu

# Get RDS endpoint from AWS Console
RDS_ENDPOINT="truematchdb.xxxxx.ap-southeast-1.rds.amazonaws.com"

# Connect to RDS
psql -h $RDS_ENDPOINT \
     -U admin \
     -d postgres

# When prompted, enter master password

# Create application database
CREATE DATABASE truematchdb
    WITH
    ENCODING 'UTF8'
    LC_COLLATE 'en_US.UTF-8'
    LC_CTYPE 'en_US.UTF-8'
    TEMPLATE template0;

# Create application user with limited privileges
CREATE ROLE appuser WITH
    LOGIN
    PASSWORD '<strong-application-password>'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT;

# Grant database connection permissions
GRANT CONNECT ON DATABASE truematchdb TO appuser;

# Connect to application database
\c truematchdb

# Grant schema permissions
GRANT USAGE ON SCHEMA public TO appuser;
GRANT CREATE ON SCHEMA public TO appuser;

# Grant table/sequence permissions (for migrations to work)
GRANT ALL ON ALL TABLES IN SCHEMA public TO appuser;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO appuser;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO appuser;

# Set defaults for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO appuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO appuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO appuser;

# Exit psql
\q
```

### Step 4: Run Database Migrations

```bash
# From EC2 instance, in your application directory
cd /opt/truematch

# If using Alembic (recommended for FastAPI)
docker-compose run --rm api alembic upgrade head

# If using Django migrations
docker-compose run --rm api python manage.py migrate

# If using custom migration script
docker-compose run --rm api python scripts/migrate_db.py

# Verify database structure
psql -h $RDS_ENDPOINT \
     -U appuser \
     -d truematchdb \
     -c "\dt"  # List tables

# Exit
```

### Step 5: Configure Automated Backups

```bash
# AWS Console → RDS → Automated backups

# Default configuration (from step 1):
# - Automatic backups: Enabled
# - Backup retention period: 7 days
# - Backup window: 03:00 UTC

# To adjust backup window:
# 1. Select RDS instance
# 2. Modify
# 3. Backup window: Set preferred time (UTC)
# 4. Apply immediately or schedule maintenance window
```

### Step 6: Monitor Database Performance

```bash
# CloudWatch Metrics (automatic)
# AWS Console → CloudWatch → Metrics → RDS

# Key metrics to monitor:
# - CPU Utilization (should be <20% for t3.micro)
# - Database Connections (monitor for leaks)
# - Storage Used (should be <20GB)
# - Read/Write Latency (should be <5ms normally)
# - Free Disk Space (alert if <5GB)

# Set up CloudWatch Alarms
# AWS Console → CloudWatch → Alarms → Create Alarm

# Example alarm: Database Storage
# - Metric: RDS → Database Connections
# - Condition: > 80
# - Action: Send email notification
```

---

## ElastiCache Redis Configuration

### Step 1: Create ElastiCache Cluster via AWS Console

```
Navigate to ElastiCache Dashboard:

1. Caches → Create cache
2. Engine: Redis
3. Engine version: 7.x (latest stable)
4. Location: ap-southeast-1
5. Cluster name: truematch-redis
6. Node type: cache.t3.micro
7. Number of nodes: 1
8. Cluster mode: Disabled
   (Disabled is recommended for single-node free tier)
9. Security:
   - Subnet group: Create new
   - VPC: Your created VPC
   - Security group: Create new "elasticache-redis"
   - Encryption at rest: Disabled (not in free tier)
   - Encryption in transit: Disabled (optional)
   - AUTH: Disabled for testing (enable in production)
10. Parameter group: default.redis7
11. Automatic failover: Disabled (single node)
12. Multi-AZ: Disabled (costs extra, not needed for testing)
13. Backup:
    - Automatic backups: Disabled (manual snapshots only)
    - Snapshot retention: 0 days
14. Maintenance window: No preference
15. Log delivery: Optional
    - Slow log: Enable to CloudWatch Logs
16. Estimated monthly cost: $0 (free tier)
17. Create
```

### Step 2: Configure ElastiCache Security Group

```bash
# From AWS Console, navigate to ElastiCache security group

# Inbound rules:
# 1. Redis (6379)
#    Source: EC2 Security Group ID
#    This allows EC2 instance to connect to ElastiCache

# Outbound rules:
# 1. All traffic (default)
```

### Step 3: Test Redis Connection

```bash
# From EC2 instance, install redis-cli
sudo yum install -y amazon-linux-extras  # Amazon Linux
sudo amazon-linux-extras install redis6 -y
# OR
sudo apt install -y redis-tools  # Ubuntu

# Get ElastiCache endpoint from AWS Console
REDIS_ENDPOINT="truematch-redis.xxxxx.ng.0001.apse1.cache.amazonaws.com"

# Test connection
redis-cli -h $REDIS_ENDPOINT ping

# Should return: PONG

# Test basic operations
redis-cli -h $REDIS_ENDPOINT
> PING
PONG
> SET test:key "Hello World"
OK
> GET test:key
"Hello World"
> DEL test:key
(integer) 1
> EXIT
```

### Step 4: Configure Redis for Celery

```bash
# Update docker-compose .env with Redis endpoint
REDIS_URL=redis://<redis-endpoint>:6379/0

# For Celery configuration (in application code):
# broker_url = 'redis://redis-endpoint:6379/0'
# result_backend = 'redis://redis-endpoint:6379/0'

# Test Celery connection (from EC2 instance)
docker-compose run --rm worker celery -A truematch.celery_app inspect active

# Should return list of active tasks (or empty dict if none)
```

### Step 5: Monitor Redis Performance

```bash
# Connect to Redis CLI
redis-cli -h $REDIS_ENDPOINT

# Check memory usage
> INFO memory
# Look for: used_memory_human, used_memory_peak_human

# Check key count
> DBSIZE

# Check connection count
> INFO clients
# Look for: connected_clients

# Check replication (should show: role:master)
> INFO replication

# Exit
> EXIT

# CloudWatch Metrics
# AWS Console → CloudWatch → Metrics → ElastiCache
# Key metrics:
# - CPUUtilization (should be <20%)
# - DatabaseMemoryUsagePercentage (should be <80%)
# - NetworkBytesIn/Out (monitor for traffic spikes)
# - EngineCPUUtilization
```

---

## Monitoring & Logging

### Step 1: Configure CloudWatch Logs

```bash
# Automatically configured if using docker-compose awslogs driver

# From EC2 instance, install CloudWatch agent (optional)
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
sudo rpm -U ./amazon-cloudwatch-agent.rpm

# Create agent configuration
sudo tee /opt/aws/amazon-cloudwatch-agent/etc/config.json > /dev/null << 'EOF'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/opt/truematch/logs/api.log",
            "log_group_name": "/truematch/api",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/opt/truematch/logs/worker.log",
            "log_group_name": "/truematch/worker",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
EOF

# Start agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

### Step 2: Create CloudWatch Alarms

```bash
# High CPU Utilization (EC2)
aws cloudwatch put-metric-alarm \
  --alarm-name truematch-ec2-cpu-high \
  --alarm-description "Alert if EC2 CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=InstanceId,Value=<instance-id> \
  --alarm-actions arn:aws:sns:ap-southeast-1:<account-id>:truematch-alerts

# High Memory Usage (RDS)
aws cloudwatch put-metric-alarm \
  --alarm-name truematch-rds-cpu-high \
  --alarm-description "Alert if RDS CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=DBInstanceIdentifier,Value=truematchdb \
  --alarm-actions arn:aws:sns:ap-southeast-1:<account-id>:truematch-alerts

# Database connections
aws cloudwatch put-metric-alarm \
  --alarm-name truematch-rds-connections-high \
  --alarm-description "Alert if DB connections > 80" \
  --metric-name DatabaseConnections \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=DBInstanceIdentifier,Value=truematchdb \
  --alarm-actions arn:aws:sns:ap-southeast-1:<account-id>:truematch-alerts

# Redis memory usage
aws cloudwatch put-metric-alarm \
  --alarm-name truematch-redis-memory-high \
  --alarm-description "Alert if Redis memory > 80%" \
  --metric-name DatabaseMemoryUsagePercentage \
  --namespace AWS/ElastiCache \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=CacheClusterId,Value=truematch-redis \
  --alarm-actions arn:aws:sns:ap-southeast-1:<account-id>:truematch-alerts
```

### Step 3: Create Custom CloudWatch Dashboard

```bash
# Create dashboard via AWS CLI
aws cloudwatch put-dashboard \
  --dashboard-name TrueMatch-Staging \
  --dashboard-body file://dashboard-body.json
```

**dashboard-body.json:**
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/EC2", "CPUUtilization", { "stat": "Average", "label": "EC2 CPU" } ],
          [ "AWS/RDS", "CPUUtilization", { "stat": "Average", "label": "RDS CPU" } ],
          [ "AWS/RDS", "DatabaseConnections", { "stat": "Sum", "label": "DB Connections" } ],
          [ "AWS/ElastiCache", "DatabaseMemoryUsagePercentage", { "stat": "Average", "label": "Redis Memory %" } ]
        ],
        "period": 300,
        "stat": "Average",
        "region": "ap-southeast-1",
        "title": "Infrastructure Metrics"
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "fields @timestamp, @message | filter @message like /ERROR/ | stats count() by @logStream",
        "region": "ap-southeast-1",
        "title": "Error Log Count",
        "queryId": "truematch-errors"
      }
    }
  ]
}
```

### Step 4: Set Up Application Monitoring

```python
# In your FastAPI application (fastapi_app.py)

from prometheus_client import Counter, Histogram, start_http_server
import time

# Prometheus metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    request_count.labels(method=request.method, endpoint=request.url.path).inc()
    request_duration.observe(duration)
    
    response.headers["X-Process-Time"] = str(duration)
    return response

# Expose metrics endpoint
if __name__ == "__main__":
    # In docker-compose, expose on 8001
    start_http_server(8001)
    # Then: uvicorn app:app --host 0.0.0.0 --port 8000
```

---

## Troubleshooting Guide

### Common Issues & Solutions

#### 1. EC2 Cannot Connect to RDS

**Symptom:** `psql: could not connect to server`

**Solutions:**
```bash
# Verify RDS is accessible
telnet <rds-endpoint> 5432

# Check EC2 security group
aws ec2 describe-security-groups --query "SecurityGroups[?GroupName=='default']"

# Add ingress rule for EC2 security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-rds-security-group \
  --protocol tcp \
  --port 5432 \
  --source-group sg-ec2-security-group

# Verify RDS security group
aws ec2 describe-security-groups --group-ids <rds-sg-id>
```

#### 2. EC2 Cannot Connect to ElastiCache

**Symptom:** `Connection refused` when running `redis-cli`

**Solutions:**
```bash
# Verify ElastiCache cluster is available
aws elasticache describe-cache-clusters --cache-cluster-id truematch-redis

# Check EC2 security group rule
aws ec2 describe-security-groups --group-ids <elasticache-sg-id>

# Add ingress rule for EC2 security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-elasticache-security-group \
  --protocol tcp \
  --port 6379 \
  --source-group sg-ec2-security-group
```

#### 3. Docker Compose Services Not Starting

**Symptom:** `docker-compose up` fails or containers exit immediately

**Solutions:**
```bash
# Check service logs
docker-compose logs api
docker-compose logs worker
docker-compose logs beat

# Common issues:
# - Invalid environment variables in .env
# - Database not accessible (check credentials)
# - Insufficient memory (t3.micro has 1GB total)

# Verify environment file
docker-compose config

# Check Docker resource usage
docker stats

# Increase available memory by stopping unused services
docker stop <container-id>
```

#### 4. Out of Memory Errors

**Symptom:** OOMKilled or memory pressure warnings

**Solutions:**
```bash
# Check memory allocation in docker-compose.yml
# Adjust resource limits:
api:
  deploy:
    resources:
      limits:
        memory: 256M  # Reduce from 512M if needed
      
# Reduce number of Celery workers
command: celery -A truematch worker --concurrency=1  # Instead of 2

# Disable local Redis (use ElastiCache only)
# Remove redis service from docker-compose.yml

# Check actual memory usage
free -m
docker stats
```

#### 5. Database Connection Pool Exhausted

**Symptom:** `Could not acquire connection pool` or connection timeout

**Solutions:**
```bash
# Reduce connection pool size in .env
DATABASE_POOL_SIZE=3  # Instead of 5

# Reduce number of concurrent processes
# In FastAPI: --workers 2 (instead of 4)
# In Celery: --concurrency=2 (instead of 4)

# Check active connections
psql -h $RDS_ENDPOINT -U appuser -d truematchdb
> SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;
```

#### 6. High Data Transfer Costs

**Symptom:** Unexpected charges, exceeding 1GB free tier

**Solutions:**
```bash
# Monitor data transfer
aws ec2 describe-instances --instance-ids <instance-id> \
  --query 'Reservations[0].Instances[0].NetworkInterfaces[0]'

# Optimize image sizes
docker images --format "table {{.Repository}}\t{{.Size}}"

# Compress logs
gzip -r /opt/truematch/logs/

# Restrict CloudWatch Logs ingestion
# In docker-compose, reduce log retention
logging:
  options:
    awslogs-retention-in-days: 7

# Set up S3 lifecycle policies for log archival
aws s3api put-bucket-lifecycle-configuration \
  --bucket truematch-logs \
  --lifecycle-configuration file://lifecycle.json
```

---

## Backup & Recovery

### Step 1: Manual Database Snapshots

```bash
# Create RDS snapshot
aws rds create-db-snapshot \
  --db-instance-identifier truematchdb \
  --db-snapshot-identifier truematchdb-snapshot-$(date +%Y%m%d-%H%M%S)

# List snapshots
aws rds describe-db-snapshots \
  --query 'DBSnapshots[?DBInstanceIdentifier==`truematchdb`]'

# Delete old snapshots (keep latest 5)
aws rds delete-db-snapshot \
  --db-snapshot-identifier <snapshot-id>
```

### Step 2: Redis Snapshots

```bash
# Trigger Redis snapshot (RDB format)
redis-cli -h $REDIS_ENDPOINT BGSAVE

# Save snapshot to S3 for backup
aws s3 cp /var/lib/redis/dump.rdb \
  s3://truematch-backups/redis/dump-$(date +%Y%m%d-%H%M%S).rdb
```

### Step 3: Application Data Backups

```bash
# Create weekly backup script
cat > /opt/truematch/backup.sh << 'EOF'
#!/bin/bash

DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="/opt/truematch/backups"
S3_BUCKET="s3://truematch-backups"

# Create backup directory
mkdir -p $BACKUP_DIR

# PostgreSQL dump
pg_dump -h $RDS_ENDPOINT -U appuser -d truematchdb | \
  gzip > $BACKUP_DIR/db-dump-$DATE.sql.gz

# Upload to S3
aws s3 cp $BACKUP_DIR/db-dump-$DATE.sql.gz \
  $S3_BUCKET/database/db-dump-$DATE.sql.gz

# Cleanup old backups (keep 4 weeks)
find $BACKUP_DIR -name "db-dump-*.sql.gz" -mtime +28 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/truematch/backup.sh

# Schedule with cron
crontab -e

# Add line:
# 0 2 * * 0 /opt/truematch/backup.sh  # Every Sunday at 2:00 AM UTC
```

### Step 4: Disaster Recovery

```bash
# Restore from RDS snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier truematchdb-restored \
  --db-snapshot-identifier <snapshot-id>

# Restore from database dump
gzip -d < $BACKUP_DIR/db-dump-*.sql.gz | \
  psql -h <new-rds-endpoint> -U admin -d postgres

# Update application configuration
# Update RDS_ENDPOINT in .env
vi /opt/truematch/.env

# Restart application
docker-compose restart api worker beat

# Verify data
docker-compose run --rm api python scripts/verify_db.py
```

---

## Upgrade to EKS

### When to Upgrade

Move to EKS when:
- Load testing shows need for auto-scaling
- Multiple development/staging environments needed
- Team size grows (better for collaboration)
- Cost budget increases beyond $100/month
- Production deployment planned

### Migration Timeline

```
Week 1: Prepare EKS infrastructure
├─ Create EKS cluster
├─ Configure node groups
└─ Deploy system add-ons

Week 2: Convert docker-compose to Kubernetes
├─ Create Kubernetes manifests
├─ Convert docker-compose to helm charts
├─ Test deployment on EKS
└─ Run parallel validation

Week 3: Traffic migration
├─ Deploy to EKS (same environment)
├─ Run compatibility tests
├─ Gradually shift traffic (DNS)
└─ Rollback plan ready

Week 4: Decommission old stack
├─ Monitor EKS stability (1 week)
├─ Decommission EC2 Docker instance
├─ Update documentation
└─ Archive docker-compose configs
```

### EKS Cluster Creation

```bash
# Prerequisites installed:
# - eksctl (https://eksctl.io)
# - kubectl (https://kubernetes.io/docs/tasks/tools/)
# - helm (https://helm.sh)

# Create cluster
eksctl create cluster \
  --name truematch-staging \
  --region ap-southeast-1 \
  --nodegroup-name truematch-workers \
  --node-type t3.micro \
  --nodes 1 \
  --nodes-min 1 \
  --nodes-max 3 \
  --managed \
  --with-oidc

# Get kubeconfig
aws eks update-kubeconfig \
  --name truematch-staging \
  --region ap-southeast-1

# Verify cluster
kubectl get nodes
kubectl get namespaces
```

---

## Cost Control Scripts

### Script 1: Daily Cost Report

```bash
#!/bin/bash
# save as: /opt/truematch/cost-report.sh

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -d "1 day ago" +%Y-%m-%d)

echo "=== TrueMatch AI Daily Cost Report ==="
echo "Date: $TODAY"
echo "Account: $ACCOUNT_ID"
echo ""

# Get today's costs
COSTS=$(aws ce get-cost-and-usage \
  --time-period Start=$TODAY,End=$(date -d "1 day" +%Y-%m-%d) \
  --granularity DAILY \
  --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --region ap-southeast-1 \
  --output text)

echo "Today's Costs by Service:"
echo "$COSTS" | awk '{print $1, $NF}'
echo ""

# Get month-to-date costs
MTD_START=$(date +%Y-%m-01)
MTD_COSTS=$(aws ce get-cost-and-usage \
  --time-period Start=$MTD_START,End=$(date -d "1 day" +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --region ap-southeast-1 \
  --output text)

echo "Month-to-Date Costs:"
echo "$MTD_COSTS" | awk '{print $1, $NF}'
```

### Script 2: Monitor Free Tier Usage

```bash
#!/bin/bash
# save as: /opt/truematch/monitor-free-tier.sh

echo "=== AWS Free Tier Usage Monitor ==="
echo ""

# EC2 Usage
echo "EC2 Instance Running Hours:"
INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Application,Values=truematch-ai" \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text)

if [ "$INSTANCE_ID" != "None" ]; then
  UPTIME=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/EC2 \
    --metric-name CPUUtilization \
    --dimensions Name=InstanceId,Value=$INSTANCE_ID \
    --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 3600 \
    --statistics Average \
    --output text | wc -l)
  echo "  Instance ID: $INSTANCE_ID"
  echo "  Estimated Hours: $UPTIME/750 (Free Tier)"
fi

echo ""

# RDS Usage
echo "RDS PostgreSQL Instance Status:"
RDS_INFO=$(aws rds describe-db-instances \
  --db-instance-identifier truematchdb \
  --query 'DBInstances[0].[DBInstanceIdentifier,DBInstanceClass,AllocatedStorage,DBInstanceStatus]' \
  --output text)
echo "$RDS_INFO"
echo "  Free Tier: db.t3.micro, 20GB storage"

echo ""

# ElastiCache Usage
echo "ElastiCache Redis Cluster Status:"
CACHE_INFO=$(aws elasticache describe-cache-clusters \
  --cache-cluster-id truematch-redis \
  --query 'CacheClusters[0].[CacheClusterId,CacheNodeType,Engine,CacheClusterStatus]' \
  --output text)
echo "$CACHE_INFO"
echo "  Free Tier: cache.t3.micro"

echo ""

# S3 Storage
echo "S3 Storage Usage:"
S3_SIZE=$(aws s3 ls s3://truematch-backups \
  --summarize --recursive | grep "Total Size" | awk '{print $3}')
S3_SIZE_GB=$((S3_SIZE / 1024 / 1024 / 1024))
echo "  Bucket Size: ${S3_SIZE_GB}GB / 5GB (Free Tier)"

echo ""
echo "=== End Report ==="
```

### Script 3: Set Budget Alerts

```bash
#!/bin/bash
# save as: /opt/truematch/set-budget-alerts.sh

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
EMAIL="your-email@example.com"

# Create SNS topic for alerts
SNS_TOPIC_ARN=$(aws sns create-topic \
  --name truematch-cost-alerts \
  --query 'TopicArn' \
  --output text)

# Subscribe email
aws sns subscribe \
  --topic-arn $SNS_TOPIC_ARN \
  --protocol email \
  --notification-endpoint $EMAIL

# Create budget alert
aws budgets create-budget \
  --account-id $AWS_ACCOUNT \
  --budget "{
    \"BudgetName\": \"TrueMatch-Monthly-Budget\",
    \"BudgetLimit\": {
      \"Amount\": \"100\",
      \"Unit\": \"USD\"
    },
    \"TimeUnit\": \"MONTHLY\",
    \"BudgetType\": \"COST\",
    \"CostFilters\": {}
  }" \
  --notifications-with-subscribers "[
    {
      \"Notification\": {
        \"NotificationType\": \"FORECASTED\",
        \"ComparisonOperator\": \"GREATER_THAN\",
        \"Threshold\": 80
      },
      \"Subscribers\": [{
        \"SubscriptionType\": \"EMAIL\",
        \"Address\": \"$EMAIL\"
      }]
    },
    {
      \"Notification\": {
        \"NotificationType\": \"ACTUAL\",
        \"ComparisonOperator\": \"GREATER_THAN\",
        \"Threshold\": 100
      },
      \"Subscribers\": [{
        \"SubscriptionType\": \"EMAIL\",
        \"Address\": \"$EMAIL\"
      }]
    }
  ]"

echo "Budget alerts configured:"
echo "- SNS Topic: $SNS_TOPIC_ARN"
echo "- Email: $EMAIL"
echo "- Budget: $100/month"
echo "- Alert Thresholds: 80% ($80) and 100% ($100)"
```

---

## Summary & Checklist

### Pre-Deployment Checklist

- [ ] AWS account created and verified
- [ ] Billing alerts configured
- [ ] VPC created in ap-southeast-1
- [ ] Security groups defined
- [ ] EC2 instance launched (t3.micro)
- [ ] Docker & Docker Compose installed
- [ ] AWS CLI configured with credentials
- [ ] RDS PostgreSQL created (db.t3.micro)
- [ ] ElastiCache Redis created (cache.t3.micro)
- [ ] ECR repositories created
- [ ] Docker images built and pushed to ECR
- [ ] Environment variables configured
- [ ] docker-compose.yml tested locally
- [ ] Application database migrations run
- [ ] Application deployed on EC2

### Post-Deployment Validation

- [ ] API endpoints responding (test with curl)
- [ ] Database connectivity verified
- [ ] Redis/cache connectivity verified
- [ ] Celery workers processing tasks
- [ ] CloudWatch Logs receiving data
- [ ] Monitoring dashboards created
- [ ] Budget alerts working
- [ ] Backup strategy implemented
- [ ] Cost tracking script running

### Maintenance Tasks (Weekly)

- [ ] Review CloudWatch dashboards
- [ ] Check system resource usage (CPU, memory, storage)
- [ ] Review application logs for errors
- [ ] Test backup/recovery procedures
- [ ] Monitor data transfer usage (watch for > 1GB)
- [ ] Verify database size (should be < 20GB)
- [ ] Check estimated monthly cost

### Maintenance Tasks (Monthly)

- [ ] Review AWS bill for unexpected charges
- [ ] Analyze application performance metrics
- [ ] Test disaster recovery procedures
- [ ] Clean up old CloudWatch logs
- [ ] Review and update security groups
- [ ] Update application dependencies
- [ ] Plan for free tier expiration (month 11)

---

**Document prepared for TrueMatch AI Staging Deployment**  
**Estimated Monthly Cost: $1-2 | Region: ap-southeast-1 | Production Ready: No (Testing Only)**
