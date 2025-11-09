"""
Dapr Service Client
Handles Dapr service-to-service invocation
"""
import logging
from typing import Dict, Any, Optional
from dapr.clients import DaprClient

logger = logging.getLogger(__name__)


class DaprServiceClient:
    """Client for Dapr service-to-service invocation"""
    
    def __init__(self):
        self.dapr_client = DaprClient()
    
    def invoke_service(
        self, 
        service_name: str, 
        method: str, 
        data: Optional[Dict[str, Any]] = None,
        http_verb: str = 'POST'
    ) -> Optional[Dict[str, Any]]:
        """
        Invoke another service via Dapr
        
        Args:
            service_name: Target service app-id
            method: HTTP method path (e.g., '/api/v1/products/123')
            data: Request payload
            http_verb: HTTP verb (GET, POST, PUT, DELETE)
            
        Returns:
            Response data or None if error
        """
        try:
            response = self.dapr_client.invoke_method(
                app_id=service_name,
                method_name=method,
                data=data,
                http_verb=http_verb
            )
            
            if response:
                return response.json()
            
            return None
            
        except Exception as e:
            logger.error(f"Error invoking service {service_name}/{method}: {str(e)}")
            return None
    
    def invoke_get(self, service_name: str, method: str) -> Optional[Dict[str, Any]]:
        """Convenience method for GET requests"""
        return self.invoke_service(service_name, method, http_verb='GET')
    
    def invoke_post(self, service_name: str, method: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convenience method for POST requests"""
        return self.invoke_service(service_name, method, data, http_verb='POST')
    
    def invoke_put(self, service_name: str, method: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convenience method for PUT requests"""
        return self.invoke_service(service_name, method, data, http_verb='PUT')
    
    def invoke_delete(self, service_name: str, method: str) -> Optional[Dict[str, Any]]:
        """Convenience method for DELETE requests"""
        return self.invoke_service(service_name, method, http_verb='DELETE')


# Singleton instance
_dapr_service_client = None


def get_dapr_service_client() -> DaprServiceClient:
    """Get singleton Dapr service client instance"""
    global _dapr_service_client
    if _dapr_service_client is None:
        _dapr_service_client = DaprServiceClient()
    return _dapr_service_client
