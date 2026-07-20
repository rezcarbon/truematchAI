# AWS Deployment Requirements
## TrueMatch AI - Service & Resource Specification

**Document Version:** 1.0  
**Last Updated:** July 21, 2026  
**Target Region:** us-east-1 (Primary) / ap-southeast-1 (Optional APAC)

---

## 1. AWS Services Checklist

### 1.1 Compute Services

#### Amazon EKS (Elastic Kubernetes Service)
**Status:** ✓ REQUIRED  
**Purpose:** Kubernetes cluster management

**Specifications:**
```yaml
EKS Cluster:
  Name: truematch-prod
  Version: 1.29+ (auto-update to latest)
  Region: us-east-1
  VPC: /16 CIDR block (10.0.0.0/16)
  
  Node Groups:
    - Name: core-nodes
      Min: 3
      Max: 10
      Instance Type: m5.large (2 vCPU, 8GB RAM)
      Disk Size: 100GB (gp3)
      
    - Name: compute-nodes (optional)
      Min: 1
      Max: 20
      Instance Type: c5.xlarge (4 vCPU, 8GB RAM)
      Disk Size: 100GB (gp3)
      For: High-computation Celery tasks
  
  Add-ons:
    - vpc-cni (networking)
    - kube-proxy
    - coredns
    - ebs-csi-driver (persistent volumes)
    
  Networking:
    - Subnets: Public (2) + Private (3)
    - Security Groups: Custom (see networking section)
    - NAT Gateways: 2+ for HA
```

**Estimated Costs:**
- Control plane: $0.20/hour (~$150/month)
- Node group 1 (3x m5.large): $0.46/hour (~$350/month)
- Node group 2 optional (2x c5.xlarge): $0.51/hour (~$380/month)

**Pre-requisites:**
- [ ] AWS account with sufficient IAM permissions
- [ ] VPC with public and private subnets
- [ ] IAM roles for nodes and cluster
- [ ] kubectl CLI installed (1.29+)
- [ ] aws-iam-authenticator configured

---

### 1.2 Database Services

#### Amazon RDS for PostgreSQL
**Status:** ✓ REQUIRED  
**Purpose:** Primary relational database

**Specifications:**
```yaml
Database Instance:
  Engine: PostgreSQL 15+
  Instance Class: db.t3.large (production minimum)
  Allocated Storage: 100GB (gp3, autoscaling enabled)
  Max Allocated Storage: 500GB
  
  Backup:
    Retention Period: 30 days
    Backup Window: 02:00-03:00 UTC
    Copy to Region: ap-southeast-1 (optional, for DR)
  
  Multi-AZ: YES (critical for HA)
    - Synchronous replication
    - Automatic failover (<2 min)
    - Standby in different AZ
  
  Performance Insights: ENABLED
    - 7-day retention free tier
    - Helpful for diagnostics
  
  Encryption:
    - At-rest: KMS (aws/rds key)
    - In-transit: SSL/TLS required
  
  Parameter Group:
    max_connections: 200
    shared_buffers: 256MB
    effective_cache_size: 1GB
    work_mem: 8MB
    maintenance_work_mem: 64MB
    
  Enhanced Monitoring:
    - Enabled with CloudWatch
    - Granularity: 60 seconds
```

**Initial Setup Script:**
```sql
CREATE ROLE truematch WITH LOGIN PASSWORD 'STRONG_PASSWORD';
GRANT CONNECT ON DATABASE truematch TO truematch;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
ALTER DATABASE truematch OWNER TO truematch;
```

**Estimated Costs:**
- db.t3.large (Multi-AZ): $0.34/hour (~$250/month)
- Storage (100GB gp3): ~$12/month
- Backup storage (30-day retention): ~$10/month
- Data transfer (0.5TB/month): ~$24/month

**Pre-requisites:**
- [ ] Subnet group created (3+ AZs)
- [ ] Security group with inbound port 5432
- [ ] Parameter group created
- [ ] KMS key for encryption

