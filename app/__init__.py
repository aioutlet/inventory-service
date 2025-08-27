from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_restx import Api
import redis
import logging
from datetime import datetime

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
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
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']))
    
    # Initialize Redis
    global redis_client
    try:
        redis_client = redis.Redis(
            host=app.config['REDIS_HOST'],
            port=app.config['REDIS_PORT'],
            db=app.config['REDIS_DB'],
            password=app.config['REDIS_PASSWORD'],
            decode_responses=True
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
    
    # Register blueprints/namespaces
    from app.controllers import inventory_bp
    app.register_blueprint(inventory_bp, url_prefix='/api/v1')
    
    # Register error handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Create tables
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Failed to create database tables: {e}")
            if not app.testing:
                raise
    
    return app


def get_redis():
    """Get Redis client instance"""
    return redis_client
