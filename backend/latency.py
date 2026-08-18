"""WebSocket connection pooling, message batching, and latency optimizations."""

import asyncio
import gzip
import hashlib
import json
import time
import logging
from typing import Any, Optional
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PooledConnection:
    ws: Any
    user_id: str
    connected_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    subscriptions: set = field(default_factory=set)


class ConnectionPool:
    """WebSocket connection pooling with heartbeat monitoring."""

    def __init__(self, max_connections: int = 1000):
        self.max_connections = max_connections
        self._connections: dict[str, list[PooledConnection]] = defaultdict(list)
        self._user_connections: dict[str, PooledConnection] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, ws: Any) -> Optional[PooledConnection]:
        async with self._lock:
            total = sum(len(conns) for conns in self._connections.values())
            if total >= self.max_connections:
                evicted = await self._evict_stale()
                if evicted == 0:
                    logger.warning("Connection pool full, rejecting connection")
                    return None

            conn = PooledConnection(ws=ws, user_id=user_id)
            self._connections[user_id].append(conn)
            self._user_connections[f"{user_id}:{id(ws)}"] = conn
            logger.debug(f"Pool: user={user_id} total={total + 1}")
            return conn

    async def disconnect(self, user_id: str, ws: Any) -> None:
        async with self._lock:
            key = f"{user_id}:{id(ws)}"
            conn = self._user_connections.pop(key, None)
            if conn and conn in self._connections.get(user_id, []):
                self._connections[user_id].remove(conn)
                if not self._connections[user_id]:
                    del self._connections[user_id]

    def get_user_connections(self, user_id: str) -> list[PooledConnection]:
        return self._connections.get(user_id, [])

    async def broadcast(self, event: str, data: Any, exclude_user: Optional[str] = None) -> int:
        count = 0
        message = {"event": event, "data": data}
        for user_id, conns in list(self._connections.items()):
            if user_id == exclude_user:
                continue
            for conn in list(conns):
                try:
                    await conn.ws.send_json(message)
                    count += 1
                except Exception:
                    await self.disconnect(user_id, conn.ws)
        return count

    async def send_to_user(self, user_id: str, event: str, data: Any) -> int:
        count = 0
        message = {"event": event, "data": data}
        for conn in self.get_user_connections(user_id):
            try:
                await conn.ws.send_json(message)
                count += 1
            except Exception:
                await self.disconnect(user_id, conn.ws)
        return count

    def update_heartbeat(self, user_id: str, ws: Any) -> None:
        key = f"{user_id}:{id(ws)}"
        conn = self._user_connections.get(key)
        if conn:
            conn.last_heartbeat = time.time()

    async def _evict_stale(self, timeout: float = 300) -> int:
        evicted = 0
        now = time.time()
        for user_id, conns in list(self._connections.items()):
            for conn in list(conns):
                if now - conn.last_heartbeat > timeout:
                    try:
                        await conn.ws.close(code=1000, reason="stale")
                    except Exception:
                        pass
                    await self.disconnect(user_id, conn.ws)
                    evicted += 1
        return evicted

    @property
    def active_count(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


class MessageBatcher:
    """Collects messages for 50ms windows before sending in batches."""

    def __init__(self, delay_ms: int = 50):
        self.delay = delay_ms / 1000
        self._batches: dict[str, list[tuple[str, dict]]] = defaultdict(list)
        self._timers: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self._send_func = None

    def set_sender(self, func):
        self._send_func = func

    async def add(self, channel: str, event: str, data: dict) -> None:
        async with self._lock:
            self._batches[channel].append((event, data))
            if channel not in self._timers or self._timers[channel].done():
                self._timers[channel] = asyncio.create_task(self._flush_after(channel))

    async def _flush_after(self, channel: str) -> None:
        await asyncio.sleep(self.delay)
        await self._flush(channel)

    async def _flush(self, channel: str) -> None:
        async with self._lock:
            messages = self._batches.pop(channel, [])
            self._timers.pop(channel, None)

        if messages and self._send_func:
            await self._send_func(channel, messages)

    async def flush_all(self) -> None:
        async with self._lock:
            channels = list(self._batches.keys())
        for channel in channels:
            await self._flush(channel)


class ResponseCompressor:
    """Gzip compression for responses exceeding threshold."""

    def __init__(self, min_size: int = 1024, level: int = 6):
        self.min_size = min_size
        self.level = level

    def compress(self, data: bytes) -> tuple[bytes, bool]:
        if len(data) < self.min_size:
            return data, False
        compressed = gzip.compress(data, compresslevel=self.level)
        if len(compressed) < len(data):
            return compressed, True
        return data, False


class ETagManager:
    """ETag generation and conditional request handling."""

    @staticmethod
    def generate(data: Any) -> str:
        content = json.dumps(data, sort_keys=True, default=str)
        return f'"{hashlib.md5(content.encode()).hexdigest()}"'

    @staticmethod
    def check_match(request_etag: str, current_etag: str) -> bool:
        if not request_etag or not current_etag:
            return False
        return request_etag == current_etag


class LazyPaginator:
    """Lazy loading support for paginated data."""

    def __init__(self, items: list, page_size: int = 20):
        self.items = items
        self.page_size = page_size
        self._cache: dict[int, list] = {}

    def get_page(self, page: int) -> dict:
        if page in self._cache:
            data = self._cache[page]
        else:
            start = (page - 1) * self.page_size
            end = start + self.page_size
            data = self.items[start:end]
            self._cache[page] = data

        total_pages = max(1, (len(self.items) + self.page_size - 1) // self.page_size)
        return {
            "data": data,
            "page": page,
            "page_size": self.page_size,
            "total_items": len(self.items),
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }

    def invalidate(self) -> None:
        self._cache.clear()


class PrefetchManager:
    """Prefetching for frequently accessed resources."""

    def __init__(self):
        self._prefetch_tasks: dict[str, asyncio.Task] = {}
        self._data: dict[str, Any] = {}

    def register(self, key: str, fetcher, ttl: float = 60):
        self._prefetch_tasks[key] = asyncio.create_task(self._loop(key, fetcher, ttl))

    async def _loop(self, key: str, fetcher, ttl: float) -> None:
        while True:
            try:
                self._data[key] = await fetcher()
            except Exception as e:
                logger.warning(f"Prefetch {key} failed: {e}")
            await asyncio.sleep(ttl)

    def get(self, key: str) -> Optional[Any]:
        return self._data.get(key)

    async def stop(self) -> None:
        for task in self._prefetch_tasks.values():
            task.cancel()
        self._prefetch_tasks.clear()


connection_pool = ConnectionPool()
message_batcher = MessageBatcher()
compressor = ResponseCompressor()
etag_manager = ETagManager()
prefetch_manager = PrefetchManager()


async def keepalive_handler(ws: Any, user_id: str, interval: float = 30) -> None:
    """Monitor connection health and clean up stale connections."""
    try:
        while True:
            await asyncio.sleep(interval)
            connection_pool.update_heartbeat(user_id, ws)
    except Exception:
        pass
    finally:
        await connection_pool.disconnect(user_id, ws)
