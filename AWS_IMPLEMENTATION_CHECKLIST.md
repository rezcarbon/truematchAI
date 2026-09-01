# AWS Implementation Checklist: TrueMatch AI
## Step-by-Step Production Deployment Guide

**Account ID:** 525125475338  
**Region:** ap-southeast-1 (Singapore)  
**Target Completion:** 6-7 weeks  

---

## Pre-Implementation Setup

### Prerequisites Verification

- [ ] **AWS Account Access**
  - [ ] Root account created with MFA enabled
  - [ ] IAM user created for deployment (truematch-admin)
  - [ ] Programmatic access keys generated (saved securely)
  - [ ] CloudTrail enabled for audit logging
  
- [ ] **Domain Registration**
  - [ ] Domain registered (truematch.io or similar)
  - [ ] Domain ownership verified
  - [ ] Access to domain registrar (GoDaddy, Namecheap, Route53)
  
- [ ] **Local Development Environment**
  - [ ] AWS CLI installed (v2.x+)
  - [ ] Configured AWS credentials: `aws configure`
  - [ ] Tested: `aws sts get-caller-identity`
  - [ ] Terraform or CloudFormation installed (optional but recommended)
  - [ ] kubectl installed (v1.29+)
  - [ ] Docker installed (for local builds)
  
- [ ] **Team Preparation**
  - [ ] Team member assigned as AWS architect
  - [ ] Backup contact defined (secondary admin)
  - [ ] Escalation contacts documented
  - [ ] Slack/PagerDuty workspace prepared for alerts

---

## Phase 1: VPC & Networking Foundation (Days 1-3)

### Step 1.1: Create VPC

```bash
# Using AWS CLI
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=truematch-vpc},{Key=Environment,Value=production}]' \
  --region ap-southeast-1
```

- [ ] VPC created with CIDR 10.0.0.0/16
- [ ] Verify in AWS Console: VPC → Your VPCs
- [ ] Note VPC ID: vpc-xxxxxxxxx
- [ ] Enable DNS hostnames: Actions → Edit VPC settings
- [ ] Enable DNS resolution: Actions → Edit VPC settings

**Validation:**
```bash
aws ec2 describe-vpcs --filters "Name=cidr,Values=10.0.0.0/16" --region ap-southeast-1
```

### Step 1.2: Create Subnets

**Public Subnets (for NAT Gateway and ALB):**

```bash
# AZ-a public subnet
aws ec2 create-subnet \
  --vpc-id vpc-xxxxxxxxx \
  --cidr-block 10.0.1.0/24 \
  --availability-zone ap-southeast-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=truematch-public-1a}]' \
  --region ap-southeast-1

# AZ-b public subnet
aws ec2 create-subnet \
  --vpc-id vpc-xxxxxxxxx \
  --cidr-block 10.0.2.0/24 \
  --availability-zone ap-southeast-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=truematch-public-1b}]' \
  --region ap-southeast-1
```

**Private Subnets - EKS (for Kubernetes nodes):**

```bash
# AZ-a EKS subnet
aws ec2 create-subnet \
  --vpc-id vpc-xxxxxxxxx \
  --cidr-block 10.0.11.0/24 \
  --availability-zone ap-southeast-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=truematch-private-eks-1a}]' \
  --region ap-southeast-1

# Repeat for AZ-b (10.0.12.0/24) and AZ-c (10.0.13.0/24)
```

**Private Subnets - Database (for RDS/ElastiCache):**

```bash
# AZ-a DB subnet
aws ec2 create-subnet \
  --vpc-id vpc-xxxxxxxxx \
  --cidr-block 10.0.21.0/24 \
  --availability-zone ap-southeast-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=truematch-private-db-1a}]' \
  --region ap-southeast-1

# Repeat for AZ-b (10.0.22.0/24) and AZ-c (10.0.23.0/24)
```

- [ ] 2 public subnets created (1a, 1b)
- [ ] 3 EKS private subnets created (1a, 1b, 1c)
- [ ] 3 DB private subnets created (1a, 1b, 1c)
- [ ] All subnets have required tags

**Validation:**
```bash
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-xxxxxxxxx" --region ap-southeast-1
```

### Step 1.3: Create Internet Gateway

```bash
# Create Internet Gateway
aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=truematch-igw}]' \
  --region ap-southeast-1

# Attach to VPC
aws ec2 attach-internet-gateway \
  --internet-gateway-id igw-xxxxxxxxx \
  --vpc-id vpc-xxxxxxxxx \
  --region ap-southeast-1
```

- [ ] Internet Gateway created (igw-xxxxxxxxx)
- [ ] Attached to VPC
- [ ] Verify status: "available"

### Step 1.4: Create NAT Gateways

```bash
# Allocate Elastic IP for NAT Gateway in AZ-a
aws ec2 allocate-address \
  --domain vpc \
  --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=truematch-nat-eip-1a}]' \
  --region ap-southeast-1

# Create NAT Gateway in public subnet AZ-a
aws ec2 create-nat-gateway \
  --subnet-id subnet-public-1a-id \
  --allocation-id eipalloc-xxxxxxxxx \
  --tag-specifications 'ResourceType=nat-gateway,Tags=[{Key=Name,Value=truematch-nat-1a}]' \
  --region ap-southeast-1

# Wait until status is "available" (2-3 minutes)
aws ec2 describe-nat-gateways --nat-gateway-ids nat-xxxxxxxxx --region ap-southeast-1 --query 'NatGateways[0].State'

# Repeat for AZ-b
```

- [ ] NAT Gateway 1 created and available (AZ-a)
- [ ] NAT Gateway 2 created and available (AZ-b)
- [ ] Elastic IP addresses allocated and associated
- [ ] Both NAT Gateways showing "available" status

### Step 1.5: Create Route Tables

```bash
# Public route table
aws ec2 create-route-table \
  --vpc-id vpc-xxxxxxxxx \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=truematch-public-rt}]' \
  --region ap-southeast-1

# Add route to Internet Gateway
aws ec2 create-route \
  --route-table-id rtb-public-id \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id igw-xxxxxxxxx \
  --region ap-southeast-1

# Associate with public subnets
aws ec2 associate-route-table \
  --route-table-id rtb-public-id \
  --subnet-id subnet-public-1a-id \
  --region ap-southeast-1

aws ec2 associate-route-table \
  --route-table-id rtb-public-id \
  --subnet-id subnet-public-1b-id \
  --region ap-southeast-1
```

