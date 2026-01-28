#!/bin/bash

# Guardrails Setup and Deployment Script
# ======================================

set -e

echo "🚀 Guardrails Setup Script"
echo "=========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on AWS or local
if [ "$1" = "aws" ]; then
    echo -e "${YELLOW}Setting up for AWS deployment...${NC}"
    IS_AWS=true
else
    echo -e "${YELLOW}Setting up for local development...${NC}"
    IS_AWS=false
fi

# 1. Check dependencies
echo -e "\n${YELLOW}Checking dependencies...${NC}"
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "❌ NPM is required"; exit 1; }
echo -e "${GREEN}✓ All dependencies found${NC}"

# 2. Create .env file if not exists
if [ ! -f ".env" ]; then
    echo -e "\n${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env with your credentials${NC}"
    echo "Edit .env? (y/n)"
    read -r EDIT_ENV
    if [ "$EDIT_ENV" = "y" ]; then
        nano .env
    fi
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# 3. Setup Backend
echo -e "\n${YELLOW}Setting up backend...${NC}"
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "Installing backend dependencies..."
pip install -q -r requirements.txt

echo -e "${GREEN}✓ Backend setup complete${NC}"
cd ..

# 4. Setup GitHub App
echo -e "\n${YELLOW}Setting up GitHub App...${NC}"
cd guardrails-github-app

if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install -q
fi

echo "Building TypeScript..."
npm run build -q

echo -e "${GREEN}✓ GitHub App setup complete${NC}"
cd ..

# 5. Create systemd services for AWS
if [ "$IS_AWS" = true ]; then
    echo -e "\n${YELLOW}Creating systemd services for AWS...${NC}"
    
    # Get current user
    CURRENT_USER=$(whoami)
    WORK_DIR=$(pwd)
    
    echo "Creating backend service..."
    sudo tee /etc/systemd/system/guardrails-backend.service > /dev/null << EOF
[Unit]
Description=Guardrails Backend Service
After=network.target

[Service]
User=$CURRENT_USER
WorkingDirectory=$WORK_DIR/backend
Environment="PATH=$WORK_DIR/backend/venv/bin"
ExecStart=$WORK_DIR/backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    echo "Creating GitHub App service..."
    sudo tee /etc/systemd/system/guardrails-app.service > /dev/null << EOF
[Unit]
Description=Guardrails GitHub App
After=network.target guardrails-backend.service

[Service]
User=$CURRENT_USER
WorkingDirectory=$WORK_DIR/guardrails-github-app
Environment="NODE_ENV=production"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    echo "Reloading systemd..."
    sudo systemctl daemon-reload
    
    echo -e "${GREEN}✓ Systemd services created${NC}"
    echo -e "\n${YELLOW}To start services, run:${NC}"
    echo "  sudo systemctl start guardrails-backend"
    echo "  sudo systemctl start guardrails-app"
    echo "  sudo systemctl status guardrails-backend guardrails-app"
fi

# 6. Summary
echo -e "\n${GREEN}✅ Setup complete!${NC}"

if [ "$IS_AWS" = false ]; then
    echo -e "\n${YELLOW}To start development:${NC}"
    echo "  Terminal 1: cd backend && source venv/bin/activate && python main.py"
    echo "  Terminal 2: cd guardrails-github-app && npm start"
    echo -e "\n${YELLOW}URLs:${NC}"
    echo "  Backend API: http://localhost:8000"
    echo "  Dashboard: http://localhost:3000"
    echo "  Health Check: curl http://localhost:8000/health"
fi

echo -e "\n${YELLOW}For deployment instructions, see:${NC}"
echo "  - AWS Setup: AWS_SETUP.md"
echo "  - Full Deployment: DEPLOYMENT.md"
echo "  - Getting Started: GETTING_STARTED.md"
