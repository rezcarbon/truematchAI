# AWS Kubernetes Deployment Guide
## TrueMatch AI - EKS Cluster Setup & Application Deployment

**Version:** 1.0  
**Last Updated:** July 21, 2026  

---

## 1. EKS Cluster Creation

### 1.1 Create Cluster with eksctl

```bash
# Create cluster configuration file
cat > truematch-cluster.yaml << 'EOF'
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: truematch-prod
  region: us-east-1
  version: "1.29"

vpc:
  cidr: 10.0.0.0/16
  nat:
    gateway: Auto  # One NAT gateway per AZ
  clusterEndpoints:
    publicAccess: true
    privateAccess: true

nodeGroups:
  - name: core-nodes
    desiredCapacity: 3
    minSize: 3
    maxSize: 10
    instanceType: m5.large
    ssh:
      enable: false  # Disable SSH for security
    labels:
      workload: general
    taints: []
    
  - name: compute-nodes
    desiredCapacity: 2
    minSize: 1
    maxSize: 20
    instanceType: c5.xlarge
    ssh:
      enable: false
    labels:
      workload: compute
    taints:
      - key: compute
        value: "true"
        effect: NoSchedule

addons:
  - name: vpc-cni
    attachPolicyARNs:
      - arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy
  - name: coredns
  - name: kube-proxy
  - name: ebs-csi-driver
    attachPolicyARNs:
      - arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverRole

iamWithOIDC: true

cloudWatch:
  clusterLogging:
    enableTypes:
      - api
      - audit
      - authenticator
      - controllerManager
      - scheduler
EOF

# Create cluster
eksctl create cluster -f truematch-cluster.yaml

# This will take 15-20 minutes
# Monitor progress:
# AWS Console → EKS → Clusters → truematch-prod
```

### 1.2 Verify Cluster Creation

```bash
# Get cluster info
aws eks describe-cluster \
  --name truematch-prod \
  --region us-east-1

# Update kubeconfig
aws eks update-kubeconfig \
  --name truematch-prod \
  --region us-east-1

# Verify kubectl access
kubectl cluster-info
kubectl get nodes
kubectl get pods --all-namespaces
```

---

## 2. Kubernetes Add-ons & Controllers

### 2.1 Install NGINX Ingress Controller

```bash
# Add Helm repo
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Install NGINX ingress
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --values - << 'EOF'
controller:
  service:
    type: LoadBalancer
    externalTrafficPolicy: Local
  
  resources:
    requests:
      cpu: 100m
      memory: 90Mi
    limits:
      cpu: 500m
      memory: 512Mi
  
  config:
    log-format: '{"timestamp":"$time_iso8601","client":"$remote_addr","method":"$request_method","uri":"$request_uri","status":$status,"bytes":$bytes_sent,"duration":$request_time}'
    enable-modsecurity: "true"
    enable-owasp-core-rules: "true"
EOF

# Get ALB DNS name
kubectl get svc -n ingress-nginx
# Save the EXTERNAL-IP (this is your ALB)
```

### 2.2 Install cert-manager

```bash
# Add Helm repo
helm repo add jetstack https://charts.jetstack.io
helm repo update

# Install cert-manager
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true \
  --set global.leaderElection.namespace=cert-manager

# Verify installation
kubectl get pods -n cert-manager
kubectl get crds | grep certmanager
```

### 2.3 Install External Secrets Operator (Optional)

```bash
# Add Helm repo
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

# Install External Secrets
helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets-system \
  --create-namespace \
  --set installCRDs=true

# Verify
kubectl get pods -n external-secrets-system
```

### 2.4 Install Prometheus & Monitoring Stack

```bash
# Add Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values - << 'EOF'
prometheus:
  prometheusSpec:
    retention: 30d
    resources:
      requests:
        cpu: 500m
        memory: 512Mi
      limits:
        cpu: 1000m
        memory: 1Gi
    
    serviceMonitorSelectorNilUsesHelmValues: false
    podMonitorSelectorNilUsesHelmValues: false

grafana:
  adminPassword: CHANGE_ME
  persistence:
    enabled: true
    size: 10Gi

alertmanager:
  enabled: true
  alertmanagerSpec:
    retention: 7d
EOF

# Access Prometheus
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
# http://localhost:9090

# Access Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# http://localhost:3000 (admin/CHANGE_ME)
```

---

## 3. VPC & Networking Configuration

