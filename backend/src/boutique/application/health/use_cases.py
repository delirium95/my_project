import asyncio

from boutique.application.health.interfaces import GetReadinessUseCase
from boutique.domain.health.enums import HealthStatus
from boutique.domain.health.interfaces import HealthChecker
from boutique.domain.health.models import ReadinessReport


class GetReadinessUseCaseImpl(GetReadinessUseCase):
    def __init__(self, *, environment: str, checkers: list[HealthChecker]) -> None:
        self._environment = environment
        self._checkers = checkers

    async def __call__(self) -> ReadinessReport:
        services = await asyncio.gather(*(checker.check() for checker in self._checkers))
        status = (
            HealthStatus.HEALTHY
            if all(service.status is HealthStatus.HEALTHY for service in services)
            else HealthStatus.UNHEALTHY
        )
        return ReadinessReport(status=status, environment=self._environment, services=services)
