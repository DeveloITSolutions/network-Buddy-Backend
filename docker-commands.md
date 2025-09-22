# 🐳 Docker Commands Reference

## Quick Start Commands

```bash
# 🚀 Start everything (recommended)
./scripts/docker-start.sh

# 🚀 Start in background
./scripts/docker-start.sh development true

# 🛑 Stop everything
./scripts/docker-manage.sh stop

# 📊 Check status
./scripts/docker-manage.sh status
```

## Service Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart specific service
docker-compose restart api

# View running containers
docker-compose ps

# View logs
docker-compose logs -f api
```

## Database Commands

```bash
# Connect to PostgreSQL
./scripts/docker-manage.sh db-shell
# OR
docker-compose exec postgres psql -U the_plugs_user -d the_plugs

# Run migrations
./scripts/docker-manage.sh db-migrate
# OR
docker-compose exec api alembic upgrade head

# Backup database
./scripts/docker-manage.sh db-backup

# Create new migration
docker-compose exec api alembic revision --autogenerate -m "your message"
```

## Development Commands

```bash
# Open shell in API container
./scripts/docker-manage.sh shell api
# OR
docker-compose exec api /bin/bash

# Run tests
docker-compose exec api pytest

# Run tests with coverage
docker-compose exec api pytest --cov=app

# Install new package
docker-compose exec api pip install package-name
# Then add to requirements.txt and rebuild:
docker-compose build api
```

## Debugging Commands

```bash
# View all logs
docker-compose logs

# Follow logs for specific service
docker-compose logs -f api

# Check container resources
docker stats

# View health status
curl http://localhost:8000/health

# Check Celery tasks
# Visit http://localhost:5555
```

## Production Commands

```bash
# Start production environment
./scripts/docker-start.sh production

# OR manually:
docker-compose -f docker-compose.prod.yml up -d

# View production logs
docker-compose -f docker-compose.prod.yml logs

# Scale API instances
docker-compose -f docker-compose.prod.yml up -d --scale api=3
```

## Maintenance Commands

```bash
# Rebuild all containers
./scripts/docker-manage.sh build
# OR
docker-compose build --no-cache

# Clean up Docker
./scripts/docker-manage.sh clean

# Prune Docker system
./scripts/docker-manage.sh prune

# Update dependencies
docker-compose build --no-cache
```

## Access URLs

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Celery Flower**: http://localhost:5555
- **pgAdmin**: http://localhost:5050 (admin@theplugs.com / admin123)
- **Redis Commander**: http://localhost:8081

## Environment Files

```bash
# Development (auto-created)
.env.docker

# Example file
.env.docker.example

# Copy example for customization
cp .env.docker.example .env.docker
```

## Useful One-Liners

```bash
# Check API health
curl -s http://localhost:8000/health | jq

# Watch logs from all services
docker-compose logs -f

# Reset everything (⚠️ destroys data)
docker-compose down -v && ./scripts/docker-start.sh

# Get into PostgreSQL quickly
docker-compose exec postgres psql -U the_plugs_user -d the_plugs

# Run a specific test
docker-compose exec api pytest tests/unit/test_specific.py -v

# Check Redis keys
docker-compose exec redis redis-cli KEYS "*"

# Monitor containers
watch docker-compose ps
```


