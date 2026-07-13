import structlog
from redis.asyncio import Redis
from redis.exceptions import RedisError

from boutique.domain.auth.exceptions import RefreshTokenStoreUnavailableError
from boutique.domain.auth.interfaces import RefreshTokenBlacklist

logger = structlog.get_logger(__name__)

_KEY_PREFIX = "auth:refresh:revoked:"


class RedisRefreshTokenBlacklist(RefreshTokenBlacklist):
    """Redis-backed, single-use refresh-token store."""

    def __init__(self, *, client: Redis) -> None:
        self._client = client

    async def consume(self, *, token_id: str, ttl_seconds: int) -> bool:
        if ttl_seconds <= 0:
            return False
        try:
            return bool(
                await self._client.set(
                    f"{_KEY_PREFIX}{token_id}",
                    "1",
                    ex=ttl_seconds,
                    nx=True,
                )
            )
        except RedisError as error:
            logger.error("refresh_token_consume_failed", exc_info=True)
            raise RefreshTokenStoreUnavailableError(
                "Refresh-token service is temporarily unavailable"
            ) from error

    async def revoke(self, *, token_id: str, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            return
        try:
            await self._client.set(f"{_KEY_PREFIX}{token_id}", "1", ex=ttl_seconds)
        except RedisError as error:
            logger.error("refresh_token_revoke_failed", exc_info=True)
            raise RefreshTokenStoreUnavailableError(
                "Refresh-token service is temporarily unavailable"
            ) from error
