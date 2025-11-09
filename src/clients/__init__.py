"""
Clients Module
Centralized exports for all external service clients
"""

# Dapr clients
from src.clients.dapr_service_client import DaprServiceClient, get_dapr_service_client
from src.clients.dapr_secret_manager import (
    DaprSecretManager, 
    get_secret_manager, 
    get_database_config, 
    get_jwt_config,
    get_service_urls
)

# HTTP clients
from src.clients.product_service_client import ProductServiceClient

__all__ = [
    # Dapr clients
    'DaprServiceClient',
    'get_dapr_service_client',
    'DaprSecretManager',
    'get_secret_manager',
    'get_database_config',
    'get_jwt_config',
    'get_service_urls',
    
    # HTTP clients
    'ProductServiceClient',
]
