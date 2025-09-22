#!/bin/bash

# Simple startup script for The Plugs Backend
echo "🚀 Starting The Plugs Backend (Simple Mode)..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'EOF'
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=postgresql://postgres.bubjtvdyuiehgyqhlioo:postgres@aws-1-us-east-2.pooler.supabase.com:6543/postgres
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key-change-in-production
SENDGRID_API_KEY=
SENDGRID_FROM_EMAIL=noreply@theplugs.com
FRONTEND_URL=http://localhost:3000
EOF
    echo "✅ .env file created with default values"
fi

# Start Redis
echo "🔴 Starting Redis..."
docker compose up -d redis

# Wait for Redis
echo "⏳ Waiting for Redis to be ready..."
sleep 5

# Check if Redis is ready
if ! docker exec the_plugs_redis redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not ready. Please check the logs."
    exit 1
fi

echo "✅ Redis is ready!"

# Build and start API
echo "🔨 Building and starting API..."
docker compose up --build -d api

# Wait for API
echo "⏳ Waiting for API to be ready..."
sleep 10

# Check if API is ready
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is ready!"
else
    echo "⚠️  API might still be starting up..."
fi

echo ""
echo "🎉 The Plugs Backend is running!"
echo ""
echo "📡 API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🔴 Redis Commander: http://localhost:8081"
echo ""
echo "📊 Service Status:"
docker compose ps
echo ""
echo "📝 To view logs: docker compose logs -f api"
echo "🛑 To stop: docker compose down"
echo ""

# Show API logs
echo "📋 Showing API logs (Press Ctrl+C to exit):"
docker compose logs -f api
