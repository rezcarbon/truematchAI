# AWS Deployment Configuration Plan: TrueMatch AI
## Comprehensive Production Architecture for ap-southeast-1

**Document Version:** 1.0  
**Date:** July 2026  
**Account ID:** 525125475338  
**Region:** ap-southeast-1 (Singapore)  
**Target Scale:** 10,000 DAU initial → 100,000+ growth  

---

## Executive Summary

This document outlines a production-grade, highly available AWS deployment architecture for TrueMatch AI's FastAPI backend. The configuration emphasizes:

- **High Availability:** Multi-AZ deployment across Singapore region
- **Scalability:** Autoscaling infrastructure supporting 10x growth without re-architecture
- **Cost Optimization:** ~USD 3,200-4,500/month for initial scale, ~USD 8,500-12,000/month at 100k DAU
- **Security:** Private subnets, encryption at rest/transit, IAM policies, VPC isolation
- **Operational Excellence:** Infrastructure as Code ready, comprehensive monitoring

### Recommended Core Configuration

| Component | Selection | Rationale |
|-----------|-----------|-----------|
| **EKS Cluster** | 3x t4g.large (ARM-based) | Graviton2 processors, 20% cost savings, sufficient for 10k DAU |
| **RDS PostgreSQL** | t4g.medium (Multi-AZ) | 4 vCPU, 16GB RAM, auto-scaling storage, 99.95% availability |
| **ElastiCache Redis** | 3x cache.t4g.small (cluster mode) | Multi-AZ, auto-failover, 30GB total capacity |
| **VPC CIDR** | 10.0.0.0/16 | Flexible for growth, 65,536 IPs |
| **NAT Gateway** | 1 per AZ (2 total) | High availability, 2 Gbps baseline |
| **Load Balancer** | ALB with 2 AZs | Layer 7 routing, auto-scaling target groups |

**Monthly Cost Estimate (Initial):** USD 3,200-3,600

---

## 1. VPC & Networking Configuration

### 1.1 VPC Design

```
VPC CIDR: 10.0.0.0/16 (65,536 IPs)

Availability Zones (ap-southeast-1a, ap-southeast-1b, ap-southeast-1c)

Public Subnets (NAT Gateway access):
  - ap-southeast-1a: 10.0.1.0/24   (256 IPs)
  - ap-southeast-1b: 10.0.2.0/24   (256 IPs)

Private Subnets - EKS Nodes:
  - ap-southeast-1a: 10.0.11.0/24  (256 IPs)
  - ap-southeast-1b: 10.0.12.0/24  (256 IPs)
  - ap-southeast-1c: 10.0.13.0/24  (256 IPs)

Private Subnets - Database/Cache (No internet egress):
  - ap-southeast-1a: 10.0.21.0/24  (256 IPs)
  - ap-southeast-1b: 10.0.22.0/24  (256 IPs)
  - ap-southeast-1c: 10.0.23.0/24  (256 IPs)

Reserved for future expansion: 10.0.30.0/22 - 10.0.255.0/24
```

**Rationale:**
- 3 AZs for high availability across Singapore region
- Separate subnets for EKS, databases, and cache isolate blast radius
- Public subnets minimal size (only NAT gateways and ALB)
- Database subnets completely private with no internet egress

### 1.2 Internet Gateway & NAT Configuration

```yaml
Internet Gateway:
  - Name: truematch-igw
  - Attached to VPC: 10.0.0.0/16
  - Route to public subnets via route tables

NAT Gateways (High Availability):
  - Gateway 1: ap-southeast-1a public subnet (10.0.1.0/24)
    Elastic IP: Static allocation (for DNS whitelisting)
  - Gateway 2: ap-southeast-1b public subnet (10.0.2.0/24)
    Elastic IP: Static allocation
    
  - Throughput: 2 Gbps baseline (sufficient for 100k DAU)
  - Data processing: ~USD 45/month per NAT (1 billion packets)
```

### 1.3 Route Table Configuration

**Public Route Table (truematch-public-rt):**
```
Destination         | Target               | Use Case
10.0.0.0/16        | Local               | Internal VPC traffic
0.0.0.0/0          | Internet Gateway     | Internet egress for public subnet
```

**Private Route Table - AZ-A (truematch-private-aza-rt):**
```
Destination         | Target                         | Use Case
10.0.0.0/16        | Local                         | Internal VPC traffic
0.0.0.0/0          | NAT Gateway (ap-southeast-1a) | Internet egress via AZ-A NAT
```

**Private Route Table - AZ-B (truematch-private-azb-rt):**
```
Destination         | Target                         | Use Case
10.0.0.0/16        | Local                         | Internal VPC traffic
0.0.0.0/0          | NAT Gateway (ap-southeast-1b) | Internet egress via AZ-B NAT
```

**Database Route Table (truematch-db-rt):**
```
Destination         | Target  | Use Case
10.0.0.0/16        | Local   | Internal VPC traffic only (NO internet)
```

### 1.4 Security Groups

**ALB Security Group (truematch-alb-sg):**
```yaml
Inbound Rules:
  - HTTP (80):   0.0.0.0/0      → Internet traffic (redirect to 443)
  - HTTPS (443): 0.0.0.0/0      → Internet traffic (production)
  - HTTPS (443): 0.0.0.0/0      → IPv6 ::/0 (IPv6 support)

Outbound Rules:
  - ALL traffic: 10.0.11.0/24   → EKS nodes (AZ-A)
  - ALL traffic: 10.0.12.0/24   → EKS nodes (AZ-B)
  - ALL traffic: 10.0.13.0/24   → EKS nodes (AZ-C)
```

**EKS Node Security Group (truematch-eks-sg):**
```yaml
Inbound Rules:
  - TCP 443:      10.0.1.0/24    → ALB (HTTPS traffic)
  - TCP 443:      10.0.2.0/24    → ALB (HTTPS traffic)
  - ALL traffic:  10.0.0.0/16    → Pod-to-pod communication
  - TCP 22:       10.0.0.0/16    → SSH from bastion (optional)

Outbound Rules:
  - ALL traffic:  0.0.0.0/0      → Internet (for yum, pip, docker pulls)
  - ALL traffic:  10.0.21.0/24   → Database (AZ-A)
  - ALL traffic:  10.0.22.0/24   → Database (AZ-B)
  - ALL traffic:  10.0.23.0/24   → Database (AZ-C)
```

**RDS Security Group (truematch-rds-sg):**
```yaml
Inbound Rules:
  - TCP 5432:     10.0.11.0/24   → EKS nodes (AZ-A)
  - TCP 5432:     10.0.12.0/24   → EKS nodes (AZ-B)
  - TCP 5432:     10.0.13.0/24   → EKS nodes (AZ-C)
  - TCP 5432:     10.0.1.0/24    → ALB for connection pooling (optional)

Outbound Rules:
  - ALL traffic:  0.0.0.0/0      → Allow all outbound (for monitoring)
```

**ElastiCache Security Group (truematch-redis-sg):**
```yaml
Inbound Rules:
  - TCP 6379:     10.0.11.0/24   → EKS nodes (AZ-A)
  - TCP 6379:     10.0.12.0/24   → EKS nodes (AZ-B)
  - TCP 6379:     10.0.13.0/24   → EKS nodes (AZ-C)
  - TCP 6379:     10.0.0.0/16    → Cross-subnet (for redundancy)

Outbound Rules:
  - ALL traffic:  0.0.0.0/0      → Allow all outbound
```

### 1.5 VPC Endpoints (Cost Optimization)

**Gateway Endpoints (Free):**
```yaml
S3 Gateway Endpoint:
  - Use: ECR image pulling, CloudWatch logs, backups
  - Route table: Private route tables
  - Policy: Allow GetObject, ListBucket for ECR and CloudWatch

DynamoDB Gateway Endpoint:
  - Use: Future session storage or caching layer
  - Route table: Private route tables
  - Policy: Restrictive (application-specific)
```

**Interface Endpoints (Optional, ~USD 7-15/month):**
```yaml
ECR API Endpoint:
  - Service: com.amazonaws.ap-southeast-1.ecr.api
  - Replaces internet route for image pulls
  - Cost: 0.014/month (2 endpoints) + 0.01/GB data
  - Recommendation: Deploy if using >50GB/month image pulls

CloudWatch Logs Endpoint:
  - Service: com.amazonaws.ap-southeast-1.logs
  - Direct log delivery without NAT bandwidth
  - Cost: Included in CloudWatch pricing
```

---

## 2. RDS PostgreSQL Configuration

### 2.1 Instance Selection: t4g.medium (Recommended)

**Rationale for t4g.medium (vs alternatives):**

