"""
Product Created Handler
Initializes inventory for newly created products
"""
import logging
from src.shared.database import db
from src.shared.models.inventory_item import InventoryItem
from datetime import datetime

logger = logging.getLogger(__name__)


async def handle_product_created(event_data: dict, correlation_id: str = None):
    """
    Handle product.created event
    Creates initial inventory record for new product
    
    Args:
        event_data: Event data containing productId and initial stock info
        correlation_id: Correlation ID for tracing
    """
    try:
        product_id = event_data.get('productId')
        initial_quantity = event_data.get('initialQuantity', 0)
        sku = event_data.get('sku')
        location = event_data.get('location', 'WAREHOUSE_MAIN')
        
        if not product_id:
            logger.warning(f"product.created event missing productId. CorrelationId: {correlation_id}")
            return
        
        logger.info(f"Initializing inventory for product {product_id}. CorrelationId: {correlation_id}")
        
        # Check if inventory already exists
        existing = InventoryItem.query.filter_by(product_id=product_id).first()
        
        if existing:
            logger.warning(f"Inventory already exists for product {product_id}. CorrelationId: {correlation_id}")
            return
        
        # Create new inventory record
        inventory = InventoryItem(
            product_id=product_id,
            sku=sku,
            quantity=initial_quantity,
            available_quantity=initial_quantity,
            reserved_quantity=0,
            location=location
        )
        
        db.session.add(inventory)
        db.session.commit()
        
        logger.info(f"Created inventory for product {product_id} with {initial_quantity} units. CorrelationId: {correlation_id}")
        
    except Exception as e:
        logger.error(f"Error handling product.created event: {str(e)}. CorrelationId: {correlation_id}")
        db.session.rollback()
        raise
