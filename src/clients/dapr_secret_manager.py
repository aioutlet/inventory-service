"""
Dapr Secret Manager Client
Manages secrets retrieval using Dapr Secret Store
"""
import os
import logging
from typing import Dict, Any, Optional
from dapr.clients import DaprClient

logger = logging.getLogger(__name__)


class DaprSecretManager:
    """Client for retrieving secrets from Dapr Secret Store"""
    
    def __init__(self):
        self.secret_store_name = os.getenv('DAPR_SECRET_STORE_NAME', 'local-secret-store')
        self.dapr_client = DaprClient()
    
    def get_secret(self, key: str) -> Optional[str]:
        """
        Get a single secret value from Dapr Secret Store
        
        Args:
            key: Secret key to retrieve
            
        Returns:
            Secret value or None if not found
        """
        try:
            secret_response = self.dapr_client.get_secret(
                store_name=self.secret_store_name,
                key=key
            )
            
            if secret_response and secret_response.secret:
                return secret_response.secret.get(key)
            
            logger.warning(f"Secret '{key}' not found in store '{self.secret_store_name}'")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving secret '{key}': {str(e)}")
            return None
    
    def get_database_config(self) -> Dict[str, Any]:
        """
        Get database configuration from secrets
        
        Returns:
            Dictionary with database configuration
        """
        return {
            'host': self.get_secret('DATABASE_HOST') or 'localhost',
            'port': int(self.get_secret('DATABASE_PORT') or '3306'),
            'database': self.get_secret('MYSQL_DATABASE') or 'inventory_service_db',
            'user': self.get_secret('MYSQL_USER') or 'admin',
            'password': self.get_secret('MYSQL_PASSWORD') or 'admin123',
            'root_password': self.get_secret('MYSQL_ROOT_PASSWORD') or 'inventory_root_pass_123'
        }
    
    def get_jwt_config(self) -> Dict[str, Any]:
        """
        Get JWT configuration from secrets
        
        Returns:
            Dictionary with JWT configuration
        """
        return {
            'secret': self.get_secret('JWT_SECRET') or '8tDBDMcpxroHoHjXjk8xp/uAn8rzD4y8ZZremFkC4gI='
        }
    
    def get_service_urls(self) -> Dict[str, str]:
        """
        Get external service URLs from configuration
        
        Returns:
            Dictionary with service URLs
        """
        return {
            'product_service': self.get_secret('PRODUCT_SERVICE_URL') or 'http://localhost:8003',
            'product_service_health': self.get_secret('PRODUCT_SERVICE_HEALTH_URL') or 'http://localhost:8003/health'
        }


# Singleton instance
_secret_manager = None


def get_secret_manager() -> DaprSecretManager:
    """Get singleton secret manager instance"""
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = DaprSecretManager()
    return _secret_manager


# Convenience functions for direct access
def get_database_config() -> Dict[str, Any]:
    """Get database configuration"""
    return get_secret_manager().get_database_config()


def get_jwt_config() -> Dict[str, Any]:
    """Get JWT configuration"""
    return get_secret_manager().get_jwt_config()


def get_service_urls() -> Dict[str, str]:
    """Get service URLs"""
    return get_secret_manager().get_service_urls()
