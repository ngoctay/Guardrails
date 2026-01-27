# AWS Deployment Quick Start Guide

This guide will walk you through deploying Guardrails to AWS using the free tier.

## Prerequisites

1. AWS Free Tier Account
2. GitHub App already created (see [GETTING_STARTED.md](GETTING_STARTED.md))
3. SSH client installed locally
4. Domain name (optional, but recommended)

## Step 1: Create EC2 Instance

### 1.1 Launch Instance

```bash
# In AWS Console:
# EC2 → Instances → Launch Instance
```

**Configuration:**
- **Name**: `guardrails-app`
- **AMI**: Ubuntu Server 22.04 LTS (Free tier eligible)
- **Instance Type**: `t2.micro` (Free tier eligible)
- **Key Pair**: Create new or use existing
- **Storage**: 30 GB gp2 (Free tier eligible)

### 1.2 Configure Security Group

Create security group `guardrails-sg` with inbound rules:

| Port | Protocol | Source |
|------|----------|--------|
| 22   | SSH      | Your IP |
| 80   | HTTP     | 0.0.0.0/0 |
| 443  | HTTPS    | 0.0.0.0/0 |
| 8000 | TCP      | 0.0.0.0/0 |
| 3000 | TCP      | 0.0.0.0/0 |

### 1.3 Get Your Instance IP

After launch, note your **Public IPv4 address**. Let's call it `YOUR_EC2_IP`.

## Step 2: Connect and Setup Server

### 2.1 SSH into Your Instance

```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# Update system
sudo apt update && sudo apt upgrade -y
```

### 2.2 Install Dependencies

```bash
# Install system packages
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm git curl

# Verify
python3 --version  # Python 3.11.x
node --version    # v18+
```

## Step 3: Clone and Configure

### 3.1 Clone Repository

```bash
cd /home/ubuntu
git clone https://github.com/YOUR_USERNAME/Guardrails.git
cd Guardrails
```

### 3.2 Create Environment File

```bash
cat > .env << 'EOF'
# Backend Configuration
GOOGLE_API_KEY=your-gemini-api-key
DEBUG=false
HOST=0.0.0.0
PORT=8000

# GitHub App Configuration
BACKEND_URL=http://YOUR_EC2_IP:8000
APP_ID=your-github-app-id
PRIVATE_KEY="your-private-key-here"
WEBHOOK_SECRET=your-webhook-secret
EOF

# Replace placeholders with actual values
nano .env
```

## Step 4: Deploy Backend

### 4.1 Setup Python Environment

```bash
cd /home/ubuntu/Guardrails/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4.2 Create Systemd Service

```bash
sudo tee /etc/systemd/system/guardrails-backend.service << 'EOF'
[Unit]
Description=Guardrails Backend Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Guardrails/backend
Environment="PATH=/home/ubuntu/Guardrails/backend/venv/bin"
Environment="GOOGLE_API_KEY=your-gemini-api-key"
Environment="DEBUG=false"
Environment="HOST=0.0.0.0"
Environment="PORT=8000"
ExecStart=/home/ubuntu/Guardrails/backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 4.3 Start Backend Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable guardrails-backend
sudo systemctl start guardrails-backend
sudo systemctl status guardrails-backend

# Check logs
sudo journalctl -u guardrails-backend -f
```

### 4.4 Verify Backend

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "ai_enabled": true,
  "timestamp": "2026-01-28T..."
}
```

## Step 5: Deploy GitHub App

### 5.1 Setup Node.js Environment

```bash
cd /home/ubuntu/Guardrails/guardrails-github-app
npm install
npm run build
```

### 5.2 Create Systemd Service

```bash
sudo tee /etc/systemd/system/guardrails-app.service << 'EOF'
[Unit]
Description=Guardrails GitHub App
After=network.target guardrails-backend.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Guardrails/guardrails-github-app
Environment="PATH=/home/ubuntu/Guardrails/guardrails-github-app/node_modules/.bin:/usr/bin:/bin"
Environment="NODE_ENV=production"
Environment="BACKEND_URL=http://localhost:8000"
Environment="APP_ID=your-github-app-id"
Environment="PRIVATE_KEY=your-private-key"
Environment="WEBHOOK_SECRET=your-webhook-secret"
Environment="WEB_PORT=3000"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 5.3 Start App Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable guardrails-app
sudo systemctl start guardrails-app
sudo systemctl status guardrails-app

# Check logs
sudo journalctl -u guardrails-app -f
```

