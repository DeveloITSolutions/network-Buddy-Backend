#!/bin/bash

# AWS S3 Setup Script for The Plugs Backend
# This script creates and configures S3 bucket for file storage

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration - Update these values
BUCKET_NAME="the-plugs-files-$(date +%s)"  # Add timestamp to make it unique
AWS_REGION="us-east-1"  # Change to your preferred region

echo -e "${GREEN}Starting S3 setup for The Plugs Backend...${NC}"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}AWS CLI is not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Get current region if not specified
if [ -z "$AWS_REGION" ]; then
    AWS_REGION=$(aws configure get region)
fi

echo -e "${YELLOW}Using AWS Region: $AWS_REGION${NC}"

# Create S3 bucket
echo -e "${YELLOW}Creating S3 bucket: $BUCKET_NAME${NC}"
if [ "$AWS_REGION" = "us-east-1" ]; then
    aws s3 mb s3://$BUCKET_NAME --region $AWS_REGION
else
    aws s3 mb s3://$BUCKET_NAME --region $AWS_REGION
fi

# Configure bucket for public read access to uploaded files
echo -e "${YELLOW}Configuring bucket policy...${NC}"
cat > /tmp/bucket-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file:///tmp/bucket-policy.json

# Configure CORS for web access
echo -e "${YELLOW}Configuring CORS...${NC}"
cat > /tmp/cors-config.json <<EOF
{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
            "AllowedOrigins": ["*"],
            "ExposeHeaders": ["ETag"],
            "MaxAgeSeconds": 3000
        }
    ]
}
EOF

aws s3api put-bucket-cors --bucket $BUCKET_NAME --cors-configuration file:///tmp/cors-config.json

# Enable versioning
echo -e "${YELLOW}Enabling versioning...${NC}"
aws s3api put-bucket-versioning --bucket $BUCKET_NAME --versioning-configuration Status=Enabled

# Configure lifecycle policy for cost optimization
echo -e "${YELLOW}Configuring lifecycle policy...${NC}"
cat > /tmp/lifecycle-config.json <<EOF
{
    "Rules": [
        {
            "ID": "DeleteIncompleteMultipartUploads",
            "Status": "Enabled",
            "Filter": {
                "Prefix": ""
            },
            "AbortIncompleteMultipartUpload": {
                "DaysAfterInitiation": 7
            }
        },
        {
            "ID": "TransitionToIA",
            "Status": "Enabled",
            "Filter": {
                "Prefix": ""
            },
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "STANDARD_IA"
                }
            ]
        },
        {
            "ID": "TransitionToGlacier",
            "Status": "Enabled",
            "Filter": {
                "Prefix": "archived/"
            },
            "Transitions": [
                {
                    "Days": 90,
                    "StorageClass": "GLACIER"
                }
            ]
        }
    ]
}
EOF

aws s3api put-bucket-lifecycle-configuration --bucket $BUCKET_NAME --lifecycle-configuration file:///tmp/lifecycle-config.json

# Create folder structure
echo -e "${YELLOW}Creating folder structure...${NC}"
aws s3api put-object --bucket $BUCKET_NAME --key "uploads/events/"
aws s3api put-object --bucket $BUCKET_NAME --key "uploads/profiles/"
aws s3api put-object --bucket $BUCKET_NAME --key "uploads/documents/"
aws s3api put-object --bucket $BUCKET_NAME --key "uploads/audio/"
aws s3api put-object --bucket $BUCKET_NAME --key "uploads/videos/"
aws s3api put-object --bucket $BUCKET_NAME --key "uploads/images/"
aws s3api put-object --bucket $BUCKET_NAME --key "archived/"

# Create IAM policy for the application
echo -e "${YELLOW}Creating IAM policy for application...${NC}"
cat > /tmp/s3-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::$BUCKET_NAME",
                "arn:aws:s3:::$BUCKET_NAME/*"
            ]
        }
    ]
}
EOF

aws iam create-policy \
    --policy-name ThePlugsS3Policy \
    --policy-document file:///tmp/s3-policy.json \
    --description "S3 access policy for The Plugs application" 2>/dev/null || echo "Policy may already exist"

# Create IAM user for the application (optional - can use EC2 instance role instead)
echo -e "${YELLOW}Creating IAM user for application...${NC}"
aws iam create-user --user-name the-plugs-app 2>/dev/null || echo "User may already exist"

# Attach policy to user
aws iam attach-user-policy \
    --user-name the-plugs-app \
    --policy-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/ThePlugsS3Policy 2>/dev/null || echo "Policy may already be attached"

# Create access keys for the user
echo -e "${YELLOW}Creating access keys...${NC}"
ACCESS_KEYS=$(aws iam create-access-key --user-name the-plugs-app --query 'AccessKey.{AccessKeyId:AccessKeyId,SecretAccessKey:SecretAccessKey}' --output text 2>/dev/null || echo "Keys may already exist")

if [ "$ACCESS_KEYS" != "Keys may already exist" ]; then
    echo -e "${GREEN}Access Keys Created:${NC}"
    echo "$ACCESS_KEYS"
else
    echo -e "${YELLOW}Access keys may already exist. Check AWS Console for existing keys.${NC}"
fi

# Clean up temporary files
rm -f /tmp/bucket-policy.json /tmp/cors-config.json /tmp/lifecycle-config.json /tmp/s3-policy.json

echo -e "${GREEN}S3 setup completed successfully!${NC}"
echo -e "${YELLOW}S3 Bucket Details:${NC}"
echo "Bucket Name: $BUCKET_NAME"
echo "Region: $AWS_REGION"
echo "URL: https://$BUCKET_NAME.s3.$AWS_REGION.amazonaws.com"

echo -e "${YELLOW}Environment Variables for your application:${NC}"
echo "AWS_REGION=$AWS_REGION"
echo "S3_BUCKET_NAME=$BUCKET_NAME"
echo "S3_BASE_URL=https://$BUCKET_NAME.s3.$AWS_REGION.amazonaws.com"

echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update your application's S3 configuration with the bucket name and region"
echo "2. Configure your file upload service to use this S3 bucket"
echo "3. Test file upload functionality"

# Create a test file to verify setup
echo -e "${YELLOW}Creating test file...${NC}"
echo "This is a test file created during S3 setup." > /tmp/test.txt
aws s3 cp /tmp/test.txt s3://$BUCKET_NAME/test.txt
echo -e "${GREEN}Test file uploaded successfully!${NC}"
echo "Test URL: https://$BUCKET_NAME.s3.$AWS_REGION.amazonaws.com/test.txt"
rm -f /tmp/test.txt