| Metric | t3.medium | t4g.medium | t3.large | t4g.large |
|--------|-----------|-----------|----------|-----------|
| vCPU | 2 | 2 | 2 | 2 |
| Memory | 4 GB | 16 GB | 8 GB | 32 GB |
| Network | Moderate | 5 Gbps | Moderate | 10 Gbps |
| Burstable | Yes | Yes | Yes | Yes |
| Price/month | $45 | $56 | $90 | $112 |
| **Processor** | Intel Xeon | **Graviton2** | Intel Xeon | **Graviton2** |

**Recommendation:** `t4g.medium` because:
1. **16GB RAM** sufficient for 10k DAU with connection pooling (100-300 connections)
2. **Graviton2** ARM processor: 20% cost savings, better price-performance
3. **Burstable capacity** suitable for variable OLTP workloads
4. **Easy upgrade path** to t4g.large (32GB) when reaching 50k DAU

### 2.2 Storage Configuration

```yaml
Initial Storage:
  Size: 100 GB
  Type: gp3 (General Purpose SSD)
  IOPS: 3,000 (baseline)
  Throughput: 125 MB/s (baseline)
  Cost: ~USD 10/month

Auto-scaling Configuration:
  Maximum: 1000 GB
  Threshold: Scale when 80% capacity used
  Increment: 10% or 100GB, whichever is less
  
Growth Projection (10k→100k DAU):
  Estimate: 1-2 GB/month growth
  Timeline to 1TB: ~40-50 months
  
Monitoring:
  CloudWatch Alarm: FreeStorageSpace < 10%
  Alert threshold: Trigger when 50GB remains
```

**Cost Breakdown:**
- 100 GB: USD 10/month
- 200 GB: USD 20/month
- 500 GB: USD 50/month
- 1000 GB: USD 100/month

### 2.3 Multi-AZ Deployment

```yaml
Configuration:
  Primary: ap-southeast-1a (t4g.medium)
  Standby: ap-southeast-1b (t4g.medium standby replica)
  
  Failover Time: <2 minutes (automatic)
  RPO (Recovery Point Objective): ~0-5 seconds
  RTO (Recovery Time Objective): <2 minutes
  
Availability:
  Single-AZ: 99.5%
  Multi-AZ: 99.95% (recommended for production)
  
Cost Impact: +100% instance cost (standby is charged)
  t4g.medium Multi-AZ: USD 112/month (vs USD 56 single)
  
Benefits:
  - Automatic failover without manual intervention
  - Zero data loss with synchronous replication
  - Maintenance windows impact only primary (seconds)
  - Regional high availability
```

### 2.4 Backup & Recovery

```yaml
Automated Backups:
  Retention Period: 14 days (balance between cost and recovery)
  Backup Window: 03:00-04:00 UTC+8 (low traffic period)
  Multi-AZ Backup: Yes (backups from standby)
  
Backup Storage Cost:
  14 days retention: ~USD 5-10/month initially
  Grows with data size: 100GB data → ~10GB backup/day
  
Point-in-Time Recovery (PITR):
  Enabled: Yes
  Recovery window: 14 days
  Restore time: 5-10 minutes to new instance
  
Manual Snapshots:
  Frequency: Weekly (before major deployments)
  Retention: 30 days minimum
  Cross-region: Yes (replicate to ap-southeast-2 for DR)
  
Emergency Recovery Plan:
  - RTO (Restore): 10-15 minutes (new instance)
  - RPO: <5 minutes (from last backup)
  - Cross-AZ failover: <2 minutes
  - Procedure: Automated via CloudFormation/Terraform
```

### 2.5 Security Configuration

```yaml
Encryption:
  At-Rest:
    Type: AWS KMS (Customer Managed Key)
    Key Policy: Restrict to truematch IAM role
    Rotation: Annual
    Cost: ~USD 1/month per key
    
  In-Transit:
    SSL/TLS: Enabled (AWS managed)
    Require SSL: Yes (force_ssl parameter)
    Port: 5432 (default, non-standard not recommended)

Database Authentication:
  Method: IAM Database Authentication + password
  Setup:
    - RDS Proxy uses IAM role for app connections
    - Password stored in AWS Secrets Manager
    - Rotation: Automatic every 30 days
    - Cost: ~USD 0.40/month per secret
    
Network Access:
  VPC: Exclusive (no public endpoint)
  Subnets: DB subnets (10.0.21.0/24, 10.0.22.0/24, 10.0.23.0/24)
  Security Group: truematch-rds-sg (port 5432 from EKS only)
  
Parameter Groups:
  Custom: truematch-postgresql14
  Key Settings:
    shared_buffers: 4GB (25% of instance RAM)
    effective_cache_size: 12GB (75% of instance RAM)
    work_mem: 16MB (per operation)
    maintenance_work_mem: 1GB
    max_connections: 500 (via RDS Proxy: 100 max)
    random_page_cost: 1.1 (SSD optimization)
    log_statement: 'ddl' (for audit)
    log_min_duration_statement: 1000 (log slow queries >1s)
    auto_vacuum: on (default)
```

### 2.6 Performance & Monitoring

```yaml
Performance Insights:
  Enabled: Yes
  Retention: 7 days free
  Features:
    - Database load visualization
    - Top SQL queries
    - Wait events monitoring
  Cost: Included in RDS pricing

Enhanced Monitoring:
  Interval: 60 seconds
  Metrics:
    - CPU utilization
    - Database connections
    - Read/write IOPS
    - Memory utilization
    - Disk queue depth
    - Network throughput
  Cost: ~USD 3-5/month

CloudWatch Alarms:
  1. CPU > 80% for 5 min → Page on-call
  2. Database connections > 400 → Investigate connection leak
  3. Free storage space < 50GB → Auto-scale trigger
  4. Read latency > 10ms → Check slow queries
  5. Replication lag > 1s → Alert DBA
  
Query Logs:
  Destination: CloudWatch Logs group: /aws/rds/database/truematch-db
  Retention: 30 days
  Filter: Queries > 1 second (slow query log)
  Cost: ~USD 0.50-2/month
```

### 2.7 Cost Estimation (RDS)

```
Monthly Cost Breakdown:

Instance (t4g.medium Multi-AZ):     USD 112.00
Storage (100 GB gp3):                USD 10.00
Automated Backups (14 days):         USD 5.00
Performance Insights:                USD 0.00 (included)
Enhanced Monitoring:                 USD 4.00
Data Transfer (out):                 USD 5.00
RDS Proxy (1 instance):              USD 15.00
────────────────────────────────────────────
TOTAL RDS Monthly:                   USD 151.00

Annual Cost (Year 1):                USD 1,812

Growth Path (10k→100k DAU):
- Month 1-6:   t4g.medium (USD 151/mo)
- Month 7-12:  t4g.large (USD 224/mo) - storage → 300GB
- Year 2:      t4g.large + standby (USD 224/mo)
```

---

## 3. ElastiCache Redis Configuration

### 3.1 Node Type Selection: cache.t4g.small (Cluster Mode)

**Rationale:**

| Metric | cache.t3.micro | cache.t4g.small | cache.t3.small | cache.t4g.medium |
|--------|---|---|---|---|
| Memory | 0.5 GB | 1.37 GB | 1.37 GB | 3.09 GB |
| vCPU | Shared | 0.5 | Shared | 1.0 |
| Burstable | Yes | Yes | Yes | Yes |
| Throughput | Low | 1 Gbps | 1 Gbps | 1 Gbps |
| Price/month | ~$8 | ~$12 | ~$12 | ~$22 |
| Suitable for | Dev | **10k DAU** | 10k DAU | 50k+ DAU |

**Recommendation:** `cache.t4g.small` cluster mode (3 nodes) because:
1. **1.37 GB per node** = 4.1 GB total (sufficient for session cache + request cache)
2. **Cluster mode** enables horizontal scaling (add nodes without downtime)
3. **Graviton2 processor** cost advantage
4. **Multi-AZ auto-failover** (each shard has primary + replica)
5. **Easy upgrade** to cache.t4g.medium at 50k DAU

### 3.2 Cluster Configuration

```yaml
Configuration:
  Cluster Name: truematch-redis-cluster
  Engine Version: 7.0 (latest stable)
  Node Type: cache.t4g.small
  
  Cluster Composition:
    Shards: 3
    Nodes per Shard: 2 (primary + replica)
    Total Nodes: 6
    Total Memory: 4.1 GB × 3 shards = 12.3 GB
    
  Multi-AZ Setup:
    Enabled: Yes (automatic failover)
    Primary Zone: ap-southeast-1a
    Replica Zones: ap-southeast-1b, ap-southeast-1c (round-robin)
    Failover Time: <30 seconds
    
Subnet Configuration:
  Cache Subnet Group: truematch-redis-subnet-group
  Subnets:
    - 10.0.21.0/24 (ap-southeast-1a)
    - 10.0.22.0/24 (ap-southeast-1b)
    - 10.0.23.0/24 (ap-southeast-1c)
  
  Availability:
    - Node failure: Auto-failover to replica
    - Shard failure: Data available on other shards
    - AZ failure: Replicas in other AZs take over
    - Overall availability: 99.95%
```

