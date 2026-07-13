from abc import ABC, abstractmethod

from boutique.domain.health.models import ServiceHealth


class HealthChecker(ABC):
    @abstractmethod
    async def check(self) -> ServiceHealth:
        """Check one external dependency without raising to the readiness use case."""
