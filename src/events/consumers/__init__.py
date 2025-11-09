"""
Event consumers/handlers package for Inventory Service
"""

from .product_consumer import handle_product_created, handle_product_updated, handle_product_deleted
from .order_consumer import handle_order_created, handle_order_cancelled, handle_order_completed

__all__ = [
    'handle_product_created',
    'handle_product_updated',
    'handle_product_deleted',
    'handle_order_created',
    'handle_order_cancelled',
    'handle_order_completed',
]
