"""
Order Cancelled Handler
Releases reserved inventory when an order is cancelled
"""
import logging
from src.shared.database import db
from src.shared.models.inventory_item import InventoryItem
from src.shared.models.reservation import Reservation
from src.shared.services.message_broker_service import get_publisher
from datetime import datetime

logger = logging.getLogger(__name__)


async def handle_order_cancelled(event_data: dict, correlation_id: str = None):
    """
    Handle order.cancelled event
    Releases reserved inventory back to available stock
    
    Args:
        event_data: Event data containing orderId
        correlation_id: Correlation ID for tracing
    """
    try:
        order_id = event_data.get('orderId')
        
        if not order_id:
            logger.warning(f"order.cancelled event missing orderId. CorrelationId: {correlation_id}")
            return
        
        logger.info(f"Releasing inventory for cancelled order {order_id}. CorrelationId: {correlation_id}")
        
        # Find all reservations for this order
        reservations = Reservation.query.filter_by(order_id=order_id, is_active=True).all()
        
        if not reservations:
            logger.warning(f"No active reservations found for order {order_id}. CorrelationId: {correlation_id}")
            return
        
        released_items = []
        
        for reservation in reservations:
            # Update inventory
            inventory = InventoryItem.query.filter_by(product_id=reservation.product_id).first()
            
            if inventory:
                inventory.reserved_quantity -= reservation.quantity
                inventory.available_quantity += reservation.quantity
                
                released_items.append({
                    'productId': reservation.product_id,
                    'quantity': reservation.quantity
                })
                
                logger.info(f"Released {reservation.quantity} units of product {reservation.product_id}")
            
            # Mark reservation as inactive
            reservation.is_active = False
        
        db.session.commit()
        
        # Publish inventory.released event
        publisher = get_publisher()
        await publisher.publish(
            event_type='inventory.released',
            data={
                'orderId': order_id,
                'items': released_items,
                'releasedAt': datetime.utcnow().isoformat()
            },
            correlation_id=correlation_id
        )
        
        logger.info(f"Successfully released inventory for order {order_id}. CorrelationId: {correlation_id}")
        
    except Exception as e:
        logger.error(f"Error handling order.cancelled event: {str(e)}. CorrelationId: {correlation_id}")
        db.session.rollback()
        raise
