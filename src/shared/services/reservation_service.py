"""
Reservation Service - Business logic for reservation management
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from uuid import uuid4

from src.shared.models import Reservation, ReservationStatus, StockMovementType
from src.shared.repositories import ReservationRepository, InventoryRepository

logger = logging.getLogger(__name__)


class ReservationService:
    """Business logic for reservation management"""
    
    def __init__(self):
        self.reservation_repo = ReservationRepository()
        self.inventory_repo = InventoryRepository()
    
    def create_reservation(self, sku: str, order_id: str, quantity: int, customer_id: str = None, ttl_minutes: int = 30) -> Dict[str, Any]:
        """Create a new reservation"""
        try:
            # Check availability first
            inventory_item = self.inventory_repo.get_by_sku(sku)
            if not inventory_item:
                raise ValueError(f"Product with SKU {sku} not found")
            
            if inventory_item.quantity_available < quantity:
                raise ValueError("Insufficient stock")
            
            # Create reservation
            expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
            reservation = Reservation(
                id=str(uuid4()),
                sku=sku,
                order_id=order_id,
                quantity=quantity,
                status=ReservationStatus.PENDING,
                expires_at=expires_at
            )
            
            created_reservation = self.reservation_repo.create(reservation)
            
            # Update stock
            self.inventory_repo.update_stock(
                sku=sku,
                quantity_change=quantity,
                movement_type=StockMovementType.RESERVED,
                reference=order_id,
                reason=f"Reserved for order {order_id}"
            )
            
            logger.info(f"Created reservation {created_reservation.id} for order {order_id}")
            return created_reservation.to_dict()
            
        except Exception as e:
            logger.error(f"Error creating reservation: {str(e)}")
            raise
    
    def get_reservation(self, reservation_id: str) -> Optional[Dict[str, Any]]:
        """Get reservation by ID"""
        try:
            reservation = self.reservation_repo.get_by_id(reservation_id)
            return reservation.to_dict() if reservation else None
        except Exception as e:
            logger.error(f"Error getting reservation {reservation_id}: {str(e)}")
            raise
    
    def confirm_reservation(self, reservation_id: str, order_id: str) -> bool:
        """Confirm a reservation"""
        try:
            reservation = self.reservation_repo.get_by_id(reservation_id)
            if not reservation:
                raise ValueError("Reservation not found")
            
            if reservation.order_id != order_id:
                raise ValueError("Order ID mismatch")
            
            if reservation.status != ReservationStatus.PENDING:
                raise ValueError("Reservation is not pending")
            
            if reservation.is_expired:
                raise ValueError("Reservation has expired")
            
            # Update status
            self.reservation_repo.update_status(reservation_id, ReservationStatus.CONFIRMED)
            
            # Convert reserved stock to sold
            self.inventory_repo.update_stock(
                sku=reservation.sku,
                quantity_change=reservation.quantity,
                movement_type=StockMovementType.OUT,
                reference=order_id,
                reason=f"Sold for order {order_id}"
            )
            
            logger.info(f"Confirmed reservation {reservation_id} for order {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error confirming reservation {reservation_id}: {str(e)}")
            raise
    
    def cancel_reservation(self, reservation_id: str) -> bool:
        """Cancel a reservation"""
        try:
            reservation = self.reservation_repo.get_by_id(reservation_id)
            if not reservation:
                return False
            
            # Cancel reservation
            updated_reservation = self.reservation_repo.cancel(reservation_id)
            if not updated_reservation:
                return False
            
            # Release stock if it was pending
            if reservation.status == ReservationStatus.PENDING:
                self.inventory_repo.update_stock(
                    sku=reservation.sku,
                    quantity_change=reservation.quantity,
                    movement_type=StockMovementType.RELEASED,
                    reference=reservation.order_id,
                    reason=f"Released cancelled reservation for order {reservation.order_id}"
                )
            
            logger.info(f"Cancelled reservation {reservation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling reservation {reservation_id}: {str(e)}")
            raise
    
    def search_reservations(self, **kwargs):
        """Search reservations with filters - returns list for compatibility with tests"""
        try:
            reservations, total = self.reservation_repo.search(**kwargs)
            # Return just the list for test compatibility
            return [r.to_dict() for r in reservations]
            
        except Exception as e:
            logger.error(f"Error searching reservations: {str(e)}")
            raise

    def search_reservations_with_count(self, **kwargs) -> tuple[List[Dict[str, Any]], int]:
        """Search reservations with filters - returns tuple with count"""
        try:
            reservations, total = self.reservation_repo.search(**kwargs)
            return [r.to_dict() for r in reservations], total
            
        except Exception as e:
            logger.error(f"Error searching reservations: {str(e)}")
            raise
    
    def confirm_reservations(self, reservation_ids: List[str], order_id: str) -> List[dict]:
        """Bulk confirm reservations"""
        try:
            results = []
            for res_id in reservation_ids:
                try:
                    success = self.confirm_reservation(res_id, order_id)
                    results.append({'reservation_id': res_id, 'success': success})
                except Exception as e:
                    results.append({'reservation_id': res_id, 'success': False, 'error': str(e)})
            
            return results
            
        except Exception as e:
            logger.error(f"Error bulk confirming reservations: {str(e)}")
            raise
    
    def process_expired_reservations(self) -> Dict[str, Any]:
        """Process expired reservations"""
        try:
            expired_reservations = self.reservation_repo.get_expired_reservations()
            processed_count = 0
            
            for reservation in expired_reservations:
                try:
                    # Update status to expired
                    self.reservation_repo.update_status(reservation.id, ReservationStatus.EXPIRED)
                    
                    # Release stock
                    self.inventory_repo.update_stock(
                        sku=reservation.sku,
                        quantity_change=reservation.quantity,
                        movement_type=StockMovementType.RELEASED,
                        reference=reservation.order_id,
                        reason=f"Released expired reservation for order {reservation.order_id}"
                    )
                    
                    processed_count += 1
                    logger.info(f"Processed expired reservation {reservation.id}")
                    
                except Exception as e:
                    logger.error(f"Error processing expired reservation {reservation.id}: {e}")
            
            return {
                'processed_count': processed_count,
                'processed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing expired reservations: {str(e)}")
            raise

    def cleanup_old_reservations(self) -> int:
        """Cleanup old expired reservations (background task)"""
        try:
            # Delete reservations expired more than 24 hours ago
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            count = self.reservation_repo.delete_expired(cutoff_time)
            
            if count > 0:
                logger.info(f"Cleaned up {count} old reservations")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up old reservations: {str(e)}")
            raise

    def reserve_stock_for_order(self, order_id: str, items: List[Dict[str, Any]], 
                     ttl_minutes: int = 30) -> Dict[str, Any]:
        """
        Reserve stock for an order
        
        Args:
            order_id: Order identifier
            items: List of {'sku': str, 'quantity': int}
            ttl_minutes: Reservation TTL in minutes
            
        Returns:
            Dict with reservation details
        """
        try:
            # Create reservations
            reservations = []
            expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
            
            for item in items:
                sku = item['sku']
                quantity = item['quantity']
                
                # Check availability first
                inventory_item = self.inventory_repo.get_by_sku(sku)
                if not inventory_item or inventory_item.quantity_available < quantity:
                    return {
                        'success': False,
                        'message': f'Insufficient stock for SKU {sku}',
                        'sku': sku,
                        'requested': quantity,
                        'available': inventory_item.quantity_available if inventory_item else 0
                    }
                
                # Create reservation record
                reservation = Reservation(
                    id=str(uuid4()),
                    order_id=order_id,
                    sku=sku,
                    quantity=quantity,
                    status=ReservationStatus.PENDING,
                    expires_at=expires_at
                )
                
                # Save reservation
                reservation = self.reservation_repo.create(reservation)
                
                # Update inventory (reserve stock)
                success = self.inventory_repo.update_stock(
                    sku=sku,
                    quantity_change=quantity,
                    movement_type=StockMovementType.RESERVED,
                    reference=order_id,
                    reason=f"Stock reserved for order {order_id}"
                )
                
                if not success:
                    # Rollback reservations if stock update fails
                    logger.error(f"Failed to reserve stock for SKU {sku}")
                    # TODO: Implement proper rollback mechanism
                    raise Exception(f"Failed to reserve stock for SKU {sku}")
                
                reservations.append(reservation)
                logger.info(f"Reserved {quantity} units of SKU {sku} for order {order_id}")
            
            return {
                'success': True,
                'reservations': [r.to_dict() for r in reservations],
                'expires_at': expires_at.isoformat(),
                'message': f'Successfully reserved stock for {len(items)} items'
            }
            
        except Exception as e:
            logger.error(f"Error reserving stock for order {order_id}: {str(e)}")
            raise

    def confirm_reservations_bulk(self, reservation_ids: List[str], order_id: str = None) -> List[dict]:
        """
        Bulk confirm reservations
        
        Args:
            reservation_ids: List of reservation IDs to confirm
            order_id: Order identifier (optional - each reservation uses its own order_id if not provided)
            
        Returns:
            List of confirmation results
        """
        try:
            results = []
            
            for res_id in reservation_ids:
                try:
                    if order_id is None:
                        # Use the reservation's own order_id
                        reservation = self.reservation_repo.get_by_id(res_id)
                        if reservation:
                            success = self.confirm_reservation(res_id, reservation.order_id)
                        else:
                            success = False
                    else:
                        # Use provided order_id for all reservations
                        success = self.confirm_reservation(res_id, order_id)
                    
                    results.append({'reservation_id': res_id, 'success': success})
                    
                except Exception as e:
                    results.append({'reservation_id': res_id, 'success': False, 'error': str(e)})
                    logger.error(f"Error confirming reservation {res_id}: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk confirm reservations: {str(e)}")
            # Return error result for all reservations
            return [{'reservation_id': res_id, 'success': False, 'error': str(e)} for res_id in reservation_ids]

    def expire_reservations(self, reservation_ids: List[str] = None) -> Dict[str, Any]:
        """
        Expire specific reservations or process all expired reservations
        
        Args:
            reservation_ids: List of reservation IDs to expire (optional)
            
        Returns:
            Dict with expiration results
        """
        try:
            if reservation_ids is None:
                # Process all expired reservations (for compatibility with tests)
                return self.process_expired_reservations()
            
            # Expire specific reservations
            results = []
            
            for res_id in reservation_ids:
                try:
                    reservation = self.reservation_repo.get_by_id(res_id)
                    if not reservation:
                        results.append({'reservation_id': res_id, 'success': False, 'error': 'Not found'})
                        continue
                    
                    # Update status to expired
                    self.reservation_repo.update_status(res_id, ReservationStatus.EXPIRED)
                    
                    # Release stock if it was reserved
                    if reservation.status == ReservationStatus.PENDING:
                        self.inventory_repo.update_stock(
                            sku=reservation.sku,
                            quantity_change=reservation.quantity,
                            movement_type=StockMovementType.RELEASED,
                            reference=reservation.order_id,
                            reason=f"Released manually expired reservation for order {reservation.order_id}"
                        )
                    
                    results.append({'reservation_id': res_id, 'success': True})
                    logger.info(f"Manually expired reservation {res_id}")
                    
                except Exception as e:
                    results.append({'reservation_id': res_id, 'success': False, 'error': str(e)})
                    logger.error(f"Error expiring reservation {res_id}: {e}")
            
            return {
                'results': results,
                'total_processed': len(reservation_ids),
                'successful': len([r for r in results if r['success']]),
                'failed': len([r for r in results if not r['success']]),
                'expired_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error expiring reservations: {str(e)}")
            raise
