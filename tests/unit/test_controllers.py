import pytest
import json
from datetime import datetime, timedelta

from src.models import InventoryItem, Reservation, StockMovementType, ReservationStatus
from tests.conftest import create_test_inventory_item, create_test_reservation


class TestInventoryEndpoints:
    """Test inventory REST endpoints."""
    
    def test_create_inventory_item(self, client, db_session):
        """Test creating inventory item."""
        data = {
            'product_id': 'TEST001',
            'quantity_available': 100,
            'reorder_level': 10,
            'max_stock': 200
        }
        
        response = client.post('/api/v1/inventory/', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data['product_id'] == 'TEST001'
        assert json_data['quantity_available'] == 100
    
    def test_get_inventory_by_product_id(self, client, db_session):
        """Test getting inventory by product ID."""
        create_test_inventory_item(db_session, product_id='GET001')
        
        response = client.get('/api/v1/inventory/GET001')
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['product_id'] == 'GET001'
    
    def test_get_inventory_not_found(self, client, db_session):
        """Test getting non-existent inventory."""
        response = client.get('/api/v1/inventory/NONEXISTENT')
        
        assert response.status_code == 404
    
    def test_delete_inventory_item(self, client, db_session):
        """Test deleting inventory item."""
        create_test_inventory_item(db_session, product_id='DELETE001')
        
        response = client.delete('/api/v1/inventory/DELETE001')
        
        assert response.status_code == 200


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check_basic(self, client, db_session):
        """Test basic health check."""
        response = client.get('/api/v1/inventory/health')
        
        # Should return some response (may be 200 or 503 depending on services)
        assert response.status_code in [200, 503]
        json_data = response.get_json()
        assert 'status' in json_data
        assert 'timestamp' in json_data
