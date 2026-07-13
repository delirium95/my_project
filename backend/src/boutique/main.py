from contextlib import asynccontextmanager
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from boutique.bootstrap.container import Container, build_container, shutdown_container
from boutique.config import Settings, get_settings
from boutique.domain.auth.exceptions import AuthenticationError
from boutique.infrastructure.observability import configure_observability
from boutique.presentation.http import security
from boutique.presentation.http.exception_handlers import authentication_error_handler
from boutique.presentation.http.router import api_router
from boutique.presentation.http.routers import auth, dashboard, dataset, health


def create_app(
    *,
    settings: Settings | None = None,
    container: Container | None = None,
) -> FastAPI:
    active_settings = settings or get_settings()
    active_container = container or build_container(settings=active_settings)
    configure_observability(settings=active_settings)
    active_container.wire(modules=[auth, dashboard, dataset, health, security])

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        await shutdown_container(container=active_container)

    app = FastAPI(
        title=active_settings.app_name,
        version="0.1.0",
        debug=active_settings.debug,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=active_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(AuthenticationError, authentication_error_handler)

    @app.middleware("http")
    async def add_request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            structlog.contextvars.clear_contextvars()

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