**Private Route Table (AZ-a with NAT-a):**

```bash
aws ec2 create-route-table \
  --vpc-id vpc-xxxxxxxxx \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=truematch-private-aza-rt}]' \
  --region ap-southeast-1

# Add route to NAT Gateway (AZ-a traffic exits through AZ-a NAT)
aws ec2 create-route \
  --route-table-id rtb-private-aza-id \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id nat-xxxxxxxxx \
  --region ap-southeast-1

# Associate with AZ-a subnets
aws ec2 associate-route-table \
  --route-table-id rtb-private-aza-id \
  --subnet-id subnet-eks-1a-id

aws ec2 associate-route-table \
  --route-table-id rtb-private-aza-id \
  --subnet-id subnet-db-1a-id
```

**Repeat for AZ-b and AZ-c**

- [ ] Public route table created and configured (0.0.0.0/0 → IGW)
- [ ] Private route table AZ-a created (0.0.0.0/0 → NAT-a)
- [ ] Private route table AZ-b created (0.0.0.0/0 → NAT-b)
- [ ] All subnets associated with correct route tables
- [ ] DB subnet group route table (no internet route)

**Validation:**
```bash
# Check routes
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=vpc-xxxxxxxxx" --region ap-southeast-1
```

### Step 1.6: Create Security Groups

```bash
# ALB Security Group
aws ec2 create-security-group \
  --group-name truematch-alb-sg \
  --description "ALB security group for TrueMatch API" \
  --vpc-id vpc-xxxxxxxxx \
  --region ap-southeast-1

# Add inbound rules
aws ec2 authorize-security-group-ingress \
  --group-id sg-alb-id \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0 \
  --region ap-southeast-1

aws ec2 authorize-security-group-ingress \
  --group-id sg-alb-id \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0 \
  --region ap-southeast-1

# Add outbound rule to EKS nodes
aws ec2 authorize-security-group-egress \
  --group-id sg-alb-id \
  --protocol tcp \
  --port 8000 \
  --cidr 10.0.11.0/24 \
  --region ap-southeast-1
```

**EKS Node Security Group:**

```bash
aws ec2 create-security-group \
  --group-name truematch-eks-sg \
  --description "EKS node security group" \
  --vpc-id vpc-xxxxxxxxx \
  --region ap-southeast-1

# Allow from ALB
aws ec2 authorize-security-group-ingress \
  --group-id sg-eks-id \
  --protocol tcp \
  --port 8000 \
  --source-group sg-alb-id \
  --region ap-southeast-1

# Allow pod-to-pod communication
aws ec2 authorize-security-group-ingress \
  --group-id sg-eks-id \
  --protocol -1 \
  --cidr 10.0.0.0/16 \
  --region ap-southeast-1
```

**RDS Security Group:**

```bash
aws ec2 create-security-group \
  --group-name truematch-rds-sg \
  --description "RDS PostgreSQL security group" \
  --vpc-id vpc-xxxxxxxxx \
  --region ap-southeast-1

# Allow from EKS nodes on port 5432
aws ec2 authorize-security-group-ingress \
  --group-id sg-rds-id \
  --protocol tcp \
  --port 5432 \
  --source-group sg-eks-id \
  --region ap-southeast-1
```

**ElastiCache Security Group:**

```bash
aws ec2 create-security-group \
  --group-name truematch-redis-sg \
  --description "ElastiCache Redis security group" \
  --vpc-id vpc-xxxxxxxxx \
  --region ap-southeast-1

# Allow from EKS nodes on port 6379
aws ec2 authorize-security-group-ingress \
  --group-id sg-redis-id \
  --protocol tcp \
  --port 6379 \
  --source-group sg-eks-id \
  --region ap-southeast-1
```

- [ ] ALB security group created (sg-alb-id)
- [ ] EKS security group created (sg-eks-id)
- [ ] RDS security group created (sg-rds-id)
- [ ] Redis security group created (sg-redis-id)
- [ ] All inbound/outbound rules configured correctly

**Validation:**
```bash
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=vpc-xxxxxxxxx" --region ap-southeast-1
```

---

## Phase 2: Data Layer - RDS PostgreSQL (Days 4-6)

### Step 2.1: Create DB Subnet Group

```bash
aws rds create-db-subnet-group \
  --db-subnet-group-name truematch-db-subnet-group \
  --db-subnet-group-description "DB subnet group for RDS PostgreSQL" \
  --subnet-ids subnet-db-1a-id subnet-db-1b-id subnet-db-1c-id \
  --tags Key=Name,Value=truematch-db-subnet-group Key=Environment,Value=production \
  --region ap-southeast-1
```

- [ ] DB subnet group created
- [ ] Verify in RDS Console: DB Subnet Groups

### Step 2.2: Create RDS Parameter Group

```bash
aws rds create-db-parameter-group \
  --db-parameter-group-name truematch-postgresql14 \
  --db-parameter-group-family postgres14 \
  --description "Custom parameter group for TrueMatch PostgreSQL" \
  --tags Key=Name,Value=truematch-postgresql14 Key=Environment,Value=production \
  --region ap-southeast-1

# Modify key parameters
aws rds modify-db-parameter-group \
  --db-parameter-group-name truematch-postgresql14 \
  --parameters "ParameterName=shared_buffers,ParameterValue=4194304,ApplyMethod=immediate" \
               "ParameterName=max_connections,ParameterValue=500,ApplyMethod=immediate" \
               "ParameterName=log_statement,ParameterValue=ddl,ApplyMethod=immediate" \
               "ParameterName=log_min_duration_statement,ParameterValue=1000,ApplyMethod=immediate" \
               "ParameterName=ssl,ParameterValue=1,ApplyMethod=immediate" \
  --region ap-southeast-1
```

- [ ] Parameter group created (truematch-postgresql14)
- [ ] Key parameters configured:
  - [ ] shared_buffers = 4GB
  - [ ] max_connections = 500
  - [ ] log_statement = ddl
  - [ ] ssl = 1

### Step 2.3: Create RDS Instance

