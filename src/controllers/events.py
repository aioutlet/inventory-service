"""
Event Controllers for Inventory Service
HTTP endpoints for handling Dapr pub/sub event delivery
"""

from flask import Blueprint, request, jsonify, current_app
from src.services.inventory_events_service import InventoryEventsService

events_bp = Blueprint('events', __name__)
events_service = InventoryEventsService()


# ============================================================================
# Product Events
# ============================================================================

@events_bp.route('/events/product-created', methods=['POST'])
def product_created():
    """Handle product.created event"""
    try:
        event_data = request.get_json()
        result = events_service.handle_product_created(event_data)
        return jsonify({"success": result.get('status') == 'success'}), 200
    except Exception as e:
        current_app.logger.error(f"❌ Error processing product.created: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 200


@events_bp.route('/events/product-updated', methods=['POST'])
def product_updated():
    """Handle product.updated event"""
    try:
        event_data = request.get_json()
        result = events_service.handle_product_updated(event_data)
        return jsonify({"success": result.get('status') == 'success'}), 200
    except Exception as e:
        current_app.logger.error(f"❌ Error processing product.updated: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 200


@events_bp.route('/events/product-deleted', methods=['POST'])
def product_deleted():
    """Handle product.deleted event"""
    try:
        event_data = request.get_json()
        result = events_service.handle_product_deleted(event_data)
        return jsonify({"success": result.get('status') == 'success'}), 200
    except Exception as e:
        current_app.logger.error(f"❌ Error processing product.deleted: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 200


# ============================================================================
# Order Events
# ============================================================================

@events_bp.route('/events/order-created', methods=['POST'])
def order_created():
    """Handle order.created event"""
    try:
        event_data = request.get_json()
        result = events_service.handle_order_created(event_data)
        return jsonify({"success": result.get('status') == 'success'}), 200
    except Exception as e:
        current_app.logger.error(f"❌ Error processing order.created: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 200


@events_bp.route('/events/order-cancelled', methods=['POST'])
def order_cancelled():
    """Handle order.cancelled event"""
    try:
        event_data = request.get_json()
        result = events_service.handle_order_cancelled(event_data)
        return jsonify({"success": result.get('status') == 'success'}), 200
    except Exception as e:
        current_app.logger.error(f"❌ Error processing order.cancelled: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 200


@events_bp.route('/events/order-completed', methods=['POST'])
def order_completed():
    """Handle order.completed event"""
    try:
        event_data = request.get_json()
        result = events_service.handle_order_completed(event_data)
        return jsonify({"success": result.get('status') == 'success'}), 200
    except Exception as e:
        current_app.logger.error(f"❌ Error processing order.completed: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 200