---

### 1.3 Cache Services

#### Amazon ElastiCache for Redis
**Status:** ✓ REQUIRED  
**Purpose:** Cache, task queue, rate limiting

**Specifications:**
```yaml
Redis Cluster:
  Engine: Redis 7.0+
  Node Type: cache.r6g.large (production recommended)
            cache.t3.micro (minimum, dev only)
  
  Cluster Mode: ENABLED
    - Shards: 2 (for HA)
    - Replicas per shard: 1
    - Auto-failover: ENABLED
  
  Nodes:
    - Primary: 1 per shard
    - Replicas: 1 per shard
    - Total: 4 nodes (2 shards × 2 nodes each)
  
  Performance:
    - Multi-AZ: ENABLED
    - Automatic failover: <30 seconds
  
  Encryption:
    - At-rest: ENABLED (KMS)
    - In-transit: TLS ENABLED
    - Auth token: ENABLED
  
  Backup:
    - Automated snapshots: DAILY
    - Retention: 5 days
  
  Maintenance:
    - Window: Sunday 03:00-04:00 UTC
    - Auto-patching: ENABLED
  
  Memory Management:
    - maxmemory policy: allkeys-lru
    - Eviction: Least Recently Used
```

**Redis Configuration (Redis 7):**
```
# Persistence
save 900 1              # 900s, 1 key change
save 300 10             # 300s, 10 key changes
save 60 10000           # 60s, 10k key changes

# Memory
maxmemory 1gb
maxmemory-policy allkeys-lru

# AOF (Append-Only File)
appendonly yes
appendfsync everysec
```

**Estimated Costs:**
- cache.r6g.large (2 shards × 2 nodes): ~$1.50/hour (~$1,100/month)
- ElastiCache backup storage: ~$5/month

**Pre-requisites:**
- [ ] Subnet group created (3+ AZs)
- [ ] Security group with inbound 6379
- [ ] Auth token generated
- [ ] KMS key for encryption

---

### 1.4 Storage Services

#### Amazon S3 (Simple Storage Service)
**Status:** ✓ REQUIRED  
**Purpose:** File uploads, backups, application logs

**Specifications:**

**Bucket 1: truematch-uploads**
```yaml
Bucket:
  Name: truematch-uploads
  Region: us-east-1
  Versioning: ENABLED
  Block Public Access: ALL (ENABLED)
  
  Encryption:
    Default: KMS (aws/s3)
    SSE: aws:kms
  
  Lifecycle Policy:
    - Transition to GLACIER after 90 days
    - Delete incomplete multipart after 7 days
  
  Access Control:
    - Private (ACL)
    - Only IAM users with permissions can access
  
  CORS: ENABLED
    AllowedMethods: GET, PUT, POST
    AllowedOrigins: https://truematch.digital
  
  Object Lock: DISABLED (unless compliance needed)
  
  Tags:
    Environment: production
    Application: truematch-ai
    Purpose: file-uploads
```

**Bucket 2: truematch-backups**
```yaml
Bucket:
  Name: truematch-backups
  Region: us-east-1
  Versioning: ENABLED
  
  Encryption:
    Default: KMS
    SSE: aws:kms
  
  Storage Class: INTELLIGENT_TIERING
    Auto-transition:
    - to IA (30 days)
    - to ARCHIVE (90 days)
    - to DEEP_ARCHIVE (180 days)
  
  Lifecycle Policy:
    Retention: 30 days (with versioning)
    Delete old versions: 90 days
  
  Replication: OPTIONAL
    Destination: ap-southeast-1 (disaster recovery)
    Replication Time: 15 minutes
  
  Logging: ENABLED
    Target: truematch-logs
    Prefix: s3-access-logs/
```

