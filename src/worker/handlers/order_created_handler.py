"""
Order Created Handler
Reserves inventory when an order is created
"""
import logging
from flask import current_app
from sqlalchemy import text
from src.shared.database import db
from src.shared.models.inventory_item import InventoryItem
from src.shared.models.reservation import Reservation
from src.shared.models.enums import MovementType
from src.shared.services.message_broker_publisher import get_publisher
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


async def handle_order_created(event_data: dict, correlation_id: str = None):
    """
    Handle order.created event
    Reserves inventory for products in the order
    
    Args:
        event_data: Event data containing orderId and items
        correlation_id: Correlation ID for tracing
    """
    try:
        order_id = event_data.get('orderId')
        items = event_data.get('items', [])
        user_id = event_data.get('userId')
        
        if not items:
            logger.warning(f"Order {order_id} has no items. CorrelationId: {correlation_id}")
            return
        
        logger.info(f"Reserving inventory for order {order_id}. CorrelationId: {correlation_id}")
        
        # Track if all reservations successful
        all_reserved = True
        reserved_items = []
        
        for item in items:
            product_id = item.get('productId')
            quantity = item.get('quantity', 1)
            
            if not product_id:
                continue
            
            # Check inventory availability
            inventory = InventoryItem.query.filter_by(product_id=product_id).first()
            
            if not inventory or inventory.available_quantity < quantity:
                logger.warning(f"Insufficient inventory for product {product_id}. CorrelationId: {correlation_id}")
                all_reserved = False
                break
            
            # Reserve inventory
            try:
                # Create reservation
                expiry_minutes = int(os.getenv('RESERVATION_TTL_MINUTES', 30))
                expiry = datetime.utcnow() + timedelta(minutes=expiry_minutes)
                
                reservation = Reservation(
                    product_id=product_id,
                    order_id=order_id,
                    user_id=user_id,
                    quantity=quantity,
                    expires_at=expiry
                )
                
                # Update inventory
                inventory.reserved_quantity += quantity
                inventory.available_quantity -= quantity
                
                db.session.add(reservation)
                reserved_items.append({
                    'productId': product_id,
                    'quantity': quantity,
                    'reservationId': str(reservation.id)
                })
                
                logger.info(f"Reserved {quantity} units of product {product_id} for order {order_id}")
                
            except Exception as e:
                logger.error(f"Error reserving product {product_id}: {str(e)}")
                all_reserved = False
                break
        
        if all_reserved and reserved_items:
            # Commit all reservations
            db.session.commit()
            
            # Publish inventory.reserved event
            publisher = get_publisher()
            await publisher.publish(
                event_type='inventory.reserved',
                data={
                    'orderId': order_id,
                    'items': reserved_items,
                    'reservedAt': datetime.utcnow().isoformat()
                },
                correlation_id=correlation_id
            )
            
            logger.info(f"Successfully reserved inventory for order {order_id}. CorrelationId: {correlation_id}")
        else:
            # Rollback on failure
            db.session.rollback()
            
            # Publish inventory.reservation.failed event
            publisher = get_publisher()
            await publisher.publish(
                event_type='inventory.reservation.failed',
                data={
                    'orderId': order_id,
                    'reason': 'Insufficient inventory',
                    'failedAt': datetime.utcnow().isoformat()
                },
                correlation_id=correlation_id
            )
            
            logger.warning(f"Failed to reserve inventory for order {order_id}. CorrelationId: {correlation_id}")
        
    except Exception as e:
        logger.error(f"Error handling order.created event: {str(e)}. CorrelationId: {correlation_id}")
        db.session.rollback()
        raise