### 3.1 Create Application VPC (if not using eksctl default)

```bash
# Get VPC info created by eksctl
aws ec2 describe-vpcs \
  --filters "Name=tag:Name,Values=eksctl-truematch-prod-cluster/VPC" \
  --region us-east-1

# Get subnets
aws ec2 describe-subnets \
  --filters "Name=tag-key,Values=eksctl.io/cluster-name" \
  --region us-east-1
```

### 3.2 Configure Security Groups

```bash
# Get current security groups
aws ec2 describe-security-groups \
  --filters "Name=tag:eks:cluster-name,Values=truematch-prod" \
  --region us-east-1

# Add inbound rules for database
aws ec2 authorize-security-group-ingress \
  --group-id sg-XXXXXXXX \
  --protocol tcp \
  --port 5432 \
  --source-security-group-id sg-XXXXXXXX \
  --region us-east-1

# Add inbound rules for Redis
aws ec2 authorize-security-group-ingress \
  --group-id sg-XXXXXXXX \
  --protocol tcp \
  --port 6379 \
  --source-security-group-id sg-XXXXXXXX \
  --region us-east-1
```

### 3.3 Configure Network Policies

Network policies are included in k8s/08-ingress.yaml

```bash
# Apply network policies
kubectl apply -f k8s/08-ingress.yaml

# Verify policies
kubectl get networkpolicies -n truematch
kubectl describe networkpolicy api-network-policy -n truematch
```

---

## 4. Database & Cache Setup

### 4.1 Create RDS PostgreSQL

```bash
# Create security group for RDS
DB_SG=$(aws ec2 create-security-group \
  --group-name truematch-db \
  --description "TrueMatch PostgreSQL RDS" \
  --vpc-id vpc-XXXXXXXX \
  --region us-east-1 \
  --query 'GroupId' --output text)

# Allow access from EKS nodes
EKS_SG=$(aws ec2 describe-security-groups \
  --filters "Name=tag:eks:cluster-name,Values=truematch-prod" \
  --query 'SecurityGroups[0].GroupId' --output text \
  --region us-east-1)

aws ec2 authorize-security-group-ingress \
  --group-id $DB_SG \
  --protocol tcp \
  --port 5432 \
  --source-security-group-id $EKS_SG \
  --region us-east-1

# Create DB subnet group
SUBNETS=$(aws ec2 describe-subnets \
  --filters "Name=tag-key,Values=eksctl.io/cluster-name" \
  --region us-east-1 \
  --query 'Subnets[].SubnetId' --output text)

aws rds create-db-subnet-group \
  --db-subnet-group-name truematch-db-subnet \
  --db-subnet-group-description "TrueMatch RDS subnet group" \
  --subnet-ids $SUBNETS \
  --region us-east-1

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier truematch-prod \
  --db-instance-class db.t3.large \
  --engine postgres \
  --engine-version 15.3 \
  --master-username truematch \
  --master-user-password "STRONG_PASSWORD" \
  --allocated-storage 100 \
  --db-name truematch \
  --vpc-security-group-ids $DB_SG \
  --db-subnet-group-name truematch-db-subnet \
  --multi-az \
  --storage-encrypted \
  --storage-type gp3 \
  --backup-retention-period 30 \
  --publicly-accessible false \
  --enable-iam-database-authentication \
  --enable-cloudwatch-logs-exports postgresql \
  --region us-east-1

# Wait for instance to be available (5-10 minutes)
aws rds wait db-instance-available \
  --db-instance-identifier truematch-prod \
  --region us-east-1

# Get RDS endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier truematch-prod \
  --region us-east-1 \
  --query 'DBInstances[0].Endpoint.Address' --output text)

echo "RDS Endpoint: $RDS_ENDPOINT"
```

### 4.2 Create ElastiCache Redis