**Bucket 3: truematch-logs** (optional)
```yaml
Bucket:
  Name: truematch-logs
  Region: us-east-1
  
  Lifecycle Policy:
    30-day retention (application logs)
    90-day retention (S3 access logs)
  
  Encryption: KMS
  Block Public Access: ALL
```

**Estimated Costs:**
- Storage (100GB uploads @ standard): ~$2.35/month
- Backups (500GB @ intelligent tiering): ~$10-20/month
- Data transfer (0.5TB/month egress): ~$24/month
- S3 API requests: ~$2/month

**Pre-requisites:**
- [ ] Bucket names verified (must be globally unique)
- [ ] KMS keys created for encryption
- [ ] IAM policies created for S3 access

---

### 1.5 Container Registry

#### Amazon ECR (Elastic Container Registry)
**Status:** ✓ REQUIRED  
**Purpose:** Docker image storage and distribution

**Specifications:**
```yaml
Repository: truematch-api
  Image URI: 123456789012.dkr.ecr.us-east-1.amazonaws.com/truematch-api
  Encryption: KMS
  Scan: ENABLED (on push)
  Image Tag Mutability: ENABLED
  
Repository: truematch-web
  Image URI: 123456789012.dkr.ecr.us-east-1.amazonaws.com/truematch-web
  Encryption: KMS
  Scan: ENABLED

Lifecycle Policies:
  Keep: Last 10 images tagged
  Keep: Last 5 untagged images
  Expire: Untagged images older than 7 days
  
Tags (for each image):
  environment: production
  version: v1.2.3
  timestamp: 2026-07-21T12:00:00Z
```

**Estimated Costs:**
- Storage: ~$0.10 per GB/month (~$5-10/month for 50-100 images)
- Scan: ~$0.50/image scanned (~$5/month for 10 scans)
- Data transfer: Included with EKS

**Pre-requisites:**
- [ ] Repositories created
- [ ] AWS credentials configured for docker push
- [ ] Lifecycle policies configured

---

### 1.6 Secrets Management

#### AWS Secrets Manager
**Status:** ✓ REQUIRED  
**Purpose:** Secure storage and rotation of secrets

**Specifications:**
```yaml
Secrets to Create:
  - truematch/db/password
  - truematch/jwt/secret
  - truematch/encryption/key
  - truematch/encryption/index-key
  - truematch/aws/s3/access-key-id
  - truematch/aws/s3/secret-access-key
  - truematch/anthropic/api-key
  - truematch/sendgrid/api-key
  - truematch/singpass/sig-jwk
  - truematch/singpass/enc-jwk

Rotation Policy:
  Database password: Every 90 days
  API keys: Every 180 days
  Encryption keys: Manual (don't rotate)
  JWT secret: Manual (rotation requires client re-auth)

Encryption:
  KMS Key: aws/secretsmanager (default)
  Custom KMS Key: (recommended for production)

Access Control:
  Policy: IAM role truematch-eks-secrets
  Permissions: GetSecretValue, DescribeSecret
```

**Integration with Kubernetes:**
Option 1: Manual secret creation
```bash
kubectl create secret generic truematch-secrets \
  --from-literal=DATABASE_PASSWORD="..." \
  -n truematch
```

Option 2: External Secrets Operator (Recommended)
```yaml
SecretStore:
  Provider: AWS Secrets Manager
  Auth: IRSA (IAM Roles for Service Accounts)
  
ExternalSecret:
  Name: truematch-secrets
  SecretStoreRef: aws-secrets
  Refresh: 1h
  Template:
    data:
      DATABASE_PASSWORD: "{{ .database_password }}"
```

**Estimated Costs:**
- Storage: $0.40/secret/month (~$4/month for 10 secrets)
- API calls: $0.04 per 10k calls (~$1/month expected)
- Rotation: $0/month (automatic)

**Pre-requisites:**
- [ ] Secrets created with rotation policies
- [ ] IAM policy for EKS nodes to access Secrets Manager
- [ ] (Optional) External Secrets Operator installed

---

