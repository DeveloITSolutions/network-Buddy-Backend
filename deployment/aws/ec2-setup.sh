#!/bin/bash

# AWS EC2 Setup Script for The Plugs Backend
# This script sets up an EC2 instance for production deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="the-plugs-backend"
APP_USER="plugs"
APP_DIR="/opt/the-plugs"
NGINX_CONF="/etc/nginx/sites-available/the-plugs"
NGINX_ENABLED="/etc/nginx/sites-enabled/the-plugs"

echo -e "${GREEN}Starting AWS EC2 setup for The Plugs Backend...${NC}"

# Update system
echo -e "${YELLOW}Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install required packages
echo -e "${YELLOW}Installing required packages...${NC}"
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    nginx \
    supervisor \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    libpq-dev \
    redis-server \
    awscli \
    certbot \
    python3-certbot-nginx

# Create application user
echo -e "${YELLOW}Creating application user...${NC}"
sudo useradd -m -s /bin/bash $APP_USER || echo "User already exists"
sudo usermod -aG sudo $APP_USER

# Create application directory
echo -e "${YELLOW}Creating application directory...${NC}"
sudo mkdir -p $APP_DIR
sudo chown $APP_USER:$APP_USER $APP_DIR

# Create logs directory
sudo mkdir -p /var/log/the-plugs
sudo chown $APP_USER:$APP_USER /var/log/the-plugs

# Create uploads directory
sudo mkdir -p /var/uploads/the-plugs
sudo chown $APP_USER:$APP_USER /var/uploads/the-plugs

# Configure AWS CLI (will be done manually)
echo -e "${YELLOW}Please configure AWS CLI with: aws configure${NC}"
echo "You'll need:"
echo "- AWS Access Key ID"
echo "- AWS Secret Access Key"
echo "- Default region (e.g., us-east-1)"
echo "- Default output format (json)"

# Install Docker (optional, for containerized deployment)
echo -e "${YELLOW}Installing Docker...${NC}"
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $APP_USER
rm get-docker.sh

# Install Docker Compose
echo -e "${YELLOW}Installing Docker Compose...${NC}"
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Configure firewall
echo -e "${YELLOW}Configuring firewall...${NC}"
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw --force enable

# Configure timezone
echo -e "${YELLOW}Setting timezone...${NC}"
sudo timedatectl set-timezone UTC

# Create systemd service for the application
echo -e "${YELLOW}Creating systemd service...${NC}"
sudo tee /etc/systemd/system/the-plugs.service > /dev/null <<EOF
[Unit]
Description=The Plugs Backend API
After=network.target

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
Environment=PYTHONPATH=$APP_DIR
Environment=ENVIRONMENT=production
Environment=DEBUG=false
ExecStart=$APP_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create Celery worker service
sudo tee /etc/systemd/system/the-plugs-celery.service > /dev/null <<EOF
[Unit]
Description=The Plugs Celery Worker
After=network.target

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
Environment=PYTHONPATH=$APP_DIR
Environment=ENVIRONMENT=production
Environment=DEBUG=false
ExecStart=$APP_DIR/venv/bin/celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo -e "${YELLOW}Configuring Nginx...${NC}"
sudo tee $NGINX_CONF > /dev/null <<EOF
upstream the_plugs_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # File upload size
    client_max_body_size 100M;
    
    # Static files
    location /static/ {
        alias /var/uploads/the-plugs/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API endpoints
    location / {
        proxy_pass http://the_plugs_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check
    location /health {
        proxy_pass http://the_plugs_backend/health;
        access_log off;
    }
}
EOF

# Enable the site
sudo ln -sf $NGINX_CONF $NGINX_ENABLED
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Create deployment script
echo -e "${YELLOW}Creating deployment script...${NC}"
sudo tee $APP_DIR/deploy.sh > /dev/null <<'EOF'
#!/bin/bash

# Deployment script for The Plugs Backend
set -e

APP_DIR="/opt/the-plugs"
APP_USER="plugs"

echo "Starting deployment..."

# Pull latest code
cd $APP_DIR
sudo -u $APP_USER git pull origin main

# Install/update dependencies
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r requirements.txt

# Run database migrations
sudo -u $APP_USER $APP_DIR/venv/bin/alembic upgrade head

# Collect static files (if any)
# sudo -u $APP_USER $APP_DIR/venv/bin/python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart the-plugs
sudo systemctl restart the-plugs-celery
sudo systemctl reload nginx

echo "Deployment completed successfully!"
EOF

sudo chmod +x $APP_DIR/deploy.sh

# Create environment file template
echo -e "${YELLOW}Creating environment file template...${NC}"
sudo tee $APP_DIR/.env.template > /dev/null <<EOF
# The Plugs Backend Environment Configuration
# Copy this file to .env and fill in your values

# Application
ENVIRONMENT=production
DEBUG=false
APP_NAME=The Plugs API
APP_VERSION=1.0.0

# Database (RDS)
DATABASE_URL=postgresql://username:password@your-rds-endpoint:5432/the_plugs_db

# Redis (ElastiCache)
REDIS_URL=redis://your-elasticache-endpoint:6379/0

# Security
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# AWS S3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-s3-bucket-name

# Email (SendGrid)
SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@yourdomain.com

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_HEADERS=*

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/the-plugs/app.log

# Celery
CELERY_BROKER_URL=redis://your-elasticache-endpoint:6379/1
CELERY_RESULT_BACKEND=redis://your-elasticache-endpoint:6379/2
EOF

echo -e "${GREEN}EC2 setup completed successfully!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Configure AWS CLI: aws configure"
echo "2. Set up RDS PostgreSQL database"
echo "3. Set up ElastiCache Redis"
echo "4. Set up S3 bucket for file storage"
echo "5. Deploy your application code"
echo "6. Configure SSL certificate with Let's Encrypt"
echo "7. Update DNS records to point to this server"

echo -e "${GREEN}Setup completed!${NC}"