```bash
aws rds create-db-instance \
  --db-instance-identifier truematch-db \
  --db-instance-class db.t4g.medium \
  --engine postgres \
  --engine-version 14.10 \
  --master-username truematch \
  --master-user-password <SECURE-PASSWORD-HERE> \
  --allocated-storage 100 \
  --storage-type gp3 \
  --storage-throughput 125 \
  --iops 3000 \
  --db-name truematch_production \
  --db-subnet-group-name truematch-db-subnet-group \
  --vpc-security-group-ids sg-rds-id \
  --db-parameter-group-name truematch-postgresql14 \
  --multi-az \
  --backup-retention-period 14 \
  --backup-window "03:00-04:00" \
  --preferred-maintenance-window "sun:04:00-sun:05:00" \
  --enable-encryption \
  --kms-key-id <KMS-KEY-ARN> \
  --enable-cloudwatch-logs-exports '["postgresql"]' \
  --deletion-protection \
  --tags Key=Name,Value=truematch-db Key=Environment,Value=production \
  --region ap-southeast-1
```

- [ ] RDS instance creation initiated
- [ ] Wait for status "available" (10-15 minutes)

**Monitor Progress:**
```bash
aws rds describe-db-instances \
  --db-instance-identifier truematch-db \
  --region ap-southeast-1 \
  --query 'DBInstances[0].{Status:DBInstanceStatus,Endpoint:Endpoint.Address,Engine:Engine}'
```

- [ ] Status shows "available"
- [ ] Endpoint accessible: truematch-db.xxxxx.ap-southeast-1.rds.amazonaws.com
- [ ] Multi-AZ standby created (visible in console)
- [ ] CloudWatch Logs enabled

### Step 2.4: Configure RDS Proxy

```bash
# Create RDS Proxy for connection pooling
aws rds create-db-proxy \
  --db-proxy-name truematch-db-proxy \
  --engine-family POSTGRESQL \
  --auth '[{"AuthScheme": "SECRETS", "SecretArn": "<SECRETS-MANAGER-ARN>", "IAMAuth": "DISABLED"}]' \
  --role-arn arn:aws:iam::525125475338:role/rds-proxy-role \
  --db-subnet-group-name truematch-db-subnet-group \
  --vpc-security-group-ids sg-rds-id \
  --max-idle-connections-percent 50 \
  --connection-borrow-timeout 120 \
  --init-query "" \
  --max-connections-percent 100 \
  --session-pinning-filters '[]' \
  --tags Key=Name,Value=truematch-db-proxy Key=Environment,Value=production \
  --region ap-southeast-1

# Create target group
aws rds create-db-proxy-target-group \
  --db-proxy-name truematch-db-proxy \
  --target-group-name default \
  --db-instance-identifiers truematch-db \
  --region ap-southeast-1
```

- [ ] RDS Proxy created (truematch-db-proxy)
- [ ] Target group created (default)
- [ ] Proxy endpoint: truematch-db-proxy.proxy-xxxxx.ap-southeast-1.rds.amazonaws.com
- [ ] Connection pooling configured

### Step 2.5: Test Database Connectivity

```bash
# Connect from EC2 instance or bastion
psql -h truematch-db.xxxxx.ap-southeast-1.rds.amazonaws.com \
     -U truematch \
     -d truematch_production \
     -c "SELECT version();"
```

- [ ] Database connection successful
- [ ] Version confirmed: PostgreSQL 14.x
- [ ] Can execute queries
- [ ] Multi-AZ status confirmed in console

### Step 2.6: Create Automated Backup Verification

```bash
# Verify backup settings
aws rds describe-db-instances \
  --db-instance-identifier truematch-db \
  --region ap-southeast-1 \
  --query 'DBInstances[0].{BackupRetentionPeriod:BackupRetentionPeriod,PreferredBackupWindow:PreferredBackupWindow,MultiAZ:MultiAZEnabled}'
```

- [ ] Backup retention: 14 days
- [ ] Backup window: 03:00-04:00 UTC+8
- [ ] Multi-AZ: Enabled
- [ ] At least one backup snapshot created

---

## Phase 3: Cache Layer - ElastiCache Redis (Days 6-7)

### Step 3.1: Create ElastiCache Subnet Group

```bash
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name truematch-redis-subnet-group \
  --cache-subnet-group-description "Redis subnet group for TrueMatch" \
  --subnet-ids subnet-db-1a-id subnet-db-1b-id subnet-db-1c-id \
  --tags Key=Name,Value=truematch-redis-subnet-group Key=Environment,Value=production \
  --region ap-southeast-1
```

- [ ] Subnet group created (truematch-redis-subnet-group)
- [ ] All 3 AZ subnets included

### Step 3.2: Create Parameter Group

```bash
aws elasticache create-parameter-group \
  --parameter-group-name truematch-redis-params \
  --parameter-group-family redis7.0 \
  --description "Parameter group for TrueMatch Redis" \
  --tags Key=Name,Value=truematch-redis-params Key=Environment,Value=production \
  --region ap-southeast-1

# Modify parameters
aws elasticache modify-parameter-group \
  --parameter-group-name truematch-redis-params \
  --parameter-name-values "ParameterName=maxmemory-policy,ParameterValue=allkeys-lru" \
                          "ParameterName=timeout,ParameterValue=300" \
                          "ParameterName=tcp-keepalive,ParameterValue=60" \
  --region ap-southeast-1
```

- [ ] Parameter group created (truematch-redis-params)
- [ ] Parameters configured:
  - [ ] maxmemory-policy = allkeys-lru
  - [ ] timeout = 300
  - [ ] tcp-keepalive = 60

### Step 3.3: Create Redis Cluster (Cluster Mode)

```bash
aws elasticache create-replication-group \
  --replication-group-id truematch-redis-cluster \
  --replication-group-description "Redis cluster for TrueMatch" \
  --engine redis \
  --engine-version 7.0 \
  --cache-node-type cache.t4g.small \
  --num-cache-clusters 6 \
  --automatic-failover enabled \
  --multi-az enabled \
  --cache-parameter-group-name truematch-redis-params \
  --cache-subnet-group-name truematch-redis-subnet-group \
  --security-group-ids sg-redis-id \
  --snapshot-retention-limit 7 \
  --snapshot-window "04:00-05:00" \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled \
  --auth-token <REDIS-AUTH-TOKEN> \
  --automatic-backup-retention-days 7 \
  --tags Key=Name,Value=truematch-redis-cluster Key=Environment,Value=production \
  --region ap-southeast-1
```

