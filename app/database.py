"""
Database configuration and instance
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize database instance
db = SQLAlchemy()
migrate = Migrate()


def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    migrate.init_app(app, db)
    return db
