# 🐳 Docker Quick Start Guide

Get The Plugs API running with Docker in under 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- Git (to clone the repository)

## 🚀 One-Command Setup

```bash
# Clone and start the project
git clone <your-repo-url>
cd the_plugs_backend
./scripts/docker-start.sh
```

That's it! The API will be running at http://localhost:8000

## 📋 What Gets Started

| Service | URL | Description |
|---------|-----|-------------|
| **API** | http://localhost:8000 | Main FastAPI application |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Health Check** | http://localhost:8000/health | Service health status |
| **Celery Flower** | http://localhost:5555 | Task queue monitoring |
| **pgAdmin** | http://localhost:5050 | Database administration |
| **Redis Commander** | http://localhost:8081 | Redis management |

### Database Access
- **Host**: localhost
- **Port**: 5432
- **Database**: the_plugs
- **Username**: the_plugs_user
- **Password**: secure_password_change_me

### pgAdmin Login
- **Email**: admin@theplugs.com
- **Password**: admin123

## 🛠️ Quick Commands

```bash
# View service status
./scripts/docker-manage.sh status

# View API logs
./scripts/docker-manage.sh logs api

# Open API container shell
./scripts/docker-manage.sh shell api

# Run database migrations
./scripts/docker-manage.sh db-migrate

# Stop all services
./scripts/docker-manage.sh stop

# Restart services
./scripts/docker-manage.sh restart
```

## 🔧 Configuration

1. **Create custom environment file:**
   ```bash
   cp .env.docker.example .env.docker
   vim .env.docker  # Edit as needed
   ```

2. **Restart with new configuration:**
   ```bash
   ./scripts/docker-start.sh
   ```

## 🧪 Testing

```bash
# Run tests in Docker
./scripts/docker-manage.sh exec api python -m pytest

# Run with coverage
./scripts/docker-manage.sh exec api python -m pytest --cov=app
```

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
lsof -i :8000

# Kill the process or change ports in docker-compose.yml
```

### Database Connection Issues
```bash
# Check database status
./scripts/docker-manage.sh logs postgres

# Reset database
docker-compose down -v
./scripts/docker-start.sh
```

### Container Won't Start
```bash
# View detailed logs
./scripts/docker-manage.sh logs

# Rebuild containers
./scripts/docker-manage.sh build
```

### Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
```

## 🏭 Production Deployment

```bash
# Create production environment file
cp .env.docker.example .env.docker
# Edit with production values

# Start production environment
./scripts/docker-start.sh production
```

## 📞 Need Help?

- Check the main [README.md](README.md) for detailed documentation
- View API documentation at http://localhost:8000/docs
- Check health status at http://localhost:8000/health

## 🎉 Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Run tests**: `./scripts/docker-manage.sh exec api pytest`
3. **Add your features**: Start coding in the `app/` directory
4. **Monitor tasks**: Check Celery Flower at http://localhost:5555

Happy coding! 🚀
