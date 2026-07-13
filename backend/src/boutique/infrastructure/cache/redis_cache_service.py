import json
from typing import Any

import structlog
from redis.asyncio import Redis
from redis.exceptions import RedisError

from boutique.domain.common.cache import BaseCacheService, CacheInvalidationError

logger = structlog.get_logger(__name__)


class RedisCacheService(BaseCacheService):
    """Best-effort Redis cache; cache failures never fail a dashboard request."""

    def __init__(self, *, client: Redis) -> None:
        self._client = client

    async def get(self, *, key: str) -> dict[str, Any] | None:
        try:
            raw_value = await self._client.get(key)
            return json.loads(raw_value) if raw_value is not None else None
        except (RedisError, json.JSONDecodeError):
            logger.warning("cache_read_failed", cache_key=key, exc_info=True)
            return None

    async def set(self, *, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        try:
            await self._client.set(key, json.dumps(value), ex=ttl_seconds)
        except RedisError:
            logger.warning("cache_write_failed", cache_key=key, exc_info=True)

    async def invalidate_prefix(self, *, prefix: str) -> None:
        try:
            keys = [key async for key in self._client.scan_iter(match=f"{prefix}*")]
            if keys:
                await self._client.delete(*keys)
        except RedisError as error:
            logger.error("cache_invalidation_failed", prefix=prefix, exc_info=True)
            raise CacheInvalidationError(
                "Dashboard data was imported, but cached dashboard values could not be invalidated"
            ) from error
