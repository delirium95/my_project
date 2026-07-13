from abc import ABC, abstractmethod

from boutique.domain.health.models import ReadinessReport


class GetReadinessUseCase(ABC):
    @abstractmethod
    async def __call__(self) -> ReadinessReport:
        """Check every dependency required to serve traffic."""
