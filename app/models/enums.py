"""
Model Enums
"""

from enum import Enum


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
