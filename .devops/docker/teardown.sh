```bash
#!/bin/bash

# Inventory Service - Docker Development Teardown Commands
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
# MYSQL DOCKER CONTAINER CLEANUP
# =============================================================================

# Stop MySQL container:
docker stop mysql-inventory

# Remove MySQL container (data preserved in volume):
docker rm mysql-inventory

# Remove MySQL data volume (optional - ALL DATA WILL BE LOST):
# docker volume rm mysql-inventory-data

# =============================================================================
# INFRASTRUCTURE SERVICES CLEANUP
# =============================================================================

# Stop infrastructure services:
cd ../infrastructure
docker-compose stop

# Or stop all infrastructure services and remove containers:
# docker-compose down

# Remove infrastructure services and volumes (optional - ALL DATA WILL BE LOST):
# docker-compose down -v

# =============================================================================
# NETWORK CLEANUP (OPTIONAL)
# =============================================================================

# Remove custom network (optional):
# docker network rm aioutlet-dev-network

# =============================================================================
# FILE CLEANUP (OPTIONAL)
# =============================================================================

# Navigate back to inventory service
cd ../inventory-service

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

# Verify port 3306 is free:
lsof -i :3306
# Or on Windows:
# netstat -ano | findstr :3306

# Verify containers are stopped:
docker ps | grep -E "(mysql-inventory|aioutlet)"

# Verify infrastructure services status:
cd ../infrastructure
docker-compose ps

# List remaining Docker volumes:
docker volume ls | grep -E "(mysql|aioutlet)"

# List remaining Docker networks:
docker network ls | grep aioutlet

echo "Docker teardown commands ready! Execute step by step as needed."

```
