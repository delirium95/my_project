import ssl
from collections.abc import Callable

from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool


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
        connect_args["ssl"] = ssl.create_default_context()
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
