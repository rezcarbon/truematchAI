# Tier 4 Optional Features - Development Plan

**Date:** June 9, 2026  
**Objective:** Develop optional features to 85%+ completion

---

## 🎯 TIER 4 FEATURE BREAKDOWN

### 1. FILE SYSTEM MONITORING (Current: 50%)

**What It Does:**
- Monitors CV and JD folders for new files
- Automatically extracts text from PDFs, DOCXs
- Creates ingest queue items for processing
- Tracks file hashes to prevent duplicates

**Current Status:**
- ❌ Watchdog module missing (FIXED with pip install)
- ❌ File event handler needs testing
- ❌ Document extraction needs verification
- ❌ Queue integration needs validation

**To Complete (85%):**
1. ✅ Install watchdog (DONE)
2. ✅ Fix import errors (DONE)
3. [ ] Verify file detection works
4. [ ] Test text extraction
5. [ ] Validate queue creation
6. [ ] Handle edge cases

**Estimated Effort:** 1-2 hours
**Target Completion:** 85%

---

### 2. EMAIL INGESTION (Current: 40%)

**What It Does:**
- Polls email inbox for new messages
- Extracts CV/JD attachments
- Automatically classifies documents
- Creates ingest queue items

**Current Status:**
- ❌ IMAP polling not working
- ❌ Email attachment extraction failing
- ❌ Type detection broken
- ❌ Queue integration incomplete

**To Complete (80%):**
1. [ ] Fix IMAP connection handling
2. [ ] Implement attachment extraction
3. [ ] Add type detection logic
4. [ ] Validate queue integration
5. [ ] Handle error cases
6. [ ] Test with mock emails

**Estimated Effort:** 2-3 hours
**Target Completion:** 80%

---

### 3. BATCH OPERATIONS (Current: 85%)

**What It Does:**
- Bulk user creation
- Batch job submission
- Batch result processing

**Current Status:**
- ✅ 85% working
- ⚠️ Minor edge cases
- ⚠️ Performance optimization needed

**To Complete (95%):**
1. [ ] Test with 1000+ users
2. [ ] Verify bulk operations
3. [ ] Handle failures gracefully
4. [ ] Optimize performance
5. [ ] Add progress tracking

**Estimated Effort:** 1-2 hours
**Target Completion:** 95%

---

### 4. ADVANCED ANALYTICS (Current: 80%)

**What It Does:**
- Tracks system metrics
- Calculates uptime
- Computes success rates
- Generates reports

**Current Status:**
- ✅ 80% working
- ⚠️ Some edge cases
- ⚠️ Report generation incomplete

**To Complete (95%):**
1. [ ] Verify metric calculations
2. [ ] Test report generation
3. [ ] Handle time zone issues
4. [ ] Add filtering options
5. [ ] Optimize queries

**Estimated Effort:** 1-2 hours
**Target Completion:** 95%

---

## 📋 DEVELOPMENT PRIORITIES

### Phase 1: Fix Critical Imports (15 min)
✅ Install watchdog
✅ Verify imports working
⏳ Run test suite

### Phase 2: File System Monitoring (1-2 hours)
- [ ] Fix file detection
- [ ] Verify text extraction
- [ ] Test queue integration
- [ ] Handle errors

### Phase 3: Email Ingestion (2-3 hours)
- [ ] Fix IMAP polling
- [ ] Implement attachment extraction
- [ ] Add type detection
- [ ] Validate queue integration

### Phase 4: Polish & Test (1-2 hours)
- [ ] Run full test suite
- [ ] Fix remaining issues
- [ ] Verify all tests pass
- [ ] Document changes

---

## 🎯 SUCCESS CRITERIA

### File System Monitoring
- ✅ Detects new CV files
- ✅ Detects new JD files
- ✅ Extracts text correctly
- ✅ Creates queue items
- ✅ Prevents duplicates
- ✅ Handles errors gracefully

### Email Ingestion
- ✅ Connects to IMAP
- ✅ Reads new emails
- ✅ Extracts attachments
- ✅ Detects file types
- ✅ Creates queue items
- ✅ Handles errors gracefully

### Batch Operations
- ✅ Creates 1000+ users
- ✅ Processes bulk jobs
- ✅ Tracks progress
- ✅ Handles failures
- ✅ Returns results

### Advanced Analytics
- ✅ Calculates metrics
- ✅ Generates reports
- ✅ Filters by date range
- ✅ Handles time zones
- ✅ Optimized queries

---

## 📊 EXPECTED OUTCOMES

### After Phase 1 (Watchdog Install)
- ✅ File system monitoring tests run
- ✅ Email ingestion tests run
- ✅ Import errors resolved

### After Phase 2 (File System)
- ✅ 85% file monitoring feature complete
- ✅ File detection working
- ✅ Text extraction working
- ✅ 8-12 tests passing

### After Phase 3 (Email)
- ✅ 80% email ingestion feature complete
- ✅ IMAP connection working
- ✅ Attachment extraction working
- ✅ Type detection working
- ✅ 12-16 tests passing

### After Phase 4 (Completion)
- ✅ Overall test pass rate: 82%+
- ✅ Tier 4 features: 85%+ ready
- ✅ Zero critical errors
- ✅ All blockers removed

---

## 📈 TEST PASS RATE TARGETS

| Phase | Expected Pass Rate | Target |
|-------|-------------------|--------|
| Initial | 77.96% | Current |
| Phase 1 | 78.5% | +5 tests |
| Phase 2 | 80% | +12 tests |
| Phase 3 | 82% | +16 tests |
| Phase 4 | 85%+ | Polish |

---

## 🔧 TECHNICAL DETAILS

### File System Monitoring Tech Stack
- watchdog (file system monitoring) - ✅ INSTALLING
- aiofiles (async file I/O) - ✅ INSTALLED
- pypdf/python-docx (document extraction)
- asyncio (async task processing)

### Email Ingestion Tech Stack
- imaplib (IMAP protocol)
- email (email parsing)
- asyncio (async polling)
- aiofiles (async file handling)

### Batch Operations Tech Stack
- SQLAlchemy bulk operations
- asyncio concurrency
- Progress tracking
- Error recovery

### Advanced Analytics Tech Stack
- SQLAlchemy aggregation
- Pandas (optional)
- Date/time utilities
- Report generation

---

## 📝 NEXT STEPS

1. ✅ Install watchdog (DONE)
2. ⏳ Run full test suite to measure impact
3. [ ] Fix file system monitoring issues
4. [ ] Fix email ingestion issues
5. [ ] Polish batch operations
6. [ ] Complete analytics features
7. [ ] Verify 85%+ test pass rate

---

**Status:** Phase 1 Complete (Watchdog installed)  
**Next:** Awaiting full test suite results