## Step 6: Setup Nginx Reverse Proxy

### 6.1 Install and Configure Nginx

```bash
sudo apt install -y nginx

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/guardrails << 'EOF'
server {
    listen 80 default_server;
    server_name _;

    client_max_body_size 100M;

    # Main application (GitHub App + Dashboard)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000/health;
    }
}
EOF

# Enable configuration
sudo rm /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/guardrails /etc/nginx/sites-enabled/guardrails

# Test and restart
sudo nginx -t
sudo systemctl restart nginx
```

### 6.2 Verify Nginx

```bash
sudo systemctl status nginx

# Test from your local machine
curl http://YOUR_EC2_IP/
curl http://YOUR_EC2_IP/health
```

## Step 7: Configure GitHub App Webhook

1. Go to GitHub App settings
2. Update **Webhook URL** to: `http://YOUR_EC2_IP/webhook`
3. Ensure webhook secret matches `WEBHOOK_SECRET` in `.env`
4. Save

## Step 8: Install App in Repository

1. Go to your GitHub App page
2. Click "Install App"
3. Select repository for testing
4. Confirm installation

## Step 9: Test Deployment

### 9.1 Test via Dashboard

Visit `http://YOUR_EC2_IP` in your browser. You should see:
- Home page with health status
- Navigation to Dashboard, Insights, Rules
- All links working properly

### 9.2 Test via API

```bash
# From your local machine
curl http://YOUR_EC2_IP/api/audit
curl http://YOUR_EC2_IP/api/rules
```

### 9.3 Test via GitHub

1. Create a test PR with some code
2. Watch for Guardrails bot comments
3. Check dashboard for audit logs at `http://YOUR_EC2_IP/dashboard`

## Step 10: Optional - Setup HTTPS with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate (requires domain name)
sudo certbot certonly --nginx -d your-domain.com

# Update Nginx configuration with SSL
# Then restart Nginx
```

## Monitoring and Maintenance

### View Logs

```bash
# Backend logs
sudo journalctl -u guardrails-backend -n 100 -f

# App logs
sudo journalctl -u guardrails-app -n 100 -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Restart Services

```bash
# Restart all services
sudo systemctl restart guardrails-backend guardrails-app nginx

# Or individually
sudo systemctl restart guardrails-backend
sudo systemctl restart guardrails-app
```

### Update Deployment

```bash
cd /home/ubuntu/Guardrails

# Pull latest changes
git pull origin main

# Reinstall backend dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart guardrails-backend

# Reinstall app dependencies
cd ../guardrails-github-app
npm install
npm run build
sudo systemctl restart guardrails-app
```

### Backup Audit Logs

```bash
# Download audit logs to your local machine
scp -i your-key.pem -r ubuntu@YOUR_EC2_IP:/home/ubuntu/Guardrails/backend/audit_logs ./backups/
```

## Troubleshooting

### Backend won't start
```bash
sudo journalctl -u guardrails-backend -n 50
# Check environment variables in service file
nano /etc/systemd/system/guardrails-backend.service
```

### App won't connect to backend
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check environment variables
ps aux | grep node
```

### Nginx 502 Bad Gateway
```bash
# Check if services are running
systemctl status guardrails-app
systemctl status guardrails-backend

# Restart Nginx
sudo systemctl restart nginx
```

### Can't SSH into instance
- Check security group inbound rules
- Verify key pair permissions: `chmod 600 your-key.pem`
- Check your IP hasn't changed (security group might be restricted to old IP)

## AWS Costs

**Free Tier includes:**
- 750 hours/month of t2.micro EC2
- 15 GB outbound data transfer/month
- 30 GB EBS storage

**Estimated costs if exceeding free tier:**
- t2.micro: ~$0.0116/hour
- Data transfer: ~$0.09/GB (after 15 GB free)

## Next Steps

1. **Configure custom domains**: Point your domain to the EC2 instance
2. **Setup automated backups**: S3 bucket for audit log backups
3. **Add monitoring**: CloudWatch dashboards for service monitoring
4. **Setup CI/CD**: Automate deployments with GitHub Actions

## Support

For issues or questions:
1. Check logs with `journalctl`
2. Review [DEPLOYMENT.md](../DEPLOYMENT.md) for more options
3. See [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) for common issues
