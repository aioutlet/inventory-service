"""
Product Service Client
External client for communicating with product service via Dapr
"""
import os
from typing import Optional, Dict, Any
import logging
from src.clients.dapr_service_client import get_dapr_service_client

logger = logging.getLogger(__name__)


class ProductServiceClient:
    """Client for communicating with product service via Dapr"""
    
    def __init__(self, app_id: str = None):
        self.app_id = app_id or os.environ.get('DAPR_PRODUCT_SERVICE_APP_ID', 'product-service')
        self.dapr_client = get_dapr_service_client()
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product details by ID from product service via Dapr"""
        try:
            method = f"api/v1/products/{product_id}"
            response = self.dapr_client.invoke_get(self.app_id, method)
            
            if response:
                return response
            else:
                logger.warning(f"Product {product_id} not found in product service")
                return None
                
        except Exception as e:
            logger.error(f"Error calling product service for {product_id}: {e}")
            return None
    
    def get_products_by_ids(self, product_ids: list) -> Dict[str, Any]:
        """Get multiple products by IDs via Dapr"""
        try:
            method = "api/v1/products/batch"
            data = {'product_ids': product_ids}
            response = self.dapr_client.invoke_post(self.app_id, method, data)
            
            if response:
                return response
            else:
                logger.error("Product service batch request returned no data")
                return {}
                
        except Exception as e:
            logger.error(f"Error in batch product fetch: {e}")
            return {}
    
    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Alias for get_product_by_id for consistency"""
        return self.get_product_by_id(product_id)