### 3.3 Memory Usage Strategy

**For 10,000 DAU:**
```
Session Cache:           ~8 MB
  - 10,000 users × 800 bytes/session = 8 MB

Request Cache:           ~500 MB
  - API responses (top 100 endpoints cached)
  - TTL: 5 minutes
  - Hit ratio target: 60%
  - Saves ~300ms per cached request

Rate Limiting:           ~50 MB
  - Redis Streams for rate limit tracking
  - Per-IP request counters
  - Sliding window (60 seconds)

Task Queue:              ~200 MB
  - Celery task results (temporary)
  - TTL: 30 minutes
  - 100 concurrent tasks × 2MB = 200MB

Database Query Cache:    ~100 MB
  - Top 50 queries
  - TTL: 10 minutes
  - Invalidated on DB write

Locks/Mutexes:           ~50 MB
  - Distributed locks for job processing
  - TTL: 5 minutes
────────────────────────
Total Memory Required:   ~900 MB
Allocated:              4,100 MB (cluster mode: 1,370 × 3)
Utilization:            ~22%
Headroom for Growth:    78% (can 4x traffic with same cluster)
```

### 3.4 Security Configuration

```yaml
Encryption:
  At-Rest:
    Enabled: Yes (AWS KMS)
    Key: Customer managed (shared with RDS)
    Automatic rotation: Annual
    
  In-Transit:
    TLS: Enabled (mandatory)
    Port: 6379 (standard)
    Certificates: AWS managed
    Protocol: RESP3 (with TLS)

Authentication:
  Method: AUTH token + username
  Token Storage: AWS Secrets Manager
  Rotation: Every 90 days
  
  Username: "default" (built-in)
  Password: 32-character random (managed by AWS)
  
  Alternative (IAM Auth - Redis 6.0+):
    - Not available in Redis 7.0 ElastiCache yet
    - Fall back to managed password rotation

Access Control:
  Network: VPC only
  Security Group: truematch-redis-sg
  Allowed IPs: 10.0.11.0/24, 10.0.12.0/24, 10.0.13.0/24 (EKS)
  
Audit Logging:
  Enabled: SlowLog (commands > 1000 microseconds)
  Destination: CloudWatch Logs
  Format: Command, duration, keys accessed
  Retention: 7 days
```

### 3.5 Backup & Recovery

```yaml
Automated Snapshots:
  Frequency: Daily
  Time Window: 04:00-05:00 UTC+8 (after DB backup)
  Retention: 7 days
  Location: S3 (encrypted)
  Size per snapshot: ~200-300 MB
  
Snapshot Restoration:
  Time: 5-10 minutes (new cluster)
  Availability: During restore (use replica first for test)
  Data Loss: None (point-in-time available)

Manual Snapshots:
  Frequency: Before major deployments
  Retention: 30 days
  Naming: truematch-redis-<date>-<version>
  
Point-in-Time Recovery:
  Not supported (use snapshots)
  Workaround: Frequent snapshots + application-level recovery
```

### 3.6 Parameter Configuration

```yaml
Cluster Parameter Group: truematch-redis-params

Key Settings:
  maxmemory-policy: "allkeys-lru"
    - Evict least recently used keys when full
    - Alternative: "volatile-lru" (only expire time-set keys)
    
  timeout: "300"
    - Close idle connections after 5 minutes
    - Prevents connection exhaustion
    
  tcp-keepalive: "60"
    - Send keepalive after 60 seconds
    - Prevents NAT timeout (default: 300)
    
  slowlog-log-slower-than: "1000"
    - Log commands slower than 1ms
    - Helps identify slow operations
    
  slowlog-max-len: "128"
    - Keep last 128 slow log entries
    - Use for performance optimization

Replication Settings:
  Cluster: Enabled (automatic replication per shard)
  Replica Read: Enabled (optional, for analytics)
    - Replicas can handle read-only commands
    - Reduces primary load
    - Suitable for high-read workloads
```

### 3.7 Monitoring & Alerts

```yaml
CloudWatch Metrics:
  - CPUUtilization (target: <30%)
  - DatabaseMemoryUsagePercentage (target: <80%)
  - NetworkBytesIn / NetworkBytesOut
  - EngineCPUUtilization
  - EvictionsPrimary (target: 0)
  - ReplicationLag (target: <100ms)
  - CommandLatency

Alarms:
  1. Memory Utilization > 80% → Scale up (add shard)
  2. Evictions > 0 → Immediate alert (data loss risk)
  3. CPU > 70% for 5 min → Investigate hot key
  4. Replication lag > 500ms → Check network
  5. Failed connections > 10 → Check security group

Custom Metrics (from application):
  - Cache hit ratio (target: 60%)
  - Session timeout rate
  - Celery task completion time
  - Rate limit rejections

Logging:
  Slow Log: /aws/elasticache/truematch-redis/slow-log
  Retention: 7 days
  Analysis: Weekly review for optimization
```

### 3.8 Cost Estimation (ElastiCache)

```
Monthly Cost Breakdown:

Cluster Mode (3 shards, 2 nodes each):
  6 × cache.t4g.small nodes           USD 72.00 ($12/mo × 6)
  
Data Transfer:
  Intra-AZ (free):                    USD 0.00
  Inter-AZ:                           USD 2.00
  
Backup Storage:
  S3 storage (7 snapshots):          USD 5.00
  
Monitoring:
  CloudWatch Logs:                    USD 1.00
────────────────────────────────────────────
TOTAL ElastiCache Monthly:            USD 80.00

Annual Cost (Year 1):                 USD 960

Scaling Path (10k→100k DAU):
- Month 1-12:  3 shards × 2 nodes (USD 80/mo)
- Month 13+:   6 shards × 2 nodes (USD 160/mo)
- At 100k DAU: 12 shards × 2 nodes (USD 320/mo)
```

---

## 4. EKS Kubernetes Cluster Configuration

### 4.1 Cluster Specifications

```yaml
Cluster Details:
  Name: truematch-eks-cluster
  Kubernetes Version: 1.29 (latest stable, released Dec 2023)
  Region: ap-southeast-1
  Subnets: EKS node subnets (10.0.11.0/24, 10.0.12.0/24, 10.0.13.0/24)
  
  API Endpoint: Public (with security group restrictions)
  Logging:
    Enabled for:
      - Cluster API calls
      - Audit logs
      - Authenticator logs
    Destination: CloudWatch Logs
    Retention: 30 days
  
  Encryption:
  - Secrets encryption: AWS KMS customer-managed key
  - ETCD encryption: AWS managed (included)
  
  RBAC:
    Enabled: Yes (built-in)
    Default SA: truematch namespace
    Role bindings: Per application module
```

### 4.2 Node Group Configuration

**Primary Node Group: truematch-node-group-1**

```yaml
Instance Configuration:
  Instance Type: t4g.large (recommended for 10k DAU)
  
  Specifications:
    vCPU: 2
    Memory: 8 GB
    Network: 5 Gbps
    Processor: Graviton2 (ARM64)
    EBS Volume: 100 GB gp3
  
  Cost per month: ~$45/instance

Node Count:
  Desired: 3 nodes
  Min: 3 nodes (maintain service availability)
  Max: 10 nodes (auto-scaling limit)
  
  Placement:
    - 1 node in ap-southeast-1a (10.0.11.0/24)
    - 1 node in ap-southeast-1b (10.0.12.0/24)
    - 1 node in ap-southeast-1c (10.0.13.0/24)
  
  Rationale for 3 nodes:
    - Kubernetes requires minimum 3 for consensus
    - High availability across 3 AZs
    - Sufficient capacity for 10k DAU
    - Allows rolling updates without downtime
    - Cost: USD 135/month (3 × USD 45)

Capacity:
  Total CPU: 6 vCPU (6000 millicores)
  Total Memory: 24 GB
  
  Reserved for System Pods:
    - eks.amazonaws.com/cluster-name: truematch-eks-cluster
    - eks.amazonaws.com/nodegroup: truematch-node-group-1
    - Reserved: ~1 vCPU + 2 GB RAM per node
  
  Available for Applications:
    - CPU: 5 vCPU (~3 large FastAPI pods per node)
    - Memory: 18 GB (~3 large pods × 6GB each)
    - Network: 15 Gbps aggregate

OS & Storage:
  AMI: EKS optimized Amazon Linux 2 (ARM64)
  Root Volume: 100 GB gp3
  
  Auto-scaling:
    Enabled: Cluster Autoscaler
    Trigger: Pods pending > 2 minutes
    Scale-down: Nodes empty > 10 minutes
    Max nodes: 10

Security:
  IAM Role: eks-truematch-node-role
  Permissions:
    - EC2: Describe, CreateVolume, AttachVolume, ModifyVolume
    - ECR: GetDownloadUrlForLayer, GetAuthorizationToken
    - CloudWatch: PutMetricData
    - S3: GetObject, ListBucket (for backups)
    - Secrets Manager: GetSecretValue (for credentials)
    - KMS: Decrypt (for encrypted secrets)
  
  Security Group: truematch-eks-sg
  Termination Protection: Enabled (prevent accidental deletion)
  Detailed Monitoring: Enabled
```

