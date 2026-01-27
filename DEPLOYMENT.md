# Deployment Guide

## Quick Start (Development)

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker & Docker Compose (optional)

### Local Development

1. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Backend runs on `http://localhost:8000`

2. **GitHub App Setup**
```bash
cd guardrails-github-app
npm install
npm run build
npm start
```

App runs on `http://localhost:3000`

3. **Local GitHub Webhook Testing**
```bash
# In a third terminal
npx smee-client -u https://smee.io/your-channel-url -t http://localhost:3000
```

### Using Docker Compose

```bash
docker-compose up
```

This starts:
- Backend API on port 8000
- GitHub App on port 3000

## Production Deployment

### Prerequisites
- Docker & Kubernetes (or cloud platform)
- GitHub App with valid credentials
- OpenAI API key (optional, for AI features)
- PostgreSQL or alternative for persistent audit logs

### Environment Variables

**Backend**
```bash
BACKEND_SECRET=<strong-secret-key>
OPENAI_API_KEY=<optional-openai-key>
DEBUG=false
HOST=0.0.0.0
PORT=8000
```

**GitHub App**
```bash
BACKEND_URL=https://guardrails-backend.yourcompany.com
APP_ID=<github-app-id>
PRIVATE_KEY=<github-app-private-key>
WEBHOOK_SECRET=<github-webhook-secret>
```

### Docker Deployment

1. **Build Images**
```bash
# Backend
docker build -t guardrails-backend:1.0.0 ./backend

# GitHub App
docker build -t guardrails-github-app:1.0.0 ./guardrails-github-app
```

2. **Push to Registry**
```bash
docker tag guardrails-backend:1.0.0 registry.example.com/guardrails-backend:1.0.0
docker push registry.example.com/guardrails-backend:1.0.0

docker tag guardrails-github-app:1.0.0 registry.example.com/guardrails-github-app:1.0.0
docker push registry.example.com/guardrails-github-app:1.0.0
```

3. **Run with Docker Compose**
```yaml
version: '3.8'
services:
  backend:
    image: registry.example.com/guardrails-backend:1.0.0
    ports:
      - "8000:8000"
    environment:
      - BACKEND_SECRET=your-secret-key
      - OPENAI_API_KEY=your-openai-key
      - DEBUG=false
    volumes:
      - audit_logs:/app/audit_logs
    restart: always

  github-app:
    image: registry.example.com/guardrails-github-app:1.0.0
    ports:
      - "3000:3000"
    environment:
      - BACKEND_URL=http://backend:8000
      - APP_ID=your-app-id
      - PRIVATE_KEY=your-private-key
      - WEBHOOK_SECRET=your-webhook-secret
    depends_on:
      - backend
    restart: always

volumes:
  audit_logs:
```

### Kubernetes Deployment

1. **Create Namespace**
```bash
kubectl create namespace guardrails
```

2. **Create Secrets**
```bash
kubectl create secret generic guardrails-backend \
  --from-literal=backend-secret=your-secret-key \
  --from-literal=openai-api-key=your-openai-key \
  -n guardrails

kubectl create secret generic guardrails-github-app \
  --from-literal=app-id=your-app-id \
  --from-literal=private-key="$(cat private-key.pem)" \
  --from-literal=webhook-secret=your-webhook-secret \
  -n guardrails
```

3. **Deploy Backend**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: guardrails-backend
  namespace: guardrails
spec:
  replicas: 2
  selector:
    matchLabels:
      app: guardrails-backend
  template:
    metadata:
      labels:
        app: guardrails-backend
    spec:
      containers:
      - name: backend
        image: registry.example.com/guardrails-backend:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: BACKEND_SECRET
          valueFrom:
            secretKeyRef:
              name: guardrails-backend
              key: backend-secret
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: guardrails-backend
              key: openai-api-key
        - name: DEBUG
          value: "false"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

4. **Deploy GitHub App**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: guardrails-github-app
  namespace: guardrails
