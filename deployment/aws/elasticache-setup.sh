#!/bin/bash

# AWS ElastiCache Redis Setup Script for The Plugs Backend
# This script creates and configures ElastiCache Redis cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration - Update these values
CACHE_CLUSTER_ID="the-plugs-redis"
CACHE_NODE_TYPE="cache.t3.micro"  # Start small, can scale up
CACHE_ENGINE="redis"
CACHE_ENGINE_VERSION="7.0"
CACHE_NUM_CACHE_NODES=1
CACHE_PARAMETER_GROUP_NAME="the-plugs-redis-params"
CACHE_SUBNET_GROUP_NAME="the-plugs-cache-subnet-group"
CACHE_SECURITY_GROUP_NAME="the-plugs-cache-sg"
VPC_ID="vpc-xxxxxxxxx"  # Update with your VPC ID
SUBNET_IDS="subnet-xxxxxxxxx,subnet-yyyyyyyyy"  # Update with your subnet IDs

echo -e "${GREEN}Starting ElastiCache Redis setup for The Plugs Backend...${NC}"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}AWS CLI is not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Get current region
AWS_REGION=$(aws configure get region)
echo -e "${YELLOW}Using AWS Region: $AWS_REGION${NC}"

# Get VPC ID if not provided
if [ "$VPC_ID" = "vpc-xxxxxxxxx" ]; then
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text --region $AWS_REGION)
    echo -e "${YELLOW}Using default VPC: $VPC_ID${NC}"
fi

# Create cache subnet group
echo -e "${YELLOW}Creating cache subnet group...${NC}"
aws elasticache create-cache-subnet-group \
    --cache-subnet-group-name $CACHE_SUBNET_GROUP_NAME \
    --cache-subnet-group-description "Subnet group for The Plugs Redis cache" \
    --subnet-ids $SUBNET_IDS \
    --region $AWS_REGION 2>/dev/null || echo "Cache subnet group may already exist"

# Create parameter group for Redis
echo -e "${YELLOW}Creating Redis parameter group...${NC}"
aws elasticache create-cache-parameter-group \
    --cache-parameter-group-name $CACHE_PARAMETER_GROUP_NAME \
    --cache-parameter-group-family redis7.x \
    --description "Parameter group for The Plugs Redis cluster" \
    --region $AWS_REGION 2>/dev/null || echo "Parameter group may already exist"

# Configure Redis parameters
echo -e "${YELLOW}Configuring Redis parameters...${NC}"
aws elasticache modify-cache-parameter-group \
    --cache-parameter-group-name $CACHE_PARAMETER_GROUP_NAME \
    --parameter-name-values \
        ParameterName=maxmemory-policy,ParameterValue=allkeys-lru \
        ParameterName=timeout,ParameterValue=300 \
        ParameterName=tcp-keepalive,ParameterValue=60 \
    --region $AWS_REGION 2>/dev/null || echo "Parameters may already be set"

# Create security group for ElastiCache
echo -e "${YELLOW}Creating security group for ElastiCache...${NC}"
CACHE_SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --group-name $CACHE_SECURITY_GROUP_NAME \
    --description "Security group for The Plugs Redis cache" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION \
    --query 'GroupId' --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=$CACHE_SECURITY_GROUP_NAME" \
    --query 'SecurityGroups[0].GroupId' --output text --region $AWS_REGION)

echo -e "${YELLOW}Cache Security Group ID: $CACHE_SECURITY_GROUP_ID${NC}"

# Add inbound rule for Redis (port 6379) from EC2 security group
echo -e "${YELLOW}Adding security group rules...${NC}"
# Get EC2 security group ID (assuming it's the default security group for now)
EC2_SECURITY_GROUP_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=default" "Name=vpc-id,Values=$VPC_ID" \
    --query 'SecurityGroups[0].GroupId' --output text --region $AWS_REGION)

aws ec2 authorize-security-group-ingress \
    --group-id $CACHE_SECURITY_GROUP_ID \
    --protocol tcp \
    --port 6379 \
    --source-group $EC2_SECURITY_GROUP_ID \
    --region $AWS_REGION 2>/dev/null || echo "Rule may already exist"

