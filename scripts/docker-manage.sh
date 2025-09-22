#!/bin/bash

# Docker Management Script for The Plugs

set -e

COMMAND=${1:-"help"}
SERVICE=${2:-""}

echo "🐳 The Plugs - Docker Management"
echo "================================"

# Function to show help
show_help() {
    echo "Docker management commands:"
    echo ""
    echo "Service Management:"
    echo "  start [env]              Start all services (dev/prod)"
    echo "  stop                     Stop all services"
    echo "  restart [service]        Restart service(s)"
    echo "  status                   Show service status"
    echo "  ps                       Show running containers"
    echo ""
    echo "Logs & Monitoring:"
    echo "  logs [service]           Show logs for service"
    echo "  logs-follow [service]    Follow logs for service"
    echo "  stats                    Show container resource usage"
    echo ""
    echo "Database Management:"
    echo "  db-shell                 Connect to PostgreSQL shell"
    echo "  db-migrate              Run database migrations"
    echo "  db-backup               Backup database"
    echo "  db-restore [file]       Restore database from backup"
    echo ""
    echo "Cache Management:"
    echo "  redis-shell             Connect to Redis CLI"
    echo "  redis-flush             Flush Redis cache"
    echo ""
    echo "Maintenance:"
    echo "  build                   Rebuild all containers"
    echo "  clean                   Clean up unused containers and images"
    echo "  prune                   Prune Docker system"
    echo "  health                  Check health of all services"
    echo ""
    echo "Development:"
    echo "  shell [service]         Open shell in service container"
    echo "  exec [service] [cmd]    Execute command in service container"
    echo ""
    echo "Examples:"
    echo "  $0 start dev            # Start development environment"
    echo "  $0 logs api             # Show API logs"
    echo "  $0 shell api            # Open shell in API container"
    echo "  $0 db-migrate           # Run database migrations"
}

# Check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ docker-compose not found"
        exit 1
    fi
}

# Get the appropriate compose file
get_compose_file() {
    local env=${1:-"dev"}
    if [[ "$env" == "prod" || "$env" == "production" ]]; then
        echo "-f docker-compose.prod.yml"
    else
        echo ""
    fi
}

# Service management
start_services() {
    local env=${1:-"dev"}
    local compose_file=$(get_compose_file $env)
    echo "🚀 Starting services ($env environment)..."
    
    if [ -f ".env.docker" ]; then
        docker-compose --env-file .env.docker $compose_file up -d
    else
        docker-compose $compose_file up -d
    fi
    
    echo "✅ Services started"
    show_status
}

stop_services() {
    echo "🛑 Stopping all services..."
    docker-compose down
    echo "✅ Services stopped"
}

restart_services() {
    local service=$1
    if [ -n "$service" ]; then
        echo "🔄 Restarting service: $service"
        docker-compose restart $service
    else
        echo "🔄 Restarting all services..."
        docker-compose restart
    fi
    echo "✅ Services restarted"
}

show_status() {
    echo "📊 Service Status:"
    docker-compose ps
}

show_stats() {
    echo "📈 Container Resource Usage:"
    docker stats --no-stream
}

# Logs management
show_logs() {
    local service=$1
    if [ -n "$service" ]; then
        docker-compose logs $service
    else
        docker-compose logs
    fi
}

follow_logs() {
    local service=$1
    if [ -n "$service" ]; then
        docker-compose logs -f $service
    else
        docker-compose logs -f
    fi
}

# Database management
db_shell() {
    echo "🗃️  Connecting to PostgreSQL shell..."
    docker-compose exec postgres psql -U the_plugs_user -d the_plugs
}

db_migrate() {
    echo "🗄️  Running database migrations..."
    docker-compose exec api alembic upgrade head
    echo "✅ Migrations completed"
}

db_backup() {
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    echo "💾 Creating database backup: $backup_file"
    docker-compose exec postgres pg_dump -U the_plugs_user -d the_plugs > $backup_file
    echo "✅ Backup created: $backup_file"
}

