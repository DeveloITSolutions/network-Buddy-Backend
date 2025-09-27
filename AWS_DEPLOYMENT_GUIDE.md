# AWS Deployment Guide for The Plugs Backend

## Overview

This guide will help you deploy your dockerized FastAPI backend on AWS using:
- **EC2 Instance**: m5.large for FastAPI backend
- **RDS**: m5.large for PostgreSQL database
- **S3**: For file storage and static assets
- **Nginx**: For reverse proxy and SSL termination

## Prerequisites

- AWS CLI configured with appropriate permissions
- EC2 instance running (m5.large)
- PEM file: `plugss.pem` in Downloads directory
- Domain name (optional, we'll use public IP for now)

## Step 1: Connect to EC2 Instance

```bash
# Navigate to Downloads directory
cd ~/Downloads

# Set proper permissions for PEM file
chmod 400 plugss.pem

# Connect to your EC2 instance (replace with your instance IP)
ssh -i plugss.pem ec2-user@YOUR_EC2_PUBLIC_IP
```

## Step 2: Install Required Software on EC2

```bash
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

# Install AWS CLI (if not already installed)
sudo yum install -y aws-cli

# Logout and login again to apply docker group changes
exit
```

## Step 3: Clone Repository and Setup

```bash
# Reconnect to EC2
ssh -i ~/Downloads/plugss.pem ec2-user@YOUR_EC2_PUBLIC_IP

# Clone your repository
git clone https://github.com/shahzaibyyy/the_plugs_network.git
cd the_plugs_network

# Create production environment file
cat > .env.production << EOF
# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secret-key-change-this-in-production

# Database (will be updated after RDS setup)
DATABASE_URL=postgresql://username:password@localhost:5432/the_plugs

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
EOF
```

## Step 4: Setup RDS Database

### Create RDS Instance via AWS CLI

```bash
# Configure AWS CLI (if not already done)
aws configure

# Create RDS subnet group
aws rds create-db-subnet-group \
    --db-subnet-group-name the-plugs-subnet-group \
    --db-subnet-group-description "Subnet group for The Plugs RDS" \
    --subnet-ids subnet-12345678 subnet-87654321

# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier the-plugs-db \
    --db-instance-class db.m5.large \
    --engine postgres \
    --engine-version 13.7 \
    --master-username theplugsadmin \
    --master-user-password YourSecurePassword123! \
    --allocated-storage 20 \
    --vpc-security-group-ids sg-12345678 \
    --db-subnet-group-name the-plugs-subnet-group \
    --backup-retention-period 7 \
    --multi-az \
    --storage-encrypted \
    --storage-type gp2

# Wait for RDS to be available (this takes 10-15 minutes)
aws rds describe-db-instances --db-instance-identifier the-plugs-db
```

### Alternative: Create RDS via AWS Console

1. Go to AWS RDS Console
2. Click "Create database"
3. Choose "PostgreSQL"
4. Select "Production" template
5. DB instance identifier: `the-plugs-db`
6. Master username: `theplugsadmin`
7. Master password: `YourSecurePassword123!`
8. DB instance class: `db.m5.large`
9. Storage: 20 GB
10. Enable Multi-AZ deployment
11. Enable encryption
12. Create database

## Step 5: Setup S3 Bucket

```bash
# Create S3 bucket
aws s3 mb s3://the-plugs-files-$(date +%s)

# Create bucket policy for public read access to uploaded files
cat > bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::the-plugs-files-*/*"
        }
    ]
}
EOF

# Apply bucket policy
aws s3api put-bucket-policy --bucket the-plugs-files-$(date +%s) --policy file://bucket-policy.json

# Create folders for different file types
aws s3api put-object --bucket the-plugs-files-$(date +%s) --key uploads/images/
aws s3api put-object --bucket the-plugs-files-$(date +%s) --key uploads/documents/
aws s3api put-object --bucket the-plugs-files-$(date +%s) --key uploads/audio/
aws s3api put-object --bucket the-plugs-files-$(date +%s) --key uploads/videos/
```

## Step 6: Update Environment Configuration

```bash
# Get RDS endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances --db-instance-identifier the-plugs-db --query 'DBInstances[0].Endpoint.Address' --output text)

# Update .env.production with RDS endpoint
sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql://theplugsadmin:YourSecurePassword123!@${RDS_ENDPOINT}:5432/the_plugs|g" .env.production

# Update S3 bucket name (replace with your actual bucket name)
BUCKET_NAME=$(aws s3 ls | grep the-plugs-files | awk '{print $3}' | head -1)
sed -i "s|S3_BUCKET_NAME=.*|S3_BUCKET_NAME=${BUCKET_NAME}|g" .env.production
```

## Step 7: Configure Nginx

```bash
# Create Nginx configuration
sudo tee /etc/nginx/conf.d/the-plugs.conf << EOF
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
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
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

    # Static files (if serving any)
    location /static/ {
        alias /var/www/the-plugs/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

## Step 8: Deploy Application with Docker

```bash
# Create production docker-compose file
cat > docker-compose.prod.yml << EOF
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
EOF

# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

# Check if services are running
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f api
```

## Step 9: Run Database Migrations

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Create superuser (optional)
docker-compose -f docker-compose.prod.yml exec api python -c "
from app.models.user import User
from app.config.database import get_db
from sqlalchemy.orm import Session
import hashlib

db = next(get_db())
user = User(
    email='admin@theplugs.com',
    password=hashlib.sha256('admin123'.encode()).hexdigest(),
    first_name='Admin',
    last_name='User',
    timezone='UTC'
)
db.add(user)
db.commit()
print('Superuser created')
"
```

## Step 10: Setup SSL with Let's Encrypt (Optional)

```bash
# Install Certbot
sudo yum install -y certbot python3-certbot-nginx

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

## Step 11: Setup Monitoring and Logging

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
sudo rpm -U ./amazon-cloudwatch-agent.rpm

# Create CloudWatch config
sudo tee /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOF
{
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/var/log/nginx/access.log",
                        "log_group_name": "/aws/ec2/the-plugs/nginx",
                        "log_stream_name": "{instance_id}"
                    },
                    {
                        "file_path": "/var/log/nginx/error.log",
                        "log_group_name": "/aws/ec2/the-plugs/nginx",
                        "log_stream_name": "{instance_id}"
                    }
                ]
            }
        }
    },
    "metrics": {
        "namespace": "ThePlugs/EC2",
        "metrics_collected": {
            "cpu": {
                "measurement": ["cpu_usage_idle", "cpu_usage_iowait", "cpu_usage_user", "cpu_usage_system"],
                "metrics_collection_interval": 60
            },
            "disk": {
                "measurement": ["used_percent"],
                "metrics_collection_interval": 60,
                "resources": ["*"]
            },
            "mem": {
                "measurement": ["mem_used_percent"],
                "metrics_collection_interval": 60
            }
        }
    }
}
EOF

# Start CloudWatch agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
    -s
```

## Step 12: Setup Auto-deployment Script

```bash
# Create deployment script
cat > deploy.sh << 'EOF'
#!/bin/bash

echo "Starting deployment..."

# Pull latest changes
git pull origin main

# Rebuild and restart services
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Restart Nginx
sudo systemctl restart nginx

echo "Deployment completed!"
EOF

chmod +x deploy.sh
```

## Step 13: Security Configuration

```bash
# Configure firewall
sudo yum install -y firewalld
sudo systemctl start firewalld
sudo systemctl enable firewalld

# Allow necessary ports
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload

# Update system regularly
echo "0 2 * * 0 yum update -y" | sudo crontab -
```

## Step 14: Test Deployment

```bash
# Test API health
curl http://localhost:8000/health

# Test through Nginx
curl http://YOUR_EC2_PUBLIC_IP/health

# Test API documentation
curl http://YOUR_EC2_PUBLIC_IP/docs

# Check all services
docker-compose -f docker-compose.prod.yml ps
```

## Step 15: Backup Strategy

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash

# Create backup directory
mkdir -p /home/ec2-user/backups/$(date +%Y%m%d)

# Backup database
docker-compose -f docker-compose.prod.yml exec -T api pg_dump $DATABASE_URL > /home/ec2-user/backups/$(date +%Y%m%d)/database.sql

# Backup uploads
tar -czf /home/ec2-user/backups/$(date +%Y%m%d)/uploads.tar.gz uploads/

# Upload to S3
aws s3 cp /home/ec2-user/backups/$(date +%Y%m%d)/ s3://your-backup-bucket/$(date +%Y%m%d)/ --recursive

# Clean old backups (keep 7 days)
find /home/ec2-user/backups -type d -mtime +7 -exec rm -rf {} \;
EOF

chmod +x backup.sh

# Schedule daily backups
echo "0 3 * * * /home/ec2-user/backup.sh" | crontab -
```

## Monitoring Commands

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f celery-worker

# Check system resources
htop
df -h
free -h

# Check Nginx status
sudo systemctl status nginx
sudo nginx -t

# Monitor API performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check RDS security groups
   aws ec2 describe-security-groups --group-ids sg-12345678
   
   # Test database connection
   docker-compose -f docker-compose.prod.yml exec api python -c "
   from app.config.database import get_db
   db = next(get_db())
   print('Database connected successfully')
   "
   ```

2. **Nginx Issues**
   ```bash
   # Check Nginx configuration
   sudo nginx -t
   
   # Check Nginx logs
   sudo tail -f /var/log/nginx/error.log
   ```

3. **Docker Issues**
   ```bash
   # Check Docker logs
   docker-compose -f docker-compose.prod.yml logs api
   
   # Restart services
   docker-compose -f docker-compose.prod.yml restart
   ```

## Production Checklist

- [ ] RDS instance created and accessible
- [ ] S3 bucket created and configured
- [ ] Environment variables set correctly
- [ ] Nginx configured and running
- [ ] Docker services running
- [ ] Database migrations applied
- [ ] SSL certificate installed (if using domain)
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Security groups configured
- [ ] Firewall rules applied

## Next Steps

1. **Domain Setup**: Configure Route 53 and ACM for custom domain
2. **CDN**: Setup CloudFront for static assets
3. **Load Balancer**: Add Application Load Balancer for high availability
4. **Auto Scaling**: Configure Auto Scaling Groups
5. **Monitoring**: Setup CloudWatch dashboards and alarms

Your FastAPI backend should now be successfully deployed on AWS! 🚀

## Quick Commands Summary

```bash
# Connect to EC2
ssh -i ~/Downloads/plugss.pem ec2-user@YOUR_EC2_PUBLIC_IP

# Deploy application
cd the_plugs_network
docker-compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Check status
docker-compose -f docker-compose.prod.yml ps
curl http://YOUR_EC2_PUBLIC_IP/health
```

For any issues, check the logs and refer to the troubleshooting section above.

