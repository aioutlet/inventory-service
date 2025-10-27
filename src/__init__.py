import os
import sys
import logging
from flask import Flask
from flask_cors import CORS
from src.shared.models import db


def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    from config import config
    app.config.from_object(config[config_name])
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize correlation ID middleware
    from src.api.middlewares.correlation_id import CorrelationIdMiddleware, init_correlation_id_logging
    correlation_middleware = CorrelationIdMiddleware(app)
    init_correlation_id_logging(app)
    
    # Initialize database
    from src.shared.database import init_db
    db = init_db(app)
    
    # CORS setup
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']))
    
    # Configure logging
    if not app.testing:
        logging.basicConfig(
            level=getattr(logging, app.config['LOG_LEVEL']),
            format='%(asctime)s %(levelname)s %(name)s: %(message)s'
        )
    
    # Register blueprints/namespaces (commented out for initial testing)
    try:
        from src.api.controllers import inventory_bp
        app.register_blueprint(inventory_bp, url_prefix='/api/v1')
        app.logger.info("Controllers registered successfully")
    except Exception as e:
        app.logger.warning(f"Controller registration failed: {e}. Running without API endpoints.")
    
    # Register direct operational endpoints (not under /api/v1)
    try:
        from src.api.controllers.operational import Health, Readiness, Liveness, Metrics
        
        # Create Flask-RESTX resources for direct access
        health_resource = Health()
        readiness_resource = Readiness()
        liveness_resource = Liveness()
        metrics_resource = Metrics()
        
        # Add direct routes for monitoring/health checks
        app.add_url_rule('/health', 'health', health_resource.get, methods=['GET'])
        app.add_url_rule('/health/ready', 'readiness', readiness_resource.get, methods=['GET'])
        app.add_url_rule('/health/live', 'liveness', liveness_resource.get, methods=['GET'])
        app.add_url_rule('/metrics', 'metrics', metrics_resource.get, methods=['GET'])
        app.logger.info("Operational endpoints registered successfully")
    except Exception as e:
        app.logger.warning(f"Operational endpoints registration failed: {e}. Running without health endpoints.")
    
    # Register error handlers
    from src.shared.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Database tables creation is deferred to init_database() function
    return app


def init_db(app):
    """Initialize database tables - call this explicitly when ready"""
    from src.shared.database import db
    with app.app_context():
        try:
            # Only create tables if database connection is successful
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))  # Test connection
            db.create_all()
            app.logger.info("Database tables created successfully")
            return True
        except Exception as e:
            app.logger.error(f"Failed to create database tables: {e}")
            if app.config.get('FLASK_ENV') == 'production':
                # In production, fail fast
                raise
            else:
                # In development, continue without database connection for now
                app.logger.warning("Continuing without database connection in development mode")
                return False
