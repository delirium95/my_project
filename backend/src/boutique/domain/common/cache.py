from abc import ABC, abstractmethod
from typing import Any


class CacheInvalidationError(RuntimeError):
    """Raised when an already-committed write cannot invalidate cached read models."""


class BaseCacheService(ABC):
    """Application-facing cache contract; implementation is Redis in production."""

    @abstractmethod
    async def get(self, *, key: str) -> dict[str, Any] | None:
        """Return a cached mapping, or ``None`` for a cache miss."""

    @abstractmethod
    async def set(self, *, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        """Store a mapping with a bounded lifetime."""

    @abstractmethod
    async def invalidate_prefix(self, *, prefix: str) -> None:
        """Invalidate every cache key beginning with ``prefix``."""
