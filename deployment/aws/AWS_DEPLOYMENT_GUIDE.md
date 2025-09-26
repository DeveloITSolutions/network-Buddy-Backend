# AWS Deployment Guide for The Plugs Backend

## Overview
This guide provides step-by-step instructions for deploying The Plugs FastAPI backend on AWS using EC2, RDS, ElastiCache, and S3.

## Architecture
```
Internet → Route 53 → CloudFront → ALB → EC2 (FastAPI) → RDS (PostgreSQL) + ElastiCache (Redis) + S3 (Files)
```

## Prerequisites
- AWS Account with appropriate permissions
- Domain name (optional, can use EC2 public IP)
- AWS CLI installed and configured
- SSH key pair for EC2 access

## Step 1: Launch EC2 Instance

### 1.1 Create EC2 Instance
```bash
# Launch m5.large instance
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --instance-type m5.large \
    --key-name your-key-pair \
    --security-groups your-security-group \
    --subnet-id your-subnet-id \
    --associate-public-ip-address \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=the-plugs-backend}]'
```

### 1.2 Connect to EC2 Instance
```bash
ssh -i your-key-pair.pem ubuntu@your-ec2-public-ip
```

### 1.3 Run EC2 Setup Script
```bash
# Download and run the setup script
curl -O https://raw.githubusercontent.com/your-repo/the-plugs-backend/main/deployment/aws/ec2-setup.sh
chmod +x ec2-setup.sh
sudo ./ec2-setup.sh
```

## Step 2: Set Up RDS PostgreSQL Database

### 2.1 Run RDS Setup Script
```bash
# Update the configuration in the script first
nano deployment/aws/rds-setup.sh

# Run the script
chmod +x deployment/aws/rds-setup.sh
./deployment/aws/rds-setup.sh
```

### 2.2 Configure Database Connection
Update your `.env` file with the RDS connection details:
```bash
DATABASE_URL=postgresql://plugs_admin:your-password@your-rds-endpoint:5432/the_plugs_db
```

## Step 3: Set Up ElastiCache Redis

### 3.1 Run ElastiCache Setup Script
```bash
# Update the configuration in the script first
nano deployment/aws/elasticache-setup.sh

# Run the script
chmod +x deployment/aws/elasticache-setup.sh
./deployment/aws/elasticache-setup.sh
```

### 3.2 Configure Redis Connection
Update your `.env` file with the ElastiCache connection details:
```bash
REDIS_URL=redis://your-elasticache-endpoint:6379/0
CELERY_BROKER_URL=redis://your-elasticache-endpoint:6379/1
CELERY_RESULT_BACKEND=redis://your-elasticache-endpoint:6379/2
```

## Step 4: Set Up S3 for File Storage

### 4.1 Run S3 Setup Script
```bash
# Update the configuration in the script first
nano deployment/aws/s3-setup.sh

# Run the script
chmod +x deployment/aws/s3-setup.sh
./deployment/aws/s3-setup.sh
```

### 4.2 Configure S3 Connection
Update your `.env` file with the S3 details:
```bash
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
S3_BASE_URL=https://your-bucket-name.s3.us-east-1.amazonaws.com
```

## Step 5: Deploy Application

### 5.1 Clone Repository
```bash
cd /opt/the-plugs
sudo -u plugs git clone https://github.com/your-repo/the-plugs-backend.git .
```

### 5.2 Set Up Python Environment
```bash
sudo -u plugs python3.11 -m venv venv
sudo -u plugs venv/bin/pip install -r requirements.txt
```

### 5.3 Configure Environment
```bash
sudo -u plugs cp .env.template .env
sudo -u plugs nano .env
```

### 5.4 Run Database Migrations
```bash
sudo -u plugs venv/bin/alembic upgrade head
```

### 5.5 Start Services
```bash
sudo systemctl enable the-plugs
sudo systemctl enable the-plugs-celery
sudo systemctl start the-plugs
sudo systemctl start the-plugs-celery
sudo systemctl reload nginx
```

## Step 6: Configure SSL Certificate

### 6.1 Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx
```

### 6.2 Obtain SSL Certificate
```bash
sudo certbot --nginx -d yourdomain.com
```

## Step 7: Configure Monitoring and Logging

### 7.1 Install CloudWatch Agent
```bash
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb
```

### 7.2 Configure CloudWatch
```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

## Step 8: Set Up Auto-Scaling (Optional)

### 8.1 Create Launch Template
```bash
aws ec2 create-launch-template \
    --launch-template-name the-plugs-template \
    --launch-template-data file://launch-template.json
```

