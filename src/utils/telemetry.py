"""
OpenTelemetry initialization and instrumentation for Inventory Service
Provides distributed tracing with W3C Trace Context support
"""
import os
import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

logger = logging.getLogger(__name__)


def init_telemetry(app) -> Optional[TracerProvider]:
    """
    Initialize OpenTelemetry tracing for Flask application.
    
    Dapr automatically configures tracing via .dapr/config.yaml
    This provides additional application-level instrumentation.
    
    Args:
        app: Flask application instance
        
    Returns:
        TracerProvider instance if tracing is enabled, None otherwise
    """
    # Check if tracing is enabled (optional, defaults to true when running with Dapr)
    enable_tracing = os.environ.get('ENABLE_TRACING', 'true').lower() == 'true'
    
    if not enable_tracing:
        logger.info("OpenTelemetry tracing is disabled")
        return None
    
    try:
        # Get service information
        service_name = os.environ.get('NAME', 'inventory-service')
        service_version = os.environ.get('VERSION', '1.0.0')
        environment = os.environ.get('FLASK_ENV', 'development')
        
        # Create resource with service information
        resource = Resource.create({
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            "service.environment": environment,
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Get OTLP endpoint (default to standard OTLP HTTP endpoint)
        # Dapr's config.yaml should point to the same collector
        # Note: Don't include /v1/traces - the exporter adds it automatically
        otlp_endpoint = os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318')
        
        if otlp_endpoint:
            # Configure OTLP exporter
            otlp_exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint,
                timeout=30
            )
            
            # Add span processor
            span_processor = BatchSpanProcessor(otlp_exporter)
            provider.add_span_processor(span_processor)
            
            logger.info(
                f"OpenTelemetry OTLP exporter configured",
                extra={
                    "endpoint": otlp_endpoint,
                    "service": service_name
                }
            )
        else:
            logger.warning("OTEL_EXPORTER_OTLP_ENDPOINT not set, spans will not be exported")
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        # Initialize logging instrumentation for trace context in logs
        LoggingInstrumentor().instrument(set_logging_format=False)
        
        logger.info(
            f"OpenTelemetry tracing initialized for {service_name}",
            extra={
                "service": service_name,
                "version": service_version,
                "environment": environment
            }
        )
        
        return provider
        
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}", exc_info=True)
        return None


def instrument_app(app):
    """
    Instrument Flask application and dependencies with OpenTelemetry.
    
    Args:
        app: Flask application instance
    """
    # Check if tracing is enabled
    enable_tracing = os.environ.get('ENABLE_TRACING', 'true').lower() == 'true'
    
    if not enable_tracing:
        return
    
    try:
        # Instrument Flask application
        FlaskInstrumentor().instrument_app(app)
        logger.info("Flask instrumentation enabled")
        
        # Instrument requests library for outgoing HTTP calls
        RequestsInstrumentor().instrument()
        logger.info("Requests instrumentation enabled")
        
        # Instrument SQLAlchemy for database operations
        # Note: Must be called after db.init_app(app)
        from src.database import db
        with app.app_context():
            if db and hasattr(db, 'engine') and db.engine:
                SQLAlchemyInstrumentor().instrument(
                    engine=db.engine,
                    enable_commenter=True,
                    commenter_options={"db_framework": "flask-sqlalchemy"}
                )
                logger.info("SQLAlchemy instrumentation enabled")
        
        logger.info("OpenTelemetry instrumentation completed")
        
    except Exception as e:
        logger.error(f"Failed to instrument application: {e}", exc_info=True)


def get_current_span():
    """
    Get the current active span.
    
    Returns:
        Current span or None if no active span
    """
    return trace.get_current_span()


def get_trace_context():
    """
    Get current trace context (trace_id and span_id).
    
    Returns:
        Dictionary with trace_id and span_id
    """
    span = get_current_span()
    if span and span.get_span_context().is_valid:
        context = span.get_span_context()
        return {
            "trace_id": format(context.trace_id, "032x"),
            "span_id": format(context.span_id, "016x"),
        }
    return {"trace_id": None, "span_id": None}
