import requests
from typing import Optional, Dict, Any
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class ProductServiceClient:
    """Client for communicating with product service"""
    
    def __init__(self, base_url: str = None):
        self._base_url = base_url
        self.timeout = 5  # seconds
    
    @property
    def base_url(self):
        """Get base URL, using Flask config if not provided during init"""
        if self._base_url is None:
            try:
                self._base_url = current_app.config.get('PRODUCT_SERVICE_URL', 'http://localhost:3001')
            except RuntimeError:
                # Working outside application context, use default
                self._base_url = 'http://localhost:3001'
        return self._base_url
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product details by ID from product service"""
        try:
            url = f"{self.base_url}/api/v1/products/{product_id}"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Product {product_id} not found in product service")
                return None
            else:
                logger.error(f"Product service error for {product_id}: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling product service for {product_id}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error calling product service for {product_id}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling product service for {product_id}: {e}")
            return None
    
    def get_products_by_ids(self, product_ids: list) -> Dict[str, Any]:
        """Get multiple products by IDs"""
        try:
            url = f"{self.base_url}/api/v1/products/batch"
            response = requests.post(
                url, 
                json={'product_ids': product_ids},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Product service batch error: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error in batch product fetch: {e}")
            return {}