### 4.3 Auto-Scaling Strategy

**Horizontal Pod Autoscaler (HPA):**

```yaml
FastAPI Deployment:
  Min Replicas: 2
  Max Replicas: 10
  
  Scaling Metrics:
    - CPU Utilization: 70% (scale up)
    - Memory Utilization: 75% (scale up)
    - Custom: Request count > 1000 req/sec (scale up)
    
  Scale-up Behavior:
    - Delay: 0 seconds
    - Increment: 50% (add min(1, 50% of current))
  
  Scale-down Behavior:
    - Delay: 300 seconds (5 minutes stabilization)
    - Decrement: 10% (remove min(1, 10% of current))
  
  Pod Disruption Budget:
    Min Available: 1 (never drain all pods)
    Enables safe rolling updates

Celery Worker Deployment:
  Min Replicas: 1
  Max Replicas: 5
  
  Scaling Metric:
    - Queue depth (messages in Redis Streams)
    - Target: 50 messages per worker
  
  Purpose:
    - Handle batch jobs without blocking API
    - Scale with task load

Job Definition (Batch Processing):
  Max Parallelism: 3
  Backoff Limit: 3
  Completion: 1 job must complete
  Retention: Delete after 30 days
```

**Cluster Autoscaler (Node-level):**

```yaml
Configuration:
  Enabled: Yes (add nodes when pods can't schedule)
  Skip-nodes-with-local-storage: False
  Scale-down-enabled: Yes
  
  Scaling Behavior:
    Scale-up: Immediately (pending pods wait)
    Scale-down: After 10 minutes (stability)
  
  Metrics:
    - Nodes at max capacity: Scale up
    - All nodes <30% CPU: Scale down
    
  Node Lifecycle:
    1. Pod creates but can't schedule (no capacity)
    2. Cluster Autoscaler detects pending pod
    3. New node launched (1-2 minutes)
    4. Pod scheduled to new node
    5. Application handles graceful startup
```

### 4.4 Container Configuration

**Deployment Resources:**

```yaml
FastAPI Container:
  Image: 525125475338.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-api:latest
  
  Resource Requests:
    CPU: 500m (0.5 vCPU)
    Memory: 512 Mi
    Ephemeral Storage: 1 Gi
  
  Resource Limits:
    CPU: 1000m (hard limit)
    Memory: 1024 Mi (OOMKilled if exceeded)
    Ephemeral Storage: 2 Gi
  
  Rationale:
    - FastAPI ~300-400MB base
    - Request handling adds ~100-200MB
    - Limits prevent resource runaway
    - 3 pods per node: 1.5 CPU + 1.5GB RAM

Celery Worker Container:
  Image: truematch-worker:latest
  
  Resource Requests:
    CPU: 300m
    Memory: 256 Mi
  
  Resource Limits:
    CPU: 500m
    Memory: 512 Mi
  
  Rationale:
    - Lightweight worker process
    - Most work happens in task (separate container)
    - 5 workers per node: 1.5 CPU + 1.25GB RAM

Task Container (Batch Processing):
  Image: truematch-task-runner:latest
  
  Resource Requests:
    CPU: 1000m
    Memory: 2048 Mi
  
  Resource Limits:
    CPU: 2000m
    Memory: 3000 Mi
  
  Rationale:
    - Heavy computation (ML/data processing)
    - Usually runs 1-2 concurrent tasks
    - Can exceed normal pod limits temporarily
```

### 4.5 Deployment Patterns

**Canary Deployment (for API updates):**

```yaml
Strategy:
  Type: Canary
  Canary: 
    Weight: 10% (send 10% traffic to new version)
    Duration: 5 minutes
  
  Process:
    1. Deploy new version to 1 pod (10% traffic)
    2. Monitor error rate, latency for 5 min
    3. If OK: Canary weight 50% (2 pods)
    4. If OK: Canary weight 100% (complete rollout)
    5. If error: Automatic rollback to previous
  
  Metric Thresholds:
    - Error rate increase: >2% → Rollback
    - Latency increase: >10% → Rollback
    - Pod restart: >1 → Rollback

Rolling Update (for worker updates):
  Max Surge: 25% (add 1 pod, continue serving)
  Max Unavailable: 0 (never drop below min replicas)
  Progress Deadline: 10 minutes
  Revision History: 10 (keep 10 old versions for quick rollback)
```

**Blue/Green Deployment (for major versions):**

```yaml
Process:
  1. Deploy new version alongside old (Blue=old, Green=new)
  2. Run smoke tests on Green
  3. Switch traffic: ALB target group → Green
  4. Monitor for 15 minutes
  5. If OK: Delete Blue, keep Green
  6. If error: Switch traffic back to Blue
  
  Benefits:
    - Zero downtime
    - Full traffic on new version (immediate feedback)
    - Simple rollback (switch ALB back to Blue)
  
  Cost:
    - Temporary 2x resource usage during switch
    - 15-30 minutes duration
    - Acceptable trade-off for major updates
```

### 4.6 Networking & Service Configuration

**Service Configuration:**

```yaml
FastAPI Service:
  Type: ClusterIP (not LoadBalancer)
  Port: 80
  TargetPort: 8000
  
  Selector:
    app: truematch-api
    version: v1
  
  Session Affinity: None (stateless)
  Service Discovery: Kubernetes DNS
  
Celery Service:
  Type: ClusterIP (internal only)
  Port: 5555 (Flower monitoring dashboard)
  
  Use: Internal monitoring, accessed via port-forward
  Not exposed to internet

Ingress Configuration:
  Controller: AWS ALB
  
  Rules:
    - Host: api.truematch.io
      Path: /
      Backend: FastAPI service (80)
    
    - Host: api-internal.truematch.io
      Path: /health
      Backend: FastAPI service (80)
  
  TLS:
    Enabled: Yes
    Certificate: ACM (*.truematch.io)
    Redirect HTTP → HTTPS: Yes
```

**Network Policies:**

```yaml
NetworkPolicy: Allow-Ingress-From-ALB
  Ingress:
    - From: Pod with label lb=aws-alb
      Port: 8000
  Egress:
    - To: pods with label role=database (RDS)
      Port: 5432
    - To: pods with label role=cache (Redis)
      Port: 6379
    - To: 0.0.0.0/0 (external APIs)
      Port: 443

NetworkPolicy: Deny-All-Default
  Ingress: None (deny by default)
  Egress: None (deny by default)
  Exception: Allow only required paths above

Benefits:
  - Prevent lateral movement (pod-to-pod attacks)
  - Reduce blast radius of compromised container
  - Comply with security best practices
  - Low performance impact
```

### 4.7 Cost Estimation (EKS)

```
Monthly Cost Breakdown:

EKS Cluster Control Plane:
  Cluster management:                 USD 73.00
  Logging (CloudWatch):               USD 5.00
  
On-Demand Nodes (3 × t4g.large):
  Compute (3 nodes × $45):           USD 135.00
  EBS storage (300 GB gp3):          USD 30.00
  Data transfer:                      USD 5.00

Load Balancer (ALB):
  Monthly charge:                    USD 16.50
  LCU charges (processed):           USD 5.00

Auto-scaling & Monitoring:
  Cluster Autoscaler:                USD 0.00 (built-in)
  CloudWatch Metrics:                USD 3.00
  
Container Registry (ECR):            USD 5.00 (separate)
────────────────────────────────────────────
TOTAL EKS Monthly:                   USD 277.50

Annual Cost (Year 1):                USD 3,330

Scaling Path (10k→100k DAU):
- Month 1-6:   3 nodes (USD 277/mo)
- Month 7-12:  5 nodes (USD 415/mo)
- Year 2:      5-7 nodes (USD 415-553/mo)
- At 100k DAU: 10+ nodes (USD 730+/mo)
```

---

## 5. Container Registry (ECR) Configuration

### 5.1 Repository Setup

