from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status

from boutique.application.health.interfaces import GetReadinessUseCase
from boutique.domain.health.enums import HealthStatus
from boutique.presentation.http.schemas.health import (
    ReadinessResponseSchema,
    ServiceHealthResponseSchema,
)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def liveness() -> dict[str, str]:
    return {"status": "healthy"}


@router.get("/ready", response_model=ReadinessResponseSchema)
@inject
async def readiness(
    http_response: Response,
    use_case: Annotated[GetReadinessUseCase, Depends(Provide["get_readiness"])],
) -> ReadinessResponseSchema:
    report = await use_case()
    if report.status is HealthStatus.UNHEALTHY:
        http_response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponseSchema(
        status=report.status,
        environment=report.environment,
        services=[
            ServiceHealthResponseSchema(name=item.name, status=item.status)
            for item in report.services
        ],
    )
