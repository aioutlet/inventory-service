"""
Message Broker Publisher Service
Publishes events to message broker service via HTTP using AWS EventBridge pattern
"""
import os
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


class MessageBrokerPublisher:
    """
    Publisher for sending events to message broker service
    Follows AWS EventBridge pattern with source, eventType, and structured data
    """
    
    def __init__(self):
        self.broker_url = os.getenv('MESSAGE_BROKER_SERVICE_URL', 'http://localhost:4000')
        self.api_key = os.getenv('MESSAGE_BROKER_API_KEY', '')
        self.service_name = os.getenv('NAME', 'inventory-service')
        self.event_version = os.getenv('EVENT_VERSION', '1.0')
        
    async def publish(
        self, 
        event_type: str, 
        data: Dict[str, Any], 
        correlation_id: Optional[str] = None,
        event_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Publish an event to the message broker service using EventBridge pattern
        
        Args:
            event_type: The type of event (e.g., 'inventory.reserved')
            data: The event payload
            correlation_id: Optional correlation ID for tracing
            event_id: Optional event-specific unique identifier
            metadata: Optional additional context
        """
        try:
            # Build EventBridge-compliant message
            payload = {
                'source': self.service_name,
                'eventType': event_type,
                'eventVersion': self.event_version,
                'eventId': event_id or str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'data': data,
                'metadata': metadata or {},
                'correlationId': correlation_id
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-Correlation-ID': correlation_id or ''
            }
            
            if self.api_key:
                headers['X-API-Key'] = self.api_key
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.broker_url}/api/v1/publish",
                    json=payload,
                    headers=headers,
                    timeout=5.0
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Published event: {event_type}. CorrelationId: {correlation_id}")
                else:
                    logger.error(f"Failed to publish event: {event_type}. Status: {response.status_code}. CorrelationId: {correlation_id}")
                    
        except Exception as e:
            logger.error(f"Error publishing event: {str(e)}. CorrelationId: {correlation_id}")
            # Don't raise - publishing failures shouldn't break main flow


# Singleton instance
_publisher = None


def get_publisher() -> MessageBrokerPublisher:
    """Get singleton publisher instance"""
    global _publisher
    if _publisher is None:
        _publisher = MessageBrokerPublisher()
    return _publisher
