import redis
import json
import hashlib
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import pickle
import os
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheService:
    """
    Redis-based caching service for geolocation and detection results.
    Provides efficient caching with TTL and cache invalidation.
    """
    
    def __init__(self, redis_url: str = None, default_ttl: int = 3600):
        """
        Initialize Redis cache service.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live in seconds (1 hour)
        """
        self.default_ttl = default_ttl
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=False)
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self.redis_client = None
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a unique cache key from arguments."""
        # Create a string representation of all arguments
        key_data = f"{prefix}:{':'.join(map(str, args))}"
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_data += f":{':'.join(f'{k}={v}' for k, v in sorted_kwargs)}"
        
        # Hash the key to ensure consistent length and avoid special characters
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return pickle.loads(cached_data)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with TTL."""
        if not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized_value = pickle.dumps(value)
            return self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {str(e)}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {str(e)}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.redis_client:
            return {'connected': False}
        
        try:
            info = self.redis_client.info()
            return {
                'connected': True,
                'used_memory': info.get('used_memory_human'),
                'total_keys': info.get('db0', {}).get('keys', 0),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'hit_rate': info.get('keyspace_hits', 0) / max(1, info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0))
            }
        except Exception as e:
            logger.error(f"Cache stats error: {str(e)}")
            return {'connected': False, 'error': str(e)}

# Global cache instance
cache = CacheService()

class GeolocationCache:
    """Specialized caching for geolocation results."""
    
    @staticmethod
    def get_location_cache_key(image_path: str, location_hint: str = "") -> str:
        """Generate cache key for geolocation results."""
        # Use file hash instead of path for consistency
        try:
            with open(image_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
        except:
            file_hash = hashlib.md5(image_path.encode()).hexdigest()
        
        return cache._generate_key('geolocation', file_hash, location_hint)
    
    @staticmethod
    def cache_location_result(image_path: str, location_hint: str, result: Dict[str, Any], ttl: int = 86400) -> bool:
        """Cache geolocation result for 24 hours by default."""
        key = GeolocationCache.get_location_cache_key(image_path, location_hint)
        return cache.set(key, result, ttl)
    
    @staticmethod
    def get_cached_location_result(image_path: str, location_hint: str = "") -> Optional[Dict[str, Any]]:
        """Get cached geolocation result."""
        key = GeolocationCache.get_location_cache_key(image_path, location_hint)
        return cache.get(key)

class DetectionCache:
    """Specialized caching for violation detection results."""
    
    @staticmethod
    def get_detection_cache_key(image_path: str, model_version: str = "yolov8") -> str:
        """Generate cache key for detection results."""
        try:
            with open(image_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
        except:
            file_hash = hashlib.md5(image_path.encode()).hexdigest()
        
        return cache._generate_key('detection', model_version, file_hash)
    
    @staticmethod
    def cache_detection_result(image_path: str, result: Dict[str, Any], model_version: str = "yolov8", ttl: int = 3600) -> bool:
        """Cache detection result for 1 hour by default."""
        key = DetectionCache.get_detection_cache_key(image_path, model_version)
        return cache.set(key, result, ttl)
    
    @staticmethod
    def get_cached_detection_result(image_path: str, model_version: str = "yolov8") -> Optional[Dict[str, Any]]:
        """Get cached detection result."""
        key = DetectionCache.get_detection_cache_key(image_path, model_version)
        return cache.get(key)

class MapCache:
    """Specialized caching for map API results."""
    
    @staticmethod
    def cache_geocode_result(query: str, result: Dict[str, Any], ttl: int = 604800) -> bool:
        """Cache geocoding result for 1 week."""
        key = cache._generate_key('geocode', query.lower().strip())
        return cache.set(key, result, ttl)
    
    @staticmethod
    def get_cached_geocode_result(query: str) -> Optional[Dict[str, Any]]:
        """Get cached geocoding result."""
        key = cache._generate_key('geocode', query.lower().strip())
        return cache.get(key)
    
    @staticmethod
    def cache_reverse_geocode_result(lat: float, lon: float, result: Dict[str, Any], ttl: int = 604800) -> bool:
        """Cache reverse geocoding result for 1 week."""
        # Round coordinates to reduce cache fragmentation
        lat_rounded = round(lat, 6)
        lon_rounded = round(lon, 6)
        key = cache._generate_key('reverse_geocode', lat_rounded, lon_rounded)
        return cache.set(key, result, ttl)
    
    @staticmethod
    def get_cached_reverse_geocode_result(lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Get cached reverse geocoding result."""
        lat_rounded = round(lat, 6)
        lon_rounded = round(lon, 6)
        key = cache._generate_key('reverse_geocode', lat_rounded, lon_rounded)
        return cache.get(key)
    
    @staticmethod
    def cache_satellite_image(lat: float, lon: float, zoom: int, image_data: bytes, ttl: int = 2592000) -> bool:
        """Cache satellite image for 1 month."""
        key = cache._generate_key('satellite', lat, lon, zoom)
        return cache.set(key, image_data, ttl)
    
    @staticmethod
    def get_cached_satellite_image(lat: float, lon: float, zoom: int) -> Optional[bytes]:
        """Get cached satellite image."""
        key = cache._generate_key('satellite', lat, lon, zoom)
        return cache.get(key)

def cached_function(prefix: str, ttl: int = 3600):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache._generate_key(prefix, func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            
            return result
        return wrapper
    return decorator

class CacheManager:
    """High-level cache management utilities."""
    
    @staticmethod
    def warm_up_cache():
        """Pre-populate cache with common data."""
        logger.info("Starting cache warm-up...")
        # This could be expanded to pre-load common geocoding results
        # or frequently accessed data
        pass
    
    @staticmethod
    def cleanup_expired():
        """Clean up expired cache entries (Redis handles this automatically)."""
        if cache.redis_client:
            try:
                # Get cache statistics
                stats = cache.get_stats()
                logger.info(f"Cache cleanup - Current stats: {stats}")
            except Exception as e:
                logger.error(f"Cache cleanup error: {str(e)}")
    
    @staticmethod
    def clear_all_cache():
        """Clear all cache entries."""
        if cache.redis_client:
            try:
                cache.redis_client.flushdb()
                logger.info("All cache cleared")
                return True
            except Exception as e:
                logger.error(f"Error clearing cache: {str(e)}")
                return False
        return False
    
    @staticmethod
    def clear_cache_by_type(cache_type: str):
        """Clear cache entries by type."""
        pattern = f"{cache_type}:*"
        cleared = cache.clear_pattern(pattern)
        logger.info(f"Cleared {cleared} entries for type {cache_type}")
        return cleared
    
    @staticmethod
    def get_cache_info() -> Dict[str, Any]:
        """Get comprehensive cache information."""
        stats = cache.get_stats()
        
        if not stats.get('connected'):
            return stats
        
        # Add more detailed information
        try:
            if cache.redis_client:
                # Count keys by type
                key_counts = {}
                for key_type in ['geolocation', 'detection', 'geocode', 'reverse_geocode', 'satellite']:
                    pattern = f"{key_type}:*"
                    keys = cache.redis_client.keys(pattern)
                    key_counts[key_type] = len(keys)
                
                stats['key_counts'] = key_counts
                stats['total_keys_by_type'] = sum(key_counts.values())
                
        except Exception as e:
            logger.error(f"Error getting detailed cache info: {str(e)}")
        
        return stats
