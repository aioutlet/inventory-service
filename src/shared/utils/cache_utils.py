import json
import hashlib
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def cache_key_generator(prefix: str, identifier: Any) -> str:
    """Generate a cache key with prefix and hashed identifier"""
    if isinstance(identifier, (list, dict)):
        # For complex objects, create a hash
        content = json.dumps(identifier, sort_keys=True)
        hash_suffix = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{prefix}:{hash_suffix}"
    else:
        return f"{prefix}:{identifier}"


def get_from_cache(key: str, redis_client) -> Optional[Any]:
    """Get data from Redis cache"""
    if not redis_client:
        return None
        
    try:
        cached_data = redis_client.get(key)
        if cached_data:
            return json.loads(cached_data)
    except Exception as e:
        logger.warning(f"Error reading from cache key {key}: {e}")
    
    return None


def set_cache(key: str, data: Any, ttl: int, redis_client) -> bool:
    """Set data in Redis cache with TTL"""
    if not redis_client:
        return False
        
    try:
        redis_client.setex(key, ttl, json.dumps(data, default=str))
        return True
    except Exception as e:
        logger.warning(f"Error setting cache key {key}: {e}")
        return False


def clear_cache_pattern(pattern: str, redis_client) -> int:
    """Clear cache keys matching a pattern"""
    if not redis_client:
        return 0
        
    try:
        keys = redis_client.keys(pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0
    except Exception as e:
        logger.warning(f"Error clearing cache pattern {pattern}: {e}")
        return 0
