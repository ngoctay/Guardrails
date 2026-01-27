# Guardrails - Critical Action Items & Implementation Plan

**Date:** January 28, 2026  
**Status:** Ready for Development  
**Total Estimated Effort:** 5-6 days to production-ready  

---

## 🔴 CRITICAL ISSUES (Must Fix - 2 days)

### Issue 1: No API Authentication ⚠️ SECURITY CRITICAL
**Severity:** 🔴 CRITICAL  
**Impact:** System is completely open to unauthorized access  
**Effort:** 1 day

**Current State:**
```python
# Anyone can call /api/analyze endpoint
@app.post("/api/analyze")
async def analyze_code(request: Request):  # No authentication
    # Process untrusted request
```

**What Needs to Be Done:**
- [ ] Add API key authentication
- [ ] Add rate limiting per API key
- [ ] Add request validation
- [ ] Document API key management
- [ ] Add API key rotation capability

**Implementation:**
```python
from fastapi.security import HTTPBearer
from fastapi import Depends

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthCredentials = Depends(security)):
    api_key = credentials.credentials
    if not validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

@app.post("/api/analyze")
async def analyze_code(request: Request, api_key: str = Depends(verify_api_key)):
    # Now authenticated
```

**Test Plan:**
- [ ] Test with valid API key - should work
- [ ] Test without API key - should get 401
- [ ] Test with invalid API key - should get 401
- [ ] Test rate limiting - should throttle after limit

---

### Issue 2: No Data Residency Configuration ⚠️ COMPLIANCE CRITICAL
**Severity:** 🔴 CRITICAL  
**Impact:** Cannot comply with GDPR, data residency laws  
**Effort:** 2 days

**Current State:**
```python
# Audit logs stored only in memory/local files
# No configurable storage backend
# No encryption at rest
```

**What Needs to Be Done:**
- [ ] Add database support (PostgreSQL/MySQL)
- [ ] Make storage backend configurable via environment
- [ ] Support multiple storage locations
- [ ] Add encryption at rest
- [ ] Add database migrations
- [ ] Document data residency options

**Implementation:**
```python
# New: backend/app/storage/storage_backends.py
from abc import ABC

class StorageBackend(ABC):
    def store_event(self, event: AuditEvent): pass
    def retrieve_events(self, filters): pass

class PostgreSQLBackend(StorageBackend):
    def __init__(self, connection_string):
        self.conn = psycopg2.connect(connection_string)
    
    def store_event(self, event):
        # Store in PostgreSQL

class FileSystemBackend(StorageBackend):
    def __init__(self, directory):
        self.dir = directory
    
    def store_event(self, event):
        # Store in configured directory
```

**Configuration:**
```bash
# .env
STORAGE_BACKEND=postgresql
DATABASE_URL=postgresql://user:pass@db-eu.example.com/guardrails
# OR
STORAGE_BACKEND=filesystem
STORAGE_DIR=/data/guardrails-logs  # Can be mounted to EU server
```

**Test Plan:**
- [ ] Test PostgreSQL storage
- [ ] Test filesystem storage
- [ ] Test EU-located database
- [ ] Verify audit logs encrypted
- [ ] Verify data doesn't leak to other storage

---

### Issue 3: LLM Integration Incomplete ⚠️ FUNCTIONALITY GAP
**Severity:** 🔴 CRITICAL  
**Impact:** AI review features don't work reliably  
**Effort:** 1 day

**Current State:**
```python
# Switched from OpenAI to Google Gemini
# But GOOGLE_API_KEY not documented
# Fallback to rule-based if not configured (user won't know)
# No error handling for API failures
```

**What Needs to Be Done:**
- [ ] Document GOOGLE_API_KEY setup requirement
- [ ] Add support for both OpenAI and Gemini
- [ ] Add proper error handling
- [ ] Add rate limiting for LLM calls
- [ ] Add logging for LLM usage
- [ ] Make LLM optional but clear

**Implementation:**
```python
class AIReviewer:
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "gemini")
        
        if self.provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                logger.warning("⚠️  OPENAI_API_KEY not set - using rule-based fallback")
            self.client = OpenAI(api_key=self.api_key)
            
        elif self.provider == "gemini":
            self.api_key = os.getenv("GOOGLE_API_KEY")
            if not self.api_key:
                logger.warning("⚠️  GOOGLE_API_KEY not set - using rule-based fallback")
            genai.configure(api_key=self.api_key)
```

