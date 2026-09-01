# Environment & Secrets Setup Guide
## TrueMatch AI - AWS Secrets Manager Integration

**Version:** 1.0  
**Last Updated:** July 21, 2026  

---

## 1. Secrets Overview

### 1.1 Critical Secrets (MUST SECURE)

| Secret | Format | Source | Rotation | Notes |
|--------|--------|--------|----------|-------|
| DATABASE_PASSWORD | String | RDS | 90 days | PostgreSQL password |
| JWT_SECRET | Base64 | Generated | 180 days | Token signing key |
| ENCRYPTION_KEY | Base64 | Generated | Manual | AES-256 encryption |
| ENCRYPTION_INDEX_KEY | Base64 | Generated | Manual | Blind index key |
| AWS_ACCESS_KEY_ID | String | IAM | 90 days | S3 access |
| AWS_SECRET_ACCESS_KEY | String | IAM | 90 days | S3 secret |
| ANTHROPIC_API_KEY | String | Anthropic | Manual | LLM API key |
| SENDGRID_API_KEY | String | SendGrid | Manual | Email provider |
| SINGPASS_SIG_JWK | JSON | Singpass | Never | Singapore auth key |

### 1.2 Non-Secret Configuration

These can be stored in ConfigMap (not Secrets):
- DATABASE_HOST (hostname, not password)
- DATABASE_PORT (port number)
- REDIS_HOST, REDIS_PORT
- AWS_REGION
- S3_BUCKET
- API_WORKERS
- LOG_LEVEL
- CORS_ORIGINS

---

## 2. Secret Key Generation

### 2.1 Generate Encryption Keys

```bash
# AES-256 encryption key (base64-encoded 32 bytes)
python3 -c "
import base64
import secrets
key = secrets.token_bytes(32)
print(base64.b64encode(key).decode())
"

# Output example:
# MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDE=

# Store this value:
export ENCRYPTION_KEY="MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDE="
```

### 2.2 Generate JWT Secret

```bash
# JWT secret (32+ characters)
python3 -c "
import secrets
secret = secrets.token_urlsafe(32)
print(secret)
"

# Or using openssl
openssl rand -base64 32

# Output example:
# 9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e=

# Store this value:
export JWT_SECRET="9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e"
```

### 2.3 Generate Database Password

```bash
# Strong random password
openssl rand -base64 32

# Or Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Output example:
# K9mL7pQ2rX8vN3bW6yZ1cF4hG5jT9sU2

# Store this value:
export DATABASE_PASSWORD="K9mL7pQ2rX8vN3bW6yZ1cF4hG5jT9sU2"
```

### 2.4 AWS Access Keys (from IAM)

```bash
# 1. Created via AWS Console (already done in IAM setup)
# 2. Access Key ID: AKIA... (20 chars)
# 3. Secret Access Key: wJal... (40 chars)

# Verify you have them:
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY
```

---

## 3. AWS Secrets Manager Setup

### 3.1 Create Secrets