```yaml
Repository Name: truematch-api

Image URI Format: 
  525125475338.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-api:<tag>

Scanning:
  Enabled: Yes (basic scanning on push)
  
  Scan Results:
    - High severity: Block image from EKS
    - Medium: Log but allow (review weekly)
    - Low: Log only
  
  Tool: Amazon ECR Inspector (free)
  
Encryption:
  Type: AWS KMS (customer managed)
  Key: Shared with other secrets
  Cost: Included in KMS key cost

Image Retention Policy:

  Rule 1: Production Images
    Filters:
      - Tags: v*, latest, stable
    Retention:
      - Keep: 30 images
      - Expire: Older versions
    Purpose: Production rollback capability
  
  Rule 2: Development Images
    Filters:
      - Tags: dev-*, feature-*
    Retention:
      - Keep: 5 images
      - Expire after: 7 days
    Purpose: Save space, allow testing
  
  Rule 3: Build Cache
    Filters:
      - Tags: build-*, cache-*
    Retention:
      - Keep: 2 images
      - Expire after: 3 days
    Purpose: Speed up CI/CD, save cost

Image Size Targets:
  FastAPI Image: 500-800 MB
    - Base: python:3.11-slim-bookworm (150 MB)
    - Dependencies: ~200 MB
    - Code: ~50 MB
    - Optimization: Multi-stage build, remove build tools
  
  Worker Image: 600-900 MB
    - Similar to FastAPI + task dependencies
    - Includes Redis CLI, PostgreSQL client
  
  Scanning Impact: <10 seconds per image

Cost Estimation:
  Storage: 10 images × 700 MB = 7 GB
  Cost: $0.10/GB/month = ~$0.70/month
  Data transfer (pulls): Included in EKS data transfer
  Scanning: Free (basic)
```

### 5.2 Push & Pull Configuration

**Tagging Strategy:**

```yaml
Production Builds:
  Tag Format: v<major>.<minor>.<patch>
  Example: v1.2.3
  
  Also tag as: latest, stable, v1.2
  Allows:
    - Patch updates (v1.2.3 → v1.2.4)
    - Minor version rollback (v1.2 to v1.1)
    - Latest stable version lookup
  
  Retain: 30 versions (≈12-18 months of releases)

Staging Builds:
  Tag Format: staging-<date>-<commit-hash>
  Example: staging-20260721-a3c5e9f
  
  Retain: 5 builds (≈1 week)

Development Builds:
  Tag Format: dev-<branch-name>-<timestamp>
  Example: dev-feature-auth-20260721-1430
  
  Retain: 2 per branch (for quick testing)

Pull Configuration:
  ImagePullPolicy: IfNotPresent
  - Pull if not present locally
  - Use cache if available
  
  For production: Always pull latest (explicit version tag)
  For canary: Pull with specific version tag
```

### 5.3 Security & Compliance

```yaml
Push Security:
  - Require AWS credentials (IAM role)
  - Only CI/CD pipeline has push permission
  - Audit logging: CloudTrail + ECR logs
  - Scan before push (in CI/CD)

Image Pull:
  - EKS nodes use IAM role (automatic)
  - Role: eks-truematch-node-role
  - Permission: ecr:GetDownloadUrlForLayer, ecr:GetAuthorizationToken
  
  Pull Secrets: Not needed (IAM-based)
  
Vulnerability Scanning:
  - Basic scanning: Free (on push)
  - Enhanced scanning: ECR Enhanced Scanning (paid)
  
  Severity Levels:
    - CRITICAL: Block from production
    - HIGH: Alert, manual review required
    - MEDIUM: Log, patch in next release
    - LOW: Ignore unless requested
  
  Remediation Process:
    1. Scan detects vulnerability
    2. Alert sent to Slack #security
    3. Developer updates dependencies
    4. Rebuild image, re-scan
    5. Once passing: Deploy to staging
    6. Once verified: Deploy to production

Image Signing:
  Not recommended for now
  Use container-native signing in future (v2.0)
  Alternative: GPG signing in metadata
```

---

## 6. Domain & SSL Certificate Configuration

### 6.1 Domain Setup

**Recommended Domain Structure:**

```yaml
Primary Domain: truematch.io (or truematch-ai.io)

Subdomains:
  api.truematch.io
    - Production API endpoint
    - Cloudflare or Route53 + ALB
    
  api-staging.truematch.io
    - Staging API (for testing)
    - Separate ALB or same ALB with different target group
    
  api-internal.truematch.io (optional)
    - Internal monitoring (Flower, Prometheus)
    - Behind VPN or IP whitelist
    - Self-signed certificate OK
    
  status.truematch.io (optional)
    - Uptime status page
    - Hosted on S3 + CloudFront
    
  docs.truematch.io
    - API documentation (Swagger UI)
    - Public or authentication-required

DNS Provider Recommendation:
  Option 1: AWS Route53
    - Cost: $0.50/month per hosted zone + $0.40 per million queries
    - Advantage: Integrated with AWS, automatic failover
    - Recommended for this architecture
  
  Option 2: Cloudflare (free tier available)
    - Cost: Free (with 20 min TTL) or paid plans
    - Advantage: DDoS protection, global CDN
    - Disadvantage: Additional service to manage

Root Domain (truematch.io):
  - Subdomain redirect: https://api.truematch.io
  - Or: Host landing page on S3 + CloudFront
  - Rationale: CNAME only available for subdomains
```

### 6.2 Route53 Configuration

```yaml
Hosted Zone: truematch.io
  Type: Public hosted zone
  Name servers: AWS (default)
  Registrar: Domain registrant's choice (GoDaddy, Namecheap, etc.)
  Update registrar NS records to Route53 NS servers

Records:

  1. A Record (api.truematch.io):
     Type: A (IPv4)
     Value: ALB DNS name (alias to ALB)
     Alias: Yes (AWS specific, no charge)
     Routing Policy: Simple
     Example: alias to "truematch-alb-1234567.ap-southeast-1.elb.amazonaws.com"
  
  2. AAAA Record (api.truematch.io):
     Type: AAAA (IPv6)
     Value: ALB IPv6 DNS name
     Alias: Yes
     Prerequisite: ALB must support IPv6
  
  3. Health Check (optional):
     Type: HTTP health check
     Target: api.truematch.io/health
     Interval: 30 seconds
     Threshold: 3 consecutive failures
     Alarm: CloudWatch SNS notification
  
  4. MX Records (email):
     Priority 10: mail1.truematch.io (or SendGrid, Mailgun)
     Priority 20: mail2.truematch.io (backup)
     Rationale: Send transactional emails
  
  5. TXT Records (verification):
     SPF: v=spf1 include:sendgrid.net ~all
     DKIM: Generated by SendGrid/Mailgun
     DMARC: v=DMARC1; p=quarantine; rua=mailto:...
     Verification: AWS SES verification (if applicable)

Cost Estimation:
  Hosted zone: $0.50/month
  Queries: ~1-10 million/month = ~$0.40-4/month
  Health checks: $0.50/month (if enabled)
  Total: ~$1.50-2/month
```

### 6.3 SSL Certificate Configuration

**ACM (AWS Certificate Manager):**

```yaml
Certificate Details:
  Domain: *.truematch.io (wildcard, covers all subdomains)
  
  Additional Domains:
    - truematch.io (root)
    - api.truematch.io (explicit)
  
  Validation Method: DNS (automatic)
    - ACM creates Route53 CNAME record
    - Validates within minutes
    - Automatic renewal (no manual action)
  
  Provider: AWS (managed certificate)
  Cost: Free (one of AWS's free services)
  
  Renewal: Automatic (60 days before expiration)
  Notification: Email 45 days before expiration (as backup)

Certificate Binding:
  ALB Listener:
    Port: 443 (HTTPS)
    Protocol: TLS 1.2, TLS 1.3
    Certificate: *.truematch.io
    Security Policy: ELBSecurityPolicy-TLS-1-2-2017-01 (recommended)
  
  HTTP Listener:
    Port: 80 (HTTP)
    Redirect: 301 permanent redirect to HTTPS (port 443)
    
Certificate Features:
  HSTS (HTTP Strict Transport Security):
    Enabled: Yes
    Max-age: 31536000 (1 year)
    Include subdomains: Yes
    Preload: Yes
    Effect: Browsers enforce HTTPS for all subdomains
  
  Certificate Pinning: Not recommended (adds complexity)
  
  Cipher Suites (TLS 1.3 preferred):
    - TLS_AES_128_GCM_SHA256
    - TLS_AES_256_GCM_SHA384
    - CHACHA20_POLY1305_SHA256
    
  Older Ciphers: Disabled (TLS 1.0, 1.1 not supported)

Multi-region Considerations:
  Certificate is regional (ap-southeast-1)
  For multi-region:
    - Replicate certificate to other region
    - Or use CloudFront (requires us-east-1 certificate)
    - Not required for now (Singapore region only)
```

