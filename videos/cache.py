"""
Redis Cache Service with graceful fallback
Provides caching for API responses with automatic Redis setup
"""
import json
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
import subprocess


class CacheService:
    """Redis cache wrapper with fallback to no-cache mode"""
    
    def __init__(self):
        self.redis_client = None
        self.enabled = False
        self._setup_redis()
    
    def _setup_redis(self):
        """Setup Redis connection with automatic container creation"""
        try:
            import redis
            
            # Try to connect to Redis
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            print("[OK] Redis cache enabled")

        except ImportError:
            print("[WARN] Redis library not installed. Install with: pip install redis")
            print("   Continuing without cache...")

        except Exception as e:
            # Redis not available, try to auto-setup
            print(f"[WARN] Redis not available: {e}")
            print("[INFO] Attempting to start porn_redis container...")
            
            try:
                # Run setup script
                result = subprocess.run(
                    ["python", "setup_redis.py"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # Try connecting again
                    import redis
                    self.redis_client = redis.Redis(
                        host='localhost',
                        port=6379,
                        db=0,
                        decode_responses=True,
                        socket_connect_timeout=2,
                        socket_timeout=2
                    )
                    self.redis_client.ping()
                    self.enabled = True
                    print("[OK] Redis cache enabled after auto-setup")
                else:
                    print("   Setup failed. Continuing without cache...")
                    
            except Exception as setup_error:
                print(f"   Auto-setup failed: {setup_error}")
                print("   Continuing without cache...")
    
    def _make_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from prefix and kwargs"""
        # Sort kwargs for consistent keys
        sorted_params = sorted(kwargs.items())
        param_str = json.dumps(sorted_params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
        return f"{prefix}:{param_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            print(f"Cache get error: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL (default 5 minutes)"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            serialized = json.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str):
        """Delete key from cache"""
        if not self.enabled or not self.redis_client:
            return
        
        try:
            self.redis_client.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")
    
    def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        if not self.enabled or not self.redis_client:
            return
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                print(f"[OK] Cleared {len(keys)} cache keys matching {pattern}")
        except Exception as e:
            print(f"Cache clear error: {e}")


# Global cache instance
cache = CacheService()


def cached(prefix: str, ttl: int = 300):
    """
    Decorator to cache function results
    
    Usage:
        @cached(prefix='eporner:search', ttl=300)
        def search(query, page=1):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip caching for class methods (self/cls as first arg)
            if args and hasattr(args[0], '__class__'):
                func_kwargs = kwargs
            else:
                func_kwargs = kwargs
            
            # Generate cache key
            cache_key = cache._make_key(prefix, **func_kwargs)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                # print(f"[HIT] Cache: {prefix}")  # Commented for less verbose output
                return cached_value

            # Cache miss - call function
            # print(f"[MISS] Cache: {prefix}")  # Commented for less verbose output
            result = func(*args, **kwargs)
            
            # Store in cache
            if result is not None:
                cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator
