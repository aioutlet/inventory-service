"""
Dapr Event Subscription Endpoints for Inventory Service
Flask blueprint handling Dapr pub/sub subscriptions
"""

from flask import Blueprint, request, jsonify, current_app
from src.events.consumers import (
    handle_product_created,
    handle_product_updated,
    handle_product_deleted,
    handle_order_created,
    handle_order_cancelled,
    handle_order_completed
)

events_bp = Blueprint('events', __name__, url_prefix='/dapr')


@events_bp.route('/subscribe', methods=['GET'])
def get_subscriptions():
    """
    Dapr calls this endpoint to discover subscription configurations.
    Returns list of topics this service wants to subscribe to.
    """
    subscriptions = [
        {
            "pubsubname": "inventory-pubsub",
            "topic": "product.created",
            "route": "/dapr/events/product-created"
        },
        {
            "pubsubname": "inventory-pubsub",
            "topic": "product.updated",
            "route": "/dapr/events/product-updated"
        },
        {
            "pubsubname": "inventory-pubsub",
            "topic": "product.deleted",
            "route": "/dapr/events/product-deleted"
        },
        {
            "pubsubname": "inventory-pubsub",
            "topic": "order.created",
            "route": "/dapr/events/order-created"
        },
        {
            "pubsubname": "inventory-pubsub",
            "topic": "order.cancelled",
            "route": "/dapr/events/order-cancelled"
        },
        {
            "pubsubname": "inventory-pubsub",
            "topic": "order.completed",
            "route": "/dapr/events/order-completed"
        }
    ]
    
    current_app.logger.info(
        f"📋 Dapr subscription discovery: {len(subscriptions)} subscriptions configured"
    )
    
    return jsonify(subscriptions)


# ============================================================================
# Product Events
# ============================================================================

@events_bp.route('/events/product-created', methods=['POST'])
def product_created():
    """Handle product.created event"""
    try:
        event_data = request.get_json()
        correlation_id = event_data.get('correlationid', 'N/A')
        
        current_app.logger.info(
            f"📥 Received product.created event",
            extra={"correlationId": correlation_id}
        )
        
        result = handle_product_created(event_data)
        
        if result.get('status') == 'success':
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "error": result.get('message')}), 200
            
    except Exception as e:
        current_app.logger.error(f"❌ Error processing product.created: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 200


@events_bp.route('/events/product-updated', methods=['POST'])
def product_updated():
    """Handle product.updated event"""
    try:
        event_data = request.get_json()
        correlation_id = event_data.get('correlationid', 'N/A')
        
        current_app.logger.info(
            f"📥 Received product.updated event",
            extra={"correlationId": correlation_id}
        )
        
        result = handle_product_updated(event_data)
        
        if result.get('status') == 'success':
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "error": result.get('message')}), 200
            
    except Exception as e:
        current_app.logger.error(f"❌ Error processing product.updated: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 200


@events_bp.route('/events/product-deleted', methods=['POST'])
def product_deleted():
    """Handle product.deleted event"""
    try:
        event_data = request.get_json()
        correlation_id = event_data.get('correlationid', 'N/A')
        
        current_app.logger.info(
            f"📥 Received product.deleted event",
            extra={"correlationId": correlation_id}
        )
        
        result = handle_product_deleted(event_data)
        
        if result.get('status') == 'success':
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "error": result.get('message')}), 200
            
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
        correlation_id = event_data.get('correlationid', 'N/A')
        
        current_app.logger.info(
            f"📥 Received order.created event",
            extra={"correlationId": correlation_id}
        )
        
        result = handle_order_created(event_data)
        
        if result.get('status') == 'success':
            return jsonify({"success": True}), 200
        else:
            # Even on error, return 200 to Dapr (let retry logic handle it)
            return jsonify({"success": False, "error": result.get('message')}), 200
            
    except Exception as e:
        current_app.logger.error(f"❌ Error processing order.created: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 200


@events_bp.route('/events/order-cancelled', methods=['POST'])
def order_cancelled():
    """Handle order.cancelled event"""
    try:
        event_data = request.get_json()
        correlation_id = event_data.get('correlationid', 'N/A')
        
        current_app.logger.info(
            f"📥 Received order.cancelled event",
            extra={"correlationId": correlation_id}
        )
        
        result = handle_order_cancelled(event_data)
        
        if result.get('status') == 'success':
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "error": result.get('message')}), 200
            
    except Exception as e:
        current_app.logger.error(f"❌ Error processing order.cancelled: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 200


@events_bp.route('/events/order-completed', methods=['POST'])
def order_completed():
    """Handle order.completed event"""
    try:
        event_data = request.get_json()
        correlation_id = event_data.get('correlationid', 'N/A')
        
        current_app.logger.info(
            f"📥 Received order.completed event",
            extra={"correlationId": correlation_id}
        )
        
        result = handle_order_completed(event_data)
        
        if result.get('status') == 'success':
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "error": result.get('message')}), 200
            
    except Exception as e:
        current_app.logger.error(f"❌ Error processing order.completed: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 200


# ============================================================================
# Health Check
# ============================================================================

@events_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint for Dapr"""
    return jsonify({
        "status": "healthy",
        "service": "inventory-service-events",
        "dapr": "enabled"
    }), 200
