"""
W3C Trace Context middleware for Flask application
Implements W3C Trace Context specification for distributed tracing
"""
import uuid
import re
import logging
from typing import Optional, Tuple
from flask import Request, Response, g, request, current_app

# W3C traceparent header format: 00-{trace-id}-{parent-id}-{trace-flags}
TRACEPARENT_PATTERN = re.compile(
    r'^00-([0-9a-f]{32})-([0-9a-f]{16})-[0-9a-f]{2}$'
)

logger = logging.getLogger(__name__)


class TraceContextMiddleware:
    """
    Flask middleware for W3C Trace Context propagation
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
        """Extract or generate trace context before request processing"""
        # Try to extract trace context from traceparent header
        traceparent = request.headers.get('traceparent')
        
        if traceparent:
            trace_context = self.extract_trace_context(traceparent)
            if trace_context:
                trace_id, span_id = trace_context
                logger.debug(f"Extracted trace context from header: {trace_id}")
            else:
                # Invalid traceparent, generate new
                trace_id, span_id = self.generate_trace_context()
                logger.warning(f"Invalid traceparent header, generated new: {trace_id}")
        else:
            # No traceparent header, generate new
            trace_id, span_id = self.generate_trace_context()
            logger.debug(f"Generated new trace context: {trace_id}")
        
        # Store in Flask's g object for request-scoped access
        g.trace_id = trace_id
        g.span_id = span_id
        
        # Log request with trace ID
        current_app.logger.info(
            f"[{trace_id[:16]}] {request.method} {request.path} - Processing request"
        )
    
    def after_request(self, response: Response) -> Response:
        """Add trace context to response headers"""
        trace_id = getattr(g, 'trace_id', 'unknown')
        span_id = getattr(g, 'span_id', '0' * 16)
        
        # Add W3C traceparent header to response
        traceparent = f"00-{trace_id}-{span_id}-01"
        response.headers['traceparent'] = traceparent
        
        # Also add X-Trace-ID for backward compatibility
        response.headers['X-Trace-ID'] = trace_id
        
        # Log response with trace ID
        current_app.logger.info(
            f"[{trace_id[:16]}] {request.method} {request.path} - "
            f"Response: {response.status_code}"
        )
        
        return response
    
    @staticmethod
    def extract_trace_context(traceparent: str) -> Optional[Tuple[str, str]]:
        """
        Extract trace context from W3C traceparent header.
        
        Format: 00-{trace-id}-{parent-id}-{trace-flags}
        Example: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
        
        Args:
            traceparent: W3C traceparent header value
            
        Returns:
            Tuple of (trace_id, span_id) or None if invalid
        """
        if not traceparent:
            return None
        
        match = TRACEPARENT_PATTERN.match(traceparent.strip())
        if not match:
            return None
        
        trace_id = match.group(1)
        span_id = match.group(2)
        
        # Validate trace-id and span-id are not all zeros
        if trace_id == '0' * 32 or span_id == '0' * 16:
            return None
        
        return trace_id, span_id
    
    @staticmethod
    def generate_trace_context() -> Tuple[str, str]:
        """
        Generate new trace context.
        
        Returns:
            Tuple of (trace_id, span_id) as hex strings
        """
        # Generate 128-bit trace ID (32 hex chars)
        trace_id = uuid.uuid4().hex + uuid.uuid4().hex[:16]
        
        # Generate 64-bit span ID (16 hex chars)
        span_id = uuid.uuid4().hex[:16]
        
        return trace_id, span_id


def get_trace_id() -> Optional[str]:
    """
    Get current trace ID from Flask g object.
    
    Returns:
        Current trace ID or None
    """
    return getattr(g, 'trace_id', None)


def get_span_id() -> Optional[str]:
    """
    Get current span ID from Flask g object.
    
    Returns:
        Current span ID or None
    """
    return getattr(g, 'span_id', None)


def set_trace_context(trace_id: str, span_id: str) -> None:
    """
    Set trace context in Flask g object.
    
    Args:
        trace_id: Trace ID as hex string
        span_id: Span ID as hex string
    """
    g.trace_id = trace_id
    g.span_id = span_id


def create_traceparent_header() -> str:
    """
    Create W3C traceparent header for current request.
    
    Returns:
        traceparent header value
    """
    trace_id = get_trace_id() or '0' * 32
    span_id = get_span_id() or '0' * 16
    
    return f"00-{trace_id}-{span_id}-01"
