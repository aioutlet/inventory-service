#!/bin/bash

# AI Outlet - Inventory Service Database Setup Script
# This script sets up the complete development environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$SCRIPT_DIR/.."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}🚀 AI Outlet - Inventory Service Setup${NC}"
    echo -e "${BLUE}=======================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header

cd "$SERVICE_DIR"

# 1. Check if .env exists
if [ ! -f ".env" ]; then
    print_info "Creating .env file from .env.example..."
    cp .env.example .env
    echo "" >> .env
    echo "# Database URL (for migrations and seeding)" >> .env
    echo "DATABASE_URL=postgres://postgres:password@localhost:5432/inventory_db?sslmode=disable" >> .env
    print_success ".env file created"
else
    print_info ".env file already exists"
fi

# 2. Start PostgreSQL and Redis
print_info "Starting PostgreSQL and Redis containers..."
docker-compose up -d postgres redis

# 3. Wait for databases to be healthy
print_info "Waiting for databases to be ready..."
sleep 10

# Check if containers are running
if ! docker-compose ps | grep -q "Up.*postgres"; then
    print_error "PostgreSQL container failed to start"
    exit 1
fi

if ! docker-compose ps | grep -q "Up.*redis"; then
    print_error "Redis container failed to start"
    exit 1
fi

print_success "Database containers are running"

# 4. Wait a bit more for PostgreSQL to fully initialize
print_info "Waiting for PostgreSQL to fully initialize..."
for i in {1..30}; do
    if docker exec inventory-service-postgres-1 pg_isready -U postgres >/dev/null 2>&1; then
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "PostgreSQL failed to become ready"
        exit 1
    fi
    sleep 1
done

print_success "PostgreSQL is ready"

# 5. Run migrations
print_info "Running database migrations..."
if docker exec -i inventory-service-postgres-1 psql -U postgres -d inventory_db < migrations/001_initial_schema.up.sql >/dev/null 2>&1; then
    print_success "Database migrations completed"
else
    print_warning "Migrations may have already been run (this is normal)"
fi

# 6. Build seeder
print_info "Building seeder..."
go build -o bin/seed ./cmd/seed
print_success "Seeder built successfully"

# 7. Run seeder
print_info "Seeding database with sample data..."
./bin/seed
print_success "Database seeded successfully"

# 8. Show status
echo ""
print_info "Setup completed! Here's what's running:"
docker-compose ps

echo ""
print_info "Database summary:"
docker exec inventory-service-postgres-1 psql -U postgres -d inventory_db -c "
SELECT 
    COUNT(*) as products,
    SUM(quantity_available) as total_stock,
    COUNT(*) FILTER (WHERE quantity_available <= reorder_level) as low_stock_items,
    COUNT(*) FILTER (WHERE quantity_available = 0) as out_of_stock_items
FROM inventory_items;"

echo ""
print_success "🎉 Inventory service database is ready for development!"
print_info "You can now run: ./bin/inventory-service"
echo ""
