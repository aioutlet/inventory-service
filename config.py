import os
from datetime import timedelta


class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    DATABASE_HOST = os.environ.get('DATABASE_HOST', 'localhost')
    DATABASE_PORT = int(os.environ.get('DATABASE_PORT', 3306))
    DATABASE_USER = os.environ.get('DATABASE_USER', 'inventoryuser')
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD', 'inventory_dev_pass_123')
    DATABASE_NAME = os.environ.get('DATABASE_NAME', 'inventory_service_db')
    
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@"
        f"{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Redis Cache
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
    
    # Cache TTL (in seconds)
    CACHE_TTL_STOCK_CHECK = int(os.environ.get('CACHE_TTL_STOCK_CHECK', 300))  # 5 minutes
    CACHE_TTL_INVENTORY = int(os.environ.get('CACHE_TTL_INVENTORY', 600))  # 10 minutes
    
    # Reservation settings
    RESERVATION_TTL_MINUTES = int(os.environ.get('RESERVATION_TTL_MINUTES', 30))
    
    # Service URLs
    PRODUCT_SERVICE_URL = os.environ.get('PRODUCT_SERVICE_URL', 'http://localhost:3001')
    
    # Pagination
    DEFAULT_PAGE_SIZE = int(os.environ.get('DEFAULT_PAGE_SIZE', 20))
    MAX_PAGE_SIZE = int(os.environ.get('MAX_PAGE_SIZE', 100))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    # MySQL is the primary database for all environments


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    # Use in-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # Use different Redis DB for testing
    REDIS_DB = 1
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Override with production values if needed


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