```bash
# Set variables for easier use
REGION="us-east-1"
APP_NAME="truematch"

# 1. Database password
aws secretsmanager create-secret \
  --name $APP_NAME/database/password \
  --description "PostgreSQL database password" \
  --secret-string "$DATABASE_PASSWORD" \
  --region $REGION \
  --add-replica-regions RegionCode=ap-southeast-1

# 2. JWT secret
aws secretsmanager create-secret \
  --name $APP_NAME/jwt/secret \
  --description "JWT token signing secret" \
  --secret-string "$JWT_SECRET" \
  --region $REGION

# 3. Encryption key
aws secretsmanager create-secret \
  --name $APP_NAME/encryption/key \
  --description "AES-256 encryption key" \
  --secret-string "$ENCRYPTION_KEY" \
  --region $REGION

# 4. Encryption index key
aws secretsmanager create-secret \
  --name $APP_NAME/encryption/index-key \
  --description "Blind index HMAC key" \
  --secret-string "$ENCRYPTION_INDEX_KEY" \
  --region $REGION

# 5. AWS S3 access key
aws secretsmanager create-secret \
  --name $APP_NAME/aws/access-key-id \
  --description "AWS IAM access key ID" \
  --secret-string "$AWS_ACCESS_KEY_ID" \
  --region $REGION

# 6. AWS S3 secret key
aws secretsmanager create-secret \
  --name $APP_NAME/aws/secret-access-key \
  --description "AWS IAM secret access key" \
  --secret-string "$AWS_SECRET_ACCESS_KEY" \
  --region $REGION

# 7. Anthropic API key
aws secretsmanager create-secret \
  --name $APP_NAME/anthropic/api-key \
  --description "Anthropic Claude API key" \
  --secret-string "$ANTHROPIC_API_KEY" \
  --region $REGION

# 8. SendGrid API key
aws secretsmanager create-secret \
  --name $APP_NAME/sendgrid/api-key \
  --description "SendGrid email service API key" \
  --secret-string "$SENDGRID_API_KEY" \
  --region $REGION

# 9. Singpass JWK files (JSON)
aws secretsmanager create-secret \
  --name $APP_NAME/singpass/sig-jwk \
  --description "Singpass signature JWK" \
  --secret-string file://singpass-sig-jwk.json \
  --region $REGION

aws secretsmanager create-secret \
  --name $APP_NAME/singpass/enc-jwk \
  --description "Singpass encryption JWK" \
  --secret-string file://singpass-enc-jwk.json \
  --region $REGION
```

### 3.2 List Created Secrets

```bash
# List all secrets
aws secretsmanager list-secrets --region us-east-1

# List secrets for truematch application
aws secretsmanager list-secrets \
  --region us-east-1 \
  --query 'SecretList[?Name.contains(@, `truematch`)].Name' \
  --output text
```

### 3.3 Retrieve Secrets

```bash
# Get database password
aws secretsmanager get-secret-value \
  --secret-id truematch/database/password \
  --region us-east-1 \
  --query SecretString \
  --output text

# Get JWT secret
aws secretsmanager get-secret-value \
  --secret-id truematch/jwt/secret \
  --region us-east-1 \
  --query SecretString \
  --output text

# Get as JSON
aws secretsmanager get-secret-value \
  --secret-id truematch/database/password \
  --region us-east-1 | jq .
```

---

## 4. Kubernetes Secrets Integration

### 4.1 Manual Secret Creation

```bash
# Create namespace first
kubectl create namespace truematch

# Create secret from literal values
kubectl create secret generic truematch-secrets \
  --from-literal=DATABASE_PASSWORD="$DATABASE_PASSWORD" \
  --from-literal=JWT_SECRET="$JWT_SECRET" \
  --from-literal=ENCRYPTION_KEY="$ENCRYPTION_KEY" \
  --from-literal=ENCRYPTION_INDEX_KEY="$ENCRYPTION_INDEX_KEY" \
  --from-literal=AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  --from-literal=AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  --from-literal=SENDGRID_API_KEY="$SENDGRID_API_KEY" \
  -n truematch

# Verify secret created
kubectl get secrets -n truematch
kubectl describe secret truematch-secrets -n truematch
```

### 4.2 External Secrets Operator (Recommended)

**Installation:**

```bash
# Add Helm repository
helm repo add external-secrets https://charts.external-secrets.io

# Install External Secrets Operator
helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace \
  --values - << 'EOF'
installCRDs: true
EOF

# Verify installation
kubectl get pods -n external-secrets-system
```

**IRSA Configuration (IAM Roles for Service Accounts):**

```bash
# 1. Create IAM policy
cat > secrets-manager-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:truematch/*"
    }
  ]
}
EOF

# Create IAM role
aws iam create-role \
  --role-name truematch-external-secrets \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Federated": "arn:aws:iam::ACCOUNT:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/EXAMPLEID"
        },
        "Action": "sts:AssumeRoleWithWebIdentity",
        "Condition": {
          "StringEquals": {
            "oidc.eks.us-east-1.amazonaws.com/id/EXAMPLEID:aud": "sts.amazonaws.com",
            "oidc.eks.us-east-1.amazonaws.com/id/EXAMPLEID:sub": "system:serviceaccount:truematch:external-secrets"
          }
        }
      }
    ]
  }'

# Attach policy
aws iam put-role-policy \
  --role-name truematch-external-secrets \
  --policy-name SecretsManagerAccess \
  --policy-document file://secrets-manager-policy.json
```

