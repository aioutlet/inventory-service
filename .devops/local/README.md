````markdown
# Inventory Service - Local Development Setup

This guide provides step-by-step instructions for setting up the Inventory Service with MySQL and Redis installed locally on your development machine.

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
- **MySQL** (v8.0+ recommended)
- **Redis** (v7.0+ recommended) - _Optional: Use infrastructure Redis instead_
- **Git** (for version control)

### Verify Prerequisites

```bash
# Check versions
python --version      # Should be v3.8+
pip --version         # Should be recent
mysql --version       # Should be 8.0+
redis-server --version # Should be 7.0+ (if installing locally)
git --version
```

## 🚀 Quick Start

For experienced developers who want to get started immediately:

```bash
# 1. Start infrastructure services (Redis + RabbitMQ)
cd ../infrastructure
docker-compose up -d

# 2. Install and start MySQL locally
# (Installation varies by OS - see Detailed Setup section)

# 3. Create MySQL database and user
mysql -u root -p -e "
CREATE DATABASE inventory_service_db;
CREATE USER 'appuser'@'localhost' IDENTIFIED BY 'apppass123';
GRANT ALL PRIVILEGES ON inventory_service_db.* TO 'appuser'@'localhost';
FLUSH PRIVILEGES;
"

# 4. Setup Python environment and install dependencies
cd inventory-service
python -m venv venv
# Windows: venv\Scripts\activate
# Unix/MacOS: source venv/bin/activate
pip install -r requirements.txt

# 5. Copy and configure environment
cp .env.example .env
# Edit .env to use local MySQL and infrastructure Redis

# 6. Initialize database and start service
python -c "from app import create_app, db; app = create_app('development'); app.app_context().push(); db.create_all(); print('Database initialized!')"
python run.py
```

## 📖 Detailed Setup

### Step 1: Infrastructure Services Setup

The Inventory Service requires Redis for caching. We'll use the shared infrastructure Redis instead of installing locally:

```bash
# Navigate to infrastructure directory
cd ../infrastructure

# Start Redis and RabbitMQ using Docker Compose
docker-compose up -d redis

# Verify Redis is running
docker ps | grep redis
```

### Step 2: MySQL Local Installation

Install MySQL Community Server on your system:

**Windows:**

```bash
# Download from https://dev.mysql.com/downloads/installer/
# Follow the installer instructions
# MySQL will be installed as a service by default
```

**macOS (using Homebrew):**

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install MySQL
brew install mysql@8.0

# Start MySQL service
brew services start mysql@8.0

# Secure installation (optional)
mysql_secure_installation
```

**Linux (Ubuntu/Debian):**

```bash
# Update package list
sudo apt update

# Install MySQL Server
sudo apt install mysql-server

# Secure installation
sudo mysql_secure_installation

# Start MySQL service
sudo systemctl start mysql
sudo systemctl enable mysql
```

### Step 3: MySQL Database Setup

Create the database and user for the Inventory Service:

```bash
# Connect to MySQL as root
mysql -u root -p

# In MySQL shell, create database and user
CREATE DATABASE inventory_service_db;
CREATE DATABASE inventory_service_test_db;

CREATE USER 'appuser'@'localhost' IDENTIFIED BY 'apppass123';
GRANT ALL PRIVILEGES ON inventory_service_db.* TO 'appuser'@'localhost';
GRANT ALL PRIVILEGES ON inventory_service_test_db.* TO 'appuser'@'localhost';
FLUSH PRIVILEGES;

# Test connection
USE inventory_service_db;
SHOW TABLES;

# Exit MySQL shell
EXIT;
```

### Step 4: Python Environment Setup

Set up a Python virtual environment for the service:

```bash
# Navigate to inventory service directory
cd inventory-service

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Unix/MacOS:
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Environment Configuration

Copy and configure the environment file:

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
# Use your preferred editor: nano .env, code .env, vim .env, etc.
```

Update the `.env` file with local configuration:

```env
# Environment
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production

# Database Configuration (Local MySQL)
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
```

### Step 6: Database Initialization

Initialize the database with the required schema:

```bash
# Initialize database schema (Python way)
python -c "
from app import create_app, db
app = create_app('development')
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')
"

# Or use MySQL script directly
mysql -u appuser -p inventory_service_db < database/init.sql
```

### Step 7: Start Development Server

```bash
# Make sure virtual environment is activated
# Windows: venv\Scripts\activate
# Unix/MacOS: source venv/bin/activate

# Start the service in development mode
python run.py

# The service should be running on http://localhost:5000
```

## 🔧 Environment Configuration

The Inventory Service uses environment variables for configuration. Here's the local-specific setup:

### Database Connection Breakdown (Local)

```env
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=appuser
DATABASE_PASSWORD=apppass123
DATABASE_NAME=inventory_service_db
```

**Connection String:**
`mysql+pymysql://appuser:apppass123@localhost:3306/inventory_service_db`

### Redis Connection Breakdown (Infrastructure)

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=redis_dev_pass_123
```

### Environment Files

- `.env.example` - Template for development
- `.env` - Your local configuration (not in git)

## 🗄️ Database Management

### MySQL Service Operations

**Windows:**

```bash
# Start MySQL service
net start MySQL80

# Stop MySQL service
net stop MySQL80

# Check service status
sc query MySQL80
```

**macOS:**

```bash
# Start MySQL service
brew services start mysql@8.0

