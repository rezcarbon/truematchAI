# 🚀 Render Disk Implementation Guide

**Status**: Foundation Complete ✅  
**Next Phase**: Update File Upload Endpoints  
**Commit**: 2202b5e

---

## ✅ What's Been Done

### 1. **FileStorage Service Created** ✅
- **File**: `backend/app/services/storage.py` (520 lines)
- **Features**:
  - `save_file()` - Upload files to `/var/data/{category}/{user_id}/`
  - `get_file()` - Read file from disk (async)
  - `delete_file()` - Delete file from disk
  - `exists()` - Check if file exists
  - `check_disk_health()` - Monitor disk usage
  - **Security**: Path traversal prevention built-in
  - **Performance**: Async I/O using aiofiles

### 2. **Render Disk Configured** ✅
- **File**: `render.yaml` updated
- **Mount Path**: `/var/data`
- **Size**: 10GB (sufficient for staging)
- **Cost**: $0.25/GB/month = $2.50/month
- **Persistence**: Survives service restarts

### 3. **Migration Plan Created** ✅
- **File**: `RENDER_DISK_MIGRATION_PLAN.md`
- **Contents**: Complete analysis of S3 usage, code changes needed, cost comparison

### 4. **AWS Variables Removed** ✅
- **From**: `backend/.env.staging`
- **Removed**: All AWS_* and S3_* variables
- **Result**: Clean Render-only environment

---

## 📋 What Still Needs to Be Done

### Phase 1: Update File Upload Endpoints (HIGH PRIORITY)

**Files to modify:**
1. `backend/app/api/v1/files.py` (Resume uploads)
2. `backend/app/api/v1/resume_upload.py` (Resume ingestion)
3. `backend/app/api/v1/uploads.py` (General uploads)

**Pattern to follow:**
```python
# OLD (S3 with boto3):
def _s3_client():
    return boto3.client("s3", ...)

@router.post("/resume")
async def upload_resume(file: UploadFile):
    s3 = _s3_client()
    s3.upload_fileobj(file, bucket, key)

# NEW (Render Disk):
from app.services.storage import get_storage

@router.post("/resume")
async def upload_resume(file: UploadFile):
    storage = get_storage(settings.render_disk_path)
    file_path = await storage.save_file("resumes", user.id, file)
    # Save file_path to database instead of S3 key
```

---

### Phase 2: Update Configuration

**File**: `backend/app/config.py`

**Changes needed:**
```python
# REMOVE these:
- aws_access_key_id: str
- aws_secret_access_key: str
- aws_region: str
- s3_bucket: str
- s3_kms_key_id: str
- def s3_enabled(self) -> bool
- def s3_configured(self) -> bool

# ADD this:
- render_disk_path: str = "/var/data"
- def storage_enabled(self) -> bool:
    return Path(self.render_disk_path).exists()
```

---

### Phase 3: Update Health Checks

**File**: `backend/app/core/health.py`

**Changes needed:**
```python
# REPLACE S3 check with:
async def check_storage() -> bool:
    """Check Render Disk availability"""
    from app.services.storage import get_storage
    storage = get_storage()
    health = await storage.check_disk_health()
    return health.get("available", False)

# In health endpoint:
"storage": await check_storage(),
```

---

### Phase 4: Update Config Validator

**File**: `backend/app/core/config_validator.py`

**Changes needed:**
```python
# REMOVE:
- def validate_s3_credentials(self)
- All S3-related validation

# ADD:
- def validate_storage(self):
    """Verify Render Disk path exists and is writable"""
    path = Path(self.settings.render_disk_path)
    if not path.exists():
        self.warnings.append(f"Storage path {path} does not exist")
    if not os.access(path, os.W_OK):
        self.errors.append(f"Storage path {path} is not writable")
```

---

### Phase 5: Update Background Workers (OPTIONAL)

**Files**:
- `backend/app/workers/file_ingestion.py`
- `backend/app/workers/render_reports.py`

**Note**: Only if these workers handle file operations. May not need changes if they just read from database.

---

### Phase 6: Remove boto3 from Dependencies

**File**: `backend/Dockerfile`

**Current**:
```dockerfile
pip install boto3>=1.34 aioboto3>=1.14 ...
```

**Change to**:
```dockerfile
# Remove boto3 and aioboto3
# Add aiofiles (already in list)
pip install aiofiles>=23.0 ...
```

---

### Phase 7: Email Service (OPTIONAL - SEPARATE TASK)

**Files**: 
- `backend/app/core/email_service.py`
- `backend/app/services/email_service.py`

**Current**: Uses AWS SES via boto3  
**Options**:
1. **Keep boto3** for email (needs AWS credentials)
2. **Use SMTP** with Gmail/SendGrid (no AWS needed)
3. **Disable email** in staging (mock mode)

**Recommendation**: Use SMTP with SendGrid or Gmail

---

## 🎯 Implementation Checklist

