#!/bin/bash

# Inventory Service Environment Setup
# This script sets up the inventory service for any environment by reading from .env files

set -e

SERVICE_NAME="inventory-service"
SERVICE_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Default environment
ENV_NAME="development"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENV_NAME="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  -e, --env ENV_NAME    Environment name (default: development)"
            echo "                        Looks for .env.ENV_NAME file"
            echo "  -h, --help           Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                   # Uses .env (development)"
            echo "  $0 -e production     # Uses .env.production"
            echo "  $0 -e staging        # Uses .env.staging"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

echo "🚀 Setting up $SERVICE_NAME for $ENV_NAME environment..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Function to load environment variables from .env file
load_env_file() {
    local env_file=""
    
    if [ "$ENV_NAME" = "development" ]; then
        env_file="$SERVICE_PATH/.env.development"
    else
        env_file="$SERVICE_PATH/.env.$ENV_NAME"
    fi
    
    log_info "Loading environment variables from $(basename $env_file)..."
    
    if [ ! -f "$env_file" ]; then
        log_error "Environment file not found: $env_file"
        log_info "Available environment files:"
        ls -la "$SERVICE_PATH"/.env* 2>/dev/null || log_info "No .env files found"
        exit 1
    fi
    
    # Load environment variables safely
    set -a  # automatically export all variables
    
    # Source the file while filtering out comments and empty lines
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip empty lines and comments
        if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
            # Export the variable if it contains an equals sign
            if [[ "$line" =~ ^[^=]+= ]]; then
                export "$line"
            fi
        fi
    done < "$env_file"
    
    set +a  # stop automatically exporting
    
    log_success "Environment variables loaded from $(basename $env_file)"
    
    # Validate required variables
    local required_vars=("DB_NAME" "DB_USER" "DB_PASSWORD" "SERVER_PORT" "GIN_MODE")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        log_info "Please ensure these variables are set in $env_file"
        exit 1
    fi
    
    log_info "Environment: $GIN_MODE"
    log_info "Port: $SERVER_PORT"
    log_info "Database: $DB_NAME"
    log_info "Database User: $DB_USER"
}

# Check for Go
check_go() {
    log_info "Checking Go installation..."
    
    if command_exists go; then
        GO_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
        log_success "Go $GO_VERSION is installed"
        
        # Check if version is 1.21 or higher
        if [[ $(echo "$GO_VERSION" | cut -d. -f1) -lt 1 ]] || [[ $(echo "$GO_VERSION" | cut -d. -f2) -lt 21 ]]; then
            log_warning "Go version 1.21+ is recommended. Current version: $GO_VERSION"
        fi
    else
        log_error "Go is not installed. Please install Go 1.21+"
        exit 1
    fi
}

# Check for PostgreSQL
check_postgresql() {
    log_info "Checking PostgreSQL installation..."
    
    if command_exists psql; then
        POSTGRES_VERSION=$(psql --version | awk '{print $3}' | sed 's/,.*//g')
        log_success "PostgreSQL $POSTGRES_VERSION is installed"
    else
        log_error "PostgreSQL is not installed. Please install PostgreSQL 12+"
        exit 1
    fi
}

# Install Go dependencies
install_dependencies() {
    log_info "Installing Go dependencies..."
    
    cd "$SERVICE_PATH"
    
    if [ -f "go.mod" ]; then
        go mod tidy
        go mod download
        log_success "Go dependencies installed successfully"
    else
        log_error "go.mod not found in $SERVICE_PATH"
        exit 1
    fi
}

# Build the Go application
build_application() {
    log_info "Building Go application..."
    
    cd "$SERVICE_PATH"
    
    # Build for the current platform
    go build -o bin/inventory-service ./cmd/server
    
    if [ $? -eq 0 ]; then
        log_success "Application built successfully"
    else
        log_error "Application build failed"
        exit 1
    fi
}

# Setup database
setup_database() {
    log_info "Setting up database: $DB_NAME"
    
    # Check if database exists and create if not
    if ! psql -h ${DB_HOST:-localhost} -U postgres -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        log_info "Creating database: $DB_NAME"
        createdb -h ${DB_HOST:-localhost} -U postgres "$DB_NAME"
        log_success "Database created successfully"
    else
        log_info "Database $DB_NAME already exists"
    fi
    
    # Create user if not exists
    psql -h ${DB_HOST:-localhost} -U postgres -d postgres -c "
        DO \$\$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$DB_USER') THEN
                CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
            END IF;
        END
        \$\$;
        
        GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
    " > /dev/null 2>&1
    
    log_success "Database user configured"
}

# Run database setup scripts
run_database_scripts() {
    if [ -d "$SERVICE_PATH/database" ]; then
        log_info "Running database setup scripts..."
        cd "$SERVICE_PATH"
        
        # Check for Go-based migration tool or setup script
        if [ -f "database/scripts/setup.go" ]; then
            log_info "Running Go database setup..."
            go run database/scripts/setup.go
            log_success "Database setup completed"
        elif [ -f "cmd/migrate/main.go" ]; then
            log_info "Running database migrations..."
            go run cmd/migrate/main.go up
            log_success "Database migrations completed"
        else
            log_warning "No database setup script found"
        fi
    else
        log_warning "Database directory not found"
    fi
}

