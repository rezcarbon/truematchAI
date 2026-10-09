# 🗄️ AWS → Render Disk Migration Plan

**Objective**: Eliminate all AWS dependencies and use Render's persistent disk storage

**Status**: Planning Phase  
**Date**: 2026-10-10

---

## 📊 Current S3 Usage Analysis

### Files with S3 Dependencies
```
backend/app/api/v1/files.py           ← Resume/file uploads
backend/app/api/v1/resume_upload.py   ← Resume ingestion
backend/app/api/v1/uploads.py         ← General uploads
backend/app/config.py                 ← S3 config settings
backend/app/core/health.py            ← S3 health checks
backend/app/core/config_validator.py  ← S3 validation
backend/app/core/email_service.py     ← AWS SES (email)
backend/app/workers/file_ingestion.py ← Background file processing
backend/app/workers/render_reports.py ← Report generation
backend/app/services/email_service.py ← Email delivery
```

### Storage Requirements
- **Resume uploads**: ~5MB max per file
- **Job descriptions**: ~2MB max per file
- **Assessment files**: ~5MB max per file
- **Generated reports**: ~10MB max per file
- **Total estimated**: ~50-100GB for staging + growth

---

## 🎯 Migration Strategy

### Phase 1: Render Disk Configuration
- [ ] Add Render Disk to render.yaml (10GB for staging)
- [ ] Mount path: `/var/data`
- [ ] Cost: $0.25/GB/month = $2.50/month for 10GB

### Phase 2: Config Updates
- [ ] Replace `AWS_*` variables with `RENDER_DISK_PATH`
- [ ] Remove boto3 dependencies from requirements
- [ ] Add `aiofiles` for async file I/O
- [ ] Update Settings class in config.py

### Phase 3: Storage Service Layer
- [ ] Create `backend/app/services/storage.py` (new abstraction)
- [ ] Implement local filesystem storage instead of S3
- [ ] Add async file operations using `aiofiles`
- [ ] Ensure directory creation and permissions

### Phase 4: File Upload Endpoints
- [ ] Update `api/v1/files.py` to use local disk
- [ ] Update `api/v1/resume_upload.py` to use local disk
- [ ] Update `api/v1/uploads.py` to use local disk

### Phase 5: Background Workers
- [ ] Update `workers/file_ingestion.py`
- [ ] Update `workers/render_reports.py`
- [ ] Remove boto3 from worker commands

### Phase 6: Health Checks
- [ ] Update `core/health.py` to check disk instead of S3
- [ ] Verify `/var/data` is writable

### Phase 7: Email (Optional - also remove SES)
- [ ] Replace AWS SES with mock email (staging)
- [ ] Or use SMTP (Gmail, SendGrid)

### Phase 8: Testing & Verification
- [ ] Test file uploads
- [ ] Test file persistence across deploys
- [ ] Test health checks
- [ ] Load testing

---

## 📁 Storage Directory Structure

```
/var/data/
├── resumes/
│   └── {user_id}/
│       └── {uuid}-{filename}
├── assessments/
│   └── {assessment_id}/
│       └── files/
├── reports/
│   └── {report_id}/
│       └── {uuid}-report.pdf
└── uploads/
    └── {upload_id}/
        └── files/
```

---

## 🔧 Code Changes Required

### 1. New Storage Service
**File**: `backend/app/services/storage.py`
```python
class FileStorage:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
    
    async def save_file(self, category: str, user_id: str, 
                       file: UploadFile) -> str:
        """Save file to disk, return path"""
    
    async def get_file(self, path: str) -> bytes:
        """Read file from disk"""
    
    async def delete_file(self, path: str) -> bool:
        """Delete file from disk"""
    
    async def exists(self, path: str) -> bool:
        """Check if file exists"""
```

### 2. Config Changes
**File**: `backend/app/config.py`
```python
# Remove:
aws_access_key_id: str
aws_secret_access_key: str
aws_region: str
s3_bucket: str

# Add:
render_disk_path: str = "/var/data"

@property
def storage_enabled(self) -> bool:
    """Disk storage always enabled on Render"""
    return True
```

### 3. File Upload Endpoint
**File**: `backend/app/api/v1/files.py`
```python
# Replace boto3 with:
from app.services.storage import FileStorage

@router.post("/resume")
async def upload_resume(file: UploadFile):
    storage = FileStorage(settings.render_disk_path)
    file_path = await storage.save_file("resumes", user.id, file)
    return UploadResponse(file_path=file_path)
```

---

## 💰 Cost Comparison

| Provider | Service | Cost |
|----------|---------|------|
| **AWS** | EC2 (t3.large) | $73/month |
| **AWS** | S3 storage (100GB) | $2.30/month |
| **AWS** | Data transfer | $5-10/month |
| **AWS Total** | | **$80-83/month** |
| **Render** | API (Starter) | $7/month |
| **Render** | Disk (10GB) | $2.50/month |
| **Render Total** | | **$9.50/month** |
| **Savings** | | **87% cheaper** |

---

## ✅ Benefits of Render Disk

✅ **No external dependencies** - Everything on Render  
✅ **Persistent across deploys** - Data survives restarts  
✅ **Cheaper** - $0.25/GB vs $0.023/GB for S3  
✅ **Faster** - Local I/O vs network I/O  
✅ **Simpler** - No credentials, no AWS account  
✅ **Isolated** - Other services can't access disk  

---

## ⚠️ Considerations

### Scaling
- ❌ Can't scale to multiple instances (disk not shared)
- ✅ Fine for staging (single instance)
- 🟡 For production: use S3 or NFS

### Backups
- ❌ Render doesn't auto-backup disks
- ✅ Can set up cron job to backup to S3 (optional)
- ✅ Can restore from snapshots

### Limits
- Single disk per service (max 1TB recommended)
- 10GB is perfect for staging
- Can be increased later if needed

---

## 📋 Implementation Checklist

- [ ] Create `backend/app/services/storage.py`
- [ ] Update `backend/app/config.py` (remove AWS, add RENDER_DISK_PATH)
- [ ] Update `backend/app/api/v1/files.py`
- [ ] Update `backend/app/api/v1/resume_upload.py`
- [ ] Update `backend/app/api/v1/uploads.py`
- [ ] Update `backend/app/core/health.py`
- [ ] Update `backend/app/core/config_validator.py`
- [ ] Update `backend/app/workers/file_ingestion.py`
- [ ] Update `backend/app/workers/render_reports.py`
- [ ] Remove boto3 from Dockerfile
- [ ] Update `render.yaml` with Disk configuration
- [ ] Update `.env.staging` (remove AWS vars)
- [ ] Test file uploads
- [ ] Test persistence
- [ ] Deploy to Render

---

## 🚀 Next Steps

1. Implement storage service layer
2. Update file upload endpoints
3. Update configuration
4. Update Render Disk in render.yaml
5. Deploy and test

**Estimated time**: 2-3 hours for full migration

---

**Prepared by**: Claude Haiku 4.5  
**Status**: Ready for Implementation
