#!/bin/bash

# RDS Setup Script for The Plugs Backend
# Usage: ./setup-rds.sh

set -e

echo "🗄️ Setting up RDS database for The Plugs Backend..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ AWS CLI configured"

# Get VPC and subnet information
echo "🔍 Getting VPC information..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)
echo "VPC ID: $VPC_ID"

# Get subnets
SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[].SubnetId' --output text)
SUBNET_ARRAY=($SUBNETS)
echo "Subnets: ${SUBNET_ARRAY[*]}"

# Create DB subnet group
echo "📦 Creating DB subnet group..."
aws rds create-db-subnet-group \
    --db-subnet-group-name the-plugs-subnet-group \
    --db-subnet-group-description "Subnet group for The Plugs RDS" \
    --subnet-ids ${SUBNET_ARRAY[0]} ${SUBNET_ARRAY[1]} || echo "Subnet group may already exist"

# Get default security group
SECURITY_GROUP_ID=$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=default" --query 'SecurityGroups[0].GroupId' --output text)
echo "Security Group ID: $SECURITY_GROUP_ID"

# Add PostgreSQL port to security group
echo "🔒 Adding PostgreSQL port to security group..."
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 5432 \
    --cidr 0.0.0.0/0 || echo "Rule may already exist"

# Create RDS instance
echo "🚀 Creating RDS instance..."
aws rds create-db-instance \
    --db-instance-identifier the-plugs-db \
    --db-instance-class db.m5.large \
    --engine postgres \
    --engine-version 13.7 \
    --master-username theplugsadmin \
    --master-user-password YourSecurePassword123! \
    --allocated-storage 20 \
    --vpc-security-group-ids $SECURITY_GROUP_ID \
    --db-subnet-group-name the-plugs-subnet-group \
    --backup-retention-period 7 \
    --multi-az \
    --storage-encrypted \
    --storage-type gp2 \
    --publicly-accessible

echo "⏳ RDS instance creation started. This will take 10-15 minutes..."

# Wait for RDS to be available
echo "🔄 Waiting for RDS instance to be available..."
aws rds wait db-instance-available --db-instance-identifier the-plugs-db

# Get RDS endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances --db-instance-identifier the-plugs-db --query 'DBInstances[0].Endpoint.Address' --output text)
echo "✅ RDS instance created successfully!"
echo "📡 RDS Endpoint: $RDS_ENDPOINT"

# Create S3 bucket
echo "🪣 Creating S3 bucket..."
BUCKET_NAME="the-plugs-files-$(date +%s)"
aws s3 mb s3://$BUCKET_NAME

# Create folders in S3
aws s3api put-object --bucket $BUCKET_NAME --key uploads/images/
aws s3api put-object --bucket $BUCKET_NAME --key uploads/documents/
aws s3api put-object --bucket $BUCKET_NAME --key uploads/audio/
aws s3api put-object --bucket $BUCKET_NAME --key uploads/videos/

echo "✅ S3 bucket created: $BUCKET_NAME"

# Create environment update script
cat > update-env.sh << EOF
#!/bin/bash
# Update .env.production with RDS and S3 details

RDS_ENDPOINT="$RDS_ENDPOINT"
BUCKET_NAME="$BUCKET_NAME"

# Update database URL
sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql://theplugsadmin:YourSecurePassword123!@\${RDS_ENDPOINT}:5432/the_plugs|g" .env.production

# Update S3 bucket name
sed -i "s|S3_BUCKET_NAME=.*|S3_BUCKET_NAME=\${BUCKET_NAME}|g" .env.production

echo "✅ Environment updated with RDS endpoint: \$RDS_ENDPOINT"
echo "✅ Environment updated with S3 bucket: \$BUCKET_NAME"
EOF

chmod +x update-env.sh

echo ""
echo "🎉 RDS and S3 setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Run: ./update-env.sh (to update .env.production)"
echo "2. Restart your application: docker-compose -f docker-compose.prod.yml restart"
echo "3. Run migrations: docker-compose -f docker-compose.prod.yml exec api alembic upgrade head"
echo ""
echo "🔗 RDS Endpoint: $RDS_ENDPOINT"
echo "🪣 S3 Bucket: $BUCKET_NAME"
echo ""
echo "🔧 To connect to your database:"
echo "   psql -h $RDS_ENDPOINT -U theplugsadmin -d the_plugs"
