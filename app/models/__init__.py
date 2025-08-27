from app import db
from datetime import datetime, timedelta
from enum import Enum
import uuid
from sqlalchemy import DECIMAL


class ReservationStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"  # Add ACTIVE status
    CONFIRMED = "confirmed"
    RELEASED = "released"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class StockMovementType(Enum):
    IN = "in"
    OUT = "out"
    RESERVED = "reserved"
    RELEASED = "released"
    ADJUSTMENT = "adjustment"


class InventoryItem(db.Model):
    """Inventory item model"""
    __tablename__ = 'inventory_items'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(100), unique=True, nullable=False, index=True)
    product_id = db.Column(db.String(36), nullable=False, index=True)  # UUID from product service
    quantity_available = db.Column(db.Integer, default=0, nullable=False)
    quantity_reserved = db.Column(db.Integer, default=0, nullable=False)
    reorder_level = db.Column(db.Integer, default=10, nullable=False)
    max_stock = db.Column(db.Integer, default=1000, nullable=False)
    cost_per_unit = db.Column(DECIMAL(10, 2), default=0.0)
    last_restocked = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    reservations = db.relationship('Reservation', backref='inventory_item', lazy=True)
    stock_movements = db.relationship('StockMovement', backref='inventory_item', lazy=True)
    
    def __repr__(self):
        return f'<InventoryItem {self.sku}>'
    
    @property
    def total_quantity(self):
        """Total quantity including reserved stock"""
        return self.quantity_available + self.quantity_reserved
    
    @property
    def is_low_stock(self):
        """Check if item is below reorder level"""
        return self.quantity_available <= self.reorder_level
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'sku': self.sku,
            'product_id': self.product_id,
            'quantity_available': self.quantity_available,
            'quantity_reserved': self.quantity_reserved,
            'total_quantity': self.total_quantity,
            'reorder_level': self.reorder_level,
            'max_stock': self.max_stock,
            'cost_per_unit': float(self.cost_per_unit) if self.cost_per_unit else 0.0,
            'is_low_stock': self.is_low_stock,
            'last_restocked': self.last_restocked.isoformat() if self.last_restocked else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Reservation(db.Model):
    """Stock reservation model"""
    __tablename__ = 'reservations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = db.Column(db.String(36), nullable=False, index=True)
    sku = db.Column(db.String(100), db.ForeignKey('inventory_items.sku'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(ReservationStatus), default=ReservationStatus.PENDING, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Reservation {self.id}>'
    
    @property
    def is_expired(self):
        """Check if reservation has expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def product_id(self):
        """Get product_id from associated inventory item"""
        from app.models import InventoryItem
        item = InventoryItem.query.filter_by(sku=self.sku).first()
        return item.product_id if item else None
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'sku': self.sku,
            'product_id': self.product_id,  # Add product_id property
            'quantity': self.quantity,
            'status': self.status.value,
            'expires_at': self.expires_at.isoformat(),
            'is_expired': self.is_expired,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class StockMovement(db.Model):
    """Stock movement history model"""
    __tablename__ = 'stock_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(100), db.ForeignKey('inventory_items.sku'), nullable=False)
    movement_type = db.Column(db.Enum(StockMovementType), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    reference = db.Column(db.String(255), nullable=True)  # Order ID, Restock ID, etc.
    reason = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.String(100), default='system', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<StockMovement {self.sku} {self.movement_type.value} {self.quantity}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'sku': self.sku,
            'movement_type': self.movement_type.value,
            'quantity': self.quantity,
            'reference': self.reference,
            'reason': self.reason,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat()
        }
