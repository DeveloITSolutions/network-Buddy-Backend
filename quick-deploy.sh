#!/bin/bash

# Quick AWS Deployment Script for The Plugs Backend
# Usage: ./quick-deploy.sh YOUR_EC2_PUBLIC_IP

set -e

EC2_IP=$1
PEM_FILE="~/Downloads/plugss.pem"

if [ -z "$EC2_IP" ]; then
    echo "Usage: ./quick-deploy.sh YOUR_EC2_PUBLIC_IP"
    echo "Example: ./quick-deploy.sh 3.15.123.45"
    exit 1
fi

echo "🚀 Starting deployment to EC2 instance: $EC2_IP"

# Step 1: Connect and setup EC2
echo "📦 Setting up EC2 instance..."
ssh -i $PEM_FILE ec2-user@$EC2_IP << 'EOF'
# Update system
sudo yum update -y

# Install Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo yum install -y git

# Install Nginx
sudo yum install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Install AWS CLI
sudo yum install -y aws-cli

echo "✅ EC2 setup completed"
EOF

# Step 2: Clone repository and setup
echo "📁 Cloning repository and setting up..."
ssh -i $PEM_FILE ec2-user@$EC2_IP << 'EOF'
# Clone repository
if [ -d "the_plugs_network" ]; then
    cd the_plugs_network
    git pull origin main
else
    git clone https://github.com/shahzaibyyy/the_plugs_network.git
    cd the_plugs_network
fi

# Create production environment file
cat > .env.production << 'ENVEOF'
# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secret-key-change-this-in-production-$(date +%s)

# Database (will be updated after RDS setup)
DATABASE_URL=postgresql://theplugsadmin:YourSecurePassword123!@localhost:5432/the_plugs

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Security
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# External Services
HUBSPOT_API_KEY=your-hubspot-api-key

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=the-plugs-files

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
ENVEOF

echo "✅ Repository setup completed"
EOF

# Step 3: Setup RDS (via AWS CLI)
echo "🗄️ Setting up RDS database..."
ssh -i $PEM_FILE ec2-user@$EC2_IP << 'EOF'
# Configure AWS CLI (you'll need to run this manually)
echo "Please configure AWS CLI with: aws configure"
echo "Then run the RDS creation commands manually:"
echo ""
echo "# Create RDS instance"
echo "aws rds create-db-instance \\"
echo "    --db-instance-identifier the-plugs-db \\"
echo "    --db-instance-class db.m5.large \\"
echo "    --engine postgres \\"
echo "    --engine-version 13.7 \\"
echo "    --master-username theplugsadmin \\"
echo "    --master-user-password YourSecurePassword123! \\"
echo "    --allocated-storage 20 \\"
echo "    --vpc-security-group-ids sg-12345678 \\"
echo "    --backup-retention-period 7 \\"
echo "    --multi-az \\"
echo "    --storage-encrypted \\"
echo "    --storage-type gp2"
echo ""
echo "Wait for RDS to be available, then get the endpoint:"
echo "aws rds describe-db-instances --db-instance-identifier the-plugs-db --query 'DBInstances[0].Endpoint.Address' --output text"
EOF

# Step 4: Setup S3
echo "🪣 Setting up S3 bucket..."
ssh -i $PEM_FILE ec2-user@$EC2_IP << 'EOF'
# Create S3 bucket
BUCKET_NAME="the-plugs-files-$(date +%s)"
aws s3 mb s3://$BUCKET_NAME

# Create folders
aws s3api put-object --bucket $BUCKET_NAME --key uploads/images/
aws s3api put-object --bucket $BUCKET_NAME --key uploads/documents/
aws s3api put-object --bucket $BUCKET_NAME --key uploads/audio/
aws s3api put-object --bucket $BUCKET_NAME --key uploads/videos/

echo "S3 Bucket created: $BUCKET_NAME"
echo "Update .env.production with: S3_BUCKET_NAME=$BUCKET_NAME"
EOF

