"""
Operational/Infrastructure endpoints for inventory service
These endpoints are used by monitoring systems, load balancers, and DevOps tools
"""

from flask import jsonify, current_app
from flask_restx import Resource, Namespace
from datetime import datetime
import time
import os
import psutil
import logging
from app.utils.health_checks import (
    perform_readiness_check, 
    perform_liveness_check, 
    get_system_metrics
)

logger = logging.getLogger(__name__)

# Create namespace for operational endpoints
operational_ns = Namespace('operational', description='Operational endpoints')

@operational_ns.route('/health')
class Health(Resource):
    def get(self):
        """Main health check endpoint"""
        return {
            'status': 'healthy',
            'service': 'inventory-service',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'version': os.environ.get('API_VERSION', '1.0.0'),
            'environment': os.environ.get('FLASK_ENV', 'development'),
        }, 200


@operational_ns.route('/health/ready')
class Readiness(Resource):
    def get(self):
        """Readiness probe - checks if service is ready to handle traffic"""
        try:
            readiness_result = perform_readiness_check()
            
            # Log readiness check results for monitoring
            logger.info('Readiness check performed', extra={
                'status': readiness_result['status'],
                'total_check_time': readiness_result['total_check_time'],
                'checks': {key: check['status'] for key, check in readiness_result['checks'].items()},
            })
            
            status_code = 200 if readiness_result['status'] == 'ready' else 503
            
            return {
                'status': readiness_result['status'],
                'service': 'inventory-service',
                'timestamp': readiness_result['timestamp'],
                'total_check_time': readiness_result['total_check_time'],
                'checks': readiness_result['checks'],
                **({'error': readiness_result['error']} if 'error' in readiness_result else {})
            }, status_code
            
        except Exception as e:
            logger.error('Readiness check failed', extra={'error': str(e)})
            return {
                'status': 'not ready',
                'service': 'inventory-service',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'error': 'Readiness check failed',
                'details': str(e),
            }, 503


@operational_ns.route('/health/live')
class Liveness(Resource):
    def get(self):
        """Liveness probe - checks if service is alive and responsive"""
        try:
            liveness_result = perform_liveness_check()
            
            # Log liveness issues for monitoring
            if liveness_result['status'] != 'alive':
                logger.warning('Liveness check failed', extra={
                    'status': liveness_result['status'],
                    'checks': liveness_result['checks'],
                })
            
            status_code = 200 if liveness_result['status'] == 'alive' else 503
            
            return {
                'status': liveness_result['status'],
                'service': 'inventory-service',
                'timestamp': liveness_result['timestamp'],
                'uptime': liveness_result['uptime'],
                'checks': liveness_result['checks'],
                **({'error': liveness_result['error']} if 'error' in liveness_result else {})
            }, status_code
            
        except Exception as e:
            logger.error('Liveness check failed', extra={'error': str(e)})
            return {
                'status': 'unhealthy',
                'service': 'inventory-service',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'error': 'Liveness check failed',
                'details': str(e),
            }, 503


@operational_ns.route('/metrics')
class Metrics(Resource):
    def get(self):
        """System metrics endpoint for monitoring"""
        try:
            system_metrics = get_system_metrics()
            
            return {
                'service': 'inventory-service',
                **system_metrics,
            }, 200
            
        except Exception as e:
            logger.error('Metrics collection failed', extra={'error': str(e)})
            return {
                'service': 'inventory-service',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'error': 'Metrics collection failed',
                'details': str(e),
            }, 500
