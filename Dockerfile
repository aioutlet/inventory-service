# =============================================================================
# Multi-stage Dockerfile for Python Inventory Service
# =============================================================================

# -----------------------------------------------------------------------------
# Base stage - Common setup for all stages
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# -----------------------------------------------------------------------------
# Dependencies stage - Install Python dependencies
# -----------------------------------------------------------------------------
FROM base AS dependencies

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Development stage - For local development
# -----------------------------------------------------------------------------
FROM dependencies AS development

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=run.py
ENV FLASK_ENV=development

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/api/v1/health/ || exit 1

# Expose port
EXPOSE 5000

# Run development server
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--debug"]

# -----------------------------------------------------------------------------
# Production stage - Optimized for production deployment
# -----------------------------------------------------------------------------
FROM dependencies AS production

# Copy application code
COPY --chown=appuser:appuser . .

# Remove unnecessary files for production
RUN rm -rf tests/ .git/ .github/ .vscode/ *.md .env.* docker-compose* .ops/

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/v1/health/ || exit 1

# Expose port
EXPOSE 5000

# Run the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--log-level", "info", "run:main().app"]

# Labels for better image management
LABEL maintainer="AIOutlet Team"
LABEL service="inventory-service"
LABEL version="1.0.0"
