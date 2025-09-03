"""
Controllers package initialization - Sets up Flask-RESTX API with all namespaces
"""

from flask import Blueprint
from flask_restx import Api
from app.utils.error_handlers import register_error_handlers
from app.controllers.operational import operational_ns
from app.controllers.inventory import register_inventory_routes
from app.controllers.reservations import register_reservation_routes
import logging

logger = logging.getLogger(__name__)

# Create Blueprint
inventory_bp = Blueprint('inventory', __name__)
api = Api(inventory_bp, version='1.0', title='Inventory Service API',
          description='Microservice for managing product inventory', 
          doc='/docs/')

# Define namespaces
inventory_ns = api.namespace('inventory', description='Inventory operations')
reservations_ns = api.namespace('reservations', description='Reservation operations')

# Add operational namespace (for monitoring endpoints)
api.add_namespace(operational_ns)

# Register routes for each namespace
register_inventory_routes(api, inventory_ns)
register_reservation_routes(api, reservations_ns)


def register_routes(app):
    """Register all routes with the Flask app"""
    app.register_blueprint(inventory_bp, url_prefix='/api/v1')
    register_error_handlers(app)
