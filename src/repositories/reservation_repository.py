"""
Reservation Repository Implementation
"""

from typing import List, Optional
from src.database import db
from src.models import Reservation, ReservationStatus
from datetime import datetime
from sqlalchemy import and_
from .base import ReservationRepositoryInterface


class ReservationRepository(ReservationRepositoryInterface):
    """Concrete implementation of reservation repository"""
    
    def create(self, reservation: Reservation) -> Reservation:
        """Create new reservation"""
        db.session.add(reservation)
        db.session.commit()
        return reservation
    
    def get_by_id(self, reservation_id: str) -> Optional[Reservation]:
        """Get reservation by ID"""
        return Reservation.query.filter_by(id=reservation_id).first()
    
    def get_by_order_id(self, order_id: str) -> List[Reservation]:
        """Get reservations by order ID"""
        return Reservation.query.filter_by(order_id=order_id).all()
    
    def update_status(self, reservation_id: str, status: ReservationStatus) -> Optional[Reservation]:
        """Update reservation status"""
        reservation = self.get_by_id(reservation_id)
        if not reservation:
            return None
        
        reservation.status = status
        reservation.updated_at = datetime.utcnow()
        db.session.commit()
        return reservation
    
    def get_expired_reservations(self) -> List[Reservation]:
        """Get expired pending reservations"""
        return Reservation.query.filter(
            and_(
                Reservation.status == ReservationStatus.PENDING,
                Reservation.expires_at < datetime.utcnow()
            )
        ).all()
    
    def delete_expired(self, expired_before: datetime) -> int:
        """Delete expired reservations"""
        count = Reservation.query.filter(
            and_(
                Reservation.status == ReservationStatus.EXPIRED,
                Reservation.updated_at < expired_before
            )
        ).delete()
        db.session.commit()
        return count

    def cancel(self, reservation_id: str) -> Optional[Reservation]:
        """Cancel a reservation"""
        reservation = self.get_by_id(reservation_id)
        if not reservation:
            return None
        
        reservation.status = ReservationStatus.CANCELLED
        reservation.updated_at = datetime.utcnow()
        db.session.commit()
        return reservation

    def bulk_confirm(self, reservation_ids: List[str]) -> List[dict]:
        """Bulk confirm reservations"""
        results = []
        for res_id in reservation_ids:
            try:
                updated = self.update_status(res_id, ReservationStatus.CONFIRMED)
                if updated:
                    results.append({'reservation_id': res_id, 'success': True})
                else:
                    results.append({'reservation_id': res_id, 'success': False, 'error': 'Not found'})
            except Exception as e:
                results.append({'reservation_id': res_id, 'success': False, 'error': str(e)})
        
        return results

    def search(self, **kwargs) -> tuple[List[Reservation], int]:
        """Search reservations with filters"""
        query = Reservation.query
        
        if 'customer_id' in kwargs and kwargs['customer_id']:
            # Assuming we might add customer_id field in future
            pass
        
        if 'order_id' in kwargs and kwargs['order_id']:
            query = query.filter(Reservation.order_id == kwargs['order_id'])
        
        if 'status' in kwargs and kwargs['status']:
            query = query.filter(Reservation.status == ReservationStatus(kwargs['status']))
        
        total = query.count()
        page = kwargs.get('page', 1)
        per_page = kwargs.get('per_page', 20)
        
        items = query.paginate(page=page, per_page=per_page, error_out=False).items
        return items, total
