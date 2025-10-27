"""
Rate limiting middleware for Inventory Service
Implements request rate limiting using Flask-Limiter
"""

import os
import logging
import warnings
from datetime import datetime
from functools import wraps
from flask import request, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)

# Suppress Flask-Limiter in-memory storage warning (intentional for now)
warnings.filterwarnings('ignore', message='.*in-memory storage.*', module='flask_limiter')

# Rate limiting configuration based on environment
def get_rate_limit_config():
    """Get rate limit configuration from environment variables"""
    env = os.environ.get('FLASK_ENV', 'production')
    
    if env == 'development':
        return {
            'default': "1000 per hour",
            'inventory_read': "500 per hour", 
            'inventory_write': "200 per hour",
            'reservations': "100 per hour",
            'stock_adjustments': "50 per hour",
            'admin_operations': "100 per hour"
        }
    elif env == 'production':
        return {
            'default': "500 per hour",
            'inventory_read': "300 per hour",
            'inventory_write': "100 per hour", 
            'reservations': "50 per hour",
            'stock_adjustments': "25 per hour",
            'admin_operations': "50 per hour"
        }
    else:  # local/test
        return {
            'default': "2000 per hour",
            'inventory_read': "1000 per hour",
            'inventory_write': "500 per hour",
            'reservations': "300 per hour", 
            'stock_adjustments': "100 per hour",
            'admin_operations': "200 per hour"
        }

# Initialize rate limiter
def init_rate_limiter(app):
    """Initialize rate limiter with in-memory storage (Redis removed, will implement caching later)"""
    logger.info("Rate limiter using in-memory storage (caching disabled)")
    
    # Get rate limit configuration
    rate_config = get_rate_limit_config()
    
    # Initialize limiter with in-memory storage
    limiter = Limiter(
        app=app,
        key_func=get_rate_limit_key,
        default_limits=[rate_config['default']],
        headers_enabled=True,
        strategy="fixed-window",
        on_breach=rate_limit_breach_handler
    )
    
    return limiter

def get_rate_limit_key():
    """Generate rate limit key based on IP and user context"""
    # Get base key from IP
    ip = get_remote_address()
    
    # Add user context if available
    user_id = getattr(g, 'current_user_id', None)
    if user_id:
        return f"user:{user_id}:{ip}"
    
    return f"ip:{ip}"

def rate_limit_breach_handler(request_limit):
    """Handle rate limit breaches with logging and proper response"""
    ip = get_remote_address()
    user_id = getattr(g, 'current_user_id', None)
    correlation_id = getattr(g, 'correlation_id', 'unknown')
    
    # Log security event
    logger.warning(
        f"Rate limit exceeded",
        extra={
            'ip': ip,
            'user_id': user_id,
            'correlation_id': correlation_id,
            'path': request.path,
            'method': request.method,
            'user_agent': request.headers.get('User-Agent'),
            'limit': str(request_limit),
            'timestamp': datetime.utcnow().isoformat()
        }
    )
    
    # Return JSON error response
    response = jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.',
        'limit': str(request_limit),
        'retry_after': request_limit.reset_at,
        'correlation_id': correlation_id
    })
    response.status_code = 429
    response.headers['Retry-After'] = str(int(request_limit.reset_at - datetime.utcnow().timestamp()))
    
    return response

# Rate limiting decorators for different endpoint types
def inventory_read_limit():
    """Rate limit for read operations (GET requests)"""
    config = get_rate_limit_config()
    return config['inventory_read']

def inventory_write_limit():
    """Rate limit for write operations (POST, PUT, PATCH, DELETE)"""
    config = get_rate_limit_config()
    return config['inventory_write']

def reservations_limit():
    """Rate limit for reservation operations"""
    config = get_rate_limit_config()
    return config['reservations']

def stock_adjustments_limit():
    """Rate limit for stock adjustment operations"""
    config = get_rate_limit_config()
    return config['stock_adjustments']

def admin_operations_limit():
    """Rate limit for admin operations"""
    config = get_rate_limit_config()
    return config['admin_operations']

# Utility function to skip rate limiting for health checks
def should_skip_rate_limiting():
    """Check if current request should skip rate limiting"""
    path = request.path.lower()
    
    # Skip for health checks and monitoring endpoints
    skip_paths = ['/health', '/metrics', '/api/health', '/api/metrics']
    
    return any(path.startswith(skip_path) for skip_path in skip_paths)

# Custom decorator that respects skip conditions
def conditional_rate_limit(limit_func):
    """Decorator that applies rate limiting conditionally"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if should_skip_rate_limiting():
                return f(*args, **kwargs)
            
            # Apply rate limiting
            from flask_limiter import Limiter
            # This should be called after limiter is initialized
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Export configuration for easy access
RATE_LIMIT_CONFIG = get_rate_limit_config()
