"""
Models package - Database models for inventory service
"""

# Import database instance
from src.database import db

# Import enums first
from .enums import ReservationStatus, StockMovementType

# Import models
from .inventory_item import InventoryItem
from .reservation import Reservation
from .stock_movement import StockMovement

# Export all models and enums
__all__ = [
    'db',
    'ReservationStatus',
    'StockMovementType', 
    'InventoryItem',
    'Reservation',
    'StockMovement'
]
