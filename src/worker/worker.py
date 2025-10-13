"""
Inventory Service Worker - Message Consumer
Processes async events from message broker
"""
import os
import sys
import signal
import asyncio
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
from src.shared.messaging.message_broker_factory import MessageBrokerFactory
from src.worker.handlers.handler_registry import get_handler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class InventoryWorker:
    """Worker process for consuming and processing messages"""
    
    def __init__(self):
        self.broker = None
        self.is_running = True
        
    async def process_message(self, message_data: dict, correlation_id: str = None):
        """
        Process incoming message by routing to appropriate handler
        
        Args:
            message_data: The message payload containing eventType and data
            correlation_id: Optional correlation ID for tracing
        """
        try:
            event_type = message_data.get('eventType')
            event_data = message_data.get('data', {})
            
            if not event_type:
                logger.error(f"Message missing eventType field. CorrelationId: {correlation_id}")
                return
            
            # Get handler for this event type
            handler = get_handler(event_type)
            
            if handler:
                logger.info(f"Processing event: {event_type}. CorrelationId: {correlation_id}")
                await handler(event_data, correlation_id)
            else:
                logger.warning(f"No handler registered for event type: {event_type}. CorrelationId: {correlation_id}")
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}. CorrelationId: {correlation_id}")
            raise
    
    async def start(self):
        """Start the worker and begin consuming messages"""
        try:
            logger.info("Inventory Worker starting...")
            
            # Create message broker instance
            broker_type = os.getenv('MESSAGE_BROKER_TYPE', 'rabbitmq')
            queue_name = os.getenv('MESSAGE_BROKER_QUEUE', 'inventory-service.queue')
            
            logger.info(f"Initializing {broker_type} message broker, queue: {queue_name}")
            
            self.broker = MessageBrokerFactory.create(broker_type)
            
            # Connect to broker
            await self.broker.connect()
            
            # Start consuming messages
            logger.info(f"Worker started, consuming from queue: {queue_name}")
            await self.broker.consume(queue_name, self.process_message)
            
        except Exception as e:
            logger.error(f"Failed to start worker: {str(e)}")
            raise
    
    async def stop(self):
        """Gracefully stop the worker"""
        logger.info("Stopping Inventory Worker...")
        self.is_running = False
        
        if self.broker:
            try:
                await self.broker.disconnect()
                logger.info("Message broker disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting broker: {str(e)}")
        
        logger.info("Inventory Worker stopped")


# Global worker instance
worker = None


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    if worker:
        asyncio.create_task(worker.stop())


async def main():
    """Main entry point for the worker"""
    global worker
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start worker
    worker = InventoryWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Worker error: {str(e)}")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
