"""
Events module for Inventory Service
Handles event publishing and consuming via Dapr
"""

from .publisher import event_publisher

__all__ = ['event_publisher']
