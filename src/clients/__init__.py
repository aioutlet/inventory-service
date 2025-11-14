"""
Clients Module
Centralized exports for all external service clients
"""

# Dapr clients
from src.clients.dapr_secret_manager import (
    DaprSecretManager, 
    get_secret_manager, 
    get_database_config, 
    get_jwt_config
)

__all__ = [
    # Dapr clients
    'DaprSecretManager',
    'get_secret_manager',
    'get_database_config',
    'get_jwt_config',
]