**Create SecretStore:**

```yaml
# k8s/04-secrets-store.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: truematch-secrets-store
  namespace: truematch
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: truematch-secrets
  namespace: truematch
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: truematch-secrets-store
    kind: SecretStore
  target:
    name: truematch-secrets
    creationPolicy: Owner
  data:
  - secretKey: DATABASE_PASSWORD
    remoteRef:
      key: truematch/database/password
  - secretKey: JWT_SECRET
    remoteRef:
      key: truematch/jwt/secret
  - secretKey: ENCRYPTION_KEY
    remoteRef:
      key: truematch/encryption/key
  - secretKey: ENCRYPTION_INDEX_KEY
    remoteRef:
      key: truematch/encryption/index-key
  - secretKey: AWS_ACCESS_KEY_ID
    remoteRef:
      key: truematch/aws/access-key-id
  - secretKey: AWS_SECRET_ACCESS_KEY
    remoteRef:
      key: truematch/aws/secret-access-key
  - secretKey: ANTHROPIC_API_KEY
    remoteRef:
      key: truematch/anthropic/api-key
  - secretKey: SENDGRID_API_KEY
    remoteRef:
      key: truematch/sendgrid/api-key
```

**Deploy SecretStore:**

```bash
kubectl apply -f k8s/04-secrets-store.yaml

# Verify
kubectl get secretstore -n truematch
kubectl get externalsecret -n truematch
kubectl get secrets -n truematch
```

---

## 5. Environment Files for Different Stages

### 5.1 Development Environment (.env.dev)

```bash
# backend/.env.dev
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=debug

DATABASE_URL=postgresql+asyncpg://truematch:password@localhost:5432/truematch
REDIS_URL=redis://localhost:6379/0

ENCRYPTION_KEY=<dev-key>
ENCRYPTION_INDEX_KEY=<dev-key>
JWT_SECRET=dev-secret-change-me

AWS_ACCESS_KEY_ID=<dev-key>
AWS_SECRET_ACCESS_KEY=<dev-secret>
S3_BUCKET=truematch-uploads-dev

ANTHROPIC_API_KEY=<dev-key>
SENDGRID_API_KEY=<dev-key>

CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 5.2 Staging Environment (.env.staging)

```bash
# backend/.env.staging
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=info

DATABASE_URL=postgresql+asyncpg://truematch:PASSWORD@truematch-staging.XXXX.us-east-1.rds.amazonaws.com:5432/truematch
REDIS_URL=redis://truematch-staging.XXXX.ng.0001.use1.cache.amazonaws.com:6379/0

ENCRYPTION_KEY=${SECRET_ENCRYPTION_KEY}
ENCRYPTION_INDEX_KEY=${SECRET_ENCRYPTION_INDEX_KEY}
JWT_SECRET=${SECRET_JWT_SECRET}

