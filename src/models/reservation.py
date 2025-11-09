"""
Reservation Model
"""

from src.database import db
from datetime import datetime
import uuid
from .enums import ReservationStatus


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
        from src.models.inventory_item import InventoryItem
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
