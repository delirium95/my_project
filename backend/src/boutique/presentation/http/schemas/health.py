from boutique.domain.health.enums import HealthStatus
from boutique.presentation.http.schemas.base import Schema


class ServiceHealthResponseSchema(Schema):
    name: str
    status: HealthStatus


class ReadinessResponseSchema(Schema):
    status: HealthStatus
    environment: str
    services: list[ServiceHealthResponseSchema]
