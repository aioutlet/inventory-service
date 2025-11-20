"""
Stats Controller - Provides inventory statistics for dashboards
"""

from flask import Blueprint, jsonify
from src.repositories.inventory_repository import InventoryRepository
import logging

logger = logging.getLogger(__name__)

# Create blueprint
stats_bp = Blueprint('stats', __name__)

# Initialize repository
inventory_repo = InventoryRepository()


@stats_bp.route('/api/stats', methods=['GET'])
def get_inventory_stats():
    """
    Get inventory statistics for admin dashboard
    
    Returns:
        JSON with inventory metrics:
        - productsWithStock: Count of items with quantity > 0
        - lowStockCount: Count of items below reorder level
        - outOfStockCount: Count of items with zero quantity
        - totalInventoryValue: Sum of (quantity * cost_per_unit)
        - totalUnits: Total units across all products
        - totalItems: Total inventory items tracked
    """
    try:
        stats = {
            "productsWithStock": inventory_repo.count_products_with_stock(),
            "lowStockCount": inventory_repo.count_low_stock(),
            "outOfStockCount": inventory_repo.count_out_of_stock(),
            "totalInventoryValue": round(inventory_repo.calculate_total_value(), 2),
            "totalUnits": inventory_repo.calculate_total_units(),
            "totalItems": inventory_repo.count_total(),
            "service": "inventory-service"
        }
        
        logger.info(f"Stats retrieved: {stats}")
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error retrieving inventory stats: {e}", exc_info=True)
        return jsonify({
            "error": "Failed to retrieve inventory statistics",
            "details": str(e)
        }), 500
