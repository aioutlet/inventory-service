#!/bin/bash

# AI Outlet - Inventory Service Seeder Script
# This script provides convenient commands for seeding the inventory database

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$SCRIPT_DIR/.."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}🌱 AI Outlet - Inventory Service Seeder${NC}"
    echo -e "${BLUE}===============================================${NC}"
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

check_dependencies() {
    print_info "Checking dependencies..."
    
    if ! command -v go &> /dev/null; then
        print_error "Go is not installed or not in PATH"
        exit 1
    fi
    
    print_success "Go found: $(go version)"
    
    # Check if we're in the right directory
    if [ ! -f "$SERVICE_DIR/go.mod" ]; then
        print_error "Not in inventory service directory or go.mod not found"
        exit 1
    fi
    
    print_success "Inventory service directory confirmed"
}

build_seeder() {
    print_info "Building seeder..."
    cd "$SERVICE_DIR"
    
    if go build -o bin/seed ./cmd/seed; then
        print_success "Seeder built successfully"
    else
        print_error "Failed to build seeder"
        exit 1
    fi
}

show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build                  Build the seeder binary"
    echo "  seed                   Run seeder with default data"
    echo "  seed-file <file>       Run seeder with custom JSON file"
    echo "  clear                  Clear all data"
    echo "  clear-and-seed         Clear data and reseed with default data"
    echo "  clear-and-seed-file    Clear data and reseed with custom JSON file"
    echo "  summary                Show database summary without seeding"
    echo ""
    echo "Options:"
    echo "  --verbose              Enable verbose logging"
    echo "  --no-summary           Disable summary after seeding"
    echo ""
    echo "Examples:"
    echo "  $0 seed                                    # Seed with default data"
    echo "  $0 seed-file inventory-data.json          # Seed with custom file"
    echo "  $0 clear-and-seed --verbose               # Clear and reseed with verbose output"
    echo "  $0 seed --no-summary                      # Seed without showing summary"
    echo ""
}

run_seeder() {
    local args=()
    local verbose=false
    local no_summary=false
    
    # Parse options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --verbose)
                verbose=true
                args+=("-verbose")
                shift
                ;;
            --no-summary)
                no_summary=true
                args+=("-summary=false")
                shift
                ;;
            *)
                args+=("$1")
                shift
                ;;
        esac
    done
    
    cd "$SERVICE_DIR"
    
    print_info "Running seeder with args: ${args[*]}"
    
    if [ "$verbose" = true ]; then
        ./bin/seed "${args[@]}"
    else
        ./bin/seed "${args[@]}" 2>/dev/null || {
            print_error "Seeder failed. Run with --verbose for more details."
            exit 1
        }
    fi
}

# Main script logic
print_header

case "${1:-}" in
    "build")
        check_dependencies
        build_seeder
        ;;
    "seed")
        check_dependencies
        build_seeder
        shift
        run_seeder "$@"
        ;;
    "seed-file")
        if [ -z "${2:-}" ]; then
            print_error "Please provide a JSON file path"
            show_usage
            exit 1
        fi
        
        file_path="$2"
        if [ ! -f "$file_path" ]; then
            print_error "File not found: $file_path"
            exit 1
        fi
        
        check_dependencies
        build_seeder
        shift 2
        run_seeder "-file" "$file_path" "$@"
        ;;
    "clear")
        check_dependencies
        build_seeder
        shift
        run_seeder "-clear" "$@"
        ;;
    "clear-and-seed")
        check_dependencies
        build_seeder
        shift
        run_seeder "-clear" "$@"
        ;;
    "clear-and-seed-file")
        if [ -z "${2:-}" ]; then
            print_error "Please provide a JSON file path"
            show_usage
            exit 1
        fi
        
        file_path="$2"
        if [ ! -f "$file_path" ]; then
            print_error "File not found: $file_path"
            exit 1
        fi
        
        check_dependencies
        build_seeder
        shift 2
        run_seeder "-clear" "-file" "$file_path" "$@"
        ;;
    "summary")
        check_dependencies
        build_seeder
        shift
        # Run seeder without any data operations, just show summary
        print_info "Showing database summary..."
        cd "$SERVICE_DIR"
        ./bin/seed -summary "$@" < /dev/null || true
        ;;
    *)
        show_usage
        ;;
esac

print_success "Operation completed!"
