"""
Pytest configuration for integration tests
"""

import os
import sys
import pytest

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Set test environment
os.environ['FLASK_ENV'] = 'test'
os.environ['TESTING'] = 'True'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
