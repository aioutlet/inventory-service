"""
Simple Flask Authentication Middleware
Pure Python/Flask implementation for JWT authentication
"""

import jwt
import requests
from functools import wraps
from flask import current_app, request, jsonify, g


def get_token_from_request():
    """Extract JWT token from Authorization header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
        
    # Expected format: "Bearer <token>"
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
        
    return parts[1]


def verify_jwt_token(token):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET'],
            algorithms=[current_app.config.get('JWT_ALGORITHM', 'HS256')]
        )
        return payload
    except jwt.ExpiredSignatureError:
        current_app.logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        current_app.logger.warning(f"Invalid JWT token: {e}")
        return None


def validate_with_user_service(token):
    """Validate token with user service and get user data"""
    try:
        user_service_url = current_app.config.get('USER_SERVICE_URL')
        if not user_service_url:
            current_app.logger.warning("USER_SERVICE_URL not configured")
            return None
            
        headers = {'Authorization': f'Bearer {token}'}
        timeout = current_app.config.get('USER_SERVICE_TIMEOUT', 5)
        
        response = requests.get(
            f"{user_service_url}/api/v1/auth/profile",
            headers=headers,
            timeout=timeout
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            current_app.logger.warning(f"User service validation failed: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"User service request failed: {e}")
        return None


def require_auth(f):
    """
    Decorator to require authentication
    Sets g.current_user, g.user_id, g.user_roles for authenticated requests
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip authentication in testing environment
        if current_app.config.get('TESTING'):
            g.current_user = {'id': 'test-user', 'username': 'testuser', 'roles': ['admin']}
            g.user_id = 'test-user'
            g.user_roles = ['admin']
            return f(*args, **kwargs)
            
        token = get_token_from_request()
        if not token:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please provide a valid JWT token'
            }), 401
        
        # Verify JWT token
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({
                'error': 'Invalid token',
                'message': 'Please provide a valid JWT token'
            }), 401
        
        # Validate with user service
        user_data = validate_with_user_service(token)
        if not user_data:
            return jsonify({
                'error': 'Authentication failed',
                'message': 'Unable to validate user credentials'
            }), 401
        
        # Set user context
        g.current_user = user_data
        g.user_id = user_data.get('id')
        g.user_roles = user_data.get('roles', [])
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_admin(f):
    """
    Decorator to require admin role
    Automatically includes authentication check
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip authentication in testing environment
        if current_app.config.get('TESTING'):
            g.current_user = {'id': 'test-user', 'username': 'testuser', 'roles': ['admin']}
            g.user_id = 'test-user'
            g.user_roles = ['admin']
            return f(*args, **kwargs)
            
        # First check authentication
        token = get_token_from_request()
        if not token:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please provide a valid JWT token'
            }), 401
        
        # Verify JWT token
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({
                'error': 'Invalid token',
                'message': 'Please provide a valid JWT token'
            }), 401
        
        # Validate with user service
        user_data = validate_with_user_service(token)
        if not user_data:
            return jsonify({
                'error': 'Authentication failed',
                'message': 'Unable to validate user credentials'
            }), 401
        
        # Set user context
        g.current_user = user_data
        g.user_id = user_data.get('id')
        g.user_roles = user_data.get('roles', [])
        
        # Check admin role
        if 'admin' not in g.user_roles:
            return jsonify({
                'error': 'Insufficient permissions',
                'message': 'Admin access required'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_roles(*required_roles):
    """
    Decorator factory to require specific roles
    Usage: @require_roles('admin', 'manager')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # First check authentication
            token = get_token_from_request()
            if not token:
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please provide a valid JWT token'
                }), 401
            
            # Verify JWT token
            payload = verify_jwt_token(token)
            if not payload:
                return jsonify({
                    'error': 'Invalid token',
                    'message': 'Please provide a valid JWT token'
                }), 401
            
            # Validate with user service
            user_data = validate_with_user_service(token)
            if not user_data:
                return jsonify({
                    'error': 'Authentication failed',
                    'message': 'Unable to validate user credentials'
                }), 401
            
            # Set user context
            g.current_user = user_data
            g.user_id = user_data.get('id')
            g.user_roles = user_data.get('roles', [])
            
            # Check required roles
            user_roles = g.user_roles or []
            if not any(role in user_roles for role in required_roles):
                return jsonify({
                    'error': 'Insufficient permissions',
                    'message': f'Required roles: {", ".join(required_roles)}'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


# Utility functions
def get_current_user():
    """Get current authenticated user from request context"""
    return getattr(g, 'current_user', None)


def get_user_id():
    """Get current user ID from request context"""
    return getattr(g, 'user_id', None)


def get_user_roles():
    """Get current user roles from request context"""
    return getattr(g, 'user_roles', [])


def is_admin():
    """Check if current user has admin role"""
    return 'admin' in get_user_roles()


def is_authenticated():
    """Check if user is authenticated in current request"""
    return hasattr(g, 'current_user') and g.current_user is not None
