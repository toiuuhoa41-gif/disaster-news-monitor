"""
Caching Service using Redis for Dashboard Stats
Provides caching decorators and utilities for FastAPI endpoints
"""

import json
import hashlib
import functools
from typing import Optional, Callable, Any, Union
from datetime import timedelta
import logging
import asyncio

logger = logging.getLogger(__name__)

# ============================================
# Cache Configuration
# ============================================

CACHE_CONFIG = {
    "dashboard_stats": 300,      # 5 minutes
    "realtime_stats": 60,        # 1 minute  
    "today_stats": 120,          # 2 minutes
    "articles_list": 180,        # 3 minutes
    "category_stats": 300,       # 5 minutes
    "source_stats": 300,         # 5 minutes
    "keyword_cloud": 600,        # 10 minutes
    "region_stats": 300,         # 5 minutes
    "default": 60,               # 1 minute default
}


class CacheService:
    """
    Async caching service using Redis.
    Falls back to in-memory cache if Redis is unavailable.
    """
    
    def __init__(self):
        self._redis = None
        self._memory_cache: dict = {}
        self._memory_expiry: dict = {}
    
    async def get_redis(self):
        """Get Redis connection lazily"""
        if self._redis is None:
            try:
                from mongodb.api.services.redis_service import RedisService
                self._redis = await RedisService.get_client()
            except Exception as e:
                logger.debug(f"Redis not available for caching: {e}")
                self._redis = False  # Mark as unavailable
        return self._redis if self._redis else None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        redis = await self.get_redis()
        
        if redis:
            try:
                value = await redis.get(f"cache:{key}")
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.debug(f"Redis get error: {e}")
        
        # Fallback to memory cache
        return self._get_from_memory(key)
    
    async def set(self, key: str, value: Any, ttl: int = 60) -> bool:
        """Set value in cache with TTL in seconds"""
        redis = await self.get_redis()
        
        if redis:
            try:
                await redis.setex(
                    f"cache:{key}",
                    ttl,
                    json.dumps(value, default=str)
                )
                return True
            except Exception as e:
                logger.debug(f"Redis set error: {e}")
        
        # Fallback to memory cache
        self._set_in_memory(key, value, ttl)
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        redis = await self.get_redis()
        
        if redis:
            try:
                await redis.delete(f"cache:{key}")
            except Exception:
                pass
        
        # Also delete from memory
        self._memory_cache.pop(key, None)
        self._memory_expiry.pop(key, None)
        return True
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        redis = await self.get_redis()
        count = 0
        
        if redis:
            try:
                async for key in redis.scan_iter(match=f"cache:{pattern}"):
                    await redis.delete(key)
                    count += 1
            except Exception as e:
                logger.debug(f"Redis delete pattern error: {e}")
        
        # Also clear matching memory cache keys
        keys_to_delete = [k for k in self._memory_cache.keys() if k.startswith(pattern.replace("*", ""))]
        for key in keys_to_delete:
            self._memory_cache.pop(key, None)
            self._memory_expiry.pop(key, None)
            count += 1
        
        return count
    
    async def clear_all(self) -> bool:
        """Clear all cache"""
        redis = await self.get_redis()
        
        if redis:
            try:
                async for key in redis.scan_iter(match="cache:*"):
                    await redis.delete(key)
            except Exception:
                pass
        
        self._memory_cache.clear()
        self._memory_expiry.clear()
        return True
    
    def _get_from_memory(self, key: str) -> Optional[Any]:
        """Get from in-memory cache with expiry check"""
        import time
        
        if key in self._memory_cache:
            expiry = self._memory_expiry.get(key, 0)
            if time.time() < expiry:
                return self._memory_cache[key]
            else:
                # Expired, clean up
                self._memory_cache.pop(key, None)
                self._memory_expiry.pop(key, None)
        
        return None
    
    def _set_in_memory(self, key: str, value: Any, ttl: int):
        """Set in memory cache with TTL"""
        import time
        
        self._memory_cache[key] = value
        self._memory_expiry[key] = time.time() + ttl
        
        # Cleanup old entries if too many (simple LRU-like)
        if len(self._memory_cache) > 1000:
            current_time = time.time()
            expired = [k for k, exp in self._memory_expiry.items() if exp < current_time]
            for k in expired[:100]:  # Remove up to 100 expired
                self._memory_cache.pop(k, None)
                self._memory_expiry.pop(k, None)


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get or create cache service singleton"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