**Documentation:**
```markdown
# AI Configuration

## Option 1: Google Gemini (Default)
```bash
export GOOGLE_API_KEY=your-api-key
export AI_PROVIDER=gemini
```

## Option 2: OpenAI
```bash
export OPENAI_API_KEY=your-api-key
export AI_PROVIDER=openai
```

## No AI (Fallback)
If no API keys configured, system uses rule-based suggestions only.
```

**Test Plan:**
- [ ] Test with OpenAI API key set
- [ ] Test with Google Gemini API key set
- [ ] Test with no API keys (should fall back gracefully)
- [ ] Test with invalid API key (should show error)
- [ ] Verify rate limiting works

---

### Issue 4: No Input Validation ⚠️ SECURITY GAP
**Severity:** 🔴 CRITICAL  
**Impact:** Malicious input could cause DoS or code injection  
**Effort:** 1 day

**Current State:**
```python
@app.post("/api/analyze")
async def analyze_code(request: Request):
    data = await request.json()
    # NO validation of data structure or content
    # Could receive malicious JSON
```

**What Needs to Be Done:**
- [ ] Validate request schema
- [ ] Limit file sizes
- [ ] Limit number of files
- [ ] Sanitize file paths
- [ ] Check for malicious content patterns
- [ ] Add request size limits

**Implementation:**
```python
from pydantic import BaseModel, validator

class AnalyzeRequest(BaseModel):
    repo_name: str  # Must be owner/repo format
    pr_number: int  # Must be positive
    commit_hash: str  # Must be valid hash
    files: dict  # Must not exceed 100 files
    
    @validator('repo_name')
    def validate_repo_name(cls, v):
        if not re.match(r'^[\w\-]+/[\w\-]+$', v):
            raise ValueError('Invalid repo name format')
        return v
    
    @validator('files')
    def validate_files(cls, v):
        if len(v) > 100:
            raise ValueError('Cannot analyze more than 100 files')
        for path, content in v.items():
            if len(content) > 1024*1024:  # 1MB per file
                raise ValueError(f'File {path} too large')
        return v

@app.post("/api/analyze")
async def analyze_code(request: AnalyzeRequest):
    # request is now validated
```

**Test Plan:**
- [ ] Test with valid request - should work
- [ ] Test with missing fields - should get 422
- [ ] Test with 101 files - should get 422
- [ ] Test with 10MB file - should get 422
- [ ] Test with invalid repo name - should get 422

---

### Issue 5: No Timeout Handling ⚠️ RELIABILITY GAP
**Severity:** 🔴 CRITICAL  
**Impact:** Large PRs could hang forever, blocking other requests  
**Effort:** 1 day

**Current State:**
```python
@app.post("/api/analyze")
async def analyze_code(request: Request):
    # No timeout - could hang forever on large PR
    # 10,000 file PR = hours of processing
```

**What Needs to Be Done:**
- [ ] Add analysis timeout (30-60 seconds)
- [ ] Add graceful timeout handling
- [ ] Return informative error on timeout
- [ ] Log timeout events
- [ ] Make timeout configurable

**Implementation:**
```python
import asyncio

ANALYSIS_TIMEOUT = int(os.getenv("ANALYSIS_TIMEOUT", 60))

@app.post("/api/analyze")
async def analyze_code(request: Request):
    try:
        async with asyncio.timeout(ANALYSIS_TIMEOUT):
            # Perform analysis
            result = await perform_analysis(...)
            return result
            
    except asyncio.TimeoutError:
        logger.warning(f"Analysis timed out after {ANALYSIS_TIMEOUT}s")
        return {
            "success": False,
            "error": "Analysis timed out",
            "message": "PR is too large for analysis",
            "suggestion": "Split PR into smaller commits",
            "timeout_seconds": ANALYSIS_TIMEOUT
        }
```

**Configuration:**
```bash
# .env
ANALYSIS_TIMEOUT=60  # seconds
```

