# Testing Guide

## Running Tests

### Backend Tests

```bash
cd backend
python -m pytest tests/ -v
```

### GitHub App Tests

```bash
cd guardrails-github-app
npm test
```

## Test Coverage

### Backend Unit Tests

```bash
# Run with coverage report
python -m pytest tests/ --cov=app --cov-report=html
```

### Integration Tests

```bash
# Start services
docker-compose up -d

# Run integration tests
python -m pytest tests/integration/ -v
```

## Sample Test Cases

### Security Rule Testing

```python
# tests/test_security_rules.py
import pytest
from app.rules.security_rules import SecurityRuleEngine
from app.models import SeverityLevel

class TestSecurityRules:
    def test_hardcoded_secret_detection(self):
        code = '''
        api_key = "sk-1234567890abcdef"
        '''
        violations = SecurityRuleEngine.scan_code(code, "test.py")
        assert len(violations) > 0
        assert violations[0].rule_id == "SEC-001"
        assert violations[0].severity == SeverityLevel.CRITICAL

    def test_sql_injection_detection(self):
        code = '''
        query = f"SELECT * FROM users WHERE id = {user_id}"
        '''
        violations = SecurityRuleEngine.scan_code(code, "test.py")
        assert len(violations) > 0
        assert violations[0].rule_id == "SEC-002"

    def test_eval_detection(self):
        code = '''
        result = eval(user_input)
        '''
        violations = SecurityRuleEngine.scan_code(code, "test.py")
        assert len(violations) > 0
        assert violations[0].rule_id == "SEC-004"
```

### Policy Engine Testing

```python
# tests/test_policy_engine.py
import pytest
from app.policy import PolicyEngine, Policy
from app.models import EnforcementMode, Violation, SeverityLevel, RuleCategory

class TestPolicyEngine:
    def test_blocking_policy(self):
        engine = PolicyEngine()
        
        violations = [
            Violation(
                rule_id="SEC-001",
                rule_name="Hardcoded Secret",
                category=RuleCategory.SECURITY,
                severity=SeverityLevel.CRITICAL,
                message="Hardcoded API key found",
                file_path="app.py",
                line_number=10,
                line_content='api_key = "secret"',
            )
        ]
        
        result = engine.enforce_policy(violations, "test-repo")
        assert result.should_block == True

    def test_advisory_policy(self):
        policy = Policy(
            name="advisory",
            enforcement_mode=EnforcementMode.ADVISORY,
        )
        engine = PolicyEngine()
        engine.register_policy(policy)
        engine.policies["test-repo"] = policy
        
        violations = [
            Violation(
                rule_id="PERF-001",
                rule_name="Performance Issue",
                category=RuleCategory.PERFORMANCE,
                severity=SeverityLevel.LOW,
                message="SELECT * detected",
                file_path="query.sql",
                line_number=1,
                line_content="SELECT * FROM users",
            )
        ]
        
        result = engine.enforce_policy(violations, "test-repo")
        assert result.enforcement_mode == EnforcementMode.ADVISORY
```

### AI Reviewer Testing

```python
# tests/test_ai_reviewer.py
import pytest
from app.ai import AIReviewer
from app.models import Violation, SeverityLevel, RuleCategory

class TestAIReviewer:
    def test_rule_based_suggestion(self):
        reviewer = AIReviewer()
        
        violation = Violation(
            rule_id="SEC-001",
            rule_name="Hardcoded API Key",
            category=RuleCategory.SECURITY,
            severity=SeverityLevel.CRITICAL,
            message="Hardcoded API key found",
            file_path="app.py",
            line_number=10,
            line_content='api_key = "sk-1234567890"',
        )
        
        suggested_code, explanation = reviewer.suggest_fix(violation)
        assert "os.getenv" in suggested_code or "environment" in suggested_code.lower()
        assert len(explanation) > 0

    def test_explanation_generation(self):
        reviewer = AIReviewer()
        
        violation = Violation(
            rule_id="SEC-002",
            rule_name="SQL Injection",
            category=RuleCategory.SECURITY,
            severity=SeverityLevel.CRITICAL,
            message="SQL injection detected",
            file_path="db.py",
            line_number=5,
            line_content='cursor.execute("SELECT * FROM users WHERE id = " + str(user_id))',
        )
        
        explanation = reviewer.generate_explanation(violation)
        assert "parameterized" in explanation.lower() or "injection" in explanation.lower()
```

