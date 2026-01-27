# Quick Reference Guide - Guardrails v1.0.0

## What's New in v1.0.0

### Core Features Enhanced
| Feature | v0.1.0 | v1.0.0 |
|---------|--------|--------|
| Security Rules | 5 basic | 30+ comprehensive |
| AI Integration | None | OpenAI + Copilot detection |
| Policy Modes | Advisory only | Advisory/Warning/Blocking + overrides |
| Compliance | None | Industry-specific packs (4 industries) |
| Audit Trail | None | Complete with export |
| Extensibility | None | Full plugin system |
| Performance | Basic | Caching, async, rate limiting |
| API Endpoints | 3 | 20+ |

## Getting Started (5 minutes)

### Local Development
```bash
# Terminal 1: Backend
cd backend
pip install -r requirements.txt
python main.py
# → http://localhost:8000

# Terminal 2: GitHub App  
cd guardrails-github-app
npm install && npm start
# → http://localhost:3000

# Terminal 3: Webhook forwarding
npx smee-client -u https://smee.io/YOUR-CHANNEL -t http://localhost:3000
```

### Quick Test
```bash
# Health check
curl http://localhost:8000/health

# Get rules
curl http://localhost:8000/api/rules

# Analyze code
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "test/repo",
    "pr_number": 1,
    "commit_hash": "abc123",
    "files": {"app.py": "api_key = \"secret\""}
  }'
```

## Feature Deep Dive

### 1. Security Rules
**12+ Categories**
- SEC-001 to SEC-010: Security issues
- AI-001 to AI-002: AI-generated code risks
- COMP-001: Compliance issues
- LICENSE-001, IP-001 to IP-002: IP/License issues
- PERF-001: Performance issues

### 2. Copilot Detection
Automatic detection of AI-generated code with stricter analysis:
```python
# Detects these patterns:
# "# This is a..."
# "# TODO: Implement"
# "# Replace with your..."
# Empty functions with pass
```

### 3. Policy Enforcement
```yaml
# .guardrails/policy.yaml
enforcement_mode: warning          # advisory, warning, blocking
block_on_critical: true
block_on_high: false
allowed_licenses: [MIT, Apache-2.0]
```

### 4. Override System
```bash
# Request override
curl -X POST http://localhost:8000/api/override \
  -d '{"repo_name":"org/repo", "reason":"business need"}'

# Use token in next analysis
curl -X POST http://localhost:8000/api/analyze \
  -d '{"override_token":"token_here", ...}'
```

### 5. Compliance Packs
```bash
# Get industry rules
GET /api/compliance/industries
# → ["banking", "healthcare", "government", "telecom"]

GET /api/compliance/rules/banking
# → PCI DSS compliance rules
```

### 6. Audit & Insights
```bash
# Get events
GET /api/audit?repo=org/repo&days=7

# Export audit log
POST /api/audit/export
# {"format": "json"} or {"format": "csv"}

# Organization insights
GET /api/insights?days=30
# → Trends, violations, hotspots, blocking stats
```

### 7. Custom Rules
```yaml
# guardrails-ruleset-custom.yaml
name: custom-ruleset
rules:
  - rule_id: CUSTOM-001
    name: My Custom Rule
    severity: high
    category: security
    pattern: your-regex
```

### 8. Plugins
```python
from app.plugins import RulePlugin, register_rule_plugin

class MyRule(RulePlugin):
    @property
    def rule_id(self):
        return "CUSTOM-001"
    
    def analyze(self, code, file_path):
        # Your logic here
        return violations

register_rule_plugin(MyRule())
```

## Configuration Guide

### Repository Policy
Place in `.guardrails/policy.yaml`:
```yaml
enforcement_mode: warning
block_on_critical: true
enable_security_checks: true
enable_compliance_checks: true
allowed_licenses:
  - MIT
  - Apache-2.0
```

### Custom Ruleset
Create YAML file with rules:
```yaml
name: my-ruleset
version: "1.0.0"
rules:
  - rule_id: SEC-001
    enabled: true
    severity: critical
```

