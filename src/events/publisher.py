"""
Dapr Event Publisher for Inventory Service
Synchronous Flask-compatible event publishing using Dapr SDK
"""

from dapr.clients import DaprClient
from flask import current_app
import json
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

# Import trace context for W3C Trace Context support
from src.api.middlewares.trace_context import get_trace_id


class InventoryEventPublisher:
    """
    Synchronous Dapr event publisher for Flask-based inventory service.
    Handles publishing inventory-related events to RabbitMQ via Dapr.
    """
    
    def __init__(self):
        self.pubsub_name = "inventory-pubsub"
        self.service_name = "inventory-service"
    
    def _build_event_payload(self, event_type: str, data: Dict[str, Any], 
                            correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Build CloudEvents-compliant event payload"""
        return {
            "specversion": "1.0",
            "type": event_type,
            "source": self.service_name,
            "id": str(uuid.uuid4()),
            "time": datetime.utcnow().isoformat() + "Z",
            "datacontenttype": "application/json",
            "data": data,
            "correlationid": correlation_id or str(uuid.uuid4())
        }
    
    def publish_event(self, event_type: str, data: Dict[str, Any], 
                     correlation_id: Optional[str] = None) -> bool:
        """
        Publish event to Dapr pub/sub synchronously.
        
        Args:
            event_type: Event type/topic name (e.g., 'inventory.stock.updated')
            data: Event payload data
            correlation_id: Optional correlation ID for tracing (defaults to current trace_id)
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        try:
            # Use trace_id from context if correlation_id not provided
            if correlation_id is None:
                correlation_id = get_trace_id()
            
            event_payload = self._build_event_payload(event_type, data, correlation_id)
            
            # Synchronous Dapr client call - blocks for ~5-20ms
            with DaprClient() as client:
                client.publish_event(
                    pubsub_name=self.pubsub_name,
                    topic_name=event_type,
                    data=json.dumps(event_payload),
                    data_content_type="application/json"
                )
            
            current_app.logger.info(
                f"✅ Published event: {event_type}",
                extra={
                    "eventType": event_type,
                    "correlationId": correlation_id,
                    "service": self.service_name
                }
            )
            return True
            
        except Exception as e:
            current_app.logger.error(
                f"❌ Failed to publish event: {event_type} - {str(e)}",
                extra={
                    "eventType": event_type,
                    "error": str(e),
                    "correlationId": correlation_id
                }
            )
            return False
    
    # =========================================================================
    # Inventory Stock Events
    # =========================================================================
    
    def publish_stock_updated(self, product_id: str, quantity: int, 
                             warehouse: str = "default",
                             correlation_id: Optional[str] = None) -> bool:
        """Publish inventory.stock.updated event"""
        data = {
            "productId": product_id,
            "quantity": quantity,
            "warehouse": warehouse,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        return self.publish_event("inventory.stock.updated", data, correlation_id)
    
    def publish_stock_reserved(self, product_id: str, quantity: int, 
                              order_id: str, reservation_id: str,
                              correlation_id: Optional[str] = None) -> bool:
        """Publish inventory.stock.reserved event"""
        data = {
            "productId": product_id,
            "quantity": quantity,
            "orderId": order_id,
            "reservationId": reservation_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        return self.publish_event("inventory.stock.reserved", data, correlation_id)
    
    def publish_stock_released(self, product_id: str, quantity: int,
                              order_id: str, reason: str,
                              correlation_id: Optional[str] = None) -> bool:
        """Publish inventory.stock.released event"""
        data = {
            "productId": product_id,
            "quantity": quantity,
            "orderId": order_id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        return self.publish_event("inventory.stock.released", data, correlation_id)
    
    def publish_low_stock_alert(self, product_id: str, current_quantity: int,
                               threshold: int, correlation_id: Optional[str] = None) -> bool:
        """Publish inventory.low.stock event"""
        data = {
            "productId": product_id,
            "currentQuantity": current_quantity,
            "threshold": threshold,
            "severity": "warning",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        return self.publish_event("inventory.low.stock", data, correlation_id)
    
    def publish_out_of_stock_alert(self, product_id: str, 
                                   correlation_id: Optional[str] = None) -> bool:
        """Publish inventory.out.of.stock event"""
        data = {
            "productId": product_id,
            "severity": "critical",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        return self.publish_event("inventory.out.of.stock", data, correlation_id)
    
    def publish_inventory_created(self, product_id: str, initial_quantity: int,
                                 correlation_id: Optional[str] = None) -> bool:
        """Publish inventory.created event"""
        data = {
            "productId": product_id,
            "initialQuantity": initial_quantity,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        return self.publish_event("inventory.created", data, correlation_id)


# Global singleton instance
event_publisher = InventoryEventPublisher()
