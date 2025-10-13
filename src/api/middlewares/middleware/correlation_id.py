"""
Correlation ID middleware for Flask application
Provides distributed tracing capabilities across microservices
"""
import uuid
import logging
from functools import wraps
from typing import Optional, Dict, Any
from contextvars import ContextVar
from flask import Request, Response, g, request, current_app

# Context variable to store correlation ID for the current request
correlation_id_context: ContextVar[str] = ContextVar('correlation_id', default='')

class CorrelationIdMiddleware:
    """
    Flask middleware for handling correlation IDs
    """
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Extract or generate correlation ID before request processing"""
        # Get correlation ID from header or generate new one
        correlation_id = (
            request.headers.get('X-Correlation-ID') or
            request.headers.get('x-correlation-id') or
            str(uuid.uuid4())
        )
        
        # Store in Flask's g object for request-scoped access
        g.correlation_id = correlation_id
        
        # Set in context variable for use in async operations
        correlation_id_context.set(correlation_id)
        
        # Log request with correlation ID
        current_app.logger.info(
            f"[{correlation_id}] {request.method} {request.path} - Processing request"
        )
    
    def after_request(self, response: Response) -> Response:
        """Add correlation ID to response headers"""
        correlation_id = getattr(g, 'correlation_id', 'unknown')
        response.headers['X-Correlation-ID'] = correlation_id
        
        # Log response with correlation ID
        current_app.logger.info(
            f"[{correlation_id}] {request.method} {request.path} - "
            f"Response: {response.status_code}"
        )
        
        return response


class CorrelationIdHelper:
    """
    Utility functions for correlation ID handling
    """
    
    @staticmethod
    def get_correlation_id() -> str:
        """Get current correlation ID from Flask g object or context"""
        # Try Flask g first (for request context)
        if hasattr(g, 'correlation_id'):
            return g.correlation_id
        
        # Fall back to context variable (for async operations)
        return correlation_id_context.get('unknown')
    
    @staticmethod
    def create_headers(additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Create headers with correlation ID for outgoing HTTP requests"""
        correlation_id = CorrelationIdHelper.get_correlation_id()
        
        headers = {
            'X-Correlation-ID': correlation_id,
            'Content-Type': 'application/json',
        }
        
        if additional_headers:
            headers.update(additional_headers)
        
        return headers
    
    @staticmethod
    def log_with_correlation(
        logger: logging.Logger,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log message with correlation ID"""
        correlation_id = CorrelationIdHelper.get_correlation_id()
        
        # Prepare log data
        log_extra = {
            'correlation_id': correlation_id,
            **(extra or {})
        }
        
        # Create formatted message
        formatted_message = f"[{correlation_id}] {message}"
        
        # Log with appropriate level
        getattr(logger, level.lower())(formatted_message, extra=log_extra)
    
    @staticmethod
    def with_correlation_context(func):
        """Decorator to ensure correlation ID context in async operations"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Ensure correlation ID is set in context
            if not correlation_id_context.get(None):
                correlation_id = CorrelationIdHelper.get_correlation_id()
                correlation_id_context.set(correlation_id)
            return func(*args, **kwargs)
        return wrapper


def init_correlation_id_logging(app):
    """
    Initialize correlation ID logging configuration
    """
    
    class CorrelationIdFormatter(logging.Formatter):
        """Custom formatter that includes correlation ID in log messages"""
        
        def format(self, record):
            # Add correlation ID to log record if available
            if hasattr(g, 'correlation_id'):
                record.correlation_id = g.correlation_id
            else:
                record.correlation_id = correlation_id_context.get('unknown')
            
            return super().format(record)
    
    # Configure logging format with correlation ID
    formatter = CorrelationIdFormatter(
        '[%(correlation_id)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    # Apply formatter to all handlers
    for handler in app.logger.handlers:
        handler.setFormatter(formatter)


# Convenience functions for common usage patterns
def get_correlation_id() -> str:
    """Get current correlation ID - convenience function"""
    return CorrelationIdHelper.get_correlation_id()

def create_request_headers(additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Create headers for outgoing requests - convenience function"""
    return CorrelationIdHelper.create_headers(additional_headers)

def log_info(message: str, **kwargs):
    """Log info message with correlation ID - convenience function"""
    CorrelationIdHelper.log_with_correlation(
        current_app.logger, 'info', message, kwargs
    )

def log_error(message: str, **kwargs):
    """Log error message with correlation ID - convenience function"""
    CorrelationIdHelper.log_with_correlation(
        current_app.logger, 'error', message, kwargs
    )

def log_warning(message: str, **kwargs):
    """Log warning message with correlation ID - convenience function"""
    CorrelationIdHelper.log_with_correlation(
        current_app.logger, 'warning', message, kwargs
    )