- [ ] Replication group creation initiated (this takes 10-15 minutes)
- [ ] Wait for status "available"

**Monitor Progress:**
```bash
aws elasticache describe-replication-groups \
  --replication-group-id truematch-redis-cluster \
  --region ap-southeast-1 \
  --query 'ReplicationGroups[0].{Status:Status,MemberClusters:MemberClusters,Engine:Engine}'
```

- [ ] Status shows "available"
- [ ] 6 cache nodes created
- [ ] Primary endpoint: truematch-redis-cluster.xxxxx.ng.0001.apse1.cache.amazonaws.com
- [ ] Reader endpoint available for read-only operations

### Step 3.4: Test Redis Connectivity

```bash
# Install redis-cli or connect via application
redis-cli -h truematch-redis-cluster.xxxxx.ng.0001.apse1.cache.amazonaws.com \
          -p 6379 \
          --tls \
          -a <REDIS-AUTH-TOKEN> \
          PING

# Should return: PONG
```

- [ ] Redis connectivity verified
- [ ] PING command returns PONG
- [ ] AUTH token works
- [ ] TLS connection successful

### Step 3.5: Configure Backups & Snapshots

```bash
# Snapshots are automatically created (already configured in Step 3.3)
# Verify snapshot settings
aws elasticache describe-replication-groups \
  --replication-group-id truematch-redis-cluster \
  --region ap-southeast-1 \
  --query 'ReplicationGroups[0].{SnapshotWindow:SnapshotWindow,SnapshotRetentionLimit:SnapshotRetentionLimit,AtRestEncryptionEnabled:AtRestEncryptionEnabled}'
```

- [ ] Snapshot window: 04:00-05:00 UTC+8
- [ ] Retention: 7 days
- [ ] Encryption at rest: Enabled
- [ ] Transit encryption: Enabled

---

## Phase 4: Container Registry - ECR (Days 7-8)

### Step 4.1: Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name truematch-api \
  --encryption-configuration encryptionType=KMS,kmsKey=<KMS-KEY-ARN> \
  --image-scanning-configuration scanOnPush=true \
  --image-tag-mutability MUTABLE \
  --tags Key=Name,Value=truematch-api Key=Environment,Value=production \
  --region ap-southeast-1
```

- [ ] Repository created (truematch-api)
- [ ] Repository URI: 525125475338.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-api
- [ ] Encryption enabled (KMS)
- [ ] Image scanning enabled

### Step 4.2: Set Image Retention Policy

```bash
aws ecr put-lifecycle-policy \
  --repository-name truematch-api \
  --lifecycle-policy-text '{
    "rules": [
      {
        "rulePriority": 1,
        "description": "Keep last 30 production images",
        "selection": {
          "tagStatus": "tagged",
          "tagPrefixList": ["v"],
          "countType": "imageCountMoreThan",
          "countNumber": 30
        },
        "action": {"type": "expire"}
      },
      {
        "rulePriority": 2,
        "description": "Keep development images for 7 days",
        "selection": {
          "tagStatus": "tagged",
          "tagPrefixList": ["dev-"],
          "countType": "sinceImagePushed",
          "countUnit": "days",
          "countNumber": 7
        },
        "action": {"type": "expire"}
      }
    ]
  }' \
  --region ap-southeast-1
```

- [ ] Lifecycle policy configured
- [ ] Production images (v*) retention: 30 images
- [ ] Development images (dev-*) retention: 7 days

### Step 4.3: Build & Push Sample Image

```bash
# Login to ECR
aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin 525125475338.dkr.ecr.ap-southeast-1.amazonaws.com

# Build image
docker build -t truematch-api:v0.1.0 .

# Tag image for ECR
docker tag truematch-api:v0.1.0 525125475338.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-api:v0.1.0
docker tag truematch-api:v0.1.0 525125475338.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-api:latest

# Push to ECR
docker push 525125475338.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-api:v0.1.0
docker push 525125475338.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-api:latest
```

- [ ] Docker login successful
- [ ] Image built locally
- [ ] Image tagged correctly
- [ ] Image pushed to ECR (visible in console)
- [ ] Image scanning completed (check for vulnerabilities)

**Validation:**
```bash
aws ecr describe-images \
  --repository-name truematch-api \
  --region ap-southeast-1 \
  --query 'imageDetails[].{Tag:imageTags,Digest:imageDigest,ScanStatus:imageScanStatus.status}'
```

---

## Phase 5: EKS Kubernetes Cluster (Days 8-12)

### Step 5.1: Create IAM Roles for EKS

**Cluster Role:**

```bash
# Create role
aws iam create-role \
  --role-name eks-truematch-cluster-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {"Service": "eks.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }
    ]
  }' \
  --tags Key=Name,Value=eks-truematch-cluster-role Key=Environment,Value=production

# Attach policy
aws iam attach-role-policy \
  --role-name eks-truematch-cluster-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy
```

**Node Role:**

```bash
aws iam create-role \
  --role-name eks-truematch-node-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {"Service": "ec2.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }
    ]
  }'

# Attach policies
aws iam attach-role-policy \
  --role-name eks-truematch-node-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy

aws iam attach-role-policy \
  --role-name eks-truematch-node-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy

aws iam attach-role-policy \
  --role-name eks-truematch-node-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly

# Allow KMS decryption and Secrets Manager access
aws iam put-role-policy \
  --role-name eks-truematch-node-role \
  --policy-name eks-truematch-node-kms-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
        "Resource": "<KMS-KEY-ARN>"
      },
      {
        "Effect": "Allow",
        "Action": ["secretsmanager:GetSecretValue"],
        "Resource": "arn:aws:secretsmanager:ap-southeast-1:525125475338:secret:*"
      }
    ]
  }'
