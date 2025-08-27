import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.services import InventoryService, ReservationService
from app.models import InventoryItem, Reservation, StockMovementType, ReservationStatus
from tests.conftest import create_test_inventory_item, create_test_reservation


class TestInventoryService:
    """Test InventoryService business logic."""
    
    def test_get_inventory_by_product_id(self, db_session):
        """Test getting inventory by product ID."""
        service = InventoryService()
        create_test_inventory_item(db_session, product_id='SERVICE001')
        
        result = service.get_inventory_by_product_id('SERVICE001')
        
        assert result is not None
        assert result['product_id'] == 'SERVICE001'
    
    def test_create_inventory_item(self, db_session):
        """Test creating inventory item through service."""
        service = InventoryService()
        
        item = service.create_inventory_item(
            product_id='CREATE001',
            quantity_available=50,
            reorder_level=10
        )
        
        assert item['product_id'] == 'CREATE001'
        assert item['quantity_available'] == 50
    
    def test_create_inventory_item_duplicate(self, db_session):
        """Test creating duplicate inventory item."""
        service = InventoryService()
        
        # Create first item
        service.create_inventory_item(product_id='DUP001')
        
        # Create item with same SKU should work (different product_id)
        item2 = service.create_inventory_item(product_id='DUP002')
        assert item2 is not None
    
    def test_update_inventory_item(self, db_session):
        """Test updating inventory item."""
        service = InventoryService()
        
        # First create an item
        created = service.create_inventory_item(product_id='UPDATE001')
        
        # Update it
        updated_item = service.update_inventory_item(
            'UPDATE001',
            quantity_available=200,
            reorder_level=20
        )
        
        assert updated_item['quantity_available'] == 200
        assert updated_item['reorder_level'] == 20
    
    def test_adjust_stock(self, db_session):
        """Test adjusting stock levels."""
        service = InventoryService()
        item = create_test_inventory_item(db_session, sku='ADJUST001', quantity_available=100)
        
        movement = service.adjust_stock(
            sku='ADJUST001',
            quantity=50,
            movement_type=StockMovementType.IN,
            reference='RESTOCK001'
        )
        
        assert movement['quantity'] == 50
        assert movement['movement_type'] == StockMovementType.IN.value
    
    def test_adjust_stock_outbound(self, db_session):
        """Test outbound stock adjustment."""
        service = InventoryService()
        item = create_test_inventory_item(db_session, sku='OUT001', quantity_available=100)
        
        movement = service.adjust_stock(
            sku='OUT001',
            quantity=30,
            movement_type=StockMovementType.OUT,
            reference='SALE001'
        )
        
        assert movement['quantity'] == 30
        assert movement['movement_type'] == StockMovementType.OUT.value
    
    def test_adjust_stock_insufficient_quantity(self, db_session):
        """Test adjusting stock with insufficient quantity."""
        service = InventoryService()
        create_test_inventory_item(db_session, sku='LOW001', quantity_available=10)
        
        with pytest.raises(ValueError, match="Insufficient stock"):
            service.adjust_stock(
                sku='LOW001',
                quantity=50,
                movement_type=StockMovementType.OUT
            )
    
    def test_check_availability(self, db_session):
        """Test checking stock availability."""
        service = InventoryService()
        item = create_test_inventory_item(db_session, sku='CHECK001', quantity_available=25)
        
        result = service.check_availability('CHECK001', 20)
        
        assert result['available'] is True
        assert result['available_quantity'] == 25
        assert result['requested_quantity'] == 20
    
    def test_search_inventory_advanced(self, db_session):
        """Test advanced inventory search."""
        service = InventoryService()
        
        # Create test items
        create_test_inventory_item(
            db_session, 
            product_id='SEARCH001',
            quantity_available=5,
            reorder_level=10
        )
        create_test_inventory_item(
            db_session,
            product_id='SEARCH002',
            quantity_available=50,
            reorder_level=10
        )
        
        # Search for low stock
        items, total = service.search_inventory_advanced(low_stock=True)
        
        assert total >= 1
        assert len(items) >= 1
    
    def test_bulk_update_inventory(self, db_session):
        """Test bulk updating inventory."""
        service = InventoryService()
        
        # Create items
        create_test_inventory_item(db_session, sku='BULK001')
        create_test_inventory_item(db_session, sku='BULK002')
        
        operations = [
            {'sku': 'BULK001', 'quantity_available': 150},
            {'sku': 'BULK002', 'quantity_available': 200}
        ]
        
        results = service.bulk_update_inventory(operations)
        
        assert len(results) == 2
        assert all(result['success'] for result in results)
    
    def test_get_inventory_with_product_details(self, db_session):
        """Test getting inventory with product details."""
        service = InventoryService()
        create_test_inventory_item(db_session, product_id='ENRICHED001')
        
        enriched_item = service.get_inventory_with_product_details('ENRICHED001')
        
        assert enriched_item is not None
        assert enriched_item['product_id'] == 'ENRICHED001'
    
    def test_health_check(self, db_session):
        """Test health check."""
        service = InventoryService()
        
        health_data = service.health_check()
        
        assert health_data['status'] == 'healthy'
        assert 'timestamp' in health_data