### 1.7 Network & Security

#### AWS VPC (Virtual Private Cloud)
**Status:** ✓ REQUIRED  
**Purpose:** Network isolation and security

**Specifications:**
```yaml
VPC:
  CIDR: 10.0.0.0/16
  EnableDnsHostnames: true
  EnableDnsSupport: true
  
  Subnets:
    Public Subnet 1: 10.0.1.0/24 (AZ: us-east-1a)
    Public Subnet 2: 10.0.2.0/24 (AZ: us-east-1b)
    Private Subnet 1: 10.0.10.0/24 (AZ: us-east-1a)
    Private Subnet 2: 10.0.11.0/24 (AZ: us-east-1b)
    Private Subnet 3: 10.0.12.0/24 (AZ: us-east-1c)
  
  Internet Gateway: 1 (for egress)
  NAT Gateways: 2+ (in public subnets for HA)
  
  Route Tables:
    Public: 0.0.0.0/0 → IGW
    Private: 0.0.0.0/0 → NAT Gateway
    Database: Internal only (via security groups)
```

#### Security Groups
```yaml
EKS Control Plane SG:
  Inbound: Allow 443 (HTTPS) from node security group
  Outbound: Allow all

EKS Node SG:
  Inbound:
    - 10.0.0.0/16 (VPC CIDR) from nodes, RDS, ElastiCache
    - 443 (HTTPS) from internet (for external APIs)
  Outbound: Allow all

ALB SG:
  Inbound:
    - 80 (HTTP) from 0.0.0.0/0 (auto-redirect to 443)
    - 443 (HTTPS) from 0.0.0.0/0
  Outbound:
    - 8000 to EKS Node SG

RDS SG:
  Inbound: 5432 from EKS Node SG only
  Outbound: None (database, no external connections)

ElastiCache SG:
  Inbound: 6379 from EKS Node SG only
  Outbound: None (cache, no external connections)
```

---

### 1.8 Load Balancing

#### AWS Application Load Balancer (ALB)
**Status:** ✓ REQUIRED  
**Purpose:** Layer 7 load balancing, SSL/TLS termination

**Specifications:**
```yaml
Load Balancer:
  Type: Application Load Balancer
  Scheme: internet-facing
  Subnets: Public subnets (2+)
  
  Target Groups:
    - Name: truematch-api
      Protocol: HTTP
      Port: 8000
      Path: /
      Health Check:
        Path: /livez
        Interval: 30s
        Timeout: 5s
        Healthy Threshold: 2
        Unhealthy Threshold: 3
  
  Listeners:
    HTTP (80):
      Action: Redirect to HTTPS (443)
      
    HTTPS (443):
      Certificates:
        - truematch-cert (from ACM)
        - Wildcard: *.truematch.digital
      Target Group: truematch-api
      
  SSL Policy: ELBSecurityPolicy-TLS-1-2-2017-01
  Minimum TLS: 1.2
  
  Logging:
    Enabled: true
    S3 Bucket: truematch-logs
    Prefix: alb-logs/
  
  WAF: (Recommended) Add to ALB
    - Prevent SQL injection
    - Prevent XSS
    - Rate limiting
```

**Estimated Costs:**
- ALB: $0.0225/hour (~$165/month)
- Data processing: $0.006 per GB (~$20/month for 3.3TB)
- New connections: $0.006 per LCU (~$30/month for 10k connections)

---

### 1.9 Certificate Management

#### AWS Certificate Manager (ACM)
**Status:** ✓ REQUIRED  
**Purpose:** SSL/TLS certificates

**Specifications:**
```yaml
Certificate:
  Domain: api.truematch.digital
  Subject Alt Names:
    - *.truematch.digital
    - truematch.digital
  
  Validation: DNS (preferred)
  Auto-renewal: ENABLED (before expiry)
  
  Integration: ALB + Kubernetes Ingress
```

