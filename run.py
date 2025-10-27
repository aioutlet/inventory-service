#!/usr/bin/env python3
"""
Inventory Service
A Flask-based microservice for managing product inventory.

Industry-standard initialization pattern:
1. Load environment variables
2. Validate configuration (blocking - must pass)
3. Check dependency health (non-blocking - log only)
4. Initialize database
5. Start application
"""

import os
import sys
import logging
import asyncio

# STEP 1: Load environment variables
from src.shared.utils.colored_print import print_step, print_success, print_error, print_info, Colors, colored_print
print_step('Step 1: Loading environment variables...')
from dotenv import load_dotenv
load_dotenv()

# STEP 2: Validate configuration (BLOCKING - must pass)
print_step('Step 2: Validating configuration...')
from src.validators.config_validator import validate_config
validate_config()

# Now we can import Flask and other dependencies
from flask import Flask
from src import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def check_dependencies():
    """Check dependencies synchronously (Flask doesn't have async startup)"""
    from src.shared.utils.dependency_health_checker import check_dependency_health, get_dependencies
    
    print_step('Step 3: Checking dependency health...')
    dependencies = get_dependencies()
    dependency_count = len(dependencies)

    if dependency_count > 0:
        colored_print(f'[DEPS] Found {dependency_count} dependencies to check', Colors.CYAN)
        try:
            # Run async health checks in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(check_dependency_health(dependencies))
            loop.close()
        except Exception as error:
            print_error(f'[DEPS] Dependency health check failed: {str(error)}')
    else:
        print_info('[DEPS] No dependencies configured for health checking')


def main():
    """Main application entry point."""
    # Get environment
    env = os.environ.get('FLASK_ENV', 'production')
    
    # Check dependencies (non-blocking)
    check_dependencies()
    
    # STEP 4: Create Flask application
    print_step('Step 4: Initializing Flask application...')
    app = create_app(env)
    
    # STEP 5: Initialize database tables
    print_step('Step 5: Initializing database...')
    from src.shared.database import db
    with app.app_context():
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))  # Test connection
            db.create_all()
            print_success("Database tables initialized successfully")
        except Exception as e:
            print_error(f"Database initialization failed: {e}")
            if env == 'production':
                raise
            else:
                print_info("Continuing without database in development mode")
    
    # Get host and port from environment
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = env == 'development'
    
    # STEP 6: Start application
    print_step(f'Step 6: Starting Inventory Service on {host}:{port} (env: {env})')
    colored_print(f'\n🚀 Inventory Service starting on http://{host}:{port}\n', Colors.GREEN, bold=True)
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