### 8.2 Create Auto Scaling Group
```bash
aws autoscaling create-auto-scaling-group \
    --auto-scaling-group-name the-plugs-asg \
    --launch-template LaunchTemplateName=the-plugs-template,Version=1 \
    --min-size 1 \
    --max-size 3 \
    --desired-capacity 1 \
    --vpc-zone-identifier subnet-12345,subnet-67890
```

## Environment Configuration

### Production Environment Variables
```bash
# Application
ENVIRONMENT=production
DEBUG=false
APP_NAME=The Plugs API
APP_VERSION=1.0.0

# Database (RDS)
DATABASE_URL=postgresql://plugs_admin:password@your-rds-endpoint:5432/the_plugs_db

# Redis (ElastiCache)
REDIS_URL=redis://your-elasticache-endpoint:6379/0
CELERY_BROKER_URL=redis://your-elasticache-endpoint:6379/1
CELERY_RESULT_BACKEND=redis://your-elasticache-endpoint:6379/2

# AWS S3
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
S3_BASE_URL=https://your-bucket-name.s3.us-east-1.amazonaws.com

# Security
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

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
```

## Security Considerations

### 1. Security Groups
- EC2: Allow SSH (22), HTTP (80), HTTPS (443)
- RDS: Allow PostgreSQL (5432) from EC2 security group
- ElastiCache: Allow Redis (6379) from EC2 security group

### 2. IAM Roles
- Create IAM role for EC2 with S3 access
- Use least privilege principle
- Rotate access keys regularly

### 3. Database Security
- Use strong passwords
- Enable encryption at rest
- Regular backups
- Multi-AZ deployment

### 4. Application Security
- Use HTTPS only
- Implement rate limiting
- Regular security updates
- Monitor logs for suspicious activity

## Monitoring and Maintenance

### 1. CloudWatch Metrics
- CPU utilization
- Memory usage
- Disk I/O
- Network I/O
- Database connections
- Application errors

### 2. Log Management
- Centralized logging with CloudWatch Logs
- Log rotation
- Error alerting
- Performance monitoring

### 3. Backup Strategy
- RDS automated backups
- S3 versioning
- Application code backups
- Configuration backups

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check RDS security groups
   aws rds describe-db-instances --db-instance-identifier the-plugs-db
   
   # Test connection
   psql -h your-rds-endpoint -U plugs_admin -d the_plugs_db
   ```

2. **Redis Connection Issues**
   ```bash
   # Check ElastiCache security groups
   aws elasticache describe-cache-clusters --cache-cluster-id the-plugs-redis
   
   # Test connection
   redis-cli -h your-elasticache-endpoint -p 6379 ping
   ```

3. **S3 Access Issues**
   ```bash
   # Check IAM permissions
   aws s3 ls s3://your-bucket-name
   
   # Test upload
   aws s3 cp test.txt s3://your-bucket-name/
   ```

4. **Application Issues**
   ```bash
   # Check service status
   sudo systemctl status the-plugs
   sudo systemctl status the-plugs-celery
   
   # Check logs
   sudo journalctl -u the-plugs -f
   sudo tail -f /var/log/the-plugs/app.log
   ```

## Cost Optimization

### 1. Instance Sizing
- Start with m5.large, scale based on usage
- Use Spot instances for non-critical workloads
- Implement auto-scaling

### 2. Storage Optimization
- Use S3 lifecycle policies
- Compress files before upload
- Use appropriate storage classes

### 3. Database Optimization
- Use appropriate instance sizes
- Enable automated backups
- Monitor performance metrics

## Deployment Checklist

- [ ] EC2 instance launched and configured
- [ ] RDS PostgreSQL database created
- [ ] ElastiCache Redis cluster created
- [ ] S3 bucket created and configured
- [ ] Application deployed and running
- [ ] SSL certificate installed
- [ ] Monitoring configured
- [ ] Security groups properly configured
- [ ] IAM roles and policies set up
- [ ] Backup strategy implemented
- [ ] DNS records updated
- [ ] Load testing completed
- [ ] Documentation updated

## Support and Maintenance

### Regular Tasks
- Security updates
- Performance monitoring
- Backup verification
- Log analysis
- Cost optimization review

### Emergency Procedures
- Incident response plan
- Rollback procedures
- Contact information
- Escalation procedures

## Conclusion

This deployment guide provides a comprehensive approach to deploying The Plugs backend on AWS. The architecture is scalable, secure, and cost-effective. Regular monitoring and maintenance will ensure optimal performance and reliability.

For additional support or questions, refer to the AWS documentation or contact your DevOps team.