spec:
  replicas: 1
  selector:
    matchLabels:
      app: guardrails-github-app
  template:
    metadata:
      labels:
        app: guardrails-github-app
    spec:
      containers:
      - name: app
        image: registry.example.com/guardrails-github-app:1.0.0
        ports:
        - containerPort: 3000
        env:
        - name: BACKEND_URL
          value: "http://guardrails-backend:8000"
        - name: APP_ID
          valueFrom:
            secretKeyRef:
              name: guardrails-github-app
              key: app-id
        - name: PRIVATE_KEY
          valueFrom:
            secretKeyRef:
              name: guardrails-github-app
              key: private-key
        - name: WEBHOOK_SECRET
          valueFrom:
            secretKeyRef:
              name: guardrails-github-app
              key: webhook-secret
        livenessProbe:
          httpGet:
            path: /
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
```

5. **Create Services**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: guardrails-backend
  namespace: guardrails
spec:
  selector:
    app: guardrails-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP

---
apiVersion: v1
kind: Service
metadata:
  name: guardrails-github-app
  namespace: guardrails
spec:
  selector:
    app: guardrails-github-app
  ports:
  - port: 3000
    targetPort: 3000
  type: LoadBalancer
```

### Cloud Platforms

#### AWS Deployment
- **ECS/EKS**: Use Kubernetes manifests above
- **Lambda**: Adapt for serverless (requires restructuring)
- **CloudWatch**: Configure audit log export
- **Secrets Manager**: Store GitHub App credentials

#### Google Cloud
- **GKE**: Deploy with kubectl
- **Cloud Run**: Use Dockerfile for serverless deployment
- **Cloud Logging**: Export audit logs
- **Secret Manager**: Store credentials

#### Azure Deployment
- **AKS**: Kubernetes deployment
- **Container Instances**: Docker deployment
- **Azure Cosmos DB**: For audit log persistence
- **Key Vault**: Store secrets

## Configuration

### Policy Configuration

Create default policies in `.guardrails/` directory:

```yaml
# organization-policy.yaml
default_enforcement_mode: warning
allow_overrides: true
require_approval_for_override: false
```

### Rule Packs

Load custom rule packs:

```bash
# Backend environment
CUSTOM_RULES_PATH=/etc/guardrails/custom-rules.yaml
```

### Audit Log Persistence

For production, configure external storage:

```python
# In backend/app/audit/audit_logger.py
# Modify to use database instead of file-based logging

class DatabaseAuditLogger(AuditLogger):
    def __init__(self, db_connection_string):
        self.db = connect(db_connection_string)
    
    def _write_event(self, event):
        self.db.insert("audit_events", event.to_dict())
```

## Monitoring & Logging

### Metrics to Monitor
- API response time (target: <2s for analysis)
- Queue depth (background jobs)
- False positive rate
- Copilot detection accuracy
- Cache hit rate

### Log Aggregation

Example with ELK Stack:
```yaml
logging:
  driver: json-file
  options:
    labels: service=guardrails
    max-file: "10"
    max-size: 10m
```

### Alerts
- High API error rate (>5%)
- Scan timeout (>30s)
- Queue overflow
- License compliance violations
- Suspicious override patterns

## Backup & Recovery

### Audit Log Backup
```bash
# Daily backup
0 2 * * * curl http://localhost:8000/api/audit/export -d '{"format": "json"}' > /backups/audit-$(date +%Y%m%d).json
```

### Database Backup (if using external DB)
```bash
# PostgreSQL example
pg_dump guardrails_db > /backups/guardrails-$(date +%Y%m%d).sql
```

## Security Hardening

### Production Checklist
- [ ] Enable HTTPS/TLS
- [ ] Configure network policies
- [ ] Set up WAF rules
- [ ] Enable audit logging
- [ ] Configure log rotation
- [ ] Set up intrusion detection
- [ ] Implement rate limiting
- [ ] Enable backup retention
- [ ] Configure disaster recovery
- [ ] Regular security scanning

### Network Configuration
```bash
# Only allow GitHub webhooks to GitHub App
# Only allow internal traffic to backend API
# Use VPN/Bastion for admin access
```

## Performance Tuning

### Backend
- Increase workers: `--workers 4` in uvicorn
- Enable gzip compression
- Configure connection pooling
- Tune cache TTL

### GitHub App
- Increase timeout for large PRs
- Configure retry policy
- Cache GitHub API responses

## Rollback Procedure

If issues arise:

```bash
# Docker
docker-compose down
docker-compose up -d version-tag-previous

# Kubernetes
kubectl rollout undo deployment/guardrails-backend -n guardrails
kubectl rollout undo deployment/guardrails-github-app -n guardrails
```

## Support & Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.
