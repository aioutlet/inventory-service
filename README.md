# Inventory Service

A high-performance inventory management microservice built with Go, PostgreSQL, and Redis. This service handles stock tracking, reservations, and inventory operations for the AI Outlet e-commerce platform.

## Features

### Core Functionality

- **Stock Management**: Real-time inventory tracking with atomic updates
- **Reservation System**: Temporary stock holds with automatic expiration
- **Cache Layer**: Redis-based caching for improved performance
- **Audit Trail**: Complete stock movement history
- **Low Stock Alerts**: Automatic monitoring of reorder levels

### API Capabilities

- **Stock Checking**: Verify availability for multiple items
- **Stock Reservation**: Reserve inventory for orders with TTL
- **Inventory Updates**: Manual stock adjustments and restocking
- **Search & Query**: Flexible inventory search and filtering
- **Admin Operations**: Background task management

### Architecture

- **Repository Pattern**: Clean separation of data access
- **Service Layer**: Business logic encapsulation
- **HTTP REST API**: Standard JSON API with Gin framework
- **Database Migrations**: Versioned schema management
- **Health Checks**: Comprehensive monitoring endpoints

## Quick Start

### Prerequisites

- Go 1.21+
- PostgreSQL 12+
- Redis 6+
- Docker & Docker Compose (optional)

### Local Development

1. **Clone and setup**:

   ```bash
   git clone <repository>
   cd inventory-service
   cp .env.example .env
   ```

2. **Start dependencies**:

   ```bash
   make dev-services
   ```

3. **Run migrations**:

   ```bash
   make migrate-up
   ```

4. **Start the service**:
   ```bash
   make run
   ```

### Docker Development

```bash
# Start everything with Docker Compose
make docker-compose-up

# Or build and run individually
make docker-build
make docker-run
```

## API Documentation

### Base URL

```
http://localhost:8080/api/v1
```

### Core Endpoints

#### Check Stock Availability

```http
POST /stock/check
```

```json
{
  "items": [
    { "sku": "LAPTOP-001", "quantity": 2 },
    { "sku": "MOUSE-001", "quantity": 5 }
  ]
}
```

#### Reserve Stock

```http
POST /stock/reserve
```

```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "items": [{ "sku": "LAPTOP-001", "quantity": 1 }]
}
```

#### Update Stock

```http
PUT /stock/update
```

```json
{
  "sku": "LAPTOP-001",
  "quantity": 50,
  "type": "in",
  "reason": "Restock from supplier"
}
```

#### Get Inventory Item

```http
GET /inventory/sku/{sku}
GET /inventory/product/{product_id}
```

#### Search Inventory

```http
GET /inventory/search?q=laptop&limit=20&offset=0
```

#### Low Stock Alert

```http
GET /inventory/low-stock
```

### Reservation Management

#### Confirm Reservation

```http
PUT /reservations/{id}/confirm
```

#### Release Reservation

```http
PUT /reservations/{id}/release
```

#### Get Reservations

```http
GET /reservations/{id}
GET /orders/{order_id}/reservations
```

### Admin Operations

#### Process Expired Reservations

```http
POST /admin/reservations/process-expired
```

#### Cleanup Old Data

```http
DELETE /admin/reservations/cleanup
```

## Configuration

### Environment Variables

| Variable      | Description         | Default        |
| ------------- | ------------------- | -------------- |
| `ENVIRONMENT` | Runtime environment | `development`  |
| `LOG_LEVEL`   | Logging level (1-5) | `4`            |
| `PORT`        | HTTP server port    | `8080`         |
| `DB_HOST`     | PostgreSQL host     | `localhost`    |
| `DB_PORT`     | PostgreSQL port     | `5432`         |
| `DB_USER`     | Database user       | `postgres`     |
| `DB_PASSWORD` | Database password   | `password`     |
| `DB_NAME`     | Database name       | `inventory_db` |
| `REDIS_HOST`  | Redis host          | `localhost`    |
| `REDIS_PORT`  | Redis port          | `6379`         |

## Integration with AI Outlet

This service integrates seamlessly with the existing microservices:

### Order Service Integration

- **Stock Reservation**: Reserve inventory during order creation
- **Order Fulfillment**: Confirm reservations after payment success
- **Order Cancellation**: Release reservations for cancelled orders

### Product Service Integration

- **Availability Display**: Real-time stock status for product listings
- **Inventory Sync**: Coordinate product catalog with stock levels

### Event-Driven Architecture

The service can publish events for:

- Low stock alerts
- Reservation expiry
- Stock movements
- Reorder triggers

## License

This project is part of the AI Outlet microservices platform.