### Must Do (Core Storage)
- [ ] Verify `backend/app/services/storage.py` compiles without errors
- [ ] Update `backend/app/api/v1/files.py` to use FileStorage
- [ ] Update `backend/app/api/v1/resume_upload.py` to use FileStorage
- [ ] Update `backend/app/api/v1/uploads.py` to use FileStorage
- [ ] Update `backend/app/config.py` (remove AWS, add render_disk_path)
- [ ] Update `backend/app/core/health.py` (storage check)
- [ ] Update `backend/app/core/config_validator.py` (remove S3 validation)
- [ ] Verify Dockerfile doesn't use boto3
- [ ] Test file uploads locally

### Should Do (Completeness)
- [ ] Update `backend/app/workers/file_ingestion.py`
- [ ] Update `backend/app/workers/render_reports.py`
- [ ] Update email service (SES → SMTP or mock)

### Nice to Have
- [ ] Add backup job for disk data
- [ ] Add monitoring for disk usage
- [ ] Add cleanup job for old files

---

## 📊 Code Changes Summary

| File | Type | Changes |
|------|------|---------|
| `services/storage.py` | NEW | Complete storage abstraction (520 LOC) |
| `api/v1/files.py` | UPDATE | Replace boto3 S3 with FileStorage |
| `api/v1/resume_upload.py` | UPDATE | Replace boto3 S3 with FileStorage |
| `api/v1/uploads.py` | UPDATE | Replace boto3 S3 with FileStorage |
| `config.py` | UPDATE | Remove AWS vars, add render_disk_path |
| `core/health.py` | UPDATE | S3 check → disk health check |
| `core/config_validator.py` | UPDATE | Remove S3 validation |
| `Dockerfile` | UPDATE | Remove boto3/aioboto3 |
| `render.yaml` | DONE ✅ | Disk configured |

**Total files to update**: 8 core files  
**Estimated time**: 2-3 hours for complete migration

---

## 🚀 Testing Strategy

### Unit Tests
```python
# Test save_file
async def test_save_file():
    storage = FileStorage("/tmp/test")
    file = UploadFile(filename="test.pdf")
    path = await storage.save_file("resumes", "user123", file)
    assert path.startswith("resumes/user123/")

# Test get_file
async def test_get_file():
    storage = FileStorage("/tmp/test")
    content = await storage.get_file(path)
    assert content is not None

# Test security (path traversal prevention)
async def test_path_traversal():
    storage = FileStorage("/var/data")
    with pytest.raises(FileStorageError):
        await storage.get_file("../../etc/passwd")
```

### Integration Tests
1. Upload file via API → verify it's on disk
2. Download file via API → verify content matches
3. Delete file via API → verify it's removed
4. Check disk health → verify usage stats

### Render Deployment Test
1. Deploy to Render with disk attached
2. Upload file via API
3. Restart service
4. Verify file still exists (persistence)
5. Check disk usage in Render dashboard

---

## 💡 Key Points to Remember

### Path Storage
- Store **relative paths** in database (e.g., `resumes/user123/uuid-file.pdf`)
- Never store absolute paths (changes if mount path changes)
- Never store URLs (use relative paths for flexibility)

### Async Operations
- Use `aiofiles` for async file I/O
- Never use sync file operations in async endpoints
- Fallback to sync if `aiofiles` not available

### Security
- All paths are resolved and checked to prevent directory traversal
- Validate user_id to prevent accessing other users' files
- Use UUID in filenames to prevent guessing

### Persistence
- Files survive service restarts (stored on Render Disk)
- Don't rely on ephemeral/tmp directories
- Always use `/var/data` (configured in render.yaml)

---

## 🆘 Troubleshooting

### "Directory doesn't exist"
```python
# The directory will be created automatically by _ensure_directory()
# If it fails, check /var/data mount permissions
```

### "Permission denied"
```python
# Check Render Disk is properly mounted
# Verify Render service has write access to /var/data
```

### "File not found after restart"
```python
# Verify disk is attached in Render Dashboard
# Check file path in database is relative path, not absolute
```

### "Disk space running out"
```python
# Monitor with check_disk_health()
# Implement cleanup job for old files
# Or increase disk size in render.yaml (sizeGB: 20)
```

---

## ✨ Success Criteria

- ✅ All files upload to `/var/data/{category}/{user_id}/`
- ✅ No boto3 or AWS credentials in code
- ✅ Files persist across service restarts
- ✅ Disk health checks working
- ✅ Tests passing (unit + integration)
- ✅ Render deployment successful
- ✅ Zero AWS dependencies
- ✅ Cost reduced to ~$9.50/month

---

## 📞 Next Steps

1. **Review** this implementation guide
2. **Update** the 8 files listed above
3. **Test** locally with mock FileStorage
4. **Deploy** to Render
5. **Verify** persistence across restarts
6. **Monitor** disk usage

**Start with**: `backend/app/api/v1/files.py` - it's the main upload endpoint

---

**Prepared by**: Claude Haiku 4.5  
**Date**: 2026-10-10  
**Status**: Ready for Implementation
