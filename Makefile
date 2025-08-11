# Makefile for Inventory Service

.PHONY: build run test clean docker-build docker-run migrate-up migrate-down deps

# Variables
BINARY_NAME=inventory-service
DOCKER_IMAGE=inventory-service:latest
DOCKER_CONTAINER=inventory-service-container

# Build the application
build:
	go build -o bin/$(BINARY_NAME) ./cmd/server

# Run the application
run:
	go run ./cmd/server

# Run tests
test:
	go test -v ./...

# Run tests with coverage
test-coverage:
	go test -v -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

# Clean build artifacts
clean:
	rm -rf bin/
	rm -f coverage.out coverage.html

# Install dependencies
deps:
	go mod download
	go mod tidy

# Build Docker image
docker-build:
	docker build -t $(DOCKER_IMAGE) .

# Run Docker container
docker-run:
	docker run --name $(DOCKER_CONTAINER) -p 8080:8080 --env-file .env $(DOCKER_IMAGE)

# Run with Docker Compose
docker-compose-up:
	docker-compose up --build

# Stop Docker Compose
docker-compose-down:
	docker-compose down

# Database migrations (requires migrate CLI tool)
migrate-install:
	go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest

migrate-up:
	migrate -path migrations -database "postgresql://postgres:password@localhost:5432/inventory_db?sslmode=disable" up

migrate-down:
	migrate -path migrations -database "postgresql://postgres:password@localhost:5432/inventory_db?sslmode=disable" down

# Format code
fmt:
	go fmt ./...

# Lint code (requires golangci-lint)
lint:
	golangci-lint run

# Generate mocks (requires mockgen)
generate-mocks:
	go generate ./...

# Security scan (requires gosec)
security:
	gosec ./...

# Development setup
dev-setup: deps migrate-install
	@echo "Installing development tools..."
	go install github.com/golang/mock/mockgen@latest
	go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest
	go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Start local services for development
dev-services:
	docker-compose up postgres redis -d

# Stop local services
dev-services-stop:
	docker-compose stop postgres redis

# Full development environment
dev: dev-services migrate-up run

# Help
help:
	@echo "Available commands:"
	@echo "  build              - Build the application"
	@echo "  run                - Run the application"
	@echo "  test               - Run tests"
	@echo "  test-coverage      - Run tests with coverage"
	@echo "  clean              - Clean build artifacts"
	@echo "  deps               - Install dependencies"
	@echo "  docker-build       - Build Docker image"
	@echo "  docker-run         - Run Docker container"
	@echo "  docker-compose-up  - Run with Docker Compose"
	@echo "  docker-compose-down- Stop Docker Compose"
	@echo "  migrate-up         - Run database migrations"
	@echo "  migrate-down       - Rollback database migrations"
	@echo "  fmt                - Format code"
	@echo "  lint               - Lint code"
	@echo "  security           - Run security scan"
	@echo "  dev-setup          - Setup development environment"
	@echo "  dev-services       - Start local services"
	@echo "  dev                - Full development environment"
	@echo "  help               - Show this help"
