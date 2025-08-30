from flask import Flask
from flask_cors import CORS
from flask_restx import Api
import redis
import logging
from datetime import datetime

# Initialize Redis client
redis_client = None


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
    from app.middleware.correlation_id import CorrelationIdMiddleware, init_correlation_id_logging
    correlation_middleware = CorrelationIdMiddleware(app)
    init_correlation_id_logging(app)
    
    # Initialize database
    from app.database import init_db
    db = init_db(app)
    
    # CORS setup
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']))
    
    # Initialize Redis
    global redis_client
    try:
        redis_client = redis.Redis(
            host=app.config['REDIS_HOST'],
            port=app.config['REDIS_PORT'],
            db=app.config['REDIS_DB'],
            password=app.config['REDIS_PASSWORD'],
            decode_responses=True,
            socket_connect_timeout=5,  # 5 second timeout
            socket_timeout=5
        )
        redis_client.ping()  # Test connection
        app.logger.info("Redis connection established")
    except Exception as e:
        app.logger.warning(f"Redis connection failed: {e}. Caching will be disabled.")
        redis_client = None
    
    # Configure logging
    if not app.testing:
        logging.basicConfig(
            level=getattr(logging, app.config['LOG_LEVEL']),
            format='%(asctime)s %(levelname)s %(name)s: %(message)s'
        )
    
    # Register blueprints/namespaces (commented out for initial testing)
    try:
        from app.controllers import inventory_bp
        app.register_blueprint(inventory_bp, url_prefix='/api/v1')
        app.logger.info("Controllers registered successfully")
    except Exception as e:
        app.logger.warning(f"Controller registration failed: {e}. Running without API endpoints.")
    
    # Register direct operational endpoints (not under /api/v1)
    try:
        from app.controllers.operational import Health, Readiness, Liveness, Metrics
        
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
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Database tables creation is deferred to init_database() function
    return app


def get_redis():
    """Get Redis client instance"""
    return redis_client


def init_database(app):
    """Initialize database tables - call this explicitly when ready"""
    from app.database import db
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