### Environment Variables
```bash
# Backend
OPENAI_API_KEY=sk-...           # Optional, for AI suggestions
BACKEND_SECRET=your-secret
DEBUG=false

# GitHub App
BACKEND_URL=http://localhost:8000
APP_ID=your-app-id
PRIVATE_KEY="----BEGIN PRIVATE KEY----..."
WEBHOOK_SECRET=your-webhook-secret
```

## API Reference

### Analysis
```bash
POST /api/analyze
{
  "repo_name": "owner/repo",
  "pr_number": 123,
  "commit_hash": "abc123",
  "files": {"path/file.py": "diff..."},
  "copilot_generated_files": ["path/file.py"],
  "override_token": "token_if_overriding"
}

# Response
{
  "success": true,
  "scan_id": "uuid",
  "violations": [...],
  "violation_count": 5,
  "critical_count": 2,
  "enforcement_mode": "warning",
  "should_block": false
}
```

### Other Endpoints
```bash
GET  /health                           # Health check
GET  /api/rules                        # List all rules
GET  /api/policies                     # List policies
GET  /api/insights?days=30             # Org insights
GET  /api/audit?repo=org/repo          # Audit events
POST /api/audit/export                 # Export logs
GET  /api/compliance/industries        # List industries
GET  /api/compliance/rules/{industry}  # Get industry rules
POST /api/override                     # Request override
GET  /api/plugins                      # List plugins
```

## Common Scenarios

### Scenario 1: Harden Security for Production
```yaml
enforcement_mode: blocking
block_on_critical: true
block_on_high: true
enable_security_checks: true
enable_compliance_checks: true
```

### Scenario 2: Permissive for Development
```yaml
enforcement_mode: advisory
block_on_critical: false
block_on_high: false
enable_quality_checks: false
```

### Scenario 3: Compliance-First (Banking)
```yaml
enforcement_mode: blocking
allowed_industries: [banking]
enable_compliance_checks: true
block_on_critical: true
block_on_high: true
```

### Scenario 4: AI Code Monitoring
```python
# Enable stricter analysis for AI-generated code
# Automatically applied when Copilot patterns detected
# Check response for "copilot_violations" count
```

## Troubleshooting

### AI Suggestions Not Working
→ Set `OPENAI_API_KEY` environment variable

### PRs Not Being Scanned
→ Check GitHub App installation and webhook settings

### High False Positive Rate
→ Customize rules in `.guardrails/policy.yaml`

### Large PRs Timing Out
→ Increase timeout, use async processing

## Performance Tips

- **Cache misses**: Same commit = <10ms
- **Large PRs**: Auto-chunked for parallelization
- **Rate limit**: 100 req/min per IP (adjustable)
- **Background jobs**: Use for async processing

## Deployment Checklists

### Local/Dev
- [ ] Backend running on 8000
- [ ] GitHub App running on 3000
- [ ] Smee forwarding webhooks
- [ ] GitHub App installed on test repo

### Staging
- [ ] HTTPS enabled
- [ ] OPENAI_API_KEY set
- [ ] Audit logs configured
- [ ] Monitoring set up

### Production
- [ ] DEBUG=false
- [ ] Strong secrets configured
- [ ] Database backup configured
- [ ] Log export automated
- [ ] Monitoring/alerting active
- [ ] Disaster recovery plan
- [ ] Security audit done
- [ ] Performance tested

## Support Resources

- **Docs**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Deployment**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Testing**: See [TESTING.md](TESTING.md)
- **API Docs**: Run server, visit `/docs`
- **Issues**: Check GitHub Issues
- **Email**: support@guardrails.ai

## Key Metrics to Monitor

- **Scan time** (target: <2s)
- **Violation rate** (baseline varies)
- **False positive rate** (target: <5%)
- **Cache hit rate** (target: >80%)
- **API availability** (target: 99.9%)
- **Override rate** (monitor for trends)

## Version History

- **v1.0.0** (2024-01): Full enterprise release
- **v0.1.0** (2024-01): MVP with basic rules

## License

See LICENSE file

## Next Steps

1. **Install**: Follow [QUICK_START.md](QUICK_START.md)
2. **Configure**: Create `.guardrails/policy.yaml`
3. **Deploy**: See [DEPLOYMENT.md](DEPLOYMENT.md)
4. **Test**: Follow [TESTING.md](TESTING.md)
5. **Monitor**: Set up audit export
6. **Extend**: Create custom rules via plugins