# Create ElastiCache cluster
echo -e "${YELLOW}Creating ElastiCache Redis cluster...${NC}"
aws elasticache create-cache-cluster \
    --cache-cluster-id $CACHE_CLUSTER_ID \
    --cache-node-type $CACHE_NODE_TYPE \
    --engine $CACHE_ENGINE \
    --engine-version $CACHE_ENGINE_VERSION \
    --num-cache-nodes $CACHE_NUM_CACHE_NODES \
    --cache-parameter-group-name $CACHE_PARAMETER_GROUP_NAME \
    --cache-subnet-group-name $CACHE_SUBNET_GROUP_NAME \
    --security-group-ids $CACHE_SECURITY_GROUP_ID \
    --preferred-availability-zone $(aws ec2 describe-subnets --subnet-ids $(echo $SUBNET_IDS | cut -d',' -f1) --query 'Subnets[0].AvailabilityZone' --output text --region $AWS_REGION) \
    --region $AWS_REGION

echo -e "${YELLOW}Waiting for ElastiCache cluster to be available...${NC}"
aws elasticache wait cache-cluster-available \
    --cache-cluster-id $CACHE_CLUSTER_ID \
    --region $AWS_REGION

# Get ElastiCache endpoint
CACHE_ENDPOINT=$(aws elasticache describe-cache-clusters \
    --cache-cluster-id $CACHE_CLUSTER_ID \
    --show-cache-node-info \
    --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' \
    --output text --region $AWS_REGION)

CACHE_PORT=$(aws elasticache describe-cache-clusters \
    --cache-cluster-id $CACHE_CLUSTER_ID \
    --show-cache-node-info \
    --query 'CacheClusters[0].CacheNodes[0].Endpoint.Port' \
    --output text --region $AWS_REGION)

echo -e "${GREEN}ElastiCache Redis setup completed successfully!${NC}"
echo -e "${YELLOW}Redis Details:${NC}"
echo "Cluster ID: $CACHE_CLUSTER_ID"
echo "Endpoint: $CACHE_ENDPOINT"
echo "Port: $CACHE_PORT"
echo "Node Type: $CACHE_NODE_TYPE"
echo "Engine: $CACHE_ENGINE $CACHE_ENGINE_VERSION"

echo -e "${YELLOW}Connection URLs:${NC}"
echo "Redis URL: redis://$CACHE_ENDPOINT:$CACHE_PORT/0"
echo "Celery Broker URL: redis://$CACHE_ENDPOINT:$CACHE_PORT/1"
echo "Celery Result Backend: redis://$CACHE_ENDPOINT:$CACHE_PORT/2"

echo -e "${YELLOW}Environment Variables for your application:${NC}"
echo "REDIS_URL=redis://$CACHE_ENDPOINT:$CACHE_PORT/0"
echo "CELERY_BROKER_URL=redis://$CACHE_ENDPOINT:$CACHE_PORT/1"
echo "CELERY_RESULT_BACKEND=redis://$CACHE_ENDPOINT:$CACHE_PORT/2"

echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update your application's Redis configuration with the connection URLs above"
echo "2. Test the Redis connection from your EC2 instance"
echo "3. Configure your Celery workers to use the Redis broker"

# Test Redis connection (if redis-cli is available)
if command -v redis-cli &> /dev/null; then
    echo -e "${YELLOW}Testing Redis connection...${NC}"
    redis-cli -h $CACHE_ENDPOINT -p $CACHE_PORT ping || echo "Redis connection test failed (redis-cli may not be installed on this machine)"
else
    echo -e "${YELLOW}To test Redis connection, install redis-cli and run:${NC}"
    echo "redis-cli -h $CACHE_ENDPOINT -p $CACHE_PORT ping"
fi

# Create Redis configuration file for the application
echo -e "${YELLOW}Creating Redis configuration file...${NC}"
cat > /tmp/redis-config.conf <<EOF
# Redis Configuration for The Plugs Backend
# ElastiCache Redis cluster configuration

# Connection settings
REDIS_HOST=$CACHE_ENDPOINT
REDIS_PORT=$CACHE_PORT
REDIS_DB=0
REDIS_PASSWORD=

# Connection pool settings
REDIS_MAX_CONNECTIONS=20
REDIS_RETRY_ON_TIMEOUT=true
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5

# Celery settings
CELERY_BROKER_URL=redis://$CACHE_ENDPOINT:$CACHE_PORT/1
CELERY_RESULT_BACKEND=redis://$CACHE_ENDPOINT:$CACHE_PORT/2

# Cache settings
CACHE_TTL=3600  # 1 hour default TTL
CACHE_PREFIX=the_plugs:
EOF

echo -e "${GREEN}Redis configuration file created at /tmp/redis-config.conf${NC}"
echo -e "${YELLOW}Copy this configuration to your application server.${NC}"
