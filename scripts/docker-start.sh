#!/bin/bash

# Docker Start Script for The Plugs

set -e

echo "🐳 The Plugs - Docker Setup and Start"
echo "======================================"

# Parse command line arguments
ENVIRONMENT=${1:-"development"}
DETACHED=${2:-"false"}

# Function to check if Docker is running
check_docker() {
    if ! docker --version &> /dev/null; then
        echo "❌ Docker is not installed or not running"
        echo "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker-compose --version &> /dev/null; then
        echo "❌ Docker Compose is not installed"
        echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    echo "✅ Docker and Docker Compose are available"
}

# Function to create .env file for Docker
create_docker_env() {
    if [ ! -f ".env.docker" ]; then
        echo "📝 Creating .env.docker file..."
        cat > .env.docker << EOF
# PostgreSQL Configuration
POSTGRES_DB=the_plugs
POSTGRES_USER=the_plugs_user
POSTGRES_PASSWORD=secure_password_change_me

# Security
SECRET_KEY=super-secret-key-for-development-change-in-production

# CORS Origins (adjust for your frontend)
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:3001

# Email Configuration (optional for development)
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true

# File Upload
MAX_FILE_SIZE=10485760

# Logging
LOG_LEVEL=INFO
EOF
        echo "✅ Created .env.docker file"
        echo "⚠️  Please edit .env.docker with your production values for production deployment"
    fi
}

# Function to start development environment
start_development() {
    echo "🚀 Starting development environment..."
    
    # Create Docker environment file
    create_docker_env
    
    # Build and start services
    if [ "$DETACHED" = "true" ]; then
        docker-compose --env-file .env.docker up -d --build
    else
        docker-compose --env-file .env.docker up --build
    fi
}

# Function to start production environment
start_production() {
    echo "🚀 Starting production environment..."
    
    # Check if production environment file exists
    if [ ! -f ".env.docker" ]; then
        echo "❌ .env.docker file not found"
        echo "Please create .env.docker with production values"
        echo "You can start with: cp .env.docker.example .env.docker"
        exit 1
    fi
    
    # Build and start production services
    if [ "$DETACHED" = "true" ]; then
        docker-compose --env-file .env.docker -f docker-compose.prod.yml up -d --build
    else
        docker-compose --env-file .env.docker -f docker-compose.prod.yml up --build
    fi
}

# Function to show service URLs
show_urls() {
    echo ""
    echo "🎯 Service URLs:"
    echo "────────────────"
    echo "🌐 API Documentation: http://localhost:8000/docs"
    echo "🩺 Health Check: http://localhost:8000/health"
    echo "📊 Celery Flower: http://localhost:5555"
    echo "🗃️  pgAdmin: http://localhost:5050"
    echo "   └── Email: admin@theplugs.com, Password: admin123"
    echo "🔧 Redis Commander: http://localhost:8081"
    echo ""
    echo "📝 Database Connection:"
    echo "   Host: localhost, Port: 5432"
    echo "   Database: the_plugs"
    echo "   Username: the_plugs_user"
    echo "   Password: (check .env.docker file)"
    echo ""
}

# Function to show help
show_help() {
    echo "Usage: $0 [environment] [detached]"
    echo ""
    echo "Arguments:"
    echo "  environment    development|production (default: development)"
    echo "  detached       true|false (default: false)"
    echo ""
    echo "Examples:"
    echo "  $0                          # Start development environment in foreground"
    echo "  $0 development true         # Start development environment in background"
    echo "  $0 production               # Start production environment in foreground"
    echo "  $0 production true          # Start production environment in background"
    echo ""
    echo "Management commands:"
    echo "  docker-compose down         # Stop all services"
    echo "  docker-compose logs -f api  # View API logs"
    echo "  docker-compose ps           # Show running services"
    echo ""
}

# Main execution
main() {
    case $ENVIRONMENT in
        "development"|"dev")
            check_docker
            start_development
            if [ "$DETACHED" = "true" ]; then
                show_urls
            fi
            ;;
        "production"|"prod")
            check_docker
            start_production
            if [ "$DETACHED" = "true" ]; then
                show_urls
            fi
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo "❌ Unknown environment: $ENVIRONMENT"
            show_help
            exit 1
            ;;
    esac
}

# Trap Ctrl+C and cleanup
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    docker-compose down
    exit 0
}

trap cleanup SIGINT SIGTERM

# Run main function
main