```

- [ ] Cluster role created (eks-truematch-cluster-role)
- [ ] Node role created (eks-truematch-node-role)
- [ ] All required policies attached

### Step 5.2: Create EKS Cluster

```bash
aws eks create-cluster \
  --name truematch-eks-cluster \
  --version 1.29 \
  --role-arn arn:aws:iam::525125475338:role/eks-truematch-cluster-role \
  --resources-vpc-config \
    subnetIds=subnet-eks-1a-id,subnet-eks-1b-id,subnet-eks-1c-id,subnet-public-1a-id,subnet-public-1b-id \
    securityGroupIds=sg-eks-id \
    endpointPublicAccess=true \
    endpointPrivateAccess=false \
  --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}' \
  --tags Name=truematch-eks-cluster,Environment=production \
  --region ap-southeast-1
```

- [ ] Cluster creation initiated
- [ ] Wait for status "ACTIVE" (10-15 minutes)

**Monitor Progress:**
```bash
aws eks describe-cluster \
  --name truematch-eks-cluster \
  --region ap-southeast-1 \
  --query 'cluster.{Status:status,Endpoint:endpoint}'
```

- [ ] Status: "ACTIVE"
- [ ] Cluster endpoint available
- [ ] Logging enabled for all types

### Step 5.3: Update kubeconfig

```bash
# Update local kubeconfig
aws eks update-kubeconfig \
  --region ap-southeast-1 \
  --name truematch-eks-cluster

# Verify connection
kubectl cluster-info
kubectl get nodes  # Should be empty (no nodes yet)
```

- [ ] kubeconfig updated
- [ ] kubectl can connect to cluster
- [ ] Current context: truematch-eks-cluster

### Step 5.4: Create Node Group

```bash
aws eks create-nodegroup \
  --cluster-name truematch-eks-cluster \
  --nodegroup-name truematch-node-group-1 \
  --node-role arn:aws:iam::525125475338:role/eks-truematch-node-role \
  --subnets subnet-eks-1a-id subnet-eks-1b-id subnet-eks-1c-id \
  --instance-types t4g.large \
  --scaling-config \
    minSize=3 \
    maxSize=10 \
    desiredSize=3 \
  --tags Name=truematch-node-group-1,Environment=production \
  --labels Environment=production,NodeGroup=truematch-1 \
  --region ap-southeast-1
```

- [ ] Node group creation initiated (5-10 minutes)
- [ ] Wait for status "ACTIVE"

**Monitor Progress:**
```bash
aws eks describe-nodegroup \
  --cluster-name truematch-eks-cluster \
  --nodegroup-name truematch-node-group-1 \
  --region ap-southeast-1 \
  --query 'nodegroup.{Status:status,DesiredSize:scalingConfig.desiredSize,RunningSize:resources.autoScalingGroups[0].desiredCapacity}'
```

- [ ] Status: "ACTIVE"
- [ ] 3 nodes running
- [ ] All nodes in "Ready" state

**Verify with kubectl:**
```bash
kubectl get nodes -o wide
# Should show 3 nodes with status "Ready"
```

- [ ] 3 nodes listed
- [ ] All nodes "Ready"
- [ ] All nodes t4g.large (ARM64 architecture)

### Step 5.5: Install Cluster Autoscaler

```bash
# Create service account for autoscaler
kubectl create namespace kube-system
kubectl create serviceaccount cluster-autoscaler -n kube-system

# Create IAM policy for autoscaler
aws iam put-role-policy \
  --role-name eks-truematch-node-role \
  --policy-name eks-autoscaler-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "autoscaling:DescribeAutoScalingGroups",
          "autoscaling:DescribeAutoScalingInstances",
          "autoscaling:DescribeLaunchConfigurations",
          "ec2:DescribeImages",
          "ec2:DescribeInstanceTypes",
          "ec2:DescribeLaunchTemplateVersions"
        ],
        "Resource": "*"
      },
      {
        "Effect": "Allow",
        "Action": [
          "autoscaling:SetDesiredCapacity",
          "autoscaling:TerminateInstanceInAutoScalingGroup"
        ],
        "Resource": "*"
      }
    ]
  }'

# Deploy Cluster Autoscaler (using Helm or manifest)
helm repo add autoscaler https://kubernetes.github.io/autoscaler
helm install cluster-autoscaler autoscaler/cluster-autoscaler \
  --namespace kube-system \
  --set autoDiscovery.clusterName=truematch-eks-cluster \
  --set awsRegion=ap-southeast-1 \
  --set rbac.serviceAccount.create=false \
  --set rbac.serviceAccount.name=cluster-autoscaler
```

- [ ] Service account created
- [ ] IAM policy attached
- [ ] Cluster Autoscaler deployed
- [ ] Pod running in kube-system namespace

**Verify:**
```bash
kubectl get pod -n kube-system -l app.kubernetes.io/name=aws-cluster-autoscaler
```

### Step 5.6: Install CoreDNS & kube-proxy

```bash
# These are pre-installed with EKS, but verify they're running
kubectl get pods -n kube-system

# Should see:
# - coredns-xxx pods (DNS)
# - kube-proxy-xxx pods (networking)
# - aws-node-xxx pods (VPC CNI)
```

- [ ] CoreDNS: Running
- [ ] kube-proxy: Running
- [ ] aws-node (VPC CNI): Running

---

## Phase 6: Load Balancer & Ingress (Days 12-14)

### Step 6.1: Install ALB Ingress Controller

```bash
# Add IAM policy for ALB controller
aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document '{...}' \
  --region ap-southeast-1

# Create service account
kubectl create serviceaccount aws-load-balancer-controller -n kube-system

# Install ALB controller via Helm
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=truematch-eks-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

- [ ] IAM policy created
- [ ] Service account created
- [ ] ALB controller pod running

**Verify:**
```bash
kubectl get pod -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
```

### Step 6.2: Create Application Load Balancer (Ingress)

```bash
# Save as ingress.yaml
cat > ingress.yaml <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: truematch-ingress
  namespace: default
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:ap-southeast-1:525125475338:certificate/xxxxx
    alb.ingress.kubernetes.io/group.name: truematch-alb
    alb.ingress.kubernetes.io/group.order: '1'
spec:
  rules:
    - host: api.truematch.io
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: truematch-api
                port:
                  number: 80
EOF

kubectl apply -f ingress.yaml
```

- [ ] Ingress created (truematch-ingress)
- [ ] Wait 2-3 minutes for ALB provisioning

