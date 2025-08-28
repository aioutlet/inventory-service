```bash
#!/bin/bash

# Inventory Service - Docker Development Setup Commands
# Execute each command manually as needed

# =============================================================================
# STEP 1: Prerequisites Check
# =============================================================================

# Check Docker
docker --version

# Check Docker Compose
docker-compose --version

# Check Python version (requires 3.8+)
python --version

# Check pip version
pip --version

# Check Git
git --version

# =============================================================================
# STEP 2: Infrastructure Services Setup
# =============================================================================

# Navigate to infrastructure directory
cd ../infrastructure

# Start all infrastructure services (Redis + RabbitMQ)
docker-compose up -d

# Verify infrastructure services are running
docker-compose ps

# Test Redis connection
docker exec -it aioutlet-redis-dev redis-cli -a redis_dev_pass_123 ping

# =============================================================================
# STEP 3: MySQL Docker Container Setup
# =============================================================================

# Pull MySQL image
docker pull mysql:8.0

# Create MySQL container with proper network and environment
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
echo "Waiting for MySQL to start..."
sleep 30

# Verify MySQL container is running
docker ps | grep mysql-inventory

# Check MySQL logs for any errors
docker logs mysql-inventory

# Create test database
docker exec -it mysql-inventory mysql -u root -proot_pass_123 -e "
CREATE DATABASE IF NOT EXISTS inventory_service_test_db;
GRANT ALL PRIVILEGES ON inventory_service_test_db.* TO 'appuser'@'%';
FLUSH PRIVILEGES;
SHOW DATABASES LIKE '%inventory%';
SELECT 'Test database created successfully!' AS status;
"

# Test MySQL connection with app credentials
docker exec -it mysql-inventory mysql -u appuser -papppass123 inventory_service_db -e "
SELECT 'MySQL connection successful!' AS status;
SHOW TABLES;
"

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

# Or create .env file manually with Docker settings:
cat << 'EOF' > .env
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
# docker exec -i mysql-inventory mysql -u appuser -papppass123 inventory_service_db < database/init.sql

# Verify tables were created:
docker exec -it mysql-inventory mysql -u appuser -papppass123 inventory_service_db -e "
SHOW TABLES;
DESCRIBE inventory_items;
SELECT 'Database initialization verified!' AS status;
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

# Docker MySQL management:
# docker exec -it mysql-inventory mysql -u appuser -papppass123 inventory_service_db
# docker start mysql-inventory      # Start container
# docker stop mysql-inventory       # Stop container
# docker restart mysql-inventory    # Restart container
# docker logs mysql-inventory       # View logs

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

# Check what's running on port 3306 (MySQL):
lsof -i :3306
# Or on Windows:
# netstat -ano | findstr :3306

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

# Docker troubleshooting:
# docker ps -a                      # List all containers
# docker logs mysql-inventory       # View MySQL logs
# docker exec -it mysql-inventory bash # Connect to container shell
# docker volume ls                  # List Docker volumes
# docker volume inspect mysql-inventory-data # Inspect volume
# docker network ls | grep aioutlet # Check networks

# MySQL Authentication Issues:
# Reset MySQL user:
# docker exec -it mysql-inventory mysql -u root -proot_pass_123 -e "
# DROP USER IF EXISTS 'appuser'@'%';
# CREATE USER 'appuser'@'%' IDENTIFIED BY 'apppass123';
# GRANT ALL PRIVILEGES ON inventory_service_db.* TO 'appuser'@'%';
# GRANT ALL PRIVILEGES ON inventory_service_test_db.* TO 'appuser'@'%';
# FLUSH PRIVILEGES;
# "

# Infrastructure troubleshooting:
# docker-compose -f ../infrastructure/docker-compose.yml ps
# docker-compose -f ../infrastructure/docker-compose.yml logs redis
# docker network ls | grep aioutlet

echo "Docker setup commands ready! Execute step by step as needed."

```
