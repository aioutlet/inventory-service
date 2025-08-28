"""
Health Controller - Basic health check operations (separate from operational monitoring)
"""

from flask_restx import Resource
from marshmallow import ValidationError
from app.services import InventoryService
from app.utils.validators import HealthCheckResponseSchema
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Initialize schemas
health_response_schema = HealthCheckResponseSchema()


def register_health_routes(api, namespace):
    """Register health check routes"""

    @namespace.route('/')
    class HealthCheck(Resource):
        @api.doc('health_check')
        def get(self):
            """Basic health check endpoint for service dependencies"""
            try:
                inventory_service = InventoryService()
                health_data = inventory_service.health_check()
                
                result = health_response_schema.dump(health_data)
                status_code = 200 if health_data['status'] == 'healthy' else 503
                
                return result, status_code
                
            except Exception as e:
                logger.error(f"Error during health check: {e}")
                return {
                    'status': 'unhealthy',
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': str(e)
                }, 503
