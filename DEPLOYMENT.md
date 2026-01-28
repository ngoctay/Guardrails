# Deployment Guide

## Prerequisites

- Python 3.9+
- Node.js 18+
- Docker & Docker Compose (for container deployment)
- GitHub App credentials
- Google Gemini API key (optional, for AI features)

## Environment Variables

### Backend
```bash
# Required
GOOGLE_API_KEY=<your-gemini-api-key>  # Optional for AI suggestions

# Optional
DEBUG=false
HOST=0.0.0.0
PORT=8000
```

### GitHub App
```bash
# Required
BACKEND_URL=<your-backend-url>
APP_ID=<github-app-id>
PRIVATE_KEY=<github-app-private-key>
WEBHOOK_SECRET=<github-webhook-secret>
```

## Local Development

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Backend runs on `http://localhost:8000`

### 2. GitHub App Setup

```bash
cd guardrails-github-app
npm install
npm run build
npm start
```

App runs on `http://localhost:3000`

## Docker Deployment

### Using Docker Compose

1. **Create `.env` file in root directory:**

```bash
# Backend
GOOGLE_API_KEY=your-gemini-api-key
DEBUG=false

# GitHub App
BACKEND_URL=http://backend:8000
APP_ID=your-github-app-id
PRIVATE_KEY=your-github-app-private-key
WEBHOOK_SECRET=your-webhook-secret
```

2. **Start services:**

```bash
docker-compose up -d
```

Services:
- Backend API: http://localhost:8000
- GitHub App: http://localhost:3000

3. **View logs:**

```bash
docker-compose logs -f
```

4. **Stop services:**

```bash
docker-compose down
```

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - DEBUG=${DEBUG}
      - HOST=0.0.0.0
      - PORT=8000
    volumes:
      - ./backend/audit_logs:/app/audit_logs
    restart: always

  github-app:
    build: ./guardrails-github-app
    ports:
      - "3000:3000"
    environment:
      - BACKEND_URL=${BACKEND_URL}
      - APP_ID=${APP_ID}
      - PRIVATE_KEY=${PRIVATE_KEY}
      - WEBHOOK_SECRET=${WEBHOOK_SECRET}
    depends_on:
      - backend
    restart: always
```

## AWS Deployment

### Prerequisites
- AWS Free Tier account
- EC2 key pair
- GitHub App credentials
- Google Gemini API key

### 1. Launch EC2 Instance

1. **Go to EC2 Dashboard** → Click "Launch Instance"
2. **Choose AMI**: Select "Ubuntu Server 22.04 LTS (Free tier eligible)"
3. **Instance Type**: Select `t2.micro` (Free tier eligible)
4. **Configure Security Group**:
   - SSH (22): From your IP
   - HTTP (80): From anywhere (0.0.0.0/0)
   - HTTPS (443): From anywhere (0.0.0.0/0)
   - Custom TCP (8000): From anywhere (for backend API)
   - Custom TCP (3000): From anywhere (for GitHub App)

5. **Storage**: Keep 30 GB (Free tier eligible)
6. **Key Pair**: Create or select an existing one
7. **Launch** and note your instance's Public IP

### 2. Connect to EC2

```bash
ssh -i your-key.pem ubuntu@<your-ec2-public-ip>

sudo apt update && sudo apt upgrade -y

sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm git curl

python3 --version
node --version
npm --version
```

### 3. Deploy Application

```bash
# Clone repository
cd /home/ubuntu
git clone https://github.com/your-username/Guardrails.git
cd Guardrails

# Create .env file
cat > .env << 'EOF'
# Backend
GOOGLE_API_KEY=your-gemini-api-key
DEBUG=false
HOST=0.0.0.0
PORT=8000

# GitHub App
BACKEND_URL=http://your-ec2-public-ip:8000
APP_ID=your-github-app-id
PRIVATE_KEY="your-private-key"
WEBHOOK_SECRET=your-webhook-secret
EOF
```

### 4. Setup Backend Service

```bash
# Create systemd service for backend
sudo tee /etc/systemd/system/guardrails-backend.service << 'EOF'
[Unit]
Description=Guardrails Backend Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Guardrails/backend
Environment="PATH=/home/ubuntu/Guardrails/backend/venv/bin"
ExecStart=/home/ubuntu/Guardrails/backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Setup Python environment
cd /home/ubuntu/Guardrails/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Enable and start backend service
sudo systemctl daemon-reload
sudo systemctl enable guardrails-backend
sudo systemctl start guardrails-backend
sudo systemctl status guardrails-backend
```

### 5. Setup GitHub App Service

```bash
# Create systemd service for GitHub App
sudo tee /etc/systemd/system/guardrails-app.service << 'EOF'
[Unit]
Description=Guardrails GitHub App
After=network.target guardrails-backend.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Guardrails/guardrails-github-app
Environment="PATH=/home/ubuntu/Guardrails/guardrails-github-app/node_modules/.bin:/usr/bin:/bin"
Environment="NODE_ENV=production"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Setup Node.js environment
cd /home/ubuntu/Guardrails/guardrails-github-app
npm install
npm run build

# Enable and start GitHub App service
sudo systemctl daemon-reload
sudo systemctl enable guardrails-app
sudo systemctl start guardrails-app
sudo systemctl status guardrails-app
```

### 6. Setup Reverse Proxy (Nginx)

```bash
# Install Nginx
sudo apt install -y nginx

# Create Nginx config
sudo tee /etc/nginx/sites-available/guardrails << 'EOF'
server {
    listen 80;
    server_name your-ec2-public-ip;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

# Enable Nginx config
sudo ln -s /etc/nginx/sites-available/guardrails /etc/nginx/sites-enabled/guardrails
sudo rm /etc/nginx/sites-enabled/default

# Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx
```

### 7. Verify Deployment

```bash
# Check services status
sudo systemctl status guardrails-backend
sudo systemctl status guardrails-app
sudo systemctl status nginx

# Check logs
sudo journalctl -u guardrails-backend -f
sudo journalctl -u guardrails-app -f

# Test endpoints
curl http://your-ec2-public-ip/health
curl http://your-ec2-public-ip/
```

### 8. Configure GitHub App Webhook

1. Go to GitHub App Settings → Webhook URL
2. Set to: `http://your-ec2-public-ip/webhook` or use your domain
3. Save

Then update GitHub App webhook to use this IP.

