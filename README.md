# Inventory Service

A Flask-based microservice for managing product inventory in the AI Outlet e-commerce platform.

## Features

- **Inventory Management**: Create, read, update, and delete inventory items
- **Stock Tracking**: Real-time stock level monitoring with automated alerts
- **Reservation System**: Reserve inventory for orders with expiration management
- **Stock Movements**: Complete audit trail of all stock changes
- **Caching**: Redis-based caching for improved performance
- **API Documentation**: Auto-generated Swagger/OpenAPI documentation
- **Health Monitoring**: Built-in health checks for all dependencies
- **Comprehensive Testing**: Unit and integration tests with high coverage

## Technology Stack

- **Framework**: Flask 2.3.3 with Flask-RESTX for API documentation
- **Database**: MySQL 8.0 with SQLAlchemy 2.0.21 ORM
- **Caching**: Redis for session and query caching
- **Testing**: pytest with comprehensive test suite
- **Containerization**: Docker and Docker Compose
- **Code Quality**: Black, flake8, pre-commit hooks

## Project Structure

```
inventory-service/
├── app/
│   ├── __init__.py          # Application factory
│   ├── controllers/         # REST API controllers
│   ├── models/             # SQLAlchemy database models
│   ├── repositories/       # Data access layer
│   ├── services/          # Business logic layer
│   └── utils/             # Utility functions and helpers
├── tests/                 # Comprehensive test suite
├── database/             # Database initialization scripts
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── run.py              # Application entry point
├── Dockerfile          # Container configuration
└── docker-compose.yml  # Multi-container orchestration
```

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone and navigate to the service directory**:

   ```bash
   cd inventory-service
   ```

2. **Start all services**:

   ```bash
   docker-compose up -d
   ```

3. **Verify services are running**:

   ```bash
   docker-compose ps
   ```

4. **Access the API**:
   - API Base URL: http://localhost:5003/api/v1
   - Documentation: http://localhost:5003/api/v1/docs/
   - Health Check: http://localhost:5003/api/v1/health/

### Local Development Setup

1. **Create virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**:

   ```bash
   export FLASK_ENV=development
   export DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/inventory_db
   export REDIS_URL=redis://localhost:6379/0
   ```

4. **Initialize database**:

   ```bash
   python -c "from app import create_app; from app.models import db; app = create_app('development'); app.app_context().push(); db.create_all()"
   ```

5. **Run the application**:
   ```bash
   python run.py
   ```

## API Endpoints

### Inventory Management

- `GET /api/v1/inventory/` - List inventory items with filtering
- `POST /api/v1/inventory/` - Create new inventory item
- `GET /api/v1/inventory/{product_id}` - Get inventory by product ID
- `PUT /api/v1/inventory/{product_id}` - Update inventory item
- `DELETE /api/v1/inventory/{product_id}` - Delete inventory item
- `POST /api/v1/inventory/{product_id}/adjust` - Adjust stock levels
- `POST /api/v1/inventory/bulk` - Bulk inventory operations

### Reservation Management

- `GET /api/v1/reservations/` - List reservations with filtering
- `POST /api/v1/reservations/` - Create new reservation
- `GET /api/v1/reservations/{id}` - Get reservation details
- `DELETE /api/v1/reservations/{id}` - Cancel reservation
- `POST /api/v1/reservations/confirm` - Confirm multiple reservations

### Health & Monitoring

- `GET /api/v1/health/` - Health check endpoint

## Environment Variables

| Variable                | Description                                  | Default    |
| ----------------------- | -------------------------------------------- | ---------- |
| `FLASK_ENV`             | Environment (development/testing/production) | production |
| `DATABASE_URL`          | MySQL database connection string             | Required   |
| `REDIS_URL`             | Redis connection string                      | Required   |
| `PRODUCT_SERVICE_URL`   | Product service base URL                     | Optional   |
| `CACHE_DEFAULT_TIMEOUT` | Cache TTL in seconds                         | 300        |
| `HOST`                  | Server host                                  | 0.0.0.0    |
| `PORT`                  | Server port                                  | 5000       |

