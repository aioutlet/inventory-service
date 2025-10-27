"""
Dependency Health Checker
Checks the health of external service dependencies at startup
Logs health status but does not block application startup
"""

import asyncio
import os
from typing import Dict, List

# Import colored print utilities
try:
    from src.shared.utils.colored_print import (
        colored_print, Colors, print_info, print_warning, 
        print_error, print_step, print_success
    )
    HAS_COLORS = True
except ImportError:
    # Fallback if import fails
    HAS_COLORS = False
    print_info = print_warning = print_error = print_step = print_success = print


async def check_database_health() -> dict:
    """
    Check MySQL database health using synchronous connection
    Returns database health status
    """
    try:
        from sqlalchemy import create_engine, text
        
        mysql_host = os.getenv('MYSQL_HOST', 'localhost')
        mysql_port = os.getenv('MYSQL_PORT', '3306')
        mysql_user = os.getenv('MYSQL_USER')
        mysql_password = os.getenv('MYSQL_PASSWORD')
        mysql_database = os.getenv('MYSQL_DATABASE')

        colored_print(f'[DB] Checking database health at {mysql_host}:{mysql_port}', Colors.CYAN)

        # Create MySQL connection URI
        if mysql_user and mysql_password:
            mysql_uri = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
            # Hide password in logs
            safe_uri = mysql_uri.replace(f':{mysql_password}@', ':***@')
            colored_print(f'[DB] Using MySQL URI: {safe_uri}', Colors.BLUE)
        else:
            print_error('[DB] Database credentials not configured')
            return {'service': 'database', 'status': 'unhealthy', 'error': 'Missing credentials'}

        # Create a separate engine for health checking with timeout
        engine = create_engine(
            mysql_uri,
            pool_pre_ping=True,
            connect_args={
                'connect_timeout': 5,
            }
        )

        # Attempt to query the database
        with engine.connect() as connection:
            result = connection.execute(text('SELECT 1'))
            result.fetchone()

        print_success('[DB] Database connection is healthy')
        engine.dispose()
        return {'service': 'database', 'status': 'healthy'}

    except asyncio.TimeoutError:
        print_error('[DB] Database health check timed out')
        return {'service': 'database', 'status': 'timeout', 'error': 'Connection timeout'}
    except Exception as error:
        print_error(f'[DB] Database health check failed: {str(error)}')
        return {'service': 'database', 'status': 'unhealthy', 'error': str(error)}


async def check_service_health(service_name: str, health_url: str, timeout: int = 5) -> dict:
    """
    Check health of an external service via HTTP
    """
    try:
        import aiohttp
        
        colored_print(f'[DEPS] Checking {service_name} health at {health_url}', Colors.CYAN)

        async with aiohttp.ClientSession() as session:
            async with session.get(
                health_url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                headers={'Accept': 'application/json'}
            ) as response:
                if response.status == 200:
                    print_success(f'[DEPS] {service_name} is healthy')
                    return {'service': service_name, 'status': 'healthy', 'url': health_url}
                else:
                    print_warning(f'[DEPS] {service_name} returned status {response.status}')
                    return {
                        'service': service_name,
                        'status': 'unhealthy',
                        'url': health_url,
                        'statusCode': response.status
                    }

    except asyncio.TimeoutError:
        print_warning(f'[DEPS] {service_name} health check timed out after {timeout}s')
        return {'service': service_name, 'status': 'timeout', 'error': 'timeout'}
    except Exception as error:
        print_error(f'[DEPS] {service_name} is not reachable: {str(error)}')
        return {'service': service_name, 'status': 'unreachable', 'error': str(error)}


async def check_dependency_health(dependencies: Dict[str, str], timeout: int = 5) -> List[dict]:
    """
    Check health of service dependencies without blocking startup
    
    Args:
        dependencies: Dict with service names as keys and health URLs as values
        timeout: Timeout for each health check in seconds
    
    Returns:
        List of health check results
    """
    print_step('[DEPS] 🔍 Checking dependency health...')

    # Check database health first
    db_health = await check_database_health()
    health_checks = [db_health]

    # Add external service health checks
    for service_name, health_url in dependencies.items():
        result = await check_service_health(service_name, health_url, timeout)
        health_checks.append(result)

    # Summary logging
    healthy_services = sum(1 for check in health_checks if check.get('status') == 'healthy')
    total_services = len(health_checks)

    if healthy_services == total_services:
        print_success(f'[DEPS] All {total_services} dependencies are healthy')
    else:
        print_warning(f'[DEPS] {healthy_services}/{total_services} dependencies are healthy')

    return health_checks


def get_dependencies() -> Dict[str, str]:
    """
    Get dependency URLs from environment variables
    Uses standardized _HEALTH_URL variables for complete health endpoint URLs
    
    Returns:
        Dict with service names as keys and health URLs as values
    """
    dependencies = {}

    # Add message broker if configured (primary dependency for inventory-service)
    message_broker_health_url = os.getenv('MESSAGE_BROKER_HEALTH_URL')
    if message_broker_health_url:
        dependencies['message-broker'] = message_broker_health_url

    # Add product service if configured
    product_service_health_url = os.getenv('PRODUCT_SERVICE_HEALTH_URL')
    if product_service_health_url:
        dependencies['product-service'] = product_service_health_url

    return dependencies
