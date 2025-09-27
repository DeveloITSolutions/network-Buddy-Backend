#!/bin/bash

# Deployment script for bcrypt fix
# This script helps deploy the fixed version to AWS EC2

set -e

echo "🔧 Deploying bcrypt fix to AWS EC2..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
EC2_HOST="${EC2_HOST:-your-ec2-host.com}"
EC2_USER="${EC2_USER:-ubuntu}"
EC2_KEY="${EC2_KEY:-~/.ssh/your-key.pem}"
PROJECT_DIR="/home/ubuntu/the_plugs_backend"

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  Host: $EC2_HOST"
echo "  User: $EC2_USER"
echo "  Key: $EC2_KEY"
echo "  Project Dir: $PROJECT_DIR"
echo ""

# Function to run commands on EC2
run_on_ec2() {
    ssh -i "$EC2_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "$1"
}

# Function to copy files to EC2
copy_to_ec2() {
    scp -i "$EC2_KEY" -o StrictHostKeyChecking=no "$1" "$EC2_USER@$EC2_HOST:$2"
}

echo -e "${YELLOW}🚀 Step 1: Stopping services on EC2...${NC}"
run_on_ec2 "cd $PROJECT_DIR && docker compose down || true"

echo -e "${YELLOW}📦 Step 2: Copying updated files to EC2...${NC}"
copy_to_ec2 "requirements.txt" "$PROJECT_DIR/"
copy_to_ec2 "app/config/security.py" "$PROJECT_DIR/app/config/"
copy_to_ec2 "app/schemas/auth.py" "$PROJECT_DIR/app/schemas/"
copy_to_ec2 "Dockerfile" "$PROJECT_DIR/"

echo -e "${YELLOW}🔨 Step 3: Rebuilding Docker images on EC2...${NC}"
run_on_ec2 "cd $PROJECT_DIR && docker compose build --no-cache"

echo -e "${YELLOW}🔄 Step 4: Starting services...${NC}"
run_on_ec2 "cd $PROJECT_DIR && docker compose up -d"

echo -e "${YELLOW}⏳ Step 5: Waiting for services to start...${NC}"
sleep 30

echo -e "${YELLOW}🏥 Step 6: Checking health...${NC}"
run_on_ec2 "curl -f http://localhost:8000/health || echo 'Health check failed'"

echo -e "${GREEN}✅ Deployment completed!${NC}"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Test the login endpoint: POST http://$EC2_HOST:8000/api/v1/auth/login"
echo "2. Monitor logs: docker logs -f the_plugs_api"
echo "3. Check health: curl http://$EC2_HOST:8000/health"
echo ""
echo -e "${YELLOW}🔍 To monitor logs:${NC}"
echo "ssh -i $EC2_KEY $EC2_USER@$EC2_HOST 'cd $PROJECT_DIR && docker compose logs -f api'"
