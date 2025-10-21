"""
JWT Authentication and Authorization Middleware for Inventory Service
Provides consistent authentication and role-based access control
"""

import os
import jwt
from functools import wraps
from flask import request, g
import logging

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your_jwt_secret_key')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')


class AuthError(Exception):
    """Custom authentication error"""
    def __init__(self, message, status_code=401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def get_token_from_request():
    """Extract JWT token from Authorization header"""
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header:
        return None
    
    if not auth_header.startswith('Bearer '):
        raise AuthError('Authorization header must start with Bearer', 401)
    
    parts = auth_header.split(' ')
    if len(parts) != 2:
        raise AuthError('Invalid Authorization header format', 401)
    
    return parts[1]


def decode_jwt(token):
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError('Token has expired', 401)
    except jwt.InvalidTokenError as e:
        logger.warning(f'Invalid token: {str(e)}')
        raise AuthError('Invalid token', 401)


def require_auth(f):
    """
    Decorator to require valid JWT authentication
    Attaches user info to g.current_user
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            token = get_token_from_request()
            
            if not token:
                logger.warning('Authentication required: No token provided')
                return {
                    'success': False,
                    'error': 'Authentication required',
                    'message': 'No authentication token provided'
                }, 401
            
            # Decode token
            payload = decode_jwt(token)
            
            # Extract user information (compatible with auth-service token structure)
            user_id = payload.get('id') or payload.get('user_id') or payload.get('sub')
            email = payload.get('email')
            roles = payload.get('roles', [])
            
            if not user_id:
                logger.warning('Invalid token: Missing user ID')
                return {
                    'success': False,
                    'error': 'Invalid token',
                    'message': 'Token missing user identifier'
                }, 401
            
            # Store user info in Flask g object
            g.current_user = {
                'id': user_id,
                'email': email,
                'roles': roles
            }
            
            logger.info(f'Authentication successful for user: {user_id}')
            
            return f(*args, **kwargs)
            
        except AuthError as e:
            logger.warning(f'Authentication failed: {e.message}')
            return {
                'success': False,
                'error': 'Authentication failed',
                'message': e.message
            }, e.status_code
        except Exception as e:
            logger.error(f'Authentication error: {str(e)}')
            return {
                'success': False,
                'error': 'Authentication error',
                'message': 'Internal authentication error'
            }, 500
    
    return decorated_function


def require_roles(*required_roles):
    """
    Decorator to require specific roles
    Usage: @require_roles('admin') or @require_roles('admin', 'manager')
    """
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user = g.current_user
            user_roles = user.get('roles', [])
            
            # Check if user has any of the required roles
            has_role = any(role in user_roles for role in required_roles)
            
            if not has_role:
                logger.warning(
                    f'Authorization failed: User {user.get("id")} lacks required roles. '
                    f'Required: {required_roles}, Has: {user_roles}'
                )
                return {
                    'success': False,
                    'error': 'Forbidden',
                    'message': f'Required roles: {", ".join(required_roles)}'
                }, 403
            
            logger.info(
                f'Authorization successful: User {user.get("id")} '
                f'with roles {user_roles} accessing endpoint'
            )
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_admin(f):
    """
    Decorator to require admin role
    Convenience wrapper around require_roles('admin')
    """
    return require_roles('admin')(f)


def optional_auth(f):
    """
    Decorator for optional authentication
    Attaches user info to g.current_user if token is present, otherwise continues
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            token = get_token_from_request()
            
            if token:
                try:
                    payload = decode_jwt(token)
                    user_id = payload.get('id') or payload.get('user_id') or payload.get('sub')
                    email = payload.get('email')
                    roles = payload.get('roles', [])
                    
                    if user_id:
                        g.current_user = {
                            'id': user_id,
                            'email': email,
                            'roles': roles
                        }
                        logger.info(f'Optional auth: User {user_id} authenticated')
                except AuthError:
                    # Invalid token, but we allow the request to continue
                    g.current_user = None
                    logger.info('Optional auth: Invalid token, continuing without authentication')
            else:
                g.current_user = None
                logger.debug('Optional auth: No token provided')
        
        except Exception as e:
            logger.warning(f'Optional auth error: {str(e)}')
            g.current_user = None
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user():
    """
    Get current authenticated user from Flask g object
    Returns None if not authenticated
    """
    return getattr(g, 'current_user', None)
