#!/bin/bash

# CORS Configuration Script for The Plugs Backend Deployment
# This script sets up environment variables to fix CORS issues

echo "Setting up CORS configuration for deployment..."

# Export CORS environment variables to allow all origins
export CORS_ORIGINS="*"
export CORS_CREDENTIALS="true"
export CORS_METHODS="*"
export CORS_HEADERS="*"

# Set environment to production
export ENVIRONMENT="production"
export DEBUG="false"

echo "CORS configuration set:"
echo "CORS_ORIGINS: $CORS_ORIGINS"
echo "CORS_CREDENTIALS: $CORS_CREDENTIALS"
echo "CORS_METHODS: $CORS_METHODS"
echo "CORS_HEADERS: $CORS_HEADERS"
echo "ENVIRONMENT: $ENVIRONMENT"
echo "DEBUG: $DEBUG"

echo "CORS configuration completed!"
echo ""
echo "To use these settings:"
echo "1. Source this script: source deployment/cors-config.sh"
echo "2. Then start your application: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "Or add these environment variables to your deployment environment."
