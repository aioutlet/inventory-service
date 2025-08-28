"""
Reservations Controller - Handles inventory reservation operations
"""

from flask import request
from flask_restx import Resource, fields
from marshmallow import ValidationError
from app.services import InventoryService
from app.utils.validators import (
    ReservationRequestSchema, ReservationResponseSchema,
    ReservationConfirmRequestSchema
)
import logging

logger = logging.getLogger(__name__)

# Initialize schemas
reservation_request_schema = ReservationRequestSchema()
reservation_response_schema = ReservationResponseSchema()
reservation_confirm_schema = ReservationConfirmRequestSchema()


def get_reservation_models(api):
    """Define API models for reservation operations"""
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

    return reservation_model


def register_reservation_routes(api, namespace):
    """Register reservation-related routes"""
    reservation_model = get_reservation_models(api)

    @namespace.route('/')
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

    @namespace.route('/<int:reservation_id>')
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

    @namespace.route('/confirm')
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
