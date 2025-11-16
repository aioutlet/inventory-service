"""
Controllers package initialization
"""

# Import all blueprints for registration
from src.api.controllers.inventory import inventory_bp
from src.api.controllers.reservations import reservations_bp
from src.api.controllers.stats import stats_bp
from src.api.controllers.home import home_bp
from src.api.controllers.events import events_bp
from src.api.controllers.operational import operational_hp

__all__ = ['inventory_bp', 'reservations_bp', 'stats_bp', 'home_bp', 'events_bp', 'operational_hp']
