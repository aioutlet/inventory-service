from flask import Blueprint, request, jsonify, current_app
from flask_restx import Api, Resource, fields
from marshmallow import ValidationError
from app.services import InventoryService
from app.utils.validators import (
    InventoryItemRequestSchema, InventoryItemResponseSchema,
    StockAdjustmentRequestSchema, StockMovementResponseSchema,
    InventorySearchSchema, BulkOperationRequestSchema,
    ReservationRequestSchema, ReservationResponseSchema,
    ReservationConfirmRequestSchema, HealthCheckResponseSchema
)
from app.utils.error_handlers import register_error_handlers
from datetime import datetime
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
health_ns = api.namespace('health', description='Health check operations')

# Initialize schemas
inventory_request_schema = InventoryItemRequestSchema()
inventory_response_schema = InventoryItemResponseSchema()
stock_adjustment_schema = StockAdjustmentRequestSchema()
stock_movement_schema = StockMovementResponseSchema()
search_schema = InventorySearchSchema()
bulk_operation_schema = BulkOperationRequestSchema()
reservation_request_schema = ReservationRequestSchema()
reservation_response_schema = ReservationResponseSchema()
reservation_confirm_schema = ReservationConfirmRequestSchema()
health_response_schema = HealthCheckResponseSchema()