**Verify:**
```bash
kubectl get ingress -o wide
# Should show ALB DNS name in ADDRESS column
```

- [ ] Ingress status: "truematch-xxx.ap-southeast-1.elb.amazonaws.com"
- [ ] ALB created in EC2 console

### Step 6.3: Update Route53 DNS

```bash
# Get ALB DNS name
ALB_DNS=$(kubectl get ingress truematch-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Create Route53 A record (alias to ALB)
aws route53 change-resource-record-sets \
  --hosted-zone-id <HOSTED-ZONE-ID> \
  --change-batch '{
    "Changes": [
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "api.truematch.io",
          "Type": "A",
          "AliasTarget": {
            "HostedZoneId": "Z1H1FL5HABSF5",
            "DNSName": "'${ALB_DNS}'",
            "EvaluateTargetHealth": true
          }
        }
      }
    ]
  }' \
  --region ap-southeast-1
```

- [ ] DNS A record created (api.truematch.io)
- [ ] Alias target points to ALB
- [ ] DNS propagation time: 5-10 minutes

---

## Phase 7: Application Deployment (Days 14-16)

### Step 7.1: Create Kubernetes Namespace

```bash
kubectl create namespace truematch
kubectl label namespace truematch environment=production
```

- [ ] Namespace "truematch" created
- [ ] Labels applied

### Step 7.2: Create Secrets

```bash
# Database password
kubectl create secret generic db-secret \
  --from-literal=username=truematch \
  --from-literal=password=<DB-PASSWORD> \
  --from-literal=host=truematch-db-proxy.proxy-xxxxx.ap-southeast-1.rds.amazonaws.com \
  --from-literal=port=5432 \
  --from-literal=dbname=truematch_production \
  -n truematch

# Redis password
kubectl create secret generic redis-secret \
  --from-literal=password=<REDIS-PASSWORD> \
  --from-literal=host=truematch-redis-cluster.xxxxx.ng.0001.apse1.cache.amazonaws.com \
  --from-literal=port=6379 \
  -n truematch

# ECR image pull secret (if needed)
kubectl create secret docker-registry ecr-secret \
  --docker-server=525125475338.dkr.ecr.ap-southeast-1.amazonaws.com \
  --docker-username=AWS \
  --docker-password=$(aws ecr get-login-password --region ap-southeast-1) \
  -n truematch
```

- [ ] db-secret created
- [ ] redis-secret created
- [ ] Secrets stored in Kubernetes

**Verify:**
```bash
kubectl get secrets -n truematch
```

### Step 7.3: Deploy FastAPI Application

```bash
# Save as deployment.yaml
cat > deployment.yaml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: truematch-api
  namespace: truematch
spec:
  replicas: 2
  selector:
    matchLabels:
      app: truematch-api
  template:
    metadata:
      labels:
        app: truematch-api
        version: v1
    spec:
      containers:
      - name: api
        image: 525125475338.dkr.ecr.ap-southeast-1.amazonaws.com/truematch-api:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        - name: ENVIRONMENT
          value: production
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1024Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
EOF

kubectl apply -f deployment.yaml
```

- [ ] Deployment created (truematch-api)
- [ ] Initial pods: 2 replicas

**Monitor Pod Startup:**
```bash
kubectl get pods -n truematch -w
# Wait for pods to show "Running" status
```

- [ ] Pods status: "Running"
- [ ] Container ready: True
- [ ] 0 restarts

### Step 7.4: Create Service

```bash
cat > service.yaml <<EOF
apiVersion: v1
kind: Service
metadata:
  name: truematch-api
  namespace: truematch
spec:
  type: ClusterIP
  selector:
    app: truematch-api
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
EOF

kubectl apply -f service.yaml
```

- [ ] Service created (truematch-api)
- [ ] Type: ClusterIP
- [ ] Endpoint: Points to pod IPs

### Step 7.5: Configure Horizontal Pod Autoscaler

```bash
cat > hpa.yaml <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: truematch-api-hpa
  namespace: truematch
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: truematch-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 75
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
EOF

kubectl apply -f hpa.yaml
```

- [ ] HPA created (truematch-api-hpa)
- [ ] Min: 2 replicas
- [ ] Max: 10 replicas
- [ ] Scaling metrics: CPU 70%, Memory 75%

**Verify:**
```bash
kubectl get hpa -n truematch
```

---

## Phase 8: Monitoring & Logging (Days 16-17)

### Step 8.1: Enable Container Insights

```bash
# Create namespace for CloudWatch agent
kubectl create namespace amazon-cloudwatch

# Deploy CloudWatch agent
curl https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluentd-quickstart.yaml | \
  sed "s/{{cluster_name}}/truematch-eks-cluster/;s/{{region_name}}/ap-southeast-1/" | \
  kubectl apply -f -
```

- [ ] amazon-cloudwatch namespace created
- [ ] CloudWatch agent deployed
- [ ] Pods running: cloudwatch-agent, fluentd

### Step 8.2: Configure Application Logging

```bash
# Application should output JSON logs to stdout
# Example (Python FastAPI):
# import json
# import logging
# logger = logging.getLogger()
# logger.info(json.dumps({"request_id": "123", "endpoint": "/api/users", "status": 200}))

# Verify logs in CloudWatch
aws logs describe-log-groups --region ap-southeast-1 | grep /aws/eks
```

- [ ] CloudWatch log groups created automatically
- [ ] /aws/eks/truematch-eks-cluster/cluster visible
- [ ] Application logs captured in /aws/truematch/api group

### Step 8.3: Create CloudWatch Dashboard

```bash
# Create dashboard via AWS Console or CLI
aws cloudwatch put-dashboard \
  --dashboard-name truematch-api-overview \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/ApplicationELB", "RequestCount", {"stat": "Sum"}],
            ["AWS/ApplicationELB", "HTTPCode_Target_2XX_Count"],
            ["AWS/ApplicationELB", "HTTPCode_Target_4XX_Count"],
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count"],
            ["ContainerInsights", "PodCPUUtilization"],
            ["ContainerInsights", "PodMemoryUtilization"]
          ],
          "period": 60,
          "stat": "Average",
          "region": "ap-southeast-1",
          "title": "TrueMatch API Metrics"
        }
      }
    ]
  }' \
  --region ap-southeast-1
```

