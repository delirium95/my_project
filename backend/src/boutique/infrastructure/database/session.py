import ssl
from collections.abc import Callable
from pathlib import Path

from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

_RDS_CA_BUNDLE = Path(__file__).resolve().parents[3] / "rds-global-bundle.pem"


def _rds_ca_bundle_path() -> str | None:
    """Return the CA bundle packaged in the Lambda image when it is available."""
    return str(_RDS_CA_BUNDLE) if _RDS_CA_BUNDLE.is_file() else None


def normalize_async_database_url(database_url: str) -> tuple[URL, dict[str, object]]:
    """Make a provider PostgreSQL URL usable by SQLAlchemy's asyncpg dialect.

    Managed PostgreSQL providers commonly expose a libpq URL such as
    ``postgresql://...?sslmode=require&channel_binding=require``.  ``asyncpg``
    needs an SSL context instead of those libpq query parameters.  Keeping this
    conversion at the infrastructure boundary lets local URLs remain unchanged
    while allowing the copied provider URL to be used directly in deployment.
    """
    url = make_url(database_url)
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+asyncpg")

    query = dict(url.query)
    sslmode = query.pop("sslmode", None)
    # Neon includes this libpq-only parameter in some connection strings.
    query.pop("channel_binding", None)
    url = url.set(query=query)

    connect_args: dict[str, object] = {}
    if sslmode in {"require", "verify-ca", "verify-full"}:
        # RDS presents an AWS-issued certificate.  The Lambda base image does
        # not include that trust chain, so the production image packages the
        # official RDS bundle.  Local providers continue using system roots.
        connect_args["ssl"] = ssl.create_default_context(cafile=_rds_ca_bundle_path())
    elif sslmode and sslmode != "disable":
        raise ValueError(f"Unsupported PostgreSQL sslmode for asyncpg: {sslmode}")

    return url, connect_args


def create_database_engine(*, database_url: str, serverless: bool) -> AsyncEngine:
    """Build an engine suited to either local development or Lambda concurrency."""
    options: dict[str, object] = {"pool_pre_ping": True}
    normalized_url, connect_args = normalize_async_database_url(database_url)
    if connect_args:
        options["connect_args"] = connect_args
    if serverless:
        options["poolclass"] = NullPool
    else:
        options["pool_size"] = 5
        options["max_overflow"] = 5
    return create_async_engine(url=normalized_url, **options)


def make_session_factory(*, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


SessionFactory = Callable[[], AsyncSession]