# ============================================
# Caching Decorators
# ============================================

def make_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments"""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(
    prefix: str,
    ttl: Optional[int] = None,
    key_builder: Optional[Callable] = None
):
    """
    Caching decorator for async functions.
    
    Usage:
        @cached("dashboard_stats", ttl=300)
        async def get_dashboard_stats():
            ...
    
    Args:
        prefix: Cache key prefix (also used to look up TTL in CACHE_CONFIG)
        ttl: Time-to-live in seconds (overrides CACHE_CONFIG)
        key_builder: Custom function to build cache key from args/kwargs
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_service()
            
            # Build cache key
            if key_builder:
                key_suffix = key_builder(*args, **kwargs)
            else:
                key_suffix = make_cache_key(*args, **kwargs)
            
            cache_key = f"{prefix}:{key_suffix}"
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value
            
            logger.debug(f"Cache MISS: {cache_key}")
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache the result
            cache_ttl = ttl or CACHE_CONFIG.get(prefix, CACHE_CONFIG["default"])
            await cache.set(cache_key, result, cache_ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(prefix: str):
    """
    Decorator to invalidate cache after function execution.
    
    Usage:
        @invalidate_cache("dashboard_stats")
        async def update_article(article_id: str, data: dict):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Invalidate cache
            cache = get_cache_service()
            await cache.delete_pattern(f"{prefix}:*")
            logger.debug(f"Cache invalidated: {prefix}:*")
            
            return result
        
        return wrapper
    return decorator


# ============================================
# FastAPI Request-based Caching
# ============================================

def cached_endpoint(
    prefix: str,
    ttl: Optional[int] = None,
    include_query_params: bool = True
):
    """
    Caching decorator specifically for FastAPI endpoints.
    
    Usage:
        @router.get("/stats")
        @cached_endpoint("dashboard_stats", ttl=300)
        async def get_stats(request: Request, page: int = 1):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_service()
            
            # Build cache key from request
            request = kwargs.get('request') or (args[0] if args else None)
            
            if request and include_query_params:
                query_string = str(request.query_params)
                key_suffix = hashlib.md5(query_string.encode()).hexdigest()
            else:
                key_suffix = make_cache_key(*args, **kwargs)
            
            cache_key = f"{prefix}:{key_suffix}"
            
            # Try cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute
            result = await func(*args, **kwargs)
            
            # Handle Pydantic models and dict-like responses
            if hasattr(result, 'dict'):
                cache_data = result.dict()
            elif hasattr(result, 'model_dump'):
                cache_data = result.model_dump()
            else:
                cache_data = result
            
            # Cache
            cache_ttl = ttl or CACHE_CONFIG.get(prefix, CACHE_CONFIG["default"])
            await cache.set(cache_key, cache_data, cache_ttl)
            
            return result
        
        return wrapper
    return decorator


# ============================================
# Cache Management API
# ============================================

async def get_cache_stats() -> dict:
    """Get cache statistics"""
    cache = get_cache_service()
    
    stats = {
        "memory_cache_size": len(cache._memory_cache),
        "redis_available": cache._redis is not None and cache._redis is not False,
        "config": CACHE_CONFIG
    }
    
    redis = await cache.get_redis()
    if redis:
        try:
            info = await redis.info("memory")
            stats["redis_memory"] = info.get("used_memory_human", "unknown")
        except:
            pass
    
    return stats


async def clear_cache(prefix: Optional[str] = None) -> dict:
    """Clear cache by prefix or all"""
    cache = get_cache_service()
    
    if prefix:
        count = await cache.delete_pattern(f"{prefix}:*")
        return {"cleared": count, "prefix": prefix}
    else:
        await cache.clear_all()
        return {"cleared": "all"}