- [ ] Dashboard created (truematch-api-overview)
- [ ] Metrics displayed: Request count, error rates, resource utilization
- [ ] Refreshes every minute

### Step 8.4: Create CloudWatch Alarms

```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name truematch-api-high-error-rate \
  --alarm-description "Alert when error rate exceeds 5%" \
  --metric-name HTTPCode_Target_5XX_Count \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 60 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:ap-southeast-1:525125475338:truematch-alerts \
  --region ap-southeast-1

# High CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name truematch-api-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:ap-southeast-1:525125475338:truematch-alerts \
  --region ap-southeast-1
```

- [ ] Error rate alarm created
- [ ] CPU alarm created
- [ ] Database connection alarm created
- [ ] Redis memory alarm created
- [ ] All alarms have SNS topic configured

---

## Phase 9: Security & Compliance Hardening (Days 17-18)

### Step 9.1: Enable VPC Flow Logs

```bash
# Create IAM role for VPC Flow Logs
aws iam create-role \
  --role-name vpc-flow-logs-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {"Service": "vpc-flow-logs.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }
    ]
  }'

aws iam put-role-policy \
  --role-name vpc-flow-logs-role \
  --policy-name vpc-flow-logs-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ],
        "Resource": "*"
      }
    ]
  }'

# Enable VPC Flow Logs
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-xxxxxxxxx \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/truematch-vpc-flows \
  --deliver-logs-permission-role-arn arn:aws:iam::525125475338:role/vpc-flow-logs-role \
  --region ap-southeast-1
```

- [ ] VPC Flow Logs role created
- [ ] Flow logs enabled for VPC
- [ ] Log group: /aws/vpc/truematch-vpc-flows
- [ ] Retention: 7 days

### Step 9.2: Configure Network Policies

```bash
# Create network policy to deny all by default
cat > network-policy-deny-all.yaml <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: truematch
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
EOF

# Create network policy to allow specific traffic
cat > network-policy-allow.yaml <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-alb
  namespace: truematch
spec:
  podSelector:
    matchLabels:
      app: truematch-api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 8000
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          role: database
    ports:
    - protocol: TCP
      port: 5432
EOF

kubectl apply -f network-policy-deny-all.yaml
kubectl apply -f network-policy-allow.yaml
```

- [ ] Network policies created
- [ ] Deny-all policy applied
- [ ] Allow-specific policies applied
- [ ] Test connectivity after applying

### Step 9.3: Enable RBAC & Pod Security Policies

```bash
# Create RBAC roles
cat > rbac.yaml <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: truematch-api-role
  namespace: truematch
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get"]
  resourceNames: ["db-secret", "redis-secret"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: truematch-api-rolebinding
  namespace: truematch
subjects:
- kind: ServiceAccount
  name: default
  namespace: truematch
roleRef:
  kind: Role
  name: truematch-api-role
  apiGroup: rbac.authorization.k8s.io
EOF

kubectl apply -f rbac.yaml
```

- [ ] RBAC roles created
- [ ] Service account bound to role
- [ ] Pods can only read necessary secrets

### Step 9.4: Scan Images for Vulnerabilities

```bash
# ECR image scanning is already enabled
# Check scan results
aws ecr describe-images \
  --repository-name truematch-api \
  --region ap-southeast-1 \
  --query 'imageDetails[].{Tag:imageTags[0],ScanStatus:imageScanStatus.status,Findings:imageScanStatus.imageScanFindingsSummary.imageScanCompletedAt}'

# Fix HIGH/CRITICAL vulnerabilities before pushing production
```

- [ ] All images scanned
- [ ] No CRITICAL vulnerabilities
- [ ] HIGH vulnerabilities documented and acceptable
- [ ] Scan reports archived

---

## Phase 10: Backup & Disaster Recovery Testing (Days 18-19)

### Step 10.1: Test RDS Backup Restore

```bash
# Get latest backup
aws rds describe-db-snapshots \
  --db-instance-identifier truematch-db \
  --region ap-southeast-1 \
  --query 'DBSnapshots[0].DBSnapshotIdentifier'

# Restore to new instance (test in non-production)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier truematch-db-restore-test \
  --db-snapshot-identifier <SNAPSHOT-ID> \
  --region ap-southeast-1

# Wait for restore to complete (10-15 minutes)
# Test connectivity to restored database
# Delete test instance
aws rds delete-db-instance \
  --db-instance-identifier truematch-db-restore-test \
  --skip-final-snapshot \
  --region ap-southeast-1
```

- [ ] Backup restore initiated
- [ ] Restore completed successfully
- [ ] Database connectivity verified
- [ ] Data integrity checked
- [ ] Test instance cleaned up

### Step 10.2: Test Redis Snapshot Restore

```bash
# Backup is automatic (already configured)
# Get snapshot info
aws elasticache describe-snapshots \
  --replication-group-id truematch-redis-cluster \
  --region ap-southeast-1

# Create test cluster from snapshot (optional)
# Verify snapshot contains expected data
# Confirm snapshot retention policy
```

- [ ] Snapshots verified
- [ ] Backup history visible
- [ ] Snapshot size acceptable

### Step 10.3: Document Runbooks

**Incident Response Runbook:**
- [ ] Database failover procedure documented
- [ ] Manual failover steps (if auto-failover fails)
- [ ] Data recovery steps
- [ ] Rollback procedure
- [ ] Escalation contacts listed

**Operations Runbook:**
- [ ] Deployment procedure documented
- [ ] Scaling procedures documented
- [ ] Monitoring alert responses documented
- [ ] Troubleshooting steps documented

### Step 10.4: Conduct DR Drill

```bash
# Simulate AZ failure
# 1. Terminate one EKS node
# 2. Verify pods reschedule to other AZs
# 3. Check application remains available
# 4. Measure RTO (recovery time)
```

- [ ] DR drill completed
- [ ] RTO measured: < 5 minutes
- [ ] All pods successfully rescheduled
- [ ] Application available during recovery

---

## Phase 11: Pre-Production Testing (Days 19-20)

### Step 11.1: Load Testing

