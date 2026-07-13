from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from boutique.domain.health.enums import HealthStatus
from boutique.domain.health.interfaces import HealthChecker
from boutique.domain.health.models import ServiceHealth


class PostgresHealthChecker(HealthChecker):
    def __init__(self, *, engine: AsyncEngine) -> None:
        self._engine = engine

    async def check(self) -> ServiceHealth:
        try:
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except Exception:
            return ServiceHealth(name="postgres", status=HealthStatus.UNHEALTHY)
        return ServiceHealth(name="postgres", status=HealthStatus.HEALTHY)


class RedisHealthChecker(HealthChecker):
    def __init__(self, *, client: Redis) -> None:
        self._client = client

    async def check(self) -> ServiceHealth:
        try:
            await self._client.ping()
        except Exception:
            return ServiceHealth(name="redis", status=HealthStatus.UNHEALTHY)
        return ServiceHealth(name="redis", status=HealthStatus.HEALTHY)