# Validate setup
validate_setup() {
    log_info "Validating setup..."
    
    # Check if we can connect to database
    if command_exists psql; then
        if psql -h ${DB_HOST:-localhost} -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
            log_success "Database connection successful"
        else
            log_error "Database connection failed"
            return 1
        fi
    fi
    
    # Check if Go binary exists
    if [ -f "$SERVICE_PATH/bin/inventory-service" ]; then
        log_success "Go application binary exists"
    else
        log_error "Go application binary not found"
        return 1
    fi
    
    return 0
}

# Create environment file if it doesn't exist
create_env_template() {
    local env_file=""
    
    if [ "$ENV_NAME" = "development" ]; then
        env_file="$SERVICE_PATH/.env.development"
    else
        env_file="$SERVICE_PATH/.env.$ENV_NAME"
    fi
    
    if [ ! -f "$env_file" ]; then
        log_info "Creating environment template: $(basename $env_file)"
        
        cat > "$env_file" << EOF
# Inventory Service Environment Configuration - $ENV_NAME

# Server Configuration
GIN_MODE=$ENV_NAME
SERVER_PORT=3005
SERVER_HOST=localhost

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=inventory_db
DB_USER=inventory_user
DB_PASSWORD=inventory_password
DB_SSL_MODE=disable
DB_MAX_OPEN_CONNS=25
DB_MAX_IDLE_CONNS=5
DB_CONN_MAX_LIFETIME=300s

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_POOL_SIZE=10
REDIS_MIN_IDLE_CONNS=5

# External Service URLs
AUTH_SERVICE_URL=http://localhost:3001
USER_SERVICE_URL=http://localhost:3002
PRODUCT_SERVICE_URL=http://localhost:3003
ORDER_SERVICE_URL=http://localhost:3004
NOTIFICATION_SERVICE_URL=http://localhost:3008
AUDIT_SERVICE_URL=http://localhost:3007

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-for-inventory-service-$ENV_NAME
JWT_TOKEN_EXPIRE=24h

# Logging Configuration
LOG_LEVEL=info
LOG_FORMAT=json
LOG_OUTPUT=stdout
LOG_FILE=logs/inventory-service.log

# Business Configuration
LOW_STOCK_THRESHOLD=10
CRITICAL_STOCK_THRESHOLD=5
AUTO_REORDER_ENABLED=true
STOCK_ALERT_ENABLED=true

# Cache Configuration
CACHE_TTL=300s
CACHE_ENABLED=true

# Health Check Configuration
HEALTH_CHECK_INTERVAL=30s
METRICS_ENABLED=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_SECOND=100

# Service Registry
SERVICE_NAME=inventory-service
SERVICE_VERSION=1.0.0
SERVICE_REGISTRY_URL=http://localhost:8761/eureka

# Background Jobs
STOCK_SYNC_INTERVAL=60s
LOW_STOCK_CHECK_INTERVAL=300s
CLEANUP_INTERVAL=3600s
EOF
        
        log_success "Environment template created: $(basename $env_file)"
        log_warning "Please review and update the configuration values as needed"
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "📦 Inventory Service Environment Setup"
    echo "=========================================="
    
    OS=$(detect_os)
    log_info "Detected OS: $OS"
    log_info "Target Environment: $ENV_NAME"
    
    # Create environment file if it doesn't exist
    create_env_template
    
    # Load environment variables
    load_env_file
    
    # Check prerequisites
    check_go
    check_postgresql
    
    # Install dependencies and build
    install_dependencies
    build_application
    
    # Setup database
    setup_database
    
    # Run database scripts
    run_database_scripts
    
    # Validate setup
    if validate_setup; then
        echo "=========================================="
        log_success "✅ Inventory Service setup completed successfully!"
        echo "=========================================="
        echo ""
        echo "📦 Setup Summary:"
        echo "  • Environment: $GIN_MODE"
        echo "  • Port: $SERVER_PORT"
        echo "  • Database: $DB_NAME"
        echo "  • Health Check: http://localhost:$SERVER_PORT/health"
        echo "  • API Base: http://localhost:$SERVER_PORT/api/v1"
        echo ""
        echo "🚀 Application Commands:"
        echo "   • ./bin/inventory-service        # Run the built binary"
        echo "   • go run cmd/server/main.go      # Run from source"
        echo "   • go test ./...                  # Run tests"
        echo "   • go build -o bin/inventory-service ./cmd/server  # Rebuild"
        echo ""
        echo "📊 Next Steps:"
        echo "  1. Review and update .env file if needed"
        echo "  2. Start the service: ./bin/inventory-service"
        echo "  3. Run tests: go test ./..."
        echo "  4. Check health: curl http://localhost:$SERVER_PORT/health"
        echo ""
    else
        log_error "Setup validation failed"
        exit 1
    fi
}

# Run main function
main "$@"
