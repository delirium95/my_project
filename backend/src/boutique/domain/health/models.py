from boutique.domain.common.models import ValueObject
from boutique.domain.health.enums import HealthStatus


class ServiceHealth(ValueObject):
    name: str
    status: HealthStatus


class ReadinessReport(ValueObject):
    status: HealthStatus
    environment: str
    services: tuple[ServiceHealth, ...]
