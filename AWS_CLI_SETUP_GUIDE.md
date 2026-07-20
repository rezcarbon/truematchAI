# AWS CLI Setup Guide
## TrueMatch AI - AWS Credentials & Configuration

**Version:** 1.0  
**Last Updated:** July 21, 2026  

---

## 1. Prerequisites

### Required Software
```bash
# macOS (using Homebrew)
brew install awscli
brew install kubectl
brew install helm
brew install eksctl

# Linux (Ubuntu/Debian)
sudo apt update
sudo apt install -y awscli kubectl helm

# Or download binaries directly
# AWS CLI: https://aws.amazon.com/cli/
# kubectl: https://kubernetes.io/docs/tasks/tools/
# helm: https://helm.sh/docs/intro/install/
```

### Verify Installations
```bash
aws --version
# aws-cli/2.15.0 Python/3.11.0 Linux/5.15.0

kubectl version --client
# Client Version: v1.29.0

helm version
# version.BuildInfo{Version:"v3.13.0", ...}

eksctl version
# 0.168.0
```

---

## 2. AWS Account Setup

### 2.1 Create IAM User (for Programmatic Access)

**Via AWS Console:**
1. Sign in to AWS Management Console
2. Navigate to IAM (Identity and Access Management)
3. Click "Users" in sidebar
4. Click "Create user"
5. Enter username: `truematch-deployment`
6. Click "Next"

