#!/usr/bin/env python3
"""
Inventory Service
A Flask-based microservice for managing product inventory.
"""

import os
import logging
from flask import Flask
from src import create_app, db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    # Get environment
    env = os.environ.get('FLASK_ENV', 'production')
    
    # Create Flask application
    app = create_app(env)
    
    # Initialize database (this is now separate from app creation)
    from src import init_database
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
    
    logger.info(f"Starting Inventory Service on {host}:{port} (env: {env})")
    
    # Run the application
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )


if __name__ == '__main__':
    main()