AWS_ACCESS_KEY_ID=${SECRET_AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${SECRET_AWS_SECRET_ACCESS_KEY}
S3_BUCKET=truematch-uploads-staging

ANTHROPIC_API_KEY=${SECRET_ANTHROPIC_API_KEY}
SENDGRID_API_KEY=${SECRET_SENDGRID_API_KEY}

CORS_ORIGINS=https://staging.truematch.digital
```

### 5.3 Production Environment (.env.prod)

```bash
# backend/.env.prod
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=warning

DATABASE_URL=postgresql+asyncpg://truematch:PASSWORD@truematch-prod.XXXX.us-east-1.rds.amazonaws.com:5432/truematch
REDIS_URL=redis://truematch-prod.XXXX.ng.0001.use1.cache.amazonaws.com:6379/0

ENCRYPTION_KEY=${SECRET_ENCRYPTION_KEY}
ENCRYPTION_INDEX_KEY=${SECRET_ENCRYPTION_INDEX_KEY}
JWT_SECRET=${SECRET_JWT_SECRET}

AWS_ACCESS_KEY_ID=${SECRET_AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${SECRET_AWS_SECRET_ACCESS_KEY}
S3_BUCKET=truematch-uploads

ANTHROPIC_API_KEY=${SECRET_ANTHROPIC_API_KEY}
SENDGRID_API_KEY=${SECRET_SENDGRID_API_KEY}

CORS_ORIGINS=https://truematch.digital,https://www.truematch.digital

SENTRY_DSN=${SECRET_SENTRY_DSN}
```

---

## 6. Kubernetes ConfigMap & Secret Reference

### 6.1 Update ConfigMap in k8s/02-config.yaml

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: truematch-config
  namespace: truematch
data:
  # Application environment
  ENVIRONMENT: "production"
  LOG_LEVEL: "info"
  DEBUG: "false"
  
  # API configuration
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  API_WORKERS: "4"
  
  # Database (non-secret values only)
  DATABASE_HOST: "truematch-db.XXXX.us-east-1.rds.amazonaws.com"
  DATABASE_PORT: "5432"
  DATABASE_NAME: "truematch"
  DATABASE_POOL_SIZE: "20"
  
  # Redis (non-secret values)
  REDIS_HOST: "truematch-redis.XXXX.ng.0001.use1.cache.amazonaws.com"
  REDIS_PORT: "6379"
  
  # AWS/S3 (non-secret)
  AWS_REGION: "us-east-1"
  S3_BUCKET: "truematch-uploads"
  
  # CORS
  CORS_ORIGINS: "https://truematch.digital,https://www.truematch.digital"
  CORS_ALLOW_CREDENTIALS: "true"
  
  # Feature flags
  ENCRYPTION_ENABLED: "true"
  VECTOR_SEARCH_ENABLED: "true"
  EMAIL_INGESTION_ENABLED: "true"
  
  # Monitoring
  ENABLE_PROMETHEUS_METRICS: "true"
  LOG_FORMAT: "json"
  LOG_LEVEL: "info"
```

### 6.2 Secret Reference in Deployments

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: truematch
spec:
  template:
    spec:
      containers:
      - name: api
        image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/truematch-api:v1.2.3
        
        # Load all ConfigMap values as environment variables
        envFrom:
        - configMapRef:
            name: truematch-config
        
        # Load all Secret values as environment variables
        - secretRef:
            name: truematch-secrets
        
        # Override/add specific environment variables
        env:
        # Construct DATABASE_URL from secret + config
        - name: DATABASE_URL
          value: "postgresql+asyncpg://$(DATABASE_USER):$(DATABASE_PASSWORD)@$(DATABASE_HOST):$(DATABASE_PORT)/$(DATABASE_NAME)"
        
        # Reference individual secrets
        - name: ENCRYPTION_KEY
          valueFrom:
            secretKeyRef:
              name: truematch-secrets
              key: ENCRYPTION_KEY
        
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: truematch-secrets
              key: JWT_SECRET
```

---

## 7. Secret Rotation

### 7.1 Set Up Automated Rotation

```bash
# Enable automatic rotation for database password
aws secretsmanager rotate-secret \
  --secret-id truematch/database/password \
  --rotation-rules AutomaticallyAfterDays=90 \
  --region us-east-1

# Configure rotation Lambda (if needed)
# For simplicity, set to manual rotation with reminder
```

### 7.2 Manual Secret Rotation

```bash
#!/bin/bash
# rotate-secret.sh

SECRET_NAME="truematch/database/password"
REGION="us-east-1"

# Generate new secret
NEW_SECRET=$(openssl rand -base64 32)

# 1. Update in Secrets Manager
aws secretsmanager update-secret \
  --secret-id $SECRET_NAME \
  --secret-string "$NEW_SECRET" \
  --region $REGION

# 2. Update in AWS RDS
MASTER_USER="truematch"
RDS_ENDPOINT="truematch-prod.XXXX.us-east-1.rds.amazonaws.com"
psql -U $MASTER_USER -h $RDS_ENDPOINT -d truematch \
  -c "ALTER ROLE truematch WITH PASSWORD '$NEW_SECRET';"

# 3. Update in Kubernetes secret
kubectl patch secret truematch-secrets \
  -p '{"data":{"DATABASE_PASSWORD":"'$(echo -n "$NEW_SECRET" | base64)'"}}'

# 4. Restart deployments to pick up new secret
kubectl rollout restart deployment/api -n truematch
kubectl rollout restart deployment/worker -n truematch

echo "✓ Secret rotated successfully"
```

---

## 8. Validation Procedures

### 8.1 Test Secret Access

```bash
# 1. Verify Kubernetes secret exists
kubectl get secret truematch-secrets -n truematch -o yaml

# 2. Verify secret values are set (don't print values!)
kubectl get secret truematch-secrets -n truematch \
  -o jsonpath='{.data.DATABASE_PASSWORD}' | base64 -d | wc -c
# Should output: 32 (password length)

# 3. Test database connection
kubectl run -it --rm debug \
  --image=postgres:15-alpine \
  --restart=Never \
  -- psql -h truematch-prod.XXXX.us-east-1.rds.amazonaws.com \
  -U truematch -d truematch -c "SELECT 1;"

# 4. Test S3 access
kubectl run -it --rm debug \
  --image=amazon/aws-cli:latest \
  --restart=Never \
  --env="AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" \
  --env="AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" \
  -- s3 ls s3://truematch-uploads/
```

### 8.2 Pod Environment Verification

```bash
# Check if secrets are mounted
kubectl exec -it deployment/api -n truematch -- env | grep ENCRYPTION_KEY
kubectl exec -it deployment/api -n truematch -- env | grep JWT_SECRET

# Verify ConfigMap values
kubectl exec -it deployment/api -n truematch -- env | grep DATABASE_HOST
kubectl exec -it deployment/api -n truematch -- env | grep S3_BUCKET
```

---

## 9. Security Best Practices

### 9.1 Secrets Management Checklist

- [ ] All secrets stored in AWS Secrets Manager
- [ ] Kubernetes secrets not committed to git
- [ ] RBAC restricts secret access
- [ ] Secrets encrypted with KMS
- [ ] Rotation policies configured
- [ ] Audit logging enabled
- [ ] Backup/disaster recovery tested
- [ ] Secrets never logged or exposed

### 9.2 Access Control

```yaml
# RBAC policy for secret access
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: secret-reader
  namespace: truematch
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get"]
  resourceNames: ["truematch-secrets"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-secrets
  namespace: truematch
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: secret-reader
subjects:
- kind: ServiceAccount
  name: truematch
  namespace: truematch
```

---

## 10. Troubleshooting

### 10.1 Secret Issues

```bash
# Secret not found
# Solution: Create secret if missing
kubectl create secret generic truematch-secrets \
  --from-literal=KEY=value \
  -n truematch

# Pod can't access secret
# Solution: Check RBAC permissions
kubectl auth can-i get secrets --as=system:serviceaccount:truematch:truematch

# Secret values incorrect
# Solution: Update secret
kubectl delete secret truematch-secrets -n truematch
kubectl create secret generic truematch-secrets \
  --from-literal=DATABASE_PASSWORD="$NEW_PASSWORD" \
  -n truematch

# External Secrets not syncing
# Solution: Check logs
kubectl logs -n external-secrets-system deployment/external-secrets
kubectl describe externalsecret truematch-secrets -n truematch
```

---

## Checklist

- [ ] All encryption keys generated and secured
- [ ] AWS Secrets Manager secrets created
- [ ] Kubernetes secrets configured
- [ ] External Secrets Operator installed (optional)
- [ ] Secret rotation policies enabled
- [ ] RBAC policies for secret access
- [ ] Audit logging configured
- [ ] Validation tests passed
- [ ] Backup/disaster recovery plan

---

*Environment & Secrets Setup - Complete. Proceed to Kubernetes deployment.*
