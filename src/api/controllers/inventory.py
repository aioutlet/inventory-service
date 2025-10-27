"""
Inventory Controller - Handles inventory CRUD operations and stock management
"""

from flask import request
from flask_restx import Resource, fields
from marshmallow import ValidationError
from src.shared.services import InventoryService
from src.shared.utils.validators import (
    InventoryItemRequestSchema, InventoryItemResponseSchema,
    StockAdjustmentRequestSchema, StockMovementResponseSchema,
    InventorySearchSchema, BulkOperationRequestSchema
)
import logging

logger = logging.getLogger(__name__)

# Initialize schemas
inventory_request_schema = InventoryItemRequestSchema()
inventory_response_schema = InventoryItemResponseSchema()
stock_adjustment_schema = StockAdjustmentRequestSchema()
stock_movement_schema = StockMovementResponseSchema()
search_schema = InventorySearchSchema()
bulk_operation_schema = BulkOperationRequestSchema()


def get_inventory_models(api):
    """Define API models for inventory operations"""
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

    return inventory_item_model, stock_adjustment_model


def register_inventory_routes(api, namespace):
    """Register inventory-related routes"""
    inventory_item_model, stock_adjustment_model = get_inventory_models(api)

    @namespace.route('/')
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

    @namespace.route('/<string:product_id>')
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

    @namespace.route('/<string:product_id>/adjust')
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

    @namespace.route('/check-availability')
    class CheckAvailability(Resource):
        @api.doc('check_stock_availability')
        def post(self):
            """Check stock availability for multiple items"""
            try:
                if not request.json or 'items' not in request.json:
                    return {'error': 'Missing items in request body'}, 400
                
                items = request.json['items']
                
                # Validate items format
                if not isinstance(items, list) or not items:
                    return {'error': 'Items must be a non-empty array'}, 400
                
                for item in items:
                    if not isinstance(item, dict) or 'sku' not in item or 'quantity' not in item:
                        return {'error': 'Each item must have sku and quantity'}, 400
                
                inventory_service = InventoryService()
                result = inventory_service.check_stock_availability(items)
                
                return result, 200
                
            except Exception as e:
                logger.error(f"Error checking stock availability: {e}")
                return {'error': 'Internal server error', 'details': str(e)}, 500

    @namespace.route('/bulk')
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

    @namespace.route('/health')
    class InventoryHealth(Resource):
        @api.doc('inventory_health')
        def get(self):
            """Basic health check for inventory service"""
            try:
                inventory_service = InventoryService()
                health_status = inventory_service.health_check()
                
                return health_status, 200
                
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return {
                    'status': 'unhealthy',
                    'service': 'inventory-service',
                    'error': str(e)
                }, 503
