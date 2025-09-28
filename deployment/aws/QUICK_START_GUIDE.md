# Quick Start Guide - AWS Deployment

## 🚀 Get Your Backend Running in 30 Minutes

This guide will help you deploy The Plugs backend to AWS quickly and efficiently.

## Prerequisites Checklist

- [ ] AWS Account with admin access
- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] SSH key pair for EC2 access
- [ ] Domain name (optional - can use EC2 public IP)

## Step-by-Step Deployment

### 1. Launch EC2 Instance (5 minutes)

```bash
# Launch m5.large instance
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --instance-type m5.large \
    --key-name your-key-pair \
    --security-groups default \
    --associate-public-ip-address \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=the-plugs-backend}]'
```

**Note**: Replace `your-key-pair` with your actual SSH key pair name.

### 2. Connect to Your Instance (2 minutes)

```bash
# Get your instance public IP
aws ec2 describe-instances --filters "Name=tag:Name,Values=the-plugs-backend" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text

# Connect via SSH
ssh -i your-key-pair.pem ubuntu@YOUR_INSTANCE_IP
```

### 3. Run the Setup Script (10 minutes)

```bash
# Download and run the EC2 setup script
curl -O https://raw.githubusercontent.com/your-repo/the-plugs-backend/main/deployment/aws/ec2-setup.sh
chmod +x ec2-setup.sh
sudo ./ec2-setup.sh
```

### 4. Set Up Database (5 minutes)

```bash
# Download and run the RDS setup script
curl -O https://raw.githubusercontent.com/your-repo/the-plugs-backend/main/deployment/aws/rds-setup.sh
chmod +x rds-setup.sh
./rds-setup.sh
```

**Important**: Update the VPC and subnet IDs in the script before running.

### 5. Set Up Redis Cache (3 minutes)

```bash
# Download and run the ElastiCache setup script
curl -O https://raw.githubusercontent.com/your-repo/the-plugs-backend/main/deployment/aws/elasticache-setup.sh
chmod +x elasticache-setup.sh
./elasticache-setup.sh
```

### 6. Set Up File Storage (2 minutes)

```bash
# Download and run the S3 setup script
curl -O https://raw.githubusercontent.com/your-repo/the-plugs-backend/main/deployment/aws/s3-setup.sh
chmod +x s3-setup.sh
./s3-setup.sh
```

### 7. Deploy Your Application (3 minutes)

```bash
# Clone your repository
cd /opt/the-plugs
sudo -u plugs git clone https://github.com/your-repo/the-plugs-backend.git .

# Set up Python environment
sudo -u plugs python3.11 -m venv venv
sudo -u plugs venv/bin/pip install -r requirements.txt

# Configure environment
sudo -u plugs cp .env.template .env
sudo -u plugs nano .env
```

**Update the `.env` file with the connection details from the previous steps.**

### 8. Start Your Services (2 minutes)

```bash
# Run database migrations
sudo -u plugs venv/bin/alembic upgrade head

# Start services
sudo systemctl enable the-plugs
sudo systemctl enable the-plugs-celery
sudo systemctl start the-plugs
sudo systemctl start the-plugs-celery
sudo systemctl reload nginx
```

### 9. Test Your Deployment (1 minute)

```bash
# Test API health
curl http://YOUR_INSTANCE_IP/health

# Test API endpoint
curl http://YOUR_INSTANCE_IP/api/v1/events/
```

## 🎉 You're Done!

Your backend is now running at: `http://YOUR_INSTANCE_IP/api/v1/`

## Next Steps (Optional)

### Set Up SSL Certificate
```bash
sudo certbot --nginx -d yourdomain.com
```

### Set Up Monitoring
```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

## 🔧 Configuration Files

All configuration files are located in `/opt/the-plugs/`:

- `.env` - Environment variables
- `nginx.conf` - Web server configuration
- `deploy.sh` - Deployment script

## 📊 Monitoring Your Application

### Check Service Status
```bash
sudo systemctl status the-plugs
sudo systemctl status the-plugs-celery
```

### View Logs
```bash
# Application logs
sudo tail -f /var/log/the-plugs/app.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Restart Services
```bash
sudo systemctl restart the-plugs
sudo systemctl restart the-plugs-celery
sudo systemctl reload nginx
```

## 🚨 Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   sudo journalctl -u the-plugs -f
   ```

2. **Database connection failed**
   - Check RDS security groups
   - Verify DATABASE_URL in .env

3. **Redis connection failed**
   - Check ElastiCache security groups
   - Verify REDIS_URL in .env

4. **S3 access denied**
   - Check IAM permissions
   - Verify AWS credentials

### Get Help

- Check the full [AWS Deployment Guide](AWS_DEPLOYMENT_GUIDE.md)
- Review service logs for error messages
- Ensure all security groups allow necessary traffic

## 💰 Cost Optimization

- **EC2**: Start with m5.large, scale based on usage
- **RDS**: Use appropriate instance size for your data
- **S3**: Enable lifecycle policies for cost savings
- **ElastiCache**: Start with cache.t3.micro, scale up as needed

## 🔒 Security Checklist

- [ ] Security groups properly configured
- [ ] Database not publicly accessible
- [ ] Redis not publicly accessible
- [ ] Strong passwords used
- [ ] SSL certificate installed
- [ ] Regular security updates enabled

## 📈 Scaling

When you need to scale:

1. **Vertical Scaling**: Increase instance sizes
2. **Horizontal Scaling**: Add more instances behind a load balancer
3. **Auto Scaling**: Set up auto-scaling groups
4. **Database Scaling**: Use RDS read replicas

---

**Need help?** Check the full documentation or contact your DevOps team.

**Happy coding!** 🚀