```bash
# Create security group for Redis
REDIS_SG=$(aws ec2 create-security-group \
  --group-name truematch-redis \
  --description "TrueMatch ElastiCache Redis" \
  --vpc-id vpc-XXXXXXXX \
  --region us-east-1 \
  --query 'GroupId' --output text)

# Allow access from EKS
aws ec2 authorize-security-group-ingress \
  --group-id $REDIS_SG \
  --protocol tcp \
  --port 6379 \
  --source-security-group-id $EKS_SG \
  --region us-east-1

# Create cache subnet group
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name truematch-redis-subnet \
  --cache-subnet-group-description "TrueMatch Redis subnet group" \
  --subnet-ids $SUBNETS \
  --region us-east-1

# Create Redis cluster
aws elasticache create-replication-group \
  --replication-group-id truematch-redis \
  --replication-group-description "TrueMatch Redis" \
  --engine redis \
  --engine-version 7.0 \
  --cache-node-type cache.r6g.large \
  --num-cache-clusters 2 \
  --automatic-failover-enabled \
  --multi-az \
  --cache-subnet-group-name truematch-redis-subnet \
  --vpc-security-group-ids $REDIS_SG \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled \
  --auth-token "STRONG_REDIS_PASSWORD" \
  --auto-minor-version-upgrade false \
  --region us-east-1

# Wait for cluster to be available
sleep 30
REDIS_ENDPOINT=$(aws elasticache describe-replication-groups \
  --replication-group-id truematch-redis \
  --region us-east-1 \
  --query 'ReplicationGroups[0].PrimaryEndpoint.Address' --output text)

echo "Redis Endpoint: $REDIS_ENDPOINT"
```

---

## 5. Deploy Application to Kubernetes

### 5.1 Prepare Kubernetes Manifests

Update `k8s/02-config.yaml` with production values:

```bash
# Update database and Redis hosts
sed -i 's/DATABASE_HOST: "postgres"/DATABASE_HOST: "'"$RDS_ENDPOINT"'"/' k8s/02-config.yaml
sed -i 's/REDIS_HOST: "redis"/REDIS_HOST: "'"$REDIS_ENDPOINT"'"/' k8s/02-config.yaml

# Update image URI
sed -i 's|image: truematch-api:latest|image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/truematch-api:v1.2.3|g' k8s/*.yaml
```

### 5.2 Apply Kubernetes Manifests

```bash
# Apply in order
kubectl apply -f k8s/01-namespace.yaml
kubectl apply -f k8s/02-config.yaml
kubectl apply -f k8s/03-postgres.yaml  # Optional: if using k8s-managed DB
kubectl apply -f k8s/04-redis.yaml     # Optional: if using k8s-managed Redis
kubectl apply -f k8s/05-migration.yaml

# Wait for migration to complete
kubectl wait --for=condition=complete job/db-migrate -n truematch --timeout=300s

# Apply remaining manifests
kubectl apply -f k8s/06-api.yaml
kubectl apply -f k8s/07-workers.yaml
kubectl apply -f k8s/07-beat.yaml
kubectl apply -f k8s/08-ingress.yaml
kubectl apply -f k8s/09-monitoring.yaml
kubectl apply -f k8s/10-backup.yaml
```

### 5.3 Verify Deployment

```bash
# Check pods are running
kubectl get pods -n truematch
# Should show: api (3), worker (3+), beat (1), postgres/redis (if k8s-managed)

# Check services
kubectl get svc -n truematch

# Check ingress
kubectl get ingress -n truematch

# Check certificate
kubectl get certificate -n truematch
kubectl describe certificate truematch-cert -n truematch

# Watch pod startup
kubectl logs -f deployment/api -n truematch
kubectl logs -f job/db-migrate -n truematch
```

---

## 6. DNS & Ingress Configuration

### 6.1 Get ALB DNS Name

```bash
# Get ALB/NLB DNS name
ALB_DNS=$(kubectl get svc -n ingress-nginx nginx-ingress-ingress-nginx \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo "ALB DNS: $ALB_DNS"
# Output: abcd1234-ingress.elb.us-east-1.amazonaws.com
```

### 6.2 Update Route53 DNS Records

```bash
# Create/update DNS record in Route53
HOSTED_ZONE_ID="Z1234567890ABC"  # Your hosted zone ID
DOMAIN="api.truematch.digital"

aws route53 change-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "'$DOMAIN'",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "'$ALB_DNS'"}]
      }
    }]
  }'

# Verify DNS resolution
nslookup api.truematch.digital
# Should resolve to ALB DNS name
```

### 6.3 Verify HTTPS Certificate

```bash
# Wait for certificate to be issued (usually 1-2 minutes)
kubectl wait --for=condition=ready certificate/truematch-cert \
  -n truematch --timeout=300s

# Check certificate details
kubectl describe certificate truematch-cert -n truematch
kubectl get secret truematch-tls -n truematch -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -text -noout

# Test HTTPS
curl -I https://api.truematch.digital/livez
```

---

## 7. Health Check & Validation