db_restore() {
    local backup_file=$1
    if [ -z "$backup_file" ]; then
        echo "❌ Please provide backup file: $0 db-restore <backup-file>"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        echo "❌ Backup file not found: $backup_file"
        exit 1
    fi
    
    echo "🔄 Restoring database from: $backup_file"
    cat $backup_file | docker-compose exec -T postgres psql -U the_plugs_user -d the_plugs
    echo "✅ Database restored"
}

# Redis management
redis_shell() {
    echo "🔧 Connecting to Redis CLI..."
    docker-compose exec redis redis-cli
}

redis_flush() {
    echo "🧹 Flushing Redis cache..."
    docker-compose exec redis redis-cli FLUSHALL
    echo "✅ Redis cache cleared"
}

# Development helpers
open_shell() {
    local service=${1:-"api"}
    echo "💻 Opening shell in $service container..."
    docker-compose exec $service /bin/bash
}

exec_command() {
    local service=${1:-"api"}
    shift
    local command="$@"
    
    if [ -z "$command" ]; then
        echo "❌ Please provide command: $0 exec <service> <command>"
        exit 1
    fi
    
    echo "⚡ Executing '$command' in $service container..."
    docker-compose exec $service $command
}

# Maintenance
build_containers() {
    echo "🔨 Building containers..."
    docker-compose build --no-cache
    echo "✅ Containers built"
}

clean_docker() {
    echo "🧹 Cleaning up Docker..."
    
    # Remove stopped containers
    echo "Removing stopped containers..."
    docker container prune -f
    
    # Remove unused images
    echo "Removing unused images..."
    docker image prune -f
    
    # Remove unused volumes
    echo "Removing unused volumes..."
    docker volume prune -f
    
    echo "✅ Docker cleanup completed"
}

prune_docker() {
    echo "🗑️  Pruning Docker system..."
    docker system prune -af
    echo "✅ Docker system pruned"
}

health_check() {
    echo "🩺 Checking service health..."
    
    # Check if containers are running
    echo "Container Status:"
    docker-compose ps
    
    echo ""
    echo "Health Checks:"
    
    # Check API health
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ API is healthy"
    else
        echo "❌ API is not responding"
    fi
    
    # Check Redis
    if docker-compose exec redis redis-cli ping | grep -q PONG; then
        echo "✅ Redis is healthy"
    else
        echo "❌ Redis is not responding"
    fi
    
    # Check PostgreSQL
    if docker-compose exec postgres pg_isready -U the_plugs_user -d the_plugs | grep -q "accepting connections"; then
        echo "✅ PostgreSQL is healthy"
    else
        echo "❌ PostgreSQL is not responding"
    fi
}

# Main command dispatcher
main() {
    check_docker_compose
    
    case $COMMAND in
        "start")
            start_services $SERVICE
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services $SERVICE
            ;;
        "status"|"ps")
            show_status
            ;;
        "stats")
            show_stats
            ;;
        "logs")
            show_logs $SERVICE
            ;;
        "logs-follow"|"logs-f")
            follow_logs $SERVICE
            ;;
        "db-shell")
            db_shell
            ;;
        "db-migrate")
            db_migrate
            ;;
        "db-backup")
            db_backup
            ;;
        "db-restore")
            db_restore $SERVICE
            ;;
        "redis-shell")
            redis_shell
            ;;
        "redis-flush")
            redis_flush
            ;;
        "shell")
            open_shell $SERVICE
            ;;
        "exec")
            exec_command $SERVICE $@
            ;;
        "build")
            build_containers
            ;;
        "clean")
            clean_docker
            ;;
        "prune")
            prune_docker
            ;;
        "health")
            health_check
            ;;
        "help"|"-h"|"--help"|*)
            show_help
            ;;
    esac
}

main $@