**Estimated Costs:**
- Public certificates: FREE (within AWS)
- Private CA: $400/month (if needed)

---

### 1.10 Monitoring & Logging

#### Amazon CloudWatch
**Status:** ✓ RECOMMENDED  
**Purpose:** Centralized monitoring, logging, alarms

**Specifications:**
```yaml
Log Groups:
  /ecs/truematch-api:
    Retention: 30 days
    
  /ecs/truematch-worker:
    Retention: 30 days
    
  /aws/rds/instance/truematch:
    Retention: 7 days

Metrics:
  Custom Namespaces:
    - TrueMatch/API (latency, errors, throughput)
    - TrueMatch/Workers (task count, processing time)
    - TrueMatch/Database (connections, queries)

Alarms:
  API:
    - HTTP 5xx errors > 5% for 5 min
    - Latency p95 > 1s for 10 min
    - Unhealthy targets > 0 for 2 min
    
  Database:
    - CPU > 80% for 5 min
    - Connections > 180 for 5 min
    - Storage > 80% for 1 hour
    
  Cache:
    - CPU > 75% for 5 min
    - Memory > 80% for 5 min
    - Evictions > 1000/min for 2 min

Dashboards:
  Main:
    - API health (uptime, latency, errors)
    - Database health (connections, CPU, storage)
    - Cache health (memory, hits, evictions)
    - Worker status (active tasks, queue depth)
```

**Estimated Costs:**
- CloudWatch Logs (1GB/day ingestion): ~$30/month
- Metrics: ~$10/month
- Dashboards: FREE
- Alarms: FREE
- (Alternative: Prometheus/Grafana in-cluster - already configured)

---

## 2. AWS Recommended Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet (0.0.0.0/0)                    │
└────────────────────────────────┬────────────────────────────────┘
                                 │ HTTPS (443)
                                 ▼
                    ┌─────────────────────────┐
                    │   ACM Certificate       │
                    │ *.truematch.digital     │
                    └────────────┬────────────┘
                                 │
                    ┌─────────────┴────────────┐
                    │ Application Load        │
                    │ Balancer (ALB)          │
                    │ internet-facing         │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │   AWS VPC (10.0/16)     │
                    │                         │
    ┌───────────────┴────────┐                │
    │ Public Subnets         │                │
    │ (NAT Gateways)         │                │
    └───────────────┬────────┘                │
                    │                         │
    ┌───────────────┴────────────────────┐    │
    │    Private Subnets (3 AZs)         │    │
    │                                    │    │
    │  ┌──────────────────────┐          │    │
    │  │  EKS Cluster         │          │    │
    │  │  (Kubernetes)        │          │    │
    │  │                      │          │    │
    │  │ Node Groups:         │          │    │
    │  │ - 3x m5.large        │          │    │
    │  │ - 2x c5.xlarge (opt) │          │    │
    │  │                      │          │    │
    │  │ Pods:                │          │    │
    │  │ ├─ API (3 replicas)  │          │    │
    │  │ ├─ Workers (3-20)    │          │    │
    │  │ ├─ Beat (1 replica)  │          │    │
    │  │ ├─ Prometheus        │          │    │
    │  │ ├─ Fluent-bit        │          │    │
    │  │ └─ Loki              │          │    │
    │  └──┬───────────────────┘          │    │
    │     │                              │    │
    │  ┌──┴─────────────────────────┐    │    │
    │  │  ElastiCache Redis         │    │    │
    │  │  (cluster mode)            │    │    │
    │  │  - 2 shards × 2 nodes      │    │    │
    │  │  - Multi-AZ failover       │    │    │
    │  └────────────────────────────┘    │    │
    │                                    │    │
    │  ┌────────────────────────────┐    │    │
    │  │  RDS PostgreSQL            │    │    │
    │  │  - db.t3.large (Multi-AZ)  │    │    │
    │  │  - 100GB gp3               │    │    │
    │  │  - Automated backups       │    │    │
    │  └────────────────────────────┘    │    │
    │                                    │    │
    └────────────────────────────────────┘    │
                                              │
    ┌─────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────┐