## Running Tests

### Full Test Suite

```bash
pytest
```

### With Coverage Report

```bash
pytest --cov=app --cov-report=html
```

### Specific Test Categories

```bash
# Unit tests only
pytest tests/test_models.py tests/test_services.py

# Integration tests only
pytest tests/test_controllers.py

# Repository tests
pytest tests/test_repositories.py
```

## Database Schema

### Inventory Items

- Tracks product stock levels and locations
- Supports minimum/maximum stock thresholds
- Automated low stock alerts

### Reservations

- Time-limited inventory reservations
- Supports order-based grouping
- Automatic expiration handling

### Stock Movements

- Complete audit trail of stock changes
- Multiple movement types (inbound, outbound, adjustment, etc.)
- Reference tracking for traceability

## Caching Strategy

- **Inventory Items**: Cached by product ID with TTL
- **Product Details**: External service responses cached
- **Search Results**: Paginated results cached temporarily
- **Health Checks**: Component status cached briefly

## Performance Features

- **Database Indexing**: Optimized indexes for common queries
- **Connection Pooling**: SQLAlchemy connection pooling
- **Async Processing**: Background tasks for non-critical operations
- **Query Optimization**: Efficient joins and aggregations
- **Bulk Operations**: Batch processing for large datasets

## Security Features

- **Input Validation**: Marshmallow schema validation
- **SQL Injection Prevention**: SQLAlchemy ORM protection
- **Error Handling**: Secure error responses
- **Health Checks**: Service availability monitoring

## Monitoring & Observability

### Health Checks

```bash
curl http://localhost:5003/api/v1/health/
```

### Docker Container Logs

```bash
docker-compose logs -f inventory-service
```

### Database Monitoring

```bash
# Access Adminer (if enabled)
docker-compose --profile tools up -d
# Visit http://localhost:8081
```

## Development Workflow

1. **Create feature branch**: `git checkout -b feature/new-feature`
2. **Make changes**: Implement features with tests
3. **Run tests**: `pytest --cov=app`
4. **Check code quality**: `black . && flake8`
5. **Test in Docker**: `docker-compose up --build`
6. **Submit PR**: Create pull request with description

## Production Deployment

### Docker Production Build

```bash
docker build -t inventory-service:latest .
docker run -p 5000:5000 --env-file .env.prod inventory-service:latest
```

### Environment Configuration

Create `.env.prod` with production values:

```
FLASK_ENV=production
DATABASE_URL=mysql+pymysql://user:pass@prod-db:3306/inventory_db
REDIS_URL=redis://prod-redis:6379/0
PRODUCT_SERVICE_URL=https://api.example.com/products/v1
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**

   ```bash
   # Check MySQL service
   docker-compose logs mysql_inventory

   # Verify connection string
   echo $DATABASE_URL
   ```

2. **Redis Connection Failed**

   ```bash
   # Check Redis service
   docker-compose logs redis_inventory

   # Test Redis connectivity
   docker exec -it inventory-service_redis_inventory_1 redis-cli ping
   ```

3. **Migration Issues**

   ```bash
   # Reset database
   docker-compose down -v
   docker-compose up -d mysql_inventory
   # Wait for MySQL to initialize, then start service
   docker-compose up inventory-service
   ```

4. **Performance Issues**

   ```bash
   # Check resource usage
   docker stats

   # Monitor database queries
   # Enable MySQL slow query log
   ```

### Debug Mode

```bash
export FLASK_ENV=development
python run.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Ensure code quality standards
5. Update documentation
6. Submit pull request

## License

This project is part of the AI Outlet e-commerce platform. All rights reserved.

## Support

For issues and questions:

- Create GitHub issues for bugs
- Use discussions for questions
- Check health endpoints for service status
- Review logs for troubleshooting
