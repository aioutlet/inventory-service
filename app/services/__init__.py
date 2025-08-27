from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
from uuid import uuid4

from app import get_redis
from app.models import InventoryItem, Reservation, StockMovement, StockMovementType, ReservationStatus
from app.repositories import InventoryRepository, ReservationRepository
from app.utils.cache_utils import cache_key_generator, get_from_cache, set_cache
from app.utils.external_service_client import ProductServiceClient

logger = logging.getLogger(__name__)


class InventoryService:
    """Business logic for inventory management"""
    
    def __init__(self):
        self.inventory_repo = InventoryRepository()
        self.reservation_repo = ReservationRepository()
        self.product_client = ProductServiceClient()
        self.redis = get_redis()
    
    def check_stock_availability(self, stock_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check stock availability for multiple items
        
        Args:
            stock_items: List of {'sku': str, 'quantity': int}
            
        Returns:
            Dict with availability status and item details
        """
        try:
            # Extract SKUs for batch query
            skus = [item['sku'] for item in stock_items]
            
            # Try cache first
            cache_key = cache_key_generator('stock_check', skus)
            cached_result = get_from_cache(cache_key, self.redis)
            if cached_result:
                logger.debug("Stock check served from cache")
                return cached_result
            
            # Get inventory items from database
            inventory_items = self.inventory_repo.get_multiple_by_skus(skus)
            inventory_map = {item.sku: item for item in inventory_items}
            
            # Check availability for each requested item
            results = []
            all_available = True
            
            for stock_item in stock_items:
                sku = stock_item['sku']
                requested_quantity = stock_item['quantity']
                
                inventory_item = inventory_map.get(sku)
                if not inventory_item:
                    available_quantity = 0
                    available = False
                else:
                    available_quantity = inventory_item.quantity_available
                    available = available_quantity >= requested_quantity
                
                results.append({
                    'sku': sku,
                    'requested_quantity': requested_quantity,
                    'available_quantity': available_quantity,
                    'available': available
                })
                
                if not available:
                    all_available = False
            
            response = {
                'available': all_available,
                'items': results,
                'checked_at': datetime.utcnow().isoformat()
            }
            
            # Cache the result
            set_cache(cache_key, response, 300, self.redis)  # 5 minutes TTL
            
            return response
            
        except Exception as e:
            logger.error(f"Error checking stock availability: {str(e)}")
            raise
    
    def reserve_stock(self, order_id: str, items: List[Dict[str, Any]], 
                     ttl_minutes: int = 30) -> Dict[str, Any]:
        """
        Reserve stock for an order
        
        Args:
            order_id: Order identifier
            items: List of {'sku': str, 'quantity': int}
            ttl_minutes: Reservation TTL in minutes
            
        Returns:
            Dict with reservation details
        """
        try:
            # First check availability
            availability_result = self.check_stock_availability(items)
            if not availability_result['available']:
                return {
                    'success': False,
                    'message': 'Insufficient stock for one or more items',
                    'availability': availability_result
                }
            
            # Create reservations
            reservations = []
            expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
            
            for item in items:
                sku = item['sku']
                quantity = item['quantity']
                
                # Create reservation record
                reservation = Reservation(
                    id=str(uuid4()),
                    order_id=order_id,
                    sku=sku,
                    quantity=quantity,
                    status=ReservationStatus.PENDING,
                    expires_at=expires_at
                )
                
                # Save reservation
                reservation = self.reservation_repo.create(reservation)
                
                # Update inventory (reserve stock)
                success = self.inventory_repo.update_stock(
                    sku=sku,
                    quantity_change=quantity,
                    movement_type=StockMovementType.RESERVED,
                    reference=order_id,
                    reason=f"Stock reserved for order {order_id}"
                )
                
                if not success:
                    # Rollback reservations if stock update fails
                    logger.error(f"Failed to reserve stock for SKU {sku}")
                    # TODO: Implement proper rollback mechanism
                    raise Exception(f"Failed to reserve stock for SKU {sku}")
                
                reservations.append(reservation)
                logger.info(f"Reserved {quantity} units of SKU {sku} for order {order_id}")
            
            # Clear relevant caches
            self._clear_stock_caches()
            
            return {
                'success': True,
                'reservations': [r.to_dict() for r in reservations],
                'expires_at': expires_at.isoformat(),
                'message': f'Successfully reserved stock for {len(items)} items'
            }
            
        except Exception as e:
            logger.error(f"Error reserving stock for order {order_id}: {str(e)}")
            raise
    
    def confirm_reservation(self, reservation_id: str) -> bool:
        """
        Confirm a reservation (convert reserved stock to sold)
        
        Args:
            reservation_id: Reservation identifier
            
        Returns:
            True if successful
        """
        try:
            reservation = self.reservation_repo.get_by_id(reservation_id)
            if not reservation:
                raise ValueError(f"Reservation {reservation_id} not found")
            
            if reservation.status != ReservationStatus.PENDING:
                raise ValueError(f"Reservation {reservation_id} is not pending")
            
            if reservation.is_expired:
                raise ValueError(f"Reservation {reservation_id} has expired")
            
            # Update reservation status
            self.reservation_repo.update_status(reservation_id, ReservationStatus.CONFIRMED)
            
            # Record stock movement (convert reserved to sold)
            self.inventory_repo.update_stock(
                sku=reservation.sku,
                quantity_change=reservation.quantity,
                movement_type=StockMovementType.OUT,
                reference=reservation.order_id,
                reason=f"Stock sold for order {reservation.order_id}"
            )
            
            logger.info(f"Confirmed reservation {reservation_id} for order {reservation.order_id}")
            self._clear_stock_caches()
            
            return True
            
        except Exception as e:
            logger.error(f"Error confirming reservation {reservation_id}: {str(e)}")
            raise
    
    def release_reservation(self, reservation_id: str) -> bool:
        """
        Release a reservation (return reserved stock to available)
        
        Args:
            reservation_id: Reservation identifier
            
        Returns:
            True if successful
        """
        try:
            reservation = self.reservation_repo.get_by_id(reservation_id)
            if not reservation:
                raise ValueError(f"Reservation {reservation_id} not found")
            
            if reservation.status != ReservationStatus.PENDING:
                raise ValueError(f"Reservation {reservation_id} is not pending")
            
            # Update reservation status
            self.reservation_repo.update_status(reservation_id, ReservationStatus.RELEASED)
            
            # Release reserved stock
            self.inventory_repo.update_stock(
                sku=reservation.sku,
                quantity_change=reservation.quantity,
                movement_type=StockMovementType.RELEASED,
                reference=reservation.order_id,
                reason=f"Released reservation for order {reservation.order_id}"
            )
            
            logger.info(f"Released reservation {reservation_id} for order {reservation.order_id}")
            self._clear_stock_caches()
            
            return True
            
        except Exception as e:
            logger.error(f"Error releasing reservation {reservation_id}: {str(e)}")
            raise
    
    def update_stock(self, sku: str, quantity: int, movement_type: str,
                    reference: str = None, reason: str = None) -> bool:
        """
        Update stock quantity
        
        Args:
            sku: Product SKU
            quantity: Quantity change
            movement_type: Type of movement (in, out, adjustment)
            reference: Reference (order ID, etc.)
            reason: Reason for change
            
        Returns:
            True if successful
        """
        try:
            movement_enum = StockMovementType(movement_type)
            
            success = self.inventory_repo.update_stock(
                sku=sku,
                quantity_change=quantity,
                movement_type=movement_enum,
                reference=reference,
                reason=reason
            )
            
            if success:
                logger.info(f"Updated stock for SKU {sku}: {movement_type} {quantity}")
                self._clear_stock_caches()
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating stock for SKU {sku}: {str(e)}")
            raise
    
    def get_inventory_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Get inventory item by SKU with product details"""
        try:
            # Try cache first
            cache_key = cache_key_generator('inventory', sku)
            cached_result = get_from_cache(cache_key, self.redis)
            if cached_result:
                return cached_result
            
            inventory_item = self.inventory_repo.get_by_sku(sku)
            if not inventory_item:
                return None
            
            result = inventory_item.to_dict()
            
            # Enrich with product details if available
            try:
                product_details = self.product_client.get_product_by_id(inventory_item.product_id)
                if product_details:
                    result['product'] = product_details
            except Exception as e:
                logger.warning(f"Failed to fetch product details for {inventory_item.product_id}: {e}")
            
            # Cache the result
            set_cache(cache_key, result, 600, self.redis)  # 10 minutes TTL
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting inventory for SKU {sku}: {str(e)}")
            raise
    
    def get_inventory_by_product_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get inventory item by product ID"""
        try:
            # Try cache first
            cache_key = cache_key_generator('inventory_pid', product_id)
            cached_result = get_from_cache(cache_key, self.redis)
            if cached_result:
                return cached_result
            
            inventory_item = self.inventory_repo.get_by_product_id(product_id)
            if not inventory_item:
                return None
            
            result = inventory_item.to_dict()
            
            # Enrich with product details if available
            try:
                product_details = self.product_client.get_product_by_id(inventory_item.product_id)
                if product_details:
                    result['product'] = product_details
            except Exception as e:
                logger.warning(f"Failed to fetch product details for {inventory_item.product_id}: {e}")
            
            # Cache the result
            set_cache(cache_key, result, 600, self.redis)  # 10 minutes TTL
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting inventory for product ID {product_id}: {str(e)}")
            raise
    
    def create_inventory_item(self, **kwargs) -> Dict[str, Any]:
        """Create a new inventory item"""
        try:
            # Create new inventory item from provided data
            inventory_item = InventoryItem(
                sku=kwargs.get('sku', f"SKU-{kwargs['product_id']}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"),
                product_id=kwargs['product_id'],
                quantity_available=kwargs.get('quantity_available', 0),
                quantity_reserved=kwargs.get('quantity_reserved', 0),
                reorder_level=kwargs.get('reorder_level', 10),
                max_stock=kwargs.get('max_stock', 1000),
                cost_per_unit=kwargs.get('cost_per_unit')
            )
            
            # Save to database
            created_item = self.inventory_repo.create(inventory_item)
            
            # Clear relevant caches
            self._clear_stock_caches()
            
            return created_item.to_dict()
            
        except Exception as e:
            logger.error(f"Error creating inventory item: {str(e)}")
            raise
    
    def delete_inventory_item(self, product_id: str) -> bool:
        """Delete an inventory item by product ID"""
        try:
            # Find the item first
            inventory_item = self.inventory_repo.get_by_product_id(product_id)
            if not inventory_item:
                return False
            
            # Delete the item
            success = self.inventory_repo.delete(inventory_item.sku)
            
            if success:
                # Clear relevant caches
                self._clear_stock_caches()
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting inventory item for product {product_id}: {str(e)}")
            raise
    
    def update_inventory_item(self, product_id: str, **kwargs) -> Dict[str, Any]:
        """Update an inventory item"""
        try:
            inventory_item = self.inventory_repo.get_by_product_id(product_id)
            if not inventory_item:
                raise ValueError(f"Inventory item for product {product_id} not found")
            
            # Update allowed fields
            for key, value in kwargs.items():
                if hasattr(inventory_item, key) and key not in ['id', 'sku', 'created_at']:
                    setattr(inventory_item, key, value)
            
            inventory_item.updated_at = datetime.utcnow()
            updated_item = self.inventory_repo.update(inventory_item)
            
            self._clear_stock_caches()
            
            return updated_item.to_dict()
            
        except Exception as e:
            logger.error(f"Error updating inventory item for product {product_id}: {str(e)}")
            raise

    def adjust_stock(self, sku: str, quantity: int, movement_type, reference: str = None, reason: str = None) -> Dict[str, Any]:
        """Adjust stock levels"""
        try:
            # Handle both string and enum inputs
            if isinstance(movement_type, str):
                movement_type = movement_type.upper()
                movement_enum = StockMovementType[movement_type]
            else:
                movement_enum = movement_type
            
            success = self.inventory_repo.update_stock(
                sku=sku,
                quantity_change=quantity,
                movement_type=movement_enum,
                reference=reference,
                reason=reason
            )
            
            if success:
                # Create and return movement record
                movement = self.inventory_repo.create_stock_movement(
                    sku=sku,
                    movement_type=movement_enum,
                    quantity=quantity,
                    reference=reference,
                    reason=reason
                )
                self._clear_stock_caches()
                return movement.to_dict()
            else:
                raise ValueError(f"Failed to adjust stock for SKU {sku}")
                
        except Exception as e:
            logger.error(f"Error adjusting stock for SKU {sku}: {str(e)}")
            raise

    def bulk_update_inventory(self, operations: List[dict]) -> List[dict]:
        """Bulk update inventory items"""
        try:
            results = self.inventory_repo.bulk_update(operations)
            self._clear_stock_caches()
            return results
            
        except Exception as e:
            logger.error(f"Error bulk updating inventory: {str(e)}")
            raise

    def get_inventory_with_product_details(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get inventory with enriched product details"""
        return self.get_inventory_by_product_id(product_id)

    def search_inventory_advanced(self, **kwargs) -> tuple[List[Dict[str, Any]], int]:
        """Advanced inventory search"""
        try:
            items, total = self.inventory_repo.search(**kwargs)
            return [item.to_dict() for item in items], total
            
        except Exception as e:
            logger.error(f"Error searching inventory: {str(e)}")
            raise

    def check_availability(self, sku: str, quantity: int) -> Dict[str, Any]:
        """Check availability for a specific item"""
        try:
            inventory_item = self.inventory_repo.get_by_sku(sku)
            if not inventory_item:
                return {
                    'available': False,
                    'available_quantity': 0,
                    'requested_quantity': quantity,
                    'sku': sku
                }
            
            available = inventory_item.quantity_available >= quantity
            return {
                'available': available,
                'available_quantity': inventory_item.quantity_available,
                'requested_quantity': quantity,
                'sku': sku
            }
            
        except Exception as e:
            logger.error(f"Error checking availability for SKU {sku}: {str(e)}")
            raise

    def health_check(self) -> Dict[str, Any]:
        """Health check for the service"""
        try:
            # Check database connectivity
            test_item = InventoryItem.query.first()
            
            # Check Redis connectivity
            redis_status = "healthy"
            try:
                if self.redis:
                    self.redis.ping()
            except:
                redis_status = "unhealthy"
            
            return {
                'status': 'healthy',
                'database': 'connected',
                'redis': redis_status,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def search_reservations(self, **kwargs) -> List[Dict[str, Any]]:
        """Search reservations - delegated to ReservationService"""
        # This method is called by controllers but should be handled by ReservationService
        # For now, return empty list to avoid errors
        return []
    
    
    
    
    def get_low_stock_items(self) -> List[Dict[str, Any]]:
        """Get items below reorder level"""
        try:
            items = self.inventory_repo.get_low_stock_items()
            return [item.to_dict() for item in items]
            
        except Exception as e:
            logger.error(f"Error getting low stock items: {str(e)}")
            raise
    
    def search_inventory(self, query: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Search inventory items"""
        try:
            items = self.inventory_repo.search_inventory(query, limit, offset)
            return [item.to_dict() for item in items]
            
        except Exception as e:
            logger.error(f"Error searching inventory: {str(e)}")
            raise
    
    def process_expired_reservations(self) -> Dict[str, Any]:
        """Process expired reservations (background task)"""
        try:
            expired_reservations = self.reservation_repo.get_expired_reservations()
            processed_count = 0
            
            for reservation in expired_reservations:
                try:
                    # Update status to expired
                    self.reservation_repo.update_status(reservation.id, ReservationStatus.EXPIRED)
                    
                    # Release reserved stock
                    self.inventory_repo.update_stock(
                        sku=reservation.sku,
                        quantity_change=reservation.quantity,
                        movement_type=StockMovementType.RELEASED,
                        reference=reservation.order_id,
                        reason=f"Expired reservation for order {reservation.order_id}"
                    )
                    
                    processed_count += 1
                    logger.info(f"Processed expired reservation {reservation.id}")
                    
                except Exception as e:
                    logger.error(f"Error processing expired reservation {reservation.id}: {e}")
            
            if processed_count > 0:
                self._clear_stock_caches()
            
            return {
                'processed_count': processed_count,
                'processed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing expired reservations: {str(e)}")
            raise
    
    def cleanup_old_reservations(self) -> int:
        """Cleanup old expired reservations (background task)"""
        try:
            # Delete reservations expired more than 24 hours ago
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            count = self.reservation_repo.delete_expired(cutoff_time)
            
            if count > 0:
                logger.info(f"Cleaned up {count} old reservations")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up old reservations: {str(e)}")
            raise
    
    def _clear_stock_caches(self):
        """Clear stock-related caches"""
        if not self.redis:
            return
            
        try:
            # Clear stock check caches
            keys = self.redis.keys("stock_check:*")
            if keys:
                self.redis.delete(*keys)
            
            # Clear inventory caches
            keys = self.redis.keys("inventory:*")
            if keys:
                self.redis.delete(*keys)
                
            logger.debug("Cleared stock caches")
            
        except Exception as e:
            logger.warning(f"Error clearing caches: {e}")


class ReservationService:
    """Business logic for reservation management"""
    
    def __init__(self):
        self.reservation_repo = ReservationRepository()
        self.inventory_repo = InventoryRepository()
    
    def create_reservation(self, sku: str, order_id: str, quantity: int, ttl_minutes: int = 30) -> Dict[str, Any]:
        """Create a new reservation"""
        try:
            # Check availability first
            inventory_item = self.inventory_repo.get_by_sku(sku)
            if not inventory_item:
                raise ValueError(f"Product with SKU {sku} not found")
            
            if inventory_item.quantity_available < quantity:
                raise ValueError("Insufficient stock")
            
            # Create reservation
            expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
            reservation = Reservation(
                id=str(uuid4()),
                sku=sku,
                order_id=order_id,
                quantity=quantity,
                status=ReservationStatus.PENDING,
                expires_at=expires_at
            )
            
            created_reservation = self.reservation_repo.create(reservation)
            
            # Update stock
            self.inventory_repo.update_stock(
                sku=sku,
                quantity_change=quantity,
                movement_type=StockMovementType.RESERVED,
                reference=order_id,
                reason=f"Reserved for order {order_id}"
            )
            
            return created_reservation.to_dict()
            
        except Exception as e:
            logger.error(f"Error creating reservation: {str(e)}")
            raise
    
    def get_reservation(self, reservation_id: str) -> Optional[Dict[str, Any]]:
        """Get reservation by ID"""
        try:
            reservation = self.reservation_repo.get_by_id(reservation_id)
            return reservation.to_dict() if reservation else None
        except Exception as e:
            logger.error(f"Error getting reservation {reservation_id}: {str(e)}")
            raise
    
    def confirm_reservation(self, reservation_id: str, order_id: str) -> bool:
        """Confirm a reservation"""
        try:
            reservation = self.reservation_repo.get_by_id(reservation_id)
            if not reservation:
                raise ValueError("Reservation not found")
            
            if reservation.order_id != order_id:
                raise ValueError("Order ID mismatch")
            
            if reservation.status != ReservationStatus.PENDING:
                raise ValueError("Reservation is not pending")
            
            # Update status
            self.reservation_repo.update_status(reservation_id, ReservationStatus.CONFIRMED)
            
            # Convert reserved stock to sold
            self.inventory_repo.update_stock(
                sku=reservation.sku,
                quantity_change=reservation.quantity,
                movement_type=StockMovementType.OUT,
                reference=order_id,
                reason=f"Sold for order {order_id}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error confirming reservation {reservation_id}: {str(e)}")
            raise
    
    def cancel_reservation(self, reservation_id: str) -> bool:
        """Cancel a reservation"""
        try:
            reservation = self.reservation_repo.get_by_id(reservation_id)
            if not reservation:
                return False
            
            # Cancel reservation
            self.reservation_repo.cancel(reservation_id)
            
            # Release stock if it was pending
            if reservation.status == ReservationStatus.PENDING:
                self.inventory_repo.update_stock(
                    sku=reservation.sku,
                    quantity_change=reservation.quantity,
                    movement_type=StockMovementType.RELEASED,
                    reference=reservation.order_id,
                    reason=f"Released cancelled reservation for order {reservation.order_id}"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling reservation {reservation_id}: {str(e)}")
            raise
    
    def search_reservations(self, **kwargs) -> List[Dict[str, Any]]:
        """Search reservations"""
        try:
            # Simple implementation - get by order_id if provided
            if 'order_id' in kwargs:
                reservations = self.reservation_repo.get_by_order_id(kwargs['order_id'])
                return [r.to_dict() for r in reservations]
            
            return []
            
        except Exception as e:
            logger.error(f"Error searching reservations: {str(e)}")
            raise
    
    def confirm_reservations_bulk(self, reservation_ids: List[str]) -> List[dict]:
        """Bulk confirm reservations"""
        try:
            results = self.reservation_repo.bulk_confirm(reservation_ids)
            return results
            
        except Exception as e:
            logger.error(f"Error bulk confirming reservations: {str(e)}")
            raise
    
    def expire_reservations(self) -> Dict[str, Any]:
        """Process expired reservations"""
        try:
            expired_reservations = self.reservation_repo.get_expired_reservations()
            processed_count = 0
            
            for reservation in expired_reservations:
                try:
                    # Update status to expired
                    self.reservation_repo.update_status(reservation.id, ReservationStatus.EXPIRED)
                    
                    # Release stock
                    self.inventory_repo.update_stock(
                        sku=reservation.sku,
                        quantity_change=reservation.quantity,
                        movement_type=StockMovementType.RELEASED,
                        reference=reservation.order_id,
                        reason=f"Released expired reservation for order {reservation.order_id}"
                    )
                    
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing expired reservation {reservation.id}: {e}")
            
            return {
                'processed_count': processed_count,
                'processed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing expired reservations: {str(e)}")
            raise
