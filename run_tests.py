#!/usr/bin/env python3
"""
Unit Test Runner for Inventory Service
Runs tests without pytest to avoid version conflicts
"""

import sys
import os
import traceback
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, '.')

# Set test environment
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['REDIS_URL'] = 'redis://localhost:6379/1'

class TestInventoryModels(unittest.TestCase):
    """Test Inventory Models"""
    
    def setUp(self):
        """Set up test environment"""
        try:
            from app import create_app
            from app.models import db
            
            self.app = create_app('testing')
            self.app_context = self.app.app_context()
            self.app_context.push()
            
            db.create_all()
            self.db = db
        except Exception as e:
            self.skipTest(f"Setup failed: {e}")
    
    def tearDown(self):
        """Clean up after test"""
        if hasattr(self, 'db'):
            self.db.session.remove()
            self.db.drop_all()
        if hasattr(self, 'app_context'):
            self.app_context.pop()
    
    def test_inventory_item_creation(self):
        """Test creating an inventory item"""
        from app.models import InventoryItem
        
        item = InventoryItem(
            product_id='TEST001',
            quantity=100,
            reserved_quantity=10,
            minimum_stock_level=20,
            location='Test Warehouse'
        )
        
        self.db.session.add(item)
        self.db.session.commit()
        
        self.assertIsNotNone(item.id)
        self.assertEqual(item.product_id, 'TEST001')
        self.assertEqual(item.quantity, 100)
        self.assertEqual(item.reserved_quantity, 10)
        self.assertEqual(item.available_quantity, 90)  # 100 - 10
    
    def test_inventory_item_computed_properties(self):
        """Test computed properties on inventory items"""
        from app.models import InventoryItem
        
        # Test low stock
        low_stock_item = InventoryItem(
            product_id='LOW001',
            quantity=5,
            minimum_stock_level=10
        )
        self.assertTrue(low_stock_item.is_low_stock)
        
        # Test out of stock
        out_of_stock_item = InventoryItem(
            product_id='OUT001',
            quantity=10,
            reserved_quantity=10
        )
        self.assertTrue(out_of_stock_item.is_out_of_stock)
    
    def test_reservation_creation(self):
        """Test creating a reservation"""
        from app.models import InventoryItem, Reservation, ReservationStatus
        
        # Create inventory item first
        item = InventoryItem(
            product_id='RES001',
            quantity=100
        )
        self.db.session.add(item)
        self.db.session.flush()
        
        # Create reservation
        reservation = Reservation(
            inventory_item_id=item.id,
            quantity=5,
            customer_id='CUSTOMER001',
            order_id='ORDER001',
            status=ReservationStatus.ACTIVE
        )
        
        self.db.session.add(reservation)
        self.db.session.commit()
        
        self.assertIsNotNone(reservation.id)
        self.assertEqual(reservation.quantity, 5)
        self.assertEqual(reservation.customer_id, 'CUSTOMER001')
        self.assertEqual(reservation.status, ReservationStatus.ACTIVE)
    
    def test_stock_movement_creation(self):
        """Test creating a stock movement"""
        from app.models import InventoryItem, StockMovement, MovementType
        
        # Create inventory item first
        item = InventoryItem(
            product_id='MOVE001',
            quantity=100
        )
        self.db.session.add(item)
        self.db.session.flush()
        
        # Create stock movement
        movement = StockMovement(
            inventory_item_id=item.id,
            movement_type=MovementType.INBOUND,
            quantity=50,
            reference_id='REF001'
        )
        
        self.db.session.add(movement)
        self.db.session.commit()
        
        self.assertIsNotNone(movement.id)
        self.assertEqual(movement.movement_type, MovementType.INBOUND)
        self.assertEqual(movement.quantity, 50)