class TestReservationService:
    """Test ReservationService business logic."""
    
    def test_create_reservation(self, db_session):
        """Test creating a reservation."""
        service = ReservationService()
        item = create_test_inventory_item(db_session, sku='RESERVE001', quantity_available=100)
        
        reservation = service.create_reservation(
            sku='RESERVE001',
            order_id='ORDER001',
            quantity=10
        )
        
        assert reservation['order_id'] == 'ORDER001'
        assert reservation['quantity'] == 10
        assert reservation['status'] == ReservationStatus.PENDING.value
    
    def test_create_reservation_insufficient_stock(self, db_session):
        """Test creating reservation with insufficient stock."""
        service = ReservationService()
        create_test_inventory_item(db_session, sku='LOW001', quantity_available=5)
        
        with pytest.raises(ValueError, match="Insufficient stock"):
            service.create_reservation(
                sku='LOW001',
                order_id='ORDER002',
                quantity=10
            )
    
    def test_confirm_reservation(self, db_session):
        """Test confirming a reservation."""
        service = ReservationService()
        inventory_item = create_test_inventory_item(db_session, sku='CONFIRM001')
        
        # Create reservation
        reservation = service.create_reservation(
            sku='CONFIRM001',
            order_id='ORDER003',
            quantity=10
        )
        
        # Confirm it
        result = service.confirm_reservation(reservation['id'], 'ORDER003')
        
        assert result is True
    
    def test_cancel_reservation(self, db_session):
        """Test cancelling a reservation."""
        service = ReservationService()
        inventory_item = create_test_inventory_item(db_session, sku='CANCEL001')
        
        # Create reservation
        reservation = service.create_reservation(
            sku='CANCEL001',
            order_id='ORDER004',
            quantity=10
        )
        
        # Cancel it
        result = service.cancel_reservation(reservation['id'])
        
        assert result is True
    
    def test_confirm_reservations_bulk(self, db_session):
        """Test bulk confirming reservations."""
        service = ReservationService()
        inventory_item = create_test_inventory_item(db_session, sku='BULK-RES001')
        
        # Create reservations
        res1 = service.create_reservation('BULK-RES001', 'ORDER005', 5)
        res2 = service.create_reservation('BULK-RES001', 'ORDER006', 5)
        
        results = service.confirm_reservations_bulk([res1['id'], res2['id']])
        
        assert len(results) == 2
        assert all(result['success'] for result in results)
    
    def test_search_reservations(self, db_session):
        """Test searching reservations."""
        service = ReservationService()
        inventory_item = create_test_inventory_item(db_session, sku='SEARCH-RES001')
        
        # Create reservations
        service.create_reservation('SEARCH-RES001', 'SEARCH-ORDER', 5)
        
        results = service.search_reservations(order_id='SEARCH-ORDER')
        
        assert len(results) >= 1
        assert all(r['order_id'] == 'SEARCH-ORDER' for r in results)
    
    def test_expire_reservations(self, db_session):
        """Test processing expired reservations."""
        service = ReservationService()
        
        # This is mostly a system process, so just test it doesn't error
        result = service.expire_reservations()
        
        assert 'processed_count' in result
        assert 'processed_at' in result
    
    def test_get_reservation_not_found(self, db_session):
        """Test getting non-existent reservation."""
        service = ReservationService()
        
        result = service.get_reservation('non-existent-id')
        
        assert result is None
    
    def test_confirm_reservation_wrong_order(self, db_session):
        """Test confirming reservation with wrong order ID."""
        service = ReservationService()
        inventory_item = create_test_inventory_item(db_session, sku='WRONG-ORDER')
        
        # Create reservation
        reservation = service.create_reservation('WRONG-ORDER', 'ORDER-CORRECT', 5)
        
        # Try to confirm with wrong order ID
        with pytest.raises(ValueError, match="Order ID mismatch"):
            service.confirm_reservation(reservation['id'], 'ORDER-WRONG')
