"""
Inventory Service - Business logic for inventory management
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from src.api.main import get_redis
from src.shared.models import InventoryItem, StockMovementType
from src.shared.repositories import InventoryRepository
from src.shared.utils.cache_utils import cache_key_generator, get_from_cache, set_cache
from src.shared.utils.external_service_client import ProductServiceClient

logger = logging.getLogger(__name__)


class InventoryService:
    """Business logic for inventory management"""
    
    def __init__(self):
        self.inventory_repo = InventoryRepository()
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

    def search_inventory(self, **kwargs) -> tuple[List[Dict[str, Any]], int]:
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

    def get_low_stock_items(self) -> List[Dict[str, Any]]:
        """Get items below reorder level"""
        try:
            items = self.inventory_repo.get_low_stock_items()
            return [item.to_dict() for item in items]
            
        except Exception as e:
            logger.error(f"Error getting low stock items: {str(e)}")
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

    def search_inventory_advanced(self, **kwargs) -> tuple[List[Dict[str, Any]], int]:
        """
        Advanced inventory search with extended filters and product details
        
        Args:
            **kwargs: Various search parameters (sku, product_id, category, etc.)
            
        Returns:
            Tuple of (items, total_count)
        """
        try:
            # Use existing search_inventory method as base
            items, total_count = self.search_inventory(**kwargs)
            
            # Enhance with additional details if needed
            for item in items:
                if 'include_product_details' in kwargs and kwargs['include_product_details']:
                    # Add product service call here if needed
                    item['product_details'] = {'status': 'enhanced'}
                    
            return items, total_count
            
        except Exception as e:
            logger.error(f"Advanced inventory search failed: {e}")
            return [], 0

    def get_inventory_with_product_details(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get inventory item with enhanced product details
        
        Args:
            product_id: Product identifier
            
        Returns:
            Inventory item with product details or None
        """
        try:
            # Get base inventory item
            inventory_item = self.get_inventory_by_product_id(product_id)
            
            if inventory_item:
                # Add product details from external service
                try:
                    product_details = self.product_client.get_product(product_id)
                    inventory_item['product_details'] = product_details
                except Exception as e:
                    logger.warning(f"Could not fetch product details for {product_id}: {e}")
                    inventory_item['product_details'] = {'error': 'Product details unavailable'}
                    
            return inventory_item
            
        except Exception as e:
            logger.error(f"Get inventory with product details failed: {e}")
            return None