### 7.1 Check Pod Health

```bash
# Check API pod health
kubectl exec deployment/api -n truematch -- curl -s http://localhost:8000/livez
# Expected output: {"status": "ok"}

# Check readiness
kubectl exec deployment/api -n truematch -- curl -s http://localhost:8000/readyz

# Check database connectivity
kubectl exec deployment/api -n truematch -- python -c \
  "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); print(engine.execute('SELECT 1'))"

# Check Redis connectivity
kubectl exec deployment/api -n truematch -- redis-cli -h $REDIS_ENDPOINT ping
# Expected output: PONG
```

### 7.2 Check Service Endpoints

```bash
# List service endpoints
kubectl get endpoints -n truematch

# Check ingress backends
kubectl describe ingress api-ingress -n truematch

# Test API endpoint
curl -I https://api.truematch.digital/
curl https://api.truematch.digital/docs
```

### 7.3 Monitor Logs

```bash
# View API logs
kubectl logs -f deployment/api -n truematch -c api

# View worker logs
kubectl logs -f deployment/worker -n truematch -c worker

# View all logs
kubectl logs --all-containers=true -f -n truematch --tail=50

# Search for errors
kubectl logs -n truematch --all-containers=true | grep ERROR
```

---

## 8. Auto-Scaling Configuration

### 8.1 Metrics Server (for HPA)

```bash
# Install metrics-server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verify
kubectl get deployment metrics-server -n kube-system
kubectl top nodes
kubectl top pods -n truematch
```

### 8.2 Verify HPA

```bash
# Check HPA status
kubectl get hpa -n truematch

# Describe HPA
kubectl describe hpa worker-hpa -n truematch

# Watch HPA in action (during load)
kubectl get hpa -n truematch -w
```

---

## 9. Backup & Disaster Recovery

### 9.1 Test Database Backups

```bash
# Create manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier truematch-prod \
  --db-snapshot-identifier truematch-backup-$(date +%Y%m%d-%H%M%S) \
  --region us-east-1

# List snapshots
aws rds describe-db-snapshots \
  --db-instance-identifier truematch-prod \
  --region us-east-1

# Test restore (to different DB)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier truematch-test-restore \
  --db-snapshot-identifier truematch-backup-20260721-120000 \
  --region us-east-1
```

### 9.2 Test Redis Backups

```bash
# Create manual snapshot
aws elasticache create-snapshot \
  --replication-group-id truematch-redis \
  --snapshot-name truematch-redis-backup-$(date +%Y%m%d-%H%M%S) \
  --region us-east-1

# List snapshots
aws elasticache describe-snapshots \
  --replication-group-id truematch-redis \
  --region us-east-1
```

---

## 10. Monitoring & Alerting

### 10.1 View Prometheus Metrics

```bash
# Port-forward to Prometheus
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090

# Navigate to http://localhost:9090
# Query examples:
# - container_cpu_usage_seconds_total
# - container_memory_usage_bytes
# - http_requests_total
```

### 10.2 Create CloudWatch Alarms

```bash
# API uptime alarm
aws cloudwatch put-metric-alarm \
  --alarm-name truematch-api-unhealthy \
  --alarm-description "Alert if API pods are unhealthy" \
  --metric-name TargetResponseTime \
  --namespace AWS/ApplicationELB \
  --statistic Average \
  --period 60 \
  --threshold 1.0 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT:truematch-alerts

# Database CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name truematch-db-high-cpu \
  --alarm-description "Alert if RDS CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=DBInstanceIdentifier,Value=truematch-prod
```

---

## Checklist

- [ ] EKS cluster created and nodes healthy
- [ ] NGINX ingress controller installed
- [ ] cert-manager installed and certificates issued
- [ ] External Secrets Operator installed (optional)
- [ ] Prometheus/Grafana monitoring deployed
- [ ] RDS PostgreSQL created and accessible
- [ ] ElastiCache Redis created and accessible
- [ ] Kubernetes manifests deployed
- [ ] Database migrations completed successfully
- [ ] Pods are running and healthy
- [ ] Ingress routes working
- [ ] HTTPS certificate valid
- [ ] DNS records pointing to ALB
- [ ] Health checks responding
- [ ] HPA metrics available
- [ ] Monitoring dashboards accessible
- [ ] Backups configured and tested
- [ ] Alarms created and functional

---

*AWS Kubernetes Deployment - Complete. Proceed to deployment checklist.*