```bash
# Use load testing tool (Apache JMeter, k6, Locust, etc.)
# Target: Simulate 10,000 DAU
# Duration: 30 minutes
# Ramp-up: Linear increase from 0 to 100% load

# Monitor during test:
# - CPU utilization (target: <70%)
# - Memory utilization (target: <75%)
# - Response time (p95 < 500ms)
# - Error rate (target: 0%)

# Example with k6:
# k6 run load-test.js --vus 100 --duration 30m
```

- [ ] Load test script created
- [ ] Load test executed
- [ ] Metrics recorded
- [ ] Autoscaling verified
- [ ] No errors during load test

### Step 11.2: Performance Benchmarking

```bash
# Measure baseline performance:
# - API response time (per endpoint)
# - Database query performance
# - Cache hit rate
# - Throughput (requests/sec)

# Record baseline metrics for future comparison
```

- [ ] Baseline performance metrics recorded
- [ ] Response times documented
- [ ] Throughput capacity measured

### Step 11.3: 24-Hour Soak Test

```bash
# Run application at 50% load for 24 hours
# Monitor for memory leaks, connection leaks
# Check logs for errors or warnings
# Verify auto-scaling behavior
```

- [ ] Soak test executed (24 hours)
- [ ] Memory stable (no leaks)
- [ ] No unhandled exceptions in logs
- [ ] Auto-scaling functioned correctly

### Step 11.4: Verify All Monitoring & Alarms

```bash
# Confirm all alarms are firing correctly
# Trigger test alert: Create high CPU load
# Verify PagerDuty/Slack notification received
# Check dashboard shows correct metrics
```

- [ ] All alarms tested
- [ ] Notifications working
- [ ] Dashboard accurate
- [ ] Escalation path verified

---

## Phase 12: Go-Live (Day 21)

### Step 12.1: Final Pre-Launch Checklist

- [ ] All security scanning complete (no critical vulnerabilities)
- [ ] All tests passing (unit, integration, load tests)
- [ ] Database backups verified
- [ ] Disaster recovery plan documented
- [ ] On-call rotation configured
- [ ] Runbooks reviewed by team
- [ ] Team trained on monitoring and incident response

### Step 12.2: DNS Cutover

```bash
# Update registrar to point to Route53 nameservers
# Or update Route53 to serve production domain

# Verify DNS propagation
nslookup api.truematch.io
dig api.truematch.io

# Check TTL: Should be low (300 seconds) for easy rollback
```

- [ ] DNS A record points to ALB
- [ ] TTL: 300 seconds (5 minutes)
- [ ] DNS propagation verified
- [ ] Test: curl https://api.truematch.io/health

### Step 12.3: Production Verification

```bash
# Test API endpoints
curl -H "Accept: application/json" \
  https://api.truematch.io/health

# Monitor metrics
# - Request rate increasing
# - Error rate: 0%
# - Response times normal

# Check logs for errors
kubectl logs -f deployment/truematch-api -n truematch
```

- [ ] API responding to requests
- [ ] Health check passing
- [ ] No errors in logs
- [ ] Metrics showing live traffic

### Step 12.4: Post-Launch Monitoring (24 hours)

```bash
# Monitor continuously for 24 hours
# - Track error rates
# - Monitor resource utilization
# - Check performance metrics
# - Review logs for anomalies
```

- [ ] 24-hour monitoring period completed
- [ ] No critical issues found
- [ ] Performance metrics baseline established
- [ ] Team on high alert (ready to rollback if needed)

### Step 12.5: Declare Production Ready

- [ ] Stakeholders notified of go-live
- [ ] Launch retrospective scheduled
- [ ] Post-launch review meeting scheduled
- [ ] Production support escalation confirmed

---

## Rollback Procedure (Emergency)

If critical issues occur post-launch:

### Immediate Actions

1. **Declare Incident**
   ```
   Notify #incident channel in Slack
   Page on-call engineer
   Start incident bridge
   ```

2. **Assess Severity**
   - Critical (data loss, complete outage): Immediate rollback
   - High (partial outage, error rate >5%): Assess & rollback within 30 min
   - Medium (degraded performance): Investigate first

3. **Rollback Steps**

   **Option A: Kubernetes Rollout Undo**
   ```bash
   # Rollback to previous deployment
   kubectl rollout history deployment/truematch-api -n truematch
   kubectl rollout undo deployment/truematch-api -n truematch
   kubectl rollout status deployment/truematch-api -n truematch
   ```

   **Option B: DNS Failover**
   ```bash
   # Point DNS to staging environment (if available)
   aws route53 change-resource-record-sets \
     --hosted-zone-id <ZONE-ID> \
     --change-batch '{"Changes":[{"Action":"UPSERT","ResourceRecordSet":{"Name":"api.truematch.io","Type":"A","AliasTarget":{"HostedZoneId":"Z1H1FL5HABSF5","DNSName":"staging-alb.amazonaws.com","EvaluateTargetHealth":true}}}]}'
   ```

   **Option C: Full Service Rollback**
   ```bash
   # Scale down affected deployment
   kubectl scale deployment truematch-api --replicas=0 -n truematch
   
   # Restore from backup if needed
   # Notify users of service status
   ```

4. **Verify Rollback**
   - [ ] Service responding
   - [ ] Error rate returning to normal
   - [ ] Database connection stable
   - [ ] No new errors in logs

5. **Post-Incident**
   - [ ] Root cause analysis
   - [ ] Fix deployed to staging
   - [ ] Additional testing performed
   - [ ] Team debriefing
   - [ ] Retry deployment after fixes

---

## Sign-Off & Handover

### Deployment Verification

- [ ] All checklist items completed
- [ ] Production environment stable
- [ ] Monitoring and alerting operational
- [ ] On-call rotation active
- [ ] Runbooks reviewed and tested

### Team Handover

- [ ] Operations team trained
- [ ] Support procedures documented
- [ ] Escalation chain confirmed
- [ ] Communication plan established

### Documentation

- [ ] Architecture diagram created
- [ ] Configuration documented
- [ ] Deployment pipeline documented
- [ ] Troubleshooting guide created

**Deployment completed:** [DATE]  
**Deployed by:** [ENGINEER]  
**Reviewed by:** [ARCHITECT]  
**Approved by:** [TECH LEAD]

---

**End of Implementation Checklist**

Total estimated time: 6-7 weeks for 1 engineer  
Expected go-live: Week 7

