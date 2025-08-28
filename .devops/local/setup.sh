```bash
#!/bin/bash

# Inventory Service - Local Development Setup Commands (MySQL and Redis locally/infrastructure)
# Execute each command manually as needed

# =============================================================================
# STEP 1: Prerequisites Check
# =============================================================================

# Check Python version (requires 3.8+)
python --version

# Check pip version
pip --version

# Check MySQL version
mysql --version

# Check Redis (if installing locally - optional)
redis-server --version

# Check Git
git --version

# =============================================================================
# STEP 2: Infrastructure Services Setup (Redis via Docker)
# =============================================================================

# Navigate to infrastructure directory
cd ../infrastructure

# Start Redis service using Docker Compose
docker-compose up -d redis

# Verify Redis is running
docker ps | grep redis

# Test Redis connection
docker exec -it aioutlet-redis-dev redis-cli -a redis_dev_pass_123 ping

# =============================================================================
# STEP 3: Local MySQL Setup
# =============================================================================

# Install MySQL Community Server:
# Windows: Download from https://dev.mysql.com/downloads/installer/
# macOS:
# brew install mysql@8.0
# brew services start mysql@8.0

# Ubuntu/Debian:
# sudo apt update
# sudo apt install mysql-server
# sudo systemctl start mysql
# sudo systemctl enable mysql

# Create database and user:
mysql -u root -p -e "
CREATE DATABASE IF NOT EXISTS inventory_service_db;
CREATE DATABASE IF NOT EXISTS inventory_service_test_db;

CREATE USER IF NOT EXISTS 'appuser'@'localhost' IDENTIFIED BY 'apppass123';
GRANT ALL PRIVILEGES ON inventory_service_db.* TO 'appuser'@'localhost';
GRANT ALL PRIVILEGES ON inventory_service_test_db.* TO 'appuser'@'localhost';
FLUSH PRIVILEGES;

-- Verify databases created
SHOW DATABASES LIKE '%inventory%';

-- Test connection
USE inventory_service_db;
SELECT 'Database connection successful!' AS status;
"

# Verify MySQL connection with app credentials:
mysql -u appuser -p -e "SHOW DATABASES;"

# =============================================================================
# STEP 4: Project Setup
# =============================================================================

# Navigate to inventory service directory (if not already there)
cd inventory-service

# Create Python virtual environment
python -m venv venv

# Activate virtual environment:
# Windows:
# venv\Scripts\activate

# Unix/MacOS:
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify key packages are installed
pip list | grep -E "(Flask|PyMySQL|redis|SQLAlchemy)"

# =============================================================================
# STEP 5: Environment Configuration
# =============================================================================

# Copy environment template:
cp .env.example .env

# Or create .env file manually with local settings:
cat << 'EOF' > .env
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

# Server
HOST=0.0.0.0
PORT=5000
EOF

# Test environment loading:
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('✅ Environment loaded successfully')
print(f'Database: {os.environ.get('DATABASE_NAME')}')
print(f'Redis Host: {os.environ.get('REDIS_HOST')}')
"

# =============================================================================
# STEP 6: Database Initialization
# =============================================================================

# Initialize database schema using Python:
python -c "
from app import create_app, db
app = create_app('development')
with app.app_context():
    try:
        db.create_all()
        print('✅ Database tables created successfully!')
    except Exception as e:
        print(f'❌ Error creating database tables: {e}')
        raise
"

# Or use MySQL script directly (optional):
# mysql -u appuser -p inventory_service_db < database/init.sql

# Verify tables were created:
mysql -u appuser -p inventory_service_db -e "
SHOW TABLES;
DESCRIBE inventory_items;
"

# =============================================================================
# STEP 7: Testing Setup
# =============================================================================

# Run tests to verify setup:
python run_tests.py

# Or with pytest (if preferred):
# pytest tests/ -v

# Check code style (optional):
black app/ tests/ --check
flake8 app/ tests/
isort app/ tests/ --check-only

# =============================================================================
# STEP 8: Start Application
# =============================================================================

# Development mode (with auto-reload):
python run.py

# Production mode (not recommended for development):
# gunicorn run:app

# =============================================================================
# STEP 9: Verify Setup (run in another terminal)
# =============================================================================

# Health check:
curl http://localhost:5000/api/v1/health/

# Test API endpoints:
# Create inventory item:
curl -X POST http://localhost:5000/api/v1/inventory/ \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "TEST001",
    "quantity": 100,
    "minimum_stock_level": 10,
    "location": "Test Warehouse"
  }'

# Get inventory:
curl http://localhost:5000/api/v1/inventory/

# Check stock for a product:
curl http://localhost:5000/api/v1/inventory/TEST001/stock/

# =============================================================================
# ADDITIONAL COMMANDS
# =============================================================================

# Development workflow commands:
# python run.py                # Start in development mode
# python run_tests.py          # Run all tests
# black app/ tests/            # Format code
# flake8 app/ tests/           # Lint code
# isort app/ tests/            # Sort imports

# Virtual environment management:
# source venv/bin/activate     # Activate (Unix/MacOS)
# venv\Scripts\activate        # Activate (Windows)
# deactivate                   # Deactivate
# pip freeze > requirements.txt # Update requirements

# MySQL database management:
# mysql -u appuser -p inventory_service_db
# mysql -u root -p -e "SHOW PROCESSLIST;"
# mysql -u root -p -e "SHOW DATABASES;"

# Infrastructure Redis management:
# docker exec -it aioutlet-redis-dev redis-cli -a redis_dev_pass_123
# docker-compose -f ../infrastructure/docker-compose.yml logs redis
# docker-compose -f ../infrastructure/docker-compose.yml restart redis

# =============================================================================
# TROUBLESHOOTING COMMANDS
# =============================================================================

# Check what's running on port 5000:
lsof -i :5000
# Or on Windows:
# netstat -ano | findstr :5000

# Kill process on port 5000:
# lsof -ti:5000 | xargs kill
# Or on Windows (find PID from netstat command above, then):
# taskkill /PID <PID> /F

# Test database connection:
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

# Test Redis connection:
python -c "
import redis
try:
    r = redis.Redis(host='localhost', port=6379, password='redis_dev_pass_123', db=0)
    r.ping()
    print('✅ Redis connection successful!')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
"

# MySQL service troubleshooting:
# Check MySQL status:
# Windows: sc query MySQL80
# macOS: brew services list | grep mysql
# Linux: sudo systemctl status mysql

# Check MySQL error logs:
# Windows: Check Event Viewer or MySQL data directory
# macOS: /opt/homebrew/var/mysql/*.err
# Linux: /var/log/mysql/error.log

# Reset MySQL user password:
# mysql -u root -p -e "ALTER USER 'appuser'@'localhost' IDENTIFIED BY 'apppass123';"

# Infrastructure troubleshooting:
# docker-compose -f ../infrastructure/docker-compose.yml ps
# docker-compose -f ../infrastructure/docker-compose.yml logs redis
# docker network ls | grep aioutlet

echo "Local setup commands ready! Execute step by step as needed."

```