**Test Plan:**
- [ ] Test normal PR completes before timeout
- [ ] Test large PR (1000 files) times out after 60s
- [ ] Verify error message is helpful
- [ ] Verify timeout is logged

---

## 🟠 IMPORTANT ISSUES (Should Fix - 3 days)

### Issue 6: No Distributed Caching
**Severity:** 🟠 HIGH  
**Impact:** Cache not shared across instances, poor scalability  
**Effort:** 2 days

**Solution:** Add Redis support
- [ ] Add Redis client
- [ ] Implement cache wrapper
- [ ] Update main.py to use distributed cache
- [ ] Add Redis configuration options

---

### Issue 7: No Custom Rule Pack Upload
**Severity:** 🟠 HIGH  
**Impact:** Users can't upload their own compliance packs  
**Effort:** 1 day

**Solution:** Add API endpoint
- [ ] Create upload endpoint: `POST /api/rule-packs/upload`
- [ ] Validate rule pack structure
- [ ] Store with versioning
- [ ] Return pack ID and version

---

### Issue 8: No Performance Analysis Rules
**Severity:** 🟠 HIGH  
**Impact:** Can't detect O(n²) loops, N+1 queries, etc.  
**Effort:** 2 days

**Solution:** Add performance pattern detection
- [ ] Create `backend/app/rules/performance_rules.py`
- [ ] Add patterns for common performance issues
- [ ] Map to OWASP guidelines
- [ ] Test with real code examples

---

## 📋 SUMMARY

### Status by Component

| Component | Status | Issue |
|-----------|--------|-------|
| Security Rules | ✅ Working | None |
| GitHub Integration | ✅ Working | Permissions (external) |
| Policy Engine | ✅ Working | None |
| Audit Logging | ⚠️ Partial | Needs DB storage |
| AI Review | ⚠️ Partial | LLM not documented |
| Rule Packs | ⚠️ Partial | No upload API |
| API Security | ❌ Missing | No authentication |
| Performance | ⚠️ Partial | No timeout, no distributed cache |

### Priority Matrix

```
HIGH IMPACT                         │    LOW IMPACT
HIGH EFFORT                         │
  • Data Residency Config           │    • Dashboard
  • Distributed Caching             │    • Auto-apply Fixes
  • Database Migrations             │    • Feedback System
                                    │
  • API Authentication        ✓ DO FIRST
  • Input Validation          ✓ DO FIRST
  • Timeout Handling          ✓ DO FIRST
  • LLM Documentation         ✓ DO FIRST
                                    │
LOW EFFORT                          │    • Copilot Detection Improve
  • Custom Rule Upload        ✓     │    • Performance Rules
  • Encryption at Rest        ✓     │    • False Positive Filter
                                    │
```

---

## 🚀 NEXT STEPS

### Week 1: Critical Issues (Mon-Tue)
1. Monday: API Authentication (1 day)
2. Tuesday: Input Validation (1 day)
3. Tuesday: Timeout Handling (same day as validation)

### Week 1: Critical Issues (Wed-Thu)
1. Wednesday: Data Residency (1 day)
2. Thursday: LLM Documentation & Setup (1 day)

### Week 2: Important Issues (Mon-Wed)
1. Monday: Custom Rule Pack Upload (1 day)
2. Tuesday-Wednesday: Distributed Caching (2 days)
3. Wednesday: Performance Rules (2 days, parallel)

### Week 2: Release
- Thursday: Testing & Bug Fixes
- Friday: v1.1.0 Release (Production-Ready)

---

## 📝 Testing Checklist Before Launch

- [ ] All 5 critical issues fixed and tested
- [ ] Load test with 1000+ files
- [ ] Load test with large file sizes (>10MB diffs)
- [ ] API authentication works with invalid keys
- [ ] Data storage configured and verified
- [ ] LLM integration documented and working
- [ ] Timeout handling tested
- [ ] Input validation tested with edge cases
- [ ] Audit logs stored and retrievable
- [ ] GitHub app still works after changes

---

**Status:** 🔴 BLOCKING LAUNCH  
**Action Required:** Implement all 5 critical issues  
**Estimated Time:** 2 days focused development  
**Target Launch:** Jan 30, 2026