# Stop MySQL service
brew services stop mysql@8.0

# Check service status
brew services list | grep mysql
```

**Linux:**

```bash
# Start MySQL service
sudo systemctl start mysql

# Stop MySQL service
sudo systemctl stop mysql

# Check service status
sudo systemctl status mysql

# Enable auto-start on boot
sudo systemctl enable mysql
```

### Database Operations

```bash
# Connect to MySQL with application credentials
mysql -u appuser -p inventory_service_db

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

### Manual Database Operations

```bash
# Connect and perform operations
mysql -u appuser -p inventory_service_db -e "
-- List tables
SHOW TABLES;

-- Count inventory items
SELECT COUNT(*) as inventory_count FROM inventory_items;

-- Show sample inventory
SELECT * FROM inventory_items LIMIT 5;

-- Show active reservations
SELECT * FROM reservations WHERE status = 'ACTIVE' LIMIT 5;
"
```

## 💻 Development Workflow

### Starting Development

```bash
# Start infrastructure services (Redis)
cd ../infrastructure
docker-compose up -d redis

# Start MySQL service (if not already running)
# Windows: net start MySQL80
# macOS: brew services start mysql@8.0
# Linux: sudo systemctl start mysql

# Activate Python virtual environment
cd ../inventory-service
# Windows: venv\Scripts\activate
# Unix/MacOS: source venv/bin/activate

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

# Run specific tests with pytest (if installed)
pytest tests/test_models.py -v

# Run tests with coverage
pytest tests/ --cov=app --cov-report=html
```

### Code Quality

```bash
# Format code with black
black app/ tests/

# Check imports with isort
isort app/ tests/

# Lint with flake8
flake8 app/ tests/
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

# Watch mode (if pytest-watch is installed)
ptw tests/
```

### Test Database

Tests use a separate test database (`inventory_service_test_db`) that's automatically created and cleaned up.

## 🔧 Troubleshooting

### MySQL Issues

**MySQL service won't start:**

```bash
# Check if port 3306 is already in use
netstat -an | findstr :3306  # Windows
lsof -i :3306               # macOS/Linux

# Check MySQL error log
# Windows: Check Event Viewer or MySQL data directory
# macOS: /opt/homebrew/var/mysql/*.err
# Linux: /var/log/mysql/error.log
```

**Can't connect to MySQL:**

```bash
# Verify MySQL is running
mysql -u root -p -e "SELECT VERSION();"

# Check if user exists
mysql -u root -p -e "SELECT User, Host FROM mysql.user WHERE User='appuser';"

# Test application credentials
mysql -u appuser -p inventory_service_db -e "SHOW TABLES;"
```

### Redis Issues (Infrastructure)

**Redis connection failed:**

```bash
# Check if infrastructure Redis is running
docker ps | grep redis

# Test Redis connection
docker exec -it aioutlet-redis-dev redis-cli -a redis_dev_pass_123 ping

# Restart infrastructure Redis
cd ../infrastructure
docker-compose restart redis
```

### Python/Application Issues

**Port already in use:**

```bash
# Find what's using port 5000
netstat -ano | findstr :5000  # Windows
lsof -i :5000                # macOS/Linux

# Kill process
taskkill /PID <PID> /F       # Windows
kill -9 <PID>                # macOS/Linux
```

**Import errors:**

```bash
# Check virtual environment is activated
which python  # Unix/MacOS
where python  # Windows

# Verify packages are installed
pip list | grep Flask
pip list | grep PyMySQL
pip list | grep redis

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Database connection issues:**

```bash
# Test database connection
python -c "
import pymysql
try:
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        user='appuser',
        password='apppass123',
        database='inventory_service_db'
    )
    print('✅ Database connection successful!')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

### Environment Issues

**Environment file issues:**

```bash
# Verify environment file exists and has correct format
cat .env

# Check for syntax errors in environment loading
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('Environment loaded successfully')
print(f'Database Host: {os.environ.get(\"DATABASE_HOST\")}')
print(f'Redis Host: {os.environ.get(\"REDIS_HOST\")}')
"
```

## 🧹 Cleanup

### Daily Cleanup

```bash
# Stop application (Ctrl+C in terminal where it's running)

# Deactivate virtual environment
deactivate

# Stop infrastructure services (optional)
cd ../infrastructure
docker-compose stop redis

# Stop MySQL service (optional)
# Windows: net stop MySQL80
# macOS: brew services stop mysql@8.0
# Linux: sudo systemctl stop mysql
```

### Full Cleanup

Use the teardown script for comprehensive cleanup:

```bash
# Navigate to local setup directory
cd .devops/local

# Run teardown commands manually
# See teardown.sh for complete list of commands

# Or follow the teardown script step by step
```

**Manual cleanup:**

```bash
# Remove virtual environment
rm -rf venv

# Clear database (optional)
mysql -u appuser -p -e "
DROP DATABASE IF EXISTS inventory_service_db;
DROP DATABASE IF EXISTS inventory_service_test_db;
"

# Remove MySQL user (optional)
mysql -u root -p -e "
DROP USER IF EXISTS 'appuser'@'localhost';
FLUSH PRIVILEGES;
"

# Clean up application files
rm .env
rm -rf __pycache__
rm -rf app/__pycache__
rm -rf tests/__pycache__
rm -rf .coverage
rm -rf htmlcov/
rm -rf instance/
```
````
