"""
Base Repository Interface - Abstract base classes
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from app.models import InventoryItem, Reservation, StockMovement, ReservationStatus, StockMovementType
from datetime import datetime


class InventoryRepositoryInterface(ABC):
    """Abstract base class for inventory repository"""
    
    @abstractmethod
    def get_by_sku(self, sku: str) -> Optional[InventoryItem]:
        pass
    
    @abstractmethod
    def get_by_product_id(self, product_id: str) -> Optional[InventoryItem]:
        pass
    
    @abstractmethod
    def get_multiple_by_skus(self, skus: List[str]) -> List[InventoryItem]:
        pass
    
    @abstractmethod
    def create(self, item: InventoryItem) -> InventoryItem:
        pass
    
    @abstractmethod
    def update(self, item: InventoryItem) -> InventoryItem:
        pass
    
    @abstractmethod
    def update_stock(self, sku: str, quantity_change: int, movement_type: StockMovementType,
                    reference: str = None, reason: str = None, created_by: str = 'system') -> bool:
        pass
    
    @abstractmethod
    def get_low_stock_items(self) -> List[InventoryItem]:
        pass
    
    @abstractmethod
    def search_inventory(self, query: str, limit: int = 20, offset: int = 0) -> List[InventoryItem]:
        pass

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[InventoryItem]:
        pass

    @abstractmethod
    def get_all(self, page: int = 1, per_page: int = 20) -> tuple[List[InventoryItem], int]:
        pass

    @abstractmethod
    def search(self, **kwargs) -> tuple[List[InventoryItem], int]:
        pass

    @abstractmethod
    def bulk_update(self, updates: List[dict]) -> List[dict]:
        pass

    @abstractmethod
    def create_stock_movement(self, **kwargs) -> StockMovement:
        pass

    @abstractmethod
    def get_stock_movements(self, sku: str) -> List[StockMovement]:
        pass


class ReservationRepositoryInterface(ABC):
    """Abstract base class for reservation repository"""
    
    @abstractmethod
    def create(self, reservation: Reservation) -> Reservation:
        pass
    
    @abstractmethod
    def get_by_id(self, reservation_id: str) -> Optional[Reservation]:
        pass
    
    @abstractmethod
    def get_by_order_id(self, order_id: str) -> List[Reservation]:
        pass
    
    @abstractmethod
    def update_status(self, reservation_id: str, status: ReservationStatus) -> bool:
        pass
    
    @abstractmethod
    def get_expired_reservations(self) -> List[Reservation]:
        pass
    
    @abstractmethod
    def delete_expired(self, expired_before: datetime) -> int:
        pass

    @abstractmethod
    def cancel(self, reservation_id: str) -> Optional[Reservation]:
        pass

    @abstractmethod
    def bulk_confirm(self, reservation_ids: List[str]) -> List[dict]:
        pass
