# Inventory Service - Docker Development Setup

This guide provides step-by-step instructions for setting up the Inventory Service in a Docker-based development environment. This approach uses MySQL and Redis running in Docker containers.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Environment Configuration](#environment-configuration)
- [Database Management](#database-management)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Cleanup](#cleanup)

## 🔧 Prerequisites

Before starting, ensure you have the following installed:

- **Python** (v3.8+ recommended)
- **pip** (comes with Python)
- **Docker** (v20+ recommended)
- **Docker Compose** (usually included with Docker Desktop)
- **Git** (for version control)

### Verify Prerequisites

```bash
# Check versions
python --version      # Should be v3.8+
pip --version         # Should be recent
docker --version      # Should be 20+
docker-compose --version
git --version
```

## 🚀 Quick Start

For experienced developers who want to get started immediately:

```bash
# 1. Start infrastructure services (includes Redis)
cd ../infrastructure
docker-compose up -d

# 2. Start MySQL container
docker run -d --name mysql-inventory \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=root_pass_123 \
  -e MYSQL_DATABASE=inventory_service_db \
  -e MYSQL_USER=appuser \
  -e MYSQL_PASSWORD=apppass123 \
  -v mysql-inventory-data:/var/lib/mysql \
  --network aioutlet-dev-network \
  mysql:8.0

# 3. Setup Python environment and install dependencies
cd inventory-service
python -m venv venv
source venv/bin/activate  # Unix/MacOS | Windows: venv\Scripts\activate
pip install -r requirements.txt

# 4. Copy and configure environment
cp .env.example .env

# 5. Initialize database and start service
python -c "from app import create_app, db; app = create_app('development'); app.app_context().push(); db.create_all(); print('Database initialized!')"
python run.py
```

## 📖 Detailed Setup

### Step 1: Infrastructure Services Setup

Start the shared infrastructure services (Redis + RabbitMQ):

```bash
# Navigate to infrastructure directory
cd ../infrastructure

# Start all infrastructure services
docker-compose up -d

# Verify services are running
docker-compose ps
```

### Step 2: MySQL Container Setup

Create and start a MySQL container:

```bash
# Create and start MySQL container
docker run -d \
  --name mysql-inventory \
  --restart unless-stopped \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=root_pass_123 \
  -e MYSQL_DATABASE=inventory_service_db \
  -e MYSQL_USER=appuser \
  -e MYSQL_PASSWORD=apppass123 \
  -v mysql-inventory-data:/var/lib/mysql \
  --network aioutlet-dev-network \
  mysql:8.0

# Wait for MySQL to start
sleep 30

# Verify container is running
docker ps | grep mysql-inventory
```

### Step 3: Database Setup

Create additional database for testing:

```bash
# Connect to MySQL and create test database
docker exec -it mysql-inventory mysql -u root -p -e "
CREATE DATABASE IF NOT EXISTS inventory_service_test_db;
GRANT ALL PRIVILEGES ON inventory_service_test_db.* TO 'appuser'@'%';
FLUSH PRIVILEGES;
SHOW DATABASES LIKE '%inventory%';
"
```

### Step 4: Python Environment Setup

Set up the Python environment for the application:

```bash
# Navigate to inventory service directory
cd ../inventory-service

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Unix/MacOS | Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Environment Configuration

Copy and configure the environment file for Docker setup:

```bash
# Copy environment template
cp .env.example .env
```

Update the `.env` file with Docker configuration:

```env
# Environment
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production

# Database Configuration (Docker MySQL)
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=appuser
DATABASE_PASSWORD=apppass123
DATABASE_NAME=inventory_service_db

# Test Database
TEST_DATABASE_NAME=inventory_service_test_db

# Redis Configuration (Infrastructure Redis)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=redis_dev_pass_123

# Cache TTL (seconds)
CACHE_TTL_STOCK_CHECK=300
CACHE_TTL_INVENTORY=600

# Reservation Settings
RESERVATION_TTL_MINUTES=30

# Service URLs
PRODUCT_SERVICE_URL=http://localhost:3001

# Pagination
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100

# Logging
LOG_LEVEL=DEBUG

# CORS
CORS_ORIGINS=*

# Server
HOST=0.0.0.0
PORT=5000
```

### Step 6: Database Initialization

Initialize the database with the required schema:

```bash
# Initialize database schema
python -c "
from app import create_app, db
app = create_app('development')
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')
"
```

### Step 7: Start Development Server

```bash
# Start the service in development mode
python run.py
# The service should be running on http://localhost:5000
```

## 🔧 Environment Configuration

### Database Connection (Docker)

```env
DATABASE_HOST=localhost        # MySQL container exposed on localhost
DATABASE_PORT=3306            # Standard MySQL port
DATABASE_USER=appuser         # Application database user
DATABASE_PASSWORD=apppass123  # User password
DATABASE_NAME=inventory_service_db  # Main database name
```

### Redis Connection (Infrastructure)

```env
REDIS_HOST=localhost          # Infrastructure Redis exposed on localhost
REDIS_PORT=6379              # Standard Redis port
REDIS_DB=0                   # Database number
REDIS_PASSWORD=redis_dev_pass_123  # Redis password from infrastructure
```

## 🗄️ Database Management

### Container Operations

```bash
# Start existing MySQL container
docker start mysql-inventory

# Stop MySQL container
docker stop mysql-inventory

# View MySQL logs
docker logs mysql-inventory

# Connect to MySQL shell in container
docker exec -it mysql-inventory mysql -u appuser -p inventory_service_db
```

### Database Operations

```bash
# Initialize database schema
python -c "
from app import create_app, db
app = create_app('development')
with app.app_context():
    db.create_all()
    print('Database initialized!')
"

# Reset database (careful!)
python -c "
from app import create_app, db
app = create_app('development')
with app.app_context():
    db.drop_all()
    db.create_all()
    print('Database reset!')
"
```

## 💻 Development Workflow

### Starting Development

```bash
# Start infrastructure services (Redis + RabbitMQ)
cd ../infrastructure
docker-compose up -d

# Start MySQL container (if not running)
docker start mysql-inventory

# Activate Python virtual environment
cd ../inventory-service
source venv/bin/activate  # Unix/MacOS | Windows: venv\Scripts\activate

# Start application in development mode
python run.py
```

### Making Changes

1. **Code Changes**: Edit source files in `app/`
2. **Database Changes**: Update models in `app/models/`
3. **API Changes**: Update controllers in `app/controllers/`
4. **Test Changes**: Update tests in `tests/`

### Testing Changes

```bash
# Run all tests using custom test runner
python run_tests.py

# Run tests with coverage (if pytest installed)
pytest tests/ --cov=app --cov-report=html
```

## 🧪 Testing

### Test Categories

1. **Unit Tests**: Test individual functions and models
2. **Integration Tests**: Test API endpoints and database interactions
3. **Service Tests**: Test business logic and service layers

### Running Tests

```bash
# All tests with custom runner
python run_tests.py

# Pytest (if available)
pytest tests/

# With coverage
pytest tests/ --cov=app --cov-report=html
```

## 🔧 Troubleshooting

### MySQL Container Issues

**Container won't start:**

```bash
# Check if port 3306 is already in use
netstat -an | findstr :3306  # Windows
lsof -i :3306               # macOS/Linux

# Check Docker logs
docker logs mysql-inventory
```

**Can't connect to MySQL:**

```bash
# Verify container is running
docker ps | grep mysql-inventory

# Test connection
docker exec -it mysql-inventory mysql -u appuser -p -e "SELECT VERSION();"
```

### Redis Issues (Infrastructure)

**Redis connection failed:**

```bash
# Check if infrastructure Redis is running
cd ../infrastructure
docker-compose ps | grep redis

# Test Redis connection
docker exec -it aioutlet-redis-dev redis-cli -a redis_dev_pass_123 ping
```

### Application Issues

**Port already in use:**

```bash
# Find what's using port 5000
netstat -ano | findstr :5000  # Windows
lsof -i :5000                # macOS/Linux
```

**Dependencies issues:**

```bash
# Clear pip cache and reinstall
pip cache purge
pip install -r requirements.txt --force-reinstall
```

## 🧹 Cleanup

### Daily Cleanup

```bash
# Stop application (Ctrl+C in terminal where it's running)

# Deactivate virtual environment
deactivate

# Stop containers (optional)
docker stop mysql-inventory

# Stop infrastructure services (optional)
cd ../infrastructure
docker-compose stop
```

### Full Cleanup

```bash
# Stop and remove MySQL container
docker stop mysql-inventory
docker rm mysql-inventory

# Remove MySQL data volume (ALL DATA WILL BE LOST)
docker volume rm mysql-inventory-data

# Stop infrastructure services
cd ../infrastructure
docker-compose down

# Clean up application files
rm .env
rm -rf venv
rm -rf __pycache__
rm -rf app/__pycache__
rm -rf tests/__pycache__
rm -rf .coverage
rm -rf htmlcov/
rm -rf instance/
```