---

## 7. Monitoring & Logging Configuration

### 7.1 CloudWatch Namespaces & Dashboards

**Main Dashboard: truematch-api-overview**

```yaml
Metrics Displayed:

  1. Application Layer:
     - API request rate (requests/sec)
     - Error rate (% of requests)
     - Latency (p50, p95, p99)
     - Active connections (to ALB)
  
  2. Compute Layer:
     - EKS node CPU utilization (avg)
     - EKS node memory utilization (avg)
     - Pod count (running/pending)
     - Node count (desired/actual)
  
  3. Database Layer:
     - RDS CPU utilization
     - RDS connections (active)
     - RDS latency (read/write)
     - Storage used (GB)
  
  4. Cache Layer:
     - Redis CPU utilization
     - Redis memory used (%)
     - Cache evictions (per minute)
     - Connection count
  
  5. Business Metrics:
     - Active users (from session cache)
     - Tasks completed (from Celery)
     - API endpoint response times (top 10)

Refresh Interval: 1 minute
Time Range: Last 6 hours + 24 hours overlay
Export: PNG export for incidents, Slack integration
```

### 7.2 Log Groups & Retention

```yaml
Log Groups:

  1. Application Logs:
     Name: /aws/truematch/api
     Retention: 30 days
     Format: JSON (structured logging)
     
     Fields:
       - timestamp (ISO 8601)
       - level (INFO, WARNING, ERROR, DEBUG)
       - module (auth, payment, search, etc.)
       - user_id (anonymized)
       - request_id (correlation ID)
       - response_time_ms
       - endpoint
       - status_code
       - error_message (if error)
  
  2. Worker Logs:
     Name: /aws/truematch/worker
     Retention: 14 days
     
     Fields:
       - task_name
       - task_id
       - status (started, completed, failed)
       - duration_seconds
       - queue_depth
       - result (success/error)
  
  3. EKS Cluster Logs:
     Name: /aws/eks/truematch-eks-cluster
     Retention: 30 days
     
     Log Types:
       - api: Kubernetes API calls
       - audit: Authentication/authorization
       - authenticator: IAM authentication
       - controllerManager: Deployment logic
       - scheduler: Pod scheduling events
  
  4. RDS Logs:
     Name: /aws/rds/database/truematch-db
     Retention: 7 days
     
     Log Types:
       - error: Database errors
       - general: All queries (optional)
       - slowquery: Queries > 1 second
       - audit: DDL statements
  
  5. ALB Logs:
     Name: /aws/elasticloadbalancing/app/truematch-alb
     Retention: 30 days
     
     Fields:
       - timestamp
       - elb (load balancer name)
       - client_ip:client_port
       - target_ip:target_port
       - request_processing_time
       - target_processing_time
       - response_processing_time
       - elb_status_code
       - target_status_code
       - received_bytes
       - sent_bytes
       - http_request
  
  6. VPC Flow Logs (optional):
     Name: /aws/vpc/truematch-vpc-flows
     Retention: 7 days
     Format: version, account-id, interface-id, srcaddr, dstaddr, srcport, dstport, protocol, packets, bytes, windowstart, windowend, action, log-status
     Use: Network troubleshooting, DDoS detection

Cost Estimation (Logging):
  Ingestion:
    - API logs: ~5-10 GB/day (500 endpoints × 1000+ req/sec)
    - Worker logs: ~1 GB/day
    - EKS logs: ~2 GB/day
    - RDS logs: ~500 MB/day
    - ALB logs: ~3 GB/day
    Total: ~12 GB/day
    
  Cost: $0.50/GB ingested + $0.03/GB stored
    Daily: 12 GB × $0.50 = $6/day
    Monthly: $180 + storage (~$10) = ~$190/month
  
  Optimization: Filter out DEBUG logs, compress older logs
```

### 7.3 Alarms & Alerting

**Critical Alarms (page on-call):**

```yaml
1. API Error Rate Spike:
   Metric: ErrorRate (%)
   Threshold: > 5% for 2 consecutive 1-min periods
   Action: PagerDuty (trigger incident)
   Context: "Check API error logs, database connections"

2. Database Connection Exhaustion:
   Metric: DatabaseConnections
   Threshold: > 450 of 500 max
   Action: PagerDuty + Auto-scaling trigger
   Context: "Check active queries, consider connection pooling"

3. Cache Evictions:
   Metric: EvictionsPrimary
   Threshold: > 0 (any eviction)
   Action: PagerDuty
   Context: "Memory saturation, add shard or increase TTL"

4. Node Unavailable:
   Metric: NodeStatus
   Threshold: Any node down
   Action: PagerDuty
   Context: "Check node logs, replace if hardware failure"

5. Pod CrashLoopBackOff:
   Metric: PodRestartCount
   Threshold: > 5 restarts in 5 minutes
   Action: PagerDuty
   Context: "Check application logs, may indicate bug"

Warning Alarms (email + Slack):
   - CPU > 80%: Scaling may not keep up
   - Memory > 75%: Plan scaling for next day
   - Latency p95 > 1s: Performance degradation
   - Database replication lag > 500ms: Failover risk
   - Certificate expiry < 7 days: Update ACM
   - Free disk space < 10%: Log cleanup needed

Alarm Actions:
   PagerDuty (critical): Immediate notification
   Slack #alerts: Warning logs + context
   Email: Daily summary of warnings
   SNS Topic: Custom integrations (webhooks, etc.)

Alarm Suppressions (prevent alert fatigue):
   - Maintenance windows: Disable alarms 2am-3am daily
   - Scheduled scaling: Suppress CPU alarm during load tests
   - Rollout periods: Suppress latency alarms during canary
```

### 7.4 Custom Metrics

**Application Metrics (via CloudWatch SDK):**

```yaml
Metrics to Publish:

1. Cache Hit Rate:
   Namespace: TrueMatch/Cache
   MetricName: HitRate
   Unit: Percent
   Dimensions:
     - CacheType: Session | Query | Request
   Frequency: Every 1 minute (from application)
   Target: 60% (aim for 60% cache hit rate)

2. Queue Depth:
   Namespace: TrueMatch/Tasks
   MetricName: QueueLength
   Unit: Count
   Dimensions:
     - QueueName: ImportData | ProcessPayment | SendNotification
   Frequency: Every 30 seconds
   Alert: > 1000 items (auto-scale workers)

3. API Endpoint Latency:
   Namespace: TrueMatch/API
   MetricName: EndpointLatency
   Unit: Milliseconds
   Dimensions:
     - Endpoint: /api/users, /api/search, /api/payment, etc.
     - Method: GET, POST, PUT, DELETE
   Frequency: Every request
   Extract: p50, p95, p99 from application

4. Business Events:
   Namespace: TrueMatch/Business
   MetricName: CompletedMatches
   Unit: Count
   Dimensions:
     - MatchType: PerfectMatch | GoodMatch | Candidate
   Frequency: Every match completion
   Use: KPI tracking, dashboard monitoring

5. Database Query Performance:
   Namespace: TrueMatch/Database
   MetricName: QueryLatency
   Unit: Milliseconds
   Dimensions:
     - QueryType: GetUser | SearchMatches | UpdateProfile
   Frequency: Every query
   Alert: p95 > 100ms (index optimization needed)

Implementation:
  Library: boto3 (Python AWS SDK)
  
  Code Example:
    ```python
    import boto3
    cloudwatch = boto3.client('cloudwatch')
    
    cloudwatch.put_metric_data(
        Namespace='TrueMatch/API',
        MetricData=[{
            'MetricName': 'EndpointLatency',
            'Value': response_time_ms,
            'Unit': 'Milliseconds',
            'Timestamp': datetime.utcnow(),
            'Dimensions': [
                {'Name': 'Endpoint', 'Value': '/api/users'},
                {'Name': 'Method', 'Value': 'GET'}
            ]
        }]
    )
    ```

Cost:
  Custom metrics: $0.03 per metric per month
  Expected metrics: ~20 custom metrics
  Monthly: $0.60 (negligible)
```

---

## 8. Cost Analysis & Optimization

### 8.1 Monthly Cost Breakdown (Initial Deployment - 10k DAU)