│   Amazon S3                      │
│                                  │
│ • truematch-uploads              │
│   (File storage)                 │
│                                  │
│ • truematch-backups              │
│   (PostgreSQL backups)           │
│                                  │
│ • truematch-logs                 │
│   (Application logs)             │
│                                  │
│ Encryption: KMS                  │
│ Versioning: ENABLED              │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│   AWS Secrets Manager            │
│                                  │
│ • Database credentials           │
│ • API keys (Anthropic, etc)      │
│ • Encryption keys                │
│ • JWT secrets                    │
│                                  │
│ Encryption: KMS                  │
│ Rotation: Automated              │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│   Amazon ECR                     │
│                                  │
│ • truematch-api:v1.2.3           │
│ • truematch-web:v1.2.3           │
│                                  │
│ Encryption: KMS                  │
│ Scan: ENABLED                    │
└──────────────────────────────────┘
```

---

## 3. Region-Specific Recommendations

### 3.1 Primary Region: us-east-1 (Virginia)
**Advantages:**
- Lowest cost for most AWS services
- Largest service availability
- Lowest latency for North America

**Recommended:**
- Production deployment
- Primary database
- Primary cache
- Application code

### 3.2 Secondary Region: ap-southeast-1 (Singapore)
**When to Deploy:**
- APAC users require local compliance (PDPA)
- Disaster recovery / business continuity
- Data residency requirements

**Setup:**
- RDS read replica (cross-region)
- S3 cross-region replication
- Separate EKS cluster (optional)

**Estimated Additional Costs:** +$1,500-2,000/month

---

## 4. Cost Optimization Strategies

### 4.1 Compute Savings

1. **Reserved Instances**
   - Save 30-50% on EC2 costs
   - Commit 1-3 years
   - Estimated savings: $100-150/month

2. **Spot Instances for Workers**
   - Save 70% on compute costs
   - Use for batch/non-critical tasks
   - Estimated savings: $200-300/month

3. **Auto-scaling**
   - Scale down during off-hours
   - Scale up during peak hours
   - Estimated savings: $50-100/month

### 4.2 Storage Savings

1. **S3 Intelligent Tiering**
   - Automatic cost optimization
   - Transition to cheaper storage classes
   - Estimated savings: 20-30% on backup storage

2. **S3 Lifecycle Policies**
   - Transition old backups to Glacier
   - Delete after retention period
   - Estimated savings: $5-10/month

3. **RDS Reserved Instances**
   - Save 30-50% on database costs
   - Estimated savings: $75-100/month

### 4.3 Network Savings

1. **Data Transfer**
   - Use VPC endpoints to avoid NAT costs
   - Minimize cross-region traffic
   - Estimated savings: $10-20/month

2. **CloudFront for Static Assets**
   - Cache static files
   - Reduce S3 bandwidth
   - Estimated savings: $20-50/month

**Total Potential Savings:** $450-650/month (36-52% reduction)

---

## 5. Security Best Practices

### 5.1 IAM Policies

**EKS Node Role Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeNetworkInterfaces",
        "ec2:DescribeInstances",
        "ec2:DescribeSubnets"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer",
        "ecr:DescribeImages",
        "ecr:DescribeRepositories",
        "ecr:ListImages"
      ],
      "Resource": "arn:aws:ecr:us-east-1:ACCOUNT:repository/truematch-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::truematch-uploads/*",
        "arn:aws:s3:::truematch-backups/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::truematch-uploads",
        "arn:aws:s3:::truematch-backups"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "arn:aws:kms:us-east-1:ACCOUNT:key/KEY_ID"
    }
  ]
}
```

