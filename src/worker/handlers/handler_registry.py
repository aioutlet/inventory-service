"""
Handler Registry - Maps event types to their handler functions
"""
from src.worker.handlers.order_created_handler import handle_order_created
from src.worker.handlers.order_cancelled_handler import handle_order_cancelled
from src.worker.handlers.product_created_handler import handle_product_created

# Registry mapping event types to handler functions
HANDLERS = {
    'order.created': handle_order_created,
    'order.cancelled': handle_order_cancelled,
    'product.created': handle_product_created,
}

def get_handler(event_type: str):
    """
    Get handler function for given event type
    
    Args:
        event_type: The type of event to handle
        
    Returns:
        Handler function or None if no handler registered
    """
    return HANDLERS.get(event_type)
