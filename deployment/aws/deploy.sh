#!/bin/bash

# Production Deployment Script for The Plugs Backend
# This script handles the complete deployment process

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="the-plugs-backend"
APP_DIR="/opt/the-plugs"
APP_USER="plugs"
BACKUP_DIR="/opt/backups"
LOG_FILE="/var/log/the-plugs/deploy.log"

# Function to log messages
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a $LOG_FILE
}

# Function to log errors
log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a $LOG_FILE
}

# Function to log success
log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1" | tee -a $LOG_FILE
}

# Function to log warnings
log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a $LOG_FILE
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_error "This script should not be run as root. Please run as the $APP_USER user."
    exit 1
fi

# Check if user is correct
if [ "$(whoami)" != "$APP_USER" ]; then
    log_error "This script must be run as the $APP_USER user."
    exit 1
fi

log "Starting deployment of $APP_NAME..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup current deployment
log "Creating backup of current deployment..."
if [ -d "$APP_DIR" ]; then
    BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S)"
    tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" -C "$APP_DIR" . 2>/dev/null || log_warning "Could not create backup"
    log_success "Backup created: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
fi

# Navigate to application directory
cd $APP_DIR

# Pull latest code
log "Pulling latest code from repository..."
git fetch origin
git reset --hard origin/main
log_success "Code updated successfully"

# Install/update dependencies
log "Installing/updating Python dependencies..."
if [ -f "requirements.txt" ]; then
    $APP_DIR/venv/bin/pip install --upgrade pip
    $APP_DIR/venv/bin/pip install -r requirements.txt
    log_success "Dependencies updated successfully"
else
    log_error "requirements.txt not found"
    exit 1
fi

# Run database migrations
log "Running database migrations..."
if [ -f "alembic.ini" ]; then
    $APP_DIR/venv/bin/alembic upgrade head
    log_success "Database migrations completed"
else
    log_warning "No Alembic configuration found, skipping migrations"
fi

# Run tests (optional)
if [ "$1" = "--with-tests" ]; then
    log "Running tests..."
    if [ -f "pytest.ini" ]; then
        $APP_DIR/venv/bin/pytest tests/ -v || log_warning "Some tests failed"
    else
        log_warning "No test configuration found, skipping tests"
    fi
fi

# Collect static files (if any)
log "Collecting static files..."
# Add any static file collection commands here if needed

# Restart services
log "Restarting services..."

# Stop services gracefully
log "Stopping services..."
sudo systemctl stop the-plugs-celery || log_warning "Could not stop Celery service"
sudo systemctl stop the-plugs || log_warning "Could not stop API service"

# Wait a moment for graceful shutdown
sleep 5

# Start services
log "Starting services..."
sudo systemctl start the-plugs
sudo systemctl start the-plugs-celery

# Wait for services to start
sleep 10

# Check service status
log "Checking service status..."
if systemctl is-active --quiet the-plugs; then
    log_success "API service is running"
else
    log_error "API service failed to start"
    sudo systemctl status the-plugs
    exit 1
fi

if systemctl is-active --quiet the-plugs-celery; then
    log_success "Celery service is running"
else
    log_error "Celery service failed to start"
    sudo systemctl status the-plugs-celery
    exit 1
fi

# Test API health
log "Testing API health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    log_success "API health check passed"
else
    log_error "API health check failed"
    exit 1
fi

# Reload nginx
log "Reloading Nginx..."
sudo systemctl reload nginx
log_success "Nginx reloaded successfully"

# Clean up old backups (keep last 5)
log "Cleaning up old backups..."
cd $BACKUP_DIR
ls -t backup-*.tar.gz | tail -n +6 | xargs -r rm
log_success "Old backups cleaned up"

# Log deployment completion
log_success "Deployment completed successfully!"
log "Application is now running at: http://$(curl -s ifconfig.me)/api/v1/"

# Show service status
log "Current service status:"
sudo systemctl status the-plugs --no-pager -l
sudo systemctl status the-plugs-celery --no-pager -l

# Show recent logs
log "Recent application logs:"
tail -n 20 /var/log/the-plugs/app.log 2>/dev/null || log_warning "No application logs found"

log "Deployment script completed successfully!"
