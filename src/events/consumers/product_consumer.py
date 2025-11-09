"""
Product Event Consumer for Inventory Service
Handles events from product-service
"""

from flask import current_app
from typing import Dict, Any
from src.shared.database import db
from src.shared.models.inventory import Inventory
from src.events.publisher import event_publisher


def handle_product_created(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle product.created event from product-service.
    Initialize inventory record for the new product.
    
    Event payload:
    {
        "data": {
            "productId": "string",
            "name": "string",
            "sku": "string",
            "price": float
        },
        "correlationid": "string"
    }
    """
    try:
        data = event_data.get('data', {})
        product_id = data.get('productId')
        correlation_id = event_data.get('correlationid')
        
        if not product_id:
            raise ValueError("Missing productId in event data")
        
        current_app.logger.info(
            f"📦 Handling product.created for product: {product_id}",
            extra={"correlationId": correlation_id}
        )
        
        # Check if inventory already exists
        existing_inventory = Inventory.query.filter_by(product_id=product_id).first()
        if existing_inventory:
            current_app.logger.warning(
                f"⚠️ Inventory already exists for product: {product_id}",
                extra={"correlationId": correlation_id}
            )
            return {"status": "skipped", "message": "Inventory already exists"}
        
        # Create new inventory record with zero initial stock
        new_inventory = Inventory(
            product_id=product_id,
            quantity=0,  # Start with zero, admin will add stock later
            reserved_quantity=0,
            warehouse="default",
            low_stock_threshold=10
        )
        
        db.session.add(new_inventory)
        db.session.commit()
        
        current_app.logger.info(
            f"✅ Created inventory for product: {product_id}",
            extra={"correlationId": correlation_id}
        )
        
        # Publish inventory.created event
        event_publisher.publish_inventory_created(
            product_id=product_id,
            initial_quantity=0,
            correlation_id=correlation_id
        )
        
        return {
            "status": "success",
            "message": f"Inventory created for product {product_id}"
        }
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"❌ Error handling product.created: {str(e)}",
            extra={"error": str(e), "correlationId": event_data.get('correlationid')}
        )
        return {"status": "error", "message": str(e)}


def handle_product_updated(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle product.updated event from product-service.
    Update product reference information in inventory.
    
    Event payload:
    {
        "data": {
            "productId": "string",
            "name": "string",
            "sku": "string",
            "price": float
        },
        "correlationid": "string"
    }
    """
    try:
        data = event_data.get('data', {})
        product_id = data.get('productId')
        correlation_id = event_data.get('correlationid')
        
        if not product_id:
            raise ValueError("Missing productId in event data")
        
        current_app.logger.info(
            f"📝 Handling product.updated for product: {product_id}",
            extra={"correlationId": correlation_id}
        )
        
        # Find inventory record
        inventory = Inventory.query.filter_by(product_id=product_id).first()
        if not inventory:
            current_app.logger.warning(
                f"⚠️ Inventory not found for product: {product_id}",
                extra={"correlationId": correlation_id}
            )
            return {"status": "not_found", "message": "Inventory not found"}
        
        # Update product metadata if needed (SKU, etc.)
        # For now, just log the update
        db.session.commit()
        
        current_app.logger.info(
            f"✅ Updated inventory metadata for product: {product_id}",
            extra={"correlationId": correlation_id}
        )
        
        return {
            "status": "success",
            "message": f"Inventory updated for product {product_id}"
        }
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"❌ Error handling product.updated: {str(e)}",
            extra={"error": str(e), "correlationId": event_data.get('correlationid')}
        )
        return {"status": "error", "message": str(e)}


def handle_product_deleted(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle product.deleted event from product-service.
    Archive or delete inventory record.
    
    Event payload:
    {
        "data": {
            "productId": "string"
        },
        "correlationid": "string"
    }
    """
    try:
        data = event_data.get('data', {})
        product_id = data.get('productId')
        correlation_id = event_data.get('correlationid')
        
        if not product_id:
            raise ValueError("Missing productId in event data")
        
        current_app.logger.info(
            f"🗑️ Handling product.deleted for product: {product_id}",
            extra={"correlationId": correlation_id}
        )
        
        # Find inventory record
        inventory = Inventory.query.filter_by(product_id=product_id).first()
        if not inventory:
            current_app.logger.warning(
                f"⚠️ Inventory not found for product: {product_id}",
                extra={"correlationId": correlation_id}
            )
            return {"status": "not_found", "message": "Inventory not found"}
        
        # Soft delete or archive (don't actually delete to preserve history)
        inventory.is_active = False
        db.session.commit()
        
        current_app.logger.info(
            f"✅ Archived inventory for deleted product: {product_id}",
            extra={"correlationId": correlation_id}
        )
        
        return {
            "status": "success",
            "message": f"Inventory archived for product {product_id}"
        }
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"❌ Error handling product.deleted: {str(e)}",
            extra={"error": str(e), "correlationId": event_data.get('correlationid')}
        )
        return {"status": "error", "message": str(e)}
