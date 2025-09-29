#!/bin/bash

# Quick Deployment Script with CORS Fix for The Plugs Backend
# This script ensures CORS is properly configured for deployment

echo "🚀 Deploying The Plugs Backend with CORS Fix..."

# Set CORS environment variables to allow all origins
export CORS_ORIGINS="*"
export CORS_CREDENTIALS="true"
export CORS_METHODS="*"
export CORS_HEADERS="*"
export ENVIRONMENT="production"
export DEBUG="false"

echo "✅ CORS Configuration:"
echo "   CORS_ORIGINS: $CORS_ORIGINS"
echo "   CORS_CREDENTIALS: $CORS_CREDENTIALS"
echo "   CORS_METHODS: $CORS_METHODS"
echo "   CORS_HEADERS: $CORS_HEADERS"
echo "   ENVIRONMENT: $ENVIRONMENT"
echo ""

# Check if running with Docker Compose
if [ -f "docker-compose.yml" ]; then
    echo "🐳 Starting with Docker Compose..."
    docker-compose up -d
elif [ -f "docker-compose.prod.yml" ]; then
    echo "🐳 Starting with Production Docker Compose..."
    docker-compose -f docker-compose.prod.yml up -d
else
    echo "🐍 Starting with Python directly..."
    echo "Make sure you have the following environment variables set:"
    echo "   DATABASE_URL, SECRET_KEY, REDIS_URL"
    echo ""
    echo "Starting application..."
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
fi

echo ""
echo "🎉 Deployment completed!"
echo "Your backend should now accept requests from any frontend URL."
echo ""
echo "Test your API at: http://localhost:8000/health"
echo "API Documentation: http://localhost:8000/docs"

