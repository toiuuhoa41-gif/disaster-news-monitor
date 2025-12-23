"""
Redis Service for Pub/Sub and Caching
Enables WebSocket scaling across multiple workers
"""

import asyncio
import json
from typing import Optional, Callable, Any, Dict, List
from datetime import timedelta
import redis.asyncio as redis
from mongodb.api.config.settings import settings
import logging

logger = logging.getLogger(__name__)


class RedisService:
    """Redis client for pub/sub and caching"""
    
    _instance: Optional['RedisService'] = None
    _client: Optional[redis.Redis] = None
    _pubsub: Optional[redis.client.PubSub] = None
    _subscribers: Dict[str, List[Callable]] = {}
    _listener_task: Optional[asyncio.Task] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def connect(cls) -> 'RedisService':
        """Connect to Redis server"""
        instance = cls()
        
        if instance._client is None:
            try:
                instance._client = redis.Redis.from_url(
                    settings.redis_url,
                    db=settings.redis_db,
                    password=settings.redis_password,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                )
                
                # Test connection
                await instance._client.ping()
                logger.info("✅ Connected to Redis")
                
                # Initialize pub/sub
                instance._pubsub = instance._client.pubsub()
                
            except Exception as e:
                logger.error(f"❌ Failed to connect to Redis: {e}")
                instance._client = None
                raise
        
        return instance
    
    @classmethod
    async def disconnect(cls):
        """Disconnect from Redis"""
        instance = cls()
        
        if instance._listener_task:
            instance._listener_task.cancel()
            try:
                await instance._listener_task
            except asyncio.CancelledError:
                pass
        
        if instance._pubsub:
            await instance._pubsub.close()
            instance._pubsub = None
        
        if instance._client:
            await instance._client.close()
            instance._client = None
        
        instance._subscribers = {}
        logger.info("🔌 Disconnected from Redis")
    
    @classmethod
    def get_client(cls) -> redis.Redis:
        """Get Redis client instance"""
        instance = cls()
        if instance._client is None:
            raise RuntimeError("Redis not connected. Call RedisService.connect() first.")
        return instance._client
    
    # ========================================
    # Pub/Sub Operations
    # ========================================
    
    @classmethod
    async def publish(cls, channel: str, message: Any) -> int:
        """Publish message to a channel"""
        client = cls.get_client()
        
        if isinstance(message, dict):
            message = json.dumps(message)
        
        return await client.publish(channel, message)
    
    @classmethod
    async def subscribe(cls, channel: str, callback: Callable[[str], Any]):
        """Subscribe to a channel with a callback"""
        instance = cls()
        
        if channel not in instance._subscribers:
            instance._subscribers[channel] = []
            await instance._pubsub.subscribe(channel)
        
        instance._subscribers[channel].append(callback)
        
        # Start listener if not running
        if instance._listener_task is None or instance._listener_task.done():
            instance._listener_task = asyncio.create_task(instance._listen())
        
        logger.info(f"📢 Subscribed to channel: {channel}")
    
    @classmethod
    async def unsubscribe(cls, channel: str, callback: Optional[Callable] = None):
        """Unsubscribe from a channel"""
        instance = cls()
        
        if channel in instance._subscribers:
            if callback:
                instance._subscribers[channel].remove(callback)
            else:
                instance._subscribers[channel] = []
            
            if not instance._subscribers[channel]:
                await instance._pubsub.unsubscribe(channel)
                del instance._subscribers[channel]
        
        logger.info(f"🔇 Unsubscribed from channel: {channel}")
    
    async def _listen(self):
        """Listen for pub/sub messages"""
        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"]
                    data = message["data"]
                    
                    # Try to parse JSON
                    try:
                        data = json.loads(data)
                    except (json.JSONDecodeError, TypeError):
                        pass
                    
                    # Call all subscribers for this channel
                    if channel in self._subscribers:
                        for callback in self._subscribers[channel]:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(data)
                                else:
                                    callback(data)
                            except Exception as e:
                                logger.error(f"Error in subscriber callback: {e}")
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
    
    # ========================================
    # Cache Operations
    # ========================================
    
    @classmethod
    async def cache_get(cls, key: str) -> Optional[Any]:
        """Get value from cache"""
        client = cls.get_client()
        value = await client.get(key)
        
        if value:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return None
    
    @classmethod
    async def cache_set(
        cls, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None,
        expire_timedelta: Optional[timedelta] = None
    ):
        """Set value in cache with optional expiration"""
        client = cls.get_client()
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        if expire_timedelta:
            expire = int(expire_timedelta.total_seconds())
        
        if expire:
            await client.setex(key, expire, value)
        else:
            await client.set(key, value)
    
    @classmethod
    async def cache_delete(cls, key: str):
        """Delete key from cache"""
        client = cls.get_client()
        await client.delete(key)
    
    @classmethod
    async def cache_exists(cls, key: str) -> bool:
        """Check if key exists in cache"""
        client = cls.get_client()
        return await client.exists(key) > 0
    
    @classmethod
    async def cache_increment(cls, key: str, amount: int = 1) -> int:
        """Increment a counter in cache"""
        client = cls.get_client()
        return await client.incrby(key, amount)
    
    # ========================================
    # Rate Limiting
    # ========================================
    
    @classmethod
    async def rate_limit_check(
        cls, 
        key: str, 
        max_requests: int, 
        window_seconds: int
    ) -> tuple[bool, int]:
        """
        Check rate limit for a key.
        Returns (is_allowed, remaining_requests)
        """
        client = cls.get_client()
        
        current = await client.get(key)
        
        if current is None:
            await client.setex(key, window_seconds, 1)
            return True, max_requests - 1
        
        current = int(current)
        
        if current >= max_requests:
            ttl = await client.ttl(key)
            return False, 0
        
        await client.incr(key)
        return True, max_requests - current - 1


# ========================================
# Disaster Event Channels
# ========================================

CHANNEL_NEW_ARTICLE = "disaster:new_article"
CHANNEL_ALERT = "disaster:alert"
CHANNEL_STATS_UPDATE = "disaster:stats_update"


async def publish_new_article(article: Dict[str, Any]):
    """Publish new disaster article to Redis channel"""
    try:
        await RedisService.publish(CHANNEL_NEW_ARTICLE, {
            "event": "new_disaster_article",
            "data": article
        })
        logger.debug(f"Published article: {article.get('title', 'Unknown')[:50]}")
    except Exception as e:
        logger.error(f"Failed to publish article: {e}")


async def publish_alert(alert: Dict[str, Any]):
    """Publish disaster alert"""
    try:
        await RedisService.publish(CHANNEL_ALERT, {
            "event": "disaster_alert",
            "data": alert
        })
    except Exception as e:
        logger.error(f"Failed to publish alert: {e}")


async def publish_stats_update(stats: Dict[str, Any]):
    """Publish stats update"""
    try:
        await RedisService.publish(CHANNEL_STATS_UPDATE, {
            "event": "stats_update",
            "data": stats
        })
    except Exception as e:
        logger.error(f"Failed to publish stats: {e}")