**Attach Permissions (Minimum Required):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters",
        "eks:CreateCluster",
        "eks:UpdateClusterConfig"
      ],
      "Resource": "arn:aws:eks:us-east-1:ACCOUNT:cluster/truematch-prod"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::ACCOUNT:role/eks-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:DescribeRepositories",
        "ecr:ListImages"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::truematch-uploads/*",
        "arn:aws:s3:::truematch-backups/*"
      ]
    }
  ]
}
```

**Or use AWS managed policy:**
- For deployment: `AmazonEKSFullAccess` (development only)
- For production: Create custom policy above

### 2.2 Generate Access Keys

1. Select the user: `truematch-deployment`
2. Click "Create access key"
3. Choose "Command Line Interface (CLI)"
4. Accept terms and click "Create access key"
5. **Important:** Download and secure the CSV file

**Access Key Format:**
```
Access Key ID:     AKIA... (20 characters)
Secret Access Key: wJal... (40 characters)
```

⚠️ **IMPORTANT:** Store these securely! They provide AWS access.

---

## 3. AWS CLI Configuration

### 3.1 Initial Setup

```bash
# Configure AWS CLI
aws configure

# Prompts:
# AWS Access Key ID: AKIA...
# AWS Secret Access Key: wJal...
# Default region: us-east-1
# Default output format: json
```

### 3.2 Verify Configuration

```bash
# Check configured credentials
aws sts get-caller-identity

# Output:
# {
#     "UserId": "AIDAI...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/truematch-deployment"
# }
```

### 3.3 Multiple Profiles (Optional)

For managing multiple AWS accounts or roles:

```bash
# Configure development profile
aws configure --profile truematch-dev

# Configure production profile
aws configure --profile truematch-prod

# Use profile for commands
aws eks describe-cluster --name truematch-prod --profile truematch-prod

# Or set default profile
export AWS_PROFILE=truematch-prod
aws eks describe-cluster --name truematch-prod
```

### 3.4 Configuration Files

**Credentials File (~/.aws/credentials):**
```
[default]
aws_access_key_id = AKIA...
aws_secret_access_key = wJal...

[truematch-prod]
aws_access_key_id = AKIA...
aws_secret_access_key = wJal...
```

**Config File (~/.aws/config):**
```
[default]
region = us-east-1
output = json

[profile truematch-prod]
region = us-east-1
output = json
role_arn = arn:aws:iam::123456789012:role/truematch-deployment
source_profile = default
```

---

## 4. MFA Configuration (Recommended)

### 4.1 Set Up MFA Device

**Virtual MFA (Google Authenticator, Authy):**

1. In AWS Console, go to IAM → Users
2. Select `truematch-deployment`
3. Click "Assign MFA device"
4. Choose "Virtual authenticator app"
5. Scan QR code with authenticator app
6. Enter two 6-digit codes from app
7. Click "Assign MFA"

### 4.2 Get Session Token with MFA

```bash
# Get temporary credentials valid for 12 hours
aws sts get-session-token \
  --serial-number arn:aws:iam::123456789012:mfa/truematch-deployment \
  --token-code 123456 \
  --duration-seconds 43200

# Output:
# {
#     "Credentials": {
#         "AccessKeyId": "ASIA...",
#         "SecretAccessKey": "...",
#         "SessionToken": "...",
#         "Expiration": "2026-07-22T12:00:00Z"
#     }
# }
```

### 4.3 Automate MFA with .bash_profile

```bash
# Add to ~/.bash_profile or ~/.zshrc
mfa_login() {
  local device_arn="arn:aws:iam::123456789012:mfa/truematch-deployment"
  read -p "MFA Code: " mfa_code
  
  local creds=$(aws sts get-session-token \
    --serial-number "$device_arn" \
    --token-code "$mfa_code" \
    --duration-seconds 43200 \
    --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' \
    --output text)
  
  export AWS_ACCESS_KEY_ID=$(echo $creds | awk '{print $1}')
  export AWS_SECRET_ACCESS_KEY=$(echo $creds | awk '{print $2}')
  export AWS_SESSION_TOKEN=$(echo $creds | awk '{print $3}')
  
  echo "✓ MFA authenticated (12 hours)"
}

# Use it:
# $ source ~/.bash_profile
# $ mfa_login
# MFA Code: 123456
# ✓ MFA authenticated (12 hours)
```

---

## 5. EKS Cluster Access

### 5.1 Update kubeconfig

```bash
# Retrieve cluster credentials
aws eks update-kubeconfig \
  --region us-east-1 \
  --name truematch-prod \
  --profile truematch-prod

# This updates ~/.kube/config
```

### 5.2 Verify kubectl Access

```bash
# List cluster info
kubectl cluster-info

# Output:
# Kubernetes control plane is running at https://...
# CoreDNS is running at https://...

# List nodes
kubectl get nodes -o wide

# Output:
# NAME            STATUS   ROLES    AGE   VERSION
# ip-10-0-1-1...  Ready    <none>   2d    v1.29.0
# ip-10-0-2-1...  Ready    <none>   2d    v1.29.0
# ip-10-0-3-1...  Ready    <none>   2d    v1.29.0

# List pods in all namespaces
kubectl get pods --all-namespaces
```

### 5.3 Set Default Namespace

```bash
# Set truematch namespace as default
kubectl config set-context --current --namespace=truematch

# Verify
kubectl config view --minify | grep namespace
# namespace: truematch
```

### 5.4 Create kubeconfig for CI/CD

For GitHub Actions or other CI/CD systems:

```bash
# Export kubeconfig as base64
cat ~/.kube/config | base64 > kubeconfig.b64

# Add to GitHub Secrets as KUBE_CONFIG
# Then in CI/CD:
# echo $KUBE_CONFIG | base64 -d > ~/.kube/config
```

---

## 6. Docker & ECR Setup

### 6.1 Create ECR Repositories

```bash
# Create repository for API
aws ecr create-repository \
  --repository-name truematch-api \
  --region us-east-1 \
  --encryption-configuration encryptionType=KMS

# Create repository for web
aws ecr create-repository \
  --repository-name truematch-web \
  --region us-east-1 \
  --encryption-configuration encryptionType=KMS

# List repositories
aws ecr describe-repositories --region us-east-1
```

### 6.2 Login to ECR

```bash
# Get login token (valid for 12 hours)
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com

# Verify login
docker ps  # Should work without auth errors
```

### 6.3 Configure Docker for Auto-login

Create ~/.docker/config.json:
```json
{
  "credsHelpers": {
    "123456789012.dkr.ecr.us-east-1.amazonaws.com": "ecr-login"
  }
}
```

Or use aws-vault:
```bash
brew install aws-vault

# Configure
aws-vault add truematch-prod
# Enter AWS credentials

# Use with Docker
aws-vault exec truematch-prod -- docker push \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/truematch-api:v1.2.3
```

---

## 7. AWS Region Configuration

### 7.1 Set Default Region

```bash
# Option 1: Environment variable (temporary)
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=us-east-1

# Option 2: CLI config (permanent)
aws configure set region us-east-1

# Option 3: Per-command flag
aws eks describe-cluster --region us-east-1 --name truematch-prod

# Verify
echo $AWS_REGION
# us-east-1
```

### 7.2 List Available Regions

```bash
# List all regions
aws ec2 describe-regions --query 'Regions[].RegionName' --output text

# List only opted-in regions
aws ec2 describe-regions --query 'Regions[?OptInStatus==`opt-in-not-required`]'
```

### 7.3 Multi-Region Strategy

```bash
# Primary region
export AWS_PRIMARY_REGION=us-east-1

# Secondary region (for DR)
export AWS_SECONDARY_REGION=ap-southeast-1

# Deploy to both regions
aws eks describe-cluster --region $AWS_PRIMARY_REGION --name truematch-prod
aws eks describe-cluster --region $AWS_SECONDARY_REGION --name truematch-dr
```

---

## 8. AWS Credentials Best Practices

### 8.1 Credential Management

```bash
# Never commit credentials to git
echo "~/.aws/credentials" >> .gitignore
echo "~/.aws/config" >> .gitignore

# Use environment variables for CI/CD
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="wJal..."
export AWS_DEFAULT_REGION="us-east-1"

# Or use GitHub Actions secrets:
# Settings → Secrets and variables → Actions
# Add: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
```

### 8.2 Credential Rotation

```bash
# Rotate access keys every 90 days
# 1. Create new access key in AWS Console
# 2. Update ~/.aws/credentials with new key
# 3. Test access with new credentials
# 4. Deactivate old access key in AWS Console
# 5. Wait 24 hours, then delete old key

# Check last access
aws iam get-access-key-last-used --access-key-id AKIA...
```

### 8.3 Assume IAM Role (Advanced)

```bash
# Create a role in another account
# Then assume it:

aws sts assume-role \
  --role-arn arn:aws:iam::ACCOUNT2:role/truematch-deployment \
  --role-session-name truematch-session \
  --duration-seconds 3600

# Returns temporary credentials
# Set in environment:
export AWS_ACCESS_KEY_ID="ASIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
```

---

## 9. AWS Account Verification

### 9.1 Verify Account Details

```bash
# Get account ID
aws sts get-caller-identity --query Account --output text
# 123456789012

# Get user/role name
aws sts get-caller-identity --query Arn --output text
# arn:aws:iam::123456789012:user/truematch-deployment

# Get all account info
aws sts get-caller-identity --output json
# {
#     "UserId": "AIDAI...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/truematch-deployment"
# }
```

### 9.2 Check Permissions

```bash
# Test EKS access
aws eks describe-cluster --name truematch-prod --region us-east-1

# Test ECR access
aws ecr describe-repositories --region us-east-1

# Test S3 access
aws s3 ls s3://truematch-uploads/

# Test RDS access
aws rds describe-db-instances --region us-east-1

# Test Redis (ElastiCache)
aws elasticache describe-cache-clusters --region us-east-1
```

### 9.3 List Active Services

```bash
# Get all AWS resources
aws resourcegroupstaggingapi get-resources \
  --tag-filter Key=Application,Values=truematch \
  --region us-east-1

# Filter by resource type
aws ec2 describe-instances --filters Name=tag:Application,Values=truematch --region us-east-1
aws rds describe-db-instances --region us-east-1
aws elasticache describe-cache-clusters --region us-east-1
```

---

## 10. Troubleshooting

### 10.1 Authentication Errors

```bash
# Error: InvalidSignatureException
# Solution: Check access key ID and secret key
aws sts get-caller-identity

# Error: UnauthorizedException
# Solution: Check IAM policy permissions
aws iam get-user --user-name truematch-deployment

# Error: MFA required
# Solution: Use get-session-token with MFA code
aws sts get-session-token \
  --serial-number arn:aws:iam::ACCOUNT:mfa/device \
  --token-code 123456
```

### 10.2 kubectl Connection Issues

```bash
# Error: Unable to connect to server
# Solution: Update kubeconfig
aws eks update-kubeconfig --region us-east-1 --name truematch-prod

# Error: cluster unreachable
# Solution: Check security group rules
aws ec2 describe-security-groups --filters Name=group-id,Values=sg-...

# Error: certificate has expired
# Solution: Rotate credentials/restart
aws eks update-kubeconfig --region us-east-1 --name truematch-prod
```

### 10.3 ECR Login Issues

```bash
# Error: denied: User is not authorized
# Solution: Check IAM permissions and ECR repository access
aws ecr describe-repositories --region us-east-1

# Error: not found
# Solution: Repository may not exist
aws ecr describe-repositories --repository-names truematch-api

# Error: unexpected EOF
# Solution: Re-login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com
```

### 10.4 S3 Access Issues

```bash
# Error: Access Denied
# Solution: Check bucket policy and IAM permissions
aws s3api get-bucket-policy --bucket truematch-uploads

# Error: NoSuchBucket
# Solution: Bucket may not exist or wrong region
aws s3 ls --region us-east-1 | grep truematch

# Test S3 access
aws s3 cp test.txt s3://truematch-uploads/test.txt --region us-east-1
```

---

## 11. Quick Reference Commands

```bash
# ===== CLUSTER OPERATIONS =====
# Describe cluster
aws eks describe-cluster --name truematch-prod --region us-east-1

# List clusters
aws eks list-clusters --region us-east-1

# Update kubeconfig
aws eks update-kubeconfig --name truematch-prod --region us-east-1

# ===== ECR OPERATIONS =====
# List repositories
aws ecr describe-repositories --region us-east-1

# List images
aws ecr list-images --repository-name truematch-api --region us-east-1

# Get image details
aws ecr describe-images --repository-name truematch-api --region us-east-1

# ===== S3 OPERATIONS =====
# List buckets
aws s3 ls

# Upload file
aws s3 cp file.txt s3://truematch-uploads/

# Download file
aws s3 cp s3://truematch-uploads/file.txt .

# List objects
aws s3 ls s3://truematch-uploads/ --recursive

# ===== RDS OPERATIONS =====
# Describe instances
aws rds describe-db-instances --region us-east-1

# Create snapshot
aws rds create-db-snapshot --db-instance-identifier truematch-prod --db-snapshot-identifier truematch-backup-$(date +%Y%m%d)

# List snapshots
aws rds describe-db-snapshots --region us-east-1

# ===== IAM OPERATIONS =====
# Get user
aws iam get-user --user-name truematch-deployment

# List access keys
aws iam list-access-keys --user-name truematch-deployment

# Check role
aws iam get-role --role-name truematch-eks-node-role
```

---

## 12. Next Steps

1. ✓ Install AWS CLI and tools
2. ✓ Create IAM user and access keys
3. ✓ Configure AWS credentials
4. ✓ Set up MFA (recommended)
5. ✓ Verify kubectl access to cluster
6. ✓ Configure Docker/ECR login
7. → Proceed to Docker Build & Push
8. → Proceed to Kubernetes Deployment

---

*AWS CLI Setup Guide - Complete and verified for production use. Proceed to next deployment stage.*