# Step 5: Configure Nginx
echo "🌐 Configuring Nginx..."
ssh -i $PEM_FILE ec2-user@$EC2_IP << 'EOF'
# Create Nginx configuration
sudo tee /etc/nginx/conf.d/the-plugs.conf << 'NGINXEOF'
upstream fastapi {
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

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss;

    # Client max body size for file uploads
    client_max_body_size 100M;

    # Proxy to FastAPI
    location / {
        proxy_pass http://fastapi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://fastapi/health;
        access_log off;
    }
}
NGINXEOF

# Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx

echo "✅ Nginx configured"
EOF

# Step 6: Create production docker-compose
echo "🐳 Creating production Docker setup..."
ssh -i $PEM_FILE ec2-user@$EC2_IP << 'EOF'
cd the_plugs_network

# Create production docker-compose file
cat > docker-compose.prod.yml << 'COMPOSEEOF'
version: '3.8'

services:
  api:
    build: .
    container_name: the-plugs-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      - redis
    networks:
      - the-plugs-network

  redis:
    image: redis:7-alpine
    container_name: the-plugs-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - the-plugs-network

  celery-worker:
    build: .
    container_name: the-plugs-celery-worker
    restart: unless-stopped
    command: celery -A app.workers.celery_app worker --loglevel=info
    env_file:
      - .env.production
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      - redis
    networks:
      - the-plugs-network

  celery-beat:
    build: .
    container_name: the-plugs-celery-beat
    restart: unless-stopped
    command: celery -A app.workers.celery_app beat --loglevel=info
    env_file:
      - .env.production
    depends_on:
      - redis
    networks:
      - the-plugs-network

  celery-flower:
    build: .
    container_name: the-plugs-celery-flower
    restart: unless-stopped
    command: celery -A app.workers.celery_app flower --port=5555
    ports:
      - "5555:5555"
    env_file:
      - .env.production
    depends_on:
      - redis
    networks:
      - the-plugs-network

volumes:
  redis_data:

networks:
  the-plugs-network:
    driver: bridge
COMPOSEEOF

echo "✅ Docker Compose file created"
EOF

# Step 7: Deploy application
echo "🚀 Deploying application..."
ssh -i $PEM_FILE ec2-user@$EC2_IP << 'EOF'
cd the_plugs_network

# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

# Wait a moment for services to start
sleep 30

# Check service status
docker-compose -f docker-compose.prod.yml ps

echo "✅ Application deployed"
EOF

# Step 8: Test deployment
echo "🧪 Testing deployment..."
ssh -i $PEM_FILE ec2-user@$EC2_IP << 'EOF'
# Test API health
echo "Testing API health..."
curl -f http://localhost:8000/health || echo "API health check failed"

# Test through Nginx
echo "Testing through Nginx..."
curl -f http://localhost/health || echo "Nginx proxy test failed"

# Check all services
echo "Service status:"
docker-compose -f docker-compose.prod.yml ps
EOF

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📋 Next steps:"
echo "1. Configure AWS CLI: ssh -i $PEM_FILE ec2-user@$EC2_IP 'aws configure'"
echo "2. Create RDS instance (see AWS_DEPLOYMENT_GUIDE.md)"
echo "3. Update .env.production with RDS endpoint and S3 bucket name"
echo "4. Run database migrations: ssh -i $PEM_FILE ec2-user@$EC2_IP 'cd the_plugs_network && docker-compose -f docker-compose.prod.yml exec api alembic upgrade head'"
echo ""
echo "🌐 Your API should be available at:"
echo "   - Direct: http://$EC2_IP:8000"
echo "   - Through Nginx: http://$EC2_IP"
echo "   - API Docs: http://$EC2_IP/docs"
echo "   - Health Check: http://$EC2_IP/health"
echo ""
echo "📊 Monitor your application:"
echo "   - Service logs: ssh -i $PEM_FILE ec2-user@$EC2_IP 'cd the_plugs_network && docker-compose -f docker-compose.prod.yml logs -f'"
echo "   - Service status: ssh -i $PEM_FILE ec2-user@$EC2_IP 'cd the_plugs_network && docker-compose -f docker-compose.prod.yml ps'"
echo ""
echo "🔧 For troubleshooting, see AWS_DEPLOYMENT_GUIDE.md"
