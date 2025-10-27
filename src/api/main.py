#!/usr/bin/env python3
"""
Inventory Service API
Flask-based REST API for managing product inventory.
"""

import os
import logging
from flask import Flask
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_app(config_name='default'):
    """Application factory pattern for API"""
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
    
    # Register blueprints/controllers
    try:
        from src.api.controllers import inventory_bp
        app.register_blueprint(inventory_bp, url_prefix='/api/v1')
        app.logger.info("Controllers registered successfully")
    except Exception as e:
        app.logger.warning(f"Controller registration failed: {e}. Running without API endpoints.")
    
    # Register operational endpoints
    try:
        from src.api.controllers.operational import Health, Readiness, Liveness, Metrics
        
        health_resource = Health()
        readiness_resource = Readiness()
        liveness_resource = Liveness()
        metrics_resource = Metrics()
        
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
    
    return app


def init_database(app):
    """Initialize database tables"""
    from src.shared.database import db
    with app.app_context():
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db.create_all()
            app.logger.info("Database tables created successfully")
            return True
        except Exception as e:
            app.logger.error(f"Failed to create database tables: {e}")
            if app.config.get('FLASK_ENV') == 'production':
                raise
            else:
                app.logger.warning("Continuing without database connection in development mode")
                return False


def main():
    """Main application entry point for API"""
    env = os.environ.get('FLASK_ENV', 'production')
    
    # Create Flask application
    app = create_app(env)
    
    # Initialize database
    try:
        init_database(app)
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        if env == 'production':
            raise
        else:
            logger.warning("Continuing without database in development mode")
    
    # Get host and port from environment
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = env == 'development'
    
    logger.info(f"Starting Inventory API Service on {host}:{port} (env: {env})")
    
    # Run the application
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )


if __name__ == '__main__':
    main()