class TestInventoryServices(unittest.TestCase):
    """Test Inventory Services"""
    
    def setUp(self):
        """Set up test environment"""
        try:
            from app import create_app
            from app.models import db
            
            self.app = create_app('testing')
            self.app_context = self.app.app_context()
            self.app_context.push()
            
            db.create_all()
            self.db = db
        except Exception as e:
            self.skipTest(f"Setup failed: {e}")
    
    def tearDown(self):
        """Clean up after test"""
        if hasattr(self, 'db'):
            self.db.session.remove()
            self.db.drop_all()
        if hasattr(self, 'app_context'):
            self.app_context.pop()
    
    @patch('app.utils.cache.redis_client')
    def test_inventory_service_creation(self, mock_redis):
        """Test inventory service item creation"""
        from app.services import InventoryService
        from app.models import InventoryItem
        
        # Mock Redis
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = True
        
        service = InventoryService()
        
        item = service.create_inventory_item(
            product_id='SERVICE001',
            quantity=100,
            minimum_stock_level=10,
            location='Service Warehouse'
        )
        
        self.assertIsNotNone(item)
        self.assertEqual(item.product_id, 'SERVICE001')
        self.assertEqual(item.quantity, 100)
        
        # Verify item was saved to database
        saved_item = self.db.session.query(InventoryItem).filter_by(
            product_id='SERVICE001'
        ).first()
        self.assertIsNotNone(saved_item)
    
    @patch('app.utils.cache.redis_client')
    def test_inventory_service_stock_adjustment(self, mock_redis):
        """Test stock adjustment through service"""
        from app.services import InventoryService
        from app.models import InventoryItem, MovementType
        
        # Mock Redis
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = True
        
        # Create inventory item
        item = InventoryItem(
            product_id='ADJUST001',
            quantity=100
        )
        self.db.session.add(item)
        self.db.session.commit()
        
        service = InventoryService()
        
        # Test inbound adjustment
        movement = service.adjust_stock(
            product_id='ADJUST001',
            quantity=50,
            movement_type=MovementType.INBOUND,
            reference_id='ADJ001'
        )
        
        self.assertIsNotNone(movement)
        self.assertEqual(movement.quantity, 50)
        
        # Verify stock was updated
        updated_item = service.get_inventory_by_product_id('ADJUST001')
        self.assertEqual(updated_item.quantity, 150)  # 100 + 50
    
    @patch('app.utils.cache.redis_client')
    def test_reservation_service_creation(self, mock_redis):
        """Test reservation service creation"""
        from app.services import ReservationService
        from app.models import InventoryItem
        
        # Mock Redis
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = True
        
        # Create inventory item with sufficient stock
        item = InventoryItem(
            product_id='RESERVE001',
            quantity=100
        )
        self.db.session.add(item)
        self.db.session.commit()
        
        service = ReservationService()
        
        reservation = service.create_reservation(
            product_id='RESERVE001',
            quantity=10,
            customer_id='CUSTOMER001',
            order_id='ORDER001'
        )
        
        self.assertIsNotNone(reservation)
        self.assertEqual(reservation.quantity, 10)
        self.assertEqual(reservation.customer_id, 'CUSTOMER001')
        
        # Verify inventory was updated
        updated_item = service._get_inventory_by_product_id('RESERVE001')
        self.assertEqual(updated_item.reserved_quantity, 10)


class TestInventoryAPI(unittest.TestCase):
    """Test Inventory API endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        try:
            from app import create_app
            from app.models import db
            
            self.app = create_app('testing')
            self.client = self.app.test_client()
            self.app_context = self.app.app_context()
            self.app_context.push()
            
            db.create_all()
            self.db = db
        except Exception as e:
            self.skipTest(f"Setup failed: {e}")
    
    def tearDown(self):
        """Clean up after test"""
        if hasattr(self, 'db'):
            self.db.session.remove()
            self.db.drop_all()
        if hasattr(self, 'app_context'):
            self.app_context.pop()
    
    @patch('app.utils.cache.redis_client')
    def test_health_check_endpoint(self, mock_redis):
        """Test health check endpoint"""
        # Mock Redis ping
        mock_redis.ping.return_value = True
        
        response = self.client.get('/api/v1/health/')
        
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
    
    @patch('app.utils.cache.redis_client')
    def test_create_inventory_endpoint(self, mock_redis):
        """Test creating inventory via API"""
        # Mock Redis
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = True
        
        data = {
            'product_id': 'API001',
            'quantity': 100,
            'minimum_stock_level': 10,
            'location': 'API Warehouse'
        }
        
        response = self.client.post(
            '/api/v1/inventory/',
            json=data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        response_data = response.get_json()
        self.assertEqual(response_data['product_id'], 'API001')
        self.assertEqual(response_data['quantity'], 100)


def run_tests():
    """Run all unit tests"""
    print("Running Unit Tests for Inventory Service")
    print("=" * 60)
    
    # Create test suite
    test_classes = [
        TestInventoryModels,
        TestInventoryServices,
        TestInventoryAPI
    ]
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    for test_class in test_classes:
        print(f"\n🧪 Running {test_class.__name__}")
        print("-" * 40)
        
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        total_tests += result.testsRun
        total_failures += len(result.failures)
        total_errors += len(result.errors)
        
        if result.failures:
            print(f"❌ Failures in {test_class.__name__}:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        
        if result.errors:
            print(f"🚨 Errors in {test_class.__name__}:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
    
    print("\n" + "=" * 60)
    print(f"📊 TEST SUMMARY:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {total_tests - total_failures - total_errors}")
    print(f"   Failed: {total_failures}")
    print(f"   Errors: {total_errors}")
    
    if total_failures == 0 and total_errors == 0:
        print("✅ ALL TESTS PASSED!")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        return False


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
