#!/bin/bash

# AWS RDS PostgreSQL Setup Script for The Plugs Backend
# This script creates and configures RDS PostgreSQL instance

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration - Update these values
DB_INSTANCE_IDENTIFIER="the-plugs-db"
DB_NAME="the_plugs_db"
DB_USERNAME="plugs_admin"
DB_PASSWORD="your-secure-password-here"  # Change this!
DB_INSTANCE_CLASS="db.m5.large"
DB_ENGINE="postgres"
DB_ENGINE_VERSION="15.4"
DB_ALLOCATED_STORAGE=20
DB_MAX_ALLOCATED_STORAGE=100
DB_SUBNET_GROUP_NAME="the-plugs-db-subnet-group"
DB_SECURITY_GROUP_NAME="the-plugs-db-sg"
VPC_ID="vpc-xxxxxxxxx"  # Update with your VPC ID
SUBNET_IDS="subnet-xxxxxxxxx,subnet-yyyyyyyyy"  # Update with your subnet IDs

echo -e "${GREEN}Starting RDS PostgreSQL setup for The Plugs Backend...${NC}"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}AWS CLI is not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Get current region
AWS_REGION=$(aws configure get region)
echo -e "${YELLOW}Using AWS Region: $AWS_REGION${NC}"

# Create DB subnet group
echo -e "${YELLOW}Creating DB subnet group...${NC}"
aws rds create-db-subnet-group \
    --db-subnet-group-name $DB_SUBNET_GROUP_NAME \
    --db-subnet-group-description "Subnet group for The Plugs database" \
    --subnet-ids $SUBNET_IDS \
    --region $AWS_REGION || echo "DB subnet group may already exist"

# Create security group for RDS
echo -e "${YELLOW}Creating security group for RDS...${NC}"
# Get VPC ID if not provided
if [ "$VPC_ID" = "vpc-xxxxxxxxx" ]; then
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text --region $AWS_REGION)
    echo -e "${YELLOW}Using default VPC: $VPC_ID${NC}"
fi

# Create security group
SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --group-name $DB_SECURITY_GROUP_NAME \
    --description "Security group for The Plugs RDS database" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION \
    --query 'GroupId' --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=$DB_SECURITY_GROUP_NAME" \
    --query 'SecurityGroups[0].GroupId' --output text --region $AWS_REGION)

echo -e "${YELLOW}Security Group ID: $SECURITY_GROUP_ID${NC}"

# Add inbound rule for PostgreSQL (port 5432) from EC2 security group
echo -e "${YELLOW}Adding security group rules...${NC}"
# Get EC2 security group ID (assuming it's the default security group for now)
EC2_SECURITY_GROUP_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=default" "Name=vpc-id,Values=$VPC_ID" \
    --query 'SecurityGroups[0].GroupId' --output text --region $AWS_REGION)

aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 5432 \
    --source-group $EC2_SECURITY_GROUP_ID \
    --region $AWS_REGION 2>/dev/null || echo "Rule may already exist"

# Create RDS instance
echo -e "${YELLOW}Creating RDS PostgreSQL instance...${NC}"
aws rds create-db-instance \
    --db-instance-identifier $DB_INSTANCE_IDENTIFIER \
    --db-instance-class $DB_INSTANCE_CLASS \
    --engine $DB_ENGINE \
    --engine-version $DB_ENGINE_VERSION \
    --master-username $DB_USERNAME \
    --master-user-password $DB_PASSWORD \
    --allocated-storage $DB_ALLOCATED_STORAGE \
    --max-allocated-storage $DB_MAX_ALLOCATED_STORAGE \
    --storage-type gp2 \
    --storage-encrypted \
    --vpc-security-group-ids $SECURITY_GROUP_ID \
    --db-subnet-group-name $DB_SUBNET_GROUP_NAME \
    --backup-retention-period 7 \
    --preferred-backup-window "03:00-04:00" \
    --preferred-maintenance-window "sun:04:00-sun:05:00" \
    --multi-az \
    --publicly-accessible false \
    --auto-minor-version-upgrade \
    --deletion-protection \
    --region $AWS_REGION

echo -e "${YELLOW}Waiting for RDS instance to be available...${NC}"
aws rds wait db-instance-available \
    --db-instance-identifier $DB_INSTANCE_IDENTIFIER \
    --region $AWS_REGION

# Get RDS endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier $DB_INSTANCE_IDENTIFIER \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text --region $AWS_REGION)

echo -e "${GREEN}RDS PostgreSQL setup completed successfully!${NC}"
echo -e "${YELLOW}Database Details:${NC}"
echo "Instance Identifier: $DB_INSTANCE_IDENTIFIER"
echo "Endpoint: $RDS_ENDPOINT"
echo "Port: 5432"
echo "Database Name: $DB_NAME"
echo "Username: $DB_USERNAME"
echo "Password: $DB_PASSWORD"

echo -e "${YELLOW}Connection String:${NC}"
echo "postgresql://$DB_USERNAME:$DB_PASSWORD@$RDS_ENDPOINT:5432/$DB_NAME"

echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update your application's DATABASE_URL with the connection string above"
echo "2. Run database migrations on your EC2 instance"
echo "3. Test the database connection"

# Create database initialization script
echo -e "${YELLOW}Creating database initialization script...${NC}"
cat > /tmp/init-database.sql <<EOF
-- The Plugs Database Initialization Script
-- Run this script to set up the initial database structure

-- Create the main database (if not exists)
-- Note: RDS creates the database specified in the instance creation

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for better performance
-- These will be created by Alembic migrations, but can be added here for reference

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USERNAME;

-- Create a read-only user for reporting (optional)
-- CREATE USER plugs_readonly WITH PASSWORD 'readonly-password';
-- GRANT CONNECT ON DATABASE $DB_NAME TO plugs_readonly;
-- GRANT USAGE ON SCHEMA public TO plugs_readonly;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO plugs_readonly;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO plugs_readonly;
EOF

echo -e "${GREEN}Database initialization script created at /tmp/init-database.sql${NC}"
echo -e "${YELLOW}To initialize the database, run:${NC}"
echo "psql -h $RDS_ENDPOINT -U $DB_USERNAME -d $DB_NAME -f /tmp/init-database.sql"