### Audit Logger Testing

```python
# tests/test_audit_logger.py
import pytest
from datetime import datetime
from app.audit import AuditLogger

class TestAuditLogger:
    def test_scan_logging(self):
        logger = AuditLogger()
        
        event = logger.log_scan(
            repo_name="test/repo",
            pr_number=123,
            commit_hash="abc123",
            violation_count=5,
            critical_count=2,
            high_count=1,
            enforcement_action="warning",
            blocked=False,
            scan_id="scan-123",
        )
        
        assert event.repo_name == "test/repo"
        assert event.violation_count == 5
        assert len(logger.events) == 1

    def test_audit_export(self):
        logger = AuditLogger()
        
        logger.log_scan(
            repo_name="test/repo",
            pr_number=123,
            commit_hash="abc123",
            violation_count=3,
            critical_count=1,
            high_count=0,
            enforcement_action="warning",
            blocked=False,
            scan_id="scan-123",
        )
        
        # Test JSON export
        filename = logger.export_audit_log("audit.json")
        assert os.path.exists(filename)
        
        # Test CSV export
        filename = logger.export_audit_log("audit.csv")
        assert os.path.exists(filename)
```

### GitHub App Integration Test

```typescript
// guardrails-github-app/test/integration.test.ts
import { describe, it, expect, beforeAll } from 'vitest';

describe('GitHub App Integration', () => {
  it('should analyze PR diff correctly', async () => {
    const prData = {
      files: {
        'app.py': `
api_key = "sk-1234567890"
password = "secret"
        `
      }
    };
    
    // Mock GitHub API
    // Send to backend
    const response = await fetch('http://localhost:8000/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(prData)
    });
    
    const result = await response.json();
    expect(result.violation_count).toBeGreaterThan(0);
    expect(result.violations).toContainEqual(
      expect.objectContaining({
        rule_id: 'SEC-001'
      })
    );
  });
});
```

## End-to-End Testing

### Manual Testing Workflow

1. **Setup**
```bash
# Start all services
docker-compose up

# In GitHub, create test repository
# Install Guardrails app
```

2. **Create Test PR**
```bash
git checkout -b test-vulnerability
echo 'api_key = "sk-1234567890"' >> app.py
git commit -am "Add test code"
git push origin test-vulnerability
# Create PR
```

3. **Verify Results**
- Check PR comments for violations
- Verify status checks
- Test override mechanism

### Performance Testing

```bash
# Load test with large PR
for i in {1..100}; do
  echo "# Test file $i" >> test_large_pr_file_$i.py
  echo "api_key_$i = \"secret\"" >> test_large_pr_file_$i.py
done

# Measure analysis time
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d @large_pr_payload.json \
  -w "Time: %{time_total}s\n"
```

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r backend/requirements.txt pytest
      - run: pytest backend/tests/ -v --cov

  app-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - run: cd guardrails-github-app && npm install
      - run: npm test
```

## Test Data

### Sample Malicious Code for Testing

```python
# All these should trigger violations

# SEC-001: Hardcoded secrets
api_key = "sk-1234567890abcdef"
password = "mypassword123"
database_url = "postgres://user:pass@host/db"

# SEC-002: SQL Injection
query = f"SELECT * FROM users WHERE id = {user_id}"
query = "SELECT * FROM users WHERE id = " + str(user_id)

# SEC-004: Unsafe execution
eval(user_input)
exec(code)
os.system("cat " + filename)

# SEC-005: Weak crypto
hash_obj = hashlib.md5(data)
hash_obj = hashlib.sha1(data)

# SEC-008: Weak randomness
token = random.randint(1, 1000000)

# SEC-009: Logging sensitive data
print(f"Password: {user_password}")

# AI-001: Incomplete code
def process_data():
    pass  # TODO: Implement
```

## Debugging Tests

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Interactive Testing

```bash
# Start backend with debug
DEBUGG=true python backend/app/main.py

# Test individual endpoints
curl -X GET http://localhost:8000/health
curl -X GET http://localhost:8000/api/rules
```

## Test Metrics

### Coverage Targets
- Backend: 80%+
- GitHub App: 75%+
- Integration: 100% of critical paths

### Performance Targets
- Single file analysis: <500ms
- Large PR (100 files): <10s
- API response time: <2s (p95)

### Reliability Targets
- False positive rate: <5%
- False negative rate: <2%
- Uptime: 99.9%
