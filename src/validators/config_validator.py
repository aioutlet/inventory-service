"""
Configuration Validator
Validates all required environment variables at application startup
Fails fast if any configuration is missing or invalid

NOTE: This module MUST NOT import logger, as the logger depends on validated config.
Uses colored print for validation messages.
"""

import os
import sys
from urllib.parse import urlparse


# Import colored print utilities
try:
    from src.shared.utils.colored_print import (
        colored_print, Colors, print_info, print_warning, 
        print_error, print_step, print_success, print_failure
    )
    HAS_COLORS = True
except ImportError:
    # Fallback if import fails
    HAS_COLORS = False
    def colored_print(msg, *args, **kwargs):
        print(msg)
    print_info = print_warning = print_error = print_step = print_success = print_failure = print


def is_valid_url(url: str) -> bool:
    """Validates a URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_valid_port(port: str) -> bool:
    """Validates a port number"""
    try:
        port_num = int(port)
        return 0 < port_num <= 65535
    except (ValueError, TypeError):
        return False


def is_valid_log_level(level: str) -> bool:
    """Validates log level"""
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    return level.upper() in valid_levels


def is_valid_environment(env: str) -> bool:
    """Validates ENVIRONMENT"""
    valid_envs = ['development', 'production', 'test', 'staging']
    return env.lower() in valid_envs


def is_valid_boolean(value: str) -> bool:
    """Validates boolean string"""
    return value.lower() in ['true', 'false']


# Configuration validation rules
VALIDATION_RULES = {
    # Service Configuration
    'FLASK_ENV': {
        'required': False,
        'validator': is_valid_environment,
        'error_message': 'FLASK_ENV must be one of: development, production, test, staging',
        'default': 'development',
    },
    'FLASK_APP': {
        'required': False,
        'validator': lambda v: not v or len(v) > 0,
        'error_message': 'FLASK_APP must be a non-empty string if provided',
        'default': 'run.py',
    },
    'NAME': {
        'required': False,
        'validator': lambda v: not v or len(v) > 0,
        'error_message': 'NAME must be a non-empty string',
        'default': 'inventory-service',
    },
    
    # Database Configuration
    'MYSQL_HOST': {
        'required': True,
        'validator': lambda v: v and len(v) > 0,
        'error_message': 'MYSQL_HOST must be a non-empty string',
    },
    'MYSQL_PORT': {
        'required': False,
        'validator': lambda v: not v or is_valid_port(v),
        'error_message': 'MYSQL_PORT must be a valid port number if provided',
        'default': '3306',
    },
    'MYSQL_USER': {
        'required': True,
        'validator': lambda v: v and len(v) > 0,
        'error_message': 'MYSQL_USER must be a non-empty string',
    },
    'MYSQL_PASSWORD': {
        'required': True,
        'validator': lambda v: v and len(v) > 0,
        'error_message': 'MYSQL_PASSWORD must be a non-empty string',
    },
    'MYSQL_DATABASE': {
        'required': True,
        'validator': lambda v: v and len(v) > 0,
        'error_message': 'MYSQL_DATABASE must be a non-empty string',
    },
    
    # Message Broker Configuration
    'MESSAGE_BROKER_SERVICE_URL': {
        'required': True,
        'validator': is_valid_url,
        'error_message': 'MESSAGE_BROKER_SERVICE_URL must be a valid URL',
    },
    'MESSAGE_BROKER_QUEUE': {
        'required': True,
        'validator': lambda v: v and len(v) > 0,
        'error_message': 'MESSAGE_BROKER_QUEUE must be a non-empty string',
    },
    'MESSAGE_BROKER_TYPE': {
        'required': False,
        'validator': lambda v: not v or v.lower() in ['rabbitmq', 'kafka'],
        'error_message': 'MESSAGE_BROKER_TYPE must be either rabbitmq or kafka',
        'default': 'rabbitmq',
    },
    'MESSAGE_BROKER_HEALTH_URL': {
        'required': False,
        'validator': lambda v: not v or is_valid_url(v),
        'error_message': 'MESSAGE_BROKER_HEALTH_URL must be a valid URL if provided',
    },
    'EVENT_VERSION': {
        'required': False,
        'validator': lambda v: not v or len(v.split('.')) >= 2,
        'error_message': 'EVENT_VERSION must be in version format (e.g., 1.0)',
        'default': '1.0',
    },
    
    # External Service URLs
    'PRODUCT_SERVICE_URL': {
        'required': True,
        'validator': is_valid_url,
        'error_message': 'PRODUCT_SERVICE_URL must be a valid URL',
    },
    'PRODUCT_SERVICE_HEALTH_URL': {
        'required': False,
        'validator': lambda v: not v or is_valid_url(v),
        'error_message': 'PRODUCT_SERVICE_HEALTH_URL must be a valid URL if provided',
    },
    
    # Security Configuration
    'JWT_SECRET': {
        'required': True,
        'validator': lambda v: v and len(v) >= 32,
        'error_message': 'JWT_SECRET must be at least 32 characters long',
    },
    'SECRET_KEY': {
        'required': True,
        'validator': lambda v: v and len(v) >= 32,
        'error_message': 'SECRET_KEY must be at least 32 characters long',
    },
    
    # CORS Configuration
    'CORS_ORIGINS': {
        'required': False,
        'validator': lambda v: not v or all(
            origin.strip() == '*' or is_valid_url(origin.strip())
            for origin in v.split(',')
        ),
        'error_message': 'CORS_ORIGINS must be a comma-separated list of valid URLs or *',
        'default': '*',
    },
    
    # Logging Configuration
    'LOG_LEVEL': {
        'required': False,
        'validator': is_valid_log_level,
        'error_message': 'LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL',
        'default': 'INFO',
    },
    
    # Business Logic Configuration
    'RESERVATION_TTL_MINUTES': {
        'required': False,
        'validator': lambda v: not v or (v.isdigit() and int(v) > 0),
        'error_message': 'RESERVATION_TTL_MINUTES must be a positive integer',
        'default': '15',
    },
    'DEFAULT_PAGE_SIZE': {
        'required': False,
        'validator': lambda v: not v or (v.isdigit() and int(v) > 0),
        'error_message': 'DEFAULT_PAGE_SIZE must be a positive integer',
        'default': '20',
    },
    'MAX_PAGE_SIZE': {
        'required': False,
        'validator': lambda v: not v or (v.isdigit() and int(v) > 0),
        'error_message': 'MAX_PAGE_SIZE must be a positive integer',
        'default': '100',
    },
}


def validate_config():
    """
    Validates all environment variables according to the rules
    Raises SystemExit if any required variable is missing or invalid
    """
    errors = []
    warnings = []

    print_step('[CONFIG] Validating environment configuration...')

    # Validate each rule
    for key, rule in VALIDATION_RULES.items():
        value = os.getenv(key)

        # Check if required variable is missing
        if rule['required'] and not value:
            errors.append(f"❌ {key} is required but not set")
            continue

        # Skip validation if value is not set and not required
        if not value and not rule['required']:
            if 'default' in rule:
                warnings.append(f"⚠️  {key} not set, using default: {rule['default']}")
                os.environ[key] = rule['default']
            continue

        # Validate the value
        if value and rule['validator'] and not rule['validator'](value):
            errors.append(f"❌ {key}: {rule['error_message']}")
            # Don't expose sensitive values
            if 'PASSWORD' in key or 'SECRET' in key or 'KEY' in key:
                errors.append(f"   Current value: ***")
            elif len(value) > 100:
                errors.append(f"   Current value: {value[:100]}...")
            else:
                errors.append(f"   Current value: {value}")

    # Log warnings
    if warnings:
        for warning in warnings:
            print_warning(warning)

    # If there are errors, log them and exit
    if errors:
        print_failure('[CONFIG] Configuration validation failed:')
        for error in errors:
            print_error(error)
        print_error('\n💡 Please check your .env file and ensure all required variables are set correctly.')
        sys.exit(1)

    print_success('[CONFIG] All required environment variables are valid')


def get_config(key: str, default=None):
    """Gets a validated configuration value"""
    return os.getenv(key, default)


def get_config_boolean(key: str, default: bool = False) -> bool:
    """Gets a validated configuration value as boolean"""
    value = os.getenv(key, str(default))
    return value.lower() == 'true'


def get_config_int(key: str, default: int = 0) -> int:
    """Gets a validated configuration value as integer"""
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def get_config_list(key: str, default=None) -> list:
    """Gets a validated configuration value as list (comma-separated)"""
    if default is None:
        default = []
    value = os.getenv(key)
    if not value:
        return default
    return [item.strip() for item in value.split(',')]
