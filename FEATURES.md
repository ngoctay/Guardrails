# Guardrails: Minimal Working System

Enterprise-grade security guardrails for GitHub Copilot PRs. A hybrid platform that combines static analysis with GitHub integration to enforce security standards before code merge.

## ✨ Key Features Implemented

### 1. Secure Coding Guardrails ✅
- **Hardcoded Secrets Detection** - API keys, passwords, tokens, AWS credentials
- **SQL Injection Prevention** - String interpolation in SQL queries
- **Insecure Deserialization** - pickle.loads(), unsafe YAML
- **Unsafe Code Execution** - eval(), exec(), os.system()
- **Weak Cryptography** - MD5, SHA1, DES detection

**Compliance Mapping:**
- CWE IDs (e.g., CWE-798, CWE-89, CWE-502)
- OWASP Top 10 (e.g., A02:2021, A03:2021)

### 2. GitHub PR Integration ✅
- Automatic scanning on PR creation/update
- PR diffs automatically fetched
- Results posted as detailed PR comments
- Formatted with severity levels and icons
- Expandable details for each violation

### 3. Developer-Friendly Feedback ✅
- Violations grouped by severity (Critical → Info)
- Inline code snippets with context
- Suggested fixes (framework ready)
- Links to security standards
- Clear explanations of why it's an issue

### 4. Policy-Based Enforcement ✅
- **Advisory Mode** - Informational comments (default)
- **Warning Mode** - Blocks on critical (configurable)
- **Blocking Mode** - Prevents merge (can be overridden)
- Configuration via guardrails-config.yml

### 5. Enterprise Traceability ✅
- Unique scan IDs for each PR
- Audit trail in PR comments
- Violation counts and categorization
- Timestamp recording
- Severity level tracking

## 📊 Architecture

```
GitHub PR Event
        ↓
GitHub App (Probot/TypeScript)
        ↓
Fetches PR Diff
        ↓
FastAPI Backend (Python)
        ↓
Security Rules Engine
        ↓
Violation Detection
        ↓
Formatted PR Comment
```

## 🚀 What's Implemented

### Backend (FastAPI)

**Framework:** Python 3.11+ with FastAPI

**Endpoints:**
- `GET /health` - Health check
- `POST /api/analyze` - Analyze PR diffs for violations
- `GET /api/rules` - List available security rules

**Components:**
- Security rules engine with 5 built-in rules
- Diff parser (handles unified diff format)
- Violation models with CWE/OWASP mapping
- Policy configuration system
- Extensible analyzer architecture

**Features:**
- File type filtering (Python, JS/TS, Java, Go, etc.)
- Line-by-line analysis
- Regex-based pattern detection
- Severity classification
- Copilot-generated code detection (framework)

### GitHub App (TypeScript/Probot)

**Framework:** Probot (Node.js/TypeScript)

**Features:**
- Webhook listener for PR events
- Automatic diff fetching
- Backend API integration
- Markdown formatting
- Severity-based grouping
- Error handling & logging

**PR Comment Output:**
- Summary statistics
- Issues grouped by severity
- Expandable details per violation
- CWE/OWASP links
- Copilot flags
- Enforcement mode indicator

## 📁 Project Structure

```
guardrails/
├── backend/                          # FastAPI backend
│   ├── app/
│   │   ├── main.py                  # FastAPI app
│   │   ├── models/violation.py      # Data models
│   │   ├── rules/security_rules.py  # 5 security rules
│   │   ├── analyzers/code_analyzer.py # Diff parser
│   │   └── config/settings.py       # Configuration
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
├── guardrails-github-app/           # GitHub App
│   ├── src/index.ts                 # Probot app (130+ lines)
│   ├── app.yml                      # GitHub App manifest
│   ├── package.json
│   └── README.md
│
├── GETTING_STARTED.md               # Quick start guide
├── README.md                        # Full documentation
├── docker-compose.yml               # Docker Compose setup
└── guardrails-config.yml            # Policy config
```

## 🔧 Security Rules

| Rule ID | Name | Severity | Detection | CWE | OWASP |
|---------|------|----------|-----------|-----|-------|
| SEC-001 | Hardcoded Secrets | CRITICAL | API keys, passwords, tokens | CWE-798 | A02:2021 |
| SEC-002 | SQL Injection | CRITICAL | String interpolation in queries | CWE-89 | A03:2021 |
| SEC-003 | Insecure Deserialization | HIGH | pickle.loads(), YAML | CWE-502 | A08:2021 |
| SEC-004 | Unsafe Code Execution | CRITICAL | eval(), exec(), os.system() | CWE-95 | A03:2021 |
| SEC-005 | Weak Cryptography | HIGH | MD5, SHA1, DES | CWE-327 | A02:2021 |

## 📦 Supported Languages

Automatically scans:
- Python (.py)
- JavaScript/TypeScript (.js, .ts, .tsx, .jsx)
- Java (.java)
- C# (.cs)
- C/C++ (.cpp, .c)
- Go (.go)
- Ruby (.rb)
- PHP (.php)
- SQL (.sql)
- Scala (.scala)
- Kotlin (.kt)

## 🎯 Workflow

### User Perspective:

