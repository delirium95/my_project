import logging

import sentry_sdk
import structlog

from boutique.config import Settings


def configure_observability(*, settings: Settings) -> None:
    logging.basicConfig(
        format="%(message)s",
        level=logging.DEBUG if settings.debug else logging.INFO,
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if settings.debug else logging.INFO
        ),
    )
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            send_default_pii=False,
        )