**S3 Bucket Policy (truematch-uploads):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowEKSNodeAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT:role/eks-node-role"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::truematch-uploads/*"
    },
    {
      "Sid": "DenyUnencryptedObjectUploads",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::truematch-uploads/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "aws:kms"
        }
      }
    }
  ]
}
```

### 5.2 Network Security

1. **VPC Flow Logs:** Monitor network traffic
2. **Security Groups:** Minimal ingress/egress
3. **NACLs:** Additional network ACL rules
4. **VPC Endpoints:** Direct access to AWS services (no NAT)
5. **AWS WAF:** Attach to ALB for web protection

### 5.3 Data Protection

1. **Encryption at Rest:** KMS for all data
2. **Encryption in Transit:** TLS 1.2+ for all connections
3. **Field-Level Encryption:** Application-level encryption for PII
4. **Backup Encryption:** All backups encrypted with KMS
5. **Secrets Rotation:** Automatic rotation via Secrets Manager

---

## 6. Compliance & Governance

### 6.1 Data Residency

**Primary:** US-based (Virginia)  
**Optional APAC:** Singapore (for PDPA compliance)  
**No:** EU deployments (not configured for GDPR)

### 6.2 Audit & Logging

1. **CloudTrail:** API call logging (3-5 years retention)
2. **VPC Flow Logs:** Network traffic logging
3. **S3 Access Logs:** Object access logging
4. **RDS Query Logging:** Database query logging
5. **Application Logs:** Fluent-bit → Loki

### 6.3 Compliance Frameworks

- ✓ SOC 2 Type II (via AWS)
- ✓ HIPAA (with proper configuration)
- ✓ PCI-DSS (with WAF/IDS)
- ✓ PDPA (Singapore, if APAC region enabled)
- ⚠️ GDPR (partial - requires additional configuration)

---

## 7. Checklist for AWS Deployment

### Pre-Deployment
- [ ] AWS account created and verified
- [ ] IAM roles and policies created
- [ ] VPC and subnets configured
- [ ] Security groups defined
- [ ] KMS keys created
- [ ] SSL/TLS certificate requested (ACM)

### Infrastructure Provisioning
- [ ] EKS cluster created
- [ ] Node groups configured and healthy
- [ ] RDS PostgreSQL deployed (Multi-AZ)
- [ ] ElastiCache Redis deployed (cluster mode)
- [ ] S3 buckets created and configured
- [ ] ECR repositories created
- [ ] Secrets Manager secrets created
- [ ] ALB deployed and configured

### Kubernetes Setup
- [ ] kubectl configured and tested
- [ ] NGINX ingress controller installed
- [ ] cert-manager installed
- [ ] External Secrets Operator installed (optional)
- [ ] Prometheus/Loki/Fluent-bit deployed
- [ ] Network policies applied

### Application Deployment
- [ ] Docker images built and pushed to ECR
- [ ] Database migrations run
- [ ] Kubernetes manifests updated with prod values
- [ ] Secrets mounted in deployments
- [ ] Health checks validated
- [ ] Monitoring and alerting configured

### Post-Deployment
- [ ] End-to-end testing completed
- [ ] Load testing passed
- [ ] Security scanning passed
- [ ] Backup/restore tested
- [ ] 24-hour monitoring completed
- [ ] Runbooks documented

---

## 8. Support & Documentation

**AWS Support Plan:** Business (recommended for production)
- Cost: $100+/month (7% of infrastructure cost)
- SLA: 4-hour response for production issues
- Access to AWS consultants

**Documentation References:**
- AWS EKS Best Practices Guide
- AWS RDS Best Practices
- AWS ElastiCache Guide
- AWS Well-Architected Framework
- AWS Security Best Practices

**Next Steps:**
1. Review this document with infrastructure team
2. Approve cost estimate and architecture
3. Begin AWS resource provisioning
4. Configure Kubernetes add-ons
5. Deploy application manifests
6. Validate and test thoroughly

---

*AWS Deployment Requirements - Approved for production deployment. Last reviewed: July 21, 2026*