# API Models for documentation
inventory_item_model = api.model('InventoryItem', {
    'id': fields.Integer(description='Inventory item ID'),
    'product_id': fields.String(required=True, description='Product identifier'),
    'quantity': fields.Integer(required=True, description='Total quantity'),
    'reserved_quantity': fields.Integer(description='Reserved quantity'),
    'available_quantity': fields.Integer(description='Available quantity'),
    'minimum_stock_level': fields.Integer(description='Minimum stock level'),
    'maximum_stock_level': fields.Integer(description='Maximum stock level'),
    'location': fields.String(description='Storage location'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp')
})

stock_adjustment_model = api.model('StockAdjustment', {
    'product_id': fields.String(required=True, description='Product identifier'),
    'quantity': fields.Integer(required=True, description='Adjustment quantity'),
    'movement_type': fields.String(required=True, description='Movement type'),
    'reference_id': fields.String(description='Reference identifier'),
    'notes': fields.String(description='Additional notes')
})

reservation_model = api.model('Reservation', {
    'id': fields.Integer(description='Reservation ID'),
    'product_id': fields.String(required=True, description='Product identifier'),
    'quantity': fields.Integer(required=True, description='Reserved quantity'),
    'customer_id': fields.String(required=True, description='Customer identifier'),
    'order_id': fields.String(required=True, description='Order identifier'),
    'status': fields.String(description='Reservation status'),
    'expires_at': fields.DateTime(description='Expiration timestamp'),
    'notes': fields.String(description='Additional notes'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp')
})


@inventory_ns.route('/')
class InventoryList(Resource):
    @api.doc('list_inventory')
    @api.marshal_list_with(inventory_item_model)
    def get(self):
        """Get all inventory items with optional filtering"""
        try:
            # Validate query parameters
            search_params = search_schema.load(request.args.to_dict())
            
            inventory_service = InventoryService()
            items, total = inventory_service.search_inventory(**search_params)
            
            # Serialize response
            result = inventory_response_schema.dump(items, many=True)
            
            return {
                'items': result,
                'pagination': {
                    'page': search_params.get('page', 1),
                    'per_page': search_params.get('per_page', 20),
                    'total': total,
                    'pages': (total + search_params.get('per_page', 20) - 1) // search_params.get('per_page', 20)
                }
            }, 200
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except Exception as e:
            logger.error(f"Error listing inventory: {e}")
            return {'error': 'Internal server error'}, 500

    @api.doc('create_inventory')
    @api.expect(inventory_item_model)
    def post(self):
        """Create new inventory item"""
        try:
            # Validate request data
            data = inventory_request_schema.load(request.json)
            
            inventory_service = InventoryService()
            item = inventory_service.create_inventory_item(**data)
            
            # Serialize response
            result = inventory_response_schema.dump(item)
            return result, 201
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except ValueError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            logger.error(f"Error creating inventory item: {e}")
            return {'error': 'Internal server error'}, 500


@inventory_ns.route('/<string:product_id>')
class InventoryItem(Resource):
    @api.doc('get_inventory')
    def get(self, product_id):
        """Get inventory item by product ID"""
        try:
            inventory_service = InventoryService()
            item = inventory_service.get_inventory_by_product_id(product_id)
            
            if not item:
                return {'error': 'Inventory item not found'}, 404
            
            result = inventory_response_schema.dump(item)
            return result, 200
            
        except Exception as e:
            logger.error(f"Error getting inventory for product {product_id}: {e}")
            return {'error': 'Internal server error'}, 500

    @api.doc('update_inventory')
    @api.expect(inventory_item_model)
    @api.marshal_with(inventory_item_model)
    def put(self, product_id):
        """Update inventory item"""
        try:
            # Validate request data
            data = inventory_request_schema.load(request.json)
            
            inventory_service = InventoryService()
            item = inventory_service.update_inventory_item(product_id, **data)
            
            if not item:
                return {'error': 'Inventory item not found'}, 404
            
            result = inventory_response_schema.dump(item)
            return result, 200
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except ValueError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            logger.error(f"Error updating inventory for product {product_id}: {e}")
            return {'error': 'Internal server error'}, 500

    @api.doc('delete_inventory')
    def delete(self, product_id):
        """Delete inventory item"""
        try:
            inventory_service = InventoryService()
            success = inventory_service.delete_inventory_item(product_id)
            
            if not success:
                return {'error': 'Inventory item not found'}, 404
            
            return {'message': 'Inventory item deleted successfully'}, 200
            
        except Exception as e:
            logger.error(f"Error deleting inventory for product {product_id}: {e}")
            return {'error': 'Internal server error'}, 500


@inventory_ns.route('/<string:product_id>/adjust')
class StockAdjustment(Resource):
    @api.doc('adjust_stock')
    @api.expect(stock_adjustment_model)
    def post(self, product_id):
        """Adjust stock for inventory item"""
        try:
            # Validate request data
            data = stock_adjustment_schema.load(request.json)
            data['product_id'] = product_id  # Ensure consistency
            
            inventory_service = InventoryService()
            movement = inventory_service.adjust_stock(**data)
            
            if not movement:
                return {'error': 'Failed to adjust stock'}, 400
            
            result = stock_movement_schema.dump(movement)
            return result, 200
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except ValueError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            logger.error(f"Error adjusting stock for product {product_id}: {e}")
            return {'error': 'Internal server error'}, 500


@inventory_ns.route('/bulk')
class BulkOperations(Resource):
    @api.doc('bulk_operations')
    def post(self):
        """Perform bulk inventory operations"""
        try:
            # Validate request data
            data = bulk_operation_schema.load(request.json)
            
            inventory_service = InventoryService()
            results = inventory_service.bulk_update_inventory(data['operations'])
            
            return {'results': results}, 200
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except Exception as e:
            logger.error(f"Error performing bulk operations: {e}")
            return {'error': 'Internal server error'}, 500


@reservations_ns.route('/')
class ReservationList(Resource):
    @api.doc('list_reservations')
    @api.marshal_list_with(reservation_model)
    def get(self):
        """Get all reservations with optional filtering"""
        try:
            # Get query parameters
            customer_id = request.args.get('customer_id')
            order_id = request.args.get('order_id')
            status = request.args.get('status')
            page = int(request.args.get('page', 1))
            per_page = min(int(request.args.get('per_page', 20)), 100)
            
            inventory_service = InventoryService()
            reservations, total = inventory_service.search_reservations(
                customer_id=customer_id,
                order_id=order_id,
                status=status,
                page=page,
                per_page=per_page
            )
            
            result = reservation_response_schema.dump(reservations, many=True)
            
            return {
                'items': result,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }, 200
            
        except Exception as e:
            logger.error(f"Error listing reservations: {e}")
            return {'error': 'Internal server error'}, 500

    @api.doc('create_reservation')
    @api.expect(reservation_model)
    @api.marshal_with(reservation_model)
    def post(self):
        """Create new reservation"""
        try:
            # Validate request data
            data = reservation_request_schema.load(request.json)
            
            inventory_service = InventoryService()
            reservation = inventory_service.create_reservation(**data)
            
            if not reservation:
                return {'error': 'Insufficient stock for reservation'}, 409
            
            result = reservation_response_schema.dump(reservation)
            return result, 201
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except ValueError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            logger.error(f"Error creating reservation: {e}")
            return {'error': 'Internal server error'}, 500


@reservations_ns.route('/<int:reservation_id>')
class Reservation(Resource):
    @api.doc('get_reservation')
    @api.marshal_with(reservation_model)
    def get(self, reservation_id):
        """Get reservation by ID"""
        try:
            inventory_service = InventoryService()
            reservation = inventory_service.get_reservation(reservation_id)
            
            if not reservation:
                return {'error': 'Reservation not found'}, 404
            
            result = reservation_response_schema.dump(reservation)
            return result, 200
            
        except Exception as e:
            logger.error(f"Error getting reservation {reservation_id}: {e}")
            return {'error': 'Internal server error'}, 500

    @api.doc('cancel_reservation')
    def delete(self, reservation_id):
        """Cancel reservation"""
        try:
            inventory_service = InventoryService()
            success = inventory_service.cancel_reservation(reservation_id)
            
            if not success:
                return {'error': 'Reservation not found or already processed'}, 404
            
            return {'message': 'Reservation cancelled successfully'}, 200
            
        except Exception as e:
            logger.error(f"Error cancelling reservation {reservation_id}: {e}")
            return {'error': 'Internal server error'}, 500


@reservations_ns.route('/confirm')
class ReservationConfirm(Resource):
    @api.doc('confirm_reservations')
    def post(self):
        """Confirm multiple reservations"""
        try:
            # Validate request data
            data = reservation_confirm_schema.load(request.json)
            
            inventory_service = InventoryService()
            results = inventory_service.confirm_reservations(
                data['reservation_ids'], 
                data['order_id']
            )
            
            return {'results': results}, 200
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except Exception as e:
            logger.error(f"Error confirming reservations: {e}")
            return {'error': 'Internal server error'}, 500


@health_ns.route('/')
class HealthCheck(Resource):
    @api.doc('health_check')
    def get(self):
        """Health check endpoint"""
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


def register_routes(app):
    """Register all routes with the Flask app"""
    app.register_blueprint(inventory_bp, url_prefix='/api/v1')
    register_error_handlers(app)
