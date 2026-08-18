"""Redis/in-memory caching system with TTL support and cache decorators."""

import asyncio
import json
import hashlib
import functools
import time
import logging
from typing import Any, Optional, Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis-py not installed, falling back to in-memory cache")


class CacheManager:
    """TTL-based caching with Redis backend and in-memory fallback."""

    def __init__(self, redis_url: str = "redis://localhost:6379", default_ttl: int = 300):
        self.default_ttl = default_ttl
        self._memory_cache: dict[str, tuple[Any, float]] = {}
        self._redis = None

        if REDIS_AVAILABLE:
            try:
                self._redis = redis.from_url(redis_url, decode_responses=True)
                self._redis.ping()
                logger.info("Connected to Redis cache backend")
            except Exception:
                logger.warning("Redis unavailable, using in-memory cache")
                self._redis = None
        else:
            logger.info("Using in-memory cache backend")

    @property
    def is_redis(self) -> bool:
        return self._redis is not None

    def _key(self, namespace: str, key: str) -> str:
        return f"campus:{namespace}:{key}"

    def get(self, namespace: str, key: str) -> Optional[Any]:
        full_key = self._key(namespace, key)
        if self._redis:
            try:
                data = self._redis.get(full_key)
                if data is not None:
                    return json.loads(data)
                return None
            except Exception:
                logger.warning(f"Redis GET failed for {full_key}")
                return self._memory_get(full_key)
        return self._memory_get(full_key)

    def set(self, namespace: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl or self.default_ttl
        full_key = self._key(namespace, key)
        serialized = json.dumps(value, default=str)

        if self._redis:
            try:
                self._redis.setex(full_key, ttl, serialized)
                return
            except Exception:
                logger.warning(f"Redis SET failed for {full_key}")

        self._memory_set(full_key, value, ttl)

    def delete(self, namespace: str, key: str) -> None:
        full_key = self._key(namespace, key)
        if self._redis:
            try:
                self._redis.delete(full_key)
            except Exception:
                logger.warning(f"Redis DELETE failed for {full_key}")
        self._memory_delete(full_key)

    def invalidate_pattern(self, namespace: str, pattern: str = "*") -> int:
        full_pattern = self._key(namespace, pattern)
        count = 0
        if self._redis:
            try:
                keys = list(self._redis.scan_iter(match=full_pattern, count=1000))
                if keys:
                    count = self._redis.delete(*keys)
                    logger.info(f"Invalidated {count} keys matching {full_pattern}")
                return count
            except Exception:
                logger.warning(f"Redis invalidation failed for {full_pattern}")

        prefix = self._key(namespace, "")
        to_delete = []
        for k in self._memory_cache:
            if k.startswith(prefix):
                if pattern == "*" or pattern in k[len(prefix):]:
                    to_delete.append(k)
        for k in to_delete:
            del self._memory_cache[k]
            count += 1
        return count

    def invalidate_chat(self, chat_id: Optional[str] = None) -> None:
        self.invalidate_pattern("messages", f"*{chat_id or ''}*")
        self.invalidate_pattern("chats", "*")

    def invalidate_groups(self, group_id: Optional[str] = None) -> None:
        self.invalidate_pattern("groups", f"*{group_id or ''}*")
        self.invalidate_pattern("chats", "*")

    def invalidate_users(self, user_id: Optional[str] = None) -> None:
        self.invalidate_pattern("users", f"*{user_id or ''}*")

    def flush_all(self) -> None:
        if self._redis:
            try:
                keys = list(self._redis.scan_iter(match="campus:*", count=5000))
                if keys:
                    self._redis.delete(*keys)
            except Exception:
                pass
        self._memory_cache.clear()

    def warm_cache(self, data_loader: Callable, namespace: str, keys: list[str], ttl: Optional[int] = None) -> int:
        count = 0
        for key in keys:
            existing = self.get(namespace, key)
            if existing is None:
                data = data_loader(key)
                if data is not None:
                    self.set(namespace, key, data, ttl)
                    count += 1
        logger.info(f"Cache warmed: {count}/{len(keys)} keys in {namespace}")
        return count

    def _memory_get(self, key: str) -> Optional[Any]:
        if key in self._memory_cache:
            value, expires_at = self._memory_cache[key]
            if time.time() < expires_at:
                return value
            del self._memory_cache[key]
        return None

    def _memory_set(self, key: str, value: Any, ttl: int) -> None:
        self._memory_cache[key] = (value, time.time() + ttl)
        if len(self._memory_cache) > 10000:
            self._evict_expired()

    def _memory_delete(self, key: str) -> None:
        self._memory_cache.pop(key, None)

    def _evict_expired(self) -> None:
        now = time.time()
        expired = [k for k, (_, exp) in self._memory_cache.items() if now >= exp]
        for k in expired:
            del self._memory_cache[k]


cache = CacheManager()


def cached(namespace: str, key_func: Optional[Callable] = None, ttl: Optional[int] = None):
    """Decorator to cache function results."""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                param_hash = hashlib.md5(
                    json.dumps({"args": args[1:] if args else [], "kwargs": kwargs}, default=str).encode()
                ).hexdigest()[:16]
                cache_key = f"{func.__module__}.{func.__name__}:{param_hash}"

            result = cache.get(namespace, cache_key)
            if result is not None:
                return result

            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            if result is not None:
                cache.set(namespace, cache_key, result, ttl)
            return result
        return wrapper
    return decorator


def cache_invalidate(namespace: str, pattern: str = "*"):
    """Decorator to invalidate cache entries after function execution."""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            cache.invalidate_pattern(namespace, pattern)
            return result
        return wrapper
    return decorator
