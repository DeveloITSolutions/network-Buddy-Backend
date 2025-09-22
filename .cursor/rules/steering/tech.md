# Technology Stack - The Plugs Enterprise Platform

## Core Framework & Language
- **FastAPI**: Modern, high-performance Python web framework for building enterprise APIs
- **Python 3.x**: Primary programming language with enterprise-grade libraries
- **Pydantic**: Advanced data validation, serialization, and type safety
- **SQLAlchemy**: Enterprise ORM with advanced relationship mapping and query optimization
- **Alembic**: Database schema migration management with version control

## Enterprise Infrastructure & Deployment
- **Docker**: Multi-stage containerization for production deployments
- **Kubernetes**: Enterprise container orchestration (see `deployment/kubernetes/`)
- **Helm**: Kubernetes package management with environment-specific configurations
- **Terraform**: Infrastructure as Code for cloud resource provisioning
- **Nginx**: High-performance reverse proxy, load balancing, and SSL termination

## Background Processing & Messaging
- **Celery**: Distributed task queue for async processing (email, analytics, AI tasks)
- **Redis**: High-performance message broker, caching, and session storage
- **Background Workers**: Specialized workers for email, media processing, analytics, and AI operations

## Database & Storage Architecture
- **PostgreSQL**: Primary ACID-compliant database with advanced indexing
- **Redis**: In-memory data structure store for caching and real-time features
- **Multi-tenant Data Isolation**: Organization-level data segregation and security

## Enterprise Integrations
- **HubSpot API**: CRM synchronization and lead management
- **CSV Export/Import**: Bulk data operations for enterprise workflows
- **RESTful APIs**: Comprehensive API design for third-party integrations

## Monitoring & Enterprise Observability
- **Custom Monitoring Stack**: Health checks, performance metrics, alerting, and distributed tracing
- **Structured Logging**: Centralized logging with correlation IDs for enterprise debugging
- **Analytics Pipeline**: Real-time data processing for business intelligence

## Development & Quality Assurance
- **pytest**: Comprehensive testing framework with fixtures, integration, and e2e tests
- **mypy**: Static type checking for enterprise code quality
- **flake8**: Code linting and style enforcement
- **pre-commit**: Git hooks for automated code quality checks
- **Coverage**: Code coverage reporting and quality gates

## Security & Compliance
- **Enterprise Authentication**: JWT-based auth with role-based access control (RBAC)
- **Data Encryption**: At-rest and in-transit encryption
- **Audit Logging**: Comprehensive audit trails for compliance
- **Security Scanning**: Automated vulnerability scanning in CI/CD

## Common Commands

### Development Setup
```bash
# Complete project setup
./setup.sh

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Start development server
./scripts/start.sh
# OR
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Operations
```bash
# Run database migrations
./scripts/migrate.sh
# OR
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback migration
alembic downgrade -1
```

### Testing & Quality
```bash
# Run all tests
./scripts/test.sh
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=app --cov-report=html

# Type checking
mypy app/

# Code linting
flake8 app/
```

### Docker Operations
```bash
# Development environment
docker-compose up -d
docker-compose logs -f

# Production environment
docker-compose -f docker-compose.prod.yml up -d

# Build and push images
docker build -t the-plugs:latest .
```

### Deployment
```bash
# Production deployment
./scripts/deploy.sh

# Kubernetes deployment
kubectl apply -f deployment/kubernetes/

# Helm deployment
helm upgrade --install the-plugs deployment/helm/ -f deployment/helm/values-production.yaml
```

### Background Workers
```bash
# Start Celery workers
celery -A app.workers.celery_app worker --loglevel=info

# Start specific worker types
celery -A app.workers.celery_app worker --loglevel=info --queues=email
celery -A app.workers.celery_app worker --loglevel=info --queues=analytics

# Monitor Celery
celery -A app.workers.celery_app flower
```