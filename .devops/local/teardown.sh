```bash
#!/bin/bash

# Inventory Service - Local Development Teardown Commands
# Execute each command manually as needed

# =============================================================================
# APPLICATION CLEANUP
# =============================================================================

# Stop any running Inventory Service processes:
# Check what's running on port 5000:
lsof -i :5000
# Or on Windows:
# netstat -ano | findstr :5000

# Kill process on port 5000:
# lsof -ti:5000 | xargs kill
# Or on Windows (find PID from netstat command above, then):
# taskkill /PID <PID> /F

# Deactivate Python virtual environment (if activated):
deactivate

# =============================================================================
# DATABASE CLEANUP
# =============================================================================

# Clear application database (keep structure):
mysql -u appuser -p inventory_service_db -e "
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE stock_movements;
TRUNCATE TABLE reservations;  
TRUNCATE TABLE inventory_items;
SET FOREIGN_KEY_CHECKS = 1;
SELECT 'Database cleared' AS status;
"

# Drop databases completely (optional - ALL DATA WILL BE LOST):
mysql -u root -p -e "
DROP DATABASE IF EXISTS inventory_service_db;
DROP DATABASE IF EXISTS inventory_service_test_db;
SELECT 'Databases dropped' AS status;
"

# Remove database user (optional):
mysql -u root -p -e "
DROP USER IF EXISTS 'appuser'@'localhost';
FLUSH PRIVILEGES;
SELECT 'User removed' AS status;
"

# =============================================================================
# INFRASTRUCTURE SERVICES CLEANUP
# =============================================================================

# Stop infrastructure Redis service:
cd ../infrastructure
docker-compose stop redis

# Or stop all infrastructure services:
# docker-compose down

# Remove infrastructure services and volumes (optional - ALL DATA WILL BE LOST):
# docker-compose down -v

# =============================================================================
# MYSQL SERVICE CLEANUP (OPTIONAL)
# =============================================================================

# Stop MySQL service:
# Windows:
# net stop MySQL80

# macOS:
# brew services stop mysql@8.0

# Linux:
# sudo systemctl stop mysql

# =============================================================================
# FILE CLEANUP (OPTIONAL)
# =============================================================================

# Remove .env file:
# rm .env

# Remove Python virtual environment:
# rm -rf venv

# Remove Python cache files:
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Remove test coverage reports:
rm -rf htmlcov/
rm -f .coverage

# Remove database instance files (SQLite backup files):
rm -rf instance/

# Remove log files (if any):
# rm -rf logs/

# =============================================================================
# VERIFICATION
# =============================================================================

# Verify port 5000 is free:
lsof -i :5000
# Or on Windows:
# netstat -ano | findstr :5000

# Verify MySQL service status:
# Windows: sc query MySQL80
# macOS: brew services list | grep mysql
# Linux: sudo systemctl status mysql

# Verify infrastructure services status:
cd ../infrastructure
docker-compose ps

echo "Local teardown commands ready! Execute step by step as needed."

```