```
Component                              Monthly Cost
────────────────────────────────────────────────────

VPC & Networking:
  NAT Gateways (2x):                   USD 45.00
  Data transfer (outbound):            USD 15.00
  ────────────────────────────────────────────────
  Subtotal Networking:                 USD 60.00

RDS PostgreSQL:
  Instance (t4g.medium Multi-AZ):      USD 112.00
  Storage (100GB gp3):                 USD 10.00
  Automated backups (14 days):         USD 5.00
  Enhanced monitoring:                 USD 4.00
  RDS Proxy:                           USD 15.00
  Data transfer:                       USD 5.00
  ────────────────────────────────────────────────
  Subtotal RDS:                        USD 151.00

ElastiCache Redis:
  Cluster mode (6 nodes):              USD 72.00
  Backup storage:                      USD 5.00
  Data transfer (inter-AZ):            USD 2.00
  Monitoring:                          USD 1.00
  ────────────────────────────────────────────────
  Subtotal ElastiCache:                USD 80.00

EKS Kubernetes:
  Control plane (cluster mgmt):        USD 73.00
  3x t4g.large nodes:                  USD 135.00
  EBS storage (300GB):                 USD 30.00
  ALB:                                 USD 21.50
  Data transfer:                       USD 5.00
  CloudWatch monitoring:               USD 3.00
  ────────────────────────────────────────────────
  Subtotal EKS:                        USD 267.50

Container Registry & Deployment:
  ECR storage (7GB):                   USD 0.70
  ECR scanning:                        USD 0.00
  ────────────────────────────────────────────────
  Subtotal ECR:                        USD 0.70

DNS & SSL:
  Route53 hosted zone:                 USD 0.50
  Route53 queries:                     USD 1.00
  ACM certificate:                     USD 0.00 (free)
  ────────────────────────────────────────────────
  Subtotal DNS/SSL:                    USD 1.50

Monitoring & Logging:
  CloudWatch logs (12 GB/day):         USD 190.00
  CloudWatch metrics:                  USD 3.00
  CloudWatch dashboards:               USD 0.00 (included)
  SNS (notifications):                 USD 0.50
  ────────────────────────────────────────────────
  Subtotal Monitoring:                 USD 193.50

Security & Compliance:
  KMS key (shared):                    USD 1.00
  Secrets Manager (1 secret):          USD 0.40
  ────────────────────────────────────────────────
  Subtotal Security:                   USD 1.40

Backup & Disaster Recovery:
  S3 storage (RDS + Redis snapshots):  USD 5.00
  ────────────────────────────────────────────────
  Subtotal Backups:                    USD 5.00

════════════════════════════════════════════════
TOTAL MONTHLY (10k DAU):               USD 760.60
════════════════════════════════════════════════

TOTAL ANNUAL (Year 1):                 USD 9,127.20
```

### 8.2 Cost Scaling Analysis

**Scaling Scenarios:**

```yaml
Scenario 1: 10k → 25k DAU (6-month growth)
  Changes:
    - Add 2 more EKS nodes (5 total): +USD 90/month
    - Increase RDS to t4g.large: +USD 112/month
    - Double ElastiCache (6 shards): +USD 72/month
    - Increase logging by 2x: +USD 190/month
  
  New monthly: USD 760 + 464 = USD 1,224/month
  Incremental cost per DAU: USD 0.049/user/month

Scenario 2: 25k → 50k DAU (12-month growth)
  Changes:
    - Add 2 more EKS nodes (7 total): +USD 90/month
    - RDS storage growth (300 GB): +USD 20/month
    - Add 3 more Redis shards (9 total): +USD 108/month
    - Increase logging: +USD 200/month
  
  New monthly: USD 1,224 + 418 = USD 1,642/month
  Incremental cost per DAU: USD 0.033/user/month

Scenario 3: 50k → 100k DAU (18-month growth)
  Changes:
    - Add 5 more EKS nodes (12 total): +USD 225/month
    - RDS storage growth (500 GB): +USD 40/month
    - Add 6 more Redis shards (15 total): +USD 216/month
    - Increase logging: +USD 300/month
  
  New monthly: USD 1,642 + 781 = USD 2,423/month
  Incremental cost per DAU: USD 0.024/user/month

Summary:
  10k DAU:   USD 760/month   = USD 0.076/user/month
  25k DAU:   USD 1,224/month = USD 0.049/user/month
  50k DAU:   USD 1,642/month = USD 0.033/user/month
  100k DAU:  USD 2,423/month = USD 0.024/user/month
```

### 8.3 Cost Optimization Recommendations

**Immediate (No architectural changes):**

```yaml
1. Spot Instances for EKS (saves 70%):
   - Use Spot for batch workers (Celery)
   - Keep on-demand for API pods
   - Interruption rate: ~2-5% in ap-southeast-1
   - Savings: ~USD 30-50/month
   
   Implementation:
     - Create separate node group: spot-workers
     - Instance types: t4g.large, t4g.medium (flexible)
     - Max price: 30% discount from on-demand
     - Pod disruption budget: Allow eviction

2. Reserved Instances (RDS):
   - Commit to 1-year t4g.medium: Save 30%
   - Prepaid: ~USD 2,000 upfront
   - Payback: 18-20 months
   - Savings: USD 30/month
   - Recommendation: Wait 6 months, then buy for t4g.large

3. Compute Savings Plan (EKS):
   - 1-year commitment: Save 20-30%
   - Flexible (can change instance type)
   - Example: 3 nodes × USD 45 = USD 135
   - With savings plan: USD 110/month
   - Savings: USD 25/month

4. S3 Lifecycle for Backups:
   - Move snapshots to Glacier after 30 days
   - Cost: USD 1/GB/month → USD 0.004/GB/month
   - Expected savings: USD 15-20/month

5. CloudWatch Logs Filter & Retention:
   - Skip DEBUG level logs (save 30%)
   - Reduce retention from 30 to 14 days
   - Compress logs after 7 days
   - Savings: USD 50-100/month

Total Immediate Savings: ~USD 120-200/month (16-26%)
```

**Medium-term (2-3 months):**

```yaml
1. CloudFront CDN for Static Assets:
   - Cache static content (dist, assets)
   - Reduce ALB data transfer
   - Improve user latency (Singapore edge)
   - Cost: ~USD 20/month for 1 TB/month transfer
   - Savings: USD 10-15/month (data transfer reduction)

2. NAT Gateway Optimization:
   - Use NAT Instance (EC2) for low-traffic periods
   - NAT Gateway peak hours (3am-8am idle)
   - Cost: t2.micro = USD 10/month
   - Savings: USD 35/month (1 NAT Gateway unused)
   - Trade-off: Manual failover, slightly slower

3. Database Query Optimization:
   - Index optimization (reduce IOPS)
   - Query caching (reduce database load)
   - Savings: USD 20-30/month (smaller instance possible)
   - Effort: 10-20 hours SQL optimization

4. Compress Log Data:
   - JSON compression for CloudWatch Logs
   - Reduce ingestion by 40%
   - Savings: USD 60-80/month
   - Effort: Update logging configuration
```

**Long-term (6+ months):**

```yaml
1. Multi-region Expansion (if needed):
   - Duplicate to ap-south-1 (Mumbai) for SEA growth
   - Data replication cost: ~USD 100/month
   - Separate infrastructure: USD 800/month
   - New region savings: Data transfer reduction
   - Full cost impact: ~USD 1,500-2,000/month for 2 regions

2. Serverless Migration (Lambda + RDS Proxy):
   - Replace EKS with Lambda (pay per execution)
   - Suitable for workloads: APIs with variable load
   - Cost benefit: 30% reduction at 50k+ DAU
   - Effort: Significant refactoring (40-50 hours)
   - Recommendation: Evaluate after 12 months

3. Database Optimization:
   - Switch to Aurora PostgreSQL (auto-scaling)
   - Cost: Similar to RDS at small scale
   - Benefit: Auto-scaling writes (multi-master)
   - Effort: Migration 10-15 hours
   - Payback: At 100k+ DAU (20% savings)
```

### 8.4 Annual Cost Projection

```
Year 1 (10k DAU growth to 50k):
  Q1 (Jan-Mar): USD 760 × 3 months           = USD 2,280
  Q2 (Apr-Jun): USD 1,000 × 3 months         = USD 3,000
  Q3 (Jul-Sep): USD 1,350 × 3 months         = USD 4,050
  Q4 (Oct-Dec): USD 1,650 × 3 months         = USD 4,950
  ─────────────────────────────────────────────────────
  Year 1 Total:                              USD 14,280

Year 2 (50k DAU stable + optimizations):
  Base cost (USD 1,650/month):               USD 19,800
  Spot instances savings:                    (USD 400)
  Reserved instance savings:                 (USD 360)
  Compute savings plan:                      (USD 300)
  Log optimization savings:                  (USD 600)
  ─────────────────────────────────────────────────────
  Year 2 Total (post-optimization):          USD 18,140

Year 3 (100k DAU):
  Projected growth cost:                     USD 29,076
  With full optimizations:                   USD 23,000-25,000
```

---

## 9. Risk Assessment & Mitigation

### 9.1 Identified Risks

