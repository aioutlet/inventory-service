"""
Repositories package - Data access layer for inventory service
"""

# Import interfaces
from .base import InventoryRepositoryInterface, ReservationRepositoryInterface

# Import concrete implementations
from .inventory_repository import InventoryRepository
from .reservation_repository import ReservationRepository

# Export all interfaces and implementations
__all__ = [
    'InventoryRepositoryInterface',
    'ReservationRepositoryInterface',
    'InventoryRepository', 
    'ReservationRepository'
]