1. Developer opens a PR with code changes
2. Guardrails automatically scans the PR
3. If violations detected, GitHub App posts comment
4. Developer sees clear feedback in PR
5. Developer can fix issues or ignore (advisory mode)
6. PR can be merged

### Example:

```
You commit this:
  api_key = "sk-1234567890"

PR comment appears:
  🔴 CRITICAL: Hardcoded API Key (SEC-001)
  File: app.py, Line: 42
  CWE-798 | OWASP A02:2021
  
Developer sees it and fixes it ✅
```

## 📈 Scalability

- **Async processing:** FastAPI handles concurrent requests
- **Lazy loading:** Rules loaded on startup
- **Memory efficient:** Diffs streamed, not stored
- **Timeout handling:** 30s default per PR
- **Rate limiting:** Respects GitHub API limits

## 🔐 Security by Default

- ✅ No source code storage
- ✅ In-memory analysis only
- ✅ Secret key never logged
- ✅ HTTPS communication
- ✅ Webhook signature validation
- ✅ Environment-based configuration

## 📝 Configuration

**guardrails-config.yml:**
```yaml
enforcement_mode: warning
security:
  enabled: true
  block_on_critical: true
  rules:
    - SEC-001  # Hardcoded secrets
    - SEC-002  # SQL injection
    - SEC-003  # Insecure deserialization
    - SEC-004  # Unsafe execution
    - SEC-005  # Weak cryptography
```

## 🚦 Enforcement Modes

### Advisory
- Posts informational comment
- Does NOT block merge
- Good for: Learning, audit trails

### Warning
- Posts warning comment
- Can optionally block critical issues
- Good for: Staged enforcement

### Blocking
- Prevents merge until resolved
- User can override
- Good for: Strict compliance

## 📊 Example PR Comment

```markdown
## 🔍 Guardrails Security Scan

**Scan ID:** `scan-abc123`

### Summary
- **Total Issues:** 2
- 🔴 **Critical:** 2

### 🔴 CRITICAL Issues

<details>
<summary><b>Hardcoded API Key</b> (SEC-001) in app.py:42</summary>

**Issue:** Hardcoded API Key detected in source code.

**Code:**
```
api_key = "sk-1234567890"
```

**Suggested Fix:**
```
api_key = os.getenv("API_KEY")
```

**CWE:** [CWE-798](https://cwe.mitre.org/data/definitions/798.html)
**OWASP:** A02:2021 – Cryptographic Failures

⚠️ This code was generated by GitHub Copilot.

</details>

---
**Policy:** Advisory Mode - Review before merge
*Generated by Guardrails Security Scanner*
```

## 🔄 Integration Points

### Receives from GitHub:
- PR number and metadata
- Commit hash
- File names and diffs
- Author information

### Posts to GitHub:
- PR comments with findings
- Comment with summary and details
- Severity icons and styling

### Integrates with:
- GitHub Actions (can extend)
- Slack webhooks (can add)
- Audit systems (can add)

## 🎓 Technology Stack

**Backend:**
- Python 3.11+
- FastAPI (async web framework)
- Pydantic (data validation)
- PyYAML (configuration)
- Regular expressions (pattern matching)

**Frontend (GitHub App):**
- TypeScript 5.8+
- Probot (GitHub App framework)
- Node.js 18+
- Async/await

**DevOps:**
- Docker & Docker Compose
- Python virtual environment or Conda

## 🌱 Future Enhancements

### Phase 2:
- LLM-based context analysis
- Custom rule builder UI
- License compliance scanning
- Dashboard with metrics
- Detailed audit logging

### Phase 3:
- Enterprise dashboard
- Custom rule packs per industry
- Multi-organization support
- Advanced Copilot detection
- Machine learning anomaly detection

## 📚 Documentation

- [GETTING_STARTED.md](GETTING_STARTED.md) - Quick start (15 minutes)
- [README.md](README.md) - Full documentation
- [backend/README.md](backend/README.md) - Backend details
- [guardrails-github-app/README.md](guardrails-github-app/README.md) - App details

## ⚡ Quick Start

```bash
# Terminal 1: Start backend
cd backend
pip install -r requirements.txt
python main.py

# Terminal 2: Set up GitHub App
cd guardrails-github-app
npm install
npm run build
export APP_ID=xxx PRIVATE_KEY=xxx WEBHOOK_SECRET=xxx
npm start

# Terminal 3 (optional): Smee webhook forwarding
npx smee-client -u https://smee.io/xxx -t http://localhost:3000
```

Then create a PR with `api_key = "sk-123"` and watch the magic happen! 🎉

## 🎯 Success Criteria (Minimal Working System)

✅ Backend analyzes code for security violations  
✅ Detects hardcoded secrets, SQL injection, unsafe execution  
✅ GitHub App triggered on PR events  
✅ PR comments posted with findings  
✅ Violations categorized by severity  
✅ CWE and OWASP mapping included  
✅ Developer-friendly formatting  
✅ Configuration support  
✅ Extensible architecture  
✅ Production-ready foundation  

## 📞 Support

For questions or issues:
1. Check GETTING_STARTED.md
2. Review README.md
3. Check component READMEs
4. Review code comments
5. Check GitHub issues

---

**Status:** ✅ Minimal Working System Complete  
**Version:** 0.1.0  
**Built with:** FastAPI, Probot, TypeScript, Python  
**License:** ISC