**High Priority:**

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| Database connection exhaustion | Service outage | Medium | RDS Proxy (limit connections), monitoring, auto-scaling |
| Data center outage (1 AZ failure) | 30% capacity loss | Low (AWS: 99.99%) | Multi-AZ deployment (standby RDS, Redis replicas) |
| OOM Pod eviction | Request failures | Medium | Memory requests/limits, HPA on memory metric, alerts |
| Cache stampede (all expires simultaneously) | Database overload | Low | Stagger cache expiration, warm-up queries |
| Uncontrolled cost scaling | Budget overrun | Medium | Alerts at USD 1000/month, cap spot instances, reserve capacity |

**Medium Priority:**

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| Slow queries performance | Increased latency | Medium | Query optimization, index strategy, slow log monitoring |
| Network saturation | Latency increase | Low | Monitor bandwidth, use VPC endpoints for AWS services |
| Key rotation failure (KMS) | Service disruption | Low | Automated rotation, test restore procedures |
| SSL certificate expiration | HTTPS failure | Very Low | Auto-renewal, 90-day alert |
| Celery task loss | Incomplete jobs | Low | Redis persistence + RDB snapshots, dead-letter queues |

### 9.2 Disaster Recovery Plan

**RTO (Recovery Time Objective): < 30 minutes**
**RPO (Recovery Point Objective): < 5 minutes**

```yaml
Scenario 1: Single RDS node failure
  - Failover time: <2 minutes (automatic)
  - Data loss: None (synchronous replication)
  - Action: Automatic, no manual intervention
  - Verify: Check CloudWatch metrics after failover

Scenario 2: Full AZ failure (e.g., ap-southeast-1a)
  - Impact: All pods in AZ-a terminate
  - Recovery:
    1. Cluster autoscaler adds nodes in AZ-b/c (1-2 min)
    2. Pods reschedule to new nodes (30 sec)
    3. RDS standby (in AZ-b) becomes primary (2 min)
    4. Redis replicas take over (30 sec)
  - Total RTO: 5 minutes
  - Data loss: None

Scenario 3: VPC network isolation
  - Impact: Pods can't reach database/cache
  - Detection: CloudWatch alarms (DB connection failures)
  - Recovery:
    1. Check security groups (common cause)
    2. Verify route tables
    3. Check NACLs (if applicable)
    4. Restart affected pods (force reschedule)
  - Total RTO: 10-15 minutes

Scenario 4: Data corruption (database)
  - Detection: Application errors, constraint violations
  - Recovery:
    1. Stop all writes (take API offline)
    2. Restore from backup (select PITR time)
    3. Replay logs from backup to incident time
    4. Verify data integrity on staging
    5. Switch to restored database
  - Total RTO: 30-45 minutes
  - Data loss: Up to 5 minutes (PITR granularity)

Backup & Restore Testing:
  - Restore RDS backup to staging: Weekly
  - Restore Redis snapshot: Weekly
  - Verify data integrity: Manual checks
  - Document time taken: Track for SLO
  - Quarterly: Full disaster recovery drill
```

---

## 10. Implementation Timeline

### Phase 1: Foundation (Week 1-2)

- [ ] Create VPC with subnets and route tables
- [ ] Set up NAT gateways and Internet gateway
- [ ] Configure security groups
- [ ] Create KMS key for encryption
- [ ] Register domain and set up Route53

**Estimated effort:** 40 hours  
**Cost incurred:** USD 100 (VPC endpoints, Route53)

### Phase 2: Data Layer (Week 2-3)

- [ ] Create RDS PostgreSQL instance (t4g.medium Multi-AZ)
- [ ] Configure parameter groups and backups
- [ ] Set up RDS Proxy for connection pooling
- [ ] Create ElastiCache Redis cluster (3 shards)
- [ ] Verify network connectivity

**Estimated effort:** 30 hours  
**Cost incurred:** USD 250 (RDS + ElastiCache)

### Phase 3: Container Registry (Week 3)

- [ ] Create ECR repository
- [ ] Configure image retention policies
- [ ] Set up image scanning
- [ ] Build and push initial images

**Estimated effort:** 10 hours  
**Cost incurred:** USD 10 (ECR storage)

### Phase 4: EKS Cluster (Week 3-4)

- [ ] Create EKS cluster (1.29 stable)
- [ ] Add node groups (3x t4g.large)
- [ ] Install CNI, CoreDNS, kube-proxy
- [ ] Configure IAM roles for pods
- [ ] Install Cluster Autoscaler

**Estimated effort:** 50 hours  
**Cost incurred:** USD 400 (EKS cluster + nodes)

### Phase 5: Networking & Ingress (Week 4)

- [ ] Create Application Load Balancer
- [ ] Configure listener rules (HTTP→HTTPS redirect)
- [ ] Set up ACM certificate (*.truematch.io)
- [ ] Deploy Ingress controller
- [ ] Configure DNS alias records

**Estimated effort:** 25 hours  
**Cost incurred:** USD 50 (ALB)

### Phase 6: Application Deployment (Week 4-5)

- [ ] Containerize FastAPI application
- [ ] Deploy to EKS (rolling update)
- [ ] Configure health checks
- [ ] Set up horizontal pod autoscaling
- [ ] Run smoke tests

**Estimated effort:** 40 hours  
**Cost incurred:** USD 100 (compute)

### Phase 7: Monitoring & Logging (Week 5)

- [ ] Create CloudWatch log groups
- [ ] Configure application logging (JSON format)
- [ ] Set up dashboards
- [ ] Create critical alarms
- [ ] Integrate PagerDuty/Slack

**Estimated effort:** 30 hours  
**Cost incurred:** USD 100 (CloudWatch)

### Phase 8: Security & Hardening (Week 5-6)

- [ ] Enable VPC Flow Logs
- [ ] Configure network policies
- [ ] Set up secrets rotation
- [ ] Enable RDS encryption
- [ ] Run security audit

**Estimated effort:** 20 hours  
**Cost incurred:** USD 50 (minimal)

### Phase 9: Backup & DR Testing (Week 6)

- [ ] Test RDS backup/restore
- [ ] Test Redis snapshot recovery
- [ ] Document runbooks
- [ ] Perform DR drill
- [ ] Get team sign-off

**Estimated effort:** 25 hours  
**Cost incurred:** USD 50 (S3 storage)

**Total Implementation Effort:** 270 hours (~6-7 weeks for 1 engineer)  
**Total Phase Cost:** USD 1,050-1,200

---

## 11. Go-Live Checklist

**Pre-Production:**
- [ ] Load test to 10,000 DAU (measure resource utilization)
- [ ] Run 24-hour soak test (identify memory leaks)
- [ ] Verify auto-scaling behavior
- [ ] Confirm all alarms are firing correctly
- [ ] Test failover procedures

**Security:**
- [ ] Penetration test (optional, for compliance)
- [ ] Verify encryption at rest and in transit
- [ ] Confirm IAM roles follow least privilege
- [ ] Review security group rules
- [ ] Audit CloudTrail logs

**Operations:**
- [ ] Document runbooks (incidents, escalation)
- [ ] Create on-call rotation
- [ ] Set up alerting to team Slack
- [ ] Define SLO/SLA targets (99.95% availability)
- [ ] Schedule weekly reviews

**Cutover:**
- [ ] DNS migration (update registrar NS records)
- [ ] Monitor for first 24 hours
- [ ] Prepare rollback plan
- [ ] Track metrics vs. baseline

---

## 12. Conclusion & Next Steps

### Recommended Immediate Actions

1. **Approve Architecture** (1 day)
   - Share this document with team
   - Gather feedback on trade-offs
   - Approve component selections

2. **Prepare AWS Account** (1 day)
   - Enable MFA for root account
   - Create IAM users with proper permissions
   - Enable CloudTrail for audit logging
   - Set up billing alerts (USD 1000/month threshold)

3. **Create Infrastructure-as-Code** (1 week)
   - Use Terraform or CloudFormation
   - Automate all manual steps
   - Version control (git)
   - Document assumptions

4. **Build Deployment Pipeline** (1 week)
   - CI/CD (GitHub Actions or GitLab)
   - Automated image builds
   - Integration tests
   - Automated canary deployments

5. **Load Test & Optimize** (2 weeks)
   - Simulate 10k DAU
   - Identify bottlenecks
   - Optimize queries and caches
   - Right-size instances

**Timeline to Production:** 6-7 weeks  
**Cost to Deployment:** USD 1,200 + ongoing USD 760/month  
**Scaling Capacity:** 10x (to 100k DAU) without re-architecture

---

**Document prepared for:** TrueMatch AI  
**Account ID:** 525125475338  
**Region:** ap-southeast-1 (Singapore)  
**Approved by:** [To be signed off]  
**Last updated:** July 2026  
